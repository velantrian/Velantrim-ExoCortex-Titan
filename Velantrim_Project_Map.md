# 🌿 Velantrim ExoCortex — Карта проекта

## Когнитивная память для AI-агентов

**Версия:** **VELANTRIM V8.6 Complex** (8.6.0) — наследует v8.5.1 Patch Series
**Тестов:** 543 passed · 17 skipped · 13 xfailed · 0 failures
**Дата:** 19 мая 2026
**Формула:** `Graph = Truth · LLM = Language · Memory = Physiology · Tests = Proof`

> 🌿 **Прежде всего:** [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) — почему Velantrim существует.
> 🔒 **Для AI-агентов:** [`docs/PHILOSOPHY_SPEC.md`](docs/PHILOSOPHY_SPEC.md) — обязательные инварианты.

> ⚠️ **Граница репозитория:** **ядро, ExoCortex, L6 MVP, Horizons docs** — здесь (`server.py`). Graphiti/Neo4j fork — `../Graphiti_fractal-main`. Карта слоёв: [`docs/LAYERS_AND_HORIZONS.ru.md`](docs/LAYERS_AND_HORIZONS.ru.md) · Horizons: [`docs/HORIZONS.md`](docs/HORIZONS.md) · **Аудит:** [`docs/AUDIT_V8_6.ru.md`](docs/AUDIT_V8_6.ru.md).

> Этот документ — твоя карта по проекту. Прочитай первый раздел чтобы понять что
> такое Velantrim. Посмотри ASCII-карту чтобы увидеть как всё связано. Дальше —
> навигация по каждому файлу, чтобы ты знал где что лежит и зачем оно нужно.

---

## 📖 Что такое Velantrim — за две минуты

Обычный AI-агент живёт в одном разговоре. Каждый новый чат — он не помнит ничего.
Даже если у него есть «память» — это плоский список заметок без связей, без
понимания что важно, без обучения на ошибках. Velantrim решает это по-другому.

Velantrim не база данных и не обёртка над LLM с историей. Это **слой долговременной
памяти**, который думает о фактах как живой организм думает о воспоминаниях:

🧬 **Каждый факт имеет состояние доверия.** Не просто «есть в базе» — а
*Observed → Hypothesized → Supported → Validated → ImmutableCore*. Состояние
меняется только через явные переходы, история всех переходов хранится.

🔗 **Факты связаны причинно.** 15 типов связей: causes, prevents, requires,
enables, implies, contradicts, generalizes, specializes, precedes, follows,
composes, analogous_to, becomes, affords, inhabited_by. Каждая связь несёт
**knowledge_status** отдельно от **confidence** — система знает, чего она не знает.

📜 **Оригинал хранится навсегда.** L0 Raw Memory — иммутабельная таблица с
SHA256-дедупликацией. Любой производный факт ссылается на оригинал через
`derived_from`. Защита от семантического дрейфа.

⚖️ **Перед записью — TruthGate.** Четыре когнитивных режима: PRECISION
(только Validated, evidence ≥ 5), BALANCED (по умолчанию), EXPLORATION
(гипотезы разрешены), CREATIVE (максимум гибкости). Мусор в память не попадает.

🌙 **Sleep worker наводит порядок.** Пока система не отвечает на запросы — она
консолидирует память: ищет дубли, понижает вес устаревшего, обнаруживает
противоречия.

---

## 🗺️ Архитектурная карта — что куда обращается

