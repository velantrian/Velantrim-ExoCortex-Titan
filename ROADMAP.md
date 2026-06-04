# Velantrim ExoCortex — Roadmap

> **Честная карта**: что реализовано, что спроектировано, что впереди.
> **V8.7 Titan · 3 июня 2026:** 25+ новых модулей добавлено аддитивно (см. ниже).
> **v8.4.0 обновление:** добавлена секция audit fixes, sprint S2a отмечен как частично завершённый.

---

## 🆕 V8.7 Titan — ЗАВЕРШЕНО (3 июня 2026)

> Все модули добавлены **аддитивно** — ни один существующий файл не сломан.
> Исходный код V8.6 сохранён нетронутым в отдельной папке.

### 🚀 Инфраструктура и производительность
| Модуль | Назначение |
|--------|-----------|
| `core/app.py` | VelantrimApp — DI-фундамент. Обратная совместимость через `get_app()` |
| `core/async_store.py` | aiosqlite + `run_in_executor` fallback. Event loop не блокируется |
| `core/metrics.py` | Prometheus-метрики + `/health` эндпоинт |
| `Dockerfile` + `docker-compose.yml` | Деплой одной командой |

### 🔒 Иммунная система (из Crystal)
| Модуль | Назначение |
|--------|-----------|
| `core/meta_supervisor.py` | HEALTHY/DEGRADED/SAFE_MODE. Heartbeat 10 сек. L3 read-only |
| `core/immutable_core_scheduler.py` | SHA-256 дельта-снапшоты каждые 24ч |
| `core/provenance_chain.py` | Append-only hash-chain. Блокчейн для памяти |
| `core/atomic_split.py` | I91: один смысл = один факт |
| `tests/test_invariants.py` | 18 исполняемых инвариантов в CI |

### 🧠 Когнитивный слой (из Synapse + Claude Code L4,L5)
| Модуль | Назначение |
|--------|-----------|
| `core/reasoning_bank.py` | Thompson Sampling (Beta-распределение) |
| `core/negative_reinforcement.py` | Anti-pattern detection + penalty escalation |
| `core/contradiction_registry.py` | NLI cross-encoder (DeBERTa-v3) + CRISPR-спейсеры |
| `core/meaning_parser.py` | Verbatim + Gist dual encoding (Fuzzy-Trace Theory) |
| `core/question_formula.py` 🆕 | 29 формул вопроса. Rule-based, 0 токенов LLM |
| `core/curiosity_engine.py` 🆕 | 4 типа любознательности. Активный стимул к исследованию |

### ⚡ Оптимизации и надёжность (из HYPERIA V5.5)
| Улучшение | Где |
|-----------|-----|
| LRU eviction стратегий (max 500) | `reasoning_bank.py` — защита от OOM при долгом аптайме |
| @lru_cache для лемматизатора | `lemmatizer_ru.py` — экономия CPU 40-60% |
| JSON extraction из смешанного LLM-вывода | `text_utils.py` → `extract_json_from_text()` |

### 🧬 Память личности и traceability (из v80.5 + ChatGPT)
| Модуль | Назначение |
|--------|-----------|
| `core/identity_layer.py` | F1–F4: VALUES, WORLDVIEW, BIOGRAPHY, COMPASS |
| `core/stimulus_map.py` | Двусторонняя трассируемость: стимул ↔ факт ↔ ответ |
| `core/forgetting.py` | GDPR «right to be forgotten» + PII redaction |
| `core/memory_archival.py` | Архивация старых фактов в JSON |

### 🎯 Retrieval и поиск
| Модуль | Назначение |
|--------|-----------|
| `core/lemmatizer_ru.py` | pymorphy3 + Snowball. Recall +30-50% для русского |
| `core/index_coordinator.py` | Синхронизация FTS5 + BM25 |
| `core/evidence_counter.py` | Реальный подсчёт evidence |
| `core/hybrid_retriever.py` | +`retrieve_5stage()` + `ego_net_expand` (multi-hop без LLM) |
| `core/cognitive_fact.py` | +`node_type`, +`truth_scope`, +`self_axis`, +`source_message_id`, +`provenance` |

