# Переименование папки проекта: VELANTRIM_ExoCortex_V8.6 → V8.6
# Запускайте ПОСЛЕ закрытия Cursor/сервера (папка не должна быть занята).
#
#   cd C:\Users\VELAN\Documents\velantrim
#   .\VELANTRIM_ExoCortex_V8.6\scripts\rename_folder_to_V8.6.ps1

$ErrorActionPreference = "Stop"
$parent = "C:\Users\VELAN\Documents\velantrim"
$oldName = "VELANTRIM_ExoCortex_V8.6"
$newName = "V8.6"
$oldPath = Join-Path $parent $oldName
$newPath = Join-Path $parent $newName

if (-not (Test-Path $oldPath)) {
    if (Test-Path $newPath) {
        Write-Host "Уже переименовано: $newPath"
        exit 0
    }
    throw "Не найдена папка: $oldPath"
}

if (Test-Path $newPath) {
    Write-Host "Папка $newPath уже существует."
    Write-Host "Если это неполная копия — удалите её вручную и запустите скрипт снова."
    exit 1
}

Write-Host "Переименование: $oldPath -> $newPath"
Rename-Item -LiteralPath $oldPath -NewName $newName
Write-Host "Готово. Откройте в Cursor: $newPath"
