# Big Data 2 — Music DNA

**Proyecto Grupal II · Big Data** · Entrega: **17 de noviembre de 2026**

**Music DNA** es una propuesta académica para explorar hábitos de escucha y comunidades musicales a partir de datos públicos de [ListenBrainz](https://listenbrainz.org/data/). Por ahora el repositorio contiene **el dataset, instrucciones de descarga y validación**, sin desarrollar todavía las bases de datos ni el dashboard.

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

**Si ya descargaste el dataset en tu Mac:** evita duplicar los 2,6 GB. Desde la raíz del repositorio:

```bash
mkdir -p data/processed
ln -s "$HOME/dev/music-dna/data/processed/listens_full.jsonl" data/processed/listens_full.jsonl
python3 scripts/validate_dataset.py
```

## Documentación del equipo

| Documento | Para qué sirve |
| --- | --- |
| [Dataset y esquema](docs/dataset.md) | Origen, estructura JSON, tipos de descarga y limitaciones |
| [Descarga y almacenamiento en GCP](docs/gcp.md) | Alternativa para guardar el comprimido en un bucket privado compartido |
| [Descarga en Windows](scripts/download_dataset.ps1) | PowerShell: descarga, SHA-256 y extracción |
| [Descarga en Linux/macOS](scripts/download_dataset.sh) | Bash: descarga, SHA-256 y extracción |
| [Validador común](scripts/validate_dataset.py) | Comprobación de los registros JSON con Python |
| [Cassandra](cassandra_db/README.md) | Modelo de tablas, carga por lotes, CRUD y KPIs diarios |

## Organización inicial

```text
big-data-2/
├── README.md
├── .gitignore
├── docs/
│   ├── dataset.md
│   └── gcp.md
├── scripts/
│   ├── download_dataset.ps1
│   ├── download_dataset.sh
│   └── validate_dataset.py
└── data/                  # Se crea al descargar; NO se sube a Git
    ├── raw/
    └── processed/
```

Los datos brutos no se versionan: cada integrante puede recuperarlos desde ListenBrainz o, cuando el equipo lo habilite, desde **Google Cloud Storage**. **Todavía no se ha creado ningún bucket ni desplegado recursos en GCP.** Ver [guía de GCP](docs/gcp.md).

### Fuentes

- [Descargas oficiales de ListenBrainz](https://listenbrainz.org/data/)
- [Documentación del dataset](https://listenbrainz.readthedocs.io/en/latest/users/listenbrainz-dumps.html)
- [Directorio de incrementales](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/)
- [Python 3.14 — soporte Zstandard en tarfile](https://docs.python.org/3.14/library/tarfile.html)