```
═════════════════════════════════════════════════════════════════════════
                          ВХОД И ВЫХОД
═════════════════════════════════════════════════════════════════════════

  👤 Пользователь
      │ HTTP
      ▼
  ╔══════════════════════════════════════════════════════════╗
  ║  🌐 server.py — FastAPI слой                              ║
  ║     • POST /query      → запрос к памяти                  ║
  ║     • POST /facts      → добавить факт (+ L0 Raw)         ║
  ║     • POST /ingest/text → загрузить текст (+ L0 Raw)      ║
  ║     • GET /memory/stats → метрики и здоровье              ║
  ║     • PATCH /facts/{id}/transition → ESM-переход          ║
  ║     • GET /reports/mhi → Memory Health Index              ║
  ╚══════════════════════════════════════════════════════════╝
      │
      ▼
═════════════════════════════════════════════════════════════════════════
                       КОГНИТИВНЫЙ КОНВЕЙЕР
═════════════════════════════════════════════════════════════════════════

  ⚙️ core/pipeline.py — главный конвейер (8 шагов)
      │
      ├── 1. 🔎 retrieve()
      │      • get_fact_ids() → лёгкий список ID (TASK-06)
      │      • NGramIndex.query() → O(log N) pre-filter
      │      • get_facts_by_ids() → top-K полных фактов
      │      • HybridRetriever (BM25 + Dense + RRF) → singleton (TASK-04)
      │
      ├── 2. 📦 build_facts_pack() → FactsPackBuilder (TASK-12)
      │      • store_fact() с no-op guard (TASK-05)
      │      • NGram-индексация
      │      • Применение CognitiveMode-политик
      │
      ├── 3. 📝 build_trace() — провенанс
      │
      ├── 4. 🛡️ guardian() — fact_id coverage check
      │
      ├── 5. ⚖️ truth_gate() — фильтр по mode
      │      • MVP: confidence ≥ min_confidence
      │      • BALANCED/PRECISION: real TruthGate + evidence_count
      │
      ├── 6. 🧬 transition_esm() — Observed → Validated
      │
      ├── 7. 🔗 _extract_causal_hints() — CausalGraph (TASK-08)
      │      • regex поиск каузальных паттернов (EN+RU)
      │      • предлагает 'implies' с knowledge_status='hypothetical'
      │
      ├── 8. ✨ generate_answer() — финальный ответ + causal_hints
      │
      └── 9. 🧠 exocortex_sections (V8.6, ENABLE_*)
             • Velum / Etir / Fusion — core/exocortex_hooks.py

═════════════════════════════════════════════════════════════════════════
              EXOCORTEX (optional, ENV) + HORIZONS — V8.6
═════════════════════════════════════════════════════════════════════════

  📚 docs/HORIZONS.md · docs/LAYERS_AND_HORIZONS.ru.md · docs/horizons/*.md
  📡 GET /layers/status · GET /horizons
  🟡 L1.5 Velum · L3.5 Etir/Immutable · L4.5 · L5.5 Fusion (ENABLE_*=0)
  🔬 L2.5 Staging · R2–R5 · KDE — research (доки, без runtime)
  🟡 L6 MVP: welfare_monitor · volition_gate (ENABLE_L6_WELFARE=0)
  ⚙️ config/exocortex-dev.env — профиль для локальной отладки

═════════════════════════════════════════════════════════════════════════
                        ХРАНЕНИЕ — SQLite
═════════════════════════════════════════════════════════════════════════

  🗄️ core/memory.py — SQLiteGraphStore (главное хранилище)
      │
      ├── 📋 Таблица facts (L1)
      │      • fact_id, claim, source, confidence
      │      • epistemic_state (8 состояний)
      │      • bi-temporal: t_event_valid_*, t_ingestion_* (I96)
      │      • derived_from → l0_raw_memory.raw_id (TASK-09)
      │      • history JSON — audit trail переходов
      │
      ├── 📜 Таблица l0_raw_memory (TASK-09)
      │      • raw_id, original_text (immutable)
      │      • content_hash (SHA256, dedup)
      │      • TRIGGER prevent_raw_update — никаких изменений никогда
      │
      ├── 🔗 Таблица relations (TASK-08)
      │      • from_fact_id, to_fact_id, relation_type
      │      • 15 forward types + backward inversions
      │      • knowledge_status: known/inferred/hypothetical/unknown
      │      • review_state: approved/pending/rejected
      │
      ├── 🧪 L0 LRU кэш — горячие факты в RAM (l0_cap=1000)
      │
      └── 📂 SQLite file: ./data/velantrim_memory.db

═════════════════════════════════════════════════════════════════════════
                  ВСПОМОГАТЕЛЬНЫЕ СЛОИ И СЕРВИСЫ
═════════════════════════════════════════════════════════════════════════

  🔍 core/hybrid_retriever.py — поисковый движок
       BM25Retriever + DenseRetriever (sentence-transformers) + RRF fusion
       Singleton + dirty flag → не пересоздаётся на каждый запрос

  🔤 core/ngram_index.py — FTS5 trigram pre-filter
       Сужает 100k фактов → 50 кандидатов за O(log N)

  ⚖️ core/truth_gate.py + core/facts_pack.py — фильтр истины
       CognitiveMode: PRECISION / BALANCED / EXPLORATION / CREATIVE

  🕸️ core/causal_graph.py — слой связей (15 типов)
       find_contradictions() с cycle protection (TASK-10)
       causal_chain() с deque BFS (TASK-11)

  📜 core/raw_memory.py — L0 API (использовался для разработки)
       Производство: SQLiteGraphStore.store_raw_text() (TASK-09)

  🌙 core/sleep_time_worker.py — фоновая консолидация
       Health checks, gap detection, asyncio _bg_tasks для GC

  📊 core/mhi.py — Memory Health Index
       Метрика 0..1 здоровья системы

  🔍 core/audit_chain.py — append-only audit trail
       Каждое изменение факта → ImmutableEntry

  💎 core/validators.py — единая валидация
       validate_source(), validate_confidence()

  🧰 core/storage.py — GraphStore ABC + AsyncGraphStore
       Контракт для будущих бэкендов (Neo4j, etc.)

═════════════════════════════════════════════════════════════════════════
                  ВХОДНЫЕ И ВЫХОДНЫЕ ФОРМАТЫ
═════════════════════════════════════════════════════════════════════════

  📥 core/file_parsers/ — извлечение фактов из файлов
       PDF · DOCX · PPTX · CSV · EPUB · HTML · email · audio · video · archive
       file_ingester.py координирует, делегирует специализированным парсерам

  📤 core/file_generators/ — экспорт результатов
       DOCX · PDF · PPTX · XLSX · HTML · Markdown
       file_exporter.py + universal_generator.py для произвольных форматов

  📊 core/velantrim_reports/ — отчёты
       mhi_report.py — здоровье памяти
       sprint_review.py — прогресс по задачам
       knowledge_base.py — состояние базы знаний
       truthgate_report.py — что проходит/блокируется

═════════════════════════════════════════════════════════════════════════
```

