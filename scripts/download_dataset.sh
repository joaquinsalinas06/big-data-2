#!/usr/bin/env bash
# Descarga verificable del incremental ListenBrainz 2746 (2026-10-27).
# Uso: bash scripts/download_dataset.sh [--extract]
set -euo pipefail

if [[ "${1:-}" != "" && "${1:-}" != "--extract" ]]; then
  echo "Uso: bash scripts/download_dataset.sh [--extract]" >&2
  exit 2
fi

for cmd in curl awk zstd tar; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Falta $cmd. Instala las dependencias del README (Linux/macOS)." >&2
    exit 1
  fi
done

if command -v sha256sum >/dev/null 2>&1; then
  SHA256_COMMAND=(sha256sum)
elif command -v shasum >/dev/null 2>&1; then
  SHA256_COMMAND=(shasum -a 256)
else
  echo "Falta sha256sum (Linux) o shasum (macOS)." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/data/raw"
PROCESSED="$ROOT/data/processed"
mkdir -p "$RAW" "$PROCESSED"

NAME="listenbrainz-listens-dump-2746-20261027-000003-incremental"
BASE="https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/listenbrainz-dump-2746-20261027-000003-incremental"
URL="$BASE/$NAME.tar.zst"
ARCHIVE="$RAW/listenbrainz-20261027.tar.zst"
CHECKSUM="$RAW/listenbrainz-20261027.sha256"
OUTPUT="$PROCESSED/listens_full.jsonl"
MEMBER="$NAME/listens/2026/10.listens"

echo "Descargando SHA-256 oficial..."
if curl -fL --retry 3 -o "$CHECKSUM.part" "$URL.sha256"; then
  mv "$CHECKSUM.part" "$CHECKSUM"
elif [[ -s "$CHECKSUM" ]]; then
  rm -f "$CHECKSUM.part"
  echo "El SHA-256 ya no está publicado; se usa la copia local $CHECKSUM."
else
  rm -f "$CHECKSUM.part"
  echo "No se pudo descargar el SHA-256 y no hay copia local en $CHECKSUM." >&2
  exit 1
fi
EXPECTED="$(awk 'NR==1 {print $1}' "$CHECKSUM")"
if [[ ! "$EXPECTED" =~ ^[[:xdigit:]]{64}$ ]]; then
  echo "Archivo de checksum inválido." >&2
  exit 1
fi

if [[ -f "$ARCHIVE" ]]; then
  ACTUAL="$("${SHA256_COMMAND[@]}" "$ARCHIVE" | awk '{print $1}')"
else
  ACTUAL=""
fi

if [[ "$ACTUAL" == "$EXPECTED" ]]; then
  echo "Archivo comprimido existente: SHA-256 correcto."
else
  echo "Descargando archivo oficial (~238 MB)..."
  curl -fL --retry 3 -C - -o "$ARCHIVE" "$URL"
  ACTUAL="$("${SHA256_COMMAND[@]}" "$ARCHIVE" | awk '{print $1}')"
  if [[ "$ACTUAL" != "$EXPECTED" ]]; then
    echo "ERROR: SHA-256 distinto. No extraer; revisa la descarga." >&2
    exit 1
  fi
  echo "OK: SHA-256 verificado."
fi

if [[ "${1:-}" == "--extract" ]]; then
  if [[ -s "$OUTPUT" ]]; then
    echo "Ya existe $OUTPUT. No se sobrescribe; usa el validador."
  else
    TEMP="$OUTPUT.part"
    trap 'rm -f "$TEMP"' EXIT
    echo "Extrayendo JSON Lines (requiere ~2,6 GB de disco)..."
    zstd -dc "$ARCHIVE" | tar -xOf - "$MEMBER" > "$TEMP"
    mv "$TEMP" "$OUTPUT"
    trap - EXIT
    echo "Extracción completada."
  fi
  wc -l "$OUTPUT"
  du -h "$OUTPUT"
  echo "Valida con: python3 scripts/validate_dataset.py"
else
  echo "Descarga completa. Para extraer: bash scripts/download_dataset.sh --extract"
fi
