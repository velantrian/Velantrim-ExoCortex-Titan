# 🚀 Velantrim — Деплой на VPS

> **Titan 9.0 — ограничения развёртывания.** Это инструкции для локального
> тестирования и оценки на VPS, не production GO. Для hardened-профиля
> используйте [docker-compose.prod.yml](../docker-compose.prod.yml) и
> [контракт развёртывания](operations/hardened-production-profile.md).
> Для обычного сервера API-ключ обязателен, кроме явно открытого dev-режима;
> CORS по умолчанию отключён. Dense-модель — опциональная зависимость.

## Быстрый старт (5 минут)

### 1. На сервере

```bash
# Python 3.11+
python3 --version

# Клонируй проект
git clone <твой репозиторий> velantrim
cd velantrim

# Требуется uv; зависимости из канонического uv.lock
uv sync --frozen --extra server

# Опционально для dense retrieval:
# uv sync --frozen --extra server --extra retrieval --extra embeddings

# Настройка
cp .env.example .env

# КРИТИЧНО: сгенерируй и впиши API ключ
# Сгенерируй ключ, замени существующее пустое поле (не добавляй дубликат).
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Для пассивной памяти установи SLEEP_WORKER_ENABLED=false.
# LLM_PROVIDER=none не запрещает request-level provider overrides:
# оставь VELANTRIM_NETWORK_MODE=deny и VELANTRIM_REMOTE_DATA_MODE=never.
nano .env

# Создай папку для данных
mkdir -p data

# Запуск
uv run --no-sync uvicorn server:app --host 127.0.0.1 --port 8000
```