---

## 📁 Что где лежит — навигация по файлам

Дальше — карта каждого файла с одной строкой объяснения. Когда нужно найти
что-то конкретное — сначала ищи здесь.

### 🏠 Корень проекта

| Файл | Что это |
|------|---------|
| `README.md` | Точка входа в проект — установка, быстрый запуск |
| `CHANGELOG.md` | История версий от v8.0 до v8.5.1-patch7 (объединён из 4 файлов) |
| `WORK_LOG.md` | Журнал задач: 15 TASK + RESEARCH + DECISION, все ✅ done |
| `SYSTEM_OVERVIEW.md` | Обзор архитектуры на 1000 строк — для глубокого погружения |
| `ROADMAP.md` | План на следующие версии |
| `server.py` | FastAPI HTTP-сервер, точка входа в production |
| `pyproject.toml` | Конфигурация Python-проекта, зависимости, тесты, coverage |

### 🧠 `core/` — ядро системы

**Главный конвейер и хранилище:**

| Файл | Назначение | Ключевое |
|------|------------|----------|
| `pipeline.py` | Главный конвейер `run()` — 8 шагов от query до ответа | `_get_hybrid_retriever()` singleton, `_get_causal_graph()` singleton |
| `memory.py` | SQLiteGraphStore — все операции с фактами | `store_fact()` → bool, `get_fact_ids()`, `store_raw_text()` |
| `storage.py` | ABC: GraphStore + AsyncGraphStore | Контракт для будущих backend (Neo4j) |
| `trace.py` | Trace builder + format_trace + promote_trace | Provenance каждого факта в ответе |

