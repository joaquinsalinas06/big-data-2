import argparse
import json
import sys
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import islice
from operator import itemgetter
from pathlib import Path
from typing import NamedTuple

from cassandra.concurrent import execute_concurrent
from cassandra.query import UNSET_VALUE, BatchStatement, BatchType

from databases.cassandra.connection import get_session

DEFAULT_FILE = Path("data/processed/listens_full.jsonl")
DEFAULT_BATCH_SIZE = 500_000
CONCURRENCY = 128
ROWS_PER_BATCH = 30  # ~5 KB por BATCH, el umbral de aviso por defecto de Cassandra
TOP_ARTISTS = 50
LISTEN_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://listenbrainz.org/listen")


class Listen(NamedTuple):
    user_id: int
    listened_at: datetime
    listen_id: uuid.UUID
    artist_name: str
    track_name: str
    release_name: str | None
    recording_msid: str | None


def month_of(moment):
    return f"{moment.year:04d}-{moment.month:02d}"


def make_listen_id(user_id, timestamp, recording_msid, artist_name, track_name):
    """Id determinista: la misma escucha siempre genera el mismo uuid, así recargar no duplica."""
    return uuid.uuid5(LISTEN_NAMESPACE, f"{user_id}|{timestamp}|{recording_msid}|{artist_name}|{track_name}")


def parse_listen(line):
    """Devuelve la escucha limpia o None si le falta algo que Cassandra necesita."""
    try:
        record = json.loads(line)
        metadata = record["track_metadata"]
        user_id, timestamp = record["user_id"], record["timestamp"]
        artist_name = metadata["artist_name"].strip()
        track_name = metadata["track_name"].strip()
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    if type(user_id) is not int or type(timestamp) is not int or not artist_name or not track_name:
        return None

    release_name = metadata.get("release_name")
    release_name = release_name.strip() if isinstance(release_name, str) and release_name.strip() else None
    recording_msid = record.get("recording_msid") or None
    return Listen(
        user_id=user_id,
        listened_at=datetime.fromtimestamp(timestamp, timezone.utc),
        listen_id=make_listen_id(user_id, timestamp, recording_msid, artist_name, track_name),
        artist_name=artist_name,
        track_name=track_name,
        release_name=release_name,
        recording_msid=recording_msid,
    )


def parse_batch(lines):
    listens, seen = [], set()
    skipped = duplicates = 0
    for line in lines:
        listen = parse_listen(line)
        if listen is None:
            skipped += 1
        elif listen.listen_id in seen:
            duplicates += 1
        else:
            seen.add(listen.listen_id)
            listens.append(listen)
    return listens, skipped, duplicates


def read_batches(path, batch_size):
    with path.open("r", encoding="utf-8") as source:
        first_line = 1
        while lines := list(islice(source, batch_size)):
            yield first_line, first_line + len(lines) - 1, lines
            first_line += len(lines)


def write_by_partition(session, statement, rows, partition_of, batch_type=BatchType.UNLOGGED):
    """Agrupa filas de la misma partición en BATCH pequeños.

    Un BATCH de una sola partición se aplica como una única mutación en Cassandra, así que
    se hacen muchos menos viajes de red que con una escritura por fila (unas 13 veces más
    rápido en las pruebas). Mezclar particiones en un BATCH sería al revés: más lento.
    """
    groups = defaultdict(list)
    for row in rows:
        groups[partition_of(row)].append(row)

    batches = []
    for group in groups.values():
        for start in range(0, len(group), ROWS_PER_BATCH):
            batch = BatchStatement(batch_type=batch_type)
            for row in group[start:start + ROWS_PER_BATCH]:
                batch.add(statement, row)
            batches.append((batch, ()))

    # Hay que recorrer el generador: es lo que espera a que terminen las escrituras y lanza el primer error.
    for _ in execute_concurrent(session, batches, concurrency=CONCURRENCY, results_generator=True):
        pass


def listen_row(listen):
    return (
        listen.user_id, month_of(listen.listened_at), listen.listened_at, listen.listen_id,
        listen.artist_name, listen.track_name,
        listen.release_name or UNSET_VALUE,  # UNSET en vez de None: no deja tombstones
        listen.recording_msid or UNSET_VALUE,
    )


def daily_stats_rows(per_user_day):
    listens, users = Counter(), Counter()
    for (_, day), count in per_user_day.items():
        listens[day] += count
        users[day] += 1

    rows = []
    for day in sorted(listens):
        previous = listens[day - timedelta(days=1)]
        growth = (listens[day] - previous) / previous * 100 if previous else None
        rows.append((day.year, day, listens[day], users[day], listens[day] / users[day], growth))
    return rows


def top_artist_rows(per_artist_month):
    by_month = defaultdict(list)
    for (artist, month), count in per_artist_month.items():
        by_month[month].append((count, artist))

    rows = []
    for month, artists in by_month.items():
        total = sum(count for count, _ in artists)
        best = sorted(artists, key=lambda item: (-item[0], item[1]))[:TOP_ARTISTS]
        rows += [(month, rank, artist, count, count / total * 100) for rank, (count, artist) in enumerate(best, 1)]
    return rows


