# Horizons — исследовательская дорожная карта

> **Канон:** **VELANTRIM V8.6 Complex** (`VELANTRIM_ExoCortex_V8.6`, `server.py`).  
> Horizons — ответ на вопрос «куда дальше после ExoCortex», **без** обязательства production-контракта, пока модуль не включён флагом или не реализован.

Спека V9 (Часть II): [`Velantrim_V9_Final_Audited.md`](Velantrim_V9_Final_Audited.md)  
Карта runtime + research: [`LAYERS_AND_HORIZONS.ru.md`](LAYERS_AND_HORIZONS.ru.md)  
Graphiti fork (интеграция): [`RELATED_PROJECTS.ru.md`](RELATED_PROJECTS.ru.md)

---

## Легенда статусов

| Маркер | Значение |
|--------|----------|
| 🟢 **on** | Включено в runtime (флаг или всегда) |
| 🟡 **available_off** | Код в репозитории, **выключено** ENV (Beta / optional) |
| 🔬 **research** | Спека и дизайн; **нет** production-кода (например L2.5) |
| 🧪 **experimental** | Частичный код или Phase 0; не production |
| 🔭 **vision** | V10+; только в спеке |

**Важно:** `research` ≠ «сломано». Это осознанно **не включённый** слой, который ведётся в документации и API как будущее направление.

---

## Структура Horizons

```
docs/horizons/
├── README.md                 # полный индекс
├── L2_5_STAGING.md           # 🔬 L2.5
├── L6_VALUES_WELFARE.md      # L6
├── R2 … R5_*.md              # 🔬 research
├── E1 … E7_*.md              # 🧪 experimental (E2 → core/mhi.py)
```

| Каталог (логический) | Содержание | Примеры |
|----------------------|------------|---------|
| **/research** | Спека без runtime | **L2.5 Staging**, полный L6, Category Truth Gate, Evo-Memory, Global Workspace, K-Lines, LensEngine |
| **/experimental** | Feature-flag, черновик | NeuroCore, MHI Phase 2, Shadow State DuckDB, Hebbian/STDP |
| **/vision** | V10+ | Predictive Coding, VSA, neuromorphic, Distributed Velantrim |
| **/archive** | Deprecated | CognitiveModeRouter → RetrievalRouter |

---

## Runtime V8.6 (что уже в коде)

| Слой | Модуль | По умолчанию | Флаг |
|------|--------|--------------|------|
| L0 | `raw_memory` | 🟢 on | — |
| L1 | `memory`, `truth_gate`, `pipeline` | 🟢 on | `ENABLE_TRUTH_GATE` |
| L1.5 | Velum, Salience | 🟡 off | `ENABLE_VELUM`, `ENABLE_SALIENCE` |
| L2 | Concept Emergence | 🟡 off | `ENABLE_CONCEPT_EMERGENCE` |
| L3 | SQLite graph / storage_facade | 🟢 on | `STORAGE_BACKEND` |
| L3.5a/b | Etir, ImmutableCore | 🟡 off | `ENABLE_ETIR`, `ENABLE_IMMUTABLE_CORE` |
| L4 | Causal, ReasoningBank | causal 🟢 / bank 🟡 | `ENABLE_CAUSAL_GRAPH`, `ENABLE_REASONING_BANK` |
| L4.5 | Audit, Focus, Volition | 🟡 off | `ENABLE_L45` |
| L5.5 | PredictiveFusion | 🟡 off | `ENABLE_PREDICTIVE_FUSION` |
| L6 | Welfare MVP | 🟡 off | `ENABLE_L6_WELFARE` |
| — | SleepTimeWorker | 🟢 on* | `SLEEP_WORKER_ENABLED` |
| — | EventBus | 🟡 off | `ENABLE_EVENT_BUS` |

\* Sleep worker — только в V8.6, не в Graphiti fork.

**L2.5 Staging** — только 🔬 research: [`horizons/L2_5_STAGING.md`](horizons/L2_5_STAGING.md).

---

## /research — активные исследования (кратко)

