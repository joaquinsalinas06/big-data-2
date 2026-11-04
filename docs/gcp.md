# Dataset compartido en Google Cloud Storage (opcional)

**Estado actual:** guía preparada; **no existe un bucket creado por este repositorio** y **no se ha ejecutado ningún despliegue ni gasto en GCP**.

## ¿Por qué usar un bucket?

Para que el grupo no descargue el mismo dataset en cada laptop y para que futuras tareas de GCP accedan a una fuente común. Nuestra primera fuente es un archivo de **238 MB comprimido** que, tras extraerse, ocupa aproximadamente **2,6 GB**. Recomandamos guardar el archivo comprimido y su SHA-256 en un bucket privado; extraerlo solo en el entorno de cómputo que lo necesite.

**Importante:** subir algo a Cloud Storage no elimina los costos de almacenamiento, operaciones o transferencia; el proyecto GCP debe estar habilitado y tener permisos/facturación correspondientes. No asumir que es gratuito. Para cargas posteriores, escoger una región cercana a los recursos de procesamiento y revisar [precios](https://cloud.google.com/storage/pricing).

## 1. Crear un bucket privado (solo el responsable de GCP)

En un terminal con [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) y permisos para crear buckets:

```bash
gcloud auth login
gcloud config set project ID_DEL_PROYECTO_GCP

BUCKET="nombre-globalmente-unico-del-grupo"
REGION="us-central1"  # Cambiar por la región de procesamiento elegida

gcloud storage buckets create "gs://$BUCKET" \
  --location="$REGION" \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access \
  --public-access-prevention
```

No ejecutes esto sin sustituir el ID, nombre y región. **Si el grupo ya dispone de un bucket apropiado, reutilizarlo** en lugar de crear otro. No hagas público el bucket.

## 2. Descargar desde GCP y subir al bucket (sin pasar por tu Mac)

Puedes ejecutar el siguiente bloque **en una VM de Compute Engine** o en una sesión de **Cloud Shell** con espacio temporal suficiente. Cloud Shell es temporal: se recomienda subir **solo el archivo comprimido**, nunca extraer allí los 2,6 GB si no has confirmado sus límites.

```bash
BUCKET="nombre-globalmente-unico-del-grupo"
BASE="https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/listenbrainz-dump-2746-20261027-000003-incremental"
FILE="listenbrainz-listens-dump-2746-20261027-000003-incremental.tar.zst"
DEST="gs://$BUCKET/listenbrainz/2746/raw"

mkdir -p /tmp/listenbrainz
curl -fL --retry 3 -C - -o "/tmp/listenbrainz/$FILE" "$BASE/$FILE"
curl -fL --retry 3 -o "/tmp/listenbrainz/$FILE.sha256" "$BASE/$FILE.sha256"

EXPECTED=$(awk 'NR==1 {print $1}' "/tmp/listenbrainz/$FILE.sha256")
ACTUAL=$(shasum -a 256 "/tmp/listenbrainz/$FILE" | awk '{print $1}')
test "$EXPECTED" = "$ACTUAL" || { echo "ERROR: SHA-256 distinto"; exit 1; }

gcloud storage cp "/tmp/listenbrainz/$FILE" "$DEST/$FILE"
gcloud storage cp "/tmp/listenbrainz/$FILE.sha256" "$DEST/$FILE.sha256"
gcloud storage ls "$DEST/"
```

Esto hace una **única transferencia desde el servidor público hacia una máquina de GCP**, y después guarda una copia en Cloud Storage. No se descargan datos a tu computadora.

> Otra alternativa de Google Cloud es **Storage Transfer Service** desde una lista de URLs públicas; exige requisitos como acceso HTTP público, peticiones Range y Content-Length. No lo configuramos todavía porque para un único archivo de 238 MB la VM/Cloud Shell es más sencilla.

## 3. Acceso de los compañeros: IAM, no enlaces públicos

El responsable del bucket puede dar permisos **de solo lectura** a cada compañero (modificar el correo):

```bash
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="user:COMPAÑERO@EJEMPLO.COM" \
  --role="roles/storage.objectViewer"
```

Evita otorgar `roles/storage.admin` a todo el grupo. Si el bucket es compartido con otros proyectos, revisa antes el alcance de ese permiso: se otorga lectura a los objetos del bucket, no solo al directorio del dataset.

## 4. Consumir el archivo dentro de GCP

En una VM de procesamiento autorizada, luego de clonar el repositorio:

```bash
BUCKET="nombre-globalmente-unico-del-grupo"
SRC="gs://$BUCKET/listenbrainz/2746/raw"
FILE="listenbrainz-listens-dump-2746-20261027-000003-incremental.tar.zst"

mkdir -p data/raw data/processed
gcloud storage cp "$SRC/$FILE" data/raw/listenbrainz-20261027.tar.zst
gcloud storage cp "$SRC/$FILE.sha256" data/raw/listenbrainz-20261027.sha256

EXPECTED=$(awk 'NR==1 {print $1}' data/raw/listenbrainz-20261027.sha256)
ACTUAL=$(shasum -a 256 data/raw/listenbrainz-20261027.tar.zst | awk '{print $1}')
test "$EXPECTED" = "$ACTUAL" || { echo "ERROR: SHA-256 distinto"; exit 1; }

set -o pipefail
zstd -dc data/raw/listenbrainz-20261027.tar.zst |
  tar -xOf - "listenbrainz-listens-dump-2746-20261027-000003-incremental/listens/2026/10.listens" > data/processed/listens_full.jsonl.part &&
  mv data/processed/listens_full.jsonl.part data/processed/listens_full.jsonl

python3 scripts/validate_dataset.py
```

La VM necesita `zstd`, `tar`, `shasum` y Python 3. Los datos se descargan **del bucket a la VM de GCP**, no a cada laptop.

## 5. Convención sugerida del bucket

```text
gs://NOMBRE-DEL-BUCKET/
└── listenbrainz/
    └── 2746/
        └── raw/
            ├── listenbrainz-listens-dump-2746-20261027-000003-incremental.tar.zst
            └── listenbrainz-listens-dump-2746-20261027-000003-incremental.tar.zst.sha256
```

No subir el JSONL de 2,6 GB por defecto: puede regenerarse desde el comprimido. Antes de ejecutar tareas automáticas, acordar con el equipo si se necesita una copia procesada permanente.

## Documentación oficial

- [Crear buckets](https://cloud.google.com/storage/docs/creating-buckets)
- [Subir objetos](https://cloud.google.com/storage/docs/uploading-objects)
- [Permisos IAM para buckets](https://cloud.google.com/storage/docs/access-control/using-iam-permissions)
- [Storage Transfer Service desde URLs](https://cloud.google.com/storage-transfer/docs/create-url-list)
- [Precios de Cloud Storage](https://cloud.google.com/storage/pricing)
