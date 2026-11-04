from contextlib import closing
from collections import Counter, defaultdict
from itertools import combinations, groupby
import hashlib
import json
import math
import sqlite3

import networkx as nx

from database import DATABASE, DATASET, PREPARED, connect
from load import metadata


PARAMETERS = {
    "top_artists": 500,
    "min_audience": 20,
    "user_top": 20,
    "min_common": 10,
    "min_jaccard": 0.05,
    "neighbors": 10,
    "resolution": 1.0,
    "seed": 42
}


def diversity(counts):
    values = [v for v in counts if v > 0]
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    total = sum(values)
    return -sum((v / total) * math.log(v / total) for v in values) / math.log(len(values))


def affinity_graph(audiences, params):
    candidates = defaultdict(list)
    for left, right in combinations(sorted(audiences), 2):
        common = len(audiences[left] & audiences[right])
        if common < params['min_common']:
            continue
        union = len(audiences[left]) + len(audiences[right]) - common
        score = common / union
        if score >= params['min_jaccard']:
            candidates[left].append((right, score, common))
            candidates[right].append((left, score, common))
    retained = {}
    for artist in sorted(candidates):
        for neighbor, score, common in sorted(candidates[artist], key=lambda x: (-x[1], -x[2], x[0]))[:params['neighbors']]:
            retained[tuple(sorted((artist, neighbor)))] = (score, common)
    graph = nx.Graph()

    for (left, right), (score, common) in sorted(retained.items()):
        graph.add_edge(left, right, weight=score, common=common)
    return graph


def participation(graph, membership, artist):
    weights = Counter()
    for neighbor in graph.neighbors(artist):
        weights[membership[neighbor]] += graph[artist][neighbor]["weight"]
    total = sum(weights.values())
    return 1 - sum((value / total) ** 2 for value in weights.values()) if total else 0.0


def select_audiences(db, params):
    selected = db.execute("""
        SELECT artist,count(*) AS audience FROM user_artists GROUP BY artist
        HAVING count(*) >= ? ORDER BY audience DESC,artist LIMIT ?
    """, (params['min_audience'], params['top_artists'])).fetchall()
    db.execute("CREATE TEMP TABLE IF NOT EXISTS selected (artist TEXT PRIMARY KEY)")
    db.execute("DELETE FROM selected")
    db.executemany("INSERT INTO selected VALUES (?)", ((name,) for name, _ in selected))
    audiences = {name: set() for name, _ in selected}
    ranked = db.execute("""
        SELECT user,artist FROM (
          SELECT ua.user,ua.artist,ROW_NUMBER() OVER (
            PARTITION BY ua.user ORDER BY ua.count DESC,ua.artist) AS rank
          FROM user_artists ua JOIN selected s ON ua.artist=s.artist
        ) WHERE rank<=? ORDER BY user,artist
    """, (params['user_top'],))
    for user, artist in ranked:
        audiences[artist].add(user)
    return audiences


def detect_communities(graph, params):
    partition = nx.community.louvain_communities(graph, weight="weight", resolution=params['resolution'],
                                                seed=params['seed']) if graph.number_of_edges() else []
    partition = sorted((sorted(c) for c in partition), key=lambda c: tuple(c))
    membership = {artist: i for i, community in enumerate(partition) for artist in community}
    modularity = nx.community.modularity(graph, partition, weight="weight", resolution=params['resolution']) if partition else None
    return partition, membership, modularity


def analysis_identity(meta, params):
    identity = json.dumps({"source": meta["source_sha256"], "dataset": meta["dataset"],
                           "parameters": params, "algorithm_version": 1,
                           "networkx_version": nx.__version__}, sort_keys=True)
    analysis_id = f"{meta['dataset']}:{hashlib.sha256(identity.encode()).hexdigest()[:16]}"
    return analysis_id


def compute_indicators(db, meta, graph, membership, modularity):
    reach = defaultdict(set)
    covered = classified_users = classified_listens = 0
    diversities = []
    rows = db.execute("SELECT user,artist,count FROM user_artists ORDER BY user,artist")
    for user, entries in groupby(rows, key=lambda r: r[0]):
        preferences = {artist: count for _, artist, count in entries}
        counts = Counter()
        for artist, count in preferences.items():
            if artist in membership:
                community = membership[artist]
                counts[community] += count
                reach[community].add(user)
        value = diversity(counts.values())
        if value is not None:
            classified_users += 1
            classified_listens += sum(counts.values())
            diversities.append(value)

        has_recommendation = any(neighbor not in preferences for known in preferences if known in graph
                                 for neighbor in graph.neighbors(known))
        covered += has_recommendation

    kpis = {"modularidad": modularity, "usuarios_lote": meta["users"],
                     "usuarios_con_recomendaciones": covered,
                     "cobertura_recomendaciones": covered / meta["users"] if meta["users"] else 0.0,
                     "usuarios_con_escuchas_clasificadas": classified_users,
                     "escuchas_clasificadas": classified_listens,
                     "proporcion_escuchas_clasificadas": classified_listens / meta["rows"],
                     "diversidad_media_usuarios_clasificados": sum(diversities) / len(diversities) if diversities else None}
    return reach, kpis


