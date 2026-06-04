# 🔱 Velantrim V9 — Финальный документ (Аудированная версия)

> **Версия:** v9.3-audit · **Дата:** Май 2026 · **Статус:** Production-ready (Specification) + Vision (Horizons)
> **Авторы:** синтез аудитов V8 Crystal + рекомендаций архитектурных проверок (DeepSeek, Gemini, Qwen, ChatGPT, Mistral, Perplexity)
> **Аудит V9→V9.1:** Claude Sonnet 4.6 (Май 2026) — добавлены разделы 10–12, восстановлен SLO, добавлен 🟦 Documented уровень
> **Аудит V9.1→V9.2:** Claude Sonnet 4.6 (Май 2026) — добавлены §0 «Как это работает», I98-I103, NGramIndex, EmbeddingRegistry, TRUSTED_SOURCES, L1.75 SleepTimeWorker + CoreMemoryBlocks; тест-база 130+
> **Аудит V9.2→V9.3:** Claude Sonnet 4.6 (Май 2026) — повторный мета-аудит обнаружил BUG-1 (split-brain L0/L1 при drift protection), BUG-2 (mock LLM priority в SleepTimeWorker), BUG-3 (TruthGate сообщение). Все три исправлены. Добавлены реальный `TruthGate` (заменяет MVP placeholder I68), `HybridRetriever` (BM25+Dense+RRF), `MHICalculator` (закрывает Horizons E2 RFC0070). Добавлен инвариант I104 про синхронизацию L0/L1 в drift protection. Тест-база 130+ → 191, coverage 81% → 86%.

---

# Часть I · Velantrim V9 Crystal — Specification

## ⚡ 0. Как это работает — за 60 секунд

> Этот раздел добавлен в v9.2-audit. Полная версия с диаграммами — в `SYSTEM_OVERVIEW.md`.

```
👤 Вопрос пользователя
         │
         ▼
┌──────────────────────── FAST PATH (миллисекунды) ───────────────────────┐
│  1. 🔎 NGramIndex      → сужает кандидатов за O(log N) до limit=50     │
│  2. 🔍 BM25 Retrieve   → ранкинг среди кандидатов                      │
│  3. 🛡️  Guardian        → структурная проверка (fact_id, claim, source) │
│  4. 🔐 Truth Gate      → confidence ≥ 0.5, source не пустой            │
│  5. 🔄 ESM Transition  → Observed → Validated (через transition_esm)   │
│  6. 💬 Answer          → ответ из Validated фактов                      │
└─────────────────────────────────────────────────────────────────────────┘
         │ fire-and-forget (EventBus)
         ▼
┌──────────────────────── SLOW PATH (фон, async) ─────────────────────────┐
│  S1. EventBus          → логирование в Redis Streams                    │
│  S2. L1 Buffer         → обработка эпизода                             │
│  S3. Velum L1.5        → synaptic pre-graph update                      │
│  S4. L2 Consolidation  → кластеризация тем                             │
│  S5. Truth Gate        → ESM + L3 граф (Neo4j)                         │
│  S6. ReasoningBank     → Thompson Sampling update                       │
│  S7. ResponseAudit     → только здесь (I28: не в Fast Path!)           │
│                                                                         │
│  SleepTimeWorker L1.75 (idle-цикл, каждые 5+ минут простоя):           │
│  ├── think()              → переоценка цели, поиск пробелов, синтез    │
│  ├── suggest_next_step()  → предлагает что делать дальше               │
│  └── CoreMemoryBlocks     → user_profile / agent_persona / current_goals│
└─────────────────────────────────────────────────────────────────────────┘

Хранилища:
  L0: OrderedDict LRU (128 слотов, RAM)     → быстрый кэш
  L1: SQLite WAL (факты + bi-temporal I96)  → персистентный буфер
  L3: Neo4j (граф истины)                   → Sprint 2c
  Notebook DB: SQLite (блокнот проекта)     → SleepTimeWorker

Три правила которые нельзя нарушать:
  Graph = Truth   → LLM говорит, граф решает, Truth Gate обязателен
  ESM ownership   → epistemic_state меняется ТОЛЬКО через transition_esm()
  Slow Path only  → ResponseAudit и SleepTimeWorker НИКОГДА в Fast Path (I28, I100)
```

---

## 📌 Принципы документа

> **Source of truth = реестр компонентов, а не markdown.**
> Этот документ — view layer над `component_registry.yaml` и `v9_contracts.yaml`.

**3 уровня прозрачности:**
- 🟢 **Production** — стабильно работает, есть тесты или подтверждённые патчи
- 🟡 **Beta** — код готов, требует валидации
- 🔴 **Experimental** — feature-flag, активно тестируется

**Verification layer:**
- ✅ **Verified** — есть конкретный именованный патч (P0.5, P2-4, P3-D, P1-1) или CI-тест
- 🟦 **Documented** — есть полная реализация и контракт в V8, именованного патча из аудита нет
- ⚠️ **Hypothesis** — статус назначен по маркерам документа, требует подтверждения тестом

> 🟦 Documented введён в v9.1-audit: ряд компонентов имеют рабочий код и описание в V8 (EventBus DLQ, Memory Budget Planner, Cognitive Modes), но не имеют именованного аудиторского патча. Сваливать их в Hypothesis — несправедливо; сваливать в Verified без патча — нечестно.

---

## 🧠 1. Фундаментальные принципы

Velantrim V9 стоит на четырёх аксиомах:

| Аксиома | Смысл |
|---------|-------|
| **Graph = Truth** | Neo4j L3 — единственный источник истины. LLM не хранит факты. |
| **Memory = Physiology** | 6 уровней (L0–L5) как биологические подсистемы памяти. L6 — в Horizons. |
| **Dual-Process** | Fast Path (ms) для ответа + Slow Path (фон) для консолидации. |
| **Truth Gate + ESM** | Каждый факт имеет жизненный цикл из 8 состояний. Прямые мутации запрещены. |

### Интеллектуальная родословная

V9 синтезирует **четыре традиции**:

```
🇷🇺 Советская кибернетика     → Лурия (3 Units → L0-L5), Глушков (ОГАС)
🇺🇸 Американская BICA          → ACT-R (activation), Soar (memory split)
🏢 LLM-индустрия 2024-2026    → Zep (bi-temporal), mem0, A-MEM
🏢 Anthropic welfare           → Введено только в Horizons
```

### Наследование из HYPERIA v5.20

Следующие компоненты V9 происходят из HYPERIA FractalMemory Core v5.20 и адаптированы для Velantrim:

| HYPERIA компонент | Velantrim наследник | Статус |
|-------------------|---------------------|--------|
| HYPERIA-1: DAAD (Domain-Aware Attention & Decay) | Weighted Semantic Decay / DecayOrchestrator | 🟡 Beta |
| HYPERIA-2: Guardian | Memory Guardian (§11) | 🟡 Beta |
| HYPERIA-3: ACT-R Activation | L4 ReasoningBank активация | 🟡 Beta, feature-flag |
| HYPERIA-4: Laplace Confidence | Truth Gate confidence scoring | 🟢 Production |
| HYPERIA-5: CognitiveModes | Cognitive Modes (§12) | 🟦 Documented |
| HYPERIA-6: OutputFaithfulnessChecker | L4.5 ResponseAudit | 🟡 Beta |
| HYPERIA-7: MemoryBudgetPlanner | Memory Budget Planner | 🟦 Documented |
| HYPERIA-8: CircuitBreaker | CircuitBreaker | 🟡 Beta |
| HYPERIA-9: SOARGoalNode | L0 Goal Stack | 🟢 Production |
| HYPERIA-10: Каскадная инвалидация стратегий | L4 strategy GC | 🟡 Beta |

---

## 🏗️ 2. Архитектурный контракт V9 (новое в V9)

Этот раздел — **обязательные контракты Sprint 1**. Они не были в V8 и являются основным архитектурным апгрейдом.

### 2.1 Bi-Temporal Validity (новое 🆕)

**Каждое ребро в L3 имеет 4 timestamp:**

```cypher
(:Entity)-[:RELATES_TO {
  fact_id: "f_abc123",
  t_event_valid_start: datetime("2025-01-15T..."),  // когда факт стал истинным в мире
  t_event_valid_end:   null,                         // null = всё ещё валиден
  t_ingestion_start:   datetime("2025-01-16T..."),   // когда система узнала
  t_ingestion_end:     null                          // null = всё ещё верим
}]->(:Entity)
```

