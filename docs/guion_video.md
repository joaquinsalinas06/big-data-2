# Guion y Estructura para el Video Demostrativo (20 - 25 Minutos)

**Curso:** Big Data (CC) · UTEC 2026-2  
**Proyecto:** ListenBrainz (Music DNA) — Arquitectura Multimodelo  
**Fecha de Entrega:** 17 de noviembre de 2026  
**Duración Total Máxima:** 20 a 25 minutos  

---

## 👥 Distribución de Participación por Integrante

Según las instrucciones del curso, **todos los integrantes deben participar y explicar claramente su aporte técnico**, demostrando las operaciones y componentes desarrollados.

| Bloque | Tiempo | Integrante | Tema / Componente a Demostrar |
| :---: | :---: | :--- | :--- |
| **1** | 00:00 - 04:30 | **Ana María Accilio** | Introducción, Arquitectura Multimodelo y Pipeline ETL en Apache Airflow |
| **2** | 04:30 - 09:00 | **Dylan Cabezas** | Persistencia Documental en MongoDB e Índices Compuestos + Demo CRUD |
| **3** | 09:00 - 13:30 | **Matías Meneses** | Series Temporales en Apache Cassandra, Particionamiento CQL + Demo CRUD |
| **4** | 13:30 - 18:00 | **Joaquín Salinas** | Grafo en Neo4j, Comunidades de Louvain, Afinidad Jaccard + Demo CRUD |
| **5** | 18:00 - 23:00 | **José Guillermo Gálvez** | Dashboard Analítico en Streamlit, 5 KPIs Oficiales y Conclusiones Técnicas |

---

## 🎬 Detalle de Cada Bloque de Presentación

### Bloque 1: Ana María Accilio (00:00 - 04:30)
* **Objetivo:** Presentar el contexto del problema, la justificación de la arquitectura multimodelo y la orquestación automatizada.
* **Qué mostrar en pantalla:**
  1. Diapositiva / Esquema de arquitectura general (MongoDB + Cassandra + Neo4j).
  2. Interfaz web de Apache Airflow (`http://localhost:8080`).
* **Puntos a explicar:**
  - Naturaleza del dataset: ListenBrainz incremental sequence 2746 (~4.85M registros).
  - Justificación de por qué cada tipo de dato va a un motor distinto (documentos crudos en MongoDB, series de tiempo en Cassandra, relaciones de afinidad en Neo4j).
  - Demostración del DAG `music_dna_pipeline`:
    - Mostrar las 6 tareas en la vista de Grid y Graph: `extraer_datos` $\rightarrow$ `validar_datos` $\rightarrow$ `cargar_mongo` $\rightarrow$ `cargar_cassandra` $\rightarrow$ `cargar_neo4j` $\rightarrow$ `generar_kpis`.
    - Resaltar la idempotencia y el manejo de fallos en la carga incremental.

---

### Bloque 2: Dylan Andrés Cabezas (04:30 - 09:00)
* **Objetivo:** Explicar el modelo documental en MongoDB y demostrar las operaciones CRUD requeridas.
* **Qué mostrar en pantalla:**
  1. MongoDB Compass / Terminal con `mongosh` / Pestaña MongoDB del Dashboard.
  2. Terminal ejecutando: `python -m databases.mongodb.crud --pause`.
* **Puntos a explicar:**
  - Estructura semiestructurada BSON en la colección `listens` (soporte para metadatos heterogéneos de `track_metadata.additional_info`).
  - Índices compuestos implementados para acelerar las consultas:
    - Paginación temporal: `[("timestamp", -1), ("_id", -1)]`.
    - Historial de usuario: `[("user_name", 1), ("timestamp", -1)]`.
    - Filtro por artista: `[("track_metadata.artist_name", 1), ("timestamp", -1)]`.
  - **Demostración de Operaciones CRUD en vivo:**
    - **Create:** `insert_one()` creando una reproducción de prueba.
    - **Read:** `find_one()` recuperando el documento por su `_id`.
    - **Update:** `update_one()` modificando el nombre de canción y álbum remasterizado.
    - **Delete:** `delete_one()` eliminando el registro de prueba y verificando no existencia.

---

### Bloque 3: Matías Alonso Meneses (09:00 - 13:30)
* **Objetivo:** Explicar el modelo columnar de series temporales en Cassandra y demostrar las operaciones CRUD y consultas CQL.
* **Qué mostrar en pantalla:**
  1. Consola interactiva CQL en el Dashboard / `cqlsh` en terminal.
  2. Terminal ejecutando: `python -m databases.cassandra.crud --step`.
