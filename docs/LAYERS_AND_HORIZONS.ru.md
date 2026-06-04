# Карта слоёв и Horizons — VELANTRIM V8.6 Complex

> Актуально для `GET /layers/status` и `.env.example`.  
> **Graphiti_fractal-main** — отдельный fork; канон документации Horizons — **здесь**.

## Легенда

| Статус | Смысл |
|--------|--------|
| 🟢 on | Работает по умолчанию |
| 🟡 available_off | Код есть, **выключено** (`ENABLE_*=0`) |
| 🔬 research | Только спека / дизайн, **нет** runtime-модуля |
| 🧪 experimental | Частичная реализация или Phase 0 |

---

## Runtime — слои с кодом в V8.6

| Слой | Модуль / путь | Статус | ENV |
|------|---------------|--------|-----|
| **L0** | `core/raw_memory.py` | 🟢 on | — |
| **L1** | `memory`, `truth_gate`, `pipeline` | 🟢 on | `ENABLE_TRUTH_GATE` |
| **L1.5** | Velum, Salience | 🟡 off | `ENABLE_VELUM`, `ENABLE_SALIENCE` |
| **L2** | Concept Emergence | 🟡 off | `ENABLE_CONCEPT_EMERGENCE` |
| **L2.5** | Staging | 🔬 research | — (нет флага) |
| **L3** | `storage_facade`, graph backends | 🟢 on | `STORAGE_BACKEND` |
| **L3.5a** | Etir | 🟡 off | `ENABLE_ETIR` |
| **L3.5b** | ImmutableCore | 🟡 off | `ENABLE_IMMUTABLE_CORE` |
| **L4** | Causal | 🟢 on* | `ENABLE_CAUSAL_GRAPH` |
| **L4** | ReasoningBank | 🟡 off | `ENABLE_REASONING_BANK` |
| **L4.5** | Audit, Focus, Volition | 🟡 off | `ENABLE_L45` |
| **L5.5** | PredictiveFusion | 🟡 off | `ENABLE_PREDICTIVE_FUSION` |
| **—** | DecayOrchestrator | 🟡 off | `ENABLE_DECAY_ORCHESTRATOR` |
| **L6** | Welfare MVP | 🟡 off | `ENABLE_L6_WELFARE` |
| **—** | EventBus | 🟡 off | `ENABLE_EVENT_BUS` |
| **—** | SleepTimeWorker | 🟢 on* | `SLEEP_WORKER_ENABLED` |

\* Causal и Sleep — по умолчанию включены; отключение через ENV при необходимости.

---

## Horizons — research (не включены, ведутся в docs)

| ID | Название | RFC | Документ |
|----|----------|-----|----------|
| **L2_5_staging** | L2.5 Staging Layer | RFC0014 | [horizons/L2_5_STAGING.md](horizons/L2_5_STAGING.md) |
| **L6_full_rfc0069** | L6 полный (Introspection, RingZero) | RFC0069 | [horizons/L6_VALUES_WELFARE.md](horizons/L6_VALUES_WELFARE.md) |
| **R2_category_truth_gate** | Category Truth Gate | — | [horizons/R2_CATEGORY_TRUTH_GATE.md](horizons/R2_CATEGORY_TRUTH_GATE.md) |
| **R3_evo_memory** | Evo-Memory (Think→Act→Refine) | — | [horizons/R3_EVO_MEMORY.md](horizons/R3_EVO_MEMORY.md) |
| **R4_global_workspace** | Global Workspace (LIDA) | — | [horizons/R4_GLOBAL_WORKSPACE.md](horizons/R4_GLOBAL_WORKSPACE.md) |
| **R5_k_lines** | K-Lines (Minsky) | — | [horizons/R5_K_LINES.md](horizons/R5_K_LINES.md) |
| **kde** | Knowledge Distillation | — | [horizons/KDE_DISTILLATION.md](horizons/KDE_DISTILLATION.md) |

---

## Horizons — experimental

| ID | Название | В репозитории V8.6 |
|----|----------|---------------------|
| **E1_neurocore** | NeuroCore (Plastic Memory) | [horizons/E1_NEUROCORE.md](horizons/E1_NEUROCORE.md) |
| **E2_mhi_phase2** | MHI Phase 2 | [horizons/E2_MHI_PHASE2.md](horizons/E2_MHI_PHASE2.md) · Phase 1 🟢 `core/mhi.py` |
| **E6_shadow_state** | CQRS Shadow State (DuckDB) | [horizons/E6_SHADOW_STATE.md](horizons/E6_SHADOW_STATE.md) |
| **E7_lens_engine_bae** | LensEngine + BAE (offline) | [horizons/E7_LENS_ENGINE_BAE.md](horizons/E7_LENS_ENGINE_BAE.md) |
| **E3_hebbian_stdp** | 3-Factor Hebbian / STDP | [horizons/E3_HEBBIAN_STDP.md](horizons/E3_HEBBIAN_STDP.md) |
| **E4_virf_pattern** | VIRF System 1↔2 | [horizons/E4_VIRF_PATTERN.md](horizons/E4_VIRF_PATTERN.md) |
| **E5_scallop_dpp** | Scallop / DeepProbLog | [horizons/E5_SCALLOP_DPP.md](horizons/E5_SCALLOP_DPP.md) |

---

## L6 — две строки в таблице

| Вариант | Статус | Что включить |
|---------|--------|--------------|
| **L6 MVP** | 🟡 available_off | `ENABLE_L6_WELFARE=1`, `ENABLE_EVENT_BUS=1` |
| **L6 полный RFC0069** | 🔬 research | IntrospectionProbe, RingZeroProtector — без кода |

---

## Проверка

```bash
curl -s http://localhost:8000/layers/status | jq '.horizons.research[] | select(.id=="L2_5_staging")'
```

Полный индекс: [HORIZONS.md](HORIZONS.md) · [horizons/README.md](horizons/README.md) · концепт **Umwelt / Innenwelt / Eigenwelt**: [ORGANIC_MEMORY_AND_WELTS.ru.md](ORGANIC_MEMORY_AND_WELTS.ru.md)
