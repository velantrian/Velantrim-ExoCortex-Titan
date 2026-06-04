# 🔱 Velantrim ExoCortex — Архитектура системы

> **Версия:** v8.5.0 (Understanding Layer)
> **Дата:** Май 2026
> **Статус:** Production-ready core · Understanding Layer в разработке

---

## 🧭 Содержание

1. [Что такое Velantrim и зачем он нужен](#1-что-такое-velantrim-и-зачем-он-нужен)
2. [Философия проекта](#2-философия-проекта)
3. [Полная карта системы — Mindmap](#3-полная-карта-системы--mindmap)
4. [Архитектурные слои](#4-архитектурные-слои)
5. [Ядро системы — Core модули](#5-ядро-системы--core-модули)
6. [Модуль ввода — File Parsers](#6-модуль-ввода--file-parsers)
7. [Модуль вывода — File Generators](#7-модуль-вывода--file-generators)
8. [Слой понимания — Understanding Layer](#8-слой-понимания--understanding-layer)
9. [HTTP API — Server](#9-http-api--server)
10. [Тесты и качество](#10-тесты-и-качество)
11. [История версий и что было сделано](#11-история-версий-и-что-было-сделано)
12. [Roadmap](#12-roadmap)

---

## 1. 🎯 Что такое Velantrim и зачем он нужен

**Velantrim ExoCortex** — это долговременная память для AI-агентов.

Обычный AI-агент (ChatGPT, Claude и т.д.) **забывает** всё после окончания разговора. Velantrim решает эту проблему: он хранит факты, верифицирует их, следит за их жизненным циклом и выдаёт нужное в нужный момент.

### Аналогия

```
Обычный AI-агент:
  Разговор 1: "Меня зовут Иван, я люблю Python"
  Разговор 2: "Как тебя зовут?" → "Я не знаю"   ← Забыл

Velantrim + AI-агент:
  Разговор 1: "Меня зовут Иван, я люблю Python"
              → Velantrim сохраняет факт [имя=Иван, язык=Python]
  Разговор 2: "Как тебя зовут?" → "Иван"         ← Помнит
  Разговор 3: "Покажи примеры кода"
              → Velantrim находит: "Иван предпочитает Python"
              → Агент показывает примеры на Python  ← Понимает контекст
```

### Что делает Velantrim v8.5.0

| Способность | Описание |
|---|---|
| 🧠 **Хранит факты** | SQLite + L0 LRU кэш. Bi-temporal модель (когда знали, с каких пор правда) |
| 🔄 **ESM — жизненный цикл** | 8 состояний: Observed → Hypothesized → Validated → ImmutableCore → ... |
| 🛡️ **Верифицирует** | TruthGate с NLI cross-encoder. Противоречия — через ML, не keyword-matching |
| 📊 **Мониторит здоровье** | MHI (Memory Health Index): HEALTHY ≥ 0.60, DEGRADED 0.30–0.60, SAFE_MODE < 0.30 |
| 🔍 **Ищет** | HybridRetriever: BM25 + Dense embeddings + RRF ранжирование |
| 📁 **Читает файлы** | 60+ форматов: PDF, DOCX, PPTX, MP3, MP4, EPUB, ZIP, EML... |
| 📄 **Создаёт документы** | PDF, DOCX, PPTX, XLSX, HTML, EPUB, LaTeX из фактов памяти |
| 🧬 **Понимает связи** | Causal Graph: 12 типов отношений между фактами |
| 🌍 **Живой контекст** | Living Context: 8 измерений практического знания |

---

## 2. 🌟 Философия проекта

> *"Не копировать человеческий мозг — создать другую архитектуру интеллекта,  
> лучшую там, где биология ограничена."*

### Принципы

| Принцип | Что значит |
|---|---|
| **📊 Числа важнее мнений** | Каждый факт имеет confidence [0.0–1.0]. Решения основаны на числах, не на "кажется" |
| **🔍 xfail > "10/10 CERTIFIED"** | Честная документация. Если что-то не работает — так и написано |
| **🧬 Типизированные отношения** | Каузальный граф вместо ассоциативной памяти |
| **📝 Audit trail** | Каждое изменение логируется. 100% прозрачность решений |
| **⚡ Anti-bias by design** | Равномерное хранение, нет confirmation bias |
| **🎯 knowledge_status** | Система знает, чего она НЕ знает (known/inferred/hypothetical/unknown) |

### Чего Velantrim не делает (честно)

```
🔴 Нет эмбодимента (нет тела, нет проприоцепции)
🔴 Нет континуума сознания
🔴 Нет воли из гомеостаза
🔴 Pearl Level 3 (полный do-calculus) — не реализован
🔴 Distributed graph с консенсусом — V3
```

---

## 3. 🗺️ Полная карта системы — Mindmap

```
🔱 velantrim-exocortex-crystal/          ← корень проекта
│
│  ┌─── ВХОДНЫЕ ДАННЫЕ ────────────────────────────────────────────┐
│  │  Любой файл (60+ форматов)                                    │
│  │  PDF · DOCX · PPTX · MP3 · MP4 · EPUB · ZIP · EML · HTML ... │
│  └────────────────────────────────────────────────────────────────┘
│                           │
│                           ▼
├── 📂 core/                              ← ЯДРО СИСТЕМЫ
│   │
│   ├── 📁 file_parsers/    ───────── ЭТАП 1 ✅ (Файл → Факт)
│   │   ├── 🐍 base.py                   ABC + ParserRegistry + _ModelSingleton
│   │   ├── 🐍 file_ingester.py          Главный оркестратор
│   │   ├── 🐍 pdf_parser.py             Marker → Docling → PyMuPDF
│   │   ├── 🐍 docx_parser.py            Unstructured → python-docx
│   │   ├── 🐍 pptx_parser.py            python-pptx
│   │   ├── 🐍 text_parser.py            TXT/MD/JSON/YAML/код
│   │   ├── 🐍 csv_parser.py             CSV/XLSX/ODS
│   │   ├── 🐍 image_parser.py           OCR multilang + EXIF
│   │   ├── 🐍 audio_parser.py           faster-whisper (singleton)
│   │   ├── 🐍 video_parser.py           ffmpeg + AudioParser (DRY)
│   │   ├── 🐍 epub_parser.py            EPUB/MOBI/FB2
│   │   ├── 🐍 email_parser.py           EML/MSG/MBOX
│   │   ├── 🐍 html_parser.py            trafilatura → BS4
│   │   └── 🐍 archive_parser.py         ZIP/TAR/7Z/RAR + рекурсия
│   │
│   ├── 🐍 memory.py         ───────── ХРАНЕНИЕ (L0 + L1)
│   │   ├── store_fact()                 Записать факт в память
│   │   ├── get_fact()                   Прочитать факт
│   │   ├── transition_esm()             Перевести ESM-состояние
│   │   └── get_all_facts()              Выгрузить с фильтрами
│   │
│   ├── 🐍 pipeline.py       ───────── ОРКЕСТРАТОР ЗАПРОСОВ
│   │   └── run(query, mode)             Query → Retrieve → Guard → Answer
│   │
│   ├── 🐍 truth_gate.py     ───────── ВЕРИФИКАЦИЯ (v8.4.4 + NLI)
│   │   ├── TruthGate.evaluate()         Проверить факт
│   │   └── ContradictionRegistry        NLI cross-encoder детектор
│   │
│   ├── 🐍 mhi.py            ───────── HEALTH MONITOR
│   │   └── MHICalculator.calculate()    MHI = 0.30×val + 0.25×fresh + 0.25×prec + 0.20×graph
│   │
│   ├── 🐍 hybrid_retriever.py ─────── ПОИСК
│   │   └── BM25 + Dense embeddings + RRF (singleton после v8.4.0)
│   │
│   ├── 🐍 ngram_index.py    ───────── FTS5 PRE-FILTER
│   ├── 🐍 sleep_time_worker.py ─────── ФОНОВАЯ КОНСОЛИДАЦИЯ
│   ├── 🐍 embedding_registry.py ────── 17 моделей embeddings
│   ├── 🐍 storage.py        ───────── ABC SQLiteGraphStore
│   ├── 🐍 trace.py          ───────── PROVENANCE W3C PROV-O
│   │
│   ├── 🆕 📁 causal_graph.py ──────── PATCH 13 (Causal Graph)
│   │   ├── Relation dataclass           Ребро с 12 типами + knowledge_status
│   │   ├── ChainResult dataclass        Цепочка с min/product confidence
│   │   └── CausalGraph                  causes · prevents · requires · enables
│   │                                    implies · contradicts · generalizes
│   │                                    specializes · precedes · follows
│   │                                    composes · analogous_to
│   │
│   ├── 🆕 📁 living_context.py ─────── PATCH 14 (Living Context)
│   │   ├── LivingContext dataclass      8 измерений: WHERE/WHO/HOW/WHAT/FEEL/ROLE/TIME/DEEP
│   │   └── LivingContextStore          SQLite CRUD + affordance index
│   │
│   ├── 🆕 📁 understanding_layer.py ── PATCH 13+14 (объединение)
│   │   └── UnderstandingLayer          understand() · for_agent() · why() · predict_intervention()
│   │
│   ├── 🆕 📁 affordance_linker.py ──── VARIANT C MVP
│   │   ├── AffordanceLinker            rule-based + опц. pymorphy2
│   │   └── BenchmarkResult             P/R/F1 + Go/No-Go критерии
│   │
│   ├── 📁 file_generators/  ───────── ЭТАП 2 ✅ (Факт → Файл)
│   │   ├── 🐍 base.py                   10 блоков · 5 тем · GeneratorRegistry
│   │   ├── 🐍 file_exporter.py          Главный оркестратор
│   │   ├── 🐍 pdf_generator.py          ReportLab + темы
│   │   ├── 🐍 docx_generator.py         python-docx
│   │   ├── 🐍 pptx_generator.py         python-pptx (16:9)
│   │   ├── 🐍 xlsx_generator.py         openpyxl + conditional formatting
│   │   ├── 🐍 html_generator.py         standalone HTML5 + inline CSS
│   │   ├── 🐍 markdown_generator.py     GitHub-flavored + YAML frontmatter
│   │   └── 🐍 universal_generator.py    pypandoc → EPUB/LaTeX/RST/AsciiDoc
│   │
│   └── 📁 velantrim_reports/ ──────── ЭТАП 3 ✅ (Готовые шаблоны)
│       ├── 🐍 mhi_report.py             generate_mhi_report()
│       ├── 🐍 truthgate_report.py       generate_truthgate_audit()
│       ├── 🐍 knowledge_base.py         generate_knowledge_base()
│       └── 🐍 sprint_review.py          generate_sprint_review()
│
│  ┌─── ВЫХОДНЫЕ ДАННЫЕ ───────────────────────────────────────────┐
│  │  Любой формат (15+ форматов)                                  │
│  │  PDF · DOCX · PPTX · XLSX · HTML · EPUB · MD · LaTeX ...     │
│  └────────────────────────────────────────────────────────────────┘
│
├── 🌐 server.py              ← FastAPI HTTP сервер
│   ├── POST /ingest/text
│   ├── POST /query
│   ├── GET  /health
│   ├── POST /facts
│   ├── PATCH /facts/{id}/transition
│   └── + export endpoints (Этап 3)
│       ├── POST /export/facts
│       ├── POST /export/mhi
│       ├── POST /export/truthgate
│       └── POST /export/knowledge_base
│
├── 🌐 server_patch/          ← Дополнительные endpoints
│   └── export_endpoints.py
│
├── 🎯 skills/                ← Best practices документация
│   ├── pdf/SKILL.md
│   ├── docx/SKILL.md
│   ├── pptx/SKILL.md
│   ├── xlsx/SKILL.md
│   └── html/SKILL.md
│
├── 🧪 tests/                 ← 370+ тестов
│   ├── test_esm.py           36 тестов ESM
│   ├── test_truth_gate.py    20 тестов
│   ├── test_pipeline.py      19 тестов
│   ├── test_mhi.py           15 тестов
│   ├── test_hybrid_retriever.py  21 тест
│   ├── test_adversarial.py   49 тестов + regression
│   ├── test_server_integration.py  14 интеграционных
│   ├── 🆕 test_causal_graph.py     45+ тестов Patch 13
│   ├── 🆕 test_understanding_layer.py  17 тестов
│   └── 🆕 test_affordance_mvp.py   10 тестов + benchmark
│
├── 🗃️ migrations/            ← SQLite миграции
│   └── 008_add_relations.sql  Causal Graph + Living Context
│
├── 📊 benchmarks/
│   └── bench_pipeline.py
│
├── ⚙️ scripts/
│   └── sync_docs.py          Автосинхронизация версий в документах
│
├── 📚 docs/                  ← Документация проекта
│   ├── INVARIANTS.md         Инварианты системы (гарантии)
│   ├── LIMITATIONS.md        Честные ограничения
│   ├── DEPLOY.md             Деплой на VPS
│   └── AUDIT_FIXES.md        История исправлений
│
├── 💾 data/                  ← Runtime данные (в .gitignore)
│   ├── velantrim.db          SQLite: факты, ESM, audit
│   ├── velantrim_ngram.db    FTS5 индекс
│   ├── core_blocks.db        SleepTimeWorker
│   └── notebook.db           ResearchNotebook
│
├── 📄 server.py
├── 📄 pyproject.toml         ← Версия + зависимости
├── 📄 .env.example           ← Шаблон настроек
├── 📄 .gitignore
└── 📄 README.md
```

---

## 4. 🏗️ Архитектурные слои

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP API Layer                           │
│               FastAPI · REST · Pydantic schemas                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Understanding Layer          🆕 v8.5.0       │
│          Causal Graph · Living Context · AffordanceLinker       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Pipeline Orchestrator                        │
│      Query → NGram pre-filter → HybridRetriever → TruthGate    │
│                    → Guardian → LLM Answer                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────┬───────────────▼──────────┬────────────────────────┐
│  Memory    │     TruthGate + NLI      │   MHI Calculator       │
│  (L0 + L1) │   Contradiction detect   │   Health monitoring    │
└────────────┴──────────────────────────┴────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Storage Layer                                │
│             SQLite (L1) + LRU Cache (L0) + FSRS                │
│          facts · relations · fact_living_context · audit        │
└─────────────────────────────────────────────────────────────────┘
        ▲                                           │
        │                                           ▼
┌───────┴──────────┐                   ┌────────────────────────┐
│   File Parsers   │                   │   File Generators      │
│  60+ форматов    │                   │   15+ форматов         │
│  File → Fact     │                   │   Fact → File          │
└──────────────────┘                   └────────────────────────┘
```

### Поток данных (полный цикл)

```
📥 ВХОД                          💾 ХРАНЕНИЕ              📤 ВЫХОД
──────                           ──────────               ──────

любой файл                       ESM lifecycle            любой формат
(PDF/DOCX/MP3...)                 8 состояний              (PDF/DOCX/HTML...)
       │                               │                        ▲
       ▼                               ▼                        │
FileIngester                     store_fact()            GenerationSpec
       │                               │                        │
       ▼                               ▼                        │
ParseResult → to_fact_dict()    TruthGate.evaluate()    FileExporter
                                       │                        │
                               Validated / Rejected      велантрим_reports
                                       │                  шаблоны отчётов
                               HybridRetriever
                               (поиск по запросу)
```

---

## 5. 🧠 Ядро системы — Core модули

### ESM — Epistemic State Machine

8 состояний жизненного цикла факта:

```
Observed ──→ Hypothesized ──→ Supported ──→ Validated ──→ ImmutableCore
                                                │
                                    Contradicted ──→ Deprecated ──→ Collapsed
```

| Состояние | Значение |
|---|---|
| `Observed` | Просто записали — ещё не проверено |
| `Hypothesized` | Есть гипотеза, ищем подтверждение |
| `Supported` | Есть доказательства, но не окончательно |
| `Validated` | Проверено TruthGate, можно доверять |
| `ImmutableCore` | Аксиома системы — нельзя изменить без 2+ approvers |
| `Contradicted` | Противоречит другим фактам |
| `Deprecated` | Устарел, но история сохранена |
| `Collapsed` | Доказан ошибочным, удалён из активной памяти |

### TruthGate — верификатор

4 режима работы (CognitiveMode):

| Режим | Что делает | Когда использовать |
|---|---|---|
| `PRECISION` | Очень строгая проверка | Критичные решения |
| `BALANCED` | Баланс точность/полнота | Обычная работа |
| `EXPLORATION` | Допускает гипотезы | Исследование |
| `CREATIVE` | Максимум гибкости | Генерация идей |

**v8.4.4:** NLI cross-encoder `cross-encoder/nli-deberta-v3-small` заменил keyword-overlap детектор. 326 тестов.

### MHI — Memory Health Index

```
MHI = 0.30 × validated_ratio
    + 0.25 × freshness
    + 0.25 × retrieval_precision
    + 0.20 × graph_coverage

🟢 HEALTHY   ≥ 0.60  → норма
🟡 DEGRADED  0.30–0.60 → мониторинг / коррекция
🔴 SAFE_MODE < 0.30  → немедленный GC + alert
```

### HybridRetriever — поиск

```
Запрос
  │
  ├── NGram FTS5 pre-filter  (быстро, грубо)
  │         │
  │         ▼
  ├── BM25  (TF-IDF на токенах)     ─┐
  │                                   ├─ RRF ранжирование → Топ-K
  └── Dense (sentence-transformers)  ─┘

После v8.4.0: singleton — загрузка модели один раз, не на каждый запрос
```

---

## 6. 📁 Модуль ввода — File Parsers (Этап 1)

**Принцип:** каскад от лучшего к fallback. Если лучший инструмент недоступен — берём следующий.

### Поддерживаемые форматы (60+)

| Категория | Форматы | Primary инструмент 2026 |
|---|---|---|
| 📄 Документы | PDF, DOCX, PPTX, ODT | **Marker** → Docling → PyMuPDF |
| 📚 Книги | EPUB, MOBI, FB2, AZW | ebooklib |
| 📝 Текст/Код | TXT, MD, JSON, YAML, TOML, Python, JS... | native |
| 📊 Таблицы | CSV, XLSX, ODS | pandas + openpyxl |
| 📧 Email | EML, MSG, MBOX | email stdlib + extract-msg |
| 🌐 Web | HTML, XHTML, XML | trafilatura |
| 🖼️ Изображения | JPG, PNG, WebP, HEIC, TIFF | pytesseract + EXIF |
| 🎤 Аудио | MP3, WAV, FLAC, M4A, OPUS | **faster-whisper** |
| 🎬 Видео | MP4, MKV, MOV, AVI | ffmpeg → AudioParser |
| 📦 Архивы | ZIP, TAR, 7Z, RAR | рекурсивный обход |

### Ключевые улучшения v2 (Этап 1)

- 🆙 **PyPDF2 → PyMuPDF** — в 10-50× быстрее
- 🆕 **Marker** — лучший универсальный PDF парсер 2026 (Surya OCR)
- 🆙 **openai-whisper → faster-whisper** — 4× быстрее, 50% меньше RAM
- 🔧 **Lazy singleton** — Whisper грузится один раз за процесс
- 🔧 **SHA256 вместо BLAKE3** — нет внешних зависимостей
- 🔧 **MAX_FILE_SIZE** — защита от OOM на больших файлах
- 🔧 **ParserRegistry** — добавление нового формата = одна строка

### Архитектура ParseResult

```python
ParseResult:
  file_path          # откуда
  file_type          # тип файла
  extracted_text     # весь текст
  metadata           # метаданные файла
  structured_data    # структурированные данные (таблицы, слайды...)
  essence            # суть (через EssenceExtractorV5 если доступен)
  confidence         # 0.55–0.85 в зависимости от качества
  word_count         # количество слов
  page_count         # страниц (для PDF/PPTX)
  language           # определённый язык (для аудио)
  warnings           # предупреждения (partial extraction и т.п.)
  provenance         # W3C PROV-O: кем, когда, как создан
  
  to_fact_dict()     # → формат для store_fact()
```

---

## 7. 🎨 Модуль вывода — File Generators (Этап 2)

**Принцип:** зеркало парсера. Факты → GenerationSpec → красиво оформленный файл.

### Поддерживаемые форматы вывода

| Формат | Библиотека | Особенности |
|---|---|---|
| 📄 **PDF** | ReportLab | Header/footer, таблицы, callouts, FactCard |
| 📝 **DOCX** | python-docx | Темы, таблицы с цветами, tracked changes ready |
| 🎯 **PPTX** | python-pptx | 16:9 widescreen, заметки докладчика |
| 📊 **XLSX** | openpyxl | Multi-sheet, conditional formatting по confidence |
| 🌐 **HTML** | native | Standalone, inline CSS, responsive, print-friendly |
| 📋 **Markdown** | native | GitHub-flavored, YAML frontmatter |
| 🔄 **Другие** | pypandoc | EPUB, LaTeX, RST, AsciiDoc — через pandoc |

### 5 тем оформления

| Тема | Палитра | Когда |
|---|---|---|
| `clean` | Blue + slate | Универсальная (default) |
| `scientific` | Blue-800 + Times Roman | Академические документы |
| `business` | Slate-900 + orange-700 | Корпоративные отчёты |
| `dark` | Cyan + violet на тёмном | Презентации в тёмном зале |
| `velantrim` 🔱 | Cyan-600 + indigo + pink | Внутренние Velantrim отчёты |

### 10 типов контентных блоков

```
HeadingBlock    — заголовки h1-h6
ParagraphBlock  — параграф (normal/bold/italic/callout)
ListBlock       — список (ordered/unordered)
TableBlock      — таблица с caption
CodeBlock       — блок кода с подсветкой синтаксиса
ImageBlock      — изображение с caption
CalloutBlock    — info/success/warning/danger выделение
QuoteBlock      — цитата с автором
DividerBlock    — горизонтальная линия
FactBlock 🔱   — Velantrim-специфичный: claim + confidence + state + source
```

---

## 8. 🧬 Слой понимания — Understanding Layer (Patch 13+14)

Это переход от **памяти** к **пониманию**.

```
Память:      "Дерево растёт в лесу"
Понимание:   "Дерево → даёт тень (enables) → птицы гнездятся (inhabited_by)
                      → кислород (causes) → можно срубить (affords)
                      → дрова (becomes) → тепло (enables)"
```

### Essence Layer — future-work над Understanding Layer

`Essence Layer` уточняет, как система должна отвечать “по-человечески”:
не пересказывать всё найденное, а извлекать суть, связывать термины в цепочку
смысла и отдавать короткий вывод.

```text
много фактов / терминов / источников
  -> EssenceExtractor: главная мысль
  -> MeaningRoleTagger: причина / механизм / следствие / риск
  -> MeaningChainBuilder: A -> B -> C
  -> ShortAnswerComposer: короткий ответ
  -> WhyTrace: почему выбрана эта суть
```

Это не заменяет Causal Graph, Truth Gate или TRACE. Слой должен работать поверх
них и не скрывать неопределённость ради красивой фразы. Канон:
[`ESSENCE_LAYER_CANON.ru.md`](ESSENCE_LAYER_CANON.ru.md).

### Attention + Noetic Orchestration — P0-контракты над Understanding Layer

После аудита FQKVE/attention принято инженерное решение: не строить “новый
Transformer”, а добавить внешний прозрачный оркестратор над Retrieval, Graph,
FactsPack и TruthGate.

```text
GoalFrame
  -> ComputeController
  -> AttentionRouter
  -> FactsPack / TruthGate
  -> NoeticCore
  -> Answer + Trace
```

Новые P0-контракты:

| Модуль | Роль |
|---|---|
| `core/goal_frame.py` | определяет цель, риск, домен и стиль ответа |
| `core/attention_router.py` | прозрачно ранжирует факты по relevance/trust/graph/salience/risk |
| `core/compute_controller.py` | выбирает fast / normal / deep / verify / creative path |
| `core/noetic_core.py` | строит суть, causal chain, predictions как hypotheses, uncertainty |

`NoeticCore` не создаёт истину и не промоутит прогнозы в факты. Он только
маркирует: fact / inference / prediction / hypothesis / unknown. Канон:
[`ATTENTION_NOETIC_ORCHESTRATION.ru.md`](ATTENTION_NOETIC_ORCHESTRATION.ru.md).

### Patch 13 — Causal Graph (12 типов отношений)

| Тип | Описание | Пример |
|---|---|---|
| `causes` | A → B причина-следствие | Дождь → мокрая земля |
| `prevents` | A блокирует B | Зонт → нет промокания |
| `requires` | A нужен для B | Кислород → горение |
| `enables` | A делает возможным B | Транзистор → компьютер |
| `implies` | Из A логически следует B | Все люди смертны → Сократ смертен |
| `contradicts` | A исключает B (симметр.) | Жидкое ↔ твёрдое |
| `generalizes` | A — обобщение B | Птица ← воробей |
| `specializes` | A — частный случай B | Воробей → птица |
| `precedes` | A во времени перед B | Ужин → сон |
| `follows` | A после B | Сон → ужин |
| `composes` | A состоит из B | Машина → колесо |
| `analogous_to` | A структурно ≈ B (симметр.) | Атом ↔ Солнечная система |

**knowledge_status** — ключевое нововведение v2:

```
known       — проверено вручную / из надёжного источника
inferred    — выведено автоматически (AutoLinker, LLM)
hypothetical — предположение, ещё не проверено
unknown     — статус неизвестен
```

**Confidence по цепочке:**

```
A →(0.9)→ B →(0.7)→ C →(0.8)→ D

min_confidence     = 0.7    ← слабое звено (conservative, для critical decisions)
product_confidence = 0.504  ← перемножение (probabilistic, для ranking)
```

### Patch 14 — Living Context (8 измерений)

| # | Измерение | Дерево — пример |
|---|---|---|
| 1 | 📍 **WHERE** | лес, парк, двор, сад |
| 2 | 🤝 **WHO** | птицы (гнездятся), белки (хранят), люди (строят) |
| 3 | 🛠️ **HOW** | срубить, посадить, взобраться, измерить |
| 4 | 📦 **WHAT** | дрова, зола, смола, доски, плоды, семена |
| 5 | 💚 **FEEL** | живое: 0.95, сильное: 0.90, успокаивающее: 0.80 |
| 6 | 🌊 **ROLE** | держит почву, даёт кислород, регулирует воду |
| 7 | ⏰ **TIME** | растёт сотни лет, плодоносит ежегодно |
| 8 | 🧠 **DEEP** | 6CO₂+6H₂O→C₆H₁₂O₆+6O₂ (фотосинтез) |

### Variant C — MVP Benchmark

Go/No-Go критерии на реальных данных:

| F1 | Действие |
|---|---|
| ≥ 0.65 | 🟢 Отлично — переходим к Patch 14b Full (spaCy) |
| 0.50–0.65 | 🟡 Хорошо — можно расширять |
| 0.38–0.50 | 🟠 Минимум — добавить pymorphy2 |
| < 0.38 | 🔴 Ниже порога — нужен spaCy |

---

## 9. 🌐 HTTP API — Server

**Базовый URL:** `http://localhost:8000`
**Документация:** `http://localhost:8000/docs` (Swagger UI)

### Основные endpoints

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/health` | Статус системы (без auth) |
| `GET` | `/docs` | Swagger UI |
| `POST` | `/ingest/text` | Загрузить текст в память |
| `POST` | `/query` | Задать вопрос агенту |
| `POST` | `/facts` | Создать факт напрямую |
| `GET` | `/facts/{id}` | Получить факт |
| `PATCH` | `/facts/{id}/transition` | Изменить ESM-состояние |
| `GET` | `/agent/notebook` | ResearchNotebook SleepTimeWorker |

### Export endpoints (Этап 3)

| Метод | Путь | Результат |
|---|---|---|
| `POST` | `/export/facts` | Факты → файл любого формата |
| `POST` | `/export/mhi` | MHI dashboard → PDF/HTML |
| `POST` | `/export/truthgate` | TruthGate аудит → отчёт |
| `POST` | `/export/knowledge_base` | Validated факты → книга знаний |
| `GET` | `/export/formats` | Список форматов |
| `GET` | `/export/themes` | Список тем оформления |

### Безопасность (v8.4.0 фиксы)

- `VELANTRIM_API_KEY` — обязателен, иначе `RuntimeError` при старте
- `X-Api-Key` заголовок — проверяется на каждом защищённом запросе
- `req.by` в transition — игнорируется (audit trail spoofing закрыт)
- `CORS_ORIGINS` — пустой по умолчанию (был `"*"` — нарушение CORS spec)

---

## 10. 🧪 Тесты и качество

### Метрики после всех этапов

| Метрика | Значение |
|---|---|
| Всего тестов | 370+ |
| Coverage | ~87% |
| xfail-strict | 1 (честный — NLI naive detector) |
| Python файлов | ~80 |
| Строк кода | ~16 000 |
| Строк документации | ~5 000 |

### Распределение тестов

```
test_causal_graph.py         45+ тестов   Patch 13 (CRUD, traversal, confidence)
test_adversarial.py          49 тестов    Безопасность + regression
test_esm.py                  36 тестов    ESM жизненный цикл
test_sleep_time_worker.py    37 тестов    SleepTimeWorker + CoreMemoryBlocks
test_hybrid_retriever.py     21 тест      Поиск
test_embedding_registry.py   19 тестов    Embeddings
test_pipeline.py             19 тестов    Оркестратор
test_truth_gate.py           20 тестов    Верификация
test_server_integration.py   14 тестов    FastAPI TestClient (стыки)
test_understanding_layer.py  17 тестов    Patch 13+14
test_affordance_mvp.py       10 тестов    Variant C + benchmark
... (остальные)
```

---

## 11. 📚 История версий и что было сделано

### v8.4.0 — Audit Fix Release (Май 2026)

**5-раундовый внешний аудит. 7 критических багов закрыты.**

| Баг | Симптом | Фикс |
|---|---|---|
| SleepTimeWorker startup | `/agent/*` всегда 503 | Убран параметр `store=` |
| NGram split | Pipeline и server читали разные БД | `set_global_ngram()` DI |
| async/sync mismatch | Whisper в `json.loads()` coroutine | `inspect.iscoroutine()` |
| TruthGate false positives | "вода кипит при 100°C" = contradiction | Opt-in `contradiction_detector=` |
| MHI dead constant | `THRESHOLD_DEGRADED` нигде не используется | Включён в `_recommendations()` |
| API_KEY optional | Сервер стартовал открытым | `RuntimeError` без ключа |
| HybridRetriever per-request | 1-2с на каждый запрос | Singleton + dirty flag |

### Этап 1 — File Parsers v2

- Marker как primary PDF парсер
- faster-whisper для аудио
- Lazy singleton моделей
- 4 новых парсера (EPUB, Email, HTML, Archive)
- ParserRegistry вместо хардкода

### Этап 2 — File Generators v1

- 7 генераторов (PDF/DOCX/PPTX/XLSX/HTML/MD/Universal)
- 5 тем оформления
- 10 типов контентных блоков
- `FactBlock` — Velantrim-специфичный блок

### Этап 3 — Integration Layer

- 5 SKILL.md документов (PDF/DOCX/PPTX/XLSX/HTML)
- 4 готовых шаблона отчётов (MHI/TruthGate/KB/Sprint)
- 6 HTTP export endpoints
- 45+ тестов для генераторов и парсеров

### v8.4.4 — NLI Contradiction Detection

- Заменён token-XOR на `cross-encoder/nli-deberta-v3-small`
- Двухуровневый детектор: Tier 1 token pre-filter → Tier 2a NLI
- 304 → 326 тестов

### v8.5.0 — Understanding Layer (Patch 13+14)

- `core/causal_graph.py` — 12 типов отношений
- `core/living_context.py` — 8 измерений практического знания
- `core/understanding_layer.py` — объединение
- `core/affordance_linker.py` — Variant C MVP с F1 benchmark
- `migrations/008_add_relations.sql` — 6 новых SQLite таблиц
- 71 новый тест

---

## 12. 🗓️ Roadmap

```
✅ v8.4.0    Audit Fix (7 critical bugs)
✅ Этап 1   File Parsers v2 (60+ форматов)
✅ Этап 2   File Generators v1 (15+ форматов, 5 тем)
✅ Этап 3   Integration Layer (skills, reports, API)
✅ v8.4.4   NLI Contradiction Detection
✅ v8.5.0   Understanding Layer (Causal Graph + Living Context)

🔜 Patch 1   asyncio.to_thread фикс              (1-2 часа)
🔜 Patch 3   FSRS retrieval-based maturation     (3-4 часа)
🔜 Patch 4   Real E2E tests без MockLLM           (1-2 дня)
🔜 Patch 5   HaluEval external benchmark          (2-3 дня)
🔜 Patch 6   Emergency invalidation trusted       (3-4 часа)
📋 Patch 14b Living Context Full (spaCy)          (4 недели, после MVP чисел)
📋 Sprint 2b Реальный LLM в pipeline
📋 Sprint 2c async/await + aiosqlite
📋 v9.0.0    Understanding Layer production ready
```

---

## 🔱 Принципиальное превосходство над конкурентами

| Способность | Mem0 | Zep | Letta | Velantrim |
|---|---|---|---|---|
| ESM жизненный цикл | ❌ | ❌ | ❌ | ✅ 8 состояний |
| Typed causal relations | ❌ | ❌ | ❌ | ✅ 12 типов |
| knowledge_status | ❌ | ❌ | ❌ | ✅ known/inferred/hyp |
| NLI contradiction | ❌ | Частично | ❌ | ✅ DeBERTa cross-encoder |
| Bi-temporal model | ❌ | ❌ | ❌ | ✅ valid_from/valid_to |
| Audit trail 100% | ❌ | ❌ | Частично | ✅ |
| File I/O (60+ → 15+) | ❌ | ❌ | ❌ | ✅ Parsers + Generators |
| Готовые отчёты | ❌ | ❌ | ❌ | ✅ 4 шаблона |

*Данные основаны на публичной документации конкурентов, май 2026.*

---

> **Velantrim ExoCortex** · v8.5.0 · May 2026
> *From memory to understanding* 🧬
