# Big Data 2 — ListenBrainz

**Proyecto Grupal II · Big Data** · Entrega: **17 de noviembre de 2026**

Este proyecto explora hábitos de escucha y comunidades musicales a partir de datos públicos de [ListenBrainz](https://listenbrainz.org/data/). El repositorio incluye descarga y validación del dataset, **Neo4j local, recomendaciones explicables, comunidades musicales e indicadores**. MongoDB, Cassandra, Airflow, dashboard y GCP son las siguientes etapas.

## Dataset de referencia

- **Fuente:** ListenBrainz / MetaBrainz (registros públicos de escuchas).
- **Archivo de referencia:** incremental del **27 de octubre de 2026**, secuencia **2746**.
- **Datos observados en la validación local:** **4 855 809** registros JSON Lines; **238 MB comprimido** y **aprox. 2,6 GB extraído**.
- **Campos principales:** `user_id`, `user_name`, `timestamp` y `track_metadata` (incluye `track_name` y `artist_name`). `recording_msid` y otros metadatos pueden ser opcionales.
- **Importante:** es un **incremental**, no el histórico completo de ListenBrainz. Contiene escuchas fechadas entre 2005 y 2026, incorporadas al sistema en este lote.

## Instalación y descarga por sistema operativo

En todos los sistemas se descarga el **mismo archivo oficial**, se comprueba el **SHA-256** y se obtiene `data/processed/listens_full.jsonl`. Reserva al menos **4 GB de espacio libre**, además de Git y Python; el espacio exacto necesario puede variar.

### 1. Windows — PowerShell (sin WSL)

**Recomendado para los compañeros que usan Windows 10/11.** Abre **PowerShell** o Windows Terminal (no CMD). Instala [Git](https://git-scm.com/install/windows) y **Python 3.14** con WinGet:

```powershell
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.14 -e --source winget
```

Cierra y vuelve a abrir PowerShell para que reconozca los programas. Comprueba:

```powershell
git --version
python --version
```

**Descargar y validar** desde PowerShell:

```powershell
git clone https://github.com/joaquinsalinas06/big-data-2.git
cd big-data-2

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\download_dataset.ps1 -Extract
python .\scripts\validate_dataset.py
```

- `download_dataset.ps1` usa `curl.exe` y `Get-FileHash` para verificar la descarga, y Python **3.14+** para extraer `.tar.zst` sin instalar `zstd` ni WSL.
- Si Windows muestra «`python` no se reconoce», reinicia la terminal y revisa la instalación/alias de Python.
- El script comprueba SHA-256 **antes** de extraer y **no sobrescribe** un JSONL ya existente.
- **Estado de pruebas:** las instrucciones están basadas en las herramientas oficiales, pero aún **no se han probado en una computadora Windows** del grupo.

### 2. Linux — Ubuntu / Debian

Instala las dependencias en la terminal. En otras distribuciones utiliza el gestor de paquetes correspondiente:

```bash
sudo apt update
sudo apt install -y git curl zstd python3 tar coreutils

git clone https://github.com/joaquinsalinas06/big-data-2.git
cd big-data-2

bash scripts/download_dataset.sh --extract
python3 scripts/validate_dataset.py
```

El script Bash usa `sha256sum` de Linux (o `shasum` como alternativa), lee el comprimido por streaming y guarda el JSONL sin cargar todo el dataset en RAM. **No se ha probado todavía en una máquina Linux del grupo.**

### 3. macOS — Terminal

Instala [Homebrew](https://brew.sh/) si aún no lo tienes. Luego:

```bash
brew install zstd

git clone https://github.com/joaquinsalinas06/big-data-2.git
cd big-data-2

bash scripts/download_dataset.sh --extract
python3 scripts/validate_dataset.py
```

Se requiere Git y Python 3. Si falta alguno, puedes instalarlo con Homebrew: `brew install git python`. **La descarga y extracción de este dump ya se verificaron en macOS**; el script versionado automatiza los mismos pasos.

### Resultado esperado

Al finalizar, el validador debe mostrar aproximadamente:

```text
=== VALIDACIÓN LISTENBRAINZ ===
Registros leídos: 4,855,809
Registros válidos: 4,855,809
Registros inválidos: 0
OK: dataset validado
```

El archivo aparecerá en `data/processed/listens_full.jsonl`. Si falla el checksum, **no utilices el archivo**: vuelve a descargarlo. Si falta espacio, libera al menos unos gigabytes antes de extraer.

## Neo4j: empezar aquí

Para leer el código y exponer siguiendo el estilo de la semana 12, empieza por **[main.py](neo4j/main.py)** y las funciones de `neo4j/graph/`. La [guía de Neo4j](neo4j/README.md) explica la estructura.

Sigue la [guía local de Neo4j](neo4j/README.md). Incluye instalación para macOS/Linux y Windows, carga completa, consultas, KPIs, comunidades y operaciones CRUD.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Cambia NEO4J_PASSWORD en .env antes de arrancar.
docker compose --env-file .env -f neo4j/compose.yaml up -d --wait
python neo4j/load.py
python neo4j/analyze.py
python neo4j/main.py
```

Abre [Neo4j Browser](http://localhost:7474). Las credenciales se configuran en tu `.env` local. Los datos persisten en un volumen Docker.

**En la Mac donde comenzó el proyecto**, los archivos descargados se trasladaron a `data/raw/` y `data/processed/` de este repositorio. Los compañeros generan las mismas rutas mediante los scripts de descarga anteriores; los datos no se incluyen en Git.

## Documentación del equipo

| Documento | Para qué sirve |
| --- | --- |
| [Código Python para la exposición](neo4j/main.py) | Consultas y CRUD organizados como el manual de la semana 12 |
| [Neo4j local y experiencias](neo4j/README.md) | Inicio, modelo, recomendaciones, comunidades, KPIs y pruebas |
| [Dataset y esquema](docs/dataset.md) | Origen, estructura JSON, tipos de descarga y limitaciones |
| [Descarga y almacenamiento en GCP](docs/gcp.md) | Alternativa para guardar el comprimido en un bucket privado compartido |
| [Descarga en Windows](scripts/download_dataset.ps1) | PowerShell: descarga, SHA-256 y extracción |
| [Descarga en Linux/macOS](scripts/download_dataset.sh) | Bash: descarga, SHA-256 y extracción |
| [Validador común](scripts/validate_dataset.py) | Comprobación de los registros JSON con Python |
| [Cassandra](cassandra_db/README.md) | Modelo de tablas, carga por lotes, CRUD y KPIs diarios |

## Organización

```text
big-data-2/
├── README.md
├── requirements.txt          # Driver, NetworkX y configuración local
├── .env.example              # Copiar a .env y cambiar contraseña
├── docs/                     # Dataset, Neo4j y futura etapa GCP
├── scripts/                  # Descarga multiplataforma y validación
├── neo4j/
│   ├── compose.yaml           # Neo4j Community con persistencia
│   ├── load.py                # Preparación y carga
│   ├── analyze.py             # Análisis musical y KPIs
│   ├── main.py                # Consultas
│   ├── database.py            # Conexión y rutas
│   ├── graph/                 # Consultas y CRUD
│   ├── model/                 # Esquema, diagrama y JSON de Arrows.app
│   ├── tests/
│   └── README.md
└── data/                     # Local, fuera de Git
    ├── raw/
    ├── processed/
    └── neo4j/                # Agregaciones y resultados regenerables
```

Los datos brutos no se versionan: cada integrante puede recuperarlos desde ListenBrainz o, cuando el equipo lo habilite, desde **Google Cloud Storage**. **Todavía no se ha creado ningún bucket ni desplegado recursos en GCP.** Ver [guía de GCP](docs/gcp.md).

### Fuentes

- [Descargas oficiales de ListenBrainz](https://listenbrainz.org/data/)
- [Documentación del dataset](https://listenbrainz.readthedocs.io/en/latest/users/listenbrainz-dumps.html)
- [Directorio de incrementales](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/)
- [Python 3.14 — soporte Zstandard en tarfile](https://docs.python.org/3.14/library/tarfile.html)
