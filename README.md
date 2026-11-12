# Big Data 2 — ListenBrainz (Music DNA)

**Proyecto Grupal II · Big Data** · Fecha de entrega: **17 de noviembre de 2026**

Este proyecto implementa una **arquitectura multimodelo** para almacenar, procesar y analizar hábitos de escucha musical a partir de datos públicos de [ListenBrainz](https://listenbrainz.org/data/). 

El sistema utiliza tres tecnologías de almacenamiento complementarias:
1. **MongoDB (`mongodb/`):** Almacenamiento de documentos originales semiestructurados (JSON) y API REST.
2. **Apache Cassandra (`cassandra_db/`):** Almacenamiento columnar optimizado para series temporales y consultas masivas de históricos.
3. **Neo4j (`neo4j/`):** Modelado de grafo para relaciones de usuarios, escuchas, canciones y artistas, con recomendaciones explicables y comunidades.

---

## 🚀 Inicio Rápido con Docker

El repositorio cuenta con un `docker-compose.yml` unificado en la raíz para levantar todas las bases de datos de forma local:

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

Puertos asignados:
- **MongoDB:** `27017`
- **Cassandra:** `9042`
- **Neo4j:** `7474` (HTTP / Browser), `7687` (Bolt)

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

## 🛠️ Demostración de CRUD por Base de Datos

Cada módulo cuenta con scripts estandarizados para demostrar las 4 operaciones básicas (Create, Read, Update, Delete) requeridas para la exposición:

### 1. MongoDB
```bash
# CRUD directo interactivo
python -m mongodb.crud --pause

# Consultas analíticas y agregaciones
python -m mongodb.queries

# (Opcional) Servidor API FastAPI
python -m mongodb.api_server
```

### 2. Apache Cassandra
```bash
# Inicializar keyspace y tablas
python -m cassandra_db.init_schema

# CRUD interactivo
python -m cassandra_db.crud --pause

# Consultas analíticas
python -m cassandra_db.queries
```

### 3. Neo4j
```bash
# Carga inicial y análisis
python neo4j/load.py
python neo4j/analyze.py

# CRUD y consultas de grafo
python neo4j/main.py
```

---

## 📂 Organización del Repositorio

```text
big-data-2/
├── docker-compose.yml          # Stack unificado (MongoDB + Cassandra + Neo4j)
├── requirements.txt            # Dependencias unificadas de todo el proyecto
├── .env.example                # Plantilla de variables de entorno
│
├── mongodb/                    # Módulo MongoDB (Documental & JSON)
│   ├── connection.py           # Conexión centralizada PyMongo
│   ├── crud.py                 # Demo CRUD estándar en consola
│   ├── load_listens.py         # Carga masiva por lotes
│   ├── queries.py              # Agregaciones analíticas
│   ├── docker-compose.yml      # Compose aislado de MongoDB
│   ├── app/                    # API REST con FastAPI (rutas, modelos, servicios)
│   ├── tests/                  # Pruebas unitarias
│   └── README.md
│
├── cassandra_db/               # Módulo Cassandra (Series Temporales)
│   ├── schema.cql              # Esquema de tablas CQL
│   ├── init_schema.py          # Script de creación de keyspace/tablas
│   ├── connection.py           # Conexión con cassandra-driver
│   ├── crud.py                 # Demo CRUD estándar en consola
│   ├── load_listens.py         # Carga masiva optimizada
│   ├── queries.py              # Consultas de series temporales
│   └── README.md
│
├── neo4j/                      # Módulo Neo4j (Grafo de Relaciones)
│   ├── compose.yaml            # Compose aislado de Neo4j
│   ├── database.py             # Conexión con driver Neo4j
│   ├── load.py                 # Carga de nodos y relaciones
│   ├── analyze.py              # Algoritmos de grafo y comunidades
│   ├── main.py                 # Consultas y CRUD
│   ├── graph/                  # Implementación de queries y CRUD en Cypher
│   └── README.md
│
├── docs/                       # Guías, PDFs oficiales y documentación
│   ├── Instrucciones Proyecto Grupal II.pdf
│   ├── dataset.md
│   ├── gcp.md
│   ├── neo4j-results.md
│   └── mongodb_crud_guide.md
│
└── scripts/                    # Scripts de utilidad común (descarga, validación)
```

---

## 🔜 Próximas Etapas

- **Automatización (Apache Airflow):** DAG de 6 tareas (Extracción, Validación, Carga MongoDB, Carga Cassandra, Carga Neo4j, Cálculo de KPIs).
- **Dashboard Analítico (Streamlit):** Visualización interactiva conectando los 3 almacenes y los 5 KPIs.
- **Informe Técnico & Video Demostrativo:** Documentación en PDF y grabación de 20-25 minutos.
