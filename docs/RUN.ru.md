# 🚀 Пошаговое руководство по запуску Velantrim на своём ПК

> Написано специально для тебя — предполагаем что Python уже есть.
> Читай последовательно, не пропускай шаги.

---

## 📋 Что понадобится

- **Python 3.11 или новее** (проверь: `python --version`)
- **Git** (для клонирования репозитория)
- **Windows/macOS/Linux** — всё работает везде

---

## Шаг 1 — Проверь Python

```bash
python --version
# Должно быть: Python 3.11.x или 3.12.x или 3.13.x
# Если меньше 3.11 → скачай с python.org
```

---

## Шаг 2 — Распакуй архивы в нужном порядке

У тебя есть несколько архивов. Применяй в таком порядке:

```
1. velantrim_FULL_v8.4.0.zip         ← основа (аудит-фиксы)
2. velantrim_file_parsers_v2.zip     ← парсеры файлов
3. velantrim_file_generators_v1.zip  ← генераторы файлов
4. velantrim_etap3_integration.zip   ← интеграция
5. velantrim_patch13.zip             ← Causal Graph + Living Context (этот архив)
```

**Как распаковать каждый:**

```bash
# Создай папку проекта
mkdir velantrim_project
cd velantrim_project

# Распакуй первый архив
unzip ~/Downloads/velantrim_FULL_v8.4.0.zip

# Посмотри что внутри
ls

# Распакуй остальные поверх (они добавляют новые файлы)
unzip -o ~/Downloads/velantrim_file_parsers_v2.zip
unzip -o ~/Downloads/velantrim_file_generators_v1.zip
unzip -o ~/Downloads/velantrim_etap3_integration.zip
unzip -o ~/Downloads/velantrim_patch13.zip
```

**На Windows** используй правый клик → "Извлечь всё", или установи 7-Zip.

---

## Шаг 3 — Создай виртуальное окружение

Виртуальное окружение — это изолированное место для зависимостей.
Не устанавливай пакеты в глобальный Python — это плохая практика.

```bash
# В папке проекта
python -m venv venv

# Активация:
# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

# Должно появиться (venv) в начале строки терминала
```

---

## Шаг 4 — Установи базовые зависимости

```bash
# Сначала обнови pip
python -m pip install --upgrade pip

# Установи основное (всегда нужно)
pip install fastapi "uvicorn[standard]" python-dotenv pydantic httpx

# Тесты
pip install pytest pytest-asyncio pytest-cov
```

---

## Шаг 5 — Настрой переменные окружения

```bash
# Скопируй шаблон
cp .env.example .env

# Открой .env в редакторе и заполни:
# На Windows:
notepad .env

# На macOS:
open -e .env

# На Linux:
nano .env
```

**Что ОБЯЗАТЕЛЬНО заполнить в .env:**

```env
# Сгенерируй ключ командой:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
VELANTRIM_API_KEY=вставь_сюда_ключ

# Пути к базам данных (можно оставить дефолтные)
VELANTRIM_DB_PATH=./data/velantrim.db
VELANTRIM_NGRAM_DB=./data/velantrim_ngram.db

# LLM провайдер (none = заглушка для разработки)
LLM_PROVIDER=none
```

---

## Шаг 6 — Создай папку для данных

```bash
mkdir -p data
```

---

## Шаг 7 — Примени SQLite миграцию

Это добавляет новые таблицы в базу данных для Causal Graph и Living Context:

```bash
# Если база ещё не существует — она создастся автоматически при первом запуске.
# Если уже есть — применяем миграцию:

python -c "
import sqlite3
import os

db_path = os.getenv('VELANTRIM_DB_PATH', './data/velantrim.db')
with open('migrations/008_add_relations.sql') as f:
    sql = f.read()
conn = sqlite3.connect(db_path)
conn.executescript(sql)
conn.close()
print('Миграция применена успешно!')
"
```

---

## Шаг 8 — Запусти базовые тесты

```bash
# Только тесты без внешних зависимостей (всегда должны работать)
pytest tests/test_causal_graph.py -v

# Тесты Understanding Layer
pytest tests/test_understanding_layer.py -v

# MVP benchmark с отчётом
pytest tests/test_affordance_mvp.py -v -s
```

**Ожидаемый результат:**
```
tests/test_causal_graph.py ...............     ← 45+ тестов
tests/test_understanding_layer.py ..........  ← 11 тестов
tests/test_affordance_mvp.py ..........        ← 10 тестов

╔══════════════════════════════════════╗
║  📊 MVP Benchmark Results            ║
║  Precision: 0.xxx                    ║
║  Recall:    0.xxx                    ║
║  F1:        0.xxx                    ║
║  Go/No-Go:  🟡 ...                  ║
╚══════════════════════════════════════╝
```

---

## Шаг 9 — Запусти все тесты

```bash
# Все тесты проекта
pytest tests/ -v

# С покрытием
pytest tests/ -v --cov=core --cov-report=term-missing

# Только быстрые (без e2e)
pytest tests/ -v -m "not e2e"
```

---

## Шаг 10 — Запусти сервер

