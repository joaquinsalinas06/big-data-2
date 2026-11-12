# ListenBrainz — Neo4j (Grafo de Entidades y Relaciones)

Módulo de Neo4j para el modelado de grafos, relaciones de escuchas, afinidades entre artistas y detección de comunidades.

---

## 🚀 Inicio Rápido

### 1. Iniciar Contenedor Neo4j

```bash
docker compose -f databases/neo4j/docker-compose.yml up -d
```

Abre en tu navegador [Neo4j Browser](http://localhost:7474) (usuario: `neo4j`, clave definida en `.env`).

---

## 🛠️ Comandos Principales

### 2. Carga y Análisis del Grafo

```bash
# 1. Preparar y cargar el grafo en Neo4j
python -m databases.neo4j.loader

# 2. Calcular afinidades, comunidades y KPIs de red
python -m databases.neo4j.analyze
```

### 3. Operaciones CRUD (Demostración en Video)

```bash
# CRUD interactivo paso a paso
python -m databases.neo4j.crud --pause
```

El script ejecuta las 4 operaciones básicas sobre el grafo:
1. **CREATE (Nodos):** Crea nodo Usuario y nodo Canción con etiquetas administradas.
2. **CREATE (Relación):** Establece la relación `[:ESCUCHO]` entre usuario y canción.
3. **UPDATE:** Modifica las propiedades de la relación (e.g. contador de reproducciones).
4. **DELETE:** Elimina la relación y realiza el borrado seguro (`DETACH DELETE`) de los nodos de prueba.

### 4. Consultas Analíticas

```bash
python -m databases.neo4j.queries
```

Muestra en consola:
- Artistas más escuchados y canciones por artista.
- Filtros por usuario y búsqueda de artistas.
- Recomendaciones explicables de artistas y canciones basadas en vecinos del grafo.
- Detección de comunidades musicales (algoritmo de Louvain) y artistas puente.
- Indicadores de red y diversidad de gustos por usuario.

---

## 📂 Organización Interna

```text
databases/neo4j/
├── docker-compose.yml      # Servicio local de Neo4j
├── connection.py           # Conexión centralizada con el driver oficial de Neo4j
├── loader.py               # Preparación y carga del dataset a Neo4j
├── analyze.py              # Algoritmos de grafo (NetworkX), afinidades y comunidades
├── crud.py                 # Runner interactivo para demostración de CRUD en Cypher
├── queries.py              # Runner de consultas analíticas del grafo
├── graph/
│   ├── queries.py          # Definición de funciones de consulta Cypher
│   └── crud.py             # Funciones primitivas de CRUD en Cypher
├── model/                  # Esquema y diagrama editable de Arrows.app
│   ├── schema.py           # Restricciones de unicidad e índices
│   └── graph.arrows.json   # Modelo visual
├── tests/                  # Pruebas unitarias de algoritmos y grafo
└── README.md
```

---

## 🧪 Pruebas Automatizadas

```bash
pytest databases/neo4j/tests
```
