# 🔱 Velantrim ExoCortex V8.7 Titan — Как это работает

> **Версия:** v8.7.0 Titan · **Дата:** 3 июня 2026
> **Модулей:** 130+ в `core/` · **Тестов:** 88 файлов · **Инвариантов:** 18 исполняемых
>
> Этот документ объясняет систему простым языком — что для чего, как работает, что с чем связано.
>
> **Ключевое в V8.7:** иммунная система (MetaSupervisor + ImmutableCore + ProvenanceChain),
> ось идентичности (Identity Layer + Stimulus Map), production-ready (Docker, Prometheus, aiosqlite),
> каталог LLM только из актуальных моделей, 4 ортогональные оси архитектуры.
>
> **V8.6 (исходный код):** нетронут в отдельной папке. Все изменения V8.7 аддитивны.

---

## 🧠 Что такое Velantrim — одним абзацем

Velantrim — это **долгосрочная память для AI-агентов**. Представь что у обычного
AI нет памяти между разговорами — каждый раз он начинает с чистого листа.
Velantrim решает эту проблему: он запоминает факты, проверяет их достоверность,
следит за тем как они устаревают, и отвечает только тем что реально знает —
с доказательствами. Не галлюцинирует.

Как future-work к этому добавлен **Essence Layer**: слой, который должен помогать
системе схватывать главное, связывать сложные термины в цепочку смысла и отвечать
коротко, по-человечески. Это не “личность” и не эмоции, а способ превратить
длинный набор фактов в ясный вывод: “вот суть, вот почему, вот что из этого
следует”. Канон: `docs/ESSENCE_LAYER_CANON.ru.md`.

Поверх этого добавлен P0-каркас **Attention + Noetic Orchestration**: система
должна сначала понять цель (`GoalFrame`), выбрать важные факты
(`AttentionRouter`), решить глубину обработки (`ComputeController`) и только
потом строить смысловую модель (`NoeticCore`: суть, причинность, возможные
последствия, неопределённость). Это внешний слой над LLM/Retrieval/Graph, а не
новая нейроархитектура. Канон: `docs/ATTENTION_NOETIC_ORCHESTRATION.ru.md`.

---

## 🗺️ Карта всего проекта

```
🔱 velantrim-exocortex-crystal  (sandbox clone "Duan")
│
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  🧠 ЯДРО СИСТЕМЫ — то что реально работает прямо сейчас           │
│  │                                                                     │
│  │   📜 storage.py ──► контракт: ЧТО должно уметь хранилище          │
│  │         │                                                           │
│  │         ▼                                                           │
│  │   🧠 memory.py ──► ПАМЯТЬ: факты, ESM, кэш, bi-temporal           │
│  │         │                                                           │
│  │         ├──────────────────────────────────────────────────────┐   │
│  │         ▼                                                       ▼   │
│  │   🔍 trace.py ──► СЛЕД: кто, откуда, когда      ⚙️ pipeline.py │   │
│  │                                                  главный вход   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  🧪 ТЕСТЫ — проверяют что ядро работает правильно                 │
│  │                                                                     │
│  │   test_esm.py ──────────────► проверяет memory.py                 │
│  │   test_pipeline.py ──────────► проверяет pipeline.py + trace.py   │
│  │   test_regression_p0.py ─────► старые баги не вернулись           │
│  │   test_sprint_a_wiring.py ───► 🛡️ страж: A6-A10 не подключены    │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  🔧 ИНСТРУМЕНТЫ — запускаются вручную, не часть runtime           │
│  │                                                                     │
│  │   velantrim_migrate_v3_1.py ─► конвертер V8 markdown → JSONL      │
│  │   fill_dependencies.py ──────► автозаполнение depends_on          │
│  │   audit_metadata.py ─────────► аудит качества JSONL               │
│  │   check_rfc_duplicates.py ───► детектор дублей RFC                │
│  │   utils/rfc_parser.py ───────► общая утилита парсинга RFC         │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  📚 ДОКУМЕНТАЦИЯ — читать и обновлять                              │
│  │                                                                     │
│  │   README.md ─────────────────► главная страница                    │
│  │   ROADMAP.md ────────────────► что сделано / что впереди           │
│  │   INVARIANTS.md ─────────────► правила которые нельзя нарушать     │
│  │   LIMITATIONS.md ────────────► честный список ограничений          │
│  │   SYSTEM_OVERVIEW.md ────────► этот файл                          │
│  └─────────────────────────────────────────────────────────────────────┘
│
└── ⚙️ КОНФИГУРАЦИЯ: pyproject.toml · requirements.txt · LICENSE
```

