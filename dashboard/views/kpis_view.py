"""
Fichas Técnicas Formales de los 5 Indicadores Clave de Rendimiento (KPIs).
Cumplimiento estricto de la formulación matemática y valores del informe técnico (Capítulo 9).
"""

import streamlit as st
import pandas as pd


def render_kpis_view():
    st.markdown("### Fichas Técnicas de Indicadores Clave (KPIs)")
    st.markdown("Especificación matemática formal, fuentes de datos e interpretación de los 5 indicadores calculados por el DAG de Airflow:")

    # KPI 1
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 1: Escuchas Procesadas por Día (Cassandra)</h3>
            <p><strong>Definición:</strong> Cantidad de escuchas cargadas en el sistema con fecha UTC igual al día de referencia <code>d*</code>.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_1 = E(d^{*})")
        st.markdown("""
        * **Fuente de Datos:** Tabla preagregada `daily_stats` de Apache Cassandra.
        * **Valor Obtenido (Archivo Completo):** **1,359,824** escuchas para el día de referencia (26 de octubre de 2026).
        * **Interpretación Técnica:** Mide el volumen absoluto procesado por el pipeline. Concentra el **28% de todo el dataset**, evidenciando cómo la ingesta del incremental de MetaBrainz se agrupó en los días inmediatamente anteriores al corte del volcado.
        """)

    st.markdown("<br/>", unsafe_allow_html=True)

    # KPI 2
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 2: Crecimiento Diario de Escuchas (Cassandra)</h3>
            <p><strong>Definición:</strong> Variación porcentual de las escuchas procesadas en el día de referencia respecto al día anterior inmediato.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_2 = \frac{E(d^{*}) - E(d^{*}-1)}{E(d^{*}-1)} \times 100\%")
        st.markdown("""
        * **Fuente de Datos:** Tabla `daily_stats` de Apache Cassandra (`growth_pct`).
        * **Valor Obtenido (Archivo Completo):** **+3,364.00%** de incremento respecto al 25 de octubre.
        * **Interpretación Técnica:** Captura la aceleración de corto plazo. Un crecimiento de esta magnitud no refleja un cambio en los hábitos biológicos de escucha humana, sino la dinámica del envío por lotes de clientes que sincronizaron sus historiales hacia ListenBrainz.
        """)

    st.markdown("<br/>", unsafe_allow_html=True)

    # KPI 3
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 3: Escuchas Promedio por Usuario Activo (Cassandra)</h3>
            <p><strong>Definición:</strong> Cociente entre las escuchas del día de referencia y la cantidad de usuarios distintos con al menos un evento registrado ese día.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_3 = \frac{E(d^{*})}{U(d^{*})}")
        st.markdown("""
        * **Fuente de Datos:** Tabla `daily_stats` de Apache Cassandra (`listens_per_user`, `active_users`).
        * **Valor Obtenido (Archivo Completo):** **52.3 escuchas/usuario** (calculado sobre 26,020 usuarios activos el 26 de octubre).
        * **Interpretación Técnica:** Desacopla la intensidad individual del alcance de la plataforma. Permite discernir si un alza de tráfico proviene de una base de usuarios más amplia o de sesiones de escucha más prolongadas.
        """)

    st.markdown("<br/>", unsafe_allow_html=True)

    # KPI 4
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 4: Participación del Artista Líder del Mes (Cassandra)</h3>
            <p><strong>Definición:</strong> Porcentaje de las escuchas totales del mes de referencia que corresponde al artista en la primera posición del ranking mensual.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{KPI}_4 = \frac{E_{a_1}(m^{*})}{\sum_{a} E_{a}(m^{*})} \times 100\%")
        st.markdown("""
        * **Fuente de Datos:** Tabla `top_artists_by_month` de Apache Cassandra (fila con `rank = 1`).
        * **Valor Obtenido (Archivo Completo):** **BTS** concentra el **12.65%** del total de escuchas en octubre de 2026.
        * **Interpretación Técnica:** Mide el grado de concentración del catálogo musical. A pesar de existir 286,291 nombres de artistas catalogados en el lote, un solo grupo monopoliza más de un octavo de la cuota total de reproducción.
        """)

    st.markdown("<br/>", unsafe_allow_html=True)

    # KPI 5
    with st.container():
        st.markdown("""
        <div class="content-box">
            <h3>KPI 5: Entidad con Más Conexiones en el Grafo (Neo4j)</h3>
            <p><strong>Definición:</strong> Artista con la mayor cantidad de usuarios distintos conectados directamente mediante relaciones de escucha en la red.</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"C(a) = \left|\{ u : (u)\text{-[:ESCUCHA\_ARTISTA]}\rightarrow(a) \}\right|, \qquad \text{KPI}_5 = \max_{a} C(a)")
        st.markdown("""
        * **Fuente de Datos:** Consulta de grado de entrada (`in-degree`) sobre el grafo en Neo4j.
        * **Valor Obtenido (Grafo Completo):** **Linkin Park** con **1,137 oyentes únicos**.
        * **Interpretación Técnica:** Contrasta volumen frente a alcance transversal. Mientras que BTS domina el volumen acumulado (KPI 4), Linkin Park es el artista con la mayor masa de usuarios independientes en el grafo, sirviendo como el puente más concurrido de la red de afinidad.
        """)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Tabla Resumen de Valores por Corrida (Tabla 4 del informe)
    st.markdown("### Tabla Comparativa de Indicadores según la Progresión del Pipeline")
    st.markdown("Evolución de los indicadores a medida que Airflow carga los lotes incrementales (Tabla 4 del informe):")

    df_kpi_table = pd.DataFrame([
        {
            "Indicador": "1. Escuchas del 26 de octubre",
            "Corrida 1 (1 lote)": "66,562",
            "Corrida 2 (2 lotes)": "223,289",
            "Archivo Completo (10 lotes)": "1,359,824",
        },
        {
            "Indicador": "2. Crecimiento respecto al 25",
            "Corrida 1 (1 lote)": "+158.31%",
            "Corrida 2 (2 lotes)": "+666.82%",
            "Archivo Completo (10 lotes)": "+3,364.00%",
        },
        {
            "Indicador": "3. Escuchas por usuario activo",
            "Corrida 1 (1 lote)": "12.45 (5,345 usuarios)",
            "Corrida 2 (2 lotes)": "24.99 (8,936 usuarios)",
            "Archivo Completo (10 lotes)": "52.30 (26,020 usuarios)",
        },
        {
            "Indicador": "4. Participación del artista líder",
            "Corrida 1 (1 lote)": "BTS, 13.10%",
            "Corrida 2 (2 lotes)": "BTS, 17.37%",
            "Archivo Completo (10 lotes)": "BTS, 12.65%",
        },
        {
            "Indicador": "5. Artista con más oyentes",
            "Corrida 1 (1 lote)": "Linkin Park, 1,137",
            "Corrida 2 (2 lotes)": "Linkin Park, 1,137",
            "Archivo Completo (10 lotes)": "Linkin Park, 1,137",
        },
    ])
    st.table(df_kpi_table)

