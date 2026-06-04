# R3 — Evo-Memory Integration (Horizons / Think → Act → Refine)

> **Статус: 🔬 research** — в **VELANTRIM V8.6 Complex** нет модуля `core/evo_memory_*`, флага `ENABLE_EVO_MEMORY` нет. Цикл описан в спеке V9 (§R3); production-runtime — **не включён**.

## Зачем Evo-Memory

Обычный RAG и статичный граф **не учатся** на каждом диалоге: стратегии ответа, веса доверия и эпизодические связи остаются прежними, пока оператор вручную не промотит факты.

**Evo-Memory** — замкнутый цикл после каждого взаимодействия:

```
Think:  retrieve top-K стратегий (L4 ReasoningBank)
  ↓
Act:    ответ + self_verify (Truth Gate / audit)
  ↓
Refine: обновить стратегии (Thompson Sampling), ESM-переходы,
        новые гипотезы, эпизоды → L1.5 Velum / A-MEM links
```

Агент **уточняет память из опыта**, не нарушая **Graph = Truth** (refine не пишет в Validated без Truth Gate).

## Что refine-ится (план)

| Объект | Действие при успехе / неудаче |
|--------|-------------------------------|
| **Стратегии (L4)** | reward+ / reward−; новые → Hypothesized |
| **ESM-факты** | подтверждённые в действии → Validated; опровергнутые → Contradicted |
| **Эпизоды (L1.5)** | Zettelkasten / A-MEM связи между сессиями |

## Планируемые компоненты (спека)

| Компонент | Назначение |
|-----------|------------|
| **StrategyRetriever** | Top-K из ReasoningBank по контексту запроса |
| **SelfVerifyHook** | Проверка ответа перед refine (Truth Gate + audit) |
| **RefineOrchestrator** | Единая точка post-turn: ESM + стратегии + Velum |
| **ThompsonBandit** | Обновление весов стратегий без LLM на каждом шаге |
| **EvoMetrics** | LoCoMo / DMR / LongMemEval — регрессия при включении |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при Evo-Memory |
|------------------|---------------------|
| `core/reasoning_bank.py` | Хранилище стратегий (🟡 off) |
| `core/truth_gate.py`, ESM | Граница promote после refine |
| `core/velum_bridge.py` | Эпизоды L1.5 после refine |
| `core/pipeline.py` | Точка внедрения post-query refine (будущее) |
| `core/response_audit.py` | Сигнал успеха/ошибки для reward |
| `core/event_bus.py` | Асинхронный Slow Path refine |

Частично перекрывается **SleepTimeWorker** (ночная консолидация без полного Think→Act→Refine на каждый turn).

## Целевые бенчмарки (V9)

| Бенчмарк | Target |
|----------|--------|
| LoCoMo | ≥ 95.0 (vs mem0 91.6) |
| DMR | ≥ 95.5 (vs Zep 94.8) |
| LongMemEval | ≥ 95.0 |
| MuSiQue | +20% vs HippoRAG |
| Evo-Memory transfer suite | внутренний регресс |

## Чего Evo-Memory **не** делает

- Не обучает embedding-модели end-to-end на пользовательских данных без политики.
- Не промотит в Validated в обход Truth Gate.
- Не заменяет L6 welfare — при Red volition refine записи блокируется.

## Этапы (дорожная карта)

| Этап | Статус |
|------|--------|
| Описание в V9 §R3 | ✅ документировано |
| ReasoningBank + Thompson (L4) | 🟡 код есть, off |
| Post-turn RefineOrchestrator | 🔬 research |
| A-MEM / Velum link automation | 🔬 research |
| Production контракт + бенчмарки | 🔜 V10+ |

## Будущие инварианты

I101–I103, I111–I114 (см. V9).

## Источники

- V9 §R3 — Evo-Memory Integration
- Wei et al., *Evo-Memory*, arXiv:2511.20857 (UIUC + DeepMind, 2025)
- Xu et al., *A-MEM: Agentic Memory*, arXiv:2502.12110, NeurIPS 2025
- Shinn et al., *Reflexion*, NeurIPS 2023
- Wang et al., *Voyager*, arXiv:2305.16291

Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