---

## ⚙️ Как работает система — шаг за шагом

Когда AI-агент задаёт вопрос, внутри происходит следующее:

```
👤 Вопрос пользователя: "Расскажи про квантовую запутанность"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  ⚙️  pipeline.py — Главный конвейер                      │
│                                                         │
│  Шаг 1 🔎 RETRIEVE                                      │
│  └─► Ищем релевантные факты (сейчас BM25 по mock БД)    │
│      Результат: [{факт о квантовой запутанности, ...}]  │
│                                                         │
│  Шаг 2 📦 BUILD FACTS PACK                              │
│  └─► Каждый факт сохраняем через memory.py              │
│      Начальный статус = Observed (только что увидели)   │
│                                                         │
│  Шаг 3 🔍 BUILD TRACE                                   │
│  └─► trace.py строит цепочку: откуда пришёл каждый факт│
│      fact_id + source + epistemic_state + retrieval_score│
│                                                         │
│  Шаг 4 🛡️ GUARDIAN (структурная проверка)              │
│  ├─► Есть ли fact_id у каждого факта?                   │
│  ├─► Есть ли claim и source?                            │
│  ├─► Каждый факт покрыт trace?                          │
│  └─► Если нет → БЛОКИРОВКА, ответ не даём              │
│                                                         │
│  Шаг 5 🔐 TRUTH GATE (проверка достоверности)          │
│  ├─► confidence >= 0.5?                                 │
│  ├─► source не пустой?                                  │
│  └─► Если нет → БЛОКИРОВКА                             │
│      (MVP: только confidence floor, Sprint 2 — полный)  │
│                                                         │
│  Шаг 6 🔄 ESM TRANSITION                               │
│  └─► Факты переводим Observed → Validated              │
│      Через transition_esm() — единственный легальный путь│
│                                                         │
│  Шаг 7 💬 GENERATE ANSWER                              │
│  └─► Берём только Validated факты                       │
│      Сейчас: string join (Sprint 2 → реальный LLM)     │
│      Future: Essence Layer → короткая суть + цепочка   │
│      смысла + WhyTrace                                  │
│      Future: AttentionRouter + NoeticCore → фокус,      │
│      причинность, прогнозы как hypotheses               │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
👤 Ответ: "Квантовая запутанность связывает частицы..."
   + trace: [f2 | source=physics | state=Validated | bm25=1.23]
```

---

## 🧠 Как устроена память (memory.py)

Память — это сердце системы. Каждый факт проходит жизненный цикл:

```
                    🌱 ЖИЗНЬ ФАКТА
                    ─────────────

  Наблюдаем         Изучаем          Проверяем
  ──────────        ─────────        ──────────
  Observed ──────► Hypothesized ──► Supported ──► Validated ──► ImmutableCore
     │                  │               │               │        (только Ring Zero)
     │                  │               │               │
     └──────────────────┴───────────────┴──► Contradicted ──► Deprecated ──► Collapsed
                                                (конфликт)      (устарел)    (забыт)

  Правила:
  ✅ Переходить можно только в разрешённых направлениях
  ✅ Из Collapsed и ImmutableCore — выхода нет (терминальные)
  ✅ Изменить state можно ТОЛЬКО через transition_esm()
  ❌ Нельзя: UPDATE facts SET epistemic_state = 'Validated' напрямую
  ❌ Нельзя: fact["epistemic_state"] = "Validated" в коде
```

