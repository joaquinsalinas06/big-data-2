#!/usr/bin/env bash
# Descarga verificable del incremental ListenBrainz 2746 (2026-10-27).
# Uso: bash scripts/download_dataset.sh [--extract]
set -euo pipefail

if [[ "${1:-}" != "" && "${1:-}" != "--extract" ]]; then
  echo "Uso: bash scripts/download_dataset.sh [--extract]" >&2
  exit 2
fi

for cmd in curl shasum awk zstd tar; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Falta $cmd. Instala zstd con: brew install zstd (macOS)" >&2
    exit 1
  fi
done

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
curl -fL --retry 3 -o "$CHECKSUM" "$URL.sha256"
EXPECTED="$(awk 'NR==1 {print $1}' "$CHECKSUM")"
if [[ ! "$EXPECTED" =~ ^[[:xdigit:]]{64}$ ]]; then
  echo "Archivo de checksum inválido." >&2
  exit 1
fi

if [[ -f "$ARCHIVE" ]]; then
  ACTUAL="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
else
  ACTUAL=""
fi

if [[ "$ACTUAL" == "$EXPECTED" ]]; then
  echo "Archivo comprimido existente: SHA-256 correcto."
else
  echo "Descargando archivo oficial (~238 MB)..."
  curl -fL --retry 3 -C - -o "$ARCHIVE" "$URL"
  ACTUAL="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
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