**Поиск и индексация:**

| Файл | Назначение |
|------|------------|
| `hybrid_retriever.py` | BM25 + Dense + RRF fusion, singleton |
| `ngram_index.py` | FTS5 trigram pre-filter, graceful degradation |
| `embedding_registry.py` | Реестр embedding-моделей (sentence-transformers) |

**Эпистемика и истина:**

| Файл | Назначение |
|------|------------|
| `truth_gate.py` | TruthGate + CognitiveMode (PRECISION/BALANCED/EXPLORATION/CREATIVE) |
| `facts_pack.py` | FactsPackBuilder — применяет CognitiveMode-политики (TASK-12) |
| `evidence.py` | Evidence collection (источники для confidence ≥ 5 в PRECISION) |
| `confidence.py` | Confidence computation utilities |
| `validators.py` | validate_source(), validate_confidence() — единая валидация |

**Граф связей и понимание:**

| Файл | Назначение |
|------|------------|
| `causal_graph.py` | 15 типов связей, find_contradictions, causal_chain, implications |
| `understanding_layer.py` | UnderstandingLayer — переход от фактов к пониманию |
| `living_context.py` | "Что с этим можно делать?" — affordances |
| `affordance_linker.py` | Canonical affordances — нормализованный словарь действий |

**Память и провенанс:**

| Файл | Назначение |
|------|------------|
| `raw_memory.py` | L0 RawMemoryStore — иммутабельная память (API из v8.5.1) |
| `audit_chain.py` | Append-only audit trail каждого изменения |
| `cache_coherence.py` | Когерентность L0 LRU кэша |

**Фоновые сервисы:**

| Файл | Назначение |
|------|------------|
| `sleep_time_worker.py` | Async background worker для консолидации |
| `mhi.py` | Memory Health Index — общий показатель здоровья |
| `errors.py` | VelantrimError + дочерние классы исключений |

### 📥 `core/file_parsers/` — извлечение из файлов

Координатор: `file_ingester.py` (выбирает парсер по MIME-type).

| Парсер | Форматы |
|--------|---------|
| `pdf_parser.py` | PDF (текстовый + сканированный через OCR) |
| `docx_parser.py` | Microsoft Word .docx |
| `pptx_parser.py` | PowerPoint .pptx |
| `csv_parser.py` | CSV tabular data |
| `epub_parser.py` | EPUB e-books |
| `html_parser.py` | HTML web pages |
| `email_parser.py` | .eml messages |
| `audio_parser.py` | Audio → text (Whisper) |
| `video_parser.py` | Video → audio → text |
| `image_parser.py` | Images → OCR (Tesseract) |
| `archive_parser.py` | ZIP/TAR с рекурсивным parsing |
| `text_parser.py` | Plain text fallback |

### 📤 `core/file_generators/` — экспорт результатов

Координатор: `file_exporter.py` + `universal_generator.py`.

| Генератор | Формат вывода |
|-----------|----------------|
| `pdf_generator.py` | PDF (через ReportLab) |
| `docx_generator.py` | Microsoft Word .docx |
| `pptx_generator.py` | PowerPoint .pptx |
| `xlsx_generator.py` | Excel .xlsx |
| `html_generator.py` | HTML |
| `markdown_generator.py` | Markdown |

### 📊 `core/velantrim_reports/` — отчёты

| Файл | Что генерирует |
|------|----------------|
| `mhi_report.py` | Memory Health Index — числовая метрика 0..1 |
| `sprint_review.py` | Отчёт по спринтам/задачам |
| `knowledge_base.py` | Состояние базы знаний (по доменам, по доверию) |
| `truthgate_report.py` | Что прошло и заблокировано через TruthGate |

### 🗄️ `migrations/` — SQL-миграции

| Файл | Что добавляет |
|------|---------------|
| `008_add_relations.sql` | Таблицы `relations` + `relation_paths` для CausalGraph |
| `009_truth_kernel.sql` | Truth kernel — контракт правды |
| `010_raw_memory.sql` | `l0_raw_memory`, `l0_fact_provenance` + immutable triggers |