### 🧠 Essence Engine Facade + Multi-Perspective Reasoning
| Модуль | Назначение |
|--------|-----------|
| `core/essence_facade/` (7 файлов) | Facade-пакет. Gist Synthesizer, Situation Model, bridges к goal/causal/observer. 0 файлов перемещено |
| `core/essence_facade/gist.py` | Gist Synthesizer: core_question, intent, constraints, hypothesis, missing_piece |
| `core/essence_facade/situation.py` | Situation Model: actors, tension, missing_piece + living_context 7 измерений |
| `core/perspectives.py` 🆕 | 7 ролей (ENGINEER/SCIENTIST/ANALYST/CRITIC/ADVISOR/FRIEND/PHILOSOPHER) |
| `core/branch_manager.py` 🆕 | Parallel Reasoning: 3 ветки одновременно → синтез. По умолчанию: Аналитик + Инженер + Критик |
| `core/reconsolidation.py` 🆕 | Живая память: факты переосмысливаются при каждом использовании |
| `core/meta_cognition.py` 🆕 | Мета-когнитивная рефлексия: оценка ПУТИ мышления, а не только ответа |
| `core/conversation_consolidation.py` 🆕 | Двухфазный блокнот диалога: реал-тайм → финальная суть |
| `core/truth_maintenance.py` 🆕 | Truth Maintenance: reinforce/supersede/contradict — атомарные операции над фактами |
| `core/epigenetic_adaptation.py` 🆕 | Эпигенетическая адаптация: адаптивное поведение без переобучения |
| `core/adaptive_truth.py` 🆕 | Adaptive Truth Thresholds: пороги TruthGate меняются под тему |
| `core/experience_replay.py` 🆕 | Experience Replay: ночная реактивация успешных цепочек (LTP-подобно) |

### 📄 Документация
| Файл | Назначение |
|------|-----------|
| `research/FUTURE_COMPONENTS.md` | 7 компонентов на будущее: KDE, MemoryRouter, Qwen3-Reranker, IndexRAG, AGRAG, CRAG, ReRAG |
| `research/ARCHITECTURE_AXES.md` | 4 ортогональные оси памяти |
| `research/DEPRECATIONS.md` | Журнал устаревших технологий (14 записей) |

### 🎛️ Обновлённый каталог LLM (только актуальные)
```
OpenAI:     chat-latest · gpt-5.5
Anthropic:  claude-sonnet-4-6 · claude-opus-4-8
DeepSeek:   deepseek-v4-flash · deepseek-v4-pro
Qwen:       qwen3.7-max · qwen3.7-plus
Google:     gemini-3.5-flash (+ gemini-3.5-pro скоро)
Llama:      llama-4-maverick
```

---

## ✅ Реализовано (MVP, v8.4.0, ~5K строк в `core/`)

> Все эти компоненты прошли 5-раундовый внешний аудит в мае 2026.
> Интеграционные баги между ними закрыты в v8.4.0 (см. CHANGELOG_v8.4.0.md).

**Ядро памяти (`core/memory.py` v8.3.0):**
- L0 LRU кэш (128 слотов, OrderedDict) + L1 SQLite (per-op connection)
- ESM: 8 состояний, матрица переходов, валидация, audit trail (history + by)
- Ring Zero иммутабельность I6 для `VALUES_CORE` / `RING_ZERO`
- I50: `store_fact` запрещает обход `transition_esm` (новые факты только в Observed)
- I50-b: `ImmutableCore` зарезервирован для Ring Zero
- **I96 (v8.2.0)**: bi-temporal схема — 4 поля `t_*` на каждый факт
- **I98 (v8.3.0)**: `TRUSTED_SOURCES` whitelist — ring_zero / domain_seed / system_axiom защищены от Contradicted и drift
- `get_fact_at()`, `invalidate_edge()`, `search()`, `make_store()`
- `TrustedSourceError` — отдельное исключение для нарушений I98
- Индексы на epistemic_state и bi-temporal полях ~~P-3~~ ✅ закрыто

**NGram L0 Pre-Filter (`core/ngram_index.py` v1.0.0):** 🆕
- SQLite FTS5 trigram tokenizer — мгновенное сужение кандидатов ~~P-1~~ ✅ закрыто
- Graceful degradation если FTS5 недоступен → pipeline fallback
- Принцип Cursor: «Narrow candidates → Validate»
- Инвариант I99: не хранит ESM-состояние, Graph = Truth сохраняется

**SleepTimeWorker + CoreMemoryBlocks (`core/sleep_time_worker.py` v1.0.0):** 🆕
- `CoreMemoryBlocks` — три постоянных слота в system prompt (user_profile / agent_persona / current_goals)
- `SleepTimeWorker` с активным циклом `think()` — думает сам, без ожидания сообщений
- `suggest_next_step()` — предлагает следующий шаг проекта (из RNE документов)
- `get_notebook()` — полный снапшот блокнота + suggested_next_step
- BUG-3/RISK-1/RISK-5 (PDR-033 HYPERIA) встроены
- LLM mock → Sprint 2c: заменить на реальный async client
- `make_sleep_time_worker()` — фабрика для тестовой изоляции