### Три слоя хранения

```
  ┌──────────────────────────────────────────────────┐
  │  L0 — Рабочий стол (в памяти компьютера)        │
  │  128 самых свежих фактов · OrderedDict (LRU)    │
  │  Самый быстрый доступ — без обращения к диску   │
  └──────────────────────┬───────────────────────────┘
                         │ промах кэша
                         ▼
  ┌──────────────────────────────────────────────────┐
  │  L1 — Архив (SQLite на диске)                   │
  │  Все факты персистентно · история переходов     │
  │  + bi-temporal: когда узнали / когда стало правдой│
  └──────────────────────┬───────────────────────────┘
                         │ Sprint 2
                         ▼
  ┌──────────────────────────────────────────────────┐
  │  L3 — Граф знаний (Neo4j) — ещё не подключён   │
  │  Отношения между фактами · семантический поиск  │
  │  GraphStore ABC уже готов — ждёт реализации     │
  └──────────────────────────────────────────────────┘
```

### Bi-temporal поля (новое в v8.2.0, инвариант I96)

Каждый факт знает **два времени** — это позволяет задавать вопрос
«а что система знала три месяца назад?»:

```
  fact = {
    "claim": "Земля вращается вокруг Солнца",
    "source": "astronomy",

    # Когда факт стал правдой в мире:
    "t_event_valid_start": "2026-01-01T...",   ← с этого момента истина
    "t_event_valid_end":   null,               ← null = всё ещё истина

    # Когда система об этом узнала:
    "t_ingestion_start":   "2026-01-15T...",   ← когда записали
    "t_ingestion_end":     null,               ← null = всё ещё верим
  }

  # Time-travel запрос: что я знал 1 февраля?
  store.get_fact_at("f3", known_at="2026-02-01", world_at="2026-02-01")
```

### Ring Zero — неизменяемое ядро

```
  IMMUTABLE_FACT_IDS = {"VALUES_CORE", "RING_ZERO"}
  │
  ├── VALUES_CORE — ценности системы (нельзя изменить, нельзя удалить)
  └── RING_ZERO   — базовые аксиомы (нельзя перевести даже в Contradicted)

  Попытка вызвать transition_esm("VALUES_CORE", ...) → ImmutableStateError
  Инвариант I6: Ring Zero immutable навсегда.
```

---

## 📜 Что такое GraphStore ABC (storage.py)

Это **контракт** — список правил который должна выполнять любая БД в системе.
Сейчас работает SQLite. В Sprint 2 придёт Neo4j. Благодаря контракту
остальной код не заметит замену — он говорит на языке контракта, а не SQLite.

```
  GraphStore (контракт)          SQLiteGraphStore (реализация сейчас)
  ─────────────────────          ─────────────────────────────────────
  store_fact()          ──────►  INSERT INTO facts ... ON CONFLICT DO UPDATE
  get_fact()            ──────►  SELECT * FROM facts WHERE fact_id = ?
  get_all_facts()       ──────►  SELECT * FROM facts (+ фильтр по state)
  update_state()        ──────►  UPDATE facts SET epistemic_state = ... (атомарно)
  get_fact_at()         ──────►  SELECT с bi-temporal фильтрами (I96)
  invalidate_edge()     ──────►  SET t_*_end (никогда DELETE!)
  search()              ──────►  LIKE по claim (заглушка → Sprint 2 semantic)

                                 Neo4jGraphStore (Sprint 2 — ещё не написан)
                                 ──────────────────────────────────────────
                                 Cypher MATCH / MERGE / SET (реальный граф)
```

---

## 🔍 Что делает trace.py

Trace — это **журнал расследования**. Каждый раз когда система даёт ответ,
она записывает: откуда пришёл каждый факт, с каким уровнем доверия,
и в каком состоянии ESM он находился.

