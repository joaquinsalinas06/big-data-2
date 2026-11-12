"""
Operaciones CRUD directas sobre MongoDB para la colección de reproducciones (listens).
Permite demostrar en vivo la creación, consulta, actualización y eliminación de documentos
sin necesidad de levantar el servidor web FastAPI.
"""

import argparse
import time
from bson import ObjectId
from bson.errors import InvalidId

from databases.mongodb.connection import get_client, get_collection, ensure_indexes

DEMO_USER_NAME = "__demo_user_test__"


def parse_id(listen_id):
    """Convierte un string a ObjectId si es válido, de lo contrario devuelve el id original."""
    if isinstance(listen_id, ObjectId):
        return listen_id
    if isinstance(listen_id, str) and ObjectId.is_valid(listen_id):
        return ObjectId(listen_id)
    return listen_id


def insert_listen(
    collection,
    user_name: str,
    timestamp: int,
    track_name: str,
    artist_name: str,
    release_name: str | None = None,
    recording_msid: str | None = None,
    is_demo: bool = False,
):
    """Crea una nueva reproducción en MongoDB y retorna su _id."""
    document = {
        "user_name": user_name,
        "timestamp": timestamp,
        "track_metadata": {
            "track_name": track_name,
            "artist_name": artist_name,
            "release_name": release_name,
            "additional_info": {},
        },
    }
    if recording_msid:
        document["recording_msid"] = recording_msid
    if is_demo:
        document["es_prueba"] = True

    result = collection.insert_one(document)
    return result.inserted_id


def get_listen(collection, listen_id):
    """Consulta un documento por su identificador único."""
    target_id = parse_id(listen_id)
    return collection.find_one({"_id": target_id})


def get_user_listens(collection, user_name: str, limit: int = 10):
    """Consulta las reproducciones más recientes de un usuario."""
    return list(
        collection.find({"user_name": user_name})
        .sort([("timestamp", -1), ("_id", -1)])
        .limit(limit)
    )


def update_listen(collection, listen_id, changes: dict):
    """
    Actualiza campos específicos de un documento.
    Ejemplo changes: {"track_metadata.track_name": "Nuevo título"}
    """
    target_id = parse_id(listen_id)
    result = collection.update_one({"_id": target_id}, {"$set": changes})
    return result.matched_count > 0


def delete_listen(collection, listen_id):
    """Elimina un documento por su identificador único."""
    target_id = parse_id(listen_id)
    result = collection.delete_one({"_id": target_id})
    return result.deleted_count > 0


def step(title: str, pause: bool = False):
    if pause:
        input("\n[Presiona Enter para continuar] ")
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def show_document(doc):
    if doc is None:
        return "  (documento no encontrado)"
    track = doc.get("track_metadata", {})
    t_name = track.get("track_name", "Desconocido")
    a_name = track.get("artist_name", "Desconocido")
    r_name = track.get("release_name") or "Sin álbum"
    return (
        f"  ID: {doc.get('_id')}\n"
        f"  Usuario: {doc.get('user_name')}\n"
        f"  Fecha (timestamp): {doc.get('timestamp')}\n"
        f"  Canción: {a_name} - {t_name} (Álbum: {r_name})"
    )


def run_demo(collection, pause: bool = False):
    print("=== DEMO INTERACTIVA CRUD: MONGODB ===")
    print("Base de datos: MongoDB (Colección 'listens')")

    # 1. CREATE
    step("1. CREATE — Insertar un nuevo documento en MongoDB", pause)
    now_ts = int(time.time())
    inserted_id = insert_listen(
        collection=collection,
        user_name=DEMO_USER_NAME,
        timestamp=now_ts,
        track_name="Cancion de Prueba Big Data",
        artist_name="Artista Demostracion",
        release_name="Album Proyecto II",
        is_demo=True,
    )
    print(f"Documento insertado exitosamente con ID: {inserted_id}")

    # 2. READ
    step("2. READ — Consultar el documento recién insertado", pause)
    retrieved = get_listen(collection, inserted_id)
    print("Resultado de la consulta por ID:")
    print(show_document(retrieved))

    # 3. UPDATE
    step("3. UPDATE — Modificar campos del documento", pause)
    print("Actualizando nombre de canción y álbum...")
    updated = update_listen(
        collection,
        inserted_id,
        {
            "track_metadata.track_name": "Cancion de Prueba (Version Remasterizada)",
            "track_metadata.release_name": "Album Proyecto II (Deluxe Edition)",
        },
    )
    print(f"¿Actualización exitosa?: {updated}")

    doc_after_update = get_listen(collection, inserted_id)
    print("\nDocumento después del UPDATE:")
    print(show_document(doc_after_update))

    # 4. DELETE
    step("4. DELETE — Eliminar el documento de prueba", pause)
    deleted = delete_listen(collection, inserted_id)
    print(f"¿Eliminación exitosa?: {deleted}")

    doc_after_delete = get_listen(collection, inserted_id)
    print("\nVerificando que ya no exista:")
    print(show_document(doc_after_delete))

    step("CRUD COMPLETADO", False)
    print("Todas las operaciones básicas sobre MongoDB fueron demostradas con éxito.")


def main():
    parser = argparse.ArgumentParser(description="CRUD interactivo en MongoDB para ListenBrainz")
    parser.add_argument("--pause", action="store_true", help="Pausa entre pasos para demostración en video")
    args = parser.parse_args()

    client = get_client()
    try:
        client.admin.command("ping")
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        print("Asegúrate de iniciar el contenedor con: docker compose -f mongodb/docker-compose.yml up -d")
        return

    collection = get_collection(client)
    ensure_indexes(collection)
    run_demo(collection, pause=args.pause)


if __name__ == "__main__":
    main()
