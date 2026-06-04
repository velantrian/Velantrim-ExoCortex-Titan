# Kuzu (L3) — подключение в VELANTRIM V8.6

## 1. Установка пакета

```powershell
cd C:\Users\VELAN\Documents\velantrim\VELANTRIM_ExoCortex_V8.6
.\.venv\Scripts\python.exe -m pip install "kuzu>=0.7,<0.12"
```

## 2. Windows: VC++ Redistributable

Если при `import kuzu` ошибка **DLL load failed** — установите:

[Microsoft Visual C++ Redistributable (x64)](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist)

Проверка:

```powershell
.\.venv\Scripts\python.exe -c "import kuzu; db=kuzu.Database(':memory:'); print('Kuzu OK')"
```

## 3. Переменные окружения

Скопируйте из `config/exocortex-kuzu.env` в `.env` или выполните:

```powershell
Get-Content config\exocortex-kuzu.env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
    Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
  }
}
```

| Переменная | Значение |
|------------|----------|
| `STORAGE_BACKEND` | `kuzu` |
| `KUZU_DB_PATH` | `./data/exocortex.kuzu` |

## 4. Перезапуск сервера

**Обязательно** остановите старый uvicorn и запустите снова (бэкенд читается при старте):

```powershell
.\.venv\Scripts\uvicorn.exe server:app --host 127.0.0.1 --port 8755
```

В логе при успехе: `GraphStore: KuzuGraphStore`.  
При ошибке DLL: `Kuzu недоступен ... → sqlite` (fallback).

## 5. Проверка

```powershell
.\.venv\Scripts\python.exe -c "
import os
os.environ['STORAGE_BACKEND']='kuzu'
from core.storage_facade import reset_graph_store, storage_info
reset_graph_store()
print(storage_info())
"
```

Ожидается: `"local_store": "KuzuGraphStore"`.

`GET /layers/status` — слой L3 с `storage_backend: kuzu`.

## 6. MHI и `/health`

`graph_coverage` в MHI **пока** завязан на Neo4j (`l3_connected`), не на Kuzu.  
Kuzu даёт **L3-граф** для Etir / Immutable Core / Cypher, но не меняет текст рекомендации про Neo4j в health.