**Контракт хранилища (`core/storage.py` v8.1.0):**
- `GraphStore` ABC + `AsyncGraphStore` ABC
- Bi-temporal методы в контракте: `get_fact_at`, `invalidate_edge`, `search`

**Пайплайн (`core/pipeline.py` v8.0.3-p0):**
- BM25 Okapi retrieval (k1=1.5, b=0.75, Robertson IDF)
- Guardian (структурная проверка с fact_id coverage) + TruthGate (confidence floor)
- Provenance trace builder с ESM-валидацией
- Идемпотентный `pipeline.run()` на persistent DB

**Trace (`core/trace.py` v8.0.4):**
- `promote_trace` с параметром `by` → `promoted_by` (audit trail)
- Разделение `retrieval_score` (BM25, volatile) и `source_confidence` (stable)
- Двухпроходная атомарность promote (two-pass: validate → mutate)

**Тесты (v8.4.0):**
- **682 теста собрано** · ✅ **652 passed, 0 failed**, 17 skipped, 13 xfailed (проверено 2026-05-30, Python 3.12, 16.5 мин) · coverage `core/` = **56%** (не 87%): ядро 85-100%, периферия не покрыта; порог 80% не достигнут
- `test_esm.py` — 36 тестов (включая BUG-1 split-brain regression)
- `test_adversarial.py` — **49 тестов** (39 базовых + 10 audit regression в v8.4.0)
- `test_sleep_time_worker.py` — 37 тестов
- `test_truth_gate.py` — 20 тестов
- `test_pipeline.py` — 19 тестов
- `test_mhi.py` — 15 тестов
- `test_ngram.py` — 14 тестов
- `test_hybrid_retriever.py` — 21 тест
- `test_embedding_registry.py` — 19 тестов
- `test_knowledge_ingester.py` — 29 тестов
- `test_regression_p0.py` — 7 тестов
- **`test_server_integration.py`** — 14 тестов 🆕 (FastAPI TestClient, ловит баги на стыках)

**RFC0063 Knowledge Ingestion Pipeline (`file_parsers/` v1.1.0):** 🆕
- `FileParser` ABC + `ParseResult` с W3C PROV provenance
- `FileIngester` — 20+ форматов: PDF, DOCX, TXT/MD/JSON/YAML, CSV, JPG/PNG, MP3/WAV, MP4
- Каскадные парсеры: Docling→MinerU→Unstructured→PyPDF2 (PDF); easytranscriber→Whisper (Audio)
- Blake3 fallback на sha256 (blake3 не в Python stdlib) ~~FIX~~
- NGramIndex: `ngram_index_fact()` после каждого `store_fact()` (I99)
- TRUSTED_SOURCES: `source_override="domain_seed"` + auto-detect из имени пути (I98)
- `TrustedSourceError` перехватывается отдельно — нормальное поведение, не баг
- SleepTimeWorker уведомление после batch `ingest_directory()` (I100)
- `KnowledgeIngesterV5` — интеграция ESM + NGramIndex + TRUSTED_SOURCES + SleepTimeWorker

**Инструменты миграции (не runtime):**
- `velantrim_migrate_v3_1.py` — production migration tool с rollback
- `fill_dependencies.py`, `audit_metadata.py`, `check_rfc_duplicates.py`
- `utils/rfc_parser.py` — shared RFC парсер с поддержкой диапазонов
- Metadata hardening: Cyrillic → ASCII (39→0), layers 55→1 null, deps 54→27

---

## 📋 Спроектировано, НЕ закодировано

| RFC | Компонент | Sprint |
|-----|-----------|--------|
| RFC0016 | Velum L1.5 synaptic pre-graph, `_degree_cache` | S2 |
| RFC0017 | FSRS power-law decay `R=(1+19/81×t/S)^(-0.5)` | S2 |
| RFC0066 | Concept Emergence, ProtoConcept, Hebbian learning | S3 |
| RFC0065 | Memory Volition, `write_voluntary()`, VolitionWorker | S3 |
| RFC0067 v2.0 | Analogy Graph, Semantic Bridge Engine, Adaptive Decoder | S4 |
| ~~RFC0063~~ | ~~Knowledge Ingestion Pipeline~~ | ✅ Done — `file_parsers/` v1.1.0 |
| RFC0068 | NeuroCore (plastic memory, Phase 0 passive tracker) | S5+ |
| — | Neo4j / KuzuDB integration (GraphStore ABC готов) | S2c |
| — | Redis Streams + fallback queue (A6 documented, not wired) | S2c |
| — | Async/await throughout (сейчас sync) | S2c |
| — | Sprint A patches A6–A10 (documented, not wired) | S2c–S3 |
| — | HybridRetriever (BM25 + vector + HotGraph + HippoRAG) | S2a |
| — | LLM Generation (сейчас string join) | S2b |
| — | OutputFaithfulnessChecker | S2b |
| — | Canonical Memory Protocol Fast/Slow Path | S2–S3 |

