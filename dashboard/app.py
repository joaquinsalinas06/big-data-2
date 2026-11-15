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
    page_title="Music DNA — Sistema Analítico Multimodelo",
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

# Barra lateral informativa
with st.sidebar:
    st.markdown("### Music DNA")
    st.markdown("**Proyecto Grupal II · Big Data**")
    st.caption("Arquitectura Multimodelo para Análisis Musical")
    
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
    st.caption("ListenBrainz incremental 2746 (4.85M registros)")
    st.caption("Entrega: 17 de noviembre de 2026")

# Encabezado principal
st.markdown("""
<div class="main-header">
    <h1>Music DNA — Sistema Analítico Multimodelo</h1>
    <p>Plataforma analítica integrada sobre MongoDB, Apache Cassandra y Neo4j para la exploración de patrones de escucha musical.</p>
</div>
""", unsafe_allow_html=True)

# Navegación por pestañas
tab_home, tab_mongo, tab_cassandra, tab_neo4j, tab_kpis = st.tabs([
    "Resumen General",
    "Persistencia Documental (MongoDB)",
    "Series Temporales (Cassandra)",
    "Grafo y Afinidades (Neo4j)",
    "Fichas Técnicas de KPIs"
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
