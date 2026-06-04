# Запуск Velantrim с веб-консолью (останавливает старый процесс на порту)
param(
    [int]$Port = 8755,
    [switch]$NoKill,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$index = Join-Path $Root "static\console\index.html"
if (-not (Test-Path $index)) {
    Write-Error "Нет $index — нужна папка VELANTRIM_ExoCortex_V8.6"
}

if (-not $NoKill) {
    & (Join-Path $PSScriptRoot "stop_server.ps1") -Port $Port
}

# Сброс устаревшего bytecode (иначе API отдаёт старый каталог gpt-4o / gemini-2.0)
Get-ChildItem -Path $Root -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Кэш Python (__pycache__) очищен"

if (-not $env:VELANTRIM_API_KEY) {
    $envFile = Join-Path $Root ".env"
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile -Encoding UTF8) {
            if ($line -match '^\s*VELANTRIM_API_KEY\s*=\s*(.+)\s*$') {
                $env:VELANTRIM_API_KEY = $Matches[1].Trim().Trim('"').Trim("'")
                break
            }
        }
    }
    if (-not $env:VELANTRIM_API_KEY) {
        $env:VELANTRIM_API_KEY = "dev-console-key"
    }
    if (-not $env:VELANTRIM_ALLOW_OPEN) {
        $env:VELANTRIM_ALLOW_OPEN = "true"
    }
    Write-Host "API key: $($env:VELANTRIM_API_KEY) (dev)"
}

$env:PORT = "$Port"
$env:SLEEP_WORKER_ENABLED = if ($env:SLEEP_WORKER_ENABLED) { $env:SLEEP_WORKER_ENABLED } else { "false" }
$env:LLM_PROVIDER = if ($env:LLM_PROVIDER) { $env:LLM_PROVIDER } else { "none" }

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

$base = "http://127.0.0.1:$Port"
$consoleUrl = "$base/console/?v=34"
Write-Host ""
Write-Host "Папка:   $Root"
Write-Host "Консоль (откройте в браузере):"
Write-Host "  $consoleUrl" -ForegroundColor Cyan
Write-Host "Проверка: $base/debug/console"
Write-Host "LLM тест:  POST $base/console/llm/test"
Write-Host ""

if (-not $NoBrowser) {
    Start-Process $consoleUrl
}

# Быстрая проверка LLM API после старта (в фоне, не блокирует uvicorn)
Start-Job -ScriptBlock {
    param($Url)
    Start-Sleep -Seconds 4
    try {
        $r = Invoke-RestMethod -Uri "$Url/console/llm/providers" -TimeoutSec 8
        if ($r.catalog_build_id) {
            Write-Host "[OK] catalog_build_id: $($r.catalog_build_id)" -ForegroundColor Green
        } else {
            Write-Host "[!] Нет catalog_build_id — запущен СТАРЫЙ server.py (не из этой папки)" -ForegroundColor Red
        }
        if ($r.providers) {
            Write-Host "[OK] LLM API: $($r.providers.Count) провайдеров"
        }
        $gem = $r.providers | Where-Object { $_.id -eq "gemini" } | Select-Object -First 1
        $ds = $r.providers | Where-Object { $_.id -eq "deepseek" } | Select-Object -First 1
        if ($gem) {
            $rev = $r.gemini_catalog_revision
            if ($rev -eq "2026-05-gemini-v2" -and ($gem.models -contains "gemini-3.5-flash")) {
                Write-Host "[OK] Каталог Gemini: 3.5/3.1/2.5 ($($gem.models.Count) моделей)" -ForegroundColor Green
            } else {
                Write-Host "[!] УСТАРЕВШИЙ каталог Gemini" -ForegroundColor Red
                Write-Host "    Сейчас: $($gem.models -join ', ')" -ForegroundColor Yellow
            }
        }
        if ($ds -and ($ds.models -contains "deepseek-v4-flash")) {
            Write-Host "[OK] DeepSeek v4 в каталоге" -ForegroundColor Green
        } elseif ($ds) {
            Write-Host "[!] Устаревший DeepSeek: $($ds.models -join ', ')" -ForegroundColor Red
        }
    } catch {
        Write-Host "[!] LLM API недоступен — дождитесь старта uvicorn или перезапустите скрипт"
    }
} -ArgumentList $base | Out-Null

& $py -m uvicorn server:app --host 127.0.0.1 --port $Port