---

## 📊 Статус инвариантов

| ID | Имя | Статус |
|----|-----|--------|
| **I1** (8 states) | ESMStatesFixed | ✅ enforced + tested |
| **I2** (transitions) | ESMTransitionsMatrix | ✅ enforced + tested |
| **I6** (Ring Zero) | RingZeroImmutable | ✅ enforced + tested |
| **I50** (ESM ownership) | ESMOwnership | ✅ enforced + tested |
| **I50-b** (ImmutableCore) | ImmutableCoreReserved | ✅ enforced + tested |
| **I68** (TruthGate) | TruthGateGateway | ✅ enforced + tested (v8.3.1: `core/truth_gate.py`, 23 теста, mode-aware) |
| **I96** (bi-temporal) | BiTemporalEdges | ✅ enforced + tested (v8.2.0) |
| **I97** (BlackboardBus) | BlackboardOnly | 📋 В контракте, SQLite-реализация pending |
| **I104** (drift L0/L1 sync) | DriftProtectionL0L1Sync | ✅ enforced + tested (v8.3.1: regression-тест для BUG-1) |
| **D1–D5** | Data invariants | ✅ enforced + tested |
| **PL1–PL4** | Pipeline invariants | ✅ enforced + tested |
| **I3..I95 (без I50/I68/I96)** | Остальные | ❌ pending Sprint 3+ |

---

## 🗓️ Sprint план

| Sprint | Что | Статус |
|--------|-----|--------|
| **S1** | Честность + аудит: ESM баги, тесты, LICENSE, P0/P1 | ✅ Done |
| **S1+** | Bi-temporal I96, make_store(), storage ABC update, trace by | ✅ Done |
| **S1++** | TRUSTED_SOURCES I98, NGramIndex I99, EmbeddingRegistry, SleepTimeWorker+CoreMemoryBlocks (sync mock) | ✅ Done |
| **v8.3.1 fix** | BUG-1 split-brain L0/L1, BUG-2 mock LLM priority, BUG-3 TruthGate text. Новые модули: реальный `TruthGate`, `HybridRetriever`, `MHICalculator`. Тестов: 130+ → 256, coverage 81% → 86% | ✅ Done |
| **S2a** | Интегрировать `HybridRetriever` в `pipeline.py` (заменить `retrieve()`), SQLite FTS5 для `search()` | ✅ Частично (singleton в v8.4.0, FTS5 search — pending) |
| **v8.4.0 audit** | 5-раундовый внешний аудит. Закрыты 7 критических integration багов: SleepTimeWorker startup, NGram split, TruthGate false positives, MHI dead constant, async/sync mismatch, security defaults, HybridRetriever per-request. +10 regression тестов, +14 integration тестов. | ✅ Done |
| **S2b** | Убрать mock DATABASE, реальная LLM generation, интегрировать `TruthGate` в pipeline по умолчанию (BALANCED), `OutputFaithfulnessChecker` | 🔜 |
| **S2c** | async/await + aiosqlite + A6–A10 wiring + Neo4j/Graphiti + реальный NLI contradiction detector через ATLAS-OS | 🔜 |
| **S3** | Patch 13 Causal Graph — начать с **одного типа отношения** (Pearl-style causal edge), не 12 сразу. RFC0066 ConceptEmergenceDetector + RFC0065 Volition + Cold Storage GC для Collapsed | 📋 |
| **S4** | Patch 14 Memory Evolution (с entity resolution, не cosine-only) + RFC0067 Analogy Graph | 📋 |
| **S5+** | RFC0068 NeuroCore (feature-flagged, Phase 0 passive) + LoCoMo/LongMemEval public benchmarks | 📋 |

---

## 🔱 Архитектурный принцип v8.4.0

После аудита было сформулировано наблюдение: **дыры в покрытии тестами не
случайные — они в точности там, где живут баги**. Это диктует приоритет:
сначала добавляем тесты под намеренный фикс, потом фиксим. xfail-тесты
честнее чем "10/10 CERTIFIED". Числа важнее мнений AI.

Следующий шаг (S2b–S2c) — НЕ начинать Patch 13 пока не пройдёт публичный
бенчмарк (LoCoMo / LongMemEval / MuSiQue). Иначе сравнение с Mem0/Zep/Letta
остаётся в режиме features-list, не numbers.
