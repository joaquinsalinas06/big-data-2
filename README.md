# Big Data 2 — Music DNA

**Proyecto Grupal II · Big Data** · Entrega: **17 de noviembre de 2026**

**Music DNA** es una propuesta académica para explorar hábitos de escucha y comunidades musicales a partir de datos públicos de [ListenBrainz](https://listenbrainz.org/data/). Esta primera versión del repositorio contiene **solo el dataset, instrucciones de descarga, inspección y validación**. El resto del proyecto será desarrollado posteriormente por el equipo.

## Dataset de referencia

- **Fuente:** ListenBrainz / MetaBrainz (datos públicos de escuchas).
- **Corte utilizado:** incremental del **27 de octubre de 2026**, secuencia **2746**.
- **Datos observados en la validación local inicial:** **4 855 809** registros JSON Lines; **238 MB comprimido** y **aprox. 2,6 GB extraído**.
- **Campos principales observados:** `user_id`, `user_name`, `timestamp`, `track_metadata` (con `track_name` y `artist_name`), `recording_msid`; algunos metadatos son opcionales.
- **Importante:** esto es **un incremental** (ingestas recientes), *no* el histórico completo ni una muestra representativa de escuchas realizadas en octubre: las fechas de escucha observadas van de 2005 a 2026.

## Inicio rápido en macOS

Necesitas Python 3, `curl`, `tar`, `shasum` y `zstd`. Instala este último si no lo tienes:

```bash
brew install zstd
git clone https://github.com/joaquinsalinas06/big-data-2.git
cd big-data-2
bash scripts/download_dataset.sh --extract
python3 scripts/validate_dataset.py
```

El script descarga el archivo oficial, comprueba su **SHA-256**, extrae el JSONL y lo deja en `data/processed/listens_full.jsonl`. La validación revisa los **4 855 809** registros esperados sin cargar todo el archivo en memoria.

**Si ya descargaste el dataset:** puedes copiarlo a `data/processed/` y ejecutar únicamente el validador. Si lo tienes en `~/dev/music-dna/` y prefieres **no duplicar 2,6 GB**, crea un enlace simbólico:

```bash
mkdir -p data/processed
ln -s "$HOME/dev/music-dna/data/processed/listens_full.jsonl" data/processed/listens_full.jsonl
python3 scripts/validate_dataset.py
```

## Documentación del equipo

| Documento | Para qué sirve |
| --- | --- |
| [Dataset y esquema](docs/dataset.md) | Origen, contenido, formato, tamaño, campos y limitaciones |
| [Descarga y almacenamiento en GCP](docs/gcp.md) | Cómo guardar una sola copia comprimida en un bucket privado, sin descargarla a las laptops |
| [Script de descarga](scripts/download_dataset.sh) | Descarga, verificación SHA-256 y extracción local |
| [Script de validación](scripts/validate_dataset.py) | Conteo y comprobación de registros JSON |

## Organización inicial

```text
big-data-2/
├── README.md
├── .gitignore
├── docs/
│   ├── dataset.md
│   └── gcp.md
├── scripts/
│   ├── download_dataset.sh
│   └── validate_dataset.py
└── data/                 # Se crea al descargar; NO se sube a Git
    ├── raw/
    └── processed/
```

Los datos brutos no se versionan: cada integrante puede recuperarlos desde la fuente o, cuando el equipo habilite GCP, desde un bucket compartido y privado. **Todavía no se ha creado ningún bucket ni se han desplegado recursos en Google Cloud.**

### Fuentes

- [Descargas de ListenBrainz](https://listenbrainz.org/data/)
- [Documentación de dumps](https://listenbrainz.readthedocs.io/en/latest/users/listenbrainz-dumps.html)
- [Directorio de incrementales](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/)
