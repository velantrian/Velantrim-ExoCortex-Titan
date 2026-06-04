# Запуск Velantrim с выбранным профилем развёртывания
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("citizen", "personal", "company", "science", "education", "research", "developer")]
    [string]$Profile,

    [string]$Port = "8755",
    [string]$ApiKey = "",
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$envFiles = @{
    citizen   = "config\profiles\citizen.env"
    personal  = "config\profiles\personal.env"
    company   = "config\profiles\company.env"
    science   = "config\profiles\science.env"
    education = "config\profiles\education.env"
    research  = "config\profiles\research.env"
    developer = "config\exocortex-dev.env"
}

$envPath = Join-Path $Root $envFiles[$Profile]
if (-not (Test-Path $envPath)) {
    Write-Error "Не найден файл профиля: $envPath"
}

Write-Host "Profile: $Profile"
Write-Host "ENV:     $envPath"

Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

$env:VELANTRIM_PROFILE = $Profile
if ($ApiKey) {
    $env:VELANTRIM_API_KEY = $ApiKey
}
if (-not $env:VELANTRIM_API_KEY) {
  $env:VELANTRIM_ALLOW_OPEN = "true"
  Write-Warning "VELANTRIM_API_KEY не задан — open mode (только dev)"
}

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

$uvicornArgs = @("-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", $Port)
if ($Reload) {
    $uvicornArgs += "--reload"
}

Write-Host ""
Write-Host "  WEB  http://127.0.0.1:$Port/console/"
Write-Host "  GET  http://127.0.0.1:$Port/profiles"
Write-Host "  GET  http://127.0.0.1:$Port/setup/llm"
Write-Host ""

& $py @uvicornArgs
