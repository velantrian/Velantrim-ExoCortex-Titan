# R5 — K-Lines (Horizons / Minsky)

> **Статус: 🔬 research** — в **VELANTRIM V8.6 Complex** нет `core/k_lines_*`, флага `ENABLE_K_LINES` нет. Механизм context-reinstatement описан в V9 (§R5); **не в runtime**.

## Зачем K-Lines

Multi-agent и длинные сессии страдают от **«phantom architecture»**: агент не восстанавливает контекст прошлой успешной задачи, а заново собирает retrieval с нуля.

**K-Line** (Minsky, *Society of Mind*):

- при **успешном** решении задачи сохраняется снимок активаций (какие модули, факты, стратегии были активны);
- при похожем новом запросе **K-reinstatement** поднимает тот же контекст;
- новые воспоминания могут строиться **поверх** активных K-узлов (рекурсия).

Цель: переиспользование проверенных контекстов без дублирования графа истины.

## Концепция (план)

```
Успешная задача T
    ↓
KNode(snapshot: modules, facts, strategies, focus)
    ↓
Новая задача T' ~ T
    ↓
match_k_lines(T') → reinstate → ускоренный retrieve + меньше шума
```

## Планируемые компоненты

| Компонент | Назначение |
|-----------|------------|
| **KNode** | Immutable snapshot активаций (ссылки на fact_id, strategy_id) |
| **KIndex** | Similarity по task embedding / тегам домена |
| **ReinstatementEngine** | Восстановление FactsPack + Focus из KNode |
| **KRecursion** | Новые эпизоды Velum привязаны к parent K |
| **KDecay** | Устаревание K-узлов при смене домена |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при K-Lines |
|------------------|------------------|
| `core/reasoning_bank.py` | Стратегии в snapshot |
| `core/focus_engine.py` | Focus vector в KNode |
| `core/velum.py` | Эпизоды как носители K-recursion |
| `core/pipeline.py` | Hook: `reinstate_before_retrieve` |
| `core/exocortex_hooks` | Аналог «сцены» без полного GWS |

Частично пересекается с **R4 Global Workspace** (broadcast сцены) и **R3 Evo-Memory** (refine после задачи).

## Чего K-Lines **не** делает

- Не копирует факты в обход ESM (только ссылки на canonical ids).
- Не заменяет Truth Gate при promote.
- Не является отдельной embedding-БД (индекс поверх существующего графа).

## Этапы

| Этап | Статус |
|------|--------|
| V9 §R5 | ✅ |
| KNode schema + storage | 🔬 research |
| Reinstatement в pipeline | 🔬 research |
| Multi-agent bench | 🔜 V10+ |

## Источники

- V9 §R5 — K-Lines (Minsky)
- Minsky M., *The Society of Mind*, 1986

Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
