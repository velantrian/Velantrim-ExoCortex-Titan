# CHANGELOG — Velantrim ExoCortex

> Формат: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
> Один файл. История всех версий. Подробности — в git log.

---

## [9.0.0] — 2026-07-09 — VELANTRIM TITAN 9.0 (version unification)

Публичный ребрендинг: продукт называется и выглядит как **Velantrim Titan 9.0** во всех
главных entrypoint-файлах. Функционально это тот же рантайм, что и 8.7.0 — изменения ниже
чисто версионные/косметические, без изменения API-логики.

### Изменено
- `pyproject.toml` — `version` → `9.0.0`; `name` → `velantrim-titan` (было `velantrim-v8-7-titan`);
  `core/__init__.py` синхронизирован с новым именем дистрибутива.
- `server.py` — заголовок, `FastAPI(title=..., version=...)` и JSON-ответы `/` и `/api` теперь
  используют `core.__version__` вместо захардкоженной строки; убраны видимые упоминания V8.7.
- `README.md`, `README.en.md` — заголовок и версия обновлены на Titan 9.0; убрано "100%
  hallucination-free"-подобных формулировок (их и не было); добавлены формулировки
  local-first verifiable memory runtime / evidence-gated AI memory / auditable provenance /
  truth-bound generation / research-grade prototype moving toward production hardening.
- `Dockerfile`, `docker-compose.yml` — image/container переименованы в `velantrim-titan`;
  `docker-compose.yml` (production) теперь требует явный `VELANTRIM_API_KEY`
  (`${VELANTRIM_API_KEY:?...}`), permissive dev-ключ вынесен в новый `docker-compose.dev.yml`.
- `.github/workflows/ci.yml` — имя workflow обновлено на "CI — Velantrim Titan 9.0".
- `docs/AUDIT_V8_6.ru.md`, `docs/MIGRATION_V8.6_TO_CANON.ru.md` — помечены как legacy-заметки
  (оставлены на месте — на них есть активные ссылки из нескольких документов).

### Намеренно не изменено
- `core/crypto.py` `_KDF_SALT` — исторический литерал с "v8-7" внутри; это фиксированная соль
  KDF для encryption-at-rest. Смена изменила бы производные ключи и сделала бы нечитаемыми уже
  зашифрованные данные. Оставлено намеренно.
- Комментарии вида `# v8.7 audit`, `# FIX P1 (v8.7 audit)` в `core/*.py` и `server.py` — это
  ссылки на конкретные исторические аудит-фиксы, документируют WHY конкретного кода, а не
  бренд продукта.
- `CANONICAL.md`, `Velantrim_Project_Map.md`, журналы (`WORK_LOG.md`, `COLLAB_JOURNAL.md`,
  `AUDIT_ACTION_ITEMS.md`, `AUDIT_DEEP_2026-06-06.md`, `ROADMAP.md`) — историческая хроника,
  версии в них документируют факты о прошлом, а не текущий бренд.

## [8.7.0] — 2026-06-03 — VELANTRIM V8.7 Titan

### 🛡️ Иммунная система (из Crystal)
- **`core/meta_supervisor.py`** — HEALTHY/DEGRADED/SAFE_MODE. Heartbeat 10 сек. L3 read-only при критической деградации
- **`core/immutable_core_scheduler.py`** — SHA-256 дельта-снапшоты графа каждые 24ч
- **`core/provenance_chain.py`** — Append-only hash-chain. Блокчейн для памяти. Verify() — математическая проверка
- **`core/atomic_split.py`** — I91: один смысл = один факт. Multi-proposition → атомы перед TruthGate
- **`tests/test_invariants.py`** — 18 исполняемых инвариантов. Падение → деплой заблокирован

### 🧬 Ось идентичности (из v80.5 + ChatGPT)
- **`core/identity_layer.py`** — F1–F4: VALUES / WORLDVIEW / BIOGRAPHY / COMPASS. self_axis 0..1
- **`core/stimulus_map.py`** — Двусторонняя трассируемость: стимул ↔ факт ↔ ответ
- **`core/forgetting.py`** — GDPR «right to be forgotten» + PII redaction
- **`core/memory_archival.py`** — Архивация старых фактов в JSON
- **`core/cognitive_fact.py`** — +node_type, +truth_scope, +self_axis, +source_message_id, +provenance