> ⚠️ Если стартуешь **без** VELANTRIM_API_KEY — сервер упадёт с RuntimeError.
> Для локальной разработки без auth установи `VELANTRIM_ALLOW_OPEN=true`
> (это включит warning'и в логах — НЕ для production!).

### 2. Проверка

```bash
# Health check (не требует auth)
curl http://localhost:8000/health

# Первый запрос — с реальным ключом из .env
curl -X POST http://localhost:8000/query \
  -H "X-Api-Key: $(grep ^VELANTRIM_API_KEY .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is quantum entanglement?", "mode": "BALANCED"}'
```

---

## Docker

```bash
# Сборка (multi-stage: builder компилирует wheel, runtime — без dev/gcc)
docker build -t velantrim-titan .

# Опционально — более широкий runtime-набор extras (по умолчанию только "server"):
docker build --build-arg RUNTIME_EXTRAS=server,parsers,retrieval,embeddings -t velantrim-titan:full .

# Запуск
docker run -d -p 127.0.0.1:8000:8000 \
  -e VELANTRIM_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))") \
  -v velantrim_data:/app/data \
  velantrim-titan

curl http://localhost:8000/health
```

Исторические compatibility/dev профили (`docker-compose.yml` / `docker-compose.dev.yml`) — только для контролируемой исследовательской среды. Для обычного развёртывания следуйте hardened-профилю из README:

```bash
cp .env.prod.example .env.prod
# Заполни VELANTRIM_API_KEY в .env.prod.
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

Заметки:
- Образ работает от фиксированного non-root пользователя (uid/gid `10001`), не от root.
- `RUNTIME_EXTRAS` (build arg) по умолчанию ставит только `server` extra
  (fastapi/uvicorn/pydantic/httpx/aiosqlite/pymorphy3 из uv.lock) — `dev` (pytest/ruff/mypy) и
  `audio` (openai-whisper) в runtime-образ никогда не попадают неявно.
- `.github/workflows/docker.yml` — CI job, который собирает образ
  `--no-cache`, проверяет `/health`, non-root uid и отсутствие
  `.git`/`.env`/кешей/БД в итоговом образе на каждый relevant PR/push.

---

## VPS с reverse proxy — пример для оценки, не hardened production

### systemd сервис

```ini
# /etc/systemd/system/velantrim.service
[Unit]
Description=Velantrim ExoCortex API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/velantrim
EnvironmentFile=/home/ubuntu/velantrim/.env
ExecStart=/home/ubuntu/velantrim/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable velantrim
sudo systemctl start velantrim
sudo systemctl status velantrim
```

### nginx reverse proxy (с SSL)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }
}
```

```bash
# SSL через certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## API Endpoints

Ниже — выборка основных маршрутов. OpenAPI и Swagger доступны только при
`ENABLE_API_DOCS=true` (включать исключительно в контролируемой локальной среде);
по умолчанию и в hardened-профиле `/openapi.json` и `/docs` отключены.
`/health/recovery` проверяет состояние восстановления; `/health` сам по себе
не доказывает готовность всех функций или production authorization.

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/` | Веб-консоль (redirect при наличии UI) |
| GET | `/api` | JSON-информация о сервере |
| GET | `/health` | MHI + статус компонентов |
| POST | `/query` | Главный запрос (memory + LLM) |
| GET | `/facts` | Список фактов |
| GET | `/facts/{id}` | Получить факт |
| POST | `/facts` | Создать факт |
| PATCH | `/facts/{id}/transition` | Изменить ESM состояние |
| PATCH | `/facts/{id}/invalidate` | Инвалидировать факт |
| GET | `/facts/{id}/time-travel` | Time-travel запрос |
| POST | `/ingest/text` | Загрузить текст |
| GET | `/memory/stats` | Статистика памяти |
| POST | `/memory/rebuild-index` | Перестроить NGram |
| GET | `/agent/notebook` | Блокнот агента |
| GET | `/agent/suggest` | Следующий шаг |
| POST | `/agent/episode` | Обновить из эпизода |

**Документация API:** `http://127.0.0.1:8000/docs` только при `ENABLE_API_DOCS=true`.

---

## Примеры запросов

### Query с LLM
```bash
curl -X POST https://your-domain.com/query \
  -H "X-Api-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Расскажи о квантовой запутанности",
    "mode": "BALANCED",
    "use_llm": true
  }'
```

### Добавить факт
```bash
curl -X POST https://your-domain.com/facts \
  -H "X-Api-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Velantrim — долговременная память для AI агентов",
    "source": "documentation",
    "confidence": 0.99
  }'
```

### Загрузить текст
```bash
curl -X POST https://your-domain.com/ingest/text \
  -H "X-Api-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Длинный текст для загрузки в память...",
    "source": "my_document",
    "confidence": 0.85,
    "chunk_size": 500
  }'
```

### Проверить здоровье
```bash
curl https://your-domain.com/health
# Ответ: {"mhi": {"score": 0.72, "status": "HEALTHY"}, ...}
```

---

## Минимальные требования VPS

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | **1 GB** | 2 GB |
| Диск | 5 GB | 20 GB |
| Python | 3.11 | 3.11+ |
| OS | Ubuntu 22.04 | Ubuntu 24.04 |

> Это ориентиры старого VPS-профиля, а не измеренные минимумы Titan 9.0.
> Dense retrieval, парсеры, размер базы и выбранный профиль меняют требования;
> проверяйте память и дисковые лимиты на собственном тестовом развёртывании.

---

## Известные ограничения

- **SQLite** — поддерживаемый профиль сервера: один worker на локальной файловой системе. Есть ограниченные межпроцессные тесты, но нет общей production-scale гарантии. PostgreSQL/Neo4j не следует считать заменой Canon без отдельного допуска.
- **Sync pipeline** — каждый запрос в отдельном thread. Sprint 2c → async
- **LLM** — только при подходящей конфигурации запроса и разрешённой egress policy; запрос памяти не обязан вызывать модель.
- **HybridRetriever** — dense-сигнал опционален; время загрузки зависит от модели, оборудования и кэша.
- **FileIngester** — PDF/DOCX требуют дополнительных зависимостей
- **TruthGate contradiction-stage** — отключена по умолчанию (false positives на naive).
  Включается через `TruthGate(store, contradiction_detector="naive")` — только dev.
