import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/processed/listens_full.jsonl"
PREPARED = ROOT / "data/neo4j/prepared.sqlite"
DATASET = "listenbrainz-2746"
load_dotenv(ROOT / ".env")
DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")


def connect():
    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "cambia-esta-clave-local")),
    )
    driver.verify_connectivity()
    return driver
