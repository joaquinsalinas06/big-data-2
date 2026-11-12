# Cassandra — Music DNA

Cassandra guarda las escuchas como **serie temporal** y las **métricas agregadas por fecha** que consume el dashboard. MongoDB conserva el documento original y Neo4j las relaciones; aquí está lo que se consulta por tiempo y en volumen.

## Por qué Cassandra para esta parte

- **Escritura masiva:** son 4,86 millones de escuchas y el DAG puede seguir agregando lotes.
- **Consultas conocidas de antemano:** el dashboard pide siempre lo mismo (actividad por día, ranking del mes, historial de un usuario). En Cassandra se diseña **una tabla por consulta** y cada lectura va directo a una sola partición, sin importar cuántos datos haya.
- **Series temporales:** la clave de clustering deja las filas ordenadas por fecha dentro de cada partición.

El costo es repetir datos entre tablas (desnormalizar) y no poder hacer consultas ad hoc: si mañana se necesita otra pregunta, se agrega otra tabla.

## Modelo

| Tabla | Partición | Clustering | Consulta que responde |
| --- | --- | --- | --- |
| `listens_by_user` | `(user_id, month)` | `listened_at DESC, listen_id` | Historial de un usuario en un mes |
| `daily_stats` | `year` | `day` | Serie diaria del año con sus KPIs |
| `top_artists_by_month` | `month` | `rank` | Top de artistas del mes, ya ordenado |
| `artist_monthly_listens` | `artist_name` | `month` | Evolución mensual de un artista |
| `user_daily_listens` | `user_id` | `day` | Actividad diaria de un usuario |
| `load_batches` | `batch_id` | — | Qué lotes del archivo ya se cargaron |

El esquema completo está en [schema.cql](schema.cql).

Decisiones del modelo:

- **`listens_by_user` se particiona por usuario y mes**, no solo por usuario. Así una partición no crece sin límite: la más grande del dataset tiene 14 205 filas.
- **`top_artists_by_month` usa `rank` como clustering** porque Cassandra solo ordena por columnas de clustering. El ranking se calcula al cargar y la consulta es un `SELECT ... LIMIT 10`.
- **No se guarda `user_name`**: con `user_id` alcanza y el dashboard no necesita exponer nombres.

## Cómo correrlo

Desde la raíz del repositorio, con el dataset ya descargado en `data/processed/listens_full.jsonl`:

```powershell
docker compose -f databases/cassandra/docker-compose.yml up -d     # esperar ~1 min a que quede "healthy"

python -m venv .venv
.venv\Scripts\activate                 # Linux/macOS: source .venv/bin/activate
pip install cassandra-driver==3.30.1 pyasyncore

python -m databases.cassandra.init_schema     # crea keyspace y tablas (--reset borra todo)
python -m databases.cassandra.loader    # carga las 4,86 M escuchas y calcula los agregados
python -m databases.cassandra.queries         # resumen: KPIs de los últimos días y top artistas
python -m databases.cassandra.crud --step     # demo CRUD paso a paso
```

`pyasyncore` hace falta en Python 3.12 o superior: el driver usa el módulo `asyncore`, que se eliminó en esa versión, y sin él falla al importar en Windows. En Python 3.10 y 3.11 se puede omitir.

## Cómo funciona el CRUD

El CRUD está en [crud.py](crud.py) y trabaja sobre `listens_by_user`: una fila es una escucha.

La clave primaria es `((user_id, month), listened_at, listen_id)`. `month` se calcula a partir de `listened_at`, así que para ubicar una escucha basta con `user_id`, `listened_at` y `listen_id`. `listen_id` es un UUID determinista calculado con los datos de la escucha: la misma escucha siempre genera el mismo id.

| Operación | Función | CQL |
| --- | --- | --- |
| Insertar | `insert_listen(...)` | `INSERT INTO listens_by_user (...) VALUES (...)` |
| Consultar una | `get_listen(...)` | `SELECT * ... WHERE user_id = ? AND month = ? AND listened_at = ? AND listen_id = ?` |
| Consultar el mes | `get_user_listens(...)` | `SELECT * ... WHERE user_id = ? AND month = ? LIMIT ?` |
| Actualizar | `update_listen(...)` | `UPDATE listens_by_user SET track_name = ?, release_name = ? WHERE <clave>` |
| Eliminar | `delete_listen(...)` | `DELETE FROM listens_by_user WHERE <clave>` |