* **Puntos a explicar:**
  - Justificación de Cassandra: escrituras concurrentes masivas y consultas secuenciales por rango de tiempo.
  - Diseño de la clave primaria en la tabla `listens_by_user`:
    - **Partition Key `(user_id, month)`:** Evita particiones desbalanceadas (*wide partitions*).
    - **Clustering Key `listened_at DESC`:** Permite consultas en tiempo constante $\mathcal{O}(1)$ para las reproducciones más recientes.
  - **Demostración de Operaciones CRUD en vivo:**
    - **Inserción:** `INSERT INTO listens_by_user ...`.
    - **Consulta:** `SELECT` sobre partición confinada.
    - **Actualización:** `UPDATE` respetando clustering keys.
    - **Eliminación:** `DELETE` de la fila por clave primaria compuesta.
  - Demostración de consulta CQL analítica en el dashboard (ej. top artistas del mes con medición de latencia).

---

### Bloque 4: Joaquín Mauricio Salinas (13:30 - 18:00)
* **Objetivo:** Explicar el modelado de grafos en Neo4j, las comunidades de Louvain y demostrar el CRUD en Cypher.
* **Qué mostrar en pantalla:**
  1. Neo4j Browser (`http://localhost:7474`) o pestaña Neo4j del Dashboard.
  2. Terminal ejecutando: `python -m databases.neo4j.crud --pause`.
* **Puntos a explicar:**
  - Esquema de grafo: `(:Usuario)-[:ESCUCHA_ARTISTA]->(:Artista)` y `(:Cancion)-[:INTERPRETADA_POR]->(:Artista)`.
  - Detección de comunidades musicales mediante el algoritmo de Louvain (modularidad ponderada de $0.7825$ con 13 clústeres identificados).
  - Cálculo de artistas puente mediante centralidad de intermediación (*betweenness centrality*).
  - Sistema de recomendaciones explicables basadas en el coeficiente de similitud de Jaccard:
    $$J(A, B) = \frac{|U_A \cap U_B|}{|U_A \cup U_B|}$$
  - **Demostración de Operaciones CRUD en vivo:**
    - **Crear:** Nodos `(:Usuario)` y `(:Cancion)` y relación `[:ESCUCHO]`.
    - **Consultar:** `MATCH` de la relación y verificación de propiedades.
    - **Actualizar:** `SET r.cantidad = 5`.
    - **Eliminar:** `DETACH DELETE` de los nodos y relaciones de prueba.

---

### Bloque 5: José Guillermo Gálvez (18:00 - 23:00)
* **Objetivo:** Demostrar la integración integral en el Dashboard Analítico de Streamlit, analizar los 5 KPIs oficiales y cerrar con las conclusiones.
* **Qué mostrar en pantalla:**
  1. Dashboard en navegador: `http://localhost:8501`.
  2. Informe Técnico PDF (`informe/main.pdf`).
* **Puntos a explicar:**
  - **Arquitectura de la UI:** Conectividad multimodelo con verificación ultrarrápida de sockets (150 ms) y consumo directo del snapshot de Airflow (`data/airflow/kpis_latest.json` y `kpi_runs`).
  - **Los 5 KPIs Oficiales (Día de corte: 26 de octubre de 2026):**
    1. *KPI 1 (Escuchas del Día):* $1\,359\,824$ eventos procesados (28.0% del total del lote).
    2. *KPI 2 (Crecimiento Diario):* $+3\,364.0\%$ de incremento interdiario debido a la concentración de sincronizaciones de clientes acumuladas en la ventana de corte.
    3. *KPI 3 (Escuchas / Usuario Activo):* $52.3$ eventos/usuario ($26\,020$ usuarios activos).
    4. *KPI 4 (Participación del Artista Líder):* BTS concentra el $12.65\%$ del tráfico mensual en octubre de 2026 ($48\,640$ escuchas).
    5. *KPI 5 (Entidad con Más Conexiones):* Linkin Park lidera el grafo con $1\,137$ oyentes únicos independientes, demostrando alcance transversal frente a la concentración de volumen de BTS.
  - **Visualizaciones interactivas:**
    - Serie temporal interactiva con selector de métrica (escuchas, crecimiento %, usuarios).
    - Ranking horizontal con porcentajes de participación del catálogo.
    - Tabla comparativa de corridas del pipeline mostrando la evolución desde 1 lote hasta los 10 lotes completos.
  - **Conclusiones Técnicas del Proyecto:**
    - Cumplimiento de los principios de especialización de almacenamiento: ningún motor único habría podido resolver simultáneamente documentos semiestructurados, series masivas y grafos densos con latencias submilisegundo.
    - Robustez de la automatización orquestada por Airflow y reproducibilidad del entorno mediante Docker y pruebas unitarias automáticas con PyTest.
