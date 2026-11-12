import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "listenbrainz_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "listens")


def get_client(uri: str | None = None) -> MongoClient:
    """Retorna un cliente MongoClient conectado con timeout de selección de servidor."""
    return MongoClient(uri or MONGO_URI, serverSelectionTimeoutMS=5000)


def get_database(client: MongoClient | None = None, name: str | None = None):
    """Retorna la base de datos de databases.mongodb."""
    cli = client or get_client()
    return cli[name or DATABASE_NAME]


def get_collection(client: MongoClient | None = None, collection_name: str | None = None):
    """Retorna la colección de reproducciones (listens)."""
    db = get_database(client)
    return db[collection_name or COLLECTION_NAME]


def ensure_indexes(collection):
    """Crea los índices recomendados para acelerar las consultas."""
    for keys in [
        [("timestamp", -1), ("_id", -1)],
        [("user_name", 1), ("timestamp", -1), ("_id", -1)],
        [("track_metadata.artist_name", 1), ("timestamp", -1), ("_id", -1)],
    ]:
        collection.create_index(keys)
