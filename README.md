# Big Data 2 — ListenBrainz (Music DNA)

**Proyecto Grupal II · Big Data** · Fecha de entrega: **17 de noviembre de 2026**

Este proyecto implementa una **arquitectura multimodelo limpia y desacoplada** para almacenar, procesar y analizar hábitos de escucha musical a partir de datos públicos de [ListenBrainz](https://listenbrainz.org/data/).

Toda la capa de persistencia se encuentra centralizada bajo el directorio [`databases/`](databases/), organizada en 3 motores complementarios:
1. **MongoDB ([`databases/mongodb/`](databases/mongodb)):** Almacenamiento de documentos originales semiestructurados (JSON) y API REST.
2. **Apache Cassandra ([`databases/cassandra/`](databases/cassandra)):** Almacenamiento columnar optimizado para series temporales y consultas masivas de históricos.
3. **Neo4j ([`databases/neo4j/`](databases/neo4j)):** Modelado de grafo para relaciones de usuarios, canciones y artistas, con recomendaciones y comunidades.

---

## 🚀 Inicio Rápido con Docker

El repositorio cuenta con un [`docker-compose.yml`](docker-compose.yml) unificado en la raíz para levantar todas las bases de datos de forma local:

```bash
# 1. Copiar configuración de variables de entorno
cp .env.example .env

# 2. Levantar los tres motores de bases de datos
docker compose up -d

# (Opcional) Levantar solo una base de datos específica:
# docker compose up -d mongodb
# docker compose up -d cassandra
# docker compose up -d neo4j
```

`docker compose up -d` también construye y levanta Airflow (postgres, airflow-init, webserver y scheduler). La primera vez conviene correr antes `docker compose build`. Docker necesita unos 10 GB de memoria para todo el stack.

Puertos asignados:
- **MongoDB:** `27017`
- **Cassandra:** `9042`
- **Neo4j:** `7474` (HTTP / Browser), `7687` (Bolt)
- **Airflow:** `8080` (http://localhost:8080, usuario `admin`, clave `admin`)

El DAG `music_dna_pipeline` aparece pausado; se activa desde la interfaz o se corre completo con `docker compose exec airflow-scheduler airflow dags test music_dna_pipeline`. Detalle en [docs/airflow.md](docs/airflow.md).

---

## 📦 Instalación de Dependencias

Se recomienda usar un entorno virtual con Python 3.11+:

```bash
python -m venv .venv

# Activar en Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Activar en Linux/macOS:
source .venv/bin/activate

# Instalar dependencias unificadas del proyecto:
pip install -r requirements.txt
```

---

## 🎵 Dataset de Referencia

- **Fuente:** [ListenBrainz / MetaBrainz](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/)
- **Corte:** Incremental 2026-10-27 (dump sequence 2746).
- **Volumen:** ~4.85 millones de registros JSON Lines (~238 MB comprimido `.tar.zst`, ~2.6 GB extraído).

### Descarga y Validación

* **Windows (PowerShell):**
  ```powershell
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\download_dataset.ps1 -Extract
  python .\scripts\validate_dataset.py
  ```
* **Linux / macOS (Bash):**
  ```bash
  bash scripts/download_dataset.sh --extract
  python3 scripts/validate_dataset.py
  ```

El dataset extraído queda en `data/processed/listens_full.jsonl` (ignorado por Git).

---

## 🛠️ Interfaz Estandarizada por Base de Datos

Cada base de datos cuenta con una **interfaz simétrica y estandarizada** para todas sus operaciones:

### 1. Demostración de CRUD (Para Video y Exposición)
```bash
# MongoDB
python -m databases.mongodb.crud --pause

# Apache Cassandra
python -m databases.cassandra.crud --pause

# Neo4j
python -m databases.neo4j.crud --pause
```

### 2. Carga Masiva de Datos (Loaders para Airflow o CLI)
```bash
# Carga a MongoDB
python -m databases.mongodb.loader --limit 50000

# Carga a Cassandra
python -m databases.cassandra.loader --limit 50000

# Carga a Neo4j
python -m databases.neo4j.loader
```

### 3. Consultas Analíticas y Agregaciones
```bash
# Consultas en MongoDB
python -m databases.mongodb.queries

# Consultas en Cassandra
python -m databases.cassandra.queries

# Consultas en Neo4j (grafo, comunidades, KPIs)
python -m databases.neo4j.queries
```

---

## 📂 Organización del Repositorio

```text
big-data-2/
├── docker-compose.yml              # Stack unificado de servicios Docker
├── requirements.txt                # Dependencias únicas y versionadas
├── .env.example                    # Plantilla de variables de entorno
│
├── databases/                      # 📁 Capa de persistencia multimodelo
│   │
│   ├── mongodb/                    # Motor Documental (JSON)
│   │   ├── connection.py           # Conexión centralizada PyMongo
│   │   ├── crud.py                 # Runner interactivo de CRUD
│   │   ├── loader.py               # Carga masiva por lotes
│   │   ├── queries.py              # Agregaciones analíticas
│   │   ├── docker-compose.yml      # Compose individual
│   │   ├── app/                    # API REST con FastAPI (rutas, modelos, servicios)
│   │   ├── tools/                  # Scripts de prueba y verificación
│   │   ├── tests/                  # Pruebas unitarias
│   │   └── README.md
│   │
│   ├── cassandra/                  # Motor de Series Temporales (Columnar)
│   │   ├── connection.py           # Conexión cassandra-driver
│   │   ├── crud.py                 # Runner interactivo de CRUD
│   │   ├── loader.py               # Carga masiva optimizada
│   │   ├── queries.py              # Consultas de series de tiempo
│   │   ├── schema.cql              # DDL de tablas CQL
│   │   ├── init_schema.py          # Script inicializador de keyspace
│   │   ├── docker-compose.yml      # Compose individual
│   │   └── README.md
│   │
│   └── neo4j/                      # Motor de Grafo (Relaciones)
│       ├── connection.py           # Conexión con driver Neo4j
│       ├── crud.py                 # Runner interactivo de CRUD en Cypher
│       ├── loader.py               # Carga de nodos y relaciones
│       ├── queries.py              # Consultas analíticas y algoritmos
│       ├── analyze.py              # Detección de comunidades (NetworkX)
│       ├── model/                  # Esquema y restricciones
│       ├── docker-compose.yml      # Compose individual
│       ├── tests/                  # Pruebas de grafo
│       └── README.md
│
├── airflow/                        # 📁 Orquestación (Ana María)
│   └── dags/
│       └── music_dna_dag.py
│
├── dashboard/                      # 📁 Dashboard Analítico (Streamlit)
│   └── app.py
│
├── docs/                           # Documentación técnica y consignas oficiales
└── scripts/                        # Descarga y verificación del dataset oficial
```

---

## 📚 Documentación Técnica

| Documento | Descripción |
| :--- | :--- |
| [Dataset y Esquema](docs/dataset.md) | Origen, campos JSON y validación del dump oficial |
| [MongoDB](docs/mongodb.md) | Modelo documental, índices y guía CRUD |
| [Apache Cassandra](docs/cassandra.md) | Modelo de series temporales, particionamiento y consultas CQL |
| [Neo4j](docs/neo4j.md) | Grafo de relaciones, comunidades e indicadores |
| [Airflow](docs/airflow.md) | DAG del pipeline, carga incremental y fórmulas de los KPIs |
| [Almacenamiento en GCP](docs/gcp.md) | Guía de configuración para Google Cloud Storage |
| [Rúbrica Oficial](docs/Instrucciones%20Proyecto%20Grupal%20II.pdf) | Requisitos y entregables del curso |

---

## 🔜 Próximas Etapas

- [x] **Automatización (Apache Airflow):** DAG de 6 tareas (Extracción, Validación, Carga MongoDB, Carga Cassandra, Carga Neo4j, Cálculo de KPIs). Ver [docs/airflow.md](docs/airflow.md).
- **Dashboard Analítico (Streamlit):** Visualización interactiva conectando los 3 almacenes y los 5 KPIs.
- **Informe Técnico & Video Demostrativo:** Documentación en PDF y grabación de 20-25 minutos.