```bash
# Запуск FastAPI сервера
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Должно появиться:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Шаг 11 — Проверь что всё работает

Открой браузер и перейди по адресу:

```
http://localhost:8000/health
```

Должен увидеть что-то вроде:
```json
{
  "status": "healthy",
  "version": "8.5.0",
  ...
}
```

**Проверь API документацию:**
```
http://localhost:8000/docs
```

Там интерактивный интерфейс Swagger — можно тестировать все endpoints прямо в браузере.

---

## Шаг 12 — Попробуй Causal Graph через API

В Swagger (http://localhost:8000/docs) найди endpoint и попробуй:

```bash
# Через curl
curl -X POST http://localhost:8000/facts \
  -H "X-Api-Key: ВАШ_КЛЮЧ" \
  -H "Content-Type: application/json" \
  -d '{"fact_id": "f1", "claim": "Вода нужна для жизни", "confidence": 0.99}'

curl -X POST http://localhost:8000/facts \
  -H "X-Api-Key: ВАШ_КЛЮЧ" \
  -H "Content-Type: application/json" \
  -d '{"fact_id": "f2", "claim": "Жизнь существует на Земле", "confidence": 0.99}'

# Добавить каузальную связь
curl -X POST http://localhost:8000/relations \
  -H "X-Api-Key: ВАШ_КЛЮЧ" \
  -H "Content-Type: application/json" \
  -d '{
    "from_fact_id": "f1",
    "to_fact_id": "f2",
    "relation_type": "enables",
    "confidence": 0.95
  }'
```

---

## 🛠️ Частые проблемы и решения

### "ModuleNotFoundError: No module named 'core'"

```bash
# Убедись что ты в корневой папке проекта
ls core/  # должен видеть файлы

# Запускай из корня
pytest tests/ -v
# НЕ из подпапки tests/
```

### "ImportError: No module named 'fastapi'"

```bash
# Виртуальное окружение не активировано
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Или зависимости не установлены
pip install fastapi uvicorn
```

### "RuntimeError: VELANTRIM_API_KEY is not set"

```bash
# Ключ не задан в .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Скопируй результат в .env: VELANTRIM_API_KEY=...
```

### "sqlite3.OperationalError: no such table: relations"

```bash
# Миграция не применена
python -c "
import sqlite3
with open('migrations/008_add_relations.sql') as f:
    sql = f.read()
conn = sqlite3.connect('./data/velantrim.db')
conn.executescript(sql)
conn.close()
print('OK')
"
```

### "pytest: command not found"

```bash
# Убедись что venv активирован, затем:
pip install pytest
```

### Тест падает с "fact_id not found"

```bash
# Базовая БД не инициализирована. Запусти сервер один раз:
uvicorn server:app --port 8000
# Он создаст таблицы при старте.
# Потом останови (Ctrl+C) и запусти тесты.
```

---

## 📦 Установка опциональных зависимостей

### Для улучшения парсера (Этап 1):

```bash
# PDF
pip install pymupdf           # PyMuPDF — быстрый fallback
pip install marker-pdf        # Лучший PDF парсер 2026

# Аудио
pip install faster-whisper    # 4× быстрее openai-whisper

# OCR
pip install pytesseract       # + нужен системный tesseract
# Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-rus
# macOS:  brew install tesseract tesseract-lang
```

### Для улучшения AffordanceLinker (Variant C):

```bash
# Лемматизация русского языка
pip install pymorphy2

# После установки — перезапусти benchmark тест:
pytest tests/test_affordance_mvp.py -v -s
# F1 должен вырасти на 5-15%
```

### Для генераторов файлов (Этап 2):

```bash
pip install reportlab         # PDF
pip install python-docx       # Word
pip install python-pptx       # PowerPoint
pip install openpyxl          # Excel
```

---

## 🔱 Структура проекта (итог)

```
velantrim_project/
│
├── core/                       ← Ядро Velantrim
│   ├── memory.py               ← ESM, bi-temporal
│   ├── pipeline.py             ← Оркестратор запросов
│   ├── truth_gate.py           ← TruthGate (v8.4.4 с NLI)
│   ├── mhi.py                  ← Memory Health Index
│   ├── causal_graph.py         ← 🆕 Causal Graph (Patch 13)
│   ├── living_context.py       ← 🆕 Living Context (Patch 14)
│   ├── understanding_layer.py  ← 🆕 Understanding Layer
│   ├── affordance_linker.py    ← 🆕 Variant C MVP
│   ├── file_parsers/           ← Парсеры 60+ форматов
│   ├── file_generators/        ← Генераторы PDF/DOCX/PPTX/...
│   └── velantrim_reports/      ← Готовые шаблоны отчётов
│
├── tests/                      ← Тесты
│   ├── test_causal_graph.py    ← 🆕 45+ тестов Causal Graph
│   ├── test_understanding_layer.py ← 🆕 11 тестов
│   ├── test_affordance_mvp.py  ← 🆕 10 тестов + benchmark
│   └── ... остальные тесты
│
├── migrations/
│   └── 008_add_relations.sql   ← 🆕 SQLite миграция
│
├── data/                       ← SQLite базы (в .gitignore)
│   ├── velantrim.db
│   └── velantrim_ngram.db
│
├── server.py                   ← FastAPI сервер
├── .env                        ← Твои настройки (в .gitignore)
├── .env.example                ← Шаблон
└── pyproject.toml              ← Зависимости
```

---

## 💬 Если что-то пошло не так

Скопируй вывод ошибки и пришли мне в чат. Обычно это:
1. Ошибка импорта → не установлена зависимость
2. Ошибка SQLite → не применена миграция
3. Ошибка API key → не заполнен .env

Большинство проблем решается в 2 строки. 🔱
