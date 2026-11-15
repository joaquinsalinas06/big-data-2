# Descarga y verificación del incremental ListenBrainz 2746 en Windows.
# Requiere PowerShell, curl.exe y Python >= 3.14 (tarfile soporta .tar.zst).
# Uso: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\download_dataset.ps1 -Extract
param([switch]$Extract)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$raw = Join-Path $root "data\raw"
$processed = Join-Path $root "data\processed"
New-Item -ItemType Directory -Force -Path $raw, $processed | Out-Null

$name = "listenbrainz-listens-dump-2746-20261027-000003-incremental"
$base = "https://data.metabrainz.org/pub/musicbrainz/listenbrainz/incremental/listenbrainz-dump-2746-20261027-000003-incremental"
$url = "$base/$name.tar.zst"
$archive = Join-Path $raw "listenbrainz-20261027.tar.zst"
$checksum = Join-Path $raw "listenbrainz-20261027.sha256"
$output = Join-Path $processed "listens_full.jsonl"

if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
    throw "No se encontró curl.exe. Actualiza Windows o instala curl."
}

Write-Host "Descargando SHA-256 oficial..."
& curl.exe -fL --retry 3 -o "$checksum.part" "$url.sha256"
if ($LASTEXITCODE -eq 0) {
    Move-Item -LiteralPath "$checksum.part" -Destination $checksum -Force
} elseif ((Test-Path -LiteralPath $checksum) -and (Get-Item -LiteralPath $checksum).Length -gt 0) {
    Remove-Item -LiteralPath "$checksum.part" -ErrorAction SilentlyContinue
    Write-Host "El SHA-256 ya no está publicado; se usa la copia local $checksum."
} else {
    Remove-Item -LiteralPath "$checksum.part" -ErrorAction SilentlyContinue
    throw "No se pudo descargar el SHA-256 y no hay copia local en $checksum."
}

$expected = ((Get-Content -LiteralPath $checksum -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
if ($expected -notmatch '^[0-9a-f]{64}$') { throw "Archivo SHA-256 inválido." }

if (Test-Path -LiteralPath $archive) {
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
} else {
    $actual = ""
}

if ($actual -ne $expected) {
    Write-Host "Descargando archivo original (~238 MB)..."
    & curl.exe -fL --retry 3 -C - -o $archive $url
    if ($LASTEXITCODE -ne 0) { throw "Falló la descarga del dataset." }
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        throw "SHA-256 no coincide. Elimina el archivo incompleto de data/raw/ y reintenta."
    }
}
Write-Host "OK: SHA-256 verificado."

if (-not $Extract) {
    Write-Host "Para extraer: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\download_dataset.ps1 -Extract"
    exit 0
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "No se encontró Python. Instala Python 3.14 con winget y abre una nueva terminal."
}
& python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 14) else 1)'
if ($LASTEXITCODE -ne 0) { throw "Se requiere Python 3.14 o superior para extraer .tar.zst sin dependencias." }

if (Test-Path -LiteralPath $output) {
    Write-Host "Ya existe $output. No se sobrescribe; ejecuta la validación."
} else {
    $temporary = Join-Path $processed ".extract-2746"
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $temporary | Out-Null
    Write-Host "Extrayendo (~2,6 GB). No cerrar esta ventana..."
    & python -m tarfile -e $archive $temporary
    if ($LASTEXITCODE -ne 0) { throw "Error al extraer el archivo." }

    $source = Join-Path $temporary "$name\listens\2026\10.listens"
    if (-not (Test-Path -LiteralPath $source)) {
        throw "No se encontró listens/2026/10.listens dentro del archivo."
    }
    Move-Item -LiteralPath $source -Destination $output
    Remove-Item -LiteralPath $temporary -Recurse -Force
    Write-Host "OK: extracción completada."
}

Write-Host "Archivo: $output"
Write-Host "Tamaño (bytes): $((Get-Item -LiteralPath $output).Length)"
Write-Host "Valida con: python scripts\validate_dataset.py"