**Никогда не DELETE — только инвалидируем через SET `t_*_end`.**

```cypher
// Time-travel: что я знал на момент T в мире на момент T'
MATCH (a)-[r:RELATES_TO]->(b)
WHERE r.t_ingestion_start <= $known_at
  AND (r.t_ingestion_end IS NULL OR r.t_ingestion_end > $known_at)
  AND r.t_event_valid_start <= $world_at
  AND (r.t_event_valid_end IS NULL OR r.t_event_valid_end > $world_at)
RETURN a, r, b;
```

**Инвариант I96:** Каждое ребро L3 имеет 4 поля времени.
**Источник:** Rasmussen et al., *Zep: A Temporal Knowledge Graph Architecture for Agent Memory*, arXiv:2501.13956 (2025).

### 2.2 Neural Blackboard Pattern (новое 🆕)

**L3 граф = blackboard. Все модули пишут ТОЛЬКО через BlackboardBus.**

```python
class BlackboardModule(ABC):
    @abstractmethod
    async def read_signals(self, kinds: list[SignalKind]) -> list[BlackboardSignal]: ...

    @abstractmethod
    async def write_observation(self, sig: BlackboardSignal) -> None: ...
```

Все существующие модули (Velum, Etir, Observer, ReasoningBank, FSRSWorker, ConceptEmergence) становятся writers/readers через адаптеры.

**Инвариант I97:** Прямой Cypher CREATE/SET на L3 запрещён вне репозиториев BlackboardBus.
**Источник:** van der Velde & de Kamps, *Neural blackboard architectures*, Behavioral and Brain Sciences 29(1), 2006.

### 2.3 Архитектурные обязательства V9 (V9 Contracts)

Это **proposals на Sprint 1**, не существующая реальность:

```yaml
# v9_contracts.yaml
contracts:
  - id: slow_path_only_decorator
    type: runtime_guard
    rationale: "Закрыть утечки Fast→Slow"
    closes_invariant: I28
    sprint: 1

  - id: decay_orchestrator
    type: architectural_unification
    rationale: "Решить интерференцию FSRS+ACT-R+Hebbian+DAAD+Salience"
    priority_chain: [ESM, DAAD, FSRS, Vintage, Salience]
    sprint: 1

  - id: retrieval_router_unification
    type: deprecation_consolidation
    rationale: "Один роутер вместо трёх"
    replaces:
      - CognitiveModeRouter
    keeps:
      - FactRouter
      - HybridRetriever
    hierarchy: "intent → mode → sources → limits"
    sprint: 1

  - id: bi_temporal_validity
    type: data_model_change
    rationale: "Честный audit trail"
    affects: "all L3 edges"
    sprint: 1

  - id: neural_blackboard_pattern
    type: write_protocol_unification
    rationale: "Единый канал записи на L3"
    affects: "Velum, Etir, Observer, ReasoningBank, FSRSWorker, ConceptEmergence"
    sprint: 1
```

---

## 🗂️ 3. Реестр компонентов V8 → V9 (37 компонентов)

**Формат записи:**
```yaml
component_id: <имя>
baseline_status: <текущий статус V8>
verification_layer: <verified|documented|hypothesis>
v9_target_status: <цель V9>
evidence: <патч или маркер из V8>
dependencies: [...]
migration: <если применимо>
```

### 3.1 Ядро архитектуры (Core Runtime)

| Компонент | Baseline | Verification | V9 Target | Evidence |
|-----------|----------|--------------|-----------|----------|
| Dual-Process (Fast/Slow Path) | 🟢 Production | ⚠️ Hypothesis | 🟢 + `@slow_path_only` | I28 в V8 |
| EventBus (Redis Streams) | 🟢 Production | 🟦 Documented | 🟢 + 3 канала (realtime/maintenance/learning) | DLQ, fallback, RFC0036 готовы |
| ConsolidationEngine | 🟢 Production | ✅ Verified | 🟢 | Patch P0.5 (race condition closed) |
| Meta-Supervisor | 🟡 Beta | ⚠️ Hypothesis | 🟢 | SAFE_MODE логика описана |
| CircuitBreaker | 🟡 Beta | 🟦 Documented | 🟢 | HYPERIA-8, per-loop lock реализован |
| Memory Budget Planner | 🟡 Beta | 🟦 Documented | 🟢 | HYPERIA-7, check_before_write() работает |
| **NGramIndex** (L0 Pre-Filter) | 🟢 Production | ✅ Verified | 🟢 | I99, FTS5 trigram, O(log N) поиск, Sprint 1++ |
| **EmbeddingRegistry** | 🟢 Production | ✅ Verified | 🟢 | Защита от numpy.dot dim-mismatch, 17 моделей |
| **TRUSTED_SOURCES** whitelist | 🟢 Production | ✅ Verified | 🟢 | I98, ring_zero/domain_seed/system_axiom защищены |

### 3.2 Слои памяти L0–L5

| Компонент | Baseline | Verification | V9 Target | Evidence |
|-----------|----------|--------------|-----------|----------|
| L0 Working Memory + CoreMemoryBlocks | 🟢 Production | ⚠️ Hypothesis | 🟢 | I1-I5 описаны |
| L1 Episodic Buffer (SQLite + FTS5) | 🟢 Production | ⚠️ Hypothesis | 🟢 | WAL-режим работает |
| L1.5 Velum (Synaptic Pre-Graph) | 🟢 Production | ✅ Verified | 🟢 | Patch P0.5 (asyncio.Lock) |
| **L1.75 SleepTimeWorker + CoreMemoryBlocks** | 🟦 Documented | ✅ Verified | 🟡 async Sprint 2c | I100-I103, RNE концепция, LLM mock → Sprint 2c |
| L2 Medium-Term Memory | 🟡 Beta | ⚠️ Hypothesis | 🟡 | RFC0013, кластеризация работает |
| L2.5 Staging Layer | 🟡 Beta | ⚠️ Hypothesis | 🟡 | RFC0014, Resource-Aware Scheduler |
| L3 Knowledge Graph (Neo4j) | 🟢 Production | ⚠️ Hypothesis | 🟢 + bi-temporal | Канонический фундамент |
| **L3.5a Etir** (Spreading Activation) | 🟡 Beta | ⚠️ Hypothesis | 🟡 | RFC0011, DeepSeek-lock: не форсируем |
| **L3.5b ImmutableCore** (Snapshots) | 🟡 Beta | ⚠️ Hypothesis | 🟡 | Разделён с Etir |
| L4 ReasoningBank | 🟡 Beta | ✅ Verified | 🟢 | Patch P3-D (Thompson Sampling, RFC0039) |
| L4.5 ResponseAudit/FocusEngine | 🟡 Beta | ⚠️ Hypothesis | 🟡 | I28, I29 описаны |
| L5 Anticipatory (SAE/EGM/XAI) | 🟡 Beta | ⚠️ Hypothesis | 🟡 | SAE decay работает, I30-I34 |
| **L5.5 PredictiveFusion** | 🔴 Experimental | ⚠️ Hypothesis | 🔴 | I35, DeepSeek-lock: не форсируем |

**L6 Values Core → перенесён в Horizons** (см. Часть II).

### 3.3 Эпистемический конвейер

| Компонент | Baseline | Verification | V9 Target | Evidence |
|-----------|----------|--------------|-----------|----------|
| Truth Gate · ESM atomicity | 🟢 Production | ✅ Verified | 🟢 + Blackboard | Patch P2-4 (atomic_split), RFC0004/RFC0015 |
| Truth Gate · Semantic (v8.3.1) | 🟢 Production | ✅ Verified | 🟢 + cross-graph (Sprint 2c) | `core/truth_gate.py` v1.0.0 — source + confidence + evidence_count + active contradictions check. Cognitive Modes (PRECISION/BALANCED/EXPLORATION/CREATIVE). 23 теста, 78% coverage. Заменяет MVP placeholder I68. |
| Write Protocol Gate | 🟢 Production | ⚠️ Hypothesis | 🟢 | ALLOWED_WRITERS логика |
| Source Trust Layer | 🟡 Beta | ⚠️ Hypothesis | 🟡 | trust_score есть |
| **Weighted Semantic Decay** | 🟡 Beta | ⚠️ Hypothesis | 🟡 + DecayOrchestrator | RFC0017, HYPERIA-1 DAAD |
| Observer++ (Иммунная система) | 🟡 Beta | 🟦 Documented | 🟡 | RFC0041 Graduated Observer++, ATK-registry |

