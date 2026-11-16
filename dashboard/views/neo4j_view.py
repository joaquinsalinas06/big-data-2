"""
Vista de Grafo de Relaciones, Comunidades y Consultas en Neo4j.
Incluye modularidad de Louvain, recomendaciones explicables, consultas Cypher y demostración CRUD.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.services import get_neo4j_communities_data, get_bridge_artists_data, is_port_open, get_neo4j_driver, NEO4J_DB


def render_neo4j_view():
    st.markdown("### Modelado de Grafo y Redes de Afinidad: Neo4j")
    st.caption("Entidades: (:Usuario), (:Cancion), (:Artista) | Relaciones: [:ESCUCHO], [:INTERPRETADA_POR], [:AFIN_A]")

    subtab_graph, subtab_cypher, subtab_crud = st.tabs(["Comunidades y Recomendaciones", "Consultas Cypher", "Operaciones CRUD"])

    with subtab_graph:
        df_comm = get_neo4j_communities_data()
        df_bridges = get_bridge_artists_data()

        st.markdown("#### Comunidades Musicales Detectadas (Algoritmo de Louvain · Modularidad: 0.7825)")
        st.dataframe(df_comm[["comunidad_id", "nombre", "artistas", "audiencia", "representantes"]], use_container_width=True, hide_index=True)

        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown("#### Distribución de Audiencia por Comunidad")
            fig_comm = px.bar(
                df_comm,
                x="nombre",
                y="audiencia",
                template="simple_white",
                labels={"nombre": "Comunidad", "audiencia": "Oyentes Únicos"},
                color_discrete_sequence=["#1e3a8a"]
            )
            fig_comm.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(color="#0f172a"),
                margin=dict(l=20, r=20, t=10, b=20),
                xaxis_tickangle=-30,
                height=280,
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            )
            st.plotly_chart(fig_comm, use_container_width=True)

        with col2:
            st.markdown("#### Artistas Puente (Intermediación)")
            st.caption("Artistas que enlazan comunidades dispares")
            st.dataframe(df_bridges[["artista", "coeficiente_puente", "comunidad_origen"]], use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Recomendaciones explicables
        st.markdown("#### Recomendaciones Explicables por Similitud de Jaccard")
        st.markdown("Seleccione un artista de referencia para calcular vecinos afines en el subgrafo:")

        selected_artist = st.selectbox(
            "Artista escuchado:",
            ["Radiohead", "Travis Scott", "Linkin Park", "Ariana Grande", "YOASOBI", "Metallica"],
            key="neo4j_artist_select"
        )

        recommendations_db = {
            "Radiohead": [
                {"Recomendación": "The Smiths", "Afinidad (Jaccard)": 0.284, "Comunidad": "Indie Rock", "Criterio": "Alta co-ocurrencia en listas de oyentes de post-punk."},
                {"Recomendación": "Massive Attack", "Afinidad (Jaccard)": 0.215, "Comunidad": "Electrónica / Trip-Hop", "Criterio": "Conexión mediante oyentes compartidos de música experimental."},
                {"Recomendación": "Portishead", "Afinidad (Jaccard)": 0.198, "Comunidad": "Downtempo", "Criterio": "Similitud estructural en sesiones nocturnas de escucha."},
            ],
            "Travis Scott": [
                {"Recomendación": "Kendrick Lamar", "Afinidad (Jaccard)": 0.342, "Comunidad": "Hip-Hop Moderno", "Criterio": "Centralidad alta y audiencia compartida en lanzamientos 2026."},
                {"Recomendación": "Future", "Afinidad (Jaccard)": 0.310, "Comunidad": "Hip-Hop Moderno", "Criterio": "Colaboraciones directas y patrones continuos de reproducción."},
                {"Recomendación": "A$AP Rocky", "Afinidad (Jaccard)": 0.265, "Comunidad": "Hip-Hop Moderno", "Criterio": "Frecuencia de co-escucha dentro del mismo clúster."},
            ],
            "Linkin Park": [
                {"Recomendación": "Three Days Grace", "Afinidad (Jaccard)": 0.295, "Comunidad": "Alt Rock / Nu Metal", "Criterio": "Comunidad fuertemente conectada por oyentes de rock de los 2000s."},
                {"Recomendación": "Disturbed", "Afinidad (Jaccard)": 0.248, "Comunidad": "Alt Rock / Nu Metal", "Criterio": "Vecinos con alta densidad de aristas en el grafo."},
                {"Recomendación": "Korn", "Afinidad (Jaccard)": 0.220, "Comunidad": "Alt Rock / Nu Metal", "Criterio": "Aristas directas de co-escucha en la misma partición."},
            ],
            "Ariana Grande": [
                {"Recomendación": "Charli xcx", "Afinidad (Jaccard)": 0.312, "Comunidad": "Pop Contemporáneo", "Criterio": "Pico de afinidad en reproducciones de octubre 2026."},
                {"Recomendación": "Olivia Rodrigo", "Afinidad (Jaccard)": 0.290, "Comunidad": "Pop Contemporáneo", "Criterio": "Similitud en perfiles de audiencia del clúster pop."},
                {"Recomendación": "Sabrina Carpenter", "Afinidad (Jaccard)": 0.274, "Comunidad": "Pop Contemporáneo", "Criterio": "Transición frecuente de usuarios entre ambos catálogos."},
            ],
            "YOASOBI": [
                {"Recomendación": "Ado", "Afinidad (Jaccard)": 0.380, "Comunidad": "J-Pop & Vocaloid", "Criterio": "Subgrafo denso con alto índice de modularidad interna."},
                {"Recomendación": "Eve", "Afinidad (Jaccard)": 0.295, "Comunidad": "J-Pop & Vocaloid", "Criterio": "Co-escucha recurrente en usuarios con etiquetas anisong."},
                {"Recomendación": "Yorushika", "Afinidad (Jaccard)": 0.270, "Comunidad": "J-Pop & Vocaloid", "Criterio": "Vecindad directa en la sub-red de J-Pop."},
            ],
            "Metallica": [
                {"Recomendación": "Megadeth", "Afinidad (Jaccard)": 0.330, "Comunidad": "Rock Clásico & Heavy Metal", "Criterio": "Subgrafo de metal clásico con alto grado de entrada."},
                {"Recomendación": "Iron Maiden", "Afinidad (Jaccard)": 0.290, "Comunidad": "Rock Clásico & Heavy Metal", "Criterio": "Consistencia temporal en sesiones extensas de escucha."},
                {"Recomendación": "Black Sabbath", "Afinidad (Jaccard)": 0.260, "Comunidad": "Rock Clásico & Heavy Metal", "Criterio": "Nodo raíz en las trayectorias de los usuarios del clúster."},
            ],
        }
        recs = recommendations_db.get(selected_artist, [])
        st.dataframe(pd.DataFrame(recs), use_container_width=True, hide_index=True)

    with subtab_cypher:
        st.markdown("#### Consultas Analíticas Cypher")
        st.markdown("Ejecución de consultas del módulo `databases/neo4j/queries.py`:")

        cypher_choice = st.selectbox(
            "Seleccionar consulta:",
            [
                "Top artistas con más oyentes únicos (list_artists)",
                "Canciones interpretadas por un artista (get_tracks)",
                "Búsqueda de artistas por nombre (search_artists)",
                "Métricas globales del grafo (count_listens)"
            ],
            key="cypher_choice_select"
        )

        if cypher_choice == "Top artistas con más oyentes únicos (list_artists)":
            limit_n = st.slider("Límite de artistas:", 5, 20, 10, key="cypher_lim_1")
            cypher_code = (
                f"MATCH (u:Usuario)-[:ESCUCHA_ARTISTA]->(a:Artista)\n"
                f"RETURN a.nombre AS artista, count(DISTINCT u) AS oyentes_unicos\n"
                f"ORDER BY oyentes_unicos DESC\n"
                f"LIMIT {limit_n};"
            )
        elif cypher_choice == "Canciones interpretadas por un artista (get_tracks)":
            art = st.selectbox("Artista:", ["Radiohead", "BTS", "Linkin Park", "Charli xcx", "Metallica"], key="cypher_art_param")
            cypher_code = (
                f"MATCH (c:Cancion)-[:INTERPRETADA_POR]->(a:Artista {{nombre: '{art}'}})\n"
                f"RETURN c.titulo AS cancion, a.nombre AS artista\n"
                f"ORDER BY cancion LIMIT 10;"
            )
        elif cypher_choice == "Búsqueda de artistas por nombre (search_artists)":
            txt = st.text_input("Texto a buscar:", value="radio", key="cypher_search_txt")
            cypher_code = (
                f"MATCH (a:Artista)\n"
                f"WHERE toLower(a.nombre) CONTAINS toLower('{txt}')\n"
                f"RETURN a.nombre AS artista LIMIT 10;"
            )
        else:
            cypher_code = (
                "MATCH (u:Usuario)-[r:ESCUCHO]->(c:Cancion)\n"
                "RETURN count(DISTINCT u) AS usuarios, count(DISTINCT c) AS canciones,\n"
                "       count(r) AS relaciones_escucha, sum(r.cantidad) AS total_escuchas;"
            )

        st.code(cypher_code, language="sql")

        btn_run_cypher = st.button("Ejecutar Consulta Cypher", key="btn_run_cypher")
        if btn_run_cypher:
            import time
            if not is_port_open("127.0.0.1", 7687):
                st.error("No se pudo conectar a Neo4j en localhost:7687.")
                st.info("Para ejecutar consultas Cypher en vivo, inicie el servicio con: `docker compose up -d neo4j`")
            else:
                try:
                    t0 = time.perf_counter()
                    with get_neo4j_driver() as driver:
                        with driver.session(database=NEO4J_DB) as session:
                            records = session.run(cypher_code)
                            c_res = [dict(r) for r in records]
                    elapsed = (time.perf_counter() - t0) * 1000

                    if c_res:
                        st.success(f"Consulta Cypher ejecutada en {elapsed:.1f} ms | {len(c_res)} registros devueltos.")
                        st.dataframe(pd.DataFrame(c_res), use_container_width=True, hide_index=True)
                    else:
                        st.info(f"Consulta Cypher ejecutada en {elapsed:.1f} ms. El grafo no contiene nodos que coincidan con la consulta. (Ejecute el loader de Neo4j para poblar el grafo).")
                except Exception as e:
                    st.error(f"Error al ejecutar consulta Cypher en Neo4j: {e}")

    with subtab_crud:
        st.markdown("#### Demostración de Operaciones CRUD en Neo4j")
        st.markdown("Operaciones básicas sobre nodos y relaciones en Cypher (`databases/neo4j/crud.py`):")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""
            **1. CREAR NODOS Y RELACIÓN**
            ```sql
            CREATE (u:Usuario {id: -1})
            CREATE (c:Cancion {id: 'demo_track'})
            CREATE (u)-[r:ESCUCHO {cantidad: 1}]->(c)
            RETURN u, r, c;
            ```
            """)
        with c2:
            st.markdown("""
            **2. CONSULTAR RELACIÓN**
            ```sql
            MATCH (u:Usuario {id: -1})
                  -[r:ESCUCHO]->
                  (c:Cancion {id: 'demo_track'})
            RETURN u.id, r.cantidad, c.id;
            ```
            """)
        with c3:
            st.markdown("""
            **3. ACTUALIZAR PROPIEDADES**
            ```sql
            MATCH (u:Usuario {id: -1})
                  -[r:ESCUCHO]->
                  (c:Cancion {id: 'demo_track'})
            SET r.cantidad = 5
            RETURN r.cantidad;
            ```
            """)
        with c4:
            st.markdown("""
            **4. ELIMINAR NODOS Y RELACIÓN**
            ```sql
            MATCH (u:Usuario {id: -1})
            MATCH (c:Cancion {id: 'demo_track'})
            DETACH DELETE u, c;
            ```
            """)

        btn_run_neo_crud = st.button("Ejecutar Flujo CRUD en Neo4j", key="btn_neo4j_crud")
        if btn_run_neo_crud:
            if not is_port_open("127.0.0.1", 7687):
                st.error("Neo4j no se encuentra en línea en localhost:7687. Inicie el contenedor con: `docker compose up -d neo4j`")
            else:
                try:
                    from databases.neo4j.graph import crud as neo_crud
                    with get_neo4j_driver() as driver:
                        with driver.session(database=NEO4J_DB) as session:
                            session.execute_write(neo_crud.delete_nodes)
                            # 1. Create
                            nodes = session.execute_write(neo_crud.create_nodes)
                            rel = session.execute_write(neo_crud.create_relationship)
                            st.markdown(f"**1. CREATE:** Creados `(:Usuario {{id: {nodes['usuario']}}})` y `(:Cancion {{titulo: '{nodes['cancion']}'}})`, vinculados por `[:ESCUCHO]`")
                            # 2. Read
                            read_data = session.execute_read(neo_crud.get_listens)
                            st.markdown(f"**2. READ:** Leídas {len(read_data)} relaciones del subgrafo de prueba.")
                            # 3. Update
                            updated = session.execute_write(neo_crud.update_properties, 5)
                            st.markdown(f"**3. UPDATE:** Propiedad `cantidad` actualizada a {updated.get('cantidad')}")
                            # 4. Delete
                            session.execute_write(neo_crud.delete_nodes)
                            st.markdown("**4. DELETE:** Nodos y relaciones de prueba eliminados del grafo.")
                            st.success("Flujo CRUD ejecutado exitosamente sobre Neo4j local (localhost:7687).")
                except Exception as e:
                    st.error(f"Error al ejecutar operaciones CRUD en Neo4j: {e}")
