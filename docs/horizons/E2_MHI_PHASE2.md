# E2 — MHICalculator Phase 2 (Horizons / RFC0070)

> **Статус: 🧪 experimental (Phase 2)** — **Phase 1 🟢 on** в `core/mhi.py`, `GET /reports/mhi`. Расширение формулы на топологию графа и ML-калибровку — **не включено**.

## Phase 1 (уже в V8.6)

| Компонент | Статус |
|-----------|--------|
| `core/mhi.py` | ✅ |
| Формула | `0.30×validated + 0.25×freshness + 0.25×precision + 0.20×graph` |
| Пороги | HEALTHY ≥0.60 · DEGRADED ≥0.30 · SAFE_MODE <0.30 |
| API | `GET /reports/mhi` |

## Phase 2 (Horizons)

| Цель | Описание |
|------|----------|
| Graph topology | Веса от Neo4j/sqlite graph coverage, не только count facts |
| Cognitive Modes | Разные пороги для PRECISION vs EXPLORATION |
| ML calibration | Исторические данные → динамические thresholds |
| Meta-Supervisor | Авто-рекомендации при деградации (связь L6 welfare) |

## Связь с V8.6

| Модуль | Роль |
|--------|------|
| `core/mhi.py` | База для расширения |
| `core/welfare_monitor.py` | Distress / error_rate как вход MHI |
| [E6_SHADOW_STATE.md](E6_SHADOW_STATE.md) | OLAP для калибровки Phase 2 |

## Этапы

| Этап | Статус |
|------|--------|
| RFC0070 Phase 1 | ✅ v8.3.1+ |
| Topology-aware weights | 🔬 research |
| Mode-aware SLO | 🔬 research |

Индекс: [`../HORIZONS.md`](../HORIZONS.md)
