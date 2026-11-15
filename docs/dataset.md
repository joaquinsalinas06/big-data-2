# Dataset: ListenBrainz

## 1. ¿Qué es?

[ListenBrainz](https://listenbrainz.org/data/) es un proyecto de MetaBrainz que recopila **escuchas** enviadas por sus usuarios. Una escucha indica que un usuario reprodujo una canción en un momento específico. No representa ventas, suscriptores de Spotify ni popularidad global. Sus datos públicos de escuchas se ofrecen bajo licencia **CC0**, según ListenBrainz.

Este dataset es útil para estudiar diversidad de gustos, intensidad de escucha, relaciones usuario–canción–artista y cambios temporales.

## 2. Qué descarga el equipo

Usamos un archivo **incremental** concreto, de modo que todos trabajemos con una versión reproducible, incluso cuando aparezcan nuevos dumps:

| Propiedad | Valor |
| --- | --- |
| Origen | [MetaBrainz — incrementales](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/) |
| Corte | 2026-10-27, dump **2746** |
| Tipo | `listenbrainz-listens-dump` |
| Comprimido | `.tar.zst`, aprox. 238 MB |
| Extraído | `.listens` / JSON Lines, aprox. 2,6 GB |
| Registros leídos y validados en la prueba inicial | **4 855 809** |
| Ruta de salida recomendada | `data/processed/listens_full.jsonl` |
| SHA-256 | Se obtiene del archivo oficial `.sha256`; **no** es un dataset adicional |

**No es todo ListenBrainz.** Los incrementales contienen eventos *enviados* desde el incremental anterior. Para reconstruir una réplica completa y coherente de toda la plataforma, se requiere un full dump y aplicar los incrementales; las eliminaciones también requieren reconciliación con un full dump. Aquí estudiamos expresamente este **lote de ingesta**.

### Resultados de la exploración local previa

En el archivo de referencia, el equipo observó:

- **4 855 809** escuchas.
- **26 394** usuarios únicos (según `user_id`).
- **286 291** nombres de artistas distintos.
- **1 066 683** combinaciones de nombre de artista y título de canción.
- Fechas de escucha entre **2005-02-13** y **2026-10-27** (UTC).

Estas cantidades proceden de una exploración local inicial; son descriptivas de **este incremento**, no estimaciones poblacionales de ListenBrainz. Los recuentos por nombre no equivalen necesariamente a artistas o grabaciones únicos: pueden existir homónimos, diferentes grafías y datos sin identificador musical.

### Validación para Neo4j

La preparación completa posterior comprobó que las **4 855 809** filas de este lote tienen `user_id` entero y `recording_msid` no vacío. Identificó **1 420 842 recording_msid distintos**, frente a las 1 066 683 combinaciones de artista y título contadas anteriormente: son criterios de identidad diferentes. El grafo utiliza el identificador, sin fusionar canciones por título. Esto no garantiza equivalencia con grabaciones canónicas de MusicBrainz.

Los archivos originales y la muestra de 200 mil filas se trasladaron al directorio `data/` de este repositorio. Los comandos compartidos dependen de las rutas del repositorio, sin enlaces a otra carpeta de una laptop. Ver [modelo y carga de Neo4j](../databases/neo4j/README.md) y [resultados verificados](neo4j.md).

## 3. Formato de cada registro

Cada línea del archivo `.listens` es **un objeto JSON**. Estructura representativa y **ficticia**, con datos sustituidos para evitar publicar datos personales:

```json
{
  "user_id": 12345,
  "user_name": "usuario_ejemplo",
  "timestamp": 1793061000,
  "recording_msid": "identificador-ejemplo",
  "track_metadata": {
    "track_name": "Cancion de ejemplo",
    "artist_name": "Artista de ejemplo",
    "release_name": "Album de ejemplo",
    "additional_info": {}
  }
}
```

| Campo | Significado | Observaciones |
| --- | --- | --- |
| `user_id` | Identificador interno de usuario | Entero observado en el dump; se reportan ausentes por separado en la validación |
| `user_name` | Nombre de usuario | Dato público; evitar mostrarlo innecesariamente |
| `timestamp` | Fecha de **escucha**, Unix UTC | **En este dump es `timestamp`, no `listened_at`** |
| `recording_msid` | Identificador musical disponible | Puede faltar; no utilizarlo sin comprobar cobertura |
| `track_metadata.track_name` | Nombre de canción | Texto libre |
| `track_metadata.artist_name` | Nombre de artista | Texto libre |
| `track_metadata.release_name` | Álbum/lanzamiento | Opcional |
| `track_metadata.additional_info` | Metadatos adicionales | Opcional; puede contener identificadores musicales |

**Cuidado:** algunas respuestas de la **API de ListenBrainz** usan `listened_at`, pero el **archivo .listens descargado por este proyecto** contiene `timestamp`. Los scripts del repositorio están adaptados al formato observado.

## 4. Opciones de descarga de ListenBrainz

- **fullexport:** snapshot completo, demasiado grande para comenzar (del orden de cientos de GB).
- **incremental:** nuevos registros incorporados desde el anterior; **opción seleccionada**.
- **spark:** exportación orientada a procesamiento distribuido.
- **sample / otros:** conjuntos o metadatos adicionales, según el directorio.

Las ubicaciones de descarga de Europa/EE. UU. son espejos de los datos, no proyectos distintos. Los archivos `.md5` / `.sha256` son solo sumas de verificación.

## 5. Descargar, verificar y validar

Desde la raíz del repositorio (macOS):

```bash
brew install zstd
bash scripts/download_dataset.sh --extract
python3 scripts/validate_dataset.py
```

El primer script comprueba la huella SHA-256 oficial y deja el JSONL en `data/processed/`. MetaBrainz solo mantiene publicados los incrementales de las últimas semanas y el 2746 ya no está en su servidor. Si el comprimido `listenbrainz-20261027.tar.zst` y su `listenbrainz-20261027.sha256` ya están en `data/raw/` (por ejemplo, copiados de otro integrante), el script usa ese checksum local cuando no puede descargar el oficial, verifica el comprimido y extrae. El segundo valida **en streaming**, muestra fechas extremas y cuenta registros inválidos.

Para inspeccionar una pequeña porción sin cargar todo:

```bash
python3 scripts/validate_dataset.py --limit 1000
```

La opción `--limit` valida solo un prefijo y **no** exige que haya 4 855 809 filas. No sustituye a la validación total.

## 6. Consideraciones para el informe

1. **No confundir ingesta con escucha:** un registro añadido en 2026 puede tener una fecha `timestamp` de 2005.
2. **No extrapolar rankings globales:** el incremento está condicionado por quiénes enviaron datos en ese lote.
3. **No deduplicar por título solamente:** una canción puede tener múltiples versiones y artistas con el mismo nombre.
4. **No publicar identificadores personales ni datos brutos en GitHub:** compartir preferentemente estadísticas agregadas y documentación.
5. **La validación básica no prueba ausencia de duplicados**, ni que todos los eventos sean independientes o representativos. Es un control de formato, no una auditoría estadística.

## Enlaces oficiales

- [ListenBrainz — Data Downloads](https://listenbrainz.org/data/)
- [ListenBrainz — Data Dumps](https://listenbrainz.readthedocs.io/en/latest/users/listenbrainz-dumps.html)
- [ListenBrainz — JSON Documentation](https://listenbrainz.readthedocs.io/en/latest/users/json.html)
- [Directorio de descarga del incremental 2746](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/listenbrainz-dump-2746-20261027-000003-incremental/)
