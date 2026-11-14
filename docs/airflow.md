# Airflow — Music DNA

El DAG `music_dna_pipeline` automatiza todo el flujo del proyecto: toma el dump de ListenBrainz, lo valida, lo carga en MongoDB, Cassandra y Neo4j y al final calcula los KPIs que lee el dashboard. Corre todos los días (`@daily`) y en cada corrida agrega un bloque nuevo de escuchas, así se simula que los datos llegan de forma incremental.

El DAG no tiene lógica propia de carga ni de análisis. Cada tarea llama a las funciones que ya están en `databases/` (las mismas que se usan por consola), de modo que lo que se probó por separado en cada base es exactamente lo que corre en Airflow.

El código está en [airflow/dags/music_dna_dag.py](../airflow/dags/music_dna_dag.py).

## Stack en Docker

Todo se levanta con el `docker-compose.yml` de la raíz. A las tres bases que ya existían se agregaron cuatro servicios:

| Servicio | Imagen | Puerto | Para qué |
| --- | --- | --- | --- |
| `mongodb` | mongo:7.0 | 27017 | Documentos originales y snapshots de KPIs (`kpi_runs`) |
| `cassandra` | cassandra:5.0 | 9042 | Serie temporal y agregados por día y mes |
| `neo4j` | neo4j:5.26.0 | 7474, 7687 | Grafo usuario–canción–artista y comunidades |
| `postgres` | postgres:16 | — | Base de metadatos de Airflow (corridas, estados, XCom) |
| `airflow-init` | imagen propia | — | Corre una vez: migra la base de metadatos y crea el usuario admin/admin |
| `airflow-webserver` | imagen propia | 8080 | Interfaz web |
| `airflow-scheduler` | imagen propia | — | Programa las corridas y ejecuta las tareas |

La imagen propia ([airflow/Dockerfile](../airflow/Dockerfile)) parte de `apache/airflow:2.10.5-python3.11`. Le agrega `curl`, `zstd` y `tar`, que necesita `scripts/download_dataset.sh`, y los paquetes del pipeline listados en [airflow/requirements.txt](../airflow/requirements.txt): pymongo, pydantic, cassandra-driver, neo4j, networkx, python-dotenv y pytz. Se instalan con el archivo de constraints oficial de Airflow para no cambiar versiones de sus propias dependencias. Streamlit y FastAPI no se instalan porque no corren dentro de Airflow.

Usamos `LocalExecutor`: las tareas corren como procesos dentro del contenedor del scheduler y pueden ir en paralelo. Para un solo equipo alcanza; Celery o Kubernetes harían falta recién con varias máquinas.

Dentro de los contenedores se montan `airflow/dags`, `databases`, `scripts` y `data` en `/opt/airflow/`, y `PYTHONPATH=/opt/airflow`. Así funcionan los imports `databases.mongodb...` y las rutas de Neo4j, que se calculan desde la raíz del proyecto (`ROOT = parents[2]` en `databases/neo4j/connection.py` queda en `/opt/airflow`). Las bases se alcanzan por nombre de servicio (`mongodb://mongodb:27017/`, `CASSANDRA_HOSTS=cassandra`, `bolt://neo4j:7687`), no por localhost. La clave de Neo4j se lee del `.env`.

Los servicios de Airflow esperan con `depends_on: condition: service_healthy` a que postgres y las tres bases respondan su healthcheck. Cassandra es la que más tarda (alrededor de un minuto).

## El DAG

| Parámetro | Valor |
| --- | --- |
| `dag_id` | `music_dna_pipeline` |
| Programación | `@daily`, desde el 2026-11-01, `catchup=False` |
| Corridas simultáneas | `max_active_runs=1` |
| Reintentos | 2 por tarea, con 5 minutos de espera |
| Tiempo máximo por tarea | 2 horas |
| Dataset | `/opt/airflow/data/processed/listens_full.jsonl` |

```text
extraer_datos >> validar_y_limpiar >> [cargar_mongodb, cargar_cassandra, cargar_neo4j] >> generar_kpis
```

`catchup=False` evita que al activar el DAG se lancen corridas atrasadas por cada día desde el `start_date`. `max_active_runs=1` es necesario porque cada corrida continúa donde quedó la anterior: dos corridas a la vez intentarían cargar el mismo bloque.

Los tamaños de lote se configuran en Admin > Variables, sin tocar el código:

| Variable | Por defecto | Uso |
| --- | --- | --- |
| `music_dna_mongo_limit` | 100000 | Documentos nuevos por corrida en Mongo |
| `music_dna_mongo_batch_size` | 2000 | Documentos por `insert_many` |
| `music_dna_cassandra_batch_size` | 500000 | Líneas por lote de Cassandra. No conviene cambiarlo después de la primera carga |

### Las tareas