### 🚀 Инфраструктура и Production
- **`Dockerfile`** + **`docker-compose.yml`** — деплой одной командой
- **`core/async_store.py`** — aiosqlite + run_in_executor. Event loop не блокируется
- **`core/metrics.py`** — Prometheus-метрики + `/health` эндпоинт
- **`core/rate_limit.py`** — Token-bucket per-IP
- **`core/app.py`** — VelantrimApp — DI-фундамент. Обратная совместимость через get_app()

### 🧠 Когнитивное усиление (из Synapse + Claude Code L4,L5)
- **`core/reasoning_bank.py`** — +LRU eviction (max 500). Защита от OOM при долгом аптайме
- **`core/negative_reinforcement.py`** — Anti-pattern detection + penalty escalation
- **`core/contradiction_registry.py`** — NLI cross-encoder (DeBERTa-v3) + CRISPR-спейсеры
- **`core/meaning_parser.py`** — Verbatim + Gist dual encoding (Fuzzy-Trace Theory)
- **`core/question_formula.py`** — 29 формул вопроса. Rule-based, 0 токенов LLM
- **`core/curiosity_engine.py`** — 4 типа любознательности. Активный стимул к исследованию
- **`core/interoception.py`** — +PAD-модель эмоций (valance-arousal-dominance)

### 🔍 Retrieval и поиск
- **`core/lemmatizer_ru.py`** — pymorphy3 + Snowball. Recall +30-50% для русского. +@lru_cache
- **`core/index_coordinator.py`** — Синхронизация FTS5 + BM25
- **`core/evidence_counter.py`** — Реальный подсчёт evidence
- **`core/hybrid_retriever.py`** — +retrieve_5stage() + ego_net_expand (multi-hop без LLM)
- **`core/text_utils.py`** — +extract_json_from_text() — извлечение JSON из смешанного LLM-вывода

### 🎛️ LLM-каталог (только актуальные)
- **`core/provider_catalog.py`** — обновлён до актуальных моделей. Удалены все старые.
  Claude Sonnet 4.6 + Opus 4.8, GPT-5.5, DeepSeek V4, Qwen 3.7 Max+Plus, Gemini 3.5 Flash.

### 📄 Документация
- **`research/FUTURE_COMPONENTS.md`** — KDE, MemoryRouter, Qwen3-Reranker, IndexRAG, AGRAG, CRAG, ReRAG, BranchManager, StepVerifier, L15 Observer
- **`research/ARCHITECTURE_AXES.md`** — 4 ортогональные оси памяти
- **`research/DEPRECATIONS.md`** — Журнал устаревших технологий (14 записей)
- **`ROADMAP.md`** — секция V8.7 Titan COMPLETED
- **`README.md`** + **`SYSTEM_OVERVIEW.md`** — обновлены до V8.7

---

## [8.6.0] — 2026-05-21 — VELANTRIM V8.6 Complex

