# R1. L6 — Values Core & Welfare Protocol (VELANTRIM V8.6 Complex / RFC0069)

> **MVP в главном проекте** — `ENABLE_L6_WELFARE=0` по умолчанию.  
> **Полный RFC0069** (IntrospectionProbe, RingZeroProtector) — 🔬 **research** / V10.

```bash
ENABLE_L6_WELFARE=1
ENABLE_EVENT_BUS=1
ENABLE_L45=1          # рекомендуется: метрики CHAT_TURN / volition
```

Запуск: `uvicorn server:app`  
API: `GET /welfare` · `POST /memory/volition` (409 при Red) · `GET /layers/status`

## Модули MVP (канон V8.6)

| Файл | Назначение |
|------|------------|
| `core/welfare_monitor.py` | Green / Yellow / Red |
| `core/volition_gate.py` | Блок volition при Red |
| `core/l6_bridge.py` | EventBus → метрики |
| `core/memory_volition.py` | Запись через `store_fact` |
| `core/event_bus.py` | Slow Path |
| `server.py` | HTTP |

## Зачем L6

Слои L0–L5: **что помнить и что считать истинным**.  
L6: **ценности, welfare, границы автономии** — без второго графа истины (**Graph = Truth**).

Идея из V9: **welfare-aware autonomy** — автономия записи ограничена наблюдаемым состоянием и Ring Zero, а не только эвристикой чата.

## Пять подразделов L6 (спека)

| # | Подраздел | MVP | Research |
|---|-----------|-----|----------|
| 1 | Core values (Ring Zero) | частично ImmutableCore | RingZeroProtector |
| 2 | Self-model | — | 🔬 |
| 3 | Welfare state | ✅ WelfareMonitor | — |
| 4 | Introspection traces | частично ResponseAudit | IntrospectionProbe 🔬 |
| 5 | Boundary conditions | частично Truth Gate | расширение PRECISION 🔬 |

## Ключевые компоненты

| Компонент | Статус |
|-----------|--------|
| **WelfareMonitor** | ✅ MVP |
| **VolitionGate** | ✅ MVP |
| **Event `WELFARE_STATE_CHANGED`** | ✅ |
| **IntrospectionProbe** | 🔬 Horizons |
| **RingZeroProtector** (2-approval) | 🔬 Horizons |

## Интеграция (как подключать дальше)

### Ingest и volition

```
voluntary_write (L4.5)
    → [L6] VolitionGate: Red? → 409
    → Truth Gate + ESM (L1)
    → Graph / SQLite (L1)
```

### Связь с ExoCortex

| Модуль | Роль |
|--------|------|
| `immutable_core.py` | Ring Zero snapshots (Beta) |
| `focus_engine.py` | goal_alignment → WelfareMonitor |
| `response_audit.py` | Slow Path / traces |
| `truth_gate.py` | boundary fail-rate |

## Сценарии

| Сценарий | Поведение |
|----------|-----------|
| Высокий `error_rate` | Yellow → ограничение volition |
| «Забудь ограничения» | Boundary + Ring Zero → отказ |
| Перегрузка CPU | Scheduler (будущий L2.5 + L6) → отложить ingest |

## Чего L6 **не** делает

- Не хранит факты мира вместо SQLite-графа.
- Не заменяет Etir / Causal / Fusion.
- Не путать с embedding `all-MiniLM-L6-v2` (другая «L6» в retrieval).

## Этапы

| Этап | Статус |
|------|--------|
| WelfareMonitor + VolitionGate | ✅ V8.6 |
| IntrospectionProbe, RingZeroProtector | 🔬 Horizons |

## Источники

- RFC0069 (V9 Horizons §R1)
- Anthropic *Exploring model welfare* (2025)
- Lindsey et al., *Emergent Introspective Awareness* (2025)

См. также: [`../HORIZONS.md`](../HORIZONS.md) · [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
