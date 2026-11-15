"""
Pruebas unitarias para los servicios del Dashboard Analítico.
Verifica la consistencia del snapshot de Airflow, fuentes de KPIs y tolerancia a fallos.
"""

import pytest
import pandas as pd
from dashboard.services import (
    get_airflow_snapshot,
    get_kpi_runs_history,
    get_top_artists_month,
    get_cassandra_timeseries,
    get_neo4j_communities_data,
    get_bridge_artists_data,
    get_mongodb_listens,
    is_port_open,
)


def test_is_port_open_non_existent():
    # Un puerto aleatorio sin servicio debe retornar False inmediatamente
    assert is_port_open("127.0.0.1", 59999, timeout=0.1) is False


def test_airflow_snapshot_structure():
    snapshot = get_airflow_snapshot()
    assert isinstance(snapshot, dict)
    assert "kpis" in snapshot
    assert "seguimiento" in snapshot
    assert "serie_diaria" in snapshot

    kpis = snapshot["kpis"]
    # Los 5 KPIs requeridos deben estar presentes
    assert "escuchas_por_dia" in kpis
    assert "crecimiento_diario_pct" in kpis
    assert "escuchas_por_usuario_activo" in kpis
    assert "participacion_artista_lider" in kpis
    assert "entidad_mas_conectada" in kpis

    # Validar valores oficiales del día de corte 2026-10-26
    assert kpis["escuchas_por_dia"]["valor"] == 1359824
    assert kpis["crecimiento_diario_pct"]["valor"] == 3364.0
    assert kpis["escuchas_por_usuario_activo"]["usuarios_activos"] == 26020
    assert kpis["participacion_artista_lider"]["artista"] == "BTS"
    assert kpis["entidad_mas_conectada"]["artista"] == "Linkin Park"


def test_kpi_runs_history():
    runs = get_kpi_runs_history()
    assert isinstance(runs, list)
    assert len(runs) >= 3

    for r in runs:
        assert "run_id" in r
        assert "kpis" in r
        assert "seguimiento" in r
        k = r["kpis"]
        # Validar que los campos existan ya sea como dict o escalares
        assert "escuchas_por_dia" in k
        assert "crecimiento_diario_pct" in k


def test_top_artists_month():
    df = get_top_artists_month("2026-10", limit=10)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "artist_name" in df.columns
    assert "listens" in df.columns
    assert "share_pct" in df.columns
    # El primer lugar debe ser BTS con ~12.65%
    assert df.iloc[0]["artist_name"] == "BTS"


def test_cassandra_timeseries():
    df_months, df_hourly = get_cassandra_timeseries()
    assert isinstance(df_months, pd.DataFrame)
    assert isinstance(df_hourly, pd.DataFrame)
    assert not df_months.empty
    assert not df_hourly.empty
    assert "month" in df_months.columns
    assert "hora_utc" in df_hourly.columns


def test_neo4j_communities_and_bridges():
    df_comm = get_neo4j_communities_data()
    df_bridges = get_bridge_artists_data()
    assert isinstance(df_comm, pd.DataFrame)
    assert isinstance(df_bridges, pd.DataFrame)
    assert not df_comm.empty
    assert not df_bridges.empty
    assert "comunidad_id" in df_comm.columns
    assert "artista" in df_bridges.columns


def test_mongodb_listens():
    records = get_mongodb_listens(query_text="", limit=5)
    assert isinstance(records, list)
    assert len(records) > 0
    assert "user_name" in records[0]
    assert "track_metadata" in records[0]
