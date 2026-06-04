# E3 — 3-Factor Hebbian / STDP (Horizons)

> **Статус: 🧪 experimental** — в **VELANTRIM V8.6 Complex** нет отдельного `core/hebbian_*`; формула используется в планах **E1 NeuroCore** и **decay_orchestrator** (🟡 off). Standalone модуль — **не включён**.

## Зачем E3

Консолидация L1–L2 сегодня разбита: FSRS (Velum), ACT-R decay, эвристики sleep worker. Нужна **единая биологически мотивированная** формула изменения «силы» связи:

```
Δw = pre × post × global_reward_signal
```

- **pre / post** — активность до/после recall или ingest;
- **global_reward_signal** — успех задачи, welfare, truth pass/fail.

E3 — **математическое ядро**; **E1 NeuroCore** — runtime-обёртка с shadow graph.

## Планируемые компоненты

| Компонент | Назначение |
|-----------|------------|
| **HebbianUpdate** | Чистая функция Δw |
| **STDPWindow** | Временное окно pre/post (мс–сек для L1, мин–час для L2) |
| **RewardBridge** | Связь с audit, MHI, welfare |
| **ClampPolicy** | min/max weight, не ломать graph invariants |

## Связь с V8.6 сегодня

| Сейчас | Роль |
|--------|------|
| `core/fsrs.py` | Частичный temporal decay |
| `core/decay_orchestrator.py` | Координация (🟡 off) |
| `core/sleep_time_worker.py` | Batch consolidate без 3-factor |
| [E1_NEUROCORE.md](E1_NEUROCORE.md) | Plasticity engine consumer |

## Этапы

| Этап | Статус |
|------|--------|
| V9 §E3 | ✅ |
| Unit tests на Δw | 🔬 research |
| Интеграция NeuroCore Phase 1 | 🔜 |

## Источники

- V9 §E3
- Pogodin R., Latham P., 2020/2025

Индекс: [`../HORIZONS.md`](../HORIZONS.md)
