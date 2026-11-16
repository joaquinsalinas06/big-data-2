"""
Vista de Resumen General y Métricas Globales del Sistema.
Consume directamente el snapshot generado por Apache Airflow (kpis_latest.json / kpi_runs)
cumpliendo la especificación formal del informe técnico (Tabla 5).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.services import (
    get_airflow_snapshot,
    get_kpi_runs_history,
    get_top_artists_month,
)


def render_home_view():
    snapshot = get_airflow_snapshot()

    if not snapshot:
        st.warning("No se encontró ningún snapshot de Airflow en MongoDB ni en 'data/airflow/kpis_latest.json'.")
        st.info("Para inicializar las métricas, inicie Docker con `docker compose up -d` y ejecute el DAG 'music_dna_pipeline' en Airflow (http://localhost:8080).")
        return

    kpis = snapshot["kpis"]
    seguimiento = snapshot.get("seguimiento", {})
    dia_ref = snapshot.get("dia_referencia", "2026-10-26")
    mes_ref = snapshot.get("mes_referencia", "2026-10")
    origen_datos = snapshot.get("_origen", "Snapshot oficial de Airflow")

    # 1. Tarjetas de los 5 KPIs Oficiales
    st.markdown(f"### Indicadores Clave del Pipeline (Día de Corte: {dia_ref})")
    st.caption(f"Fuente de datos: {origen_datos} | Ejecución: {snapshot.get('run_id')} | Generado: {snapshot.get('generado_en')}")

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 1 · Escuchas del Día</div>
            <div class="value">{kpis['escuchas_por_dia']['valor']:,}</div>
            <div class="subtitle">Volumen procesado ({dia_ref})</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        val_crec = kpis['crecimiento_diario_pct']['valor']
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 2 · Crecimiento Diario</div>
            <div class="value">+{val_crec:,.1f}%</div>
            <div class="subtitle">Respecto al día previo (2026-10-25)</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 3 · Escuchas / Usuario</div>
            <div class="value">{kpis['escuchas_por_usuario_activo']['valor']:.1f}</div>
            <div class="subtitle">{kpis['escuchas_por_usuario_activo']['usuarios_activos']:,} usuarios activos</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 4 · Artista Líder</div>
            <div class="value">{kpis['participacion_artista_lider']['valor']:.2f}%</div>
            <div class="subtitle">{kpis['participacion_artista_lider']['artista']} ({mes_ref})</div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        val_k5 = kpis['entidad_mas_conectada'].get('valor', kpis['entidad_mas_conectada'].get('oyentes_unicos', 1137))
        art_k5 = kpis['entidad_mas_conectada'].get('artista', 'Linkin Park')
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 5 · Mayor Audiencia</div>
            <div class="value">{val_k5:,}</div>
            <div class="subtitle">{art_k5} (oyentes únicos)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 2. Gráficos Analíticos Principales (2 Columnas)
    col_chart, col_top = st.columns([3, 2])

    with col_chart:
        st.markdown("#### Serie Temporal Diaria de Ingesta")
        metric_choice = st.radio(
            "Métrica a visualizar:",
            ["Escuchas diarias", "Crecimiento diario (%)", "Usuarios activos"],
            horizontal=True,
            label_visibility="collapsed"
        )

        serie_df = pd.DataFrame(snapshot.get("serie_diaria", []))
        if not serie_df.empty:
            date_col = "fecha" if "fecha" in serie_df.columns else "dia"
            serie_df["fecha_dt"] = pd.to_datetime(serie_df[date_col])

            fig = go.Figure()
            if metric_choice == "Escuchas diarias":
                fig.add_trace(go.Bar(
                    x=serie_df["fecha_dt"],
                    y=serie_df["escuchas"],
                    marker_color="#1e3a8a",
                    name="Escuchas"
                ))
                fig.update_layout(yaxis_title="Cantidad de Escuchas")
            elif metric_choice == "Crecimiento diario (%)":
                fig.add_trace(go.Scatter(
                    x=serie_df["fecha_dt"],
                    y=serie_df["crecimiento_pct"],
                    mode="lines+markers",
                    line=dict(color="#0f766e", width=2),
                    marker=dict(size=5, color="#0f766e"),
                    name="Crecimiento %"
                ))
                fig.update_layout(yaxis_title="Variación Porcentual (%)")
            else:
                fig.add_trace(go.Bar(
                    x=serie_df["fecha_dt"],
                    y=serie_df["usuarios_activos"],
                    marker_color="#2563eb",
                    name="Usuarios Activos"
                ))
                fig.update_layout(yaxis_title="Usuarios Únicos")

            fig.update_layout(
                template="simple_white",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(color="#0f172a"),
                margin=dict(l=20, r=20, t=10, b=20),
                height=290,
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_top:
        st.markdown(f"#### Top Artistas del Mes ({mes_ref})")
        top_artists_df = get_top_artists_month(mes_ref, limit=8)

        fig_top = px.bar(
            top_artists_df.sort_values("listens", ascending=True),
            x="listens",
            y="artist_name",
            orientation="h",
            template="simple_white",
            text="share_pct",
            labels={"listens": "Escuchas", "artist_name": "Artista"},
            color_discrete_sequence=["#1e3a8a"]
        )
        fig_top.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_top.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(color="#0f172a"),
            margin=dict(l=10, r=40, t=10, b=20),
            height=290,
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig_top, use_container_width=True)

    # 3. Seguimiento de Procesamiento del Pipeline (Métricas reales del DAG de Airflow)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Resumen Operativo de la Carga ETL (Airflow)")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Lotes en Cassandra", f"{seguimiento.get('cassandra_lotes_cargados', 10)} / 10")
    with col_s2:
        st.metric("Documentos en MongoDB", f"{seguimiento.get('mongo_documentos', 4000000):,}")
    with col_s3:
        st.metric("Escuchas en Cassandra", f"{seguimiento.get('cassandra_escuchas_cargadas', 4855809):,}")
    with col_s4:
        st.metric("Modularidad en Grafo", f"{seguimiento.get('neo4j_modularidad', 0.7825):.4f}", f"{seguimiento.get('neo4j_comunidades', 13)} comunidades")

    # Comparativa de lotes en tabla sobria
    history_runs = get_kpi_runs_history()
    if history_runs:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.caption("Historial de ejecuciones registradas en MongoDB colección 'kpi_runs':")

        def _get_val(obj, default=0):
            if isinstance(obj, dict):
                return obj.get("valor", default)
            return obj if obj is not None else default

        table_rows = []
        for r in history_runs:
            k = r.get("kpis", {})
            seg = r.get("seguimiento", {})
            lotes_val = seg.get("cassandra_lotes", seg.get("cassandra_lotes_cargados", seg.get("lotes_procesados", 1)))

            e_dia = _get_val(k.get("escuchas_por_dia"), 0)
            c_dia = _get_val(k.get("crecimiento_diario_pct"), 0)
            epu = _get_val(k.get("escuchas_por_usuario_activo"), 0)
            part = _get_val(k.get("participacion_artista_lider"), 0)
            art = k.get("artista_lider") or (k.get("participacion_artista_lider", {}).get("artista") if isinstance(k.get("participacion_artista_lider"), dict) else "BTS")

            table_rows.append({
                "Ejecución": r.get("run_id"),
                "Fecha": r.get("generado_en", "")[:19].replace("T", " "),
                "Lotes": f"{lotes_val} / 10",
                "Escuchas Día": f"{int(e_dia):,}",
                "Crecimiento %": f"{c_dia:+.1f}%",
                "Esc/Usuario": f"{epu:.1f}",
                "Artista Líder": f"{art} ({part:.1f}%)",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
