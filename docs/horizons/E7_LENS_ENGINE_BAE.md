# E7 — LensEngine + BAE (Horizons / RFC0045, RFC0051)

> **Статус: 🧪 experimental** — в **VELANTRIM V8.6 Complex** нет `core/lens_engine_*`, `core/bae_*`, флага `ENABLE_LENS_ENGINE` нет. Зависит от **offline-режима** (RFC0044); **не включён** в runtime.

## Зачем LensEngine + BAE

В **offline** (`LLM_PROVIDER=none`) агент всё равно должен отвечать из памяти **детерминированно**:

- без CoT-галлюцинаций LLM;
- с предсказуемым retrieval по графу;
- с приоритетами «линз» (временная, каузальная, доверие, Ring Zero).

**LensEngine** — набор **линз** (фильтров) поверх фактов/рёбер.  
**BAE** (Behavioral Activation Engine) — выбирает **какую линзу** применить по контексту запроса и Cognitive Mode.

## Принцип (RFC0044 + RFC0045)

```
Query + CognitiveMode
    ↓
BAE.select_lenses() → ordered lens stack
    ↓
LensEngine.apply_each(facts, graph) → narrowed FactsPack
    ↓
FactRouter / HybridRetriever (без LLM)
    ↓
Детерминированный ответ (template + citations)
```

## Планируемые компоненты (спека)

| Компонент | Назначение |
|-----------|------------|
| **Lens** | Protocol: `filter(facts, graph, ctx) → facts` |
| **TemporalLens** | Bi-temporal окна, recency |
| **CausalLens** | Подграф по causes/requires |
| **TrustLens** | ESM ≥ Supported, source trust |
| **RingZeroLens** | Только immutable / core values |
| **BAE** | Активация линз по mode: PRECISION vs EXPLORATION |
| **LensComposition** | RFC0051 — порядок и merge политики |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при LensEngine |
|------------------|---------------------|
| `core/truth_gate.py` | Cognitive Modes — вход BAE |
| `core/pipeline.py` | `FactsPackBuilder` — заменить/обогатить lens stack |
| `core/hybrid_retriever.py` | BM25+RRF без линз |
| `server.py` | `LLM_PROVIDER=none` — целевой offline сценарий |
| `core/causal_graph.py` | Данные для CausalLens |

**FactRouter** (RFC0038) в V9 — предшественник; LensEngine — **композиция** детерминированных фильтров вместо одного роутера.

## Связь с RFC0044 (offline)

| Режим | Поведение |
|-------|-----------|
| `online` | LensEngine опционален (LLM основной) |
| `offline` | LensEngine + BAE **обязательны** для ответа |
| `lite` | Подмножество линз + SLM |

Инвариант V9: в `offline` **LLM не вызывается**.

## Чего LensEngine **не** делает

- Не промотит факты в Validated (только фильтрация read path).
- Не заменяет Truth Gate при записи.
- Не является embedding-поиском (работает поверх уже retrieved facts).

## Этапы (дорожная карта)

| Этап | Статус |
|------|--------|
| RFC0045/0051 в V9 §E7 | ✅ документировано |
| Lens protocol + 2 линзы (Trust, Temporal) | 🔬 research |
| BAE + CognitiveMode mapping | 🔬 research |
| Offline path в pipeline | 🔜 после RFC0044 контракта |
| Production + `ENABLE_LENS_ENGINE` | 🔜 V10+ |

## Источники

- V9 §E7 — LensEngine + BAE
- RFC0044 — LLM modes (offline)
- RFC0045 — LensEngine
- RFC0051 — Lens composition

Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
