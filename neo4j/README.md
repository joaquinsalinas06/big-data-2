# ListenBrainz — Neo4j

Tres comandos, sin opciones de consola:

```bash
python neo4j/load.py
python neo4j/analyze.py
python neo4j/main.py
```

## Organización

```text
neo4j/
├── load.py                 # Preparación y carga del dataset
├── analyze.py              # Afinidades, comunidades y publicación de resultados
├── main.py                 # Consultas y CRUD
├── database.py             # Conexión y rutas
├── graph/
│   ├── queries.py          # Consultas de lectura
│   └── crud.py             # Operaciones sobre entidades ficticias
├── model/                  # Esquema y diagrama editable de Arrows.app
│   └── schema.py           # Tablas de preparación y restricciones de Neo4j
├── tests/
│   └── test_graph.py
└── README.md
```

Para estudiar el código, empezar por `main.py`, después `graph/queries.py`. Las funciones siguen el manual del profesor: `def ... (tx)`, una variable `query`, parámetros Cypher y llamadas mediante `session.execute_read` o `session.execute_write`. Archivos, carpetas, constantes y funciones tienen nombres en inglés; las explicaciones y el modelo de datos existente se mantienen en español.

El CRUD es un módulo Python importable, sin servidor ni FastAPI. Desde la carpeta `neo4j`, se puede usar en otro script así:

```python
from database import DATABASE, connect
from graph import crud

with connect() as driver, driver.session(database=DATABASE) as session:
    try:
        session.execute_write(crud.create_nodes)
        session.execute_write(crud.create_relationship)
        session.execute_write(crud.update_properties, 3)
        print(session.execute_read(crud.get_listens))
    finally:
        session.execute_write(crud.delete_nodes)
```

Importar el módulo no ejecuta operaciones ni abre conexiones. Estas funciones pertenecen al CRUD del grupo manual: crean y modifican entidades ficticias, no escuchas reales. Las consultas del lote se llaman del mismo modo, usando `graph.queries`.

## Primera ejecución

Descargar el dataset siguiendo el [README del proyecto](../README.md). Instalar Python 3.12 o posterior, las dependencias y Docker con al menos 6 GB disponibles para este proyecto. En Windows, el extractor existente requiere Python 3.14 o posterior. Reservar al menos 10 GB de disco para el dataset, intermedios y Neo4j.

En macOS/Linux, desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Cambiar la contraseña de `.env` y encender Docker. Después:

```bash
docker compose up -d --wait
python neo4j/load.py
python neo4j/analyze.py
python neo4j/main.py
```

