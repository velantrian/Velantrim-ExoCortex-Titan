# 🔱 Velantrim Этап 3 — Integration Layer

> Этап 3 связывает file_parsers (Этап 1) и file_generators (Этап 2) с ядром Velantrim:
> готовые шаблоны отчётов, HTTP endpoints, тесты и skills documentation.

---

## 📦 Что внутри

```
velantrim_etap3_integration/
│
├── 📂 skills/                          ← Best practices documentation (как у Claude)
│   ├── pdf/SKILL.md                    ← Когда использовать PDF, темы, шаблоны
│   ├── docx/SKILL.md                   ← DOCX vs PDF, шаблоны, нюансы
│   ├── pptx/SKILL.md                   ← Презентации: правила 6×6, pitch deck
│   ├── xlsx/SKILL.md                   ← Excel: листы, conditional formatting
│   └── html/SKILL.md                   ← HTML standalone, email-friendly
│
├── 🎯 core/velantrim_reports/          ← Готовые шаблоны отчётов
│   ├── __init__.py                     ← Публичный API: 4 generator-функции
│   ├── mhi_report.py                   ← generate_mhi_report() — MHI dashboard
│   ├── truthgate_report.py             ← generate_truthgate_audit() — TG audit
│   ├── knowledge_base.py               ← generate_knowledge_base() — KB export
│   └── sprint_review.py                ← generate_sprint_review() — спринт-отчёт
│
├── 🌐 server_patch/                    ← FastAPI endpoints
│   └── export_endpoints.py             ← POST /export/{facts,mhi,truthgate,kb}
│                                           GET /export/{formats,themes}
│
└── 🧪 tests/                           ← Pytest интеграционные тесты
    ├── test_file_generators/
    │   └── test_basic.py               ← 9 классов, 25+ тестов
    └── test_file_parsers/
        └── test_basic.py               ← 6 классов, 20+ тестов
```

---

## 🚀 Как использовать

### 1. Готовые отчёты — одной строкой

```python
from core.velantrim_reports import generate_mhi_report
from core.file_generators import FileExporter
from core.mhi import MHICalculator

# Генерируем MHI dashboard
mhi = MHICalculator(store).calculate()
spec = generate_mhi_report(mhi)
FileExporter().export(spec, "reports/mhi.pdf")

# Или сразу в несколько форматов
FileExporter().export_multi(spec, "reports/mhi", formats=["pdf", "html", "docx"])
```

### 2. HTTP API — экспорт через REST

```bash
# Список форматов
curl http://localhost:8000/export/formats

# Список тем
curl http://localhost:8000/export/themes

# Экспорт MHI dashboard в PDF
curl -X POST http://localhost:8000/export/mhi?format=pdf \
  -H "X-Api-Key: $API_KEY" \
  -o mhi.pdf

# Экспорт фактов в DOCX
curl -X POST http://localhost:8000/export/facts \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "facts": [{"fact_id":"f1","claim":"...","confidence":0.9,
               "epistemic_state":"Validated","source":"test"}],
    "format": "docx",
    "theme": "business",
    "title": "Q1 Report"
  }' \
  -o report.docx

# Экспорт TruthGate аудита
curl -X POST http://localhost:8000/export/truthgate \
  -H "X-Api-Key: $API_KEY" \
  -d '{"format":"pdf","theme":"scientific","mode":"BALANCED"}' \
  -o audit.pdf

# Knowledge base в EPUB
curl -X POST http://localhost:8000/export/knowledge_base \
  -H "X-Api-Key: $API_KEY" \
  -d '{"format":"epub","group_by":"source","title":"Velantrim KB"}' \
  -o kb.epub
```

### 3. Skills documentation — для разработчиков

Файлы `skills/<format>/SKILL.md` — это **best practices** для каждого формата. Когда разработчик собирается генерировать PDF/DOCX/PPTX/XLSX/HTML, он читает соответствующий SKILL.md первым.

Это та же паттерн, что я (Claude) использую для своих skills.

---

## 🔧 Установка

### Шаг 1: распаковать поверх существующего проекта

```bash
unzip velantrim_etap3_integration.zip -d /path/to/velantrim/
```

Это положит файлы в:
- `core/velantrim_reports/` — новая папка
- `server_patch/` — рядом с server.py
- `skills/` — в корне проекта
- `tests/test_file_generators/` и `tests/test_file_parsers/` — добавится к тестам