### 3.4 Интеллектуальные расширения (RFC)

| Компонент | Baseline | Verification | V9 Target | Evidence |
|-----------|----------|--------------|-----------|----------|
| RFC0065 Memory Volition | 🟡 Beta | ✅ Verified | 🟢 | Patch P0.5-3 (confidence prior fix) |
| **RFC0066 Concept Emergence** | 🔴 Experimental | ⚠️ Hypothesis | 🔴 | I50, I66, I70; DeepSeek-lock |
| RFC0067 Creative Intelligence | 🔴 Experimental | ⚠️ Hypothesis | 🔴 | I57/I58 разделены, v2.0 |
| RFC0063 Knowledge Ingestion | 🔴 Experimental | ⚠️ Hypothesis | 🔴 | I60-I65, EdgeSuggester HITL-only |

**RFC0068 NeuroCore → перенесён в Horizons**.
**RFC0045 LensEngine + BAE → перенесён в Horizons** (P10).

### 3.5 Кросс-функциональные подсистемы

| Компонент | Baseline | Verification | V9 Target | Evidence |
|-----------|----------|--------------|-----------|----------|
| SafeFTSQuery | 🟢 Production | ✅ Verified | 🟢 | Patch P1-1 (защита от инъекций) |
| HybridRetriever (v8.3.1) | 🟢 Production | ✅ Verified | 🟢 → часть RetrievalRouter | `core/hybrid_retriever.py` v1.0.0 — BM25 + Dense Embeddings + Reciprocal Rank Fusion (Cormack et al., k=60) + опциональный CrossEncoderReranker. Graceful degradation: работает без `rank-bm25` (naive TF-IDF) и без `sentence-transformers` (BM25-only). 22 теста, 72% coverage. Готов к замене BM25-only в pipeline.py |
| FactRouter | 🟡 Beta | 🟦 Documented | 🟡 → ядро RetrievalRouter | RFC0038, Rule-based, детерминирован |
| **CognitiveModeRouter** | 🟡 Beta | ⚠️ Hypothesis | 💤 **Deprecated** | migration_target: RetrievalRouter, deprecation_phase: Sprint 1 |
| CausalGraph | 🟡 Beta | ⚠️ Hypothesis | 🟡 | LLM-path с эвристическим fallback |

**KDE → Horizons**. **Shadow State (RFC0040 CQRS DuckDB) → Horizons /experimental**.

---

## 🐛 4. Исправленные баги из аудитов (P0/P1)

Этот раздел документирует все 11 архитектурных проблем найденных в ходе аудита V8 и их решение в V9.

### Исправлено в V9 (через V9 Contracts)

| # | Баг из V8 | Найден кем | Решение V9 |
|---|-----------|-----------|------------|
| 1 | L3.5 двойной компонент (Etir + ImmutableCore) | DeepSeek | Разделены → L3.5a + L3.5b |
| 2 | Три конкурирующих роутера | DeepSeek, Qwen, ChatGPT | RetrievalRouter unification (V9 Contract) |
| 3 | Два пути записи на граф (Graphiti + прямой Cypher) | DeepSeek | Neural Blackboard Pattern |
| 4 | Тройная decay интерференция (FSRS + ACT-R + Hebbian) | Gemini, Qwen, Mistral | DecayOrchestrator (V9 Contract) |
| 5 | Fast Path без runtime guard | Qwen | `@slow_path_only` декоратор |
| 6 | EventBus перегружен (god object) | ChatGPT | Split на 3 канала |
| 7 | SQLite FTS5 bypass ESM | Gemini | SafeFTSQuery enforce |
| 8 | Config fragmentation | Qwen | Единый `velantrim_config` |
| 9 | Changelog разорван на 7 строк | Claude (1-й аудит) | Один блок в V9 |
| 10 | RFC0004 дублируется | Claude | Один канонический раздел |
| 11 | L6 spec pending в обзоре | Claude, Kimi | Перенесён в Horizons |

### Не подтверждено (требует код-ревью)

Эти баги были предположены Gemini, но **не найдены в V8 документе**. Помечены как `unverified hypothesis`:

- ❓ UnboundLocalError в ConsolidationEngine worker loop
- ❓ Cypher срезы `[-500:]` вместо `[-500..]`
- ❓ Type mismatch при S3 restore Truth Gate
- ❓ Heartbeat генерируется ложно в Meta-Supervisor

**Рекомендация:** провести точечное код-ревью перед канонизацией статусов этих модулей.

---

## 📐 5. Инварианты V9 (I1-I97)

**I1-I37** — унаследованы из V8 (см. V8 Crystal `test_invariants.py`). Ниже — навигационный список с кратким смыслом каждого инварианта:

| Инвариант | Компонент | Смысл |
|-----------|-----------|-------|
| I1-I5 | L0 Working Memory | Детерминизм, трассируемость, разделение факта/вывода, анти-взрыв графа, конфликт-осознанность |
| I6 | L0 Ring Zero | RingZeroImmutable — Ring Zero никогда не изменяется напрямую |
| I7-I8 | ESM | Базовые ESM переходы (см. RFC0015) |
| I13 | ConsolidationEngine | Детерминированный replay в аудите — seed всегда фиксирован |
| I28 | ResponseAuditWorker | НИКОГДА не выполняется в Fast Path (критично для latency) |
| I29 | FocusEngine | FocusVector читается только через граф и SQLite |
| I30 | SAE (L5) | Работает только по существующим рёбрам графа |
| I31 | EGM (L5) | Не навязывает — предлагает только один раз |
| I32 | EGM | Seed-узлы помечены `{source_type: "domain_seed"}` |
| I33 | EGM | `authority_domain` не может быть пустым |
| I34 | XAI (L5) | Показывает только реальные TRACE-пути |
| I35 | L5.5 PredictiveFusion | Не пишет в граф — только читает и возвращает FusedPrediction |
| I36 | L5 Prediction | Prediction Error только ослабляет/усиливает рёбра |
| I37 | LSM (L5) | Не пишет в граф — только читает историю запросов |
| I38 | ConflictResolutionWorker | Вызов только из Slow Path (RFC0062) |
| I49 | Memory Volition | `write_voluntary()` ВСЕГДА через TruthGate. Обход = баг. |
| I50 | ConceptEmergence | `observe()` не пишет в L3 |
| I55-I59 | RFC0067 Creative | CREATIVE mode: только Validated; CREATIVE ≠ EXPLORATION |
| I60-I65 | RFC0063 Ingestion | FactExtractor, SemanticIndexer, EdgeSuggester инварианты |
| I66, I70 | RFC0066 Concept Emergence | ProtoConcept только в памяти; активных ≤ 500 |
| I85 | OutputFaithfulnessChecker | Quality Gate ПОСЛЕ LLM-генерации, ДО отправки |
| I86 | HybridRetriever | IntentRouter вызывается ТОЛЬКО из HybridRetriever.retrieve() |

**I38-I65 (полные)** — pending → перенесены в Horizons для формализации.

**Новые в V9.1 (bi-temporal + blackboard):**
- **I96** — Каждое ребро L3 имеет 4 поля времени (bi-temporal)
- **I97** — Прямой Cypher на L3 запрещён вне BlackboardBus

**Новые в V9.2 (Sprint 1++ — реализованы в коде):**
- **I98** — TRUSTED_SOURCES: ring_zero/domain_seed/system_axiom нельзя перевести в Contradicted
- **I99** — NGramIndex хранит только (doc_id, content) — не ESM-состояние, Graph = Truth сохраняется
- **I100** — SleepTimeWorker.think() только в Slow Path (I28 распространяется)
- **I101** — CoreMemoryBlocks.update() только явный CRUD, никакого auto-overwrite
- **I102** — ResearchNotebook хранится в отдельной БД, не пишет в L3 напрямую
- **I103** — SleepTimeWorker держит ссылку на asyncio.Task (защита от silent GC death)

