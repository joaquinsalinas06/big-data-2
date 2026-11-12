"""
Consultas analíticas en Neo4j (Cypher) para ListenBrainz.
Ejecuta y muestra consultas del grafo: comunidades, recomendaciones, diversidad e indicadores.
"""

import argparse
from databases.neo4j.connection import DATABASE, DATASET, connect
from databases.neo4j.graph import queries


def show(title, result):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
    if isinstance(result, list):
        for row in result[:15]:  # Muestra primeros 15 resultados
            print(row)
        if len(result) > 15:
            print(f"... y {len(result) - 15} registros más.")
        if not result:
            print("Sin resultados.")
    else:
        print(result)


def run_queries(session, dataset=DATASET, user_id=20, artist="Motörhead"):
    state = session.run("""
        MATCH (l:Lote {id:$dataset,estado:'completo'})
              -[:ANALISIS_ACTIVO]->(:Analisis {estado:'completo'})
        RETURN l.id AS lote
    """, dataset=dataset).single()
    if not state:
        print("Aviso: Para ver resultados analíticos completos, ejecuta primero:")
        print("  python -m databases.neo4j.loader")
        print("  python -m databases.neo4j.analyze")
        return

    show("Artistas con más oyentes", session.execute_read(queries.list_artists, dataset))
    show(f"Canciones del artista '{artist}'", session.execute_read(queries.get_tracks, dataset, artist))
    show(f"Filtrar escuchas del usuario {user_id}", session.execute_read(queries.filter_listens, dataset, user_id))
    show("Buscar artistas con 'radio'", session.execute_read(queries.search_artists, dataset, "radio"))
    show("Total de escuchas en el lote", session.execute_read(queries.count_listens, dataset))
    show(f"Recomendar artistas al usuario {user_id}", session.execute_read(queries.recommend_artists, dataset, user_id))
    show(f"Recomendar canciones al usuario {user_id}", session.execute_read(queries.recommend_tracks, dataset, user_id))
    show("Comunidades detectadas", session.execute_read(queries.get_communities, dataset))
    show("Artistas puente (con mayor intermediación)", session.execute_read(queries.get_bridge_artists, dataset))
    show(f"Diversidad de escucha del usuario {user_id}", session.execute_read(queries.get_user_diversity, dataset, user_id))
    show("Indicadores analíticos del grafo", session.execute_read(queries.get_indicators, dataset))


def main():
    parser = argparse.ArgumentParser(description="Consultas analíticas de grafo en Neo4j")
    parser.add_argument("--user-id", type=int, default=20, help="ID de usuario para recomendaciones")
    parser.add_argument("--artist", default="Motörhead", help="Artista de búsqueda")
    args = parser.parse_args()

    try:
        with connect() as driver, driver.session(database=DATABASE) as session:
            run_queries(session, user_id=args.user_id, artist=args.artist)
    except Exception as e:
        print(f"Error al conectar o consultar Neo4j: {e}")


if __name__ == "__main__":
    main()