En PowerShell, crear el entorno con `python -m venv .venv`, copiar la configuración con `Copy-Item .env.example .env` y usar `.\.venv\Scripts\python.exe` en lugar de `python`. Las dependencias se instalan con `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

El lote y las rutas están en `database.py`. El usuario 20 y el artista Motörhead son ejemplos del lote; se cambian en `USER_ID` y `ARTIST`, al principio de `main.py`. No se muestran nombres de usuario ni contraseñas. El script imprime un mensaje cuando una consulta no tiene resultados.

## Datos y carga

La entrada común es `data/processed/listens_full.jsonl`: 4 855 809 escuchas. La preparación valida cada registro, calcula SHA-256 y agrupa en `data/neo4j/prepared.sqlite`. Es un intermedio local; el grafo se almacena en Neo4j.

`load.py` reutiliza la preparación existente. Para regenerarla desde el JSONL, borrar únicamente `data/neo4j/prepared.sqlite` y repetir el comando. Si la nueva preparación tiene otro contenido para el mismo lote, la carga se detiene para no reemplazarlo silenciosamente.

Los lotes de 1 000 filas son un detalle interno para limitar memoria, no una opción que haya que configurar. `MERGE` y cantidades absolutas permiten repetir la carga sin sumar dos veces las mismas escuchas. Si se interrumpe, repetir `load.py`: vuelve a recorrer la preparación desde el principio. No hay checkpoints ni modos de recarga. La carga comprueba al terminar las cantidades de relaciones y reproducciones.

Ejecutar una carga o análisis a la vez. El análisis se publica en una transacción: si falla, se conserva el anterior. Repetir `analyze.py` recalcula solo los datos derivados. No se borra el dataset ni el volumen existente durante esta reorganización.

## Modelo del grafo

El [JSON de Arrows.app](model/graph.arrows.json) permite editar el diagrama. Sus datos de ejemplo son ficticios.

| Relación | Qué representa |
| --- | --- |
| `Usuario → ESCUCHO → Cancion` | Cantidad de reproducciones, primera y última fecha UTC, y lote. |
| `Cancion → INTERPRETADA_POR → Artista` | Asociación observada en los metadatos del lote. |
| `Usuario → ESCUCHA_ARTISTA → Artista` | Cantidad y proporción de escucha dentro del historial del usuario en el lote. |
| `Artista — AFIN_A — Artista` | Público compartido y similitud Jaccard calculados; se guarda una vez y se consulta en ambos sentidos. |
| `Artista → PERTENECE_A → Comunidad` | Agrupación calculada y coeficiente de artista puente. |

Usuarios se identifican por `user_id`, canciones por `recording_msid` y artistas por nombre exacto. No se fusionan canciones por título. Un nombre no garantiza identidad musical canónica; las comunidades tampoco equivalen a géneros confirmados. Cada reproducción sigue en el JSONL original; el grafo resume repeticiones del mismo usuario y canción. `Lote` y `Analisis` conservan procedencia y el análisis activo.

`graph/crud.py` opera sobre nodos `Usuario` y `Cancion` etiquetados además como `ManagedRecord`, dentro de un grupo y lote ficticios. El bloque `finally` del programa limpia sus nodos. No modifica las escuchas reales. El esquema está en `model/schema.py` y se aplica automáticamente durante la carga.

## Afinidades, comunidades e indicadores

Las decisiones están juntas en `analyze.py`: hasta 500 artistas con al menos 20 usuarios; top 20 de esos artistas por usuario; mínimo 10 usuarios comunes y Jaccard ≥ 0,05; unión de los 10 mejores vecinos por artista. Louvain utiliza resolución 1 y semilla 42. Los aislados quedan sin comunidad.

`analyze()` coordina cinco pasos: `select_audiences`, `affinity_graph`, `detect_communities`, `compute_indicators` y `build_result`. `save_analysis` publica el resultado dentro de una única transacción. Se mantienen en el mismo archivo para poder seguir el cálculo sin abrir más carpetas.

La intersección y unión de Jaccard usan las mismas audiencias filtradas por el top 20. Las recomendaciones suman `proporción de escucha del artista conocido × Jaccard` y excluyen artistas ya escuchados. Las canciones recomendadas se ordenan por el puntaje de su artista y su audiencia en el lote, excluyendo canciones ya escuchadas.

| Indicador | Cálculo e interpretación |
| --- | --- |
| Afinidad | Usuarios comunes / usuarios en la unión de las audiencias filtradas. Describe cercanía de públicos. |
| Alcance de comunidad | Usuarios distintos que escucharon alguno de sus artistas. Las audiencias de comunidades pueden solaparse. |
| Artista puente | `1 − Σ (peso hacia una comunidad / peso total)²`. Mide distribución de conexiones entre comunidades. |
| Diversidad | Entropía de las proporciones de escucha por comunidad, dividida por `ln(K)` de comunidades escuchadas. Cero con una comunidad y `null` sin escuchas clasificadas. |
| Cobertura | Usuarios con al menos una recomendación / usuarios del lote. No mide acierto. |
| Modularidad | `Σ [peso interno / peso total − (grado de comunidad / (2 × peso total))²]`, con resolución 1. Describe la partición del grafo podado; es `null` sin aristas. |

El análisis también informa cuántas escuchas pudieron clasificarse. El [registro de resultados](../docs/neo4j-results.md) conserva la referencia del lote: 13 comunidades, 1 553 afinidades y cobertura de 62,03 %. Son resultados del lote de ingesta, no de toda ListenBrainz; aún no se mide precisión predictiva.

## Ver el grafo y probar el código

Abrir [Neo4j Browser](http://localhost:7474), conectar con las credenciales de `.env` y ejecutar, por ejemplo:

```cypher
MATCH (:Lote {id:'listenbrainz-2746',estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis)
MATCH (a:Artista {nombre:'Motörhead'})-[r:AFIN_A {analisis:an.id}]-(b:Artista)
RETURN a,r,b LIMIT 10
```

```bash
python -m unittest discover -s neo4j/tests -v
```

Para incluir la carga, análisis y CRUD sobre un lote ficticio con Neo4j encendido:

```bash
NEO4J_INTEGRATION=1 python -m unittest discover -s neo4j/tests -v
```

En PowerShell, definir antes `$env:NEO4J_INTEGRATION="1"`. Las pruebas no sustituyen el ensayo de la exposición. La ejecución nativa en Windows y Linux sigue pendiente.

Los datos persisten con `docker compose stop` y `docker compose up -d --wait`. `docker compose down -v` elimina los volúmenes; no usarlo para un reinicio normal. Cambiar `.env` no cambia una contraseña ya inicializada en el volumen de Neo4j.
