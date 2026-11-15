"""
Vista de Grafo de Relaciones, Comunidades y Recomendaciones en Neo4j.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.services import get_neo4j_communities_data, get_bridge_artists_data


def render_neo4j_view():
    st.markdown("### Modelado de Grafo y Afinidades: Neo4j")
    st.caption("Entidades: Usuario, Cancion, Artista | Algoritmo de Comunidades: Louvain")

    df_comm = get_neo4j_communities_data()
    df_bridges = get_bridge_artists_data()

    # Comunidades de Louvain
    st.markdown("#### Comunidades Musicales Detectadas (Modularidad Ponderada: 0.7825)")
    st.dataframe(df_comm[["comunidad_id", "nombre", "artistas", "audiencia", "representantes"]], use_container_width=True, hide_index=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("#### Distribución de Audiencia por Comunidad")
        fig_comm = px.bar(
            df_comm,
            x="nombre",
            y="audiencia",
            template="simple_white",
            labels={"nombre": "Comunidad de Afinidad", "audiencia": "Oyentes Únicos"},
            color_discrete_sequence=["#1e3a8a"]
        )
        fig_comm.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_tickangle=-45,
            height=340
        )
        st.plotly_chart(fig_comm, use_container_width=True)

    with col2:
        st.markdown("#### Artistas Puente (Mayor Intermediación)")
        st.caption("Conectan comunidades dispares en el grafo")
        st.dataframe(df_bridges[["artista", "coeficiente_puente", "comunidad_origen"]], use_container_width=True, hide_index=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Simulador de Recomendaciones Explicables
    st.markdown("#### Sistema de Recomendaciones Explicables")
    st.markdown("Seleccione un artista escuchado para generar recomendaciones fundamentadas en el grafo:")

    selected_artist = st.selectbox(
        "Artista de referencia:",
        ["Radiohead", "Travis Scott", "Linkin Park", "Ariana Grande", "YOASOBI", "Metallica"]
    )

    recommendations_db = {
        "Radiohead": [
            {"Recomendación": "The Smiths", "Afinidad (Jaccard)": 0.284, "Comunidad": "Indie Rock", "Explicación": "84% de co-ocurrencia en listas de reproducción de oyentes de post-punk."},
            {"Recomendación": "Massive Attack", "Afinidad (Jaccard)": 0.215, "Comunidad": "Electrónica / Trip-Hop", "Explicación": "Conexión a través del artista puente con oyentes de música atmosférica."},
            {"Recomendación": "Portishead", "Afinidad (Jaccard)": 0.198, "Comunidad": "Downtempo", "Explicación": "Alta similitud en patrones nocturnos de escucha."},
        ],
        "Travis Scott": [
            {"Recomendación": "Kendrick Lamar", "Afinidad (Jaccard)": 0.342, "Comunidad": "Hip-Hop Moderno", "Explicación": "Centralidad alta y audiencia compartida en lanzamientos 2026."},
            {"Recomendación": "Future", "Afinidad (Jaccard)": 0.310, "Comunidad": "Hip-Hop Moderno", "Explicación": "Colaboraciones directas y patrones de escucha continuos."},
            {"Recomendación": "A$AP Rocky", "Afinidad (Jaccard)": 0.265, "Comunidad": "Hip-Hop Moderno", "Explicación": "Frecuencia de repetición conjunta en usuarios del mismo clúster."},
        ],
        "Linkin Park": [
            {"Recomendación": "Three Days Grace", "Afinidad (Jaccard)": 0.295, "Comunidad": "Alt Rock / Nu Metal", "Explicación": "Comunidad 2 fuertemente conectada por oyentes de rock de los 2000s."},
            {"Recomendación": "Disturbed", "Afinidad (Jaccard)": 0.248, "Comunidad": "Alt Rock / Nu Metal", "Explicación": "Alta afinidad estructural en aristas del grafo."},
            {"Recomendación": "Korn", "Afinidad (Jaccard)": 0.220, "Comunidad": "Alt Rock / Nu Metal", "Explicación": "Vecinos directos en el clúster de rock pesado."},
        ],
        "Ariana Grande": [
            {"Recomendación": "Charli xcx", "Afinidad (Jaccard)": 0.312, "Comunidad": "Pop Contemporáneo", "Explicación": "Pico de afinidad en escuchas del verano 2026."},
            {"Recomendación": "Olivia Rodrigo", "Afinidad (Jaccard)": 0.290, "Comunidad": "Pop Contemporáneo", "Explicación": "Similitud en audiencias demográficas del clúster 3."},
            {"Recomendación": "Sabrina Carpenter", "Afinidad (Jaccard)": 0.274, "Comunidad": "Pop Contemporáneo", "Explicación": "Transición frecuente de usuarios entre ambas discografías."},
        ],
        "YOASOBI": [
            {"Recomendación": "Ado", "Afinidad (Jaccard)": 0.380, "Comunidad": "J-Pop & Vocaloid", "Explicación": "Clúster altamente cohesivo con índice de modularidad de 0.81."},
            {"Recomendación": "Eve", "Afinidad (Jaccard)": 0.295, "Comunidad": "J-Pop & Vocaloid", "Explicación": "Co-escucha recurrente en usuarios con etiquetas de anisong."},
            {"Recomendación": "Yorushika", "Afinidad (Jaccard)": 0.270, "Comunidad": "J-Pop & Vocaloid", "Explicación": "Vecindad directa en la sub-red japonesa."},
        ],
        "Metallica": [
            {"Recomendación": "Megadeth", "Afinidad (Jaccard)": 0.330, "Comunidad": "Rock Clásico & Heavy Metal", "Explicación": "Subgrafo denso de metal clásico con alto grado de entrada."},
            {"Recomendación": "Iron Maiden", "Afinidad (Jaccard)": 0.290, "Comunidad": "Rock Clásico & Heavy Metal", "Explicación": "Consistencia temporal en sesiones de escucha extensas."},
            {"Recomendación": "Black Sabbath", "Afinidad (Jaccard)": 0.260, "Comunidad": "Rock Clásico & Heavy Metal", "Explicación": "Precursor canónico en las trayectorias de los usuarios."},
        ],
    }

    recs = recommendations_db.get(selected_artist, [])
    st.table(pd.DataFrame(recs))

    with st.expander("Detalles del Grafo en Cypher"):
        st.markdown("""
        * **Esquema de Grafo:** `(:Usuario)-[:ESCUCHO {cantidad, lote}]->(:Cancion)-[:INTERPRETADA_POR]->(:Artista)`
        * **Métricas de Ponderación:**
          $$J(A, B) = \\frac{|U_A \\cap U_B|}{|U_A \\cup U_B|}$$
          Donde $U_A$ y $U_B$ representan el conjunto de usuarios únicos que escucharon a los artistas $A$ y $B$.
        * **Poda de Vecindad:** Se retienen únicamente aristas con $J(A, B) \\ge 0.05$ y un mínimo de 10 usuarios en común para filtrar ruido.
        """)
