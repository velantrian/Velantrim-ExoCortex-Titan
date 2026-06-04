<#
.SYNOPSIS
  Запустить Velantrim в "умном" режиме на графе знаний (одна команда).

.DESCRIPTION
  Включает все слои рассуждения (Essence + graph-expansion + truth_policy + causal_graph)
  на отдельной KB-БД (data/velantrim_kb.db), не трогая разговорную velantrim.db.
  Если графа ещё нет (или -Rebuild) — сперва строит его через build_kb_graph.py.

.PARAMETER Port
  Порт сервера (по умолчанию 8000).

.PARAMETER Rebuild
  Перестроить граф знаний из текущей KB перед запуском (после новых батчей Codex).

.EXAMPLE
  .\scripts\serve_smart_kb.ps1
  .\scripts\serve_smart_kb.ps1 -Rebuild          # пересобрать граф (KB выросла)
  .\scripts\serve_smart_kb.ps1 -Port 8755

.NOTES
  Проверять качество рассуждения: .venv\Scripts\python.exe scripts\eval_reasoning.py
  Качество растёт со связностью KB (ID-связи в батчах Codex + рост к 50k).
#>
param(
    [int]$Port = 8000,
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$py = ".venv\Scripts\python.exe"
$db = "data\velantrim_kb.db"

if (-not (Test-Path $py)) {
    Write-Error "Не найден $py — активируй/создай .venv в корне репозитория."
    exit 1
}

if ($Rebuild -or -not (Test-Path $db)) {
    Write-Host "🔗 Строю связный граф знаний (build_kb_graph.py)..." -ForegroundColor Cyan
    & $py scripts\build_kb_graph.py
    if ($LASTEXITCODE -ne 0) { Write-Error "build_kb_graph упал"; exit 1 }
}

# Умный режим: все слои рассуждения ON, отдельная KB-БД, мультиязычные эмбеддинги.
$env:VELANTRIM_DB_PATH         = $db
$env:ENABLE_ESSENCE            = "1"
$env:ENABLE_GRAPH_EXPANSION    = "1"
$env:ENABLE_TRUTH_POLICY       = "1"
$env:ENABLE_CAUSAL_GRAPH       = "1"
$env:VELANTRIM_ALLOW_OPEN      = "true"   # dev: без API-ключа (для прод — задай VELANTRIM_API_KEY)
# $env:VELANTRIM_GRAPH_EXPANSION_DEPTH = "2"  # длиннее цепочки (когда связность подрастёт)

Write-Host ""
Write-Host "🧠 Velantrim SMART на $db" -ForegroundColor Green
Write-Host "   → http://127.0.0.1:$Port   (консоль: /console, запрос: POST /query)" -ForegroundColor Green
Write-Host ""

& $py -m uvicorn server:app --port $Port