**1. `extraer_datos`.** Si el JSONL ya está en `data/processed/`, lo reporta y no descarga nada. Si no, ejecuta `bash scripts/download_dataset.sh --extract`, que baja el incremental 2746 de MetaBrainz (~238 MB), verifica el SHA-256 oficial y extrae el archivo de escuchas (~2,6 GB). Devuelve la ruta, el tamaño y la cantidad de líneas. Va primero porque todas las demás leen ese archivo.

**2. `validar_y_limpiar`.** Ejecuta `scripts/validate_dataset.py --file <ruta>`, que recorre el archivo en streaming y comprueba que cada línea sea un objeto JSON con `user_name`, `timestamp` entero, artista y canción, y que haya exactamente 4 855 809 registros. Si el script termina con error, la tarea falla y las cargas no se ejecutan. Además deja `data/airflow/validacion.json` con los registros leídos, válidos e inválidos y el rango de fechas.

Esta tarea es un control de calidad del archivo completo. La limpieza registro por registro la hace cada loader al cargar, porque cada base necesita cosas distintas: Mongo valida el esquema con Pydantic y descarta duplicados por huella SHA-256 del documento; Cassandra exige `user_id` y `timestamp` enteros y artista y canción no vacíos, y descarta duplicados dentro del lote por un id determinista; Neo4j exige además `recording_msid`. Hacerlo dos veces en Airflow solo duplicaría código.

**3. `cargar_mongodb`.** Llama a `load_to_mongodb` con `limit=100000`, `batch_size=2000` y el estado en `data/airflow/mongo_state.sqlite3`. En ese SQLite el loader guarda en qué byte del archivo quedó y las huellas de los documentos ya insertados, así que cada corrida sigue desde donde terminó la anterior y no inserta dos veces el mismo documento.

**4. `cargar_cassandra`.** Primero crea el keyspace y las tablas con `create_schema` (son `CREATE ... IF NOT EXISTS`, no pasa nada si ya existen). Después llama a `load_listens(session, ruta, max_batches=1)`: carga un lote nuevo de 500 000 líneas en `listens_by_user`, lo registra en `load_batches` y recalcula `daily_stats`, `top_artists_by_month` y las demás tablas agregadas con todo lo cargado hasta ese momento.

**5. `cargar_neo4j`.** Sigue el mismo flujo que `main()` de `databases/neo4j/loader.py`. Si no existe `data/neo4j/prepared.sqlite`, llama a `prepare`, que agrega las escuchas por usuario–canción y usuario–artista. Luego consulta el nodo `(:Lote {id: 'listenbrainz-2746'})`: si su estado es `completo`, lo registra en el log y no recarga; si no, ejecuta `load_data`. Al final cuenta usuarios, canciones, relaciones y escuchas del lote.

Las tres cargas dependen solo de la validación y no entre sí, por eso van en paralelo. Si una falla, las otras dos terminan igual y al reintentar solo se repite la que falló.

**6. `generar_kpis`.** Espera a las tres cargas. Ejecuta el análisis de Neo4j (`analyze.main()`), que calcula afinidades entre artistas y comunidades con Louvain y guarda el resultado en el grafo y en `data/neo4j/analysis.json`. Luego consulta Cassandra con `get_daily_stats`, `get_top_artists` y `get_load_batches`, busca en Neo4j el artista con más oyentes y cuenta los documentos de Mongo. Con eso arma los 5 KPIs y guarda un snapshot con el `run_id` y la fecha en la colección `kpi_runs` de Mongo y en `data/airflow/kpis_latest.json`.

Cada tarea devuelve un diccionario pequeño (conteos, rutas, banderas) que queda como XCom y se ve en la pestaña XCom de cada instancia. Los datos grandes nunca pasan por XCom: las tareas se comunican por el archivo y por las bases.

## Cómo se simula la carga incremental

El dataset es un solo archivo, así que la llegada de datos nuevos se simula cargando una parte en cada corrida:

| Base | Qué agrega cada corrida | Corridas para el archivo completo |
| --- | --- | --- |
| MongoDB | 100 000 documentos nuevos, desde el byte donde quedó la anterior | 40 (el loader tiene un tope de 4 000 000 documentos) |
| Cassandra | 1 lote de 500 000 líneas y recálculo de agregados | 10 |
| Neo4j | Nada después de la primera carga completa | 1 |

Para que Mongo fuera incremental hubo que corregir `load_to_mongodb`: le pasaba `target=limit` a `import_file`, y como `target` es el total de documentos que debe tener la colección, desde la segunda corrida ya estaba alcanzado y no insertaba nada. Ahora el target es lo que ya hay más `limit`, con el tope de 4 000 000 que valida `process_file`.