- **Titan v7.5 port (май 2026):** `output_faithfulness`, `memory_budget`, `circuit_breaker`, `response_guardian`, `actr_activation` — ENV-флаги `ENABLE_*`, интеграция в pipeline/LLM/audit; тесты `tests/test_titan_port.py`
- **ExoCortex L1.5–L5.5** перенесены из `Graphiti_fractal-main` (`velum`, `etir`, `immutable_core`, `concept_emergence`, `l45_bridge`, `predictive_fusion`, `decay_orchestrator`, `storage_facade`, backends)
- **`core/feature_config.py`** — единые ENV-флаги; `runtime_flags` делегирует в него
- **Интеграция:** `exocortex_hooks` (ingest + pipeline enrich), `event_bridge` (+ L45 handlers), `api/exocortex_api.py`
- API: `/layers/status`, `/etir/activate`, `/focus`, `/audit/recent`, `/immutable/snapshots`, `/welfare`, `/memory/volition`, `/eventbus/metrics`
- **L6 Horizons MVP:** `welfare_monitor`, `volition_gate`, `l6_bridge`, `memory_volition`, `event_bus`
- Тесты: `tests/test_exocortex_import.py`, `tests/test_l6_welfare.py` (полный suite: 543 passed)
- Аудит: `docs/AUDIT_V8_6.ru.md`
- P1: `causal_persistence`, `async_utils`, `pip install -e .`, L6 flags → `runtime_flags`
- Спринт 1: `fact_integrity`, `consolidation_engine`, `POST /memory/consolidate`, episode dedup
- Документация Horizons: полный набор карточек `docs/horizons/` (L2.5, R2–R5, E1–E7, KDE, L6), `GET /horizons`, `GET /layers/status`
- Исправления: `get_causal_graph` / `is_causal_graph_enabled`, `on_causal_relation` в EventBus
- Тесты: `test_exocortex_e2e`, `test_exocortex_flags_matrix`, `test_causal_bridge`; CI `.github/workflows/ci.yml`
- Dev-профиль: `config/exocortex-dev.env`; OpenAPI для ExoCortex; `QueryResponse.exocortex_sections`
- **Innenwelt MVP:** `goal_stack`, `gap_detector`, `interoception` (somatic_marker), API `/goals`, `/gaps`, `/innenwelt`; `QueryResponse.gaps` + `innenwelt`; `ENABLE_INNENWELT=1`
- **ModeRouter MVP:** `core/router/` (PERSONAL, VELANTRIM, UMWELT), `response_lens` в `POST /query`, `/router/modes`, `/router/route`; `ENABLE_MODE_ROUTER=1`
- **Umwelt store MVP:** `umwelt_store` (layer 99), `docs/seed/umwelt_mvp_seed.json`, API `/umwelt/*`, интеграция с `UMWELT` линзой; `ENABLE_UMWELT_STORE=1`
- **Telegram → L0 (2.6):** `app/telegram_ingest.py`, polling `python -m app.telegram_bot`, `/telegram/ingest`, `/telegram/webhook`; `ENABLE_TELEGRAM_INGEST=1`
- **CognitiveFact v9.1 + domain tags:** `core/cognitive_fact.py`, `core/domain_tags.py`, `GET /facts/{id}/cognitive`, `domain` в query/facts
- **CognitiveFactStore v9.2–9.3:** `core/cognitive_store.py`, `POST/GET /cognitive/facts`, `POST /facts` через store; `ENABLE_COGNITIVE_STORE=1`; гидратация L0 через `get_raw_text_for_fact`
- **Relations preview v9.7 (3.3):** `GET /facts/{id}/relations`, `include_relations` в CognitiveFact
- **Graphiti adapter (2.5):** `core/graphiti_adapter.py`, `POST /causal/reload-from-graph`, `CausalGraph.import_snapshots`
- **Ingest → CognitiveFactStore:** Telegram и `sync_perceptions_to_memory` через `save_fact_dict`
- **Unified Cognitive Runtime V10 MVP:** `core/cognitive_runtime.py`, `ENABLE_COGNITIVE_RUNTIME`, fact_* → `mark_retriever_dirty`
- **PolyWeltRegistry (6 agents):** `core/poly_welt_registry.py`, `GET /umwelt/agents`, расширен seed
- **CrossDomain V3 MVP:** `core/cross_domain.py`, `ENABLE_CROSS_DOMAIN`, NGram инкремент в runtime; smart routing, `ENABLE_CROSS_DOMAIN_CAUSAL`, опц. `ENABLE_CROSS_DOMAIN_LLM_ROUTING`

## [8.5.1-patch7] — 2026-05-19 — Deep Audit Patch Series

> **Аудиторы:** Claude Sonnet 4.6 (импорт-граф, runtime, интеграция) + ChatGPT (pytest прогон)
> **Метод:** Глубокий аудит → WORK_LOG.md → патчи по задачам → 498 тестов, 0 failures

### ✅ P0: Сломано прямо сейчас
- **TASK-01** `NGramIndex.available` property вызывался как метод → `TypeError` при CI.
- **TASK-02** Coverage target `--cov=file_parsers` → убран `CoverageWarning`.
- **TASK-03** `datetime.utcnow()` → `datetime.now(timezone.utc)` в `velantrim_reports/*.py`.

### ✅ P1: Performance и архитектурные мины
- **TASK-04** `mark_retriever_dirty()` на каждом `/query`. `store_fact()` → `bool` (was_new). **40x** ускорение повторных запросов.
- **TASK-05** Двойная запись `store_fact()` для существующих фактов. No-op guard.
- **TASK-06** `get_all_facts()` без LIMIT → `get_fact_ids()` + `get_facts_by_ids()`.
- **TASK-07** `DATABASE_DEV_ONLY` fallback убран из production. Пустой store → честный `[]`.