```
  Trace-элемент = {
    "fact_id":           "f2",
    "source":            "physics",
    "origin":            "retrieval",      ← как попал (retrieval / ingestion / volition)
    "epistemic_state":   "Validated",      ← статус в момент использования
    "retrieval_score":   1.23,             ← BM25-балл (query-зависимый, не сохраняется)
    "source_confidence": 0.85,             ← доверие источника (стабильное, сохраняется)
    "retrieved_at":      "2026-05-11T...", ← когда извлекли
    "promoted_at":       "2026-05-11T...", ← когда перевели в Validated
    "promoted_by":       "pipeline.run",   ← кто перевёл (аудит)
  }
```

Разница между `retrieval_score` и `source_confidence` важна:
- `retrieval_score` — насколько факт подходит под этот конкретный запрос (меняется)
- `source_confidence` — насколько мы доверяем источнику вообще (стабильная)

---

## 🔧 Инструменты миграции — зачем они нужны

```
  V8 Crystal Specification (markdown, 18 784 строки)
         │
         │  velantrim_migrate_v3_1.py
         │  ├── Разбивает на чанки (каждый раздел = чанк)
         │  ├── Кириллица → ASCII в ID (привет_мир → privet_mir)
         │  ├── Извлекает RFC упоминания
         │  ├── Присваивает layer (L0/L1/L2/L3...)
         │  └── Backup + rollback + dry-run
         ▼
  Velantrim_V8_Crystal_Sprint1.jsonl  ← 63 чанка, ~948KB
         │
         │  fill_dependencies.py
         │  └── Находит RFC ссылки в тексте → заполняет depends_on
         ▼
  База знаний с зависимостями   ← готова для векторного поиска
         │
         │  audit_metadata.py / check_rfc_duplicates.py
         └── Проверяют качество: нет ли дублей, null полей, мега-блобов

  utils/rfc_parser.py — используется обоими инструментами:
  ├── extract_rfc("...RFC0067 v2.0...")   → "RFC0067 v2.0"
  └── extract_rfc_mentions("RFC0036–0051") → [RFC0036, RFC0037, ..., RFC0051]
```

---

## 🧪 Тесты — кто за что отвечает

```
  tests/
  │
  ├── test_esm.py (44 теста) ─────────────────────────────────────────────┐
  │   Проверяет memory.py                                                  │
  │   ✅ 8 состояний ESM ровно                                             │
  │   ✅ Переходы только по разрешённым путям                              │
  │   ✅ Ring Zero нельзя изменить (I6)                                    │
  │   ✅ Новые факты только в Observed (I50)                               │
  │   ✅ Drift protection: claim изменился у Validated → Contradicted      │
  │   ✅ Bi-temporal поля установлены при создании (I96)                   │
  │   ✅ invalidate_edge не удаляет, только ставит t_*_end                 │
  │   ✅ get_fact_at возвращает факт в нужный момент времени               │
  │   ✅ Collapsed устанавливает t_ingestion_end                           │
  │   ✅ LRU кэш: 128 слотов, вытесняет старое, чтение освежает           │
  │   ✅ history: каждый переход записывается с caller'ом                  │
  │   ✅ deepcopy: внешняя мутация не корруптит L0                        │
  │                                                                         │
  ├── test_pipeline.py (19 тестов) ────────────────────────────────────────┤
  │   Проверяет pipeline.py + trace.py                                     │
  │   ✅ Happy path: вопрос → факты Validated → ответ                      │
  │   ✅ Нет совпадений → блокировка, не падение                           │
  │   ✅ Повторный запрос не падает (idempotency)                           │
  │   ✅ Три запроса подряд — одинаковый ответ                             │
  │   ✅ tokenize("...") → [] (не [""])                                    │
  │   ✅ em-dash, en-dash, дефис разделяют слова                           │
  │   ✅ retrieval_score ≠ source_confidence                               │
  │   ✅ Guardian блокирует если fact не покрыт trace                      │
  │   ✅ TruthGate блокирует низкий confidence                             │
  │   ✅ promote_trace записывает promoted_by                              │
  │                                                                         │
  ├── test_regression_p0.py (7 тестов) ────────────────────────────────────┤
  │   Проверяет что старые баги не вернулись                               │
  │   ✅ P0.1: повторный store_fact не сбрасывает Validated → Observed     │
  │   ✅ P0.3: get_all_facts прогревает L0 кэш                            │
  │   ✅ Два отдельных SQLiteGraphStore → две отдельных БД                 │
  │   ✅ pipeline.run() дважды подряд — не падает                          │
  │   ✅ Collapsed устанавливает t_ingestion_end (новое)                   │
  │   ✅ invalidate_edge не удаляет факт                                   │
  │                                                                         │
  └── test_sprint_a_wiring.py ─────────────────────────────────────────────┘
      🛡️ Страж-тест
      НЕ проверяет функциональность — проверяет ОТСУТСТВИЕ
      Читает core/*.py через AST (абстрактное синтаксическое дерево)
      и убеждается что event_bus, lock_manager, circuit_breaker,
      rate_limiter, health_check — НЕ импортированы ни в одном файле.
      Если кто-то случайно подключит A6-A10 раньше времени →
      этот тест упадёт и предупредит команду.
```