### 📚 `docs/` — документация

**Главные:**

| Файл | Содержание |
|------|------------|
| `PHILOSOPHY.md` | 🌿 **Манифест проекта** — почему Velantrim существует, роли Человека и ИИ |
| `PHILOSOPHY_SPEC.md` | 🔒 **Обязательно для AI-агентов** — 6 инвариантов + inversion tests |
| `TONE_OF_VOICE.md` | 🗣️ **Как Velantrim говорит** — 7 правил формулирования ответов (TASK-17) |
| `KERNEL_STATE.md` | 🔩 **Реальное состояние ядра** — что укреплено, что нет, без преувеличений |
| `AUDIT_2026_05_20_MULTI_AI.md` | 📋 Мульти-AI аудит (6 систем) с P0/P1/P2 backlog |
| `VISION_V10_DRAFT.md` | 🔭 **Маяк для V10** — нативная CognitiveFact архитектура |
| `knowledge/KNOWLEDGE_0_OVERVIEW.md` | 🌿 **v3.0 Машинная суть** — без педагогики, только знание |
| `knowledge/KNOWLEDGE_BASE_LAWS.md` | 🏛️ v3.0 Базовые законы (140-170 законов всех наук) |
| `knowledge/KNOWLEDGE_1_INVARIANT.md` | 🪨 v3.0 Производные факты (800-1200) |
| `knowledge/KNOWLEDGE_2_VARIANT.md` | 🌊 v3.0 Меняющиеся факты (500-1500) |
| `knowledge/KNOWLEDGE_3_PRACTICAL.md` | 🔧 v3.0 Процессы и технологии (500-2000) |
| `knowledge/KNOWLEDGE_4_PERCEPTION.md` | 👁️ v3.0 Восприятие организмами (300-1000) |
| `knowledge/KNOWLEDGE_5_LOGIC.md` | ⚖️ v3.0 Логика и правила вывода (200-500) |
| `knowledge/KNOWLEDGE_6_ABSTRACT.md` | 🌌 v1.0 Воображение, фантазия, история, интуиция (200-400) |
| `INVARIANTS.md` | Все инварианты системы (I1-I99+) — список того что НЕ может произойти |
| `VELANTRIM_ARCHITECTURE.md` | Подробная архитектура всех слоёв |
| `VELANTRIM_GUIDE.md` | Гайд для разработчиков |

**Операционные:**

| Файл | Содержание |
|------|------------|
| `DEPLOY.md` | Деплой инструкции (Docker, env vars, миграции) |
| `RUN.ru.md` | Быстрый старт на русском |
| `LIMITATIONS.md` | Что система НЕ делает (важно для честности) |
| `AUDIT_FIXES.md` | История фиксов из аудитов |

**Аудиты и исторические:**

| Файл | Содержание |
|------|------------|
| `Velantrim_V9_Final_Audited.md` | Аудит V9 архитектуры |
| `Velantrim_Code_Audit_vs_V9.md` | Сравнение текущего кода с V9 |
| `WORK_SUMMARY.md` | Сводка работ |
| `README_ETAP3.md` | Описание этапа 3 разработки |

### 🌱 `docs/seed/` — манифесты проекта (раньше `Diary/`)

| Файл | Содержание |
|------|------------|
| `01_vision_manifesto.md` | Видение проекта — зачем это всё |
| `02_polyperspective_seed.md` | Полиперспективное мышление в Velantrim |
| `README.md` | Зачем эта папка существует |

### 🧪 `tests/` — тесты (498 passed)

