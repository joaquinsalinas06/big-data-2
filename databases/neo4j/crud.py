"""
Operaciones CRUD interactivas en Neo4j (Cypher) para ListenBrainz.
Demuestra en consola las operaciones básicas sobre nodos y relaciones:
1. CREATE: Crear nodo Usuario y nodo Canción, y crear relación :ESCUCHO.
2. READ: Consultar la relación y propiedades en el grafo.
3. UPDATE: Actualizar propiedades de la relación (e.g. cantidad de reproducciones).
4. DELETE: Eliminar la relación y los nodos de prueba.
"""

import argparse
from databases.neo4j.connection import DATABASE, connect
from databases.neo4j.graph import crud


def step(title: str, pause: bool = False):
    if pause:
        input("\n[Presiona Enter para continuar] ")
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def run_demo(driver, pause: bool = False):
    print("=== DEMO INTERACTIVA CRUD: NEO4J (CYPHER) ===")
    print(f"Base de datos: Neo4j (Base: '{DATABASE}')")

    with driver.session(database=DATABASE) as session:
        # Asegurar limpieza previa
        session.execute_write(crud.delete_nodes)

        # 1. CREATE NODES
        step("1. CREATE (Nodos) — Crear nodo Usuario y nodo Canción", pause)
        nodes_created = session.execute_write(crud.create_nodes)
        print("Nodos creados exitosamente:")
        print(f"  Usuario ID: {nodes_created.get('usuario')}")
        print(f"  Canción Título: '{nodes_created.get('cancion')}'")

        # 1. CREATE RELATIONSHIP
        step("1b. CREATE (Relación) — Crear relación [:ESCUCHO] entre Usuario y Canción", pause)
        rel_created = session.execute_write(crud.create_relationship)
        print("Relación creada:")
        print(f"  Tipo: :{rel_created.get('relacion')} (cantidad inicial: {rel_created.get('cantidad')})")

        # 2. READ
        step("2. READ — Consultar la relación creada en el grafo", pause)
        listens = session.execute_read(crud.get_listens)
        print("Lectura del grafo:")
        for row in listens:
            print(f"  (Usuario {row['usuario']})-[:ESCUCHO {{cantidad: {row['cantidad']}}}]->(Cancion '{row['cancion']}')")

        # 3. UPDATE
        step("3. UPDATE — Actualizar propiedad de la relación (cantidad = 5)", pause)
        updated = session.execute_write(crud.update_properties, 5)
        print(f"Propiedad actualizada en Neo4j. Nueva cantidad: {updated.get('cantidad')}")

        doc_after_update = session.execute_read(crud.get_listens)
        print("\nVerificando datos actualizados:")
        for row in doc_after_update:
            print(f"  (Usuario {row['usuario']})-[:ESCUCHO {{cantidad: {row['cantidad']}}}]->(Cancion '{row['cancion']}')")

        # 4. DELETE
        step("4. DELETE — Eliminar la relación y los nodos de prueba", pause)
        rel_deleted = session.execute_write(crud.delete_relationship)
        print(f"Relaciones eliminadas: {rel_deleted}")
        nodes_deleted = session.execute_write(crud.delete_nodes)
        print(f"Nodos eliminados: {nodes_deleted}")

        doc_after_delete = session.execute_read(crud.get_listens)
        print("\nVerificando ausencia en el grafo:")
        if not doc_after_delete:
            print("  (El grafo de prueba ha sido completamente limpiado)")
        else:
            print(f"  Registros restantes: {doc_after_delete}")

        step("CRUD COMPLETADO EN NEO4J", False)
        print("Todas las operaciones básicas sobre Neo4j fueron demostradas con éxito.")


def main():
    parser = argparse.ArgumentParser(description="CRUD interactivo en Neo4j para ListenBrainz")
    parser.add_argument("--pause", action="store_true", help="Pausa entre pasos para demostración en video")
    args = parser.parse_args()

    try:
        with connect() as driver:
            run_demo(driver, pause=args.pause)
    except Exception as e:
        print(f"Error conectando a Neo4j: {e}")
        print("Asegúrate de iniciar el contenedor con: docker compose -f databases/neo4j/docker-compose.yml up -d")


if __name__ == "__main__":
    main()
