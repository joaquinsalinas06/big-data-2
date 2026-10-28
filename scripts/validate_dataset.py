#!/usr/bin/env python3
"""Valida en streaming el JSONL de ListenBrainz, sin cargarlo en RAM."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_REFERENCE_COUNT = 4_855_809


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar un JSONL de escuchas ListenBrainz")
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/processed/listens_full.jsonl"),
        help="Ruta del JSONL extraído",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=EXPECTED_REFERENCE_COUNT,
        help="Registros esperados (0 para no exigir cantidad fija)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Leer solo las primeras N líneas; no comprueba la cantidad total",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"ERROR: no existe {args.file}", file=sys.stderr)
        return 2

    total = invalid = missing_user_id = missing_recording_msid = 0
    min_ts = max_ts = None
    keys_seen = None
    examples = []

    with args.file.open("r", encoding="utf-8") as source:
        for line_no, line in enumerate(source, 1):
            if args.limit and line_no > args.limit:
                break

            total += 1
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("Se esperaba un objeto JSON")

                if keys_seen is None:
                    keys_seen = sorted(record.keys())

                metadata = record.get("track_metadata")
                ts = record.get("timestamp")
                valid = (
                    isinstance(record.get("user_name"), str)
                    and bool(record["user_name"].strip())
                    and type(ts) is int
                    and isinstance(metadata, dict)
                    and isinstance(metadata.get("artist_name"), str)
                    and bool(metadata["artist_name"].strip())
                    and isinstance(metadata.get("track_name"), str)
                    and bool(metadata["track_name"].strip())
                )
                if not valid:
                    raise ValueError("Faltan user_name, timestamp o artista/canción")

                if type(record.get("user_id")) is not int:
                    missing_user_id += 1
                if not record.get("recording_msid"):
                    missing_recording_msid += 1
                min_ts = ts if min_ts is None else min(min_ts, ts)
                max_ts = ts if max_ts is None else max(max_ts, ts)

            except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as exc:
                invalid += 1
                if len(examples) < 5:
                    examples.append(f"Línea {line_no}: {exc}")

    valid_count = total - invalid
    print("=== VALIDACIÓN LISTENBRAINZ ===")
    print(f"Archivo: {args.file}")
    print(f"Registros leídos: {total:,}")
    print(f"Registros válidos: {valid_count:,}")
    print(f"Registros inválidos: {invalid:,}")
    print(f"Registros sin user_id entero: {missing_user_id:,}")
    print(f"Registros sin recording_msid: {missing_recording_msid:,}")
    print(f"Claves del primer objeto: {keys_seen or []}")

    if min_ts is not None:
        print("Fecha mínima de escucha (UTC):", datetime.fromtimestamp(min_ts, timezone.utc))
        print("Fecha máxima de escucha (UTC):", datetime.fromtimestamp(max_ts, timezone.utc))
    if examples:
        print("Primeros errores:", "; ".join(examples))

    if invalid:
        print("ERROR: hay registros no válidos", file=sys.stderr)
        return 1
    if total == 0:
        print("ERROR: el archivo está vacío", file=sys.stderr)
        return 1
    if not args.limit and args.expected_count and total != args.expected_count:
        print(
            f"ERROR: se esperaban {args.expected_count:,} registros para este dump",
            file=sys.stderr,
        )
        return 1
    print("OK: dataset validado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
