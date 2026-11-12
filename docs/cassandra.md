# Apache Cassandra — Modelo de Series Temporales y Operaciones CRUD

Guía técnica del almacenamiento de series temporales y consultas masivas de históricos en **Apache Cassandra** (`music_dna.listens_by_user`).

---

## 1. Modelo de Datos CQL y Estrategia de Particionamiento

Cassandra está optimizada para escrituras de alto rendimiento y lecturas secuenciales sobre series de tiempo. Para evitar particiones infinitamente grandes ("wide partitions"), se utiliza una **clave de partición compuesta**:

```sql
CREATE KEYSPACE IF NOT EXISTS music_dna
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS music_dna.listens_by_user (
    user_id        bigint,
    month          text,          -- 'YYYY-MM' (agrupador de partición)
    listened_at    timestamp,     -- clustering key descendente
    listen_id      text,          -- tie-breaker determinista
    artist_name    text,
    track_name     text,
    release_name   text,
    recording_msid text,
    PRIMARY KEY ((user_id, month), listened_at, listen_id)
) WITH CLUSTERING ORDER BY (listened_at DESC, listen_id ASC);
```

### Justificación de Claves:
* **Partition Key `(user_id, month)`:** Cada nodo en el cluster aloja los datos de un usuario en un mes concreto. Esto permite consultar el historial mensual de un usuario en un único salto de red (*single partition query*).
* **Clustering Key `listened_at DESC`:** Los datos se ordenan físicamente en disco del evento más reciente al más antiguo.
* **Clustering Key `listen_id ASC`:** Hash determinista SHA-1 que actúa como desempatador para reproducciones simultáneas en el mismo segundo.

---

## 2. Operaciones CRUD en Python (Directas)

Para la sustentación y video demostrativo:

```bash
python -m databases.cassandra.crud --pause
```

Operaciones implementadas en CQL:
* **CREATE (`insert_listen`):** Inserción mediante `INSERT INTO listens_by_user`.
* **READ (`get_listen` / `get_user_listens`):** Consulta por clave primaria completa o consulta de rango mensual de un usuario.
* **UPDATE (`update_listen`):** Modificación de columnas no-clave (`track_name`, `release_name`) mediante `UPDATE ... WHERE`.
* **DELETE (`delete_listen`):** Eliminación controlada por clave primaria.

---

## 3. Carga Masiva y Rendimiento

El cargador optimizado utiliza `execute_concurrent_with_args` sobre conexiones asíncronas:

```bash
# Cargar 50,000 registros (mínimo de rúbrica)
python -m databases.cassandra.loader --file data/processed/listens_full.jsonl --batch-size 1000
```

---

## 4. Consultas Analíticas (KPIs)

```bash
python -m databases.cassandra.queries
```

Ejecuta métricas temporales como volumen de escuchas por mes, picos de actividad horaria y usuarios más activos en una ventana de tiempo.
