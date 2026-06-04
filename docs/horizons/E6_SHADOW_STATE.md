# E6 — CQRS Shadow State (Horizons / RFC0040 DuckDB)

> **Статус: 🧪 experimental** — в **VELANTRIM V8.6 Complex** нет `core/shadow_state_*`, DuckDB-адаптера и флага `ENABLE_SHADOW_STATE`. Принцип CQRS описан в V9 (§E6); **read-only аналитика** — в исследовании, не в production.

## Зачем Shadow State

Оператору и Meta-Supervisor нужны **тяжёлые аналитические запросы** (drift ESM, volition rate, ошибки по источникам, welfare-тренды) без нагрузки на:

- основной SQLite/Neo4j граф истины,
- Fast Path запросов агента.

**Shadow State** — отдельный **OLAP-слой** (план: DuckDB), синхронизируемый из событий EventBus. Запись в граф истины по-прежнему только через L1 + Truth Gate.

## Принцип CQRS

| Сторона | Роль |
|---------|------|
| **Command** (writes) | Neo4j / SQLite graph — единственный источник истины |
| **Query** (analytics) | DuckDB shadow — копия событий и снимков для отчётов |

```
EventBus (Slow Path)
    → ShadowProjector (batch / stream)
        → DuckDB tables (read-only для API отчётов)
    → Graph writes (как сегодня, без дубля истины)
```

## Планируемые компоненты (спека)

| Компонент | Назначение |
|-----------|------------|
| **ShadowProjector** | Подписка на `CHAT_TURN`, `MEMORY_VOLITION`, `WELFARE_STATE_CHANGED`, ESM transitions |
| **DuckDBStore** | Партиции по дате; только INSERT/REPLACE из projector |
| **DriftAnalytics** | Отчёты split-brain L0/L1, semantic drift |
| **ShadowAPI** | `GET /analytics/drift` (read-only, отдельный API key) |
| **RetentionPolicy** | TTL сырых событий vs агрегаты |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при Shadow State |
|------------------|------------------------|
| `core/event_bus.py` | Источник событий для projector (🟡 off) |
| `core/mhi.py` | Phase 1 MHI — частично закрывает «здоровье» без DuckDB |
| `core/welfare_monitor.py` | Метрики welfare → события в shadow |
| `core/memory.py` | ESM transitions → shadow rows |
| `GET /reports/mhi` | Предшественник analytics API |

В V8.6 основная БД — **SQLite** (`VELANTRIM_DB_PATH`); DuckDB shadow не требует Neo4j, но в спеке V9 акцент на bi-temporal + Graphiti — projector должен быть backend-agnostic.

## Критерии promotion в Specification (V9)

| Критерий | Порог |
|----------|--------|
| Валидация на production-данных | ≥ 30 дней |
| Analytics queries P95 | < 100 ms |
| Нет рассинхрона с графом истины | аудит projector |

## Чего Shadow State **не** делает

- Не становится вторым графом истины (только **read replica** событий).
- Не принимает прямые `INSERT` фактов от агента.
- Не заменяет L0 Raw Memory (оригиналы остаются в `raw_memory`).

## Этапы (дорожная карта)

| Этап | Статус |
|------|--------|
| RFC0040 в V9 §E6 | ✅ документировано |
| EventBus schema freeze | 🟡 EventBus optional |
| DuckDB projector MVP | 🧪 experimental |
| Drift dashboards + SLO | 🔬 research |
| Production + `ENABLE_SHADOW_STATE` | 🔜 после критериев |

## Источники

- V9 §E6 — CQRS Shadow State (RFC0040)
- RFC0040 — CQRS Shadow State (DuckDB)
- Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
