"""Pipeline Music DNA: del dump de ListenBrainz a MongoDB, Cassandra, Neo4j y los KPIs.

Las tareas solo orquestan: la lógica de carga y análisis está en databases/ y aquí se llama
tal cual. Los imports de databases.* van dentro de cada tarea para que el scheduler pueda
leer el DAG rápido aunque una base no esté disponible.
"""
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable

ROOT = Path("/opt/airflow")
DATASET_PATH = ROOT / "data/processed/listens_full.jsonl"
REPORT_DIR = ROOT / "data/airflow"
MONGO_STATE = REPORT_DIR / "mongo_state.sqlite3"
VALIDATION_REPORT = REPORT_DIR / "validacion.json"
KPIS_LATEST = REPORT_DIR / "kpis_latest.json"
KPI_COLLECTION = "kpi_runs"
SERIES_DAYS = 30

# Valores por defecto; se cambian en Admin > Variables sin tocar el código.
DEFAULT_MONGO_LIMIT = 100_000
DEFAULT_MONGO_BATCH_SIZE = 2_000
# El id de cada lote de Cassandra depende de este tamaño: si se cambia entre corridas,
# los lotes ya cargados no se reconocen y los agregados cuentan dos veces.
DEFAULT_CASSANDRA_BATCH_SIZE = 500_000

log = logging.getLogger("airflow.task")


def int_variable(name, default):
    return int(Variable.get(name, default_var=default))


