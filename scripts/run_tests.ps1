# Запуск тестов VELANTRIM V8.6 (PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Host "Создаём .venv..."
    python -m venv .venv
    $Py = Join-Path $Root ".venv\Scripts\python.exe"
    & $Py -m ensurepip --upgrade
}

& $Py -m pip install -r requirements-dev.txt -q

$env:VELANTRIM_API_KEY = "test-key"
$env:VELANTRIM_ALLOW_OPEN = "true"
$env:LLM_PROVIDER = "none"
$env:SLEEP_WORKER_ENABLED = "false"

$Target = $args[0]
if (-not $Target) { $Target = "tests/" }

Write-Host "pytest $Target ..."
& $Py -m pytest $Target --tb=short --no-cov @args[1..($args.Length)]
