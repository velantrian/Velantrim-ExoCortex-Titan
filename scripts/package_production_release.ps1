# 📦 Упаковать production БД для GitHub Release (не коммитить в git).
# Использование:
#   powershell -File scripts/package_production_release.ps1
#   powershell -File scripts/package_production_release.ps1 -OutDir dist

param(
    [string]$OutDir = "dist"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$stamp = Get-Date -Format "yyyyMMdd"
$zipName = "velantrim_production_db_$stamp.zip"
$outPath = Join-Path $OutDir $zipName

$files = @(
    @{ Path = "data/velantrim_kb_clean_20260710_graph.db"; Required = $true },
    @{ Path = "data/exocortex_graph.db"; Required = $true },
    @{ Path = "data/exocortex.lbug"; Required = $true },
    @{ Path = "data/ngram_house.db"; Required = $true },
    @{ Path = "kb_graph.json"; Required = $true },
    @{ Path = "data/kb_ru_en_cache.json"; Required = $false }
)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stage = Join-Path $env:TEMP "velantrim_release_$stamp"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

$manifest = @()
foreach ($item in $files) {
    $full = Join-Path $Root $item.Path
    if (-not (Test-Path $full)) {
        if ($item.Required) {
            throw "Обязательный файл не найден: $($item.Path)"
        }
        Write-Host "⚠ пропуск (нет файла): $($item.Path)"
        continue
    }
    $destDir = Join-Path $stage (Split-Path $item.Path -Parent)
    if ($destDir -and -not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    }
    Copy-Item $full (Join-Path $stage $item.Path) -Force
    $hash = (Get-FileHash $full -Algorithm SHA256).Hash.ToLower()
    $size = (Get-Item $full).Length
    $manifest += [PSCustomObject]@{
        path = $item.Path
        bytes = $size
        sha256 = $hash
    }
    Write-Host "✅ $($item.Path) ($([math]::Round($size/1MB,1)) MB)"
}

$manifest | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $stage "MANIFEST.json") -Encoding UTF8
@"
# Velantrim Titan 9.0 — Production Database Bundle
Generated: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")

Unpack into repository root, then set .env:

VELANTRIM_DB_PATH=./data/velantrim_kb_clean_20260710_graph.db
STORAGE_BACKEND=ladybug
LADYBUG_DB_PATH=./data/exocortex.lbug
SQLITE_GRAPH_PATH=./data/exocortex_graph.db
VELANTRIM_NGRAM_DB=./data/ngram_house.db

Verify SHA256 against MANIFEST.json before use.
"@ | Set-Content (Join-Path $stage "README.txt") -Encoding UTF8

if (Test-Path $outPath) { Remove-Item -Force $outPath }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $outPath -CompressionLevel Optimal
Remove-Item -Recurse -Force $stage

$zipHash = (Get-FileHash $outPath -Algorithm SHA256).Hash.ToLower()
$zipMb = [math]::Round((Get-Item $outPath).Length / 1MB, 1)
Write-Host ""
Write-Host "📦 Release zip: $outPath ($zipMb MB)"
Write-Host "🔐 SHA256: $zipHash"
