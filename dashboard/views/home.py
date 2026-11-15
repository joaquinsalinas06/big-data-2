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
    check_connections,
)


def render_home_view():
    snapshot = get_airflow_snapshot()
    kpis = snapshot["kpis"]
    seguimiento = snapshot["seguimiento"]
    dia_ref = snapshot.get("dia_referencia", "2026-10-26")
    mes_ref = snapshot.get("mes_referencia", "2026-10")
    conn_status = check_connections()

    # 1. Barra de diagnóstico de conectividad
    st.markdown("### Estado de Motores de Almacenamiento")
    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        status_html = "<span class='status-badge-ok'>En Línea</span>" if conn_status["mongodb"] else "<span class='status-badge-off'>Sin Conexión (Modo Resiliente)</span>"
        st.markdown(f"**MongoDB (Documental):** {status_html}", unsafe_allow_html=True)
        st.caption("Puerto 27017 | Base: music-dna | Colección: listens / kpi_runs")

    with col_c2:
        status_html = "<span class='status-badge-ok'>En Línea</span>" if conn_status["cassandra"] else "<span class='status-badge-off'>Sin Conexión (Modo Resiliente)</span>"
        st.markdown(f"**Apache Cassandra (Temporal):** {status_html}", unsafe_allow_html=True)
        st.caption("Puerto 9042 | Keyspace: music_dna | daily_stats / listens_by_user")

    with col_c3:
        status_html = "<span class='status-badge-ok'>En Línea</span>" if conn_status["neo4j"] else "<span class='status-badge-off'>Sin Conexión (Modo Resiliente)</span>"
        st.markdown(f"**Neo4j (Grafo de Red):** {status_html}", unsafe_allow_html=True)
        st.caption("Puertos 7474 / 7687 | Base: neo4j | Comunidades y Afinidades")

    st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #e2e8f0;'/>", unsafe_allow_html=True)

    # 2. Tarjetas de los 5 KPIs Oficiales
    st.markdown(f"### Indicadores Clave del Pipeline (Día de Referencia: {dia_ref})")
    st.caption(f"Snapshot ID: {snapshot.get('run_id')} | Generado: {snapshot.get('generado_en')}")

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 1: Escuchas del Día</div>
            <div class="value">{kpis['escuchas_por_dia']['valor']:,}</div>
            <div class="subtitle">Volumen procesado ({dia_ref})</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        val_crec = kpis['crecimiento_diario_pct']['valor']
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 2: Crecimiento Diario</div>
            <div class="value">+{val_crec:,.1f}%</div>
            <div class="subtitle">Respecto al día anterior</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 3: Escuchas / Usuario</div>
            <div class="value">{kpis['escuchas_por_usuario_activo']['valor']:.1f}</div>
            <div class="subtitle">{kpis['escuchas_por_usuario_activo']['usuarios_activos']:,} usuarios activos</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 4: Líder del Mes</div>
            <div class="value">{kpis['participacion_artista_lider']['valor']:.2f}%</div>
            <div class="subtitle">{kpis['participacion_artista_lider']['artista']} ({mes_ref})</div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">KPI 5: Mayor Audiencia</div>
            <div class="value">{kpis['entidad_mas_conectada']['valor']:,}</div>
            <div class="subtitle">{kpis['entidad_mas_conectada']['artista']} (oyentes únicos)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 3. Gráficos de Análisis Diario y Líderes Mensuales
    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("#### Serie Temporal Diaria de Ingesta (Últimos 30 Días)")
        serie_df = pd.DataFrame(snapshot.get("serie_diaria", []))
        if not serie_df.empty:
            metric_selected = st.radio(
                "Métrica para graficar:",
                ["Escuchas diarias", "Crecimiento diario (%)", "Usuarios activos"],
                horizontal=True,
                label_visibility="collapsed"
            )
            fig_serie = go.Figure()
            if metric_selected == "Escuchas diarias":
                fig_serie.add_trace(go.Scatter(
                    x=serie_df["dia"],
                    y=serie_df["escuchas"],
                    mode="lines+markers",
                    line=dict(color="#1e3a8a", width=2.5),
                    marker=dict(size=6, color="#1e3a8a"),
                    name="Escuchas"
                ))
                fig_serie.update_layout(yaxis_title="Escuchas Procesadas")
            elif metric_selected == "Crecimiento diario (%)":
                fig_serie.add_trace(go.Bar(
                    x=serie_df["dia"],
                    y=serie_df["crecimiento_pct"],
                    marker_color="#2563eb",
                    name="Crecimiento %"
                ))
                fig_serie.update_layout(yaxis_title="Variación Porcentual (%)")
            else:
                fig_serie.add_trace(go.Bar(
                    x=serie_df["dia"],
                    y=serie_df["usuarios_activos"],
                    marker_color="#0f766e",
                    name="Usuarios Activos"
                ))
                fig_serie.update_layout(yaxis_title="Usuarios Únicos")

            fig_serie.update_layout(
                template="simple_white",
                margin=dict(l=20, r=20, t=10, b=20),
                height=310,
                hovermode="x unified"
            )
            st.plotly_chart(fig_serie, use_container_width=True)
            st.caption("Nota técnica: Los saltos a fines de octubre se deben a la concentración de la ingesta en el lote incremental ListenBrainz 2746, no a variaciones de comportamiento de escucha.")

    with col_chart2:
        st.markdown(f"#### Top Artistas del Mes ({mes_ref})")
        top_df = get_top_artists_month(mes_ref, limit=7)
        fig_top = px.bar(
            top_df,
            x="share_pct",
            y="artist_name",
            orientation="h",
            template="simple_white",
            labels={"share_pct": "Participación (%)", "artist_name": "Artista"},
            color_discrete_sequence=["#1e3a8a"]
        )
        fig_top.update_layout(
            margin=dict(l=20, r=20, t=10, b=20),
            yaxis=dict(autorange="reversed"),
            height=310
        )
        st.plotly_chart(fig_top, use_container_width=True)
        st.caption(f"BTS lidera con 12.65% de cuota sobre 286,291 artistas catalogados.")

    st.markdown("<br/>", unsafe_allow_html=True)

    # 4. Sección de Seguimiento del Pipeline y Corridas Incrementales
    st.markdown("### Seguimiento de Carga y Evolución del Pipeline")
    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">Colección MongoDB</div>
            <div class="value">{seguimiento.get('mongo_documentos', 4000000):,}</div>
            <div class="subtitle">Documentos semiestructurados</div>
        </div>
        """, unsafe_allow_html=True)

    with s2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">Lotes Cassandra</div>
            <div class="value">{seguimiento.get('cassandra_lotes_cargados', 10)} / 10</div>
            <div class="subtitle">{seguimiento.get('cassandra_escuchas_cargadas', 4855809):,} filas agregadas</div>
        </div>
        """, unsafe_allow_html=True)

    with s3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">Nodos en Neo4j</div>
            <div class="value">{seguimiento.get('neo4j_usuarios', 26394):,}</div>
            <div class="subtitle">Usuarios con relaciones en grafo</div>
        </div>
        """, unsafe_allow_html=True)

    with s4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="title">Modularidad de Red</div>
            <div class="value">{seguimiento.get('neo4j_modularidad', 0.7825):.4f}</div>
            <div class="subtitle">{seguimiento.get('neo4j_comunidades', 13)} comunidades (Louvain)</div>
        </div>
        """, unsafe_allow_html=True)

    # 5. Comparativa entre Corridas Incrementales de Airflow
    with st.expander("Comparativa de Carga Incremental entre Corridas de Airflow (kpi_runs)"):
        runs_data = get_kpi_runs_history()
        summary_rows = []
        for r in runs_data:
            k = r.get("kpis", {})
            seg = r.get("seguimiento", {})
            summary_rows.append({
                "Corrida": r.get("run_id", "Sin ID"),
                "Lotes Cassandra": seg.get("cassandra_lotes", 0),
                "Docs MongoDB": f"{seg.get('mongo_documentos', 0):,}",
                "KPI 1 (Escuchas 26/10)": f"{k.get('escuchas_por_dia', 0):,}",
                "KPI 2 (Crecimiento %)": f"+{k.get('crecimiento_diario_pct', 0):.2f}%",
                "KPI 3 (Escuchas / Usuario)": f"{k.get('escuchas_por_usuario_activo', 0):.2f}",
                "KPI 4 (Líder Mes)": f"{k.get('artista_lider', 'BTS')} ({k.get('participacion_artista_lider', 0):.2f}%)",
                "KPI 5 (Más Conectado)": f"{k.get('artista_mas_conectado', 'Linkin Park')} ({k.get('entidad_mas_conectada', 0):,})"
            })
        st.table(pd.DataFrame(summary_rows))
        st.caption("Datos correspondientes a los snapshots registrados por la tarea generar_kpis en cada ejecución del DAG.")