En Cassandra el id de cada lote es `listens_full.jsonl:<primera línea>-<última línea>`, por eso el tamaño de lote tiene que ser siempre el mismo. Si se cambiara, los ids no coincidirían con los ya registrados y los agregados contarían dos veces.

Como los KPIs se recalculan en cada corrida con lo que hay en las bases, cambian a medida que crece Cassandra. Una vez que se terminan los lotes, las corridas siguen funcionando pero los valores se estabilizan.

## Por qué Neo4j se carga completo

El loader de Neo4j no está pensado para cargar por partes. `prepare` exige el archivo completo (falla si no tiene 4 855 809 filas) y guarda el SHA-256 del archivo en el nodo `Lote`. Las relaciones `ESCUCHO` y `ESCUCHA_ARTISTA` guardan la cantidad total de escuchas de cada par usuario–canción y usuario–artista, y la proporción de cada artista en el historial del usuario. Esos valores se calculan sobre todo el lote: cargar por partes obligaría a sumar sobre lo ya cargado y recalcular las proporciones, es decir, otro loader.

Además el grafo responde preguntas de relaciones (quién escucha a quién, comunidades, recomendaciones) que no ganan nada con ver el lote a medias. Por eso la tarea carga el grafo completo la primera vez y en las siguientes solo comprueba que el lote esté completo. La carga usa `MERGE`, así que aunque se repitiera no duplicaría nodos ni relaciones.

## Idempotencia y reintentos

Cada tarea se puede repetir sin dejar datos duplicados, y eso es lo que permite los 2 reintentos automáticos:

| Tarea | Qué pasa si se repite |
| --- | --- |
| `extraer_datos` | Si el archivo ya está, no descarga. La extracción escribe a un `.part` y lo renombra al final, nunca deja un archivo a medias |
| `validar_y_limpiar` | Solo lee el archivo y sobrescribe el reporte |
| `cargar_mongodb` | Sigue desde el último checkpoint; los documentos tienen `_id` derivado de su huella, así que un reintento no los duplica |
| `cargar_cassandra` | Los lotes registrados en `load_batches` se saltan, las escuchas tienen id determinista (el `INSERT` sobrescribe) y los agregados se reemplazan, no se suman |
| `cargar_neo4j` | Si el lote está `completo`, no hace nada; si quedó en `cargando`, `load_data` vuelve a correr con `MERGE` |
| `generar_kpis` | El análisis borra y vuelve a crear sus propias afinidades y comunidades; el snapshot se guarda con `replace_one` usando el `run_id` como `_id` |

Un detalle para el reintento de Mongo: si una corrida falla en medio de un lote, el checkpoint queda en el último lote confirmado y las huellas se reconstruyen leyendo la colección al empezar, así que lo que alcanzó a entrar no se vuelve a insertar.

## Cómo levantarlo y ejecutarlo

Docker necesita unos 10 GB de memoria asignada: Cassandra y Neo4j tienen 2 GB de heap cada uno y Neo4j 1 GB más de page cache.

```bash
cp .env.example .env                     # en Linux, poner AIRFLOW_UID=$(id -u)
docker compose build                     # construye la imagen de Airflow
docker compose up -d                     # bases, postgres y Airflow
docker compose ps                        # esperar a que todo quede "healthy"
```

La interfaz queda en http://localhost:8080 (usuario `admin`, clave `admin`). El DAG aparece pausado: se activa con el interruptor y se lanza con el botón de play. También se puede correr completo desde la terminal:

```bash
docker compose exec airflow-scheduler airflow dags list-import-errors
docker compose exec airflow-scheduler airflow dags test music_dna_pipeline
```

Si el dataset no está en `data/processed/`, la primera tarea lo descarga. Para revisar el resultado:

```bash
cat data/airflow/kpis_latest.json
docker compose exec mongodb mongosh listenbrainz_db --eval "db.listens.countDocuments(); db.kpi_runs.countDocuments()"
docker compose exec cassandra cqlsh -e "SELECT count(*) FROM music_dna.load_batches"
```

## KPIs

Los cinco KPIs se calculan en `generar_kpis`. Los cuatro primeros salen de las tablas agregadas de Cassandra y el quinto del grafo de Neo4j.

Los de Cassandra se calculan sobre un día de referencia `d`: el penúltimo día de `daily_stats`. El último se descarta porque el dump se cortó el 27 de octubre a las 00:01 y ese día tiene solo 4 escuchas; usarlo daría un crecimiento de −100 % que no dice nada. Como el dataset es un lote de ingesta, los valores reflejan qué enviaron los usuarios a ListenBrainz en ese periodo, no la popularidad general (ver [docs/dataset.md](dataset.md)).

