from contextlib import closing
import hashlib
import json
import sqlite3
import time
from pathlib import Path

from databases.neo4j.connection import SOURCE, DATABASE, DATASET, PREPARED, connect
from databases.neo4j.model.schema import GRAPH_SCHEMA, SQLITE_SCHEMA


def metadata(db):
    return {k: json.loads(v) for k, v in db.execute("SELECT key,value FROM meta")}


def add_event(group, key, timestamp):
    if key not in group:
        group[key] = [1, timestamp, timestamp]
    else:
        entry = group[key]
        entry[0] += 1
        entry[1] = min(entry[1], timestamp)
        entry[2] = max(entry[2], timestamp)


def flush(db, events):
    users, tracks, artists, credits = set(), {}, set(), set()
    listens, user_artists = {}, {}
    for user, track, title, artist, timestamp in events:
        users.add(user)
        tracks.setdefault(track, title)
        artists.add(artist)
        credits.add((track, artist))
        add_event(listens, (user, track), timestamp)
        add_event(user_artists, (user, artist), timestamp)
    with db:
        db.executemany("INSERT OR IGNORE INTO users VALUES (?)", ((u,) for u in users))
        db.executemany("INSERT OR IGNORE INTO tracks VALUES (?,?)", tracks.items())
        db.executemany("INSERT OR IGNORE INTO artists VALUES (?)", ((a,) for a in artists))
        db.executemany("INSERT OR IGNORE INTO credits VALUES (?,?)", sorted(credits))
        for table, field, rows in (("listens", "track", listens),
                                   ("user_artists", "artist", user_artists)):
            db.executemany(
                f"INSERT INTO {table} VALUES (?,?,?,?,?) ON CONFLICT(user,{field}) DO UPDATE SET "
                f"count={table}.count+excluded.count, first=MIN({table}.first,excluded.first), "
                f"last=MAX({table}.last,excluded.last)",
                ((*key, *values) for key, values in rows.items()),
            )


def read_events(db, source, digest):
    count, invalid, errors, events = 0, 0, [], []
    with source.open("rb") as stream:
        for count, line in enumerate(stream, 1):
            digest.update(line)
            try:
                record = json.loads(line)
                user, track, timestamp = (record["user_id"], record["recording_msid"],
                                          record["timestamp"])
                title = record["track_metadata"]["track_name"]
                artist = record["track_metadata"]["artist_name"]
                if type(user) is not int or type(timestamp) is not int:
                    raise ValueError("user_id y timestamp deben ser enteros")
                if not -(2**63) <= user < 2**63:
                    raise ValueError("user_id fuera del rango entero de 64 bits")
                if not all(isinstance(v, str) and v.strip() for v in (track, title, artist)):
                    raise ValueError("recording_msid, título y artista deben ser textos no vacíos")

                if not -62_135_596_800 <= timestamp <= 253_402_300_799:
                    raise ValueError("timestamp fuera del rango soportado")
                events.append((user, track, title, artist, timestamp))
            except (ValueError, TypeError, KeyError) as exc:
                invalid += 1
                if len(errors) < 5:
                    errors.append(f"Línea {count}: {exc}")
            if len(events) >= 10_000:
                flush(db, events)
                events.clear()
            if count % 250_000 == 0:
                print(f"Preparación: {count:,} filas; inválidas: {invalid}", flush=True)
    if events:
        flush(db, events)
    return count, invalid, errors


def prepare(source, output, dataset, expected_count=4_855_809):
    source, output = Path(source), Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    if temporary.exists():
        temporary.unlink()
    start = time.monotonic()
    before = source.stat()
    digest = hashlib.sha256()
    try:
        with sqlite3.connect(temporary) as db:
            db.executescript(SQLITE_SCHEMA)
            db.execute("PRAGMA journal_mode=OFF")
            db.execute("PRAGMA synchronous=OFF")
            db.execute("PRAGMA cache_size=-65536")
            count, invalid, errors = read_events(db, source, digest)
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("El archivo de entrada cambió durante la preparación")
            if invalid or not count:
                raise ValueError(f"Filas: {count}; inválidas: {invalid}. {'; '.join(errors)}")
            if expected_count and count != expected_count:
                raise ValueError(f"Se esperaban {expected_count:,} filas; se leyeron {count:,}")

            db.execute("CREATE INDEX ua_artist ON user_artists(artist,user)")
            db.execute("CREATE INDEX listens_track ON listens(track,user)")
            stats = {"dataset": dataset, "source_sha256": digest.hexdigest(), "rows": count,
                     "source_bytes": before.st_size, "schema_version": 1,
                     "prepare_seconds": round(time.monotonic() - start, 3)}
            for table in ("users", "tracks", "artists", "credits", "listens", "user_artists"):
                stats[table] = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            stats["first"], stats["last"] = db.execute("SELECT min(first),max(last) FROM listens").fetchone()
            db.executemany("INSERT INTO meta VALUES (?,?)",
                           ((k, json.dumps(v)) for k, v in stats.items()))
            db.commit()

        db.close()
        temporary.replace(output)
        print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)
        return stats
    except BaseException:
        if 'db' in locals():
            db.close()
        temporary.unlink(missing_ok=True)
        raise


