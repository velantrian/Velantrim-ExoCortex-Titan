# Остановить Velantrim на указанном порту (по умолчанию 8755)
param([int]$Port = 8755)

function Get-PortListenerPids {
    param([int]$Port)
    @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { $_.OwningProcess } |
        Select-Object -Unique)
}

function Get-UvicornPidsOnPort {
    param([int]$Port)
    $pattern = "--port\s+$Port\b"
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(\.exe)?$' -and
            $_.CommandLine -match 'uvicorn' -and
            $_.CommandLine -match $pattern
        } |
        ForEach-Object { $_.ProcessId } |
        Select-Object -Unique
}

$targets = @(
    (Get-PortListenerPids -Port $Port)
    (Get-UvicornPidsOnPort -Port $Port)
) | ForEach-Object { $_ } | Select-Object -Unique

if (-not $targets) {
    Write-Host "На порту $Port ничего не слушает."
    exit 0
}

foreach ($procId in $targets) {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue).CommandLine
    Write-Host "Останавливаю PID $procId (порт $Port)..."
    if ($cmd) { Write-Host "  $cmd" }
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

$left = Get-PortListenerPids -Port $Port
if ($left) {
    Write-Host "Порт $Port всё ещё занят (PID: $($left -join ', ')) — повторная остановка..."
    foreach ($procId in $left) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

if (Get-PortListenerPids -Port $Port) {
    Write-Host "⚠️  Порт $Port не освободился. Закройте процесс вручную."
} else {
    Write-Host "Готово. Запустите: .\scripts\start_console.ps1"
}