### ✅ P2: Интеграция написанного
- **TASK-08** CausalGraph в `pipeline.run()`. Regex-экстрактор каузальных паттернов. `causal_hints` в ответе.
- **TASK-09** L0 Raw Memory в `POST /facts` и `POST /ingest/text`. `facts.derived_from` заполняется.
- **TASK-10** `find_contradictions()` cycle protection (`_visited_facts: set`).
- **TASK-11** `causal_chain()` BFS: `list.pop(0)` O(n) → `deque.popleft()` O(1).
- **TASK-12** `pipeline.build_facts_pack()` → `FactsPackBuilder` с CognitiveMode-политиками.

### ✅ P3: Гигиена
- **TASK-13** 4 CHANGELOG → один (этот файл).
- **TASK-14** `Diary/` → `docs/seed/`. `docs/ЗАПУСК.md` → `docs/RUN.ru.md`.
- **TASK-15** `.coverage` удалён из дистрибутива.

### 📊 Метрики патч-серии

| Метрика | До | После |
|---------|-----|-------|
| Падающие тесты | 1 (`TypeError`) | 0 |
| `/query` latency (повторный) | 1-2 сек | 20-50ms |
| CausalGraph в pipeline | ❌ orphan | ✅ `causal_hints` |
| L0 Raw Memory | ❌ пустые таблицы | ✅ `derived_from` при ingest |
| `get_all_facts()` | вся БД в RAM | top-K fetch |

---

## [8.5.3] — Май 2026 — Orphan Wiring + Concurrency Hardening

> **Аудиторы:** Claude Opus 4.7, Gemini, DeepSeek/Qwen/ChatGPT

### 🐛 Исправлено
- SleepTimeWorker concurrency: `_bg_tasks: set` для asyncio-задач, защита от GC.
- CausalGraph: graceful degradation при отсутствии таблицы `relations`.
- FileIngester: архивная вложенность `max_depth` + singleton double-checked locking.
- `core/validators.py`: `validate_source()` / `validate_confidence()` выделены.
- FORWARD/BACKWARD relation types: разделение с explicit `inference_source`.
- 12 тестов помечены `xfail` с явным reason'ом вместо silent skip.

---

## [8.5.2] — Май 2026 — Cross-AI Audit Hotfix

> **Аудиторы:** Claude Opus 4.7, ChatGPT, Gemini
> До: 17.5% failure rate. После: 0%.

### 🐛 Исправлено (P0)
- `core.pipeline` NameError при импорте: `DATABASE` → `_DATABASE_DEV_ONLY` (неполное переименование).
- `Theme` dataclass: `font_body_bold/italic` отсутствовали → `TypeError` → весь `core.file_generators` падал.
- CausalGraph: 6 из 12 backward relation types терялись silently.
- TruthKernel: 7 тестов ловили `Exception` вместо `VelantrimError`.
- `temporal_decay`: формула, docstring и тест расходились.
- `test_knowledge_ingester`: ссылался на удалённый `KnowledgeIngesterV5`.

---

## [8.5.1] — Май 2026 — Patch 13: Causal Graph

### ✨ Добавлено
- `core/causal_graph.py` — 15 типов связей + backward-инверсии + `knowledge_status`.
- `migrations/008_add_relations.sql`, `migrations/010_raw_memory.sql`.
- `core/raw_memory.py`, `core/facts_pack.py`, `core/understanding_layer.py`.
- `core/living_context.py`, `core/affordance_linker.py`, `core/audit_chain.py`.

---

## [8.4.0] — Май 2026 — Audit Fix Release

> 5-раундовый аудит (Claude Opus 4.7). 7 production-blockers.

### 🐛 Исправлено
- SleepTimeWorker не запускался (TypeError), /agent/* → 503.
- NGramIndex split: server и pipeline писали в разные БД.
- HybridRetriever per-request init заменён на singleton.
- Bi-temporal поля добавлены в DDL и `store_fact()`.
- ESM idempotency: `Validated → Validated` больше не падает.
- Actor spoofing: `req.by` игнорируется, actor = `sha256(key)[:8]`.

---

## [8.3.x и ранее]

- v8.3: drift protection, split-brain fix L0/L1, Ring Zero invariants
- v8.2: bi-temporal model (I96), `store_facts_batch()`, time-travel queries
- v8.1: HybridRetriever (BM25 + Dense + RRF), NGramIndex pre-filter
- v8.0: первый рабочий pipeline (Query → Retrieval → TruthGate → Answer)
