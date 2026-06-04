# Запуск VELANTRIM с LadybugDB L3 (V8.6) — форк Kuzu (Kuzu заархивирован окт. 2025)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$envFile = Join-Path $Root "config\exocortex-ladybug.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
        }
    }
}

if (-not $env:VELANTRIM_API_KEY) { $env:VELANTRIM_API_KEY = "dev-local-only-change-me" }
if (-not $env:VELANTRIM_DB_PATH) { $env:VELANTRIM_DB_PATH = ".\data\velantrim.db" }
if (-not $env:VELANTRIM_NGRAM_DB) { $env:VELANTRIM_NGRAM_DB = ".\data\velantrim_ngram.db" }
if (-not $env:PORT) { $env:PORT = "8755" }

Write-Host "STORAGE_BACKEND=$env:STORAGE_BACKEND"
Write-Host "LADYBUG_DB_PATH=$env:LADYBUG_DB_PATH"
Write-Host "Проверка LadybugDB..."
& "$Root\.venv\Scripts\python.exe" -c "import ladybug; print('LadybugDB OK', ladybug.__version__)"
Write-Host "Старт uvicorn на порту $env:PORT ..."
& "$Root\.venv\Scripts\uvicorn.exe" server:app --host 127.0.0.1 --port $env:PORT
