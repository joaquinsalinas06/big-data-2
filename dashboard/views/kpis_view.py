"""
Fichas Técnicas Formales de los 5 Indicadores Clave de Rendimiento (KPIs).
Cumplimiento estricto de la formulación matemática y valores del informe técnico (Capítulo 9).
"""

import streamlit as st
import pandas as pd


def render_kpis_view():
    st.markdown("### Fichas Técnicas de Indicadores Clave (KPIs)")
    st.markdown("Especificación matemática formal, fuentes de datos e interpretación analítica de los 5 indicadores calculados por el DAG de Airflow:")

    # KPI 1
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 1: Escuchas Procesadas por Día (Cassandra)</h3>
            <p><strong>Definición:</strong> Cantidad total de eventos de escucha registrados en el sistema con fecha UTC correspondiente al día de corte <code>d*</code>.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_1 = E(d^{*})")
        st.markdown("""
        * **Fuente de Datos:** Tabla preagregada `daily_stats` de Apache Cassandra.
        * **Valor Obtenido (Lote Completo):** **1,359,824** escuchas para el 26 de octubre de 2026.
        * **Interpretación Técnica:** Mide el volumen absoluto procesado por el pipeline. Este día concentra el **28.0% del total de eventos del dataset**, evidenciando la concentración temporal típica de volcados de datos generados al final de un periodo de recolección.
        """)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # KPI 2
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 2: Crecimiento Diario de Escuchas (Cassandra)</h3>
            <p><strong>Definición:</strong> Variación porcentual en el volumen de escuchas del día de referencia con respecto al día calendario inmediatamente anterior.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_2 = \frac{E(d^{*}) - E(d^{*}-1)}{E(d^{*}-1)} \times 100\%")
        st.markdown("""
        * **Fuente de Datos:** Tabla `daily_stats` de Apache Cassandra (`growth_pct`).
        * **Valor Obtenido (Lote Completo):** **+3,364.00%** de incremento respecto al 25 de octubre (de 39,250 a 1,359,824 escuchas).
        * **Interpretación Técnica:** Captura la aceleración del flujo de datos. Este incremento cuantitativo responde a la llegada masiva de sincronizaciones de clientes acumuladas en la ventana previa al corte del dump incremental de ListenBrainz.
        """)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # KPI 3
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 3: Escuchas Promedio por Usuario Activo (Cassandra)</h3>
            <p><strong>Definición:</strong> Relación entre el total de escuchas y el número de usuarios distintos que registraron al menos un evento en la fecha de corte.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_3 = \frac{E(d^{*})}{U(d^{*})}")
        st.markdown("""
        * **Fuente de Datos:** Tabla `daily_stats` de Apache Cassandra (`listens_per_user`, `active_users`).
        * **Valor Obtenido (Lote Completo):** **52.3 escuchas/usuario** (calculado sobre 26,020 usuarios activos el 26 de octubre).
        * **Interpretación Técnica:** Permite evaluar la intensidad de uso individual frente al crecimiento de la base de usuarios. En comparación con el promedio habitual de 8 a 10 escuchas/usuario de días previos, el valor refleja sesiones de sincronización de historiales acumulados.
        """)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # KPI 4
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 4: Participación del Artista Líder del Mes (Cassandra)</h3>
            <p><strong>Definición:</strong> Proporción de reproducciones que concentra el artista en primer lugar del ranking mensual respecto al total del catálogo en dicho mes.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_4 = \frac{E_{a_1}(m^{*})}{\sum_{a} E_{a}(m^{*})} \times 100\%")
        st.markdown("""
        * **Fuente de Datos:** Tabla preagregada `top_artists_by_month` de Apache Cassandra (registro con `rank = 1`).
        * **Valor Obtenido (Lote Completo):** **BTS** con **12.65%** del total mensual en octubre de 2026 (48,640 escuchas).
        * **Interpretación Técnica:** Evalúa el grado de concentración del consumo musical. A pesar de existir más de 286,000 nombres de artistas en el catálogo, un único artista representa más de un octavo de todo el tráfico del mes.
        """)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # KPI 5
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 5: Entidad con Mayor Grado de Conexión en el Grafo (Neo4j)</h3>
            <p><strong>Definición:</strong> Artista con la mayor cantidad de nodos de usuario distintos conectados directamente mediante relaciones de tipo <code>:ESCUCHA_ARTISTA</code>.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"C(a) = \left|\{ u : (u)\text{-[:ESCUCHA\_ARTISTA]}\rightarrow(a) \}\right|, \qquad \text{KPI}_5 = \max_{a} C(a)")
        st.markdown("""
        * **Fuente de Datos:** Grado de entrada (`in-degree`) en el grafo de Neo4j (`MATCH (u:Usuario)-[:ESCUCHA_ARTISTA]->(a:Artista) RETURN a, count(DISTINCT u)`).
        * **Valor Obtenido (Grafo Completo):** **Linkin Park** con **1,137 oyentes únicos**.
        * **Interpretación Técnica:** Permite contrastar la concentración de volumen con el alcance transversal. Aunque BTS lidera en cantidad absoluta de escuchas (KPI 4), Linkin Park es el artista que conecta a un mayor número de oyentes distintos e independientes en la red de afinidad.
        """)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Tabla Resumen de Valores por Corrida (Tabla 4 del informe)
    st.markdown("### Comparativa de Indicadores según la Progresión del Pipeline")
    st.markdown("Evolución de los indicadores calculados a medida que Airflow procesa lotes incrementales (Tabla 4 del informe técnico):")

    df_kpi_table = pd.DataFrame([
        {
            "Indicador": "1. Escuchas del 26 de octubre",
            "1 Lote (Parcial)": "66,562",
            "2 Lotes (Parcial)": "223,289",
            "Archivo Completo (10 lotes)": "1,359,824",
        },
        {
            "Indicador": "2. Crecimiento respecto al día 25",
            "1 Lote (Parcial)": "+158.31%",
            "2 Lotes (Parcial)": "+666.82%",
            "Archivo Completo (10 lotes)": "+3,364.00%",
        },
        {
            "Indicador": "3. Escuchas por usuario activo",
            "1 Lote (Parcial)": "12.45 (5,345 usuarios)",
            "2 Lotes (Parcial)": "24.99 (8,936 usuarios)",
            "Archivo Completo (10 lotes)": "52.30 (26,020 usuarios)",
        },
        {
            "Indicador": "4. Artista líder del mes",
            "1 Lote (Parcial)": "BTS (11.82%)",
            "2 Lotes (Parcial)": "BTS (12.10%)",
            "Archivo Completo (10 lotes)": "BTS (12.65%)",
        },
        {
            "Indicador": "5. Mayor audiencia en grafo",
            "1 Lote (Parcial)": "Linkin Park (142 oyentes)",
            "2 Lotes (Parcial)": "Linkin Park (418 oyentes)",
            "Archivo Completo (10 lotes)": "Linkin Park (1,137 oyentes)",
        },
    ])

    st.dataframe(df_kpi_table, use_container_width=True, hide_index=True)