| Файл | Что тестирует |
|------|----------------|
| `test_pipeline.py` | Главный конвейер end-to-end, регрессии TASK-04/05/06/08 |
| `test_esm.py` | ESM transitions, drift protection, L0 RawMemory (TASK-09) |
| `test_causal_graph.py` | CausalGraph: cycle protection (TASK-10), deque BFS (TASK-11) |
| `test_truth_gate.py` | TruthGate filtering по CognitiveMode |
| `test_truth_kernel.py` | Truth kernel инварианты |
| `test_hybrid_retriever.py` | BM25 + Dense + RRF |
| `test_ngram.py` | NGramIndex pre-filter |
| `test_sleep_time_worker.py` | Async background worker |
| `test_server_integration.py` | E2E HTTP endpoints |
| `test_understanding_layer.py` | UnderstandingLayer |
| `test_affordance_mvp.py` | Affordance linker |
| `test_mhi.py` | Memory Health Index |
| `test_smoke.py` | Дымовые тесты импортов |
| `test_regression_p0.py` | Регрессии P0 багов (v8.0.2 idempotency, etc.) |
| `test_adversarial.py` | Adversarial inputs — попытки сломать систему |
| `test_embedding_registry.py` | Реестр embedding-моделей |
| `test_knowledge_ingester.py` | Извлечение знаний из файлов |
| `golden_dataset.py` | Эталонные тестовые данные |

Подпапки: `test_file_parsers/`, `test_file_generators/` — для соответствующих модулей.

### 🛠️ `scripts/` — утилиты

| Файл | Что делает |
|------|------------|
| `apply_migrations.py` | Применяет SQL-миграции к БД |
| `sync_docs.py` | Синхронизация документации |

### 📐 `skills/` — спецификации форматов для AI

| Папка | Содержание |
|-------|------------|
| `docx/`, `html/`, `pdf/`, `pptx/`, `xlsx/` | SKILL.md с инструкциями как Claude должен генерировать каждый формат |

### 🏃 `benchmarks/` — нагрузочные тесты

| Файл | Что измеряет |
|------|--------------|
| `bench_pipeline.py` | Pipeline latency p95, retrieval speed |

### 🔧 `utils/` и `server_patch/`

| Файл | Назначение |
|------|------------|
| `utils/text_utils.py` | tokenize, normalize и другие текстовые утилиты |
| `server_patch/export_endpoints.py` | Расширения для server.py (export-эндпоинты) |

---

## 🧬 Ключевые концепции — куда смотреть

Если ищешь конкретную концепцию — вот где её код:

### Epistemic State Machine (ESM)

`core/memory.py` — константы `ESM_STATES`, `ESM_TRANSITIONS`, функция `transition_esm()`.

8 состояний: `Observed → Hypothesized → Supported → Validated → ImmutableCore`,
с веткой конфликта `Contradicted → Deprecated → Collapsed`. Матрица переходов
определена явно — нелегальные переходы (`Validated → Validated`) выбрасывают ValueError.

### CognitiveFact (будущее — V10)

См. `docs/VISION_V10_DRAFT.md`. Сейчас факты живут в нескольких местах
(SQLite + HybridRetriever + CausalGraph). V10 — единый объект.

### CognitiveMode policies

`core/facts_pack.py` — словарь `COGNITIVE_MODE_POLICIES`:
- **PRECISION** — только Validated + ImmutableCore, confidence ≥ 0.75
- **BALANCED** — + Supported, confidence ≥ 0.55 (по умолчанию)
- **EXPLORATION** — + Hypothesized, confidence ≥ 0.35
- **CREATIVE** — + Observed, confidence ≥ 0.20

### Bi-temporal model (I96)

`core/memory.py` — поля `t_event_valid_*` и `t_ingestion_*`.

Время события (когда оно реально произошло) ≠ время ingestion (когда система
узнала об этом). Time-travel запросы через `get_fact_at(fact_id, known_at, world_at)`.

### Ring Zero (ImmutableCore)

`core/memory.py` — `IMMUTABLE_FACT_IDS = {"VALUES_CORE", "RING_ZERO"}`.

Эти факты создаются сразу в `Validated` и переходят в `ImmutableCore` —
неизменяемое состояние без выхода. Защита базовых ценностей системы.

### 15 типов связей

`core/causal_graph.py` — `FORWARD_RELATION_TYPES` (15) + `INVERSE_RELATIONS` (автоматические).