def run_command(args):
    """Ejecuta un comando, copia su salida al log de la tarea y la devuelve."""
    log.info("Ejecutando: %s", " ".join(str(arg) for arg in args))
    process = subprocess.Popen(
        [str(arg) for arg in args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    lines = []
    for line in process.stdout:
        line = line.rstrip()
        log.info(line)
        lines.append(line)
    return process.wait(), lines


def count_lines(path):
    lines = 0
    with path.open("rb") as stream:
        while chunk := stream.read(16 * 1024 * 1024):
            lines += chunk.count(b"\n")
    return lines


def write_json(path, content):
    """Escribe a un temporal y lo renombra, así quien lee nunca ve un archivo a medias."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(content, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)


def parse_validation(lines):
    """Toma los valores que imprime scripts/validate_dataset.py."""
    labels = {
        "Registros leídos": "registros",
        "Registros válidos": "validos",
        "Registros inválidos": "invalidos",
        "Registros sin user_id entero": "sin_user_id",
        "Registros sin recording_msid": "sin_recording_msid",
    }
    report = {}
    for line in lines:
        label, _, value = line.partition(":")
        value = value.strip()
        if label in labels:
            report[labels[label]] = int(value.replace(",", ""))
        elif label.startswith("Fecha mínima"):
            report["fecha_minima"] = line.split(": ", 1)[1]
        elif label.startswith("Fecha máxima"):
            report["fecha_maxima"] = line.split(": ", 1)[1]
    return report


def as_float(value, digits=2):
    return round(float(value), digits) if value is not None else None


DOC_MD = """
### Pipeline Music DNA (ListenBrainz)

Lleva el incremental 2746 de ListenBrainz (4 855 809 escuchas en JSON Lines) a las tres bases
del proyecto y calcula los KPIs que lee el dashboard.

1. `extraer_datos`: usa el JSONL si ya existe; si no, lo descarga y verifica con `scripts/download_dataset.sh --extract`.
2. `validar_y_limpiar`: corre `scripts/validate_dataset.py` y guarda `data/airflow/validacion.json`.
   La limpieza por registro (esquema, duplicados) la hace cada loader al cargar.
3. `cargar_mongodb`: agrega el siguiente bloque de documentos (Variable `music_dna_mongo_limit`).
4. `cargar_cassandra`: carga un lote nuevo de 500 000 líneas y recalcula los agregados.
5. `cargar_neo4j`: carga el grafo completo una sola vez; si el lote ya está completo, no hace nada.
6. `generar_kpis`: análisis de comunidades en Neo4j, 5 KPIs y snapshot en Mongo (`kpi_runs`)
   y en `data/airflow/kpis_latest.json`.

Cada corrida diaria agrega datos nuevos en Mongo y Cassandra, así se simula la llegada
incremental de escuchas. Documentación completa en `docs/airflow.md`.
"""


@dag(
    dag_id="music_dna_pipeline",
    description="ListenBrainz -> MongoDB, Cassandra y Neo4j, con KPIs para el dashboard",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 11, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "music-dna",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(hours=2),
    },
    tags=["music-dna", "listenbrainz", "big-data"],
    doc_md=DOC_MD,
)
def music_dna_pipeline():

    @task
    def extraer_datos():
        if DATASET_PATH.is_file() and DATASET_PATH.stat().st_size > 0:
            log.info("El dataset ya está en %s; no se descarga de nuevo", DATASET_PATH)
            downloaded = False
        else:
            log.info("No existe %s; se descarga el incremental 2746 de ListenBrainz", DATASET_PATH)
            code, _ = run_command(["bash", ROOT / "scripts/download_dataset.sh", "--extract"])
            if code != 0:
                raise AirflowException(f"download_dataset.sh terminó con código {code}")
            downloaded = True

        size = DATASET_PATH.stat().st_size
        lines = count_lines(DATASET_PATH)
        log.info("Dataset: %s líneas, %.1f MB", f"{lines:,}", size / 1e6)
        return {"ruta": str(DATASET_PATH), "bytes": size, "lineas": lines, "descargado": downloaded}

    @task
    def validar_y_limpiar(extraccion: dict, **context):
        code, lines = run_command([sys.executable, ROOT / "scripts/validate_dataset.py", "--file", extraccion["ruta"]])
        report = parse_validation(lines)
        report.update({
            "archivo": extraccion["ruta"],
            "valido": code == 0,
            "run_id": context["run_id"],
            "validado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        write_json(VALIDATION_REPORT, report)
        log.info("Reporte de validación en %s", VALIDATION_REPORT)
        if code != 0:
            raise AirflowException(f"El dataset no pasó la validación (código {code}); ver {VALIDATION_REPORT}")
        return {key: report.get(key) for key in ("registros", "invalidos", "fecha_minima", "fecha_maxima")}

    @task
    def cargar_mongodb(validacion: dict):
        from databases.mongodb.loader import load_to_mongodb

        limit = int_variable("music_dna_mongo_limit", DEFAULT_MONGO_LIMIT)
        batch_size = int_variable("music_dna_mongo_batch_size", DEFAULT_MONGO_BATCH_SIZE)
        result = load_to_mongodb(DATASET_PATH, limit=limit, batch_size=batch_size,
                                 state_path=MONGO_STATE, progress=False)
        log.info("Mongo: %s insertados, %s duplicados, %s inválidos; la colección tiene %s documentos",
                 f"{result['inserted']:,}", f"{result['duplicates']:,}", f"{result['invalid']:,}", f"{result['total']:,}")
        if result["source_exhausted"]:
            log.info("Se llegó al final del archivo: no quedan escuchas nuevas para Mongo")
        return {
            "insertados": result["inserted"],
            "duplicados": result["duplicates"],
            "invalidos": result["invalid"],
            "total_coleccion": result["total"],
            "offset_bytes": result["offset"],
            "archivo_agotado": result["source_exhausted"],
            "segundos": result["elapsed_seconds"],
        }

    @task
    def cargar_cassandra(validacion: dict):
        from databases.cassandra.connection import KEYSPACE, get_session
        from databases.cassandra.init_schema import create_schema
        from databases.cassandra.loader import load_listens

        batch_size = int_variable("music_dna_cassandra_batch_size", DEFAULT_CASSANDRA_BATCH_SIZE)
        session = get_session(keyspace=None)
        try:
            create_schema(session)  # CREATE ... IF NOT EXISTS, se puede repetir
            session.set_keyspace(KEYSPACE)
            summary = load_listens(session, DATASET_PATH, batch_size=batch_size, max_batches=1)
        finally:
            session.cluster.shutdown()

        if not summary["batches_loaded"]:
            log.info("No quedan lotes nuevos: solo se recalcularon los agregados")
        log.info("Cassandra: %s lote(s) nuevo(s), %s ya cargados, %s escuchas en los agregados",
                 summary["batches_loaded"], summary["batches_already_loaded"], f"{summary['listens_in_aggregates']:,}")
        return {
            "lotes_nuevos": summary["batches_loaded"],
            "lotes_previos": summary["batches_already_loaded"],
            "escuchas_escritas": summary["rows_loaded"],
            "omitidas": summary["rows_skipped"],
            "duplicadas": summary["duplicates"],
            "escuchas_en_agregados": summary["listens_in_aggregates"],
        }

    @task
    def cargar_neo4j(validacion: dict):
        import sqlite3
        from contextlib import closing

        from databases.neo4j.connection import DATABASE, DATASET, PREPARED, SOURCE, connect
        from databases.neo4j.graph import queries
        from databases.neo4j.loader import load_data, metadata, prepare

        # Mismo flujo que main() de databases/neo4j/loader.py, más el control del lote ya cargado.
        if PREPARED.exists():
            log.info("Usando la preparación existente %s", PREPARED)
        else:
            log.info("Preparando %s a partir del archivo completo", PREPARED)
            prepare(SOURCE, PREPARED, DATASET)

        with closing(sqlite3.connect(PREPARED)) as db:
            meta = metadata(db)
            if meta["dataset"] != DATASET:
                raise AirflowException(f"La preparación es del lote {meta['dataset']}, se esperaba {DATASET}")
            with connect() as driver, driver.session(database=DATABASE) as session:
                lote = session.run("MATCH (l:Lote {id:$dataset}) RETURN l.estado AS estado",
                                   dataset=DATASET).single()
                if lote and lote["estado"] == "completo":
                    log.info("El lote %s ya está completo en Neo4j; no se vuelve a cargar", DATASET)
                    reloaded = False
                else:
                    log.info("Cargando el lote %s en Neo4j (estado actual: %s)", DATASET, lote["estado"] if lote else "sin cargar")
                    load_data(session, db, meta)
                    reloaded = True
                totals = session.execute_read(queries.count_listens, DATASET)

        log.info("Neo4j: %s usuarios, %s canciones, %s relaciones ESCUCHO, %s escuchas",
                 *(f"{totals[key]:,}" for key in ("usuarios", "canciones", "relaciones", "escuchas")))
        return {"lote": DATASET, "recargado": reloaded, **totals}

    @task
    def generar_kpis(mongo: dict, cassandra: dict, neo4j: dict, **context):
        from databases.cassandra.connection import get_session
        from databases.cassandra.queries import get_daily_stats, get_load_batches, get_top_artists
        from databases.mongodb.connection import get_client, get_collection, get_database
        from databases.neo4j import analyze
        from databases.neo4j.connection import DATABASE, DATASET, PREPARED, connect
        from databases.neo4j.graph import queries as graph_queries

        # Neo4j: afinidades y comunidades. analyze.main() guarda el análisis en el grafo
        # y en data/neo4j/analysis.json; de ahí se leen los indicadores de red.
        analyze.main()
        analysis = json.loads((PREPARED.parent / "analysis.json").read_text(encoding="utf-8"))
        with connect() as driver, driver.session(database=DATABASE) as session:
            leader_node = session.execute_read(graph_queries.list_artists, DATASET, 1)[0]

        # Cassandra: serie diaria y ranking mensual.
        session = get_session()
        try:
            years = sorted(row["year"] for row in session.execute("SELECT DISTINCT year FROM daily_stats"))
            if not years:
                raise AirflowException("daily_stats está vacía: revisa cargar_cassandra")
            days = get_daily_stats(session, years[-1])
            if len(days) < 2 and len(years) > 1:
                days = get_daily_stats(session, years[-2]) + days
            # El día del corte del dump se descarta: el dump se corta a las 00:01 y ese día
            # queda casi vacío (el 27 de octubre tiene 4 escuchas). Se filtra por fecha y no
            # por posición porque con pocos lotes cargados ese día todavía no aparece.
            validation = json.loads(VALIDATION_REPORT.read_text(encoding="utf-8"))
            cut_day = datetime.fromisoformat(validation["fecha_maxima"]).date()
            complete_days = [row for row in days if row["day"].date() < cut_day]
            reference = complete_days[-1] if complete_days else days[-1]
            day = reference["day"].date()
            month = f"{day.year:04d}-{day.month:02d}"
            top_artist = get_top_artists(session, month, 1)[0]
            batches = get_load_batches(session)
        finally:
            session.cluster.shutdown()

        with get_client() as client:
            mongo_total = get_collection(client).count_documents({})

            kpis = {
                "escuchas_por_dia": {
                    "nombre": "Escuchas procesadas por día",
                    "valor": reference["listens"],
                    "unidad": "escuchas",
                    "dia": str(day),
                    "fuente": "cassandra.daily_stats",
                },
                "crecimiento_diario_pct": {
                    "nombre": "Crecimiento diario de escuchas",
                    "valor": as_float(reference["growth_pct"]),
                    "unidad": "%",
                    "dia": str(day),
                    "fuente": "cassandra.daily_stats",
                },
                "escuchas_por_usuario_activo": {
                    "nombre": "Escuchas promedio por usuario activo",
                    "valor": as_float(reference["listens_per_user"]),
                    "unidad": "escuchas/usuario",
                    "usuarios_activos": reference["active_users"],
                    "dia": str(day),
                    "fuente": "cassandra.daily_stats",
                },
                "participacion_artista_lider": {
                    "nombre": "Participación del artista líder del mes",
                    "valor": as_float(top_artist["share_pct"]),
                    "unidad": "%",
                    "artista": top_artist["artist_name"],
                    "escuchas": top_artist["listens"],
                    "mes": month,
                    "fuente": "cassandra.top_artists_by_month",
                },
                "entidad_mas_conectada": {
                    "nombre": "Artista con más oyentes en el grafo",
                    "valor": leader_node["oyentes"],
                    "unidad": "oyentes",
                    "artista": leader_node["artista"],
                    "relacion": "(:Usuario)-[:ESCUCHA_ARTISTA]->(:Artista)",
                    "fuente": "neo4j",
                },
            }
            snapshot = {
                "_id": context["run_id"],
                "run_id": context["run_id"],
                "fecha_logica": context["logical_date"].isoformat(),
                "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "dia_referencia": str(day),
                "mes_referencia": month,
                "kpis": kpis,
                "seguimiento": {
                    "mongo_documentos": mongo_total,
                    "mongo_insertados_corrida": mongo["insertados"],
                    "cassandra_lotes_cargados": len(batches),
                    "cassandra_escuchas_cargadas": sum(row["rows_loaded"] for row in batches),
                    "cassandra_lotes_nuevos_corrida": cassandra["lotes_nuevos"],
                    "neo4j_usuarios": neo4j["usuarios"],
                    "neo4j_canciones": neo4j["canciones"],
                    "neo4j_escuchas": neo4j["escuchas"],
                    "neo4j_comunidades": len(analysis["communities"]),
                    "neo4j_modularidad": as_float(analysis["kpis"]["modularidad"], 4),
                    "neo4j_cobertura_recomendaciones": as_float(analysis["kpis"]["cobertura_recomendaciones"], 4),
                },
                "serie_diaria": [
                    {
                        "dia": str(row["day"]),
                        "escuchas": row["listens"],
                        "usuarios_activos": row["active_users"],
                        "escuchas_por_usuario": as_float(row["listens_per_user"]),
                        "crecimiento_pct": as_float(row["growth_pct"]),
                    }
                    for row in days[-SERIES_DAYS:]
                ],
            }
            # replace_one con el run_id como _id: si la tarea se reintenta, no duplica el snapshot.
            get_database(client)[KPI_COLLECTION].replace_one({"_id": snapshot["_id"]}, snapshot, upsert=True)

        write_json(KPIS_LATEST, snapshot)
        for key, kpi in kpis.items():
            log.info("KPI %s = %s %s", key, kpi["valor"], kpi["unidad"])
        log.info("Snapshot guardado en Mongo (%s) y en %s", KPI_COLLECTION, KPIS_LATEST)
        return {
            "dia_referencia": str(day),
            **{key: kpi["valor"] for key, kpi in kpis.items()},
            "mongo_documentos": mongo_total,
            "cassandra_lotes_cargados": len(batches),
        }

    extraccion = extraer_datos()
    validacion = validar_y_limpiar(extraccion)
    generar_kpis(cargar_mongodb(validacion), cargar_cassandra(validacion), cargar_neo4j(validacion))


music_dna_pipeline()
