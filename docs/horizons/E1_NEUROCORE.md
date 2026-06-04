# E1 — NeuroCore / Plastic Memory Layer (Horizons / RFC0068)

> **Статус: 🧪 experimental** — в **VELANTRIM V8.6 Complex** нет `core/neurocore_*`, флаг `NEUROCORE_ENABLED` не подключён. В спеке V9 — Phase 0 (логирование); **plastic consolidation** — в исследовании.

## Зачем NeuroCore

Классический decay (FSRS, ACT-R, Hebbian) размазан по слоям и конфликтует (см. V9: DecayOrchestrator). **NeuroCore** — единый **пластический** слой:

- симулирует Hebbian / STDP-подобное усиление связей при успешном recall;
- ослабляет неиспользуемые пути;
- ведёт **shadow-copy** графа для экспериментов без мутации истины.

Цель: биологически правдоподобная консолидация **L1–L2** без нарушения **Graph = Truth**.

## Фазы (V9 / RFC0068)

| Phase | Содержание | Статус |
|-------|------------|--------|
| **0** | Только логирование активаций, без изменения весов | 🧪 спека |
| **1** | Hebbian на shadow-copy, overhead < 5% | 🔬 после критериев |
| **2** | Promotion в production graph через Truth Gate | 🔜 V10+ |

### Критерии входа в Phase 1

- ≥ 10 000 Phase 0 sessions в логах
- Hebbian dynamics валидированы на shadow-copy
- Performance overhead < 5% на Fast Path

## Планируемые компоненты (спека)

| Компонент | Назначение |
|-----------|------------|
| **ActivationLogger** | Phase 0: episodic pre/post synaptic activity |
| **ShadowGraph** | Копия рёбер для plastic updates |
| **PlasticityEngine** | `Δw = f(pre, post, reward)` |
| **NeuroCoreBridge** | Slow Path EventBus → batch consolidate |
| **SafetyGate** | Никаких writes в canonical graph без promote |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при NeuroCore |
|------------------|---------------------|
| `core/fsrs.py` | Базовый decay (Velum) |
| `core/decay_orchestrator.py` | 🟡 off — координация decay |
| `core/velum.py` | Эпизодический pre-graph L1.5 |
| `core/event_bus.py` | Slow Path для batch plasticity |
| `core/sleep_time_worker.py` | Ночная консолидация (частичный аналог) |

**E3 Hebbian/STDP** (отдельная карточка в Horizons) — формула; NeuroCore — **runtime-обёртка** вокруг неё.

## Чего NeuroCore **не** делает

- Не меняет ESM-статусы напрямую (только веса/салience до Truth Gate).
- Не заменяет Etir spreading activation.
- Не обучает LLM.

## Этапы (дорожная карта)

| Этап | Статус |
|------|--------|
| RFC0068 в V9 §E1 | ✅ документировано |
| Phase 0 logger | 🧪 experimental |
| Shadow graph + Hebbian | 🔬 research |
| Integration DecayOrchestrator | 🔜 V10+ |

## Источники

- V9 §E1 — NeuroCore (RFC0068)
- RFC0068 — Plastic Memory Layer
- Pogodin R., Latham P. — 3-factor Hebbian (см. также E3 в Horizons)

Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