---

## 📚 Документы — что читать, что обновлять

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │  ЧИТАТЬ при онбординге (в таком порядке)                           │
  │                                                                     │
  │  1. README.md        ← главная страница, честный статус системы    │
  │  2. SYSTEM_OVERVIEW.md ← этот файл, как всё работает              │
  │  3. ROADMAP.md       ← что сделано, что впереди по спринтам       │
  │  4. INVARIANTS.md    ← правила которые нельзя нарушать            │
  │  5. LIMITATIONS.md   ← что ещё не работает и почему               │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ОБНОВЛЯТЬ при каждом спринте                                      │
  │                                                                     │
  │  README.md       ← версия, таблица файлов, список исправлений      │
  │  ROADMAP.md      ← переносить пункты из "planned" в "done"        │
  │  INVARIANTS.md   ← добавлять новые инварианты при их реализации    │
  │  LIMITATIONS.md  ← убирать закрытые ограничения                   │
  │  WORK_SUMMARY.md ← журнал: что сделано в этом спринте             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  НЕ ТРОГАТЬ (исторические артефакты)                               │
  │                                                                     │
  │  AUDIT_DIFF_REPORT.md   ← зафиксированный diff v8.0.2 → v8.0.3   │
  │  METADATA_FIX_REPORT.md ← зафиксированный отчёт по JSONL          │
  │  audit_issues.json      ← результат конкретного аудита            │
  │  validate_dangling.json ← результат конкретной проверки           │
  │  velantrim_migration.log ← лог конкретного запуска                │
  │  SANDBOX_CLONE.md       ← описание этого клона (Duan)             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ОБНОВЛЯТЬ при подключении A6-A10 (Sprint 2c)                      │
  │                                                                     │
  │  SPRINT_A_NOTES.md ← замечания по патчам                          │
  │  test_sprint_a_wiring.py ← удалить sentinel, создать интеграционный│
  └─────────────────────────────────────────────────────────────────────┘