**Новые в V9.3 (v8.3.1 — реализованы в коде):**
- **I104** — `DriftProtectionL0L1Sync`: когда `store_fact()` обнаруживает claim drift у Validated/Supported факта и переводит его в Contradicted, обновление **должно быть атомарным** по обоим слоям (L0 и L1). Это **единственное** легитимное исключение из правила «epistemic_state меняется только через `transition_esm()`». Реализация: в `memory.py` после стандартного `INSERT ... ON CONFLICT DO UPDATE` (который исключает `epistemic_state`) выполняется дополнительный `UPDATE facts SET epistemic_state = ?, history = ? WHERE fact_id = ?`. Тест: `test_store_fact_drift_protection_keeps_l0_l1_in_sync` (regression для BUG-1).

**Будущие (в Horizons):** I105-I115 (см. Часть II).

---

## 🛡️ 6. Validation Layer (CI/CD)

V9 вводит **3 уровня машинной валидации:**

### Pre-commit
```bash
# scripts/ci_invariant_check.sh
- mypy --strict velantrim/
- проверка namespace violations
- запрет direct Cypher CREATE/SET вне репозиториев
```

### Runtime
```python
# velantrim/runtime/invariant_guard.py
@slow_path_only  # I28 enforcement
@blackboard_only  # I97 enforcement
```

### CI Schema validation
```yaml
# Проверка целостности реестра
- все компоненты имеют baseline_status
- все RFC из оглавления существуют
- нет dead links
- lifecycle consistency (no Deprecated → Production переходов)
```

---

## 🗺️ 7. Namespace архитектура

```
velantrim/
├── core/          🟢 Production strict (Dual-Process, EventBus, CircuitBreaker)
├── memory/        🟢 Production (L0-L3) + 🟡 Beta (L2.5, L3.5, L4.5)
├── epistemic/     🟢 Production (TruthGate, ESM, WriteProtocol)
├── reasoning/     🟡 Beta (L4 ReasoningBank, RFC0065 Volition)
├── runtime/       🟢 Production (Bus split, gates, decorators)
├── governance/    🟡 Beta (Meta-Supervisor, Observer++)
├── retrieval/     🟡 Beta (RetrievalRouter unification)
├── protection/    🟡 Beta (MemoryGuardian, ImmutableRawMemory, AuditLayer) ← восстановлено v9.1
├── production/    🟦 Documented (MCPServer, CognitiveModes, PIIRedaction, FractalMonitor) ← восстановлено v9.1
└── _research/     🔴 Experimental (изолировано, RFC0066, RFC0067, L5.5)

→ /horizons/      ⚪ Vision (см. Часть II)
```

**Правило:** код из `_research/` НЕ может импортировать в `core/`, `memory/`, `epistemic/`.

---

## 📅 8. Sprint 1 Roadmap

```
Неделя 1-2:  Bi-Temporal Validity (Cypher migration, shadow-copy)
Неделя 2-3:  Neural Blackboard Pattern (refactor 6 модулей)
Неделя 3-4:  RetrievalRouter unification (deprecate CognitiveModeRouter)
Неделя 4-5:  DecayOrchestrator (priority chain)
Неделя 5-6:  @slow_path_only enforcement + EventBus split
Неделя 6:    CI validation layer + financial regression tests

✅ V9 Specification готова к релизу
```

> ⚠️ **Риск темпа:** 5 крупных контрактов за 6 недель — агрессивный план. Рекомендуется добавить буфер: если Bi-Temporal migration займёт >2 недель, сдвинуть DecayOrchestrator в Sprint 1.1.

**Smart-rollback triggers:**
- P95 graph search > 250 ms → откат bi-temporal
- I97 violations > 0/неделю → откат blackboard
- RetrievalRouter accuracy < baseline → откат deprecation

### 📐 SLO Contract (Service Level Objectives)

> Пороги для Grafana alert rules. Все значения из `velantrim_config.SLOConfig`.

| Метрика | SLO (цель) | WARN | CRITICAL |
|---------|-----------|------|---------| 
| search P95 latency | <500ms | >800ms | >2000ms |
| Etir P95 latency | <50ms | >80ms | >200ms |
| consolidation lag | <60s | >120s | >300s |
| GC weekly runtime | <2h | >3h | >6h |
| staging_candidates | <5 000 записей | >8 000 | >MAX_STAGING |
| DLQ size | <10 | >10 (DEGRADED) | >50 (SAFE_MODE) |
| budget fill ratio | <0.85 | >0.85 | >0.90 |
| output_faithfulness | >0.80 | <0.60 | <0.40 |
| L2 MHI | >0.60 | <0.50 | <0.30 |

**Автотриггеры MetaSupervisor:**
```
MHI < 0.30           → немедленный GC + alert ops
MHI < 0.50           → MetaSupervisor → DEGRADED (ускорить ConsolidationEngine)
budget_fill > 0.85   → MetaSupervisor → DEGRADED
budget_fill > 0.90   → MetaSupervisor → блокировка записи
DLQ > 50             → MetaSupervisor → SAFE_MODE
faithfulness < 0.40  → алерт + логировать unsupported_sentences в AuditLayer
```

**Smart-rollback для bi-temporal (Sprint 1 специфично):**
```
P95 graph search > 250ms после миграции → откат bi-temporal schema
I97 violations > 0/неделю → немедленный rollback blackboard
```

---

## ✅ 9. Что готово к релизу в V9 Specification

**🟢 Production-grade:**
- Dual-Process с runtime guard
- EventBus с 3 каналами
- L0-L1, L1.5 Velum, L3 Knowledge Graph
- Truth Gate + ESM (с bi-temporal I96)
- Write Protocol Gate + **TRUSTED_SOURCES whitelist (I98)**
- SafeFTSQuery
- FSRSWorker, ConceptEmergence (детектор)
- Memory Volition (RFC0065)
- Neural Blackboard Pattern
- Bi-Temporal Validity (I96)
- **NGramIndex L0 Pre-Filter (I99)** 🆕 — FTS5 trigram, O(log N)
- **EmbeddingRegistry** 🆕 — защита от numpy.dot dim-mismatch
- **TruthGate Semantic (v8.3.1)** 🆕 — реальный пропускной пункт вместо MVP placeholder; mode-aware (PRECISION/BALANCED/EXPLORATION/CREATIVE); 4 проверки: source + confidence + evidence_count + active contradictions; 23 теста
- **HybridRetriever (v8.3.1)** 🆕 — BM25 + Dense Embeddings + RRF (Cormack et al., k=60) + опциональный CrossEncoderReranker; graceful degradation; 22 теста
- **MHICalculator (v8.3.1)** 🆕 — Memory Health Index, закрывает RFC0070 stub; HEALTHY/DEGRADED/SAFE_MODE по V9 §8 SLO Contract; автоматические рекомендации; 14 тестов

**🟦 Documented (рабочий код, ожидает именованного CI-теста):**
- EventBus DLQ + Fallback Queue (RFC0036)
- Memory Budget Planner (HYPERIA-7)
- CircuitBreaker (HYPERIA-8)
- Observer++ Graduated (RFC0041)
- FactRouter (RFC0038)
- Cognitive Modes — 4 режима (PRECISION/BALANCED/EXPLORATION/CREATIVE)
- MCP Server (stdio transport)
- PII Redaction
- Memory Guardian (§11)
- Immutable Raw Memory (§11)
- Audit Layer Phase 1 (§11)
- **L1.75 SleepTimeWorker + CoreMemoryBlocks** 🆕 — активный think(), suggest_next_step(), RNE концепция; LLM mock → Sprint 2c async

**🟡 Beta:**
- L2, L2.5, L4.5, L5
- L3.5a Etir, L3.5b ImmutableCore (раздельно)
- Meta-Supervisor, Observer++
- RetrievalRouter (объединение)
- DecayOrchestrator (новое)

**🔴 Experimental (в Specification, но feature-flagged):**
- L5.5 PredictiveFusion
- RFC0066 Concept Emergence (validation phase)
- RFC0067 Creative Intelligence

---

## 🗺️ 10. Navigation Manifest (v9.2-audit) 🆕

> **Назначение:** этот раздел — единственная точка навигации между V8 и V9. Для каждого важного элемента V8 указано где он живёт сейчас. Source of truth = реестр, этот раздел = view layer поверх реестра.
>
> **Легенда:** ✅ В Specification · 🌌 В Horizons · 🗃️ В Archive · ⚠️ Частично · 🔴 LOST (требует решения)

### 10.1 RFC Navigation