Forward: causes, prevents, requires, enables, implies, contradicts, generalizes,
specializes, precedes, follows, composes, analogous_to, becomes, affords, inhabited_by.

### CausalDistance v0 (будущее — V10)

См. `docs/VISION_V10_DRAFT.md` раздел Retrieval Model.

Формула: `Ws·semantic + Wt·temporal + We·epistemic + Wr·relation + Wu·usage`.
Веса калибруются через learning-to-rank после накопления данных.

### Memory Health Index (MHI)

`core/mhi.py` — `MHICalculator` + `check_mhi(store)`.

Показатель 0..1 учитывающий: долю Contradicted, среднюю confidence,
скорость drift, размер orphan-фактов без provenance.

---

## 🎯 Как найти ответ на вопрос

| Вопрос | Где смотреть |
|--------|---------------|
| Как запустить локально? | `docs/RUN.ru.md` или `README.md` |
| Что делает endpoint X? | `server.py` — поиск по `@app.post`/`@app.get` |
| Как добавляется факт? | `server.py:create_fact` → `core/memory.py:store_fact` |
| Что такое state X? | `core/memory.py:ESM_STATES` + `docs/VISION_V10_DRAFT.md:ESM` |
| Какие есть типы связей? | `core/causal_graph.py:FORWARD_RELATION_TYPES` |
| Почему этот тест ловит этот баг? | Имя теста = название инварианта или TASK-XX |
| Какая текущая версия? | `CHANGELOG.md` сверху |
| Что планируется дальше? | `ROADMAP.md` + `docs/VISION_V10_DRAFT.md` |
| Где список инвариантов? | `docs/INVARIANTS.md` |
| Где история работ? | `WORK_LOG.md` |
| Куда система НЕ умеет? | `docs/LIMITATIONS.md` |

---

## 🚦 Текущий статус — что работает сейчас

| Слой | Статус | Где код |
|------|--------|---------|
| HTTP API (FastAPI) | ✅ работает | `server.py` |
| ESM transitions | ✅ 8 состояний + матрица | `core/memory.py` |
| Bi-temporal storage | ✅ 4 поля времени | `core/memory.py` |
| HybridRetriever singleton | ✅ 40x ускорение | `core/hybrid_retriever.py` + `pipeline.py` |
| NGramIndex pre-filter | ✅ FTS5 graceful degradation | `core/ngram_index.py` |
| TruthGate + CognitiveMode | ✅ 4 режима | `core/truth_gate.py` + `core/facts_pack.py` |
| CausalGraph в pipeline | ✅ causal_hints в ответе | `core/causal_graph.py` + `pipeline.py:step 7` |
| L0 RawMemory | ✅ derived_from при ingest | `core/memory.py:store_raw_text` |
| Sleep worker | ✅ async фон | `core/sleep_time_worker.py` |
| MHI отчёт | ✅ метрика 0..1 | `core/mhi.py` + `velantrim_reports/mhi_report.py` |
| File parsers | ✅ 12 форматов | `core/file_parsers/` |
| File generators | ✅ 6 форматов | `core/file_generators/` |
| Audit chain | ✅ append-only | `core/audit_chain.py` |

---

## 🛤️ Что должно быть сделано (P0/P1/P2 Backlog)

Из мульти-AI аудита 20 мая 2026 — приоритизация работ по три уровня:

### 🔴 P0 — СЕЙЧАС (жёсткость и честность)

```
✅ Contradiction-First         (TASK-16, done)
✅ Tone of Voice               (TASK-17, done)
🟡 Contract-test "TruthGate → store"  ← следующее
🟡 Stress-test конкурентной записи
🟡 DI рефакторинг mhi_report.py
```

### 🟡 P1 — ПОТОМ (порядок памяти)

```
🔴 Memory Tiers (L0 / L1 / L2 явные уровни)
🔴 Knowledge Types (INVARIANT / VARIANT / PRACTICAL)
🔴 Bi-temporal queries расширение
```

