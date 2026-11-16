"""
Vista de Series Temporales y Agregaciones en Apache Cassandra.
Incluye visualizaciones analíticas, consola interactiva de consultas CQL y demostración CRUD.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.services import get_cassandra_timeseries, is_port_open, get_cassandra_session, KEYSPACE


def render_cassandra_view():
    st.markdown("### Series Temporales y Agregaciones: Apache Cassandra")
    st.caption("Keyspace: 'music_dna' | Particionamiento por (user_id, month) | Ordenamiento temporal clustering key")

    subtab_cql, subtab_crud = st.tabs(["Métricas y Consultas CQL", "Operaciones CRUD (Demostración)"])

    with subtab_cql:
        df_months, df_hourly = get_cassandra_timeseries()

        if not df_months.empty:
            st.markdown("#### Tendencia de Reproducciones Mensuales (2026)")
            fig_months = go.Figure()
            fig_months.add_trace(go.Scatter(
                x=df_months["month"],
                y=df_months["listens_count"],
                mode="lines+markers",
                line=dict(color="#1e3a8a", width=2.5),
                marker=dict(size=6, color="#1e3a8a"),
                name="Escuchas"
            ))
            fig_months.update_layout(
                template="simple_white",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(color="#0f172a"),
                margin=dict(l=20, r=20, t=10, b=20),
                xaxis_title="Mes",
                yaxis_title="Cantidad de Escuchas",
                hovermode="x unified",
                height=250,
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            )
            st.plotly_chart(fig_months, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if not df_hourly.empty:
                st.markdown("#### Distribución Horaria de Escuchas (UTC)")
                fig_hourly = px.bar(
                    df_hourly,
                    x="hora_utc",
                    y="escuchas",
                    template="simple_white",
                    labels={"hora_utc": "Hora del Día (UTC)", "escuchas": "Escuchas"},
                    color_discrete_sequence=["#2563eb"]
                )
                fig_hourly.update_layout(
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(color="#0f172a"),
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=240,
                    xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                    yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                )
                st.plotly_chart(fig_hourly, use_container_width=True)

        with col2:
            if not df_months.empty:
                st.markdown("#### Usuarios Activos por Mes")
                fig_users = px.bar(
                    df_months,
                    x="month",
                    y="active_users",
                    template="simple_white",
                    labels={"month": "Mes", "active_users": "Usuarios Únicos"},
                    color_discrete_sequence=["#0f766e"]
                )
                fig_users.update_layout(
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(color="#0f172a"),
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=240,
                    xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                    yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                )
                st.plotly_chart(fig_users, use_container_width=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Consola interactiva de consultas CQL en vivo
        st.markdown("#### Consola Interactiva de Consultas CQL")
        st.markdown("Seleccione una de las consultas analíticas del módulo `databases/cassandra/queries.py`:")

        col_q1, col_q2 = st.columns([1, 2])
        with col_q1:
            cql_query_type = st.selectbox(
                "Tipo de consulta:",
                [
                    "Top artistas por mes (top_artists_by_month)",
                    "Historial mensual de un artista (artist_monthly_listens)",
                    "Estadísticas diarias del año (daily_stats)"
                ],
                key="cql_type_select"
            )

        with col_q2:
            if cql_query_type == "Top artistas por mes (top_artists_by_month)":
                col_m, col_l = st.columns(2)
                with col_m:
                    month_param = st.selectbox("Mes:", ["2026-10", "2026-09", "2026-08"], index=0, key="cql_month_param")
                with col_l:
                    limit_param = st.slider("Límite:", min_value=5, max_value=20, value=10, step=5, key="cql_limit_slider")
                cql_str = f"SELECT rank, artist_name, listens, share_pct FROM top_artists_by_month WHERE month = '{month_param}' LIMIT {limit_param};"
            elif cql_query_type == "Historial mensual de un artista (artist_monthly_listens)":
                artist_param = st.selectbox("Artista:", ["BTS", "Linkin Park", "Radiohead", "Taylor Swift", "Charli xcx", "Kendrick Lamar"], key="cql_artist_param")
                cql_str = f"SELECT month, listens FROM artist_monthly_listens WHERE artist_name = '{artist_param}';"
            else:
                year_param = st.selectbox("Año:", [2026, 2025], index=0, key="cql_year_param")
                cql_str = f"SELECT day, listens, active_users, listens_per_user, growth_pct FROM daily_stats WHERE year = {year_param};"

        st.code(cql_str, language="sql")

        btn_exec = st.button("Ejecutar Consulta CQL", key="btn_exec_cql")
        if btn_exec:
            import time
            if not is_port_open("127.0.0.1", 9042):
                st.error("No se pudo conectar a Apache Cassandra en localhost:9042.")
                st.info("Para ejecutar consultas CQL en vivo, inicie el contenedor con: `docker compose up -d cassandra`")
            else:
                try:
                    t0 = time.perf_counter()
                    session = get_cassandra_session()
                    rows = session.execute(cql_str)
                    results = [dict(r) for r in rows]
                    session.cluster.shutdown()
                    elapsed_ms = (time.perf_counter() - t0) * 1000

                    if results:
                        st.success(f"Consulta ejecutada en {elapsed_ms:.1f} ms | {len(results)} filas devueltas.")
                        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
                    else:
                        st.info(f"Consulta ejecutada en {elapsed_ms:.1f} ms. La tabla no contiene registros para los parámetros seleccionados. (Ejecute el loader de Cassandra para poblarla).")
                except Exception as e:
                    st.error(f"Error al ejecutar consulta en Cassandra: {e}")

    with subtab_crud:
        st.markdown("#### Demostración de Operaciones CRUD en Cassandra")
        st.markdown("Operaciones básicas sobre la tabla particionada `listens_by_user` (`databases/cassandra/crud.py`):")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""
            **1. INSERCIÓN**
            ```sql
            INSERT INTO listens_by_user
            (user_id, month, listened_at,
             listen_id, artist_name, track_name)
            VALUES (-1, '2026-10', toTimestamp(now()),
                    uuid(), 'Radiohead', 'Creep');
            ```
            """)
        with c2:
            st.markdown("""
            **2. CONSULTA**
            ```sql
            SELECT * FROM listens_by_user
            WHERE user_id = -1
              AND month = '2026-10'
            LIMIT 5;
            ```
            """)
        with c3:
            st.markdown("""
            **3. ACTUALIZACIÓN**
            ```sql
            UPDATE listens_by_user
            SET track_name = 'Creep (Acoustic)'
            WHERE user_id = -1
              AND month = '2026-10'
              AND listened_at = ?
              AND listen_id = ?;
            ```
            """)
        with c4:
            st.markdown("""
            **4. ELIMINACIÓN**
            ```sql
            DELETE FROM listens_by_user
            WHERE user_id = -1
              AND month = '2026-10'
              AND listened_at = ?
              AND listen_id = ?;
            ```
            """)

        btn_run_c_crud = st.button("Ejecutar Flujo CRUD en Cassandra", key="btn_cassandra_crud")
        if btn_run_c_crud:
            if not is_port_open("127.0.0.1", 9042):
                st.error("Cassandra no se encuentra en línea en localhost:9042. Inicie el contenedor con: `docker compose up -d cassandra`")
            else:
                try:
                    import datetime
                    from databases.cassandra.crud import insert_listen, get_listen, update_listen, delete_listen
                    session = get_cassandra_session()
                    now = datetime.datetime.now(datetime.timezone.utc)
                    # 1. Insert
                    l_id = insert_listen(session, -1, now, "Radiohead", "Creep", "Pablo Honey")
                    st.markdown(f"**1. INSERCIÓN:** Fila insertada en `listens_by_user` con `listen_id = {l_id}`")
                    # 2. Read
                    row = get_listen(session, -1, now, l_id)
                    st.markdown(f"**2. CONSULTA:** Fila leída por clave primaria: `{row['artist_name']} - {row['track_name']}`")
                    # 3. Update
                    update_listen(session, -1, now, l_id, "Creep (Acoustic)", "Pablo Honey (Special Edition)")
                    st.markdown("**3. ACTUALIZACIÓN:** track_name y release_name modificados en disco.")
                    # 4. Delete
                    delete_listen(session, -1, now, l_id)
                    session.cluster.shutdown()
                    st.markdown("**4. ELIMINACIÓN:** Fila eliminada por clave primaria. Comprobación: registro borrado.")
                    st.success("Flujo CRUD ejecutado exitosamente sobre Cassandra local (localhost:9042).")
                except Exception as e:
                    st.error(f"Error al ejecutar operaciones CRUD en Cassandra: {e}")