Dos detalles de Cassandra que explican el código:

1. **`INSERT` y `UPDATE` son "upserts".** Un `UPDATE` sobre una fila que no existe la crea. Por eso `update_listen` y `delete_listen` primero leen la fila y devuelven `False` si no existe.
2. **No usamos `IF EXISTS`.** Lo probamos y fallaba: esas escrituras (transacciones ligeras) usan el reloj del servidor y las normales el del cliente. Con Docker en Windows el `UPDATE ... IF EXISTS` respondía "aplicado", pero quedaba con un timestamp anterior al del `INSERT` y Cassandra se quedaba con el valor viejo.

La demo `python -m databases.cassandra.crud --step` usa el usuario `-1`, que no existe en ListenBrainz: inserta una escucha, la lee, la corrige, la borra y comprueba que ya no está. Termina con una lectura real: las últimas escuchas de un usuario del dataset. Con `--step` se detiene entre pasos para explicarlo en el video.

El CRUD no modifica las tablas agregadas; esas se recalculan en cada carga.

## Carga por lotes (paso 4 del DAG)

[load_listens.py](load_listens.py) lee el JSONL por lotes de 500 000 líneas:

1. Limpia cada línea (`user_id` y `timestamp` enteros, artista y canción no vacíos) y descarta duplicados dentro del lote.
2. Escribe las escuchas nuevas en `listens_by_user` y registra el lote en `load_batches`.
3. Recalcula las tablas agregadas con **todas** las escuchas cargadas hasta ese momento y las sobrescribe.

Repetir la carga no duplica nada: las escuchas tienen id determinista (el `INSERT` sobrescribe la misma fila), los lotes registrados no se vuelven a escribir y los agregados se reemplazan en vez de sumarse.

Para **simular actualizaciones incrementales**, el DAG puede cargar un lote por ejecución con `--max-batches 1`: cada corrida agrega 500 000 escuchas nuevas y los KPIs se actualizan. Hay que usar siempre el mismo `--batch-size`, porque el id del lote depende de ese tamaño.

Optimizaciones que hicieron falta:

- **BATCH por partición.** Las filas de la misma partición se envían juntas en un `UNLOGGED BATCH` de hasta 30 filas, que Cassandra aplica como una sola mutación. Fue unas 13 veces más rápido que una escritura por fila.
- **Sin counters.** La primera versión usaba columnas `counter`, pero cada incremento lee antes de escribir y con ~1 millón de claves artista-mes la carga se volvía cada vez más lenta. Además, si el DAG reintenta un lote, un counter suma dos veces. Recalcular y sobrescribir resultó más rápido y seguro.
- **`UNSET_VALUE` en vez de `None`** para campos opcionales: insertar `None` crea un tombstone (marca de borrado) por cada fila.

## Resultados con el dataset completo

Medido en un notebook con Windows 11, 20 GB de RAM y Cassandra 5.0 en Docker (un nodo, heap de 2 GB), cargando el archivo completo del incremental 2746.

**Carga** (`python -m databases.cassandra.loader` con las tablas vacías):

| Etapa | Tiempo |
| --- | --- |
| 10 lotes de escuchas (lectura, limpieza y escritura) | 343 s, entre 7 500 y 21 600 filas/s según el lote |
| Recálculo de las tablas agregadas | 196 s |
| **Total** | **553 s (~9 min)** |
| Segunda ejecución sin lotes nuevos | 439 s; los totales no cambian (4 855 809) |

La segunda ejecución demuestra que es idempotente, pero también muestra el costo del diseño: cada corrida relee el archivo para recalcular los agregados, así que tarda ~7 min aunque no haya lotes nuevos. Para el DAG alcanza; si hiciera falta bajarlo, habría que recalcular solo los días y meses que tocó el lote nuevo.

**Filas resultantes:**