| KPI | Definición | Fórmula | Fuente |
| --- | --- | --- | --- |
| Escuchas procesadas por día | Escuchas cargadas con fecha `d` (UTC) | `E(d)` | `daily_stats.listens` |
| Crecimiento diario | Variación de escuchas respecto al día anterior | `(E(d) − E(d−1)) / E(d−1) × 100` | `daily_stats.growth_pct` |
| Escuchas por usuario activo | Promedio de escuchas de los usuarios que escucharon algo ese día | `E(d) / U(d)`, con `U(d)` = usuarios distintos con escuchas en `d` | `daily_stats.listens_per_user` |
| Participación del artista líder | Porcentaje de las escuchas del mes que se lleva el artista más escuchado | `escuchas del artista rank 1 en m / escuchas totales de m × 100`, con `m` el mes de `d` | `top_artists_by_month.share_pct` |
| Entidad con más conexiones | Artista con más usuarios distintos conectados en el grafo | `C(a)` = usuarios distintos `u` con `(u)-[:ESCUCHA_ARTISTA]->(a)`; se reporta el artista con mayor `C(a)` | Neo4j |

Interpretación:

- **Escuchas por día** mide el volumen que procesa el pipeline. Sirve para ver si un día viene con muchos menos datos de lo normal (un corte del dump o una falla de la fuente).
- **Crecimiento diario** muestra la tendencia. En este dataset tiene saltos muy grandes porque el incremental concentra la ingesta en los últimos días de octubre: el 26 de octubre tiene el 28 % de todas las escuchas. Un salto así indica un cambio en la ingesta, no que la gente haya escuchado 30 veces más música.
- **Escuchas por usuario activo** separa intensidad de alcance: si suben las escuchas pero no los usuarios, los mismos usuarios están escuchando más.
- **Participación del artista líder** mide concentración. Un valor alto (BTS tiene 12,65 % de octubre según la carga completa de Cassandra) indica que un solo artista domina el mes; uno bajo, que las escuchas están repartidas.
- **Entidad con más conexiones** es el grado de entrada del artista en el grafo usuario–artista: cuántos usuarios distintos lo escuchan, sin importar cuántas veces. Mide alcance, no volumen; un artista puede tener muchas escuchas de pocos fans y otro pocas escuchas de mucha gente.

Como métricas de seguimiento el snapshot incluye el total acumulado de documentos en Mongo, los lotes y escuchas cargados en Cassandra, los totales del grafo y del análisis de Neo4j (comunidades, modularidad y cobertura de recomendaciones).

### Formato del snapshot

`data/airflow/kpis_latest.json` y cada documento de `kpi_runs` tienen la misma forma, pensada para que el dashboard la lea sin transformar:

```json
{
  "run_id": "scheduled__2026-11-14T00:00:00+00:00",
  "fecha_logica": "2026-11-14T00:00:00+00:00",
  "generado_en": "2026-11-15T00:12:41+00:00",
  "dia_referencia": "2026-10-26",
  "mes_referencia": "2026-10",
  "kpis": {
    "escuchas_por_dia": {"nombre": "Escuchas procesadas por día", "valor": 0, "unidad": "escuchas", "dia": "2026-10-26", "fuente": "cassandra.daily_stats"},
    "crecimiento_diario_pct": {"nombre": "...", "valor": 0.0, "unidad": "%"},
    "escuchas_por_usuario_activo": {"nombre": "...", "valor": 0.0, "unidad": "escuchas/usuario", "usuarios_activos": 0},
    "participacion_artista_lider": {"nombre": "...", "valor": 0.0, "unidad": "%", "artista": "...", "escuchas": 0, "mes": "2026-10"},
    "entidad_mas_conectada": {"nombre": "...", "valor": 0, "unidad": "oyentes", "artista": "..."}
  },
  "seguimiento": {"mongo_documentos": 0, "cassandra_lotes_cargados": 0, "cassandra_escuchas_cargadas": 0, "neo4j_escuchas": 0, "neo4j_comunidades": 0},
  "serie_diaria": [{"dia": "2026-10-26", "escuchas": 0, "usuarios_activos": 0, "escuchas_por_usuario": 0.0, "crecimiento_pct": 0.0}]
}
```

`serie_diaria` trae los últimos 30 días del año de referencia para graficar la tendencia. Para ver la evolución entre corridas, el dashboard puede leer `kpi_runs` ordenado por `generado_en`.

## Limitaciones

- Cada corrida de Mongo recorre la colección completa para reconstruir las huellas de duplicados, y cada corrida de Cassandra relee los lotes ya cargados para recalcular los agregados. Las dos tareas tardan más a medida que crecen las bases.
- La carga incremental es simulada: siempre es el mismo archivo. Con datos reales, `extraer_datos` tendría que bajar el siguiente incremental de ListenBrainz y Neo4j necesitaría un loader que sume sobre lo ya cargado.
- Es un solo nodo de cada base y Airflow con `LocalExecutor` en la misma máquina. Sirve para el proyecto, no para producción.
