# L2.5 — Staging Layer (Horizons / RFC0014)

> **Статус: 🔬 research** — в **VELANTRIM V8.6 Complex** нет модуля `core/staging_*`, флага `ENABLE_L2_5` нет. Слой описан в спеке V9; включение в runtime — **не планируется** до отдельного RFC-ревью.

## Зачем L2.5

Между **L2 Medium-Term** (кластеры, среднесрочные паттерны) и **L3 Knowledge Graph** нужен буфер для материала, который:

- уже осмыслен эвристиками L2, но
- ещё **не прошёл** Truth Gate / promote в Validated,
- или ждёт **Resource-Aware Scheduler** (CPU, очередь ingest, welfare Yellow/Red).

Staging — не второй граф истины: это **очередь гипотез** с TTL, приоритетом и явным отказом от автоматического promote.

## Планируемые компоненты (спека)

| Компонент | Назначение |
|-----------|------------|
| **StagingBuffer** | SQLite/память: записи `staging_id`, `claim`, `provenance`, `priority`, `expires_at` |
| **ResourceAwareScheduler** | Откладывает promote/ingest при нагрузке или L6 Yellow/Red |
| **PromoteGate** | Единственный выход в L3 — только через Truth Gate + ESM |
| **Decay stub** | Быстрое устаревание неподтверждённых гипотез |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при появлении L2.5 |
|------------------|-------------------------|
| `core/truth_gate.py` | Граница promote из staging |
| `core/memory.py` ESM | Целевое состояние после staging |
| `core/welfare_monitor.py` (L6 MVP) | Сигнал для scheduler: отложить фоновый promote |
| `core/sleep_time_worker.py` | Частично закрывает «ночную консолидацию» без отдельного staging |

## Чего L2.5 **не** делает

- Не заменяет L0 Raw Memory (оригинал остаётся immutable).
- Не дублирует Etir / Velum — это другие уровни (L1.5 / L3.5).
- Не обходит Truth Gate (инвариант **Graph = Truth**).

## Этапы (дорожная карта)

| Этап | Статус |
|------|--------|
| RFC0014 в V9 Specification | ✅ документировано |
| Прототип StagingBuffer | 🔬 research |
| Интеграция с EventBus / L6 scheduler | 🔬 research |
| Production контракт + тесты | 🔜 V10+ |

## Источники

- V9 §3.2 — L2.5 Staging Layer
- RFC0014 (Resource-Aware Scheduler)
- Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта слоёв: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