### Шаг 2: подключить export endpoints к server.py

В `server.py` добавь перед `if __name__ == "__main__"`:

```python
from server_patch.export_endpoints import register_export_endpoints
register_export_endpoints(app, require_api_key=require_api_key)
```

### Шаг 3: запустить тесты

```bash
# Только Этап 3
pytest tests/test_file_generators/ tests/test_file_parsers/ -v

# Все тесты Velantrim
pytest tests/ -v
```

Зависимости опциональные — тесты используют `pytest.importorskip`, поэтому пропускаются если конкретная библиотека не установлена.

---

## 📋 API endpoints — справочник

| Endpoint | Метод | Назначение |
|---|---|---|
| `/export/formats` | GET | Список поддерживаемых форматов |
| `/export/themes` | GET | Список доступных тем оформления |
| `/export/facts` | POST | Экспорт произвольного списка фактов |
| `/export/mhi` | POST | MHI dashboard в выбранном формате |
| `/export/truthgate` | POST | TruthGate audit отчёт |
| `/export/knowledge_base` | POST | Полная книга validated фактов |

Все POST endpoints возвращают бинарный файл нужного формата с правильным `Content-Type`.

---

## 🎨 Готовые reports — что в каждом

### `generate_mhi_report(mhi_report, theme)`

MHI dashboard с:
- 🟢/🟡/🔴 hero callout со статусом
- Таблица компонентов (validated_ratio, freshness, precision, graph_coverage) с весами и вкладом
- Таблица SLO порогов (HEALTHY/DEGRADED/SAFE_MODE)
- Рекомендации
- Дополнительная статистика (total_facts, validated_count и т.д.)

### `generate_truthgate_audit(verdicts, theme)`

TruthGate отчёт с:
- ✅/⚠️/🚨 сводка (% прошедших)
- Таблица причин отклонения с распределением
- Таблица использованных режимов (PRECISION/BALANCED/EXPLORATION)
- Полная таблица всех вердиктов
- FactBlock'и для каждого отклонённого факта с причиной

### `generate_knowledge_base(facts, theme, group_by)`

Книга знаний с:
- Цитата-эпиграф
- Сводка (количество, средняя уверенность, источники)
- Таблица распределения по состояниям
- Группировка по `source` / `epistemic_state` / `confidence_band` / `none`
- FactBlock'и отсортированы по confidence (DESC) внутри группы

### `generate_sprint_review(sprint, format_hint)`

Sprint review с:
- 🎯 Цель спринта (CalloutBlock)
- ✅ Что доставили (FactBlock'и для PPTX, ListBlock для DOCX)
- 📊 Метрики (TableBlock с до/после/Δ)
- ⏰ Что перенесли (CalloutBlock + ListBlock)
- 💡 Уроки (CalloutBlock'и)
- 🚀 Следующий спринт

---

## 🔱 Главное достижение Этапа 3

После применения этого этапа:

1. **Velantrim умеет генерировать красивые документы из своей памяти** в 7 форматах.
2. **Эти документы доступны через HTTP API** — внешние системы могут запросить отчёт.
3. **Есть готовые шаблоны** для типичных задач (MHI, аудит, книга знаний, спринт).
4. **Skills documentation** объясняет разработчикам как выбирать формат и оформление.
5. **Тесты** покрывают парсер и генератор (50+ тестов).

Цикл замкнут: **файл → парсер → факт → память → генератор → файл**. 🔱

---

## 📊 Метрики

- **Файлов:** 14 (5 SKILL.md + 4 report templates + 1 server patch + 2 test файла + 2 __init__)
- **Строк кода:** ~2,500
- **Тестов:** 45+ (file_generators + file_parsers)
- **Поддерживаемых форматов экспорта:** 15+ через FileExporter
- **API endpoints:** 6

---

## 🎯 Что осталось (на будущее)

- **Sprint 2c:** реальная LLM генерация в `pipeline.generate_answer`
- **Patch 13:** Causal Graph (12 типов отношений)
- **Memory Evolution** (с entity resolution)
- **Public benchmarks** (LoCoMo, LongMemEval, MuSiQue)
- **Real charts в отчётах** (matplotlib/plotly интеграция)
- **TOC автоматический** для длинных PDF
- **Vision-LLM** в image_parser для better OCR
- **AST-парсер** для code files (вместо plain text)
