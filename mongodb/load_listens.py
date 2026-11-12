"""
Carga masiva de escuchas de ListenBrainz en MongoDB.
Permite ejecutar la ingesta por línea de comandos o invocarse programáticamente desde Airflow.
"""

import argparse
import json
from pathlib import Path
from pymongo.errors import PyMongoError

from mongodb.connection import get_client, get_collection, ensure_indexes
from mongodb.app.services.import_service import import_file


def load_to_mongodb(
    source_path: Path | str,
    limit: int = 50000,
    batch_size: int = 2000,
    state_path: Path | str | None = None,
    dry_run: bool = False,
    progress: bool = True,
):
    """
    Función programática para cargar escuchas en MongoDB.
    Diseñada para ser llamada por el DAG de Apache Airflow o scripts de automatización.
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Archivo de origen no encontrado: {source}")

    if state_path is None:
        state_path = Path("data/import_state_mongo.sqlite3")

    with get_client() as client:
        collection = get_collection(client)
        ensure_indexes(collection)

        print(f"Iniciando carga a MongoDB desde {source} (límite: {limit}, lote: {batch_size})...")
        result = import_file(
            collection=collection,
            source=source,
            state_path=state_path,
            limit=limit,
            batch_size=batch_size,
            target=limit,
            dry_run=dry_run,
            progress=progress,
        )
        print("Carga a MongoDB finalizada con éxito:")
        print(json.dumps(result, indent=2))
        return result


def main():
    parser = argparse.ArgumentParser(description="Cargador masivo de ListenBrainz a MongoDB")
    parser.add_argument("--source", type=Path, default=Path("data/processed/listens_full.jsonl"), help="Ruta al archivo JSONL")
    parser.add_argument("--limit", type=int, default=50000, help="Cantidad de registros a cargar (mínimo 50,000 según rúbrica)")
    parser.add_argument("--batch-size", type=int, default=2000, help="Tamaño de cada lote de inserción")
    parser.add_argument("--dry-run", action="store_true", help="Validar sin insertar en la base de datos")
    parser.add_argument("--full", action="store_true", help="Cargar el archivo completo sin límite")
    args = parser.parse_args()

    limit = 2**63 - 1 if args.full else args.limit
    load_to_mongodb(
        source_path=args.source,
        limit=limit,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        progress=True,
    )


if __name__ == "__main__":
    try:
        main()
    except (PyMongoError, OSError, ValueError) as error:
        raise SystemExit(f"Error durante la carga a MongoDB: {error}")
