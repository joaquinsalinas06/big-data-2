from database import DATABASE, DATASET, connect
from graph import crud, queries

USER_ID = 20
ARTIST = "Motörhead"


def show(title, result):
    print(f"\n{title}")
    if isinstance(result, list):
        for row in result:
            print(row)
        if not result:
            print("Sin resultados para estos parámetros.")
    else:
        print(result)


def main():
    with connect() as driver, driver.session(database=DATABASE) as session:
        state = session.run("""
            MATCH (l:Lote {id:$dataset,estado:'completo'})
                  -[:ANALISIS_ACTIVO]->(:Analisis {estado:'completo'})
            RETURN l.id AS lote
        """, dataset=DATASET).single()
        if not state:
            raise ValueError("Ejecuta primero load.py y analyze.py")

        show("Artistas con más oyentes", session.execute_read(queries.list_artists, DATASET))
        show("Canciones del artista", session.execute_read(queries.get_tracks, DATASET, ARTIST))
        show("Filtrar escuchas", session.execute_read(queries.filter_listens, DATASET, USER_ID))
        show("Buscar artistas", session.execute_read(queries.search_artists, DATASET, "radio"))
        show("Contar escuchas", session.execute_read(queries.count_listens, DATASET))
        show("Recomendar artistas", session.execute_read(queries.recommend_artists, DATASET, USER_ID))
        show("Recomendar canciones", session.execute_read(queries.recommend_tracks, DATASET, USER_ID))
        show("Comunidades", session.execute_read(queries.get_communities, DATASET))
        show("Artistas puente", session.execute_read(queries.get_bridge_artists, DATASET))
        show("Diversidad", session.execute_read(queries.get_user_diversity, DATASET, USER_ID))
        show("Camino entre artistas", session.execute_read(queries.find_artist_path, DATASET, ARTIST, "Judas Priest"))
        show("Indicadores", session.execute_read(queries.get_indicators, DATASET))

        try:
            show("Crear nodos", session.execute_write(crud.create_nodes))
            show("Crear relación", session.execute_write(crud.create_relationship))
            show("Actualizar propiedad", session.execute_write(crud.update_properties, 3))
            show("Consultar el cambio", session.execute_read(crud.get_listens))
            show("Eliminar relación", session.execute_write(crud.delete_relationship))
        finally:
            show("Eliminar nodos del grupo", session.execute_write(crud.delete_nodes))
    print("\nConexión cerrada.")


if __name__ == "__main__":
    main()
