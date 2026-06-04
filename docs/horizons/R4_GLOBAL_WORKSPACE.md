# R4 — Global Workspace Layer (Horizons / LIDA-style)

> **Статус: 🔬 research** — в **VELANTRIM V8.6 Complex** нет `core/global_workspace_*`, флага `ENABLE_GLOBAL_WORKSPACE` нет. Архитектура описана в V9 (§R4); runtime — **не включён**.

## Зачем Global Workspace

Retrieval, Causal, Fusion и Focus работают **параллельно**, но агенту нужен единый «сцена-контекст» на один cognitive tick — что сейчас **достойно внимания**, а что фон.

**Global Workspace (GWT / LIDA)** — слой **между L4 и L5**:

- модули (Etir, Causal, ReasoningBank, Focus) формируют **коалиции** активаций;
- победитель (~200 ms cycle) **broadcast** в общий workspace;
- downstream (ответ LLM, PredictiveFusion, audit) читает только workspace, не весь граф.

Цель V9: **«понимание сути»** (gist intelligence) без смешения всех сигналов в один prompt.

## Архитектура (план)

```
[L4 модули] → Coalition bids (salience, novelty, goal_alignment)
        ↓
GlobalWorkspace.arbitrate()  ~200ms tick
        ↓
Winning coalition → broadcast ScenePacket
        ↓
[L5 / LLM / Fusion] ← единый контекст
```

## Планируемые компоненты (спека)

| Компонент | Назначение |
|-----------|------------|
| **Coalition** | Набор модулей + суммарный activation score |
| **WorkspaceArbiter** | Конкуренция коалиций, anti-thrashing |
| **ScenePacket** | Сериализуемый snapshot: факты, hints, focus vector |
| **BroadcastBus** | Подписчики Fast Path (не путать с EventBus Slow Path) |
| **WorkspaceMetrics** | Когерентность сцены, switch rate |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при Global Workspace |
|------------------|---------------------------|
| `core/focus_engine.py` | Частичный «winner» по goal_alignment (🟡 off) |
| `core/pipeline.py` | Собирает facts_pack вручную — заменить на ScenePacket |
| `core/predictive_fusion.py` | Вход L5 после broadcast |
| `core/etir_bridge.py`, `causal_bridge` | Кандидаты в коалицию |
| `core/exocortex_hooks.enrich_query_context` | Предшественник multi-section merge |

Сейчас merge секций **линейный**; GWS добавляет **конкуренцию за внимание** и лимит токенов на сцену.

## Чего Global Workspace **не** делает

- Не хранит долговременные факты (только ephemeral scene).
- Не заменяет Truth Gate / ESM.
- Не является отдельным embedding-индексом.

## Этапы (дорожная карта)

| Этап | Статус |
|------|--------|
| Описание в V9 §R4 | ✅ документировано |
| ScenePacket schema + pipeline hook | 🔬 research |
| Coalition из Focus + Etir + Causal | 🔬 research |
| 200ms arbiter (async tick) | 🔬 research |
| Production + бенчмарки gist quality | 🔜 V10+ |

## Источники

- V9 §R4 — Global Workspace Layer
- Baars B., *A Cognitive Theory of Consciousness*, 1988
- Franklin S., *LIDA*, IEEE 2012
- Dehaene S., *Consciousness and the Brain*, 2014

Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
