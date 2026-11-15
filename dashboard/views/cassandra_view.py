"""
Vista de Series Temporales y Agregaciones en Apache Cassandra.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dashboard.services import get_cassandra_timeseries


def render_cassandra_view():
    st.markdown("### Series Temporales y Consultas Masivas: Apache Cassandra")
    st.caption("Keyspace 'music_dna' | Tabla 'listens_by_user'")

    df_months, df_hourly = get_cassandra_timeseries()

    # Gráfico 1: Evolución mensual
    st.markdown("#### Tendencia de Reproducciones por Mes (2026)")
    fig_months = go.Figure()
    fig_months.add_trace(go.Scatter(
        x=df_months["month"],
        y=df_months["listens_count"],
        mode="lines+markers",
        line=dict(color="#1e3a8a", width=3),
        marker=dict(size=7, color="#1e3a8a"),
        name="Escuchas Registradas"
    ))
    fig_months.update_layout(
        template="simple_white",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Mes de Registro",
        yaxis_title="Cantidad de Reproducciones",
        hovermode="x unified",
        height=320,
    )
    st.plotly_chart(fig_months, use_container_width=True)

    # Gráficos en dos columnas: Distribución Horaria y Usuarios Activos
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Distribución Horaria de Escuchas (UTC)")
        fig_hourly = px.bar(
            df_hourly,
            x="hora_utc",
            y="escuchas",
            template="simple_white",
            labels={"hora_utc": "Hora del Día (UTC)", "escuchas": "Volumen de Escuchas"},
            color_discrete_sequence=["#3b82f6"]
        )
        fig_hourly.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig_hourly, use_container_width=True)

    with col2:
        st.markdown("#### Usuarios Activos por Mes")
        fig_users = px.bar(
            df_months,
            x="month",
            y="active_users",
            template="simple_white",
            labels={"month": "Mes", "active_users": "Usuarios Únicos"},
            color_discrete_sequence=["#0f766e"]
        )
        fig_users.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig_users, use_container_width=True)

    # Detalle de arquitectura CQL
    with st.expander("Estrategia de Particionamiento en Cassandra (Evitar Wide Partitions)"):
        st.markdown("""
        * **Clave Primaria Compuesta:** `PRIMARY KEY ((user_id, month), listened_at, listen_id)`
        * **Estrategia de Partición `(user_id, month)`:** Garantiza que el histórico de un usuario en un mes se almacene secuencialmente en el mismo nodo, evitando *wide partitions* infinitas al limitar el tamaño de cada partición a un mes.
        * **Ordenamiento en Disco `listened_at DESC`:** Clustering key que optimiza las consultas de historiales recientes sin requerir ordenamiento en memoria.
        * **Desempatador Determinista `listen_id ASC`:** Hash SHA-1 para asegurar que múltiples escuchas en el mismo segundo no se sobrescriban.
        """)