def build_result(meta, params, audiences, graph, partition, membership, reach, kpis):
    analysis_id = analysis_identity(meta, params)
    community_ids = {i: f"{analysis_id}:c{i + 1}" for i in range(len(partition))}
    edges = [{"left": a, "right": b, "jaccard": graph[a][b]["weight"], "common": graph[a][b]["common"],
              "audience_left": len(audiences[a]), "audience_right": len(audiences[b])}
             for a, b in sorted(tuple(sorted((a, b))) for a, b in graph.edges())]
    communities = [{"id": community_ids[i], "numero": i + 1, "artistas": len(names),
                    "audiencia": len(reach[i]), "representantes": sorted(names,
                        key=lambda n: (-graph.degree(n, weight="weight"), n))[:5]}
                   for i, names in enumerate(partition)]
    memberships = [{"artist": artist, "community": community_ids[i],
                    "bridge": participation(graph, membership, artist)}
                   for artist, i in sorted(membership.items())]
    return {"id": analysis_id, "dataset": meta["dataset"], "source_sha256": meta["source_sha256"],
            "parameters": params, "networkx_version": nx.__version__,
            "selected_artists": len(audiences), "connected_artists": len(graph),
            "isolated_artists": len(audiences) - len(graph), "edges": edges,
            "communities": communities, "memberships": memberships,
            "kpis": kpis}


def analyze(db, meta, params=PARAMETERS):
    audiences = select_audiences(db, params)
    graph = affinity_graph(audiences, params)
    partition, membership, modularity = detect_communities(graph, params)
    reach, kpis = compute_indicators(db, meta, graph, membership, modularity)
    return build_result(meta, params, audiences, graph, partition, membership, reach, kpis)


def save_analysis(tx, result):
    dataset, analysis_id = result["dataset"], result["id"]
    base = tx.run("MATCH (l:Lote {id:$dataset,estado:'completo'}) RETURN l.source_sha256 AS sha", dataset=dataset).single()
    if not base or base["sha"] != result["source_sha256"]:
        raise ValueError("Primero carga el mismo dataset en Neo4j")
    tx.run("""
        MERGE (a:Analisis {id:$id})
        SET a.lote=$dataset,a.parametros=$settings,a.source_sha256=$sha,a.networkx_version=$version
    """, id=analysis_id, dataset=dataset, settings=json.dumps(result["parameters"], sort_keys=True),
           sha=result["source_sha256"], version=result["networkx_version"]).consume()
    tx.run("MATCH ()-[r:AFIN_A {analisis:$id}]->() DELETE r", id=analysis_id).consume()
    tx.run("MATCH (c:Comunidad {analisis:$id}) DETACH DELETE c", id=analysis_id).consume()
    total = tx.run("""
        UNWIND $rows AS f
        MATCH (a:Artista {nombre:f.left}),(b:Artista {nombre:f.right})
        MERGE (a)-[r:AFIN_A {analisis:$id}]->(b)
        SET r.jaccard=f.jaccard,r.usuarios_comunes=f.common,
            r.audiencia_origen=f.audience_left,r.audiencia_destino=f.audience_right
        RETURN count(r) AS cantidad
    """, rows=result["edges"], id=analysis_id).single()["cantidad"]
    if total != len(result["edges"]):
        raise ValueError("Faltan artistas para construir las afinidades")
    tx.run("""
        UNWIND $rows AS f MERGE (c:Comunidad {id:f.id})
        SET c.analisis=$id,c.numero=f.numero,c.artistas=f.artistas,c.audiencia=f.audiencia,
            c.representantes=f.representantes
    """, rows=result["communities"], id=analysis_id).consume()
    tx.run("""
        UNWIND $rows AS f
        MATCH (a:Artista {nombre:f.artist}),(c:Comunidad {id:f.community})
        MERGE (a)-[r:PERTENECE_A {analisis:$id}]->(c) SET r.puente=f.bridge
    """, rows=result["memberships"], id=analysis_id).consume()
    tx.run("""
        MATCH (l:Lote {id:$dataset}),(a:Analisis {id:$id})
        OPTIONAL MATCH (l)-[anterior:ANALISIS_ACTIVO]->() DELETE anterior
        SET a += $kpis,a.estado='completo',a.artistas_seleccionados=$selected,
            a.artistas_conectados=$connected,a.artistas_aislados=$isolated
        MERGE (l)-[:ANALISIS_ACTIVO]->(a)
    """, dataset=dataset, id=analysis_id, kpis=result["kpis"],
           selected=result["selected_artists"], connected=result["connected_artists"],
           isolated=result["isolated_artists"]).consume()


def main():
    with closing(sqlite3.connect(f"{PREPARED.as_uri()}?mode=ro", uri=True)) as db:
        meta = metadata(db)
        if meta["dataset"] != DATASET:
            raise ValueError("La preparación pertenece a otro lote")
        result = analyze(db, meta)
    with connect() as driver, driver.session(database=DATABASE) as session:
        session.execute_write(save_analysis, result)
    destination = PREPARED.parent / "analysis.json"
    temporary = destination.with_suffix(".json.part")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(destination)
    print(f"{len(result['communities'])} comunidades; {len(result['edges'])} afinidades")
    print(f"Cobertura de recomendaciones: {result['kpis']['cobertura_recomendaciones']:.2%}")


if __name__ == "__main__":
    main()
