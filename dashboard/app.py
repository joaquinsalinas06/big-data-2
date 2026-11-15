"""
Music DNA — Dashboard Analítico Multimodelo
Universidad de Ingeniería y Tecnología (UTEC) · Big Data 2026-2 · Proyecto Grupal II
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Music DNA — Dashboard Analítico Multimodelo",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyección de estilos sobrios (sin emojis, colores claros)
from dashboard.styles import CUSTOM_CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Vistas modulares
from dashboard.views.home import render_home_view
from dashboard.views.mongodb_view import render_mongodb_view
from dashboard.views.cassandra_view import render_cassandra_view
from dashboard.views.neo4j_view import render_neo4j_view
from dashboard.views.kpis_view import render_kpis_view
from dashboard.services import check_connections

# Barra lateral informativa
conn_status = check_connections()

with st.sidebar:
    st.markdown("### Music DNA")
    st.markdown("**Proyecto Grupal II · Big Data**")
    st.caption("Arquitectura Multimodelo para Análisis Musical")

    st.markdown("---")
    st.markdown("**Estado de Motores:**")
    for name, port, key in [("MongoDB (Doc)", 27017, "mongodb"), ("Cassandra (Time)", 9042, "cassandra"), ("Neo4j (Grafo)", 7687, "neo4j")]:
        status_badge = "En Línea" if conn_status[key] else "Local (Snapshot)"
        badge_class = "status-badge-ok" if conn_status[key] else "status-badge-off"
        st.markdown(f"""
        <div class="sidebar-db-status">
            <span class="db-name">{name}</span>: <span class="{badge_class}">{status_badge}</span>
            <div class="db-detail">Puerto {port}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Equipo de Desarrollo:**")
    st.markdown("""
    * Accilio Villanueva, Ana María
    * Cabezas Ramírez, Dylan Andrés
    * Gálvez Pacori, José Guillermo
    * Meneses Roncal, Matías Alonso
    * Salinas Salas, Joaquín Mauricio
    """)

    st.markdown("---")
    st.markdown("**Dataset de Referencia:**")
    st.caption("ListenBrainz incremental 2746")
    st.caption("4.85 millones de registros JSON")
    st.caption("Entrega: 17 de noviembre de 2026")

# Encabezado compacto (sin ocupar espacio excesivo)
st.markdown("""
<div class="dashboard-header">
    <h2>Music DNA — Sistema Analítico Multimodelo</h2>
    <span class="header-sub">UTEC · Big Data 2026-2 · Evaluación Grupal II</span>
</div>
""", unsafe_allow_html=True)

# Navegación por pestañas limpias y directas
tab_home, tab_mongo, tab_cassandra, tab_neo4j, tab_kpis = st.tabs([
    "Resumen General",
    "MongoDB",
    "Cassandra",
    "Neo4j",
    "Fichas de KPIs"
])

with tab_home:
    render_home_view()

with tab_mongo:
    render_mongodb_view()

with tab_cassandra:
    render_cassandra_view()

with tab_neo4j:
    render_neo4j_view()

with tab_kpis:
    render_kpis_view()