| Tabla | Filas |
| --- | --- |
| `listens_by_user` | 4 855 809 en 30 315 particiones (la mayor, 14 205 filas) |
| `artist_monthly_listens` | 961 898 |
| `user_daily_listens` | 113 827 |
| `daily_stats` | 7 575 días, del 2005-02-13 al 2026-10-27 |
| `top_artists_by_month` | hasta 50 artistas por cada uno de los 260 meses |

Comprobamos el total de tres formas independientes: suma de `load_batches`, suma de `daily_stats` y `COUNT(*)` partición por partición en `listens_by_user`. Las tres dan 4 855 809, igual que `scripts/validate_dataset.py`. No hubo líneas omitidas ni duplicadas.

**Lecturas** (una partición cada una):

| Consulta | Tiempo |
| --- | --- |
| Serie diaria de 2026 (`daily_stats`) | 6 ms |
| Top 10 artistas de octubre 2026 | 11 ms |
| Historial mensual de un artista | 16 ms |
| Últimas 5 escuchas de la partición más grande (14 205 filas) | 14 ms |

**Cuidado al interpretar los KPIs:** el incremental refleja la **ingesta** de octubre de 2026. Solo el 26 de octubre tiene 1 359 824 escuchas (28 % del dataset) de 26 020 usuarios, y el 27 de octubre tiene 4 porque el dump se cortó a las 00:01. Por eso el crecimiento diario muestra saltos de +3 364 % y −100 %. Lo mismo pasa con el ranking: BTS concentra el 12,65 % de las escuchas de octubre.

## Para el resto del equipo

**Airflow** (paso 4, "Transformación y carga en Cassandra"). Dentro de Docker, el host es el nombre del servicio (`CASSANDRA_HOSTS=cassandra`):

```python
from databases.cassandra.connection import get_session
from databases.cassandra.loader import load_listens


def load_cassandra():
    session = get_session()
    try:
        return load_listens(session, "/opt/airflow/data/processed/listens_full.jsonl", max_batches=1)
    finally:
        session.cluster.shutdown()
```

`load_listens` devuelve un diccionario con lo que hizo (lotes, filas, omitidas), útil como XCom. Variables de entorno: `CASSANDRA_HOSTS`, `CASSANDRA_PORT`, `CASSANDRA_KEYSPACE`, `CASSANDRA_DC`.

**Dashboard.** [queries.py](queries.py) tiene una función por consulta y todas devuelven listas de dicts (`pd.DataFrame(rows)`):

| Función | Devuelve |
| --- | --- |
| `get_daily_stats(session, year)` | Escuchas, usuarios activos, escuchas por usuario y crecimiento % de cada día |
| `get_top_artists(session, month, limit)` | Ranking del mes con escuchas y % del total |
| `get_artist_history(session, artist_name)` | Escuchas por mes de un artista |
| `get_user_activity(session, user_id)` | Escuchas por día de un usuario |
| `get_load_batches(session)` | Lotes cargados (sirve para el KPI de registros procesados) |

**KPIs que salen de Cassandra** (tabla `daily_stats`, día en UTC):

| KPI | Fórmula |
| --- | --- |
| Escuchas por día | `E(d)` = escuchas con fecha `d` |
| Usuarios activos por día | `U(d)` = `user_id` distintos con escuchas en `d` |
| Escuchas por usuario activo | `E(d) / U(d)` |
| Crecimiento diario | `(E(d) − E(d−1)) / E(d−1) × 100`; vacío si `E(d−1) = 0` |
| Participación del artista líder | `share_pct` del rank 1 en `top_artists_by_month` = escuchas del artista / escuchas del mes × 100 |

## Limitaciones

- Un solo nodo con replication factor 1: sirve para desarrollo, no tolera caídas. En producción sería `NetworkTopologyStrategy` con RF=3.
- Los artistas se identifican por nombre tal como viene en el dataset; homónimos y variantes de escritura cuentan por separado.
- Los agregados se recalculan desde el archivo; una escucha creada a mano con el CRUD no aparece en ellos.
- Los duplicados se descartan dentro de cada lote. Entre lotes, `listens_by_user` no duplica (mismo id), pero los agregados contarían dos veces. En este dataset no hay duplicados: lo comprobamos sobre los 4,86 M registros.