### 🟢 P2 — ПОЗЖЕ (расширение мышления)

```
🔴 Multi-domain Retrieval (поликогнитивность)
🔴 Synaptic Decay (живая память)
🔴 NeuroSleep (3 фазы консолидации)
🔴 Voice interface (шаг к Джарвису)
```

### 📜 Главный принцип

```
Честность ⚖️
     ↓
Порядок памяти 🗂️
     ↓
Типы знаний 📚
     ↓
Многоголосое мышление 🌐
     ↓
Живой организм 🧬
```

**Не строить новый слой пока не закреплён предыдущий.**

См. `docs/AUDIT_2026_05_20_MULTI_AI.md` для деталей и `docs/KERNEL_STATE.md` для честного состояния ядра.

---

## ⏭️ Что планируется (V9 → V10)

Подробно — в `docs/VISION_V10_DRAFT.md`. Кратко:

```
v9.1   CognitiveFact dataclass — единый объект вместо dict
v9.2   CognitiveFactStore — унификация записи через одну точку
v9.3   Унификация чтения и retrieval
v9.4   EventBus — устраняет mark_retriever_dirty через события
v9.5   CognitiveDistance v0 — заменяет RRF на 5-осевую формулу
v9.6   Consolidation как event handlers
v9.7   Relations нативно в CognitiveFact
v9.8   ESM transitions через EventBus
v9.9   Contract tests на стыках (>95% pass)
v9.10  CognitiveDistance калибровка через learning-to-rank
...
v10+   Полный Native CognitiveFact Runtime + Insight Engine
```

---

## 📝 История версий

Полная история — в `CHANGELOG.md`. Кратко по версиям:

- **v8.5.1-patch7** (19 мая 2026) — Deep Audit Patch Series, 15 задач закрыты
- **v8.5.3** — Orphan Wiring + Concurrency Hardening
- **v8.5.2** — Cross-AI Audit Hotfix (17.5% failures → 0%)
- **v8.5.1** — Patch 13: CausalGraph + L0 RawMemory модули
- **v8.4.0** — Audit Fix Release (7 production-blockers)
- **v8.0–v8.3** — pipeline, HybridRetriever, bi-temporal, drift protection

---

## 🧭 Принципы проекта

Эти принципы определяют каждое архитектурное решение:

🧠 **Graph = Truth.** Граф фактов — единственный источник правды. LLM не источник
правды, он язык для общения. NeuroCore не источник правды (когда будет), он скорость.

⚖️ **Числа > мнения AI.** Когда меришь — меришь числами. Когда сомневаешься —
проверяешь тестом. `xfail` с пояснением лучше чем "10/10 CERTIFIED".

📜 **Оригинал хранится навсегда.** L0 Raw Memory иммутабелен. Любой производный
факт прослеживается до оригинального текста. Никакого silent semantic drift.

🛡️ **Negative space design.** Архитектура определяется не только тем что система
делает, а тем что она НЕ может сделать. Список инвариантов > список фич.

🔄 **Идемпотентность по умолчанию.** `run("X")` дважды → тот же результат.
ESM-переход в текущее состояние → no-op, не ошибка. `store_fact()` с теми же
данными → no-op, не двойная запись.

🎚️ **Когнитивный режим — параметр.** Один и тот же запрос в PRECISION и
EXPLORATION даёт разные ответы по правилу. Это не баг, это feature.

🤝 **Adversarial collaboration.** Развитие через несколько AI которые работают
друг против друга: Claude находит архитектурное, ChatGPT находит runtime,
Grok синтезирует. Результат сильнее любого индивидуального.

---

> 🌿 **Velantrim ExoCortex** — не база данных и не RAG, а слой долговременной
> памяти для AI-агентов. Каждый факт имеет состояние доверия, связан причинно,
> хранит оригинал и проходит через TruthGate перед записью.
>
> Память — это не склад. Это рабочая среда интеллекта.
>
> *Состояние на 2026-05-19: 498 тестов passed, 15 задач закрыто, готов к V9.*