| ID | Тема | RFC / источник | Карточка |
|----|------|----------------|----------|
| **L2.5** | Staging Layer | RFC0014 | [`horizons/L2_5_STAGING.md`](horizons/L2_5_STAGING.md) |
| **L6 full** | Values Core (полный) | RFC0069 | [`horizons/L6_VALUES_WELFARE.md`](horizons/L6_VALUES_WELFARE.md) |
| **R2** | Category-Theoretic Truth Gate | — | [`horizons/R2_CATEGORY_TRUTH_GATE.md`](horizons/R2_CATEGORY_TRUTH_GATE.md) |
| **R3** | Evo-Memory | — | [`horizons/R3_EVO_MEMORY.md`](horizons/R3_EVO_MEMORY.md) |
| **R4** | Global Workspace | — | [`horizons/R4_GLOBAL_WORKSPACE.md`](horizons/R4_GLOBAL_WORKSPACE.md) |
| **R5** | K-Lines (Minsky) | — | [`horizons/R5_K_LINES.md`](horizons/R5_K_LINES.md) |
| **FMR** | Fractal Memory Router | Qwen / MemTree / Stingy Context | [`FRACTAL_MEMORY_CANON.ru.md`](FRACTAL_MEMORY_CANON.ru.md) |
| **ELC** | Essence Layer Canon | gist, meaning chain, short answer, WhyTrace | [`ESSENCE_LAYER_CANON.ru.md`](ESSENCE_LAYER_CANON.ru.md) |
| **ANO** | Attention + Noetic Orchestration | GoalFrame, AttentionRouter, ComputeController, NoeticCore | [`ATTENTION_NOETIC_ORCHESTRATION.ru.md`](ATTENTION_NOETIC_ORCHESTRATION.ru.md) |
| **WKC** | World Knowledge Core | future work: quality, time, negative knowledge, contradiction review | [`WORLD_KNOWLEDGE_CORE_v1_0.ru.md`](WORLD_KNOWLEDGE_CORE_v1_0.ru.md) |
| — | KDE | — | [`horizons/KDE_DISTILLATION.md`](horizons/KDE_DISTILLATION.md) |

---

## L6 — две границы

| Часть | Статус в V8.6 |
|-------|----------------|
| **MVP** — WelfareMonitor, VolitionGate, EventBus | 🟡 `ENABLE_L6_WELFARE=0` |
| **Полный RFC0069** — IntrospectionProbe, RingZeroProtector | 🔬 research (V10) |

```bash
ENABLE_L6_WELFARE=1
ENABLE_EVENT_BUS=1
```

API: `GET /welfare` · `POST /memory/volition` · `GET /layers/status` · `GET /horizons`

---

## /experimental (кратко)

| ID | Тема | В V8.6 |
|----|------|--------|
| E1 | NeuroCore | [`horizons/E1_NEUROCORE.md`](horizons/E1_NEUROCORE.md) |
| E2 | MHI Phase 2 | [`horizons/E2_MHI_PHASE2.md`](horizons/E2_MHI_PHASE2.md) · Phase 1 в `core/mhi.py` 🟢 |
| E3 | Hebbian / STDP | [`horizons/E3_HEBBIAN_STDP.md`](horizons/E3_HEBBIAN_STDP.md) |
| E4 | VIRF Pattern | [`horizons/E4_VIRF_PATTERN.md`](horizons/E4_VIRF_PATTERN.md) |
| E5 | Scallop / DeepProbLog | [`horizons/E5_SCALLOP_DPP.md`](horizons/E5_SCALLOP_DPP.md) |
| E6 | Shadow State DuckDB | [`horizons/E6_SHADOW_STATE.md`](horizons/E6_SHADOW_STATE.md) |
| E7 | LensEngine + BAE | [`horizons/E7_LENS_ENGINE_BAE.md`](horizons/E7_LENS_ENGINE_BAE.md) |

---

## Почему L6 не в «памяти L0–L5»

| Факт | Пояснение |
|------|-----------|
| Память V9 = **L0–L5** (+ L3.5, L4.5, L5.5 Beta) | Ingest / recall / Truth Gate |
| **L6** = ценности + welfare + introspection | Horizons + MVP-флаг |
| **L2.5** = staging гипотез | Только Horizons, без кода |

---

## Связь с ядром (мосты для будущих слоёв)

| Сейчас (V8.6) | Роль при Horizons |
|---------------|-------------------|
| `truth_gate.py`, ESM | Boundary / fail-rate → WelfareMonitor |
| `memory_volition.py` | VolitionGate при Red welfare |
| `immutable_core.py` | Ring Zero snapshots (Beta) |
| `focus_engine.py`, `response_audit.py` | goal_alignment, introspection traces |
| `goal_frame.py`, `attention_router.py`, `compute_controller.py`, `noetic_core.py` | P0-контракты внешней когнитивной оркестрации |
| `sleep_time_worker.py` | Ночная консолидация (частично вместо L2.5 scheduler) |
| `event_bus.py` | Slow Path метрики |

---

## Roadmap (из V9)

- **V8.6 (сейчас):** ESM, pipeline, ExoCortex optional, L6 MVP, SleepTimeWorker
- **V9 target:** Bi-Temporal, Blackboard, DecayOrchestrator, Beta Etir/L4.5
- **V10 (research-block):** L2.5, полный L6, Evo-Memory, Global Workspace
- **V11+:** формализация Truth Gate, Predictive Coding, K-Lines

---

## API и документация

- `GET /layers/status` — `layers` (runtime) + `horizons` (research / experimental / optional)
- Индекс карточек: [`horizons/README.md`](horizons/README.md)
