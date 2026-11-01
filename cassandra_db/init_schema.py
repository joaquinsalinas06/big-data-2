"""Crea el keyspace y las tablas definidas en schema.cql.

Uso: python -m cassandra_db.init_schema [--reset]
"""
import argparse
from pathlib import Path

from cassandra_db.connection import KEYSPACE, get_session

SCHEMA_FILE = Path(__file__).with_name("schema.cql")


def read_statements(path=SCHEMA_FILE):
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("--")]
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def create_schema(session, reset=False):
    if reset:
        session.execute(f"DROP KEYSPACE IF EXISTS {KEYSPACE}")
    for statement in read_statements():
        session.execute(statement)


def main():
    parser = argparse.ArgumentParser(description="Crear el esquema de Cassandra")
    parser.add_argument("--reset", action="store_true", help="Borra el keyspace y todos sus datos antes de crearlo")
    args = parser.parse_args()

    session = get_session(keyspace=None)
    try:
        create_schema(session, reset=args.reset)
        tables = session.execute(
            "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", (KEYSPACE,)
        )
        print(f"Keyspace {KEYSPACE} listo. Tablas: {', '.join(row['table_name'] for row in tables)}")
    finally:
        session.cluster.shutdown()


if __name__ == "__main__":
    main()