def write_aggregates(session, per_user_day, per_artist_month):
    by_first_column = itemgetter(0)  # en todas estas tablas la partición es la primera columna

    insert_daily_stats = session.prepare("""
        INSERT INTO daily_stats (year, day, listens, active_users, listens_per_user, growth_pct)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    write_by_partition(session, insert_daily_stats, daily_stats_rows(per_user_day), by_first_column)

    insert_top_artist = session.prepare("""
        INSERT INTO top_artists_by_month (month, rank, artist_name, listens, share_pct)
        VALUES (?, ?, ?, ?, ?)
    """)
    write_by_partition(session, insert_top_artist, top_artist_rows(per_artist_month), by_first_column)

    insert_artist_month = session.prepare("""
        INSERT INTO artist_monthly_listens (artist_name, month, listens)
        VALUES (?, ?, ?)
    """)
    write_by_partition(session, insert_artist_month,
                       [(artist, month, n) for (artist, month), n in per_artist_month.items()], by_first_column)

    insert_user_day = session.prepare("""
        INSERT INTO user_daily_listens (user_id, day, listens)
        VALUES (?, ?, ?)
    """)
    write_by_partition(session, insert_user_day,
                       [(user, day, n) for (user, day), n in per_user_day.items()], by_first_column)


def load_listens(session, path=DEFAULT_FILE, batch_size=DEFAULT_BATCH_SIZE, max_batches=0):
    """Carga los lotes pendientes y recalcula los agregados. Devuelve un resumen (sirve como XCom en Airflow)."""
    path = Path(path)
    insert_listen = session.prepare("""
        INSERT INTO listens_by_user (user_id, month, listened_at, listen_id,
                                     artist_name, track_name, release_name, recording_msid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    insert_batch = session.prepare("""
        INSERT INTO load_batches (batch_id, source_file, first_line, last_line,
                                  rows_loaded, rows_skipped, duplicates, loaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    loaded_before = {row["batch_id"] for row in session.execute("SELECT batch_id FROM load_batches")}
    per_user_day, per_artist_month = Counter(), Counter()
    summary = {"batches_loaded": 0, "batches_already_loaded": 0, "rows_loaded": 0, "rows_skipped": 0, "duplicates": 0}

    for first_line, last_line, lines in read_batches(path, batch_size):
        batch_id = f"{path.name}:{first_line}-{last_line}"
        is_new = batch_id not in loaded_before
        if is_new and max_batches and summary["batches_loaded"] >= max_batches:
            break

        started = time.perf_counter()
        listens, skipped, duplicates = parse_batch(lines)
        for listen in listens:
            per_user_day[(listen.user_id, listen.listened_at.date())] += 1
            per_artist_month[(listen.artist_name, month_of(listen.listened_at))] += 1
        if not is_new:
            summary["batches_already_loaded"] += 1
            continue

        write_by_partition(session, insert_listen, [listen_row(listen) for listen in listens], lambda row: (row[0], row[1]))
        session.execute(insert_batch, (
            batch_id, str(path), first_line, last_line, len(listens), skipped, duplicates, datetime.now(timezone.utc),
        ))
        elapsed = time.perf_counter() - started
        summary["batches_loaded"] += 1
        summary["rows_loaded"] += len(listens)
        summary["rows_skipped"] += skipped
        summary["duplicates"] += duplicates
        print(
            f"Lote {first_line:,}-{last_line:,}: {len(listens):,} escuchas, {skipped:,} omitidas, "
            f"{duplicates:,} duplicadas, {elapsed:.0f} s ({len(listens) / elapsed:,.0f} filas/s)",
            flush=True,
        )

    started = time.perf_counter()
    write_aggregates(session, per_user_day, per_artist_month)
    summary["listens_in_aggregates"] = sum(per_user_day.values())
    summary["aggregate_rows"] = len(per_user_day) + len(per_artist_month)
    print(f"Tablas agregadas recalculadas en {time.perf_counter() - started:.0f} s", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Cargar escuchas ListenBrainz en Cassandra")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="JSONL de escuchas")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Líneas por lote")
    parser.add_argument("--max-batches", type=int, default=0, help="Máximo de lotes nuevos a cargar (0 = todos)")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"ERROR: no existe {args.file}", file=sys.stderr)
        return 2

    session = get_session()
    started = time.perf_counter()
    try:
        summary = load_listens(session, args.file, args.batch_size, args.max_batches)
    finally:
        session.cluster.shutdown()

    print("=== CARGA CASSANDRA ===")
    print(f"Lotes nuevos: {summary['batches_loaded']} (ya cargados antes: {summary['batches_already_loaded']})")
    print(f"Escuchas escritas en esta ejecución: {summary['rows_loaded']:,}")
    print(f"Líneas omitidas: {summary['rows_skipped']:,}")
    print(f"Duplicadas dentro del lote: {summary['duplicates']:,}")
    print(f"Escuchas incluidas en los agregados: {summary['listens_in_aggregates']:,}")
    print(f"Tiempo total: {time.perf_counter() - started:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