```

---

## ⏳ Что работает сейчас vs что впереди

```
  ✅ РАБОТАЕТ ПРЯМО СЕЙЧАС (v8.3.1)
  ──────────────────────────────────────
  🧠 memory.py      ESM (8 состояний), L0 LRU, L1 SQLite
                    Bi-temporal поля (I96)
                    Ring Zero иммутабельность (I6)
                    TRUSTED_SOURCES whitelist (I98) — ring_zero/domain_seed/system_axiom
                    Drift protection (TASK-02) + L0/L1 sync (I104, v8.3.1)
                    Audit trail (history + by)

  🔍 trace.py       Провенанс цепочка
                    Атомарный promote (two-pass)
                    Разделение retrieval_score / source_confidence

  📜 storage.py     GraphStore ABC (контракт для будущих бэкендов)
                    Bi-temporal методы в контракте

  ⚙️ pipeline.py    BM25 Okapi retrieval
                    Guardian + TruthGate (MVP placeholder в pipeline)
                    Idempotent run()

  🔐 truth_gate.py  Реальный Truth Gate (v8.3.1) — заменяет placeholder I68
                    Mode-aware: PRECISION / BALANCED / EXPLORATION / CREATIVE
                    4 проверки: source + confidence + evidence + contradictions
                    Готов к интеграции в pipeline.py (Sprint 2b)

  🔎 hybrid_retriever.py
                    BM25 + Dense Embeddings + RRF (v8.3.1)
                    Graceful degradation если зависимости не установлены
                    Готов заменить BM25-only в pipeline.py (Sprint 2a)

  📊 mhi.py         Memory Health Index (v8.3.1) — закрывает RFC0070 stub
                    HEALTHY / DEGRADED / SAFE_MODE
                    Автоматические рекомендации для Meta-Supervisor

  📚 ngram_index.py NGramIndex L0 Pre-Filter (FTS5 trigram, O(log N), I99)
                    Graceful degradation если FTS5 недоступен

  💤 sleep_time_worker.py
                    SleepTimeWorker + CoreMemoryBlocks (I100-I103)
                    Активный think() в idle-цикле
                    LLM mock → Sprint 2c заменить на реальный async client

  🗂️ embedding_registry.py
                    EmbeddingRegistry: 17 моделей, защита от dim-mismatch

  🧪 tests/         682 теста собрано · ✅ 652 passed, 0 failed, 17 skipped, 13 xfailed
                    (проверено 2026-05-30, Python 3.12, 16.5 мин — реально ЗЕЛЁНЫЙ)
                    coverage core/ = 56% (НЕ 87%): ядро 85-100% (memory/truth_gate/
                    trace/storage/causal), но периферия не покрыта; порог 80% не достигнут

  🔧 tooling/       Миграция V8 → JSONL (v3.1)
                    Аудит и заполнение зависимостей


  🚧 SPRINT 2 (следующий)
  ────────────────────────
  🗄️ S2a  HybridRetriever (BM25 + vector + HotGraph)
  🗄️ S2b  SQLite FTS5, убрать mock DATABASE из pipeline
  🔄 S2c  async/await + aiosqlite
  🔄 S2c  A6-A10 подключить (EventBus, LockManager, ...)
  🗄️ S2c  Neo4jGraphStore реализация


  📋 SPRINT 3+
  ─────────────
  🌱 S3   RFC0066 ConceptEmergence (ProtoConcept, Hebbian)
  🗳️ S3   RFC0065 Memory Volition (write_voluntary)
  🎨 S4   RFC0067 v2.0 Analogy Graph
  📚 S4   RFC0063 Knowledge Ingestion Pipeline
  🧠 S5+  RFC0068 NeuroCore (plastic memory, Phase 0)
```

---

## 🔑 Три главных принципа — почему архитектура именно такая

```
  1. Graph = Truth
     ─────────────
     Neo4j граф — единственный источник истины.
     LLM говорит красиво, но не решает что правда.
     Факт попадает в граф только пройдя Truth Gate.
     Нет Truth Gate → нет записи. Без исключений.

  2. Memory = Physiology
     ────────────────────
     Память устроена как биологическая:
     L0 = рабочая память (быстро, мало)
     L1 = эпизодическая (дольше, полнее)
     L3 = долгосрочная (постоянно, структурированно)
     Факты не живут вечно — они стареют (FSRS decay, Sprint 2)

  3. Dual-Process
     ─────────────
     Fast Path (миллисекунды) — пользователь ждёт, отвечаем быстро
     Slow Path (фон, async)   — консолидация, обучение, GC
     Никакой тяжёлой работы в Fast Path. I28: ResponseAuditWorker
     только в Slow Path. Это не договорённость — это инвариант.
```

---

> **Graph = Truth · LLM = Language · Memory = Physiology · Volition = Agency**
>
> Velantrim — не «ещё один memory layer».
> Это недостающее звено между LLM, Graph и RAG.