def load_users(tx, rows, dataset):
    tx.run("UNWIND $rows AS f MERGE (:Usuario {id:f.id})", rows=rows).consume()


def load_tracks(tx, rows, dataset):
    tx.run("""
        UNWIND $rows AS f MERGE (c:Cancion {id:f.id})
        ON CREATE SET c.titulo=f.title
    """, rows=rows).consume()


def load_artists(tx, rows, dataset):
    tx.run("UNWIND $rows AS f MERGE (:Artista {nombre:f.name})", rows=rows).consume()


def load_credits(tx, rows, dataset):
    tx.run("""
        UNWIND $rows AS f
        MATCH (c:Cancion {id:f.track}), (a:Artista {nombre:f.artist})
        MERGE (c)-[:INTERPRETADA_POR {lote:$dataset}]->(a)
    """, rows=rows, dataset=dataset).consume()


def load_listens(tx, rows, dataset):
    tx.run("""
        UNWIND $rows AS f
        MATCH (u:Usuario {id:f.user}), (c:Cancion {id:f.track})
        MERGE (u)-[r:ESCUCHO {lote:$dataset}]->(c)
        SET r.cantidad=f.count,r.primera_escucha=f.first,r.ultima_escucha=f.last
    """, rows=rows, dataset=dataset).consume()


def load_preferences(tx, rows, dataset):
    tx.run("""
        UNWIND $rows AS f
        MATCH (u:Usuario {id:f.user}), (a:Artista {nombre:f.artist})
        MERGE (u)-[r:ESCUCHA_ARTISTA {lote:$dataset}]->(a)
        SET r.cantidad=f.count,r.proporcion=f.proportion,
            r.primera_escucha=f.first,r.ultima_escucha=f.last
    """, rows=rows, dataset=dataset).consume()


def load_data(session, db, meta):
    dataset = meta["dataset"]
    for statement in GRAPH_SCHEMA:
        session.run(statement).consume()
    previous = session.run("MATCH (l:Lote {id:$dataset}) RETURN l.source_sha256 AS sha", dataset=dataset).single()
    if previous and previous["sha"] != meta["source_sha256"]:
        raise ValueError("El lote existente tiene otro contenido; no se reemplaza")
    session.run("""
        MERGE (l:Lote {id:$dataset})
        SET l.source_sha256=$sha,l.registros=$total,l.estado='cargando'
    """, dataset=dataset, sha=meta["source_sha256"], total=meta["rows"]).consume()

    db.row_factory = sqlite3.Row

    def send_batches(select, callback):
        cursor = db.execute(select)
        total = 0
        while rows := cursor.fetchmany(1000):
            session.execute_write(callback, [dict(f) for f in rows], dataset)
            total += len(rows)
        print(f"{callback.__name__}: {total:,}", flush=True)

    send_batches("SELECT id FROM users", load_users)
    send_batches("SELECT id,title FROM tracks", load_tracks)
    send_batches("SELECT name FROM artists", load_artists)
    send_batches("SELECT track,artist FROM credits", load_credits)
    send_batches("SELECT user,track,count,first,last FROM listens", load_listens)
    send_batches("""
        SELECT ua.*,1.0*ua.count/t.total AS proportion FROM user_artists ua
        JOIN (SELECT user,sum(count) AS total FROM user_artists GROUP BY user) t ON ua.user=t.user
    """, load_preferences)

    for relation_type, table in (("ESCUCHO", "listens"), ("ESCUCHA_ARTISTA", "user_artists")):
        result = session.run(f"""
            MATCH ()-[r:{relation_type} {{lote:$dataset}}]->()
            RETURN count(r) AS relaciones,sum(r.cantidad) AS escuchas
        """, dataset=dataset).single()
        if (result["relaciones"], result["escuchas"]) != (meta[table], meta["rows"]):
            raise ValueError(f"La carga de {relation_type} no coincide con los datos preparados")
    session.run("MATCH (l:Lote {id:$dataset}) SET l.estado='completo'", dataset=dataset).consume()
    print(f"Carga completa: {meta['rows']:,} escuchas")


def main():
    if not PREPARED.exists():
        prepare(SOURCE, PREPARED, DATASET)
    with closing(sqlite3.connect(PREPARED)) as db:
        meta = metadata(db)
        if meta["dataset"] != DATASET:
            raise ValueError("La preparación pertenece a otro lote")
        with connect() as driver, driver.session(database=DATABASE) as session:
            load_data(session, db, meta)


if __name__ == "__main__":
    main()
