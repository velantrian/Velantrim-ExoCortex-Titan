# 🧠 Attention + Noetic Orchestration Canon v1.0

Статус: P0-контракты добавлены, runtime-интеграция не включена автоматически.

Этот документ фиксирует честный вывод из аудита FQKVE / attention / memory
discussion: Velantrim не должен становиться “новым Transformer”. Его сила в
другом: во внешнем прозрачном слое, который управляет целью, фокусом, памятью,
доказательствами, глубиной вычислений и проверкой перед тем, как LLM оформляет
ответ.

## 1. Главный принцип

```text
LLM = голос
Graph = истина
FactsPack = доказательства
TruthGate = запрет выдумки
AttentionRouter = фокус
ComputeController = глубина мышления
FractalMemory = память
ReflectionObserver = самопроверка
NoeticCore = суть + причинность + прогноз
```

Transformer attention выбирает токены внутри модели. Velantrim attention должен
выбирать факты, источники и маршруты снаружи модели.

## 2. Что НЕ утверждаем

| Нельзя говорить | Почему |
|---|---|
| “FQKVE — новый Transformer” | нет реализации новой нейроархитектуры |
| “Velantrim лучше Titans/Mamba/ATLAS” | нет собственных benchmark/ablation |
| “PaTH подтверждает route memory” | PaTH — positional encoding, не episodic memory |
| “dense LLM сбрасывает веса на лету” | можно управлять контекстом/KV/экспертами, но не произвольно отключать веса |
| “предсказание = факт” | prediction всегда остаётся hypothesis/inference до проверки |

## 3. Что принимаем

| Идея | Инженерное имя в Velantrim | Статус |
|---|---|---|
| F / зачем | `GoalFrame` | P0 contract |
| E / маршрут и отбор | `AttentionRouter` | P0 contract |
| C / сколько думать | `ComputeController` | P0 contract |
| H / рабочая и эпизодическая память | FractalMemory L0-L3 | уже есть canon/code skeleton |
| S / “сон” | `ConsolidationCycle` | уже есть частично через consolidation/sleep |
| R / самопроверка | Observer + TruthGate + Trace | уже есть частично |
| W / World Model | `NoeticCore` | P0 contract + future runtime |

## 4. P0-модули

### `core/goal_frame.py`

Задача: понять, зачем пользователь спрашивает.

Выход:

```json
{
  "intent": "analyze",
  "risk_level": "medium",
  "domain_hint": "engineering",
  "output_style": "deep",
  "constraints": [],
  "reasons": ["analysis marker", "deep answer requested"]
}
```

### `core/attention_router.py`

Задача: выбрать факты, которые достойны попасть в FactsPack / NoeticCore.

Скоринг:

```text
score =
  goal_fit
  + relevance
  + trust
  + graph proximity
  + memory priority
  + lens boost
  - risk
  - noise
```

Важно: это не softmax над токенами. Это прозрачное ранжирование фактов.

### `core/compute_controller.py`

Задача: решить, какой путь нужен.

| Путь | Когда |
|---|---|
| `FAST_PATH` | простой короткий вопрос |
| `NORMAL_PATH` | обычный ответ |
| `DEEP_PATH` | сложный анализ / сравнение / объяснение |
| `VERIFY_PATH` | high-risk или проверка фактов |
| `CREATIVE_PATH` | творческий режим, но с пометкой статусов |

### `core/noetic_core.py`

Задача: выделить суть, причинность, возможные последствия и границы знания.

Выход:

```json
{
  "essence": "главная суть по фактам",
  "causal_chain": ["A --causes--> B"],
  "predictions": [
    {
      "kind": "prediction",
      "statement": "If A holds, B may follow",
      "confidence": 0.62,
      "basis": ["fact_a", "fact_b"],
      "uncertainty": ["prediction_requires_review"]
    }
  ],
  "uncertainties": ["no_relations_available"]
}
```

Главное правило: `NoeticCore` не создаёт truth. Он только маркирует выводы.

## 5. Будущий runtime pipeline

```text
User Query
  ↓
GoalFrame
  ↓
ComputeController
  ↓
Retrieval / Graph / FractalMemory
  ↓
AttentionRouter
  ↓
FactsPack
  ↓
TruthGate
  ↓
NoeticCore
  ↓
ReflectionObserver
  ↓
BAE / Small LLM
  ↓
Answer + Trace
  ↓
ConsolidationCycle
```

В P0 эти модули не подключаются автоматически к `/query`. Это сделано
намеренно: сначала контракт, потом тесты, потом флаговая интеграция.

## 6. Почему это полезно простому человеку

Без этого обычный AI часто делает так:

```text
прочитал вопрос -> сгенерировал красивый ответ
```

С этим слоем Velantrim должен делать так:

```text
понял цель
выбрал нужные факты
отбросил шум
проверил источники
понял суть
построил причинную цепочку
отметил, где не уверен
ответил коротко и честно
```

## 7. Связь с существующей архитектурой

| Уже есть | Новый слой использует |
|---|---|
| `facts_pack.py` | `AttentionRouter` выбирает кандидатов перед FactsPack |
| `truth_gate.py` | `ComputeController` требует gate для verify/deep paths |
| `trace.py` | future `AttentionTrace` должен логировать route decisions |
| `causal_graph.py` | `NoeticCore` строит causal_chain/predictions |
| `salience.py` | `AttentionRouter` учитывает memory/salience priority |
| `fractal_memory.py` | H-уровни памяти для будущего routing |
| `consolidation_engine.py` / `sleep_time_worker.py` | S / consolidation |

## 8. Каноническая формула

```text
Velantrim Orchestration =
  GoalFrame
  + AttentionRouter
  + FractalMemory
  + FactsPack
  + TruthGate
  + ComputeController
  + NoeticCore
  + ReflectionObserver
  + ConsolidationCycle
```

Коротко:

> Velantrim не “придумывает новый attention”.  
> Velantrim делает attention объяснимым: не для токенов, а для фактов,
> причин, памяти, доказательств и человеческой сути вопроса.
