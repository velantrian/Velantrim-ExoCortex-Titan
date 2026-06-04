# 🌌 Fractal Memory Canon — Qwen/MemTree Update

**Дата:** 26.05.2026  
**Статус:** 🟡 архитектурный каркас в V8.6, runtime-подключение отдельно  
**Код:** `core/fractal_memory.py`

---

## 🧠 Что полезно из Qwen

Исследование полезно не как замена Velantrim, а как уточнение Retrieval/MemFabric:

| Идея | Решение для Velantrim |
|------|------------------------|
| Fractal / hierarchical memory | ✅ принять как форму организации L0–L3 |
| MemTree | ✅ использовать как инженерный образ дерева памяти |
| Stingy Context | ✅ применять для иерархического сжатия длинных корпусов |
| Recursive Retrieval | ✅ оформить как будущий режим навигации |
| ESM protein models | 🟡 не ядро; пример domain-specific encoders |
| Standard RAG | ⚠️ оставить как инструмент, не как всю память |

Главное: Velantrim не должен превращаться в плоский RAG. Retrieval должен стать
навигацией по уровням смысла: domain -> concept -> relation -> mechanism ->
evidence -> principle.

---

## 🧩 Каноническая формула L0–L3

```text
L0 Raw Data
  -> L1 Working / Session Memory
  -> L2 Episodic Summary
  -> Pending Layer
  -> Truth Gate + Guardian
  -> L3 Canonical Graph Memory
```

Формула:

> Fractal Memory = L0 raw traces -> L1 working context -> L2 episodic summaries -> Pending -> Truth Gate -> L3 canonical graph concepts.

Важно: L2 не продвигается в L3 автоматически. Между ними обязателен Pending
Layer, provenance, Guardian и TruthGate.

---

## 🔎 Hierarchical Memory Router

Будущий режим поиска:

```text
Query
  -> Intent Detection
  -> Domain Selection
  -> Level Selection
  -> Recursive Retrieval
  -> Detail Expansion
  -> Evidence Check
  -> TRACE
```

Это не замена `HybridRetriever`, `cross_domain`, `causal_graph` и `TRACE`.
Router должен использовать их как backend и возвращать поверх них `memory_route`.

---

## 🧾 Контракты данных

В V8.6 добавлен безопасный каркас:

| Контракт | Роль |
|----------|------|
| `MemoryRecord` | минимальная запись для движения L0/L1/L2/Pending/L3 |
| `FractalMemoryNode` | MemTree-подобный узел: domain/concept/evidence/etc. |
| `TraceRecord` | высокий TRACE для recursive retrieval route |
| `RetrievalPath` | анализируемый маршрут: start node, traversed nodes, decisions, depth, time |
| `RecursiveRetrievalRequest` | будущий запрос `retrieval_mode="recursive"` |
| `CompressionRule` | контракт сжатия между слоями |
| `GuardianPolicy` | контракт многоуровневого Guardian |

Ограничение L3:

```text
L3 entry allowed only if:
  layer in {L2_EPISODIC, PENDING, L3_CANONICAL}
  truth_status in {VERIFIED, CANON}
  Guardian approved
  provenance exists
  confidence >= 0.5
```

---

## 🧭 RetrievalPath

Обычный TRACE отвечает на вопрос: **какие факты попали в ответ**.
`RetrievalPath` отвечает на другой вопрос: **как система шла по дереву памяти**.

```text
RetrievalPath:
  start_node: root
  traversed_nodes: [root, domain_biology, concept_tree, fact_tree_001]
  decisions:
    - DOMAIN_MATCH, confidence=0.91
    - HIERARCHICAL_DESCENT, confidence=0.68
    - EVIDENCE_FOUND, confidence=0.86
  end_node: fact_tree_001
  total_depth: 3
  time_ms: 12.5
```

Зачем это нужно:

| Что видно | Зачем |
|----------|-------|
| какие узлы посещены | аудит маршрута поиска |
| где confidence просела | понять, почему router спустился глубже |
| где найдено evidence | связать ответ с источником |
| какие узлы не достигаются | искать "мертвые зоны" дерева памяти |

`RetrievalPath` не заменяет `TraceRecord`; он расширяет его.

---

## 🗜️ Compression Strategy

Сжатие не должно быть одним общим "summary". Для каждого перехода свой смысл:

| Переход | Что делать | Контроль риска |
|---------|------------|----------------|
| L0 -> L1 | фильтрация шума, дедупликация, токенизация | raw immutable, source refs |
| L1 -> L2 | summary эпизода, entities, relations | derivation chain, UNVERIFIED |
| L2 -> Pending | обобщение, candidate principle, conflict scan | TruthGate required, Guardian required |
| Pending -> L3 | verification, graph integration, trace persist | provenance required, contestable status |

Принцип: чем выше слой, тем меньше текста и больше смысла; но каждый шаг обязан
оставлять путь назад к L0.

---

## 🛡️ Multi-Level Guardian

Guardian не один монолит, а три зоны контроля:

| Уровень | Где работает | Что проверяет |
|---------|--------------|---------------|
| L1 Guardian | retrieval | source reliability, dangerous content, stale context |
| L2 Guardian | generation | trace coverage, faithfulness, contradiction disclosure |
| L3 Guardian | action / canon promotion | TruthGate, provenance, policy boundary |

Для L3 правило самое строгое: если `L3_ACTION` Guardian не пройден, запись не
может стать canonical graph memory.

---

## 🛡️ Что не переносить буквально

| Тема | Почему |
|------|--------|
| ESM как “мозг” Velantrim | ESM тут про белковые модели, не general memory |
| Автоматический L2 -> L3 | ломает Truth Gate и Guardian |
| Полная замена pipeline | текущий pipeline уже содержит Retrieval -> TRACE -> Guardian -> TruthGate |
| Fractal Memory как отдельный silo | это форма организации существующих L0–L3 |

---

## 🧭 Следующий безопасный шаг

1. Подключить optional `retrieval_mode="recursive"` без изменения default-пути.
2. В ответ `/query` добавить `memory_route` рядом с обычным `trace`.
3. Заполнять `RetrievalPath` для анализа маршрутов и "мертвых зон".
4. На первом этапе использовать существующие `HybridRetriever`, `CrossDomainLayer`,
   `CausalGraph` и `TruthGate`.
5. После этого добавить hierarchical compression для больших документов.

Итоговая формула:

> Velantrim Exo-Cortex = Graph Truth Store + Fractal Memory L0–L3 + Recursive Retrieval Router + Essence Layer + Multi-Level Guardian + TRACE with RetrievalPath + Domain-Specific Models.