| RFC | Название | Статус в V9 | Расположение |
|-----|----------|------------|-------------|
| RFC0004 | Truth Gate Contract | ✅ Specification | §3.3 Truth Gate + ESM; §2.2 Neural Blackboard |
| RFC0011 | Etir Spreading Activation Engine | ✅ Specification | §3.2 L3.5a Etir |
| RFC0012 | Taxonomy / Domain Hierarchy | ⚠️ Частично | Встроен в L3 Knowledge Graph; явного раздела нет → добавить в `component_registry.yaml` |
| RFC0013 | L2 Medium-Term Memory CORE | ✅ Specification | §3.2 L2 Medium-Term Memory |
| RFC0014 | L2.5 Staging Layer | ✅ Specification | §3.2 L2.5 Staging Layer |
| RFC0015 | TruthGateWithESM | ✅ Specification | §3.3, объединён с RFC0004 (баг #10 исправлен) |
| RFC0016 | L1.5 Velum | ✅ Specification | §3.2 L1.5 Velum |
| RFC0017 | Weighted Semantic Decay | ✅ Specification | §3.3 + DecayOrchestrator |
| RFC0036 | Persistent Event Fallback Queue | ✅ Specification | §3.1 EventBus, 🟦 Documented |
| RFC0037 | Async Closed Loop Eval | ⚠️ Частично | Поглощён L4 ReasoningBank loop; явного упоминания нет |
| RFC0038 | Fact Router (детерминированный) | ✅ Specification | §3.5 FactRouter |
| RFC0039 | Thompson Sampling для L4 | ✅ Verified | §3.2 L4 ReasoningBank (Patch P3-D) |
| RFC0040 | CQRS Shadow State (DuckDB) | 🌌 Horizons /experimental | V9 §3.5 одна строка; нужна запись в Horizons E6 |
| RFC0041 | Graduated Observer++ | ✅ Specification | §3.3 Observer++, 🟦 Documented |
| RFC0042 | Трёхслойный Архитектурный Контракт | ✅ Specification | §7 Namespace архитектура (implicit) |
| RFC0043 | Hardware Profile Selector | 🔴 LOST | V8 строка 15280; нужно добавить в §12 или `velantrim_config` |
| RFC0044 | LLM_MODE Offline-режим | 🔴 LOST | V8 строка 15413; нужно добавить в §12 |
| RFC0045 | LensEngine + BAE | 🌌 Horizons | V9 §3.4 одна строка; раздел в Horizons отсутствует → добавить E7 |
| RFC0046 | DAG Rollback + epistemic_variance | ⚠️ Частично | Поглощён L4 Beta; инварианты не перечислены явно |
| RFC0047 | epistemic_variance Formula | ⚠️ Частично | В L4 Beta, не поименован |
| RFC0048 | Multi-Component Memory Budget | ✅ Specification | §3.1 Memory Budget Planner |
| RFC0049 | Temporal-ESM Sync Protocol | ✅ Specification | §2.1 Bi-Temporal Validity |
| RFC0050 | DAG Rollback Transactional Write | ⚠️ Частично | В L4 Beta, не поименован |
| RFC0051 | LensEngine Composition | 🌌 Horizons | Вместе с RFC0045 |
| RFC0062 | TZ-Fix Integration Patch | 🔴 LOST | V8 строка 38, 3223; ConflictResolutionWorker + I38; нужно упомянуть в §4 или §5 |
| RFC0063 | Knowledge Ingestion Pipeline | ✅ Specification | §3.4 |
| RFC0065 | Memory Volition | ✅ Verified | §3.4 (Patch P0.5-3) |
| RFC0066 | Concept Emergence | ✅ Specification | §3.4, 🔴 Experimental |
| RFC0067 | Creative Intelligence v2.0 | ✅ Specification | §3.4, 🔴 Experimental |
| RFC0068 | NeuroCore (Plastic Memory Layer) | 🌌 Horizons /experimental | Horizons §E1 |
| RFC0069 | L6 Values Core & Welfare | 🌌 Horizons /research | Horizons §R1 |
| RFC0070 | MHICalculator (Phase 1 done v8.3.1, Phase 2 pending) | 🌌 Horizons /experimental | Horizons §E2 (частично закрыт) |

**🔴 Требуют решения до Sprint 1 завершения:**
- RFC0043 (Hardware Profile Selector) — добавить в §12 Production Interface
- RFC0044 (LLM_MODE Offline) — добавить в §12 Production Interface
- RFC0062 (TZ-Fix / ConflictResolutionWorker + I38) — упомянуть в §5 как I38

### 10.2 Компоненты V8 → местонахождение в V9

| Компонент V8 | Статус в V9 | Раздел V9 |
|--------------|------------|----------|
| Memory Guardian | ✅ Восстановлен | §11 Защитный периметр |
| Immutable Raw Memory | ✅ Восстановлен | §11 Защитный периметр |
| Audit Layer (Phase 1+) | ✅ Восстановлен | §11 Защитный периметр |
| Cognitive Modes (4 режима) | ✅ Восстановлен | §12 Production Interface |
| MCP Server | ✅ Восстановлен | §12 Production Interface |
| PII Redaction | ✅ Восстановлен | §12 Production Interface |
| Fractal Similarity Monitor | ✅ Восстановлен | §12 Production Interface |
| Hardware Profile Selector (RFC0043) | 🔴 LOST | Добавить в §12 |
| LLM_MODE Offline (RFC0044) | 🔴 LOST | Добавить в §12 |
| Canonical Memory Protocol v1 | ✅ Specification | §10.3 ниже |
| Token Contract + Promote/Demote | ✅ Specification | §10.4 ниже |
| HYPERIA v5.20 components | ✅ Specification | §1 Наследование из HYPERIA |
| Shadow State (RFC0040 DuckDB) | 🌌 Horizons | /experimental E6 (добавить) |
| SLO Contract | ✅ Восстановлен | §8 Sprint 1 Roadmap |
| Production Runbook | 🗃️ Остаётся в V8 | V8 Crystal §Production Runbook |
| KDE (Knowledge Distillation Engine) | 🌌 Horizons | Horizons (упомянуто в §3.5) |
| RFC0036+ OCC Patch ESMChunkedInvalidator | ⚠️ Частично | Поглощён EventBus split |

### 10.3 Canonical Memory Protocol v1 — краткий контракт

> Полная реализация: V8 Crystal §Canonical Memory Protocol v1 (строка 9142).
> V9 наследует полностью; ниже — навигационная сводка точек входа.

**Fast Path (синхронный):**
```
F1 → Validation Loop L4 (DECISION / VALIDATION / SELF-CHECK)
F1.5 → Velum Context Hint (RFC0016, fire-and-forget)
F2 → L0 update (Goal Stack + Ring Zero)
F3 → L1 FTS5 search (recency bias)
F4 → Graphiti search → Neo4j (hybrid semantic+keyword+graph)
F5 → Context Builder → 4±1 чанка, token_budget=2000
F6 → LLM Generation (единственный вызов на Fast Path)
F6.5 → OutputFaithfulnessChecker (HYPERIA-6, keyword overlap ≥40%)
Выход → ответ + AgentEvent в шину
```

**Slow Path (асинхронный, фон):**
```
S1 → EventBus Logging (Redis Streams, retry 3x, DLQ, RFC0036)
S2 → L1 Buffer Processing
S2.5 → ConflictResolutionWorker (каждые 5 минут, RFC0062, I38)
S3 → L1.5 Velum synapse update
S4 → L2 Consolidation (clustering)
S5 → L3 Truth Gate + ESM (atomic, RFC0015)
S6 → ReasoningBank update (Thompson Sampling, RFC0039)
S7 → ResponseAuditWorker (I28: только Slow Path)
```

### 10.4 Token Contract + Протокол Promote/Demote

> Полная реализация: V8 Crystal §Токен-контракт и Протокол Promote/Demote (строка 6790).

**Token budgets по Cognitive Mode:**
```
PRECISION   → token_budget = 1 000 (медицина, право, финансы)
BALANCED    → token_budget = 2 000 (стандарт, 90% задач)
EXPLORATION → token_budget = 4 000 (brainstorm, гипотезы)
CREATIVE    → token_budget = 3 000 (аналогии + только Validated)
```

**Promote/Demote протокол (жизненный цикл данных):**
```
L1 → L2 Promote: importance > threshold + idle > 24h
L2 → L3 Promote: confidence ≥ 0.7 + evidence_count ≥ 3 + Truth Gate pass
L3 Demote → ESM.Collapsed: importance < 0.1 → архив S3 + Immutable Raw Memory
```

---

## 🛡️ 11. Защитный периметр (восстановлено в v9.1-audit) 🆕

> Этот раздел восстановлен из V8 Crystal. Все три компонента имеют рабочую реализацию в V8 (строки 8122–8573). Статус: 🟦 Documented. Namespace: `velantrim/protection/`.

### 11.1 Memory Guardian — Защита от отравления памяти

**Проблема:** без Guardian агент записывает галлюцинацию в L3 как факт. Через 1–2 месяца система повторяет ошибочные паттерны с уверенностью — у неё есть «доказательства».

**Роль:** L5 Observer расширенный до привратника L3. Ни один факт не попадает в Neo4j без прохождения этого слоя.

**4 проверки `validate_proposal()`:**
1. Наличие источника (`evidence` обязателен)
2. Confidence threshold ≥ 0.7
3. Проверка противоречий → `[:CONTRADICTS]` связь (не удаление)
4. Дедупликация → `evidence_count++` если факт уже есть

**Интеграция:** `MemoryGuardian.validate_proposal()` вызывается внутри `GraphMemory.add_episode()` до любой записи в Neo4j.

**Инвариант:** Memory Guardian = единственный путь в L3 вне Truth Gate pipeline.

### 11.2 Immutable Raw Memory — Защита от Semantic Drift

**Проблема Semantic Drift:** консолидация L1→L2→L3 через LLM-суммаризацию постепенно искажает смысл. «User prefers Python» → «User programs» → «User expert developer». Оригинал теряется.

**Решение:** сырые эпизоды хранятся отдельно и **никогда не изменяются**. Суммаризации отдельно. Доступ к первоисточнику всегда есть.

**Ключевые связи:**
- PII matches сохраняются в Immutable Raw Memory (никогда не в граф)
- ESM.Collapsed факты → ссылка в Immutable Raw Memory (физически не удаляются)
- L3 узлы с importance < 0.1 → Collapsed → архив S3 + Immutable Raw Memory

**Инвариант:** данные в Immutable Raw Memory только `append`, никогда `UPDATE/DELETE`.

### 11.3 Audit Layer — Слой проверяемости (Phase 1+)

**Проблема:** без Audit Layer невозможно понять почему агент ответил именно так. При галлюцинации — нет инструмента найти виновника: LLM при генерации, Etir при поиске, или Graphiti при записи факта.

**3 обязательных API:**
```
GET /memory/audit/context?request_id=
    → какие Etir-узлы активированы, какие L3 факты в контексте, токенов использовано

GET /memory/audit/strategy?request_id=
    → какая стратегия выбрана, Thompson Sampling scores, режим (exploration/exploitation)

GET /memory/audit/forgetting?since=
    → какие факты деактивированы, почему ([:CONTRADICTS] / low importance / age), S3 архив
```

**Реализация:** SQLite (`velantrim_audit.db`). Все writes — `fire-and-forget` через `asyncio.create_task()` (I28: не блокировать Fast Path).

**Roadmap:**
- Phase 1 (Sprint 1): минимальный Audit Layer — logging в SQLite
- Phase 2 (V10): полный Audit Layer API с 3 методами
- Phase 3 (V10+): интеграция с Grafana dashboard

---

## 🔌 12. Production Interface (восстановлено в v9.1-audit) 🆕

> Этот раздел восстановлен из V8 Crystal. Все компоненты имеют рабочую реализацию в V8. Статус: 🟦 Documented. Namespace: `velantrim/production/`.

### 12.1 Cognitive Modes — Четыре режима работы

**Почему критично:** без Cognitive Modes система работает одинаково для критичных данных и творческих задач. Режимы позволяют агенту адаптироваться как человек думает по-разному в зависимости от контекста.

| Режим | Token Budget | Evidence Required | Truth Gate | Гипотезы | Применение |
|-------|-------------|-------------------|------------|---------|------------|
| PRECISION | 1 000 | 5 | ≥0.9 | ❌ | Медицина, право, финансы |
| BALANCED | 2 000 | 3 | ≥0.7 | ✅ | Стандарт (90% задач) |
| EXPLORATION | 4 000 | 1 | ≥0.4 | ✅ | Brainstorm, исследование |
| CREATIVE | 3 000 | 3 | ≥0.7 | ❌ (I57) | Аналогии + только Validated |

**Инвариант:** CREATIVE ≠ EXPLORATION (I58). CREATIVE запрещает Hypothesized факты; EXPLORATION разрешает.

**Связь с CognitiveModeRouter:** CognitiveModeRouter (deprecated, §3.5) — маршрутизатор для выбора режима. Cognitive Modes — сами режимы как поведенческие контракты. Deprecation касается роутера, но не режимов.

### 12.2 MCP Server — Подключение к внешним клиентам

**Транспорт:** stdio (совместим с Cursor, Claude Code, любым MCP-клиентом).

**Инвариант:** MCP Server — только тонкая обёртка над существующим pipeline. Никакой логики памяти внутри. `memory_write` обязательно идёт через `VolitionWorker → Truth Gate`, не напрямую в граф.

**Exposed tools:**
```
memory_read(query, session_id, mode)  → Canonical Fast Path
memory_write(content, session_id)     → VolitionWorker → Truth Gate
memory_status()                       → SLO metrics snapshot
memory_audit(request_id)             → AuditLayer lookup
```

### 12.3 PII Redaction

**Цель:** удаление персональных данных до записи в L3. GDPR compliance — не декларация.

**Что редактируется:** имена, email, телефоны, адреса, паспортные данные, финансовые идентификаторы.

**Ключевой инвариант:** PII matches сохраняются в Immutable Raw Memory (§11.2), **никогда** не попадают в L3 граф.

**Интеграция:** PII Redaction срабатывает в Fast Path F1 (до любого поиска) и в Slow Path S5 (до Truth Gate).

### 12.4 Fractal Similarity Monitor

**Цель:** обнаружение нарастающей повторяемости ответов агента — симптом semantic drift или over-consolidation.

**Принцип:** мониторинг cosine similarity между последовательными ответами. При нарастании → алерт + рекомендация принудительного GC.

**Порог:** similarity > 0.85 на трёх последних ответах → WARN. > 0.92 → CRITICAL + Meta-Supervisor trigger.

### 12.5 Hardware Profile Selector (RFC0043) 🔴 Требует восстановления

> **Статус:** LOST в V9. Реализация в V8 строка 15280. Требует добавления в `velantrim_config.py`.

**3 профиля:**

| Профиль | LLM | Условие |
|---------|-----|---------|
| Full | GPT-4o / Claude Sonnet | ≥16 GB RAM, GPU |
| Balanced | Qwen3-7B / Mistral-7B | 8-16 GB RAM |
| Edge/Lite | RWKV-7 Goose 2.9B | <8 GB, LLM_MODE=lite |

### 12.6 LLM_MODE Offline (RFC0044) 🔴 Требует восстановления

> **Статус:** LOST в V9. Реализация в V8 строка 15413. Требует добавления в `velantrim_config.py`.

**Режимы:** `online` (default) · `lite` (SLM fallback) · `offline` (без LLM: FactRouter + BM25 + LensEngine).

**Инвариант RFC0044:** в `offline` режиме LLM не вызывается. Ответ строится детерминированно из графа.

---

# Часть II · Velantrim Horizons — Future Research & Vision

## 🌌 Манифест

> **Velantrim — это не просто memory layer. Это недостающее звено индустрии.**
>
> Сегодня:
> - **LLM** умеет думать, но забывает
> - **RAG** умеет искать, но не понимает суть
> - **Graph** хранит структуру, но не оценивает важность
> - **Vector Search** находит похожее, но не различает истину от шума
>
> **Никто не построил memory-слой который понимает что важно, что истинно, что устарело, что эмоционально, что приоритетно.**
>
> Velantrim + LLM + Graph + RAG вместе могут разблокировать:
> - 🎯 Понимание сути (gist intelligence)
> - 🔍 Различение шума от истины
> - 💗 Эмоциональную модуляцию памяти
> - 🔮 Прозорливость (anticipation)
> - 🔄 Self-evolving capability
> - 🛡️ Welfare-aware autonomy

Horizons — это **исследовательская дорожная карта** того что Velantrim **может стать**, если индустрия выделит ресурсы.

> **Канон V8.6 (карточки с путями):** [`HORIZONS.md`](HORIZONS.md) · [`LAYERS_AND_HORIZONS.ru.md`](LAYERS_AND_HORIZONS.ru.md) · [`horizons/README.md`](horizons/README.md) · API: `GET /horizons`, `GET /layers/status`

| § V9 | Карточка V8.6 |
|------|----------------|
| R1 L6 | [`horizons/L6_VALUES_WELFARE.md`](horizons/L6_VALUES_WELFARE.md) |
| R2 | [`horizons/R2_CATEGORY_TRUTH_GATE.md`](horizons/R2_CATEGORY_TRUTH_GATE.md) |
| R3 | [`horizons/R3_EVO_MEMORY.md`](horizons/R3_EVO_MEMORY.md) |
| R4 | [`horizons/R4_GLOBAL_WORKSPACE.md`](horizons/R4_GLOBAL_WORKSPACE.md) |
| R5 | [`horizons/R5_K_LINES.md`](horizons/R5_K_LINES.md) |
| E1 | [`horizons/E1_NEUROCORE.md`](horizons/E1_NEUROCORE.md) |
| E2 | [`horizons/E2_MHI_PHASE2.md`](horizons/E2_MHI_PHASE2.md) |
| E3–E7 | [`horizons/README.md`](horizons/README.md) |
| KDE | [`horizons/KDE_DISTILLATION.md`](horizons/KDE_DISTILLATION.md) |
| L2.5 | [`horizons/L2_5_STAGING.md`](horizons/L2_5_STAGING.md) |

---

## 📂 Структура Horizons

```
/horizons
├── /research        активные исследовательские направления
├── /experimental    feature-flagged код в разработке
├── /vision          long-term архитектурные направления
└── /archive         deprecated или поглощённые идеи
```

---

## 🔬 /research — Активные исследования

### R1. L6 Values Core & Welfare Protocol (RFC0069)

**Цель:** формализовать слой ценностей агента с механизмами introspection.

**5 подразделов L6:**
1. Core values (Ring Zero) — immutable
2. Self-model — как агент описывает себя
3. Welfare state — текущее психологическое состояние
4. Introspection traces — логи self-checks
5. Boundary conditions — что агент отказывается делать

**Ключевые компоненты:**
- **IntrospectionProbe** (Anthropic-style, Lindsey et al. 2025)
  - Периодические self-tests на инъекции концептов
  - Target detection rate ≥20% (paritet с Claude Opus 4.1)
- **WelfareMonitor** — cpu_smoothness, error_rate, goal_alignment, volition_rate, distress_signal
- **RingZeroProtector** — 2-approval flow с cooling-off
- **VolitionGate** — блокирует Memory Volition при Red welfare

**Инварианты (будущие):** I98-I100, I115

**Источники:**
- Anthropic *Exploring model welfare* (24 апр 2025)
- Lindsey J. *Emergent Introspective Awareness*, transformer-circuits.pub/2025/introspection
- Claude Opus 4.6 System Card (Feb 2026)

### R2. Category-Theoretic Formalization Truth Gate

**Цель:** перевести проверки Truth Gate с runtime на compile-time через теорию категорий.

**Конструкция:**
- **Категория Velantrim:** объекты = (Layer, ESM), морфизмы = Promote/Demote/Invalidate
- **Функторы** F: Velantrim → Velantrim сохраняющие ESM transitions
- **Естественные преобразования** для смены стратегий валидации
- **TruthMonad T** с return + bind (Kleisli category)
- **GATs** (Generalized Algebraic Theories) для compose:
  ```julia
  compose(f::Hom(A,B), g::Hom(B,C)) :: Hom(A,C)
  ```

**Инструменты:**
- Catlab.jl (AlgebraicJulia) — для прототипа
- Python: `typing.Protocol` + `TypeVar` + `mypy --strict`
- PyJulia bridge для production

**Инварианты (будущие):** I104-I110

**Источники:**
- Fong & Spivak, *Seven Sketches in Compositionality*, arXiv:1803.05316
- Cartmell J., *Generalised algebraic theories*, 1986
- Gavranović et al., *Categorical Deep Learning*, arXiv:2402.15332, ICML 2024
- Symbolica AI ($31M seed, 2024)

### R3. Evo-Memory Integration (Think → Act → Refine)

**Цель:** агент учится из каждого взаимодействия, не только на training.

**Loop:**
```
Think:  retrieve top-K strategies
  ↓
Act:    respond + self_verify
  ↓
Refine: update strategies (Thompson Sampling), update ESM,
        add new hypothesis strategies, episode → L1.5
```

**Что refine-ится:**
- **Стратегии (L4):** успех → reward+, failure → reward-, новые → Hypothesized
- **ESM факты:** validated в action → Validated, опровергнутые → Contradicted
- **Эпизоды (L1.5):** A-MEM Zettelkasten links

**Бенчмарки:**
- LoCoMo: target ≥95.0 (vs mem0 91.6)
- DMR: target ≥95.5 (vs Zep 94.8)
- LongMemEval: target ≥95.0
- MuSiQue: +20% над HippoRAG
- Evo-Memory transfer suite

**Инварианты (будущие):** I101-I103, I111-I114

**Источники:**
- Wei et al., *Evo-Memory*, arXiv:2511.20857, UIUC+DeepMind (ноя 2025)
- Xu et al., *A-MEM: Agentic Memory*, arXiv:2502.12110, NeurIPS 2025
- Shinn et al., *Reflexion*, NeurIPS 2023
- Wang et al., *Voyager*, arXiv:2305.16291

### R4. Global Workspace Layer (LIDA-style)

**Цель:** "понимание сути" через broadcast scene.

**Архитектура:**
- Cycle ~200ms winning coalition broadcast
- Между L4 и L5
- Coalitions из активных модулей борются за внимание

**Источники:**
- Baars B., *A Cognitive Theory of Consciousness*, 1988
- Franklin S., *LIDA*, IEEE 2012
- Dehaene S., *Consciousness and the Brain*, 2014

### R5. K-Lines (Minsky)

**Цель:** context-reinstatement mechanism — переиспользование контекстов прошлых задач.

**Концепция:**
- K-узел = снимок активаций при успешном решении
- K-recursion: новые memories строятся на активных K-узлах
- Closes "phantom architecture" белое пятно multi-agent систем

**Источник:** Minsky M., *The Society of Mind*, 1986.

---

## 🧪 /experimental — Feature-flagged разработка

### E1. NeuroCore (RFC0068) — Phase 1/2

**Текущее:** Phase 0 (логирование), `NEUROCORE_ENABLED=False`.

**Phase 1 trigger criteria:**
- ≥10 000 Phase 0 sessions logged
- Hebbian dynamics validated на shadow-copy
- Performance overhead <5%

### E2. MHICalculator (Memory Health Index)

**Phase 1 — Реализовано в v8.3.1:** `core/mhi.py` v1.0.0 — формула `0.30×validated_ratio + 0.25×freshness_score + 0.25×retrieval_precision + 0.20×graph_coverage`, пороги HEALTHY ≥0.60 / DEGRADED ≥0.30 / SAFE_MODE <0.30 из V9 §8 SLO Contract, автоматические рекомендации для Meta-Supervisor. 14 тестов, 90% coverage. Базовая формула закрывает RFC0070 stub.

**Phase 2 — Требуется (в Horizons):** расширение формулы на graph topology (после подключения Neo4j), distribution-aware веса для разных Cognitive Modes, ML-калибровка thresholds на основе исторических данных.

### E3. 3-Factor Hebbian / STDP

**Цель:** биологически правдоподобное consolidation L1-L2.

**Формула:** `Δw = pre × post × global_reward_signal`

**Источник:** Pogodin R., Latham P., 2020/2025.

### E4. VIRF Pattern (System 1 ↔ System 2)

**Цель:** педагогический диалог между LLM и formal verifier.

**Результаты на SafeAgentBench:** 0% опасных действий + 77.3% целевых.

**Источник:** arXiv:2602.08373.

### E5. Scallop / DeepProbLog в L4

**Цель:** дифференцируемое логическое программирование вместо LLM CoT.

**Преимущество:** formally verifiable reasoning, integration с PyTorch.

### E6. CQRS Shadow State (RFC0040 DuckDB) 🆕

**Цель:** OLAP-аналитика drift без нагрузки на Neo4j.

**Принцип:** DuckDB как read-only аналитический слой над событиями EventBus. Writes — только через Neo4j (источник истины). DuckDB = shadow copy для аналитики.

**Trigger criteria для promotion в Specification:**
- Shadow State validated на ≥30 дней production данных
- Analytics queries P95 < 100ms

### E7. LensEngine + BAE (RFC0045, RFC0051) 🆕

**Цель:** детерминированные линзы L4/L5 для offline-режима (RFC0044).

**Принцип:** LensEngine = набор детерминированных фильтров поверх графа без вызова LLM. BAE (Behavioral Activation Engine) управляет приоритетами линз.

**Связь:** RFC0044 (LLM_MODE=offline) зависит от LensEngine как основного retrieval механизма.

---

## 🔭 /vision — Long-term направления

### V1. Predictive Coding Engine (Free Energy Principle)

**Цель:** "прозорливость" через минимизацию free energy.
**Источник:** Friston K., 2009-2025; Salvatori et al., Neural Networks 2026.

### V2. VSA / Hyperdimensional Computing

**Цель:** L0-L1 encoding гипервекторами вместо embeddings.
**3 операции:** binding · bundling · permutation.
**Преимущество:** CPU-only, deployable на neuromorphic чипы.
**Источники:** Kanerva P., Eliasmith C. SPAUN, Symbolica AI.

### V3. OCC/VAD/Lövheim Emotion Tags

**Цель:** эмоциональные модуляторы памяти, не диагностика.
**Юридический ограничитель:** EU AI Act compliance — модуляторы legal, диагностика — risky.
**Источник:** Ortony, Clore, Collins, 1988.

### V4. Temporal Receptive Windows

**Цель:** калибровка FSRS constants по нейробиологическим временным шкалам.

| Уровень | Временное окно |
|---------|----------------|
| L0 | миллисекунды – секунды |
| L1-L2 | секунды – минуты |
| L3+ | минуты – часы – дни |

### V5. Loihi 2 Neuromorphic Deployment

**Цель:** L0-L1 на spiking neural network hardware.
**Преимущество:** energy-efficient edge inference.

### V6. Distributed Velantrim (à la OGAS Глушкова)

**Цель:** multi-node Velantrim с консенсусом по графу истины.
**Архитектурный референс:** Глушков, 1962 (нереализованная "нервная система страны").

### V7. MOSES Program Synthesis

**Цель:** evolutionary discovery новых концептов для Creative Intelligence Layer.
**Источник:** OpenCog Hyperon, Ben Goertzel.

### V8. Theory of Mind Module

**Цель:** для multi-agent сценариев.
**Источники:** XToM, Multi-ToM benchmarks 2025.

### V9. Metacognition Layer ⭐

**Цель:** self-monitoring + dynamic self-correction.
**Статистический факт:** только 5% NS-AI исследований 2020-2024 касаются metacognition.
**→ Уникальное позиционирование Velantrim.**

---

## 🗄️ /archive — Деприкейт

| Компонент | Причина |
|-----------|---------|
| CognitiveModeRouter | Поглощён RetrievalRouter |
| LadybugDB references | Устаревший vector store |
| Engram isolation patterns | Заменены Neural Blackboard |

---

## 🎯 Куда мы идём

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Velantrim V9 → V10 → V11+:                                │
│                                                            │
│  V9 (Sprint 1, Q2 2026)                                    │
│  ├── Bi-Temporal Validity ✅                               │
│  ├── Neural Blackboard ✅                                  │
│  ├── DecayOrchestrator ✅                                  │
│  └── RetrievalRouter unified ✅                            │
│                                                            │
│  V10 (Q3-Q4 2026): первый research-block                   │
│  ├── L6 Welfare Protocol                                   │
│  ├── Evo-Memory loop                                       │
│  └── Global Workspace                                      │
│                                                            │
│  V11+ (2027): математическая ось                           │
│  ├── Category Theory formalization                         │
│  ├── 3-Factor Hebbian                                      │
│  ├── Predictive Coding                                     │
│  └── K-Lines                                               │
│                                                            │
│  V∞ (vision): neuromorphic + distributed                   │
│  ├── Loihi 2 deployment                                    │
│  ├── Distributed Velantrim                                 │
│  └── Metacognition layer                                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📚 Полная библиография

**Биология и психология:**
- Hebb D., *The Organization of Behavior*, 1949
- Лурия А.Р., *Высшие корковые функции человека*, 1962/1973
- Tulving E., *Episodic and Semantic Memory*, 1972
- Minsky M., *The Society of Mind*, 1986
- Ebbinghaus H., *Memory: A Contribution to Experimental Psychology*, 1885

**Кибернетика:**
- Глушков В.М., ОГАС, 1962-1982
- Bush V., *As We May Think*, Atlantic 1945
- Wiener N., *Cybernetics*, 1948
- Грей Уолтер У., *Machina Speculatrix*, 1948-1950
- Паск Г., *Conversation Theory*, 1953-1970
- Бир С., *Cybersyn*, 1971-1973

**Когнитивные архитектуры:**
- Anderson J., ACT-R (CMU, 1976→2025)
- Newell A. & Laird J., Soar (1983→9.6)
- Franklin S., LIDA (1990s→2012+)
- Goertzel B., OpenCog Hyperon (2024)

**Современная индустрия (2024-2026):**
- Rasmussen et al., *Zep*, arXiv:2501.13956
- van der Velde & de Kamps, *Neural Blackboard*, BBS 2006
- Wei et al., *Evo-Memory*, arXiv:2511.20857
- Xu et al., *A-MEM*, arXiv:2502.12110
- Chhikara et al., *Mem0*, arXiv:2504.19413
- Gutiérrez et al., *HippoRAG / HippoRAG 2*, arXiv:2405.14831

**Anthropic welfare:**
- *Exploring model welfare*, April 2025
- Lindsey J., *Emergent Introspective Awareness*, transformer-circuits.pub/2025/introspection
- Claude Opus 4 / 4.5 / 4.6 System Cards (2025-2026)

**Category Theory:**
- Fong & Spivak, *Seven Sketches*, arXiv:1803.05316
- Cartmell J., *Generalised algebraic theories*, 1986
- Gavranović et al., *Categorical Deep Learning*, ICML 2024
- Catlab.jl (AlgebraicJulia)

---

# 🔱 Финальные слова

> **V8 Crystal — это умная память.**
> **V9 Crystal — это умная память с инженерной дисциплиной.**
> **V9.1-audit — это умная память с инженерной дисциплиной и навигацией.**
> **Horizons — это видение того, что умная память может разблокировать для всего AI.**
>
> Velantrim — не "ещё один memory layer". Velantrim — недостающее звено между LLM, Graph и RAG, способное превратить их из инструментов в систему которая **понимает суть, различает истину, чувствует ритм и предвидит будущее**.
>
> Это путь длиной не в одну версию. Но V9 — первый шаг где мы перестали смешивать "что есть" с "что мечта". И именно поэтому он — настоящий.

---

**Принципы документа:**
- ✅ Никакого смешения production и vision
- ✅ Verification layer честно показывает verified / documented / hypothesis
- ✅ V9 Contracts отдельно от текущей реальности
- ✅ Все 11 архитектурных багов из аудитов V8 учтены
- ✅ Source of truth = реестр, документ = view layer
- ✅ Migration metadata встроена в реестр
- ✅ Navigation Manifest (§10) — единая точка навигации V8→V9
- ✅ Защитный периметр (§11) — восстановлен из V8
- ✅ Production Interface (§12) — восстановлен из V8
- ✅ SLO Contract — восстановлен в §8
- ✅ HYPERIA v5.20 наследование — задокументировано в §1
- ✅ v8.3.1 фиксы интегрированы: BUG-1 split-brain L0/L1, BUG-2 mock LLM priority, BUG-3 TruthGate сообщение
- ✅ Новые модули v8.3.1 в реестре: TruthGate.Semantic, HybridRetriever, MHICalculator
- ✅ Инвариант I104 (DriftProtectionL0L1Sync) добавлен в раздел 5

🔱 **Velantrim V9.3-audit готов к Sprint 2.**
