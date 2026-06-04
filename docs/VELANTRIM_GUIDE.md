# 🚀 Velantrim ExoCortex — Установка и запуск

> **Версия:** v8.5.0
> **Для кого:** разработчик, который хочет поднять систему с нуля
> **Время:** ~30 минут на первый запуск

---

## 📋 Содержание

1. [Требования](#1-требования)
2. [Структура папок](#2-структура-папок)
3. [Установка по шагам](#3-установка-по-шагам)
4. [Применение архивов](#4-применение-архивов)
5. [Конфигурация (.env)](#5-конфигурация-env)
6. [SQLite миграции](#6-sqlite-миграции)
7. [Запуск тестов](#7-запуск-тестов)
8. [Запуск сервера](#8-запуск-сервера)
9. [Проверка работы](#9-проверка-работы)
10. [Полезные команды](#10-полезные-команды)
11. [Частые проблемы](#11-частые-проблемы)
12. [Опциональные зависимости](#12-опциональные-зависимости)

---

## 1. ✅ Требования

| Компонент | Минимум | Рекомендуется |
|---|---|---|
| **Python** | 3.11 | 3.12+ |
| **RAM** | 1 GB | 2 GB |
| **Диск** | 5 GB | 20 GB |
| **ОС** | Windows / macOS / Linux | Ubuntu 24.04 |

**Проверь Python:**
```bash
python --version
# Должно быть: Python 3.11.x или новее
```

Если Python старше — скачай с [python.org](https://python.org).

---

## 2. 🗂️ Структура папок

Вот как должна выглядеть папка проекта после установки:

```
velantrim-exocortex-crystal/          ← корень (назови как хочешь)
│
├── 🧠 core/                          ← ВСЁ ЯДРО ЗДЕСЬ
│   │
│   ├── 📁 file_parsers/              ← парсеры (Этап 1)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── file_ingester.py          ← точка входа для парсинга
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── pptx_parser.py
│   │   ├── text_parser.py
│   │   ├── csv_parser.py
│   │   ├── image_parser.py
│   │   ├── audio_parser.py
│   │   ├── video_parser.py
│   │   ├── epub_parser.py
│   │   ├── email_parser.py
│   │   ├── html_parser.py
│   │   └── archive_parser.py
│   │
│   ├── 📁 file_generators/           ← генераторы файлов (Этап 2)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── file_exporter.py          ← точка входа для генерации
│   │   ├── pdf_generator.py
│   │   ├── docx_generator.py
│   │   ├── pptx_generator.py
│   │   ├── xlsx_generator.py
│   │   ├── html_generator.py
│   │   ├── markdown_generator.py
│   │   └── universal_generator.py
│   │
│   ├── 📁 velantrim_reports/         ← готовые шаблоны отчётов (Этап 3)
│   │   ├── __init__.py
│   │   ├── mhi_report.py
│   │   ├── truthgate_report.py
│   │   ├── knowledge_base.py
│   │   └── sprint_review.py
│   │
│   ├── __init__.py                   ← экспортирует __version__
│   ├── memory.py                     ← хранение фактов
│   ├── pipeline.py                   ← оркестратор запросов
│   ├── truth_gate.py                 ← верификация (NLI v8.4.4)
│   ├── mhi.py                        ← Memory Health Index
│   ├── hybrid_retriever.py           ← BM25 + Dense + RRF
│   ├── ngram_index.py                ← FTS5 pre-filter
│   ├── sleep_time_worker.py          ← фоновая консолидация
│   ├── embedding_registry.py         ← реестр embedding моделей
│   ├── storage.py                    ← SQLiteGraphStore ABC
│   ├── trace.py                      ← provenance W3C PROV-O
│   ├── causal_graph.py               ← 🆕 Patch 13 (причинные связи)
│   ├── living_context.py             ← 🆕 Patch 14 (живой контекст)
│   ├── understanding_layer.py        ← 🆕 Patch 13+14 объединение
│   └── affordance_linker.py          ← 🆕 Variant C MVP
│
├── 🌐 server_patch/                  ← дополнительные API endpoints
│   └── export_endpoints.py
│
├── 🎯 skills/                        ← документация best practices
│   ├── pdf/SKILL.md
│   ├── docx/SKILL.md
│   ├── pptx/SKILL.md
│   ├── xlsx/SKILL.md
│   └── html/SKILL.md
│
├── 🧪 tests/                         ← все тесты (370+)
│   ├── __init__.py
│   ├── test_esm.py
│   ├── test_truth_gate.py
│   ├── test_pipeline.py
│   ├── test_mhi.py
│   ├── test_hybrid_retriever.py
│   ├── test_adversarial.py
│   ├── test_server_integration.py
│   ├── test_causal_graph.py          ← 🆕 Patch 13
│   ├── test_understanding_layer.py   ← 🆕 Patch 14
│   └── test_affordance_mvp.py        ← 🆕 Variant C benchmark
│
├── 🗃️ migrations/                    ← SQLite схема
│   └── 008_add_relations.sql         ← 🆕 Causal Graph + Living Context
│
├── 📊 benchmarks/
│   └── bench_pipeline.py
│
├── ⚙️ scripts/
│   └── sync_docs.py                  ← синхронизация версий в доках
│
├── 📚 docs/
│   ├── INVARIANTS.md
│   ├── LIMITATIONS.md
│   ├── DEPLOY.md
│   └── AUDIT_FIXES.md
│
├── 💾 data/                          ← SQLite базы (в .gitignore!)
│   ├── .gitkeep
│   ├── velantrim.db                  ← создаётся при первом запуске
│   ├── velantrim_ngram.db
│   ├── core_blocks.db
│   └── notebook.db
│
├── 📄 server.py                      ← FastAPI приложение
├── 📄 pyproject.toml                 ← версия + зависимости
├── 📄 .env                           ← ТВОИ настройки (не в git!)
├── 📄 .env.example                   ← шаблон настроек
├── 📄 .gitignore
└── 📄 README.md
```

---

## 3. 🔧 Установка по шагам

### Шаг 1 — Создай папку проекта

```bash
mkdir velantrim-project
cd velantrim-project
```

### Шаг 2 — Создай виртуальное окружение

```bash
python -m venv venv
```

**Активация:**

```bash
# Windows (CMD):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# macOS / Linux:
source venv/bin/activate
```

После активации в начале строки появится `(venv)`.

> ⚠️ **Важно:** всегда активируй venv перед работой с проектом!

### Шаг 3 — Обнови pip и установи базовые зависимости

```bash
python -m pip install --upgrade pip

pip install fastapi "uvicorn[standard]" python-dotenv pydantic httpx

pip install pytest pytest-asyncio pytest-cov
```

### Шаг 4 — Создай папку для данных

```bash
mkdir data
```

---

## 4. 📦 Применение архивов

Архивы применяются **в строгом порядке** — каждый следующий добавляет новые файлы поверх предыдущего.

```
ПОРЯДОК ПРИМЕНЕНИЯ:

1️⃣  velantrim_FULL_v8.4.0.zip          ← Основа (аудит-фиксы)
2️⃣  velantrim_file_parsers_v2.zip      ← Парсеры (Этап 1)
3️⃣  velantrim_file_generators_v1.zip   ← Генераторы (Этап 2)
4️⃣  velantrim_etap3_integration.zip    ← Интеграция (Этап 3)
5️⃣  velantrim_patch13.zip              ← Understanding Layer (Patch 13+14)
```

**Команды для распаковки:**

```bash
# macOS / Linux:
unzip velantrim_FULL_v8.4.0.zip
unzip -o velantrim_file_parsers_v2.zip
unzip -o velantrim_file_generators_v1.zip
unzip -o velantrim_etap3_integration.zip
unzip -o velantrim_patch13.zip

# Windows — правый клик на файле → "Извлечь всё"
# Или установи 7-Zip и используй командную строку:
7z x velantrim_FULL_v8.4.0.zip
7z x velantrim_file_parsers_v2.zip
# ... и т.д.
```

> ⚠️ Флаг `-o` означает "перезаписывать существующие файлы" — это нормально.

**Проверь что всё на месте:**

```bash
ls core/
# Должны быть: memory.py pipeline.py truth_gate.py causal_graph.py ...

ls core/file_parsers/
# Должны быть: base.py file_ingester.py pdf_parser.py ...

ls core/file_generators/
# Должны быть: base.py file_exporter.py pdf_generator.py ...

ls migrations/
# Должны быть: 008_add_relations.sql
```

---

## 5. ⚙️ Конфигурация (.env)

```bash
# Скопируй шаблон
cp .env.example .env

# Открой в редакторе:
# macOS:
open -e .env

# Windows:
notepad .env

# Linux:
nano .env
```

**Минимально необходимые настройки:**

```env
# ════════════════════════════════════════
# ОБЯЗАТЕЛЬНО — без этого сервер не стартует
# ════════════════════════════════════════

# Сгенерируй командой:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
VELANTRIM_API_KEY=вставь_сгенерированный_ключ_сюда

# Пути к базам данных (можно оставить дефолтные)
VELANTRIM_DB_PATH=./data/velantrim.db
VELANTRIM_NGRAM_DB=./data/velantrim_ngram.db

# ════════════════════════════════════════
# ОПЦИОНАЛЬНО
# ════════════════════════════════════════

# none = заглушка (для разработки), anthropic = реальный Claude
LLM_PROVIDER=none

# Ключ если LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=

# Фоновый воркер
SLEEP_WORKER_ENABLED=true

# Разрешённые CORS домены (пусто = CORS отключён)
CORS_ORIGINS=

# Порт сервера
PORT=8000
```

**Генерация ключа:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Вывод: что-то вроде: X4mK9p2vQ8wR3nL7jH5tB1cE6yA0sN-dF
# Это и есть твой API ключ — скопируй в .env
```

---

## 6. 🗃️ SQLite миграции

Добавляют новые таблицы для Causal Graph и Living Context:

```bash
python -c "
import sqlite3, os

db_path = os.getenv('VELANTRIM_DB_PATH', './data/velantrim.db')
print(f'Применяю миграцию к: {db_path}')

with open('migrations/008_add_relations.sql') as f:
    sql = f.read()

conn = sqlite3.connect(db_path)
conn.executescript(sql)
conn.close()
print('✅ Миграция применена!')
"
```

**Проверка что таблицы созданы:**

```bash
python -c "
import sqlite3
conn = sqlite3.connect('./data/velantrim.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\").fetchall()
for t in tables:
    print(' ✓', t[0])
"
```

Должны увидеть:

```
 ✓ canonical_affordances
 ✓ fact_affordance_tokens
 ✓ fact_affordances
 ✓ fact_living_context
 ✓ facts
 ✓ relation_paths
 ✓ relations
 ✓ ... (остальные таблицы)
```

---

## 7. 🧪 Запуск тестов

### Быстрая проверка (без внешних зависимостей)

```bash
pytest tests/test_causal_graph.py -v
```

Ожидаемый вывод:
```
tests/test_causal_graph.py::TestRelationCRUD::test_add_simple_relation PASSED
tests/test_causal_graph.py::TestRelationCRUD::test_invalid_type_rejected PASSED
...
45 passed in 0.32s
```

### MVP Benchmark (Variant C) — показывает реальные числа

```bash
pytest tests/test_affordance_mvp.py -v -s
```

```
📊 Variant C MVP Benchmark Results
══════════════════════════════════
  Precision:  0.xxx
  Recall:     0.xxx
  F1:         0.xxx
  Coverage:   xx.x%
  Go/No-Go: 🟡 ХОРОШО — можно расширять
══════════════════════════════════
```

### Все тесты

```bash
# Базовые (быстро, без Docker, без LLM)
pytest tests/ -v -m "not e2e" --ignore=tests/test_knowledge_ingester.py

# С покрытием
pytest tests/ -v --cov=core --cov-report=term-missing

# Конкретный модуль
pytest tests/test_understanding_layer.py -v
pytest tests/test_truth_gate.py -v
pytest tests/test_mhi.py -v
```

### Ожидаемые результаты

```
370+ passed   ← всё зелёное
1 xfailed     ← честный: NLI naive detector (известное ограничение)
```

---

## 8. 🌐 Запуск сервера

```bash
# Для разработки (с автоперезапуском при изменении файлов)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Для production (без --reload)
uvicorn server:app --host 0.0.0.0 --port 8000
```

Успешный запуск выглядит так:

```
INFO:     ✅ SleepTimeWorker started
INFO:     ✅ NGramIndex initialized (shared singleton)
INFO:     ✅ HybridRetriever ready
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

> ⚠️ Если видишь `RuntimeError: VELANTRIM_API_KEY is not set` — ты не заполнил .env

---

## 9. ✅ Проверка работы

### 1. Открой браузер

```
http://localhost:8000/health
```

Должен увидеть:
```json
{
  "status": "healthy",
  "version": "8.5.0"
}
```

### 2. Swagger UI (интерактивная документация)

```
http://localhost:8000/docs
```

Здесь можно тестировать все endpoints прямо в браузере без curl.

### 3. Проверь через curl

```bash
# Замени YOUR_KEY на ключ из .env

# Загрузить факт
curl -X POST http://localhost:8000/ingest/text \
  -H "X-Api-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Вода кипит при 100 градусах Цельсия при атмосферном давлении",
    "source": "physics",
    "confidence": 0.99
  }'

# Задать вопрос
curl -X POST http://localhost:8000/query \
  -H "X-Api-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "при какой температуре кипит вода?"}'

# Проверить здоровье памяти
curl http://localhost:8000/health
```

### 4. Попробуй Causal Graph

```python
# test_live.py — запусти этот скрипт для проверки
import sqlite3
from core.causal_graph import CausalGraph

# Открываем БД
conn = sqlite3.connect("./data/velantrim.db")
conn.execute("PRAGMA foreign_keys = ON")

graph = CausalGraph(conn)

# Смотрим статистику графа
stats = graph.stats()
print("📊 Статистика графа:", stats)

# Если уже есть факты в памяти — можно посмотреть связи
# graph.add_relation("fact_id_1", "fact_id_2", "causes", 0.9)
# chain = graph.causal_chain("fact_id_1")
# print("⛓️ Цепочки:", chain)

conn.close()
```

```bash
python test_live.py
```

---

## 10. 🛠️ Полезные команды

### Версия проекта

```bash
python -c "from core import __version__; print(__version__)"
```

### Синхронизация документов (обновить цифры в README и INVARIANTS)

```bash
python scripts/sync_docs.py          # применить
python scripts/sync_docs.py --check  # только проверить (для CI)
python scripts/sync_docs.py --dry-run # показать что изменится
```

### Запустить MHI benchmark

```bash
python benchmarks/bench_pipeline.py
```

### Экспорт фактов через API

```bash
# Все Validated факты → PDF
curl -X POST http://localhost:8000/export/knowledge_base \
  -H "X-Api-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"format": "pdf", "theme": "velantrim", "group_by": "source"}' \
  -o knowledge_base.pdf

# MHI dashboard → HTML
curl -X POST "http://localhost:8000/export/mhi?format=html&theme=velantrim" \
  -H "X-Api-Key: YOUR_KEY" \
  -o mhi_dashboard.html
```

### Использование FileIngester напрямую

```python
from core.file_parsers import FileIngester

ingester = FileIngester()

# Парсинг одного файла
result = ingester.ingest("документ.pdf")
print(f"Тип: {result.file_type}")
print(f"Слов: {result.word_count}")
print(f"Уверенность: {result.to_fact_dict()['confidence']}")

# Парсинг директории (параллельно)
results = ingester.ingest_directory(
    "/docs",
    workers=4,
    recursive=True,
    progress=lambda done, total, f: print(f"[{done}/{total}] {f}"),
)
print(f"Обработано: {ingester.get_stats()}")
```

### Генерация документов

```python
from core.file_generators import FileExporter
from core.velantrim_reports import generate_mhi_report

# MHI отчёт (нужен реальный MHI объект)
# spec = generate_mhi_report(mhi, theme="velantrim")
# FileExporter().export(spec, "reports/mhi.pdf")

# Или напрямую из фактов
facts = [
    {"fact_id": "f1", "claim": "Земля вращается вокруг Солнца",
     "confidence": 0.999, "epistemic_state": "ImmutableCore", "source": "astronomy"},
]
FileExporter().export_facts(facts, "facts_report.pdf", theme="velantrim")
```

---

## 11. 🔥 Частые проблемы

### ❌ `ModuleNotFoundError: No module named 'core'`

**Причина:** запускаешь из неправильной папки.

```bash
# Убедись что ты в корне проекта (там где лежит server.py)
ls server.py   # должен существовать

# Запускай pytest из корня
pytest tests/ -v
# НЕ из: cd tests && pytest
```

### ❌ `RuntimeError: VELANTRIM_API_KEY is not set`

```bash
# Сгенерируй ключ
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Добавь в .env:
# VELANTRIM_API_KEY=полученный_ключ
```

### ❌ `ImportError: No module named 'fastapi'`

```bash
# venv не активирован или зависимости не установлены
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

pip install fastapi uvicorn
```

### ❌ `sqlite3.OperationalError: no such table: relations`

```bash
# Миграция не применена
python -c "
import sqlite3
with open('migrations/008_add_relations.sql') as f:
    sql = f.read()
conn = sqlite3.connect('./data/velantrim.db')
conn.executescript(sql)
conn.close()
print('✅ OK')
"
```

### ❌ `SleepTimeWorker не стартует` (все `/agent/*` → 503)

Это был баг v8.4.0 — закрыт в аудит-фиксе. Если возникает:

```bash
# Проверь что используешь v8.4.0+
python -c "from core import __version__; print(__version__)"
# Должно быть 8.4.0 или новее
```

### ❌ `pytest: command not found`

```bash
# Активируй venv и установи pytest
source venv/bin/activate
pip install pytest
```

### ❌ Тест падает с `KeyError: 'fact_id'`

```bash
# БД не инициализирована. Стартуй сервер один раз:
uvicorn server:app --port 8000
# Дождись INFO об успешном старте
# Останови Ctrl+C
# Запусти тесты
pytest tests/ -v
```

### ❌ `WARNING: CORS` в браузере

```env
# В .env добавь свой frontend URL
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### ❌ Медленный первый запрос (1-2 секунды)

Это нормально — HybridRetriever грузит embedding модель. После первого запроса модель кешируется в singleton и последующие запросы быстрые (~20ms).

---

## 12. 📦 Опциональные зависимости

Все зависимости опциональные — система работает с любым подмножеством, автоматически выбирая лучший доступный метод.

### Для лучших результатов парсинга (Этап 1)

```bash
# PDF — лучший инструмент 2026
pip install marker-pdf          # Marker (Surya OCR)
pip install pymupdf             # PyMuPDF (быстрый fallback)

# Аудио транскрипция
pip install faster-whisper      # 4× быстрее openai-whisper

# OCR изображений
pip install pytesseract Pillow
# + системный Tesseract:
# Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-rus
# macOS:  brew install tesseract tesseract-lang
```

### Для генерации файлов (Этап 2)

```bash
pip install reportlab            # PDF
pip install python-docx          # Word
pip install python-pptx          # PowerPoint
pip install openpyxl             # Excel
```

### Для Understanding Layer (Patch 13+14)

```bash
# Лемматизация русского языка (улучшает F1 AffordanceLinker на ~10-15%)
pip install pymorphy2

# После установки — перезапусти benchmark:
pytest tests/test_affordance_mvp.py -v -s
```

### Для конвертации форматов через pandoc (Этап 2)

```bash
pip install pypandoc

# + системный pandoc:
# Ubuntu: sudo apt install pandoc
# macOS:  brew install pandoc
# Windows: https://pandoc.org/installing.html
```

### Для EPUB книг (парсинг и генерация)

```bash
pip install ebooklib beautifulsoup4  # парсинг
```

### Для архивов

```bash
pip install py7zr    # .7z файлы
pip install rarfile  # .rar файлы
# + системный unrar на Linux: sudo apt install unrar
```

### Полная установка всего (рекомендуется для production)

```bash
pip install -r core/file_parsers/requirements_parsers.txt
pip install -r core/file_generators/requirements_generators.txt
```

---

## 🔱 Быстрый старт (TL;DR)

```bash
# 1. Создай папку и войди в неё
mkdir velantrim && cd velantrim

# 2. Виртуальное окружение
python -m venv venv && source venv/bin/activate

# 3. Зависимости
pip install fastapi "uvicorn[standard]" python-dotenv pydantic pytest

# 4. Распакуй архивы (в этом порядке!)
unzip velantrim_FULL_v8.4.0.zip
unzip -o velantrim_file_parsers_v2.zip
unzip -o velantrim_file_generators_v1.zip
unzip -o velantrim_etap3_integration.zip
unzip -o velantrim_patch13.zip

# 5. Настрой .env
cp .env.example .env
python -c "import secrets; print('VELANTRIM_API_KEY='+secrets.token_urlsafe(32))" >> .env

# 6. Создай папку данных
mkdir -p data

# 7. Применить миграцию
python -c "
import sqlite3
conn = sqlite3.connect('./data/velantrim.db')
conn.executescript(open('migrations/008_add_relations.sql').read())
conn.close(); print('OK')
"

# 8. Запусти тесты
pytest tests/test_causal_graph.py tests/test_understanding_layer.py -v

# 9. Запусти сервер
uvicorn server:app --port 8000 --reload

# 10. Открой в браузере
# http://localhost:8000/health
# http://localhost:8000/docs
```

---

> **Velantrim ExoCortex** · v8.5.0 · May 2026
> *Если что-то пошло не так — пришли вывод ошибки, решим за 2 строки* 🔱
