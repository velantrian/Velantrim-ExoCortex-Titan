# 🌿 VELANTRIM EXOCORTEX — VISION V10 DRAFT
## Native Cognitive Architecture Specification v0.2

**Статус:** 🔭 Маяк — описание цели, не детальный roadmap  
**Версия кода при создании:** v8.5.1 (патч 13.1)  
**Дата:** 2026-05-19  
**Основа:** Синтез ChatGPT spec + критика Claude + аудит кода + Grok synthesis  
**Следующая ревизия:** после интеграции CausalGraph (TASK-08) и RawMemory (TASK-09)

---

## 📖 Как использовать этот документ

Это не план работ. Это **описание места назначения**.  
Маршрут — в `WORK_LOG.md`. Компас — в `docs/INVARIANTS.md`.

```
Этот файл отвечает на вопрос: КУДА идём?
WORK_LOG отвечает на вопрос: ЧТО делаем сейчас?
```

**Жизненный цикл документа:**

1. Сейчас — положить в `docs/VISION_V10_DRAFT.md`, читать как горизонт
2. В процессе фаз 1-3 — вести `WORK_LOG/VISION-01` (три категории ниже)
3. После интеграции CausalGraph + RawMemory — переписать в рабочее ТЗ v10

**Три категории для VISION-01 по ходу работы:**
- 🔥 Что из спецификации подтвердилось реальной болью кода
- 🔧 Где спецификация упрощает и нужен нюанс из текущей системы
- 💡 Новые идеи, которых не было в этом документе

---

## 🎯 Формула проекта

```
Сейчас:
  SQLite (строки)
  + BM25 (отдельный индекс)
  + SentenceTransformer (отдельный индекс)
  + NGramIndex (третий индекс)
  + CausalGraph (четвёртый индекс)
  + L0 RawMemory (пятая таблица)
  + ESM (надстройка над SQLite)
  = polyglot persistence со швами между каждым слоем
        ↓
V10:
  CognitiveFact (единый нативный объект)
  + CognitiveStore (одно хранилище)
  + CognitiveDistance (одна функция поиска)
  + EventBus (один поток изменений)
  = Unified Cognitive Runtime
        ↓
  Velantrim Exocortex 🌿🧠
```

**Что это значит на практике:**  
Сейчас изменение одного факта требует синхронизации 5 мест вручную
(вот откуда `mark_retriever_dirty`, двойная запись в `build_facts_pack`,
`get_all_facts()` без LIMIT — это всё симптомы одной болезни: швы).  
В V10 изменение факта это одно событие `FactUpdated`,
все производные индексы обновляются автоматически.

---

## 🧬 CognitiveFact — единица системы

Не `Text → DB row`. Не `Text → embedding`. Не `Text → graph node`.  
Всё это — **один объект**.

```python
@dataclass
class CognitiveFact:
    # ── Идентичность (иммутабельно) ─────────────────────────────
    id:               str        # неизменяем с момента создания
                                 # см. core/memory.py:IMMUTABLE_FACT_IDS

    # ── Содержание ───────────────────────────────────────────────
    raw_input:        str        # исходный текст (иммутабельно, I1)
                                 # сейчас: планируется в core/raw_memory.py
    canonical_text:   str        # очищенная форма
                                 # сейчас: core/memory.py:store_fact()["claim"]

    # ── Смысловое представление ──────────────────────────────────
    semantic_vector:  list[float]  # эмбеддинг
                                   # сейчас: core/hybrid_retriever.py:DenseRetriever
    semantic_tokens:  list[str]    # токены для BM25
                                   # сейчас: core/hybrid_retriever.py:BM25Retriever

    # ── Эпистемическое состояние (ESM) ───────────────────────────
    epistemic_state:  str        # см. раздел ESM ниже
                                 # сейчас: core/memory.py:ESM_STATES (8 состояний)

    # ── Временна́я модель (bi-temporal) ──────────────────────────
    t_event_valid_start:   str   # когда событие произошло в реальности
    t_event_valid_end:     str   # конец периода валидности (None = актуально)
    t_ingestion_start:     str   # когда система узнала о факте
    t_ingestion_end:       str   # когда система перестала верить факту
                                 # сейчас: core/memory.py:118-135 (4 поля)

    # ── Связи (нативно, не в отдельном графе) ────────────────────
    relations:        list[Relation]  # см. раздел Relations ниже
                                      # сейчас: core/causal_graph.py (отдельно)

    # ── Происхождение ────────────────────────────────────────────
    source:           str        # обязателен (I5)
    derived_from:     str | None # raw_id из L0 RawMemory
                                 # сейчас: планируется, TASK-09

    # ── История использования ────────────────────────────────────
    usage_count:      int        # сколько раз был использован
    last_used_at:     str        # когда последний раз
    retrieval_scores: list[float]  # история оценок релевантности

    # ── Уверенность ──────────────────────────────────────────────
    confidence:       float      # [0.0, 1.0]
                                 # сейчас: core/confidence.py (orphan, TASK-12)

    # ── Служебное ────────────────────────────────────────────────
    metadata:         dict       # расширяемое поле
    history:          list[dict] # audit trail всех изменений
```

**Почему это важно:**  
Сейчас `semantic_vector` живёт в `HybridRetriever` (в памяти процесса),
`relations` живут в `CausalGraph` (в SQLite таблице `relations`),
`raw_input` планируется в `RawMemory` (в третьей таблице),
`epistemic_state` в `facts` таблице.
Один факт = 4 места = 4 точки рассинхрона.
`CognitiveFact` убирает все 4 шва.

---

## ⚖️ ESM — Эпистемическая Модель Состояний

**Полная модель из текущего кода** (`core/memory.py:29-48`):

```
                    ┌─────────────────────────┐
                    │                         │
          Observed ─┼─→ Hypothesized          │
              │     │        │                │
              │     │        ▼                │
              │     │    Supported ──────────→│
              │     │        │                │
              └─────┼────────▼                │
                    │    Validated ──────────→ ImmutableCore
                    │        │                │  (Ring Zero,
                    │        ▼                │   навсегда)
                    │   Contradicted          │
                    │        │                │
                    │        ▼                │
                    │    Deprecated           │
                    │        │                │
                    └────────▼────────────────┘
                          Collapsed
                        (терминальное)
```

**Матрица переходов** (`core/memory.py:ESM_TRANSITIONS`):

| Из → В | Hypo | Supp | Valid | Contra | ImmCore | Colla | Depre |
|--------|------|------|-------|--------|---------|-------|-------|
| Observed | ✅ | ✅ | ✅ | — | — | ✅ | — |
| Hypothesized | — | ✅ | ✅ | — | — | ✅ | — |
| Supported | — | — | ✅ | — | — | ✅ | — |
| Validated | — | — | — | ✅ | ✅ | ✅ | — |
| Contradicted | — | — | — | — | — | ✅ | ✅ |
| Deprecated | — | — | — | — | — | ✅ | — |
| ImmutableCore | — | — | — | — | — | — | — |

**Почему 8 состояний, а не 4 (как у ChatGPT):**

`Hypothesized` ≠ `Supported` — гипотеза это "может быть так",
Support это "несколько источников подтверждают". Стоимость ошибки разная.

`Collapsed` ≠ `Deprecated` — Collapsed это "система решила забыть",
Deprecated это "факт устарел но история сохранена". Разная семантика.

`ImmutableCore` — специальное состояние для Ring Zero (`VALUES_CORE`, `RING_ZERO`).
Это единственное состояние без переходов. Нельзя изменить ничем.

---

## 🔗 Relation Engine

**Полный список типов** (`core/causal_graph.py:45-70`):

```
FORWARD типы (15):
┌────────────────────────────────────────────────────────────┐
│ causes       → причинно-следственная связь                 │
│ prevents     → предотвращение                              │
│ requires     → необходимое условие                         │
│ enables      → достаточное условие                         │
│ implies      → логическая импликация (НЕ то же что causes) │
│ contradicts  → противоречие (симметрично)                  │
│ generalizes  → обобщение                                   │
│ specializes  → конкретизация                               │
│ precedes     → предшествует                                │
│ follows      → следует за                                  │
│ composes     → является частью                             │
│ analogous_to → аналогия (симметрично)                      │
│ becomes      → трансформация (дерево → дрова)              │
│ affords      → прямая affordance-связь                     │
│ inhabited_by → использует / населяет                       │
└────────────────────────────────────────────────────────────┘

BACKWARD типы (автоматические инверсии):
caused_by | prevented_by | required_by | enabled_by | implied_by | composed_of

СИММЕТРИЧНЫЕ (нет инверсии):
contradicts, analogous_to
```

**Критически важное различие** (`implies` vs `causes`):

```
"Если идёт дождь, то дорога мокрая"  → implies  (логика)
"Дождь сделал дорогу мокрой"         → causes   (физика)

Дождь не всегда делает дорогу мокрой (крыша, навес).
Но "если дождь → дорога мокрая" может быть истиной в нашей модели.
Путать их = ошибки в причинно-следственном анализе.
```

**В V10:** `relations` живут внутри `CognitiveFact`, а не в отдельной таблице.
Это убирает JOIN при каждом `get_relations_from/to()`.

---

## 🔎 CognitiveDistance — функция поиска

**Текущий подход** (`core/hybrid_retriever.py`):

```python
# Три отдельных индекса, ручное RRF слияние:
final_score = RRF(bm25_rank, dense_rank, k=60)

# Не учитывает: epistemic_state, возраст факта,
# количество использований, причинные связи с запросом.
```

**V10 baseline (v0)** — линейная комбинация пяти осей:

```python
def cognitive_distance(fact: CognitiveFact, query: Query) -> float:
    """
    ⚠️ v0 BASELINE — наивное приближение.
    Оси коррелируют (temporal↔epistemic, semantic↔relation).
    Использовать как стартовую точку, калибровать через learning-to-rank.
    См. VISION-01 roadmap: v9.10 — калибровка весов.
    """
    Ws = 0.40  # semantic:   смысловое сходство (cosine similarity)
    Wt = 0.20  # temporal:   актуальность (decay по t_event_valid)
    We = 0.20  # epistemic:  вес состояния (Validated > Supported > Hypothesized)
    Wr = 0.10  # relational: связность с другими релевантными фактами
    Wu = 0.10  # usage:      история успешного использования

    return (
        Ws * semantic_similarity(fact.semantic_vector, query.vector)
        + Wt * temporal_relevance(fact.t_event_valid_start, fact.t_event_valid_end)
        + We * epistemic_weight(fact.epistemic_state)
        + Wr * relational_density(fact.relations, query.context_ids)
        + Wu * usage_weight(fact.usage_count, fact.last_used_at)
    )
```

**Веса эпистемических состояний** (для `We`):

```python
EPISTEMIC_WEIGHTS = {
    "ImmutableCore":  1.00,   # Ring Zero — абсолютный приоритет
    "Validated":      0.90,
    "Supported":      0.70,
    "Hypothesized":   0.40,
    "Observed":       0.30,
    "Contradicted":   0.05,   # почти не используем
    "Deprecated":     0.02,
    "Collapsed":      0.00,   # не показываем никогда
}
```

**Проблема v0 которую нужно решить в v9.10:**  
`temporal` и `epistemic` коррелируют — старый факт скорее всего
уже `Deprecated` и получает штраф дважды. Нужна ортогонализация.
Подход: PCA или disentangled representation после накопления
достаточного количества данных (>1000 запросов с оценками).

---

## 📡 Event Architecture

**Принцип:** все изменения в системе — события. Нет silent mutation.

```
Сейчас: mark_retriever_dirty() ← вызывается вручную,
         не всегда когда нужно, всегда когда не нужно.

V10:    FactCreated → [HybridRetriever обновляется автоматически]
                    → [NGramIndex обновляется автоматически]
                    → [SleepWorker получает сигнал для consolidation]
                    → [AuditChain записывает событие]
```

**Полный список событий:**

```python
# core/events.py (создать в v9.4)

@dataclass
class FactCreated:
    fact_id: str
    timestamp: str
    source: str

@dataclass
class FactUpdated:
    fact_id: str
    field: str          # что именно изменилось
    old_value: Any
    new_value: Any
    timestamp: str

@dataclass
class FactLinked:
    from_fact_id: str
    to_fact_id: str
    relation_type: str  # из FORWARD_RELATION_TYPES
    knowledge_status: str  # "hypothetical" | "known" | "inferred"

@dataclass
class FactDeprecated:
    fact_id: str
    reason: str
    timestamp: str

@dataclass
class FactConsolidated:
    source_ids: list[str]  # что объединилось
    result_id: str         # во что
    operation: str         # "merge" | "compress" | "summarize"

@dataclass
class FactContradicted:
    fact_id_a: str
    fact_id_b: str
    detected_by: str       # "autolinker" | "llm_extraction" | "manual"
```

**Что это убирает из текущего кода:**  
`mark_retriever_dirty()` — больше не нужен, `FactCreated` сам триггерит rebuild.  
`AuditChain` (сейчас orphan, 417 строк) — становится обработчиком событий.  
`CacheCoherence` (сейчас orphan, 225 строк) — становится обработчиком `FactUpdated`.

---

## 🌙 Consolidation Layer

**Sleep Worker превращается в event-driven консолидатор.**

```
Сейчас: SleepTimeWorker.think() → _reassess_goal() + _detect_gaps()
         (см. core/sleep_time_worker.py:380-510)

V10:    SleepTimeWorker подписывается на события:
         FactCreated  → триггерит merge-кандидатов
         FactLinked   → триггерит detect_conflict
         По расписанию: decay, compress, pattern_search
```

**Операции консолидации:**

```python
# 🧹 merge: объединить семантически близкие факты
# Когда: cosine_similarity > 0.92 AND same epistemic_state
# Результат: FactConsolidated событие, старые → Deprecated

# 📉 decay: снизить usage_weight устаревших фактов
# Когда: t_event_valid_end < (now - decay_threshold)
# Не удаляет, только снижает вес в CognitiveDistance

# 🔗 connect: предлагать новые рёбра графа
# Когда: два факта прошли через один запрос 3+ раз
# Создаёт FactLinked с knowledge_status="hypothetical"
# Требует human-in-the-loop approve (⚠️ важно — см. ниже)

# ⚠️ detect_conflict: автообнаружение противоречий
# Когда: два факта с contradicts_score > 0.85
# Создаёт FactContradicted, НЕ меняет epistemic_state автоматически
# Требует подтверждения (автоматические Contradicted — это риск)

# 🧠 compress: когнитивное сжатие группы похожих фактов
# Когда: >5 фактов на одну тему в Supported/Validated
# Создаёт один новый факт с derived_from=[список id]
```

---

## 💡 Insight Layer — предупреждение

Insight Layer выявляет скрытые закономерности и гипотезы.  
Это самый сложный компонент и самый опасный при неправильной реализации.

```
⚠️ ТРЕБОВАНИЕ: каждый инсайт создаётся с epistemic_state="Hypothesized"
   и НИКОГДА не повышается автоматически.

⚠️ ТРЕБОВАНИЕ: каждый инсайт имеет audit trail:
   - какие факты использованы (derived_from)
   - какой паттерн сработал
   - какой алгоритм его нашёл

⚠️ ТРЕБОВАНИЕ: human-in-the-loop обязателен перед переходом
   Hypothesized → Supported для любого инсайта.

Без этих трёх требований Insight Layer превращается в
генератор уверенных галлюцинаций. Это не философия —
это инженерный контракт.
```

```
Facts → Graph → Pattern Search → Insight (Hypothesized)
                                      ↓
                              Human Review
                                      ↓
                            Supported / Collapsed
```

---

## 🔒 Инварианты (Negative Space Design)

Расширить до 15-20, взяв основу из `docs/INVARIANTS.md`.  
Базовые (из аудита + спецификации):

```
I1.  raw_input никогда не изменяется после создания
I2.  id факта неизменяем
I3.  Факт не удаляется физически (только Collapsed/Deprecated)
I4.  Состояние ESM изменяется только через явный переход по матрице
I5.  source обязателен (не пустой, не whitespace-only)
I6.  Любое изменение порождает событие (нет silent mutation)
I7.  Запрещены циклические causal-конфликты в CausalGraph
I8.  Новые факты создаются только в состоянии Observed
I9.  ImmutableCore → нет переходов (Ring Zero абсолютен)
I10. Инсайты создаются только в Hypothesized
I11. Автоматические Contradicted требуют подтверждения
I12. Отчёты строятся только из основного store (нет кэшей-копий)
...  (дополнить из docs/INVARIANTS.md при написании V10 ТЗ)
```

---

## 🗺️ Инкрементальный Roadmap

**Принцип:** каждый шаг — это рабочий коммит.  
Нельзя сломать систему на полпути. После каждого шага Velantrim работает лучше.

### Фаза v8.x (сейчас — текущий WORK_LOG)
```
TASK-01 ✅ available property fix
TASK-02 ✅ coverage config fix
TASK-03 ✅ datetime.utcnow fix
TASK-04    mark_retriever_dirty → conditional
TASK-05    store_fact double-write
TASK-06    get_all_facts without LIMIT
TASK-07    DATABASE_DEV_ONLY fallback removal
TASK-08    CausalGraph → pipeline.run()
TASK-09    RawMemory → store_fact + ingest
TASK-10    find_contradictions cycle protection
TASK-11    BFS deque optimization
TASK-12    FactsPackBuilder unification
```

### Фаза v9.x (начало после v8.x завершён)
```
v9.1   CognitiveFact dataclass — один объект вместо dict
       (SQLite row + vector + ESM в одном Python объекте)
       Файл: core/cognitive_fact.py
       Тест: факт создаётся, сериализуется, десериализуется без потерь

v9.2   CognitiveFactStore — унификация записи
       Все write-операции через один метод
       Убирает: store_fact() дублирование из pipeline
       Файл: core/cognitive_store.py

v9.3   CognitiveFactStore — унификация чтения
       Все read-операции возвращают CognitiveFact, не dict
       Убирает: get_fact() + get_all_facts() расхождение форматов

v9.4   EventBus — базовая событийная архитектура
       FactCreated / FactUpdated / FactLinked как dataclasses
       Убирает: mark_retriever_dirty (автоматически по FactCreated)
       Файл: core/events.py, core/event_bus.py

v9.5   CognitiveDistance v0 — baseline формула
       Заменяет RRF(bm25, dense) на взвешенную комбинацию
       Параметры: Ws=0.4, Wt=0.2, We=0.2, Wr=0.1, Wu=0.1
       Файл: core/cognitive_distance.py

v9.6   Consolidation как event handlers
       SleepTimeWorker подписывается на FactCreated, FactLinked
       Добавляет: merge_candidates(), detect_conflicts()
       Убирает: orphan AuditChain интегрируется как handler

v9.7   Relations нативно в CognitiveFact
       relation_state как поле объекта, не отдельная таблица
       Убирает: JOIN при get_relations_from/to()
       Тест: causal_chain() работает без отдельного SQL запроса

v9.8   ESM transitions через EventBus
       ESM-переход = событие FactUpdated(field="epistemic_state")
       История переходов автоматически в audit trail

v9.9   Contract tests на стыки (TASK-18)
       server→pipeline, pipeline→store, store→events, events→worker
       Порог: >95% pass

v9.10  CognitiveDistance калибровка
       Собрать 1000+ запросов с оценками релевантности
       Learning-to-rank для подбора весов Ws..Wu
       Убрать корреляцию temporal↔epistemic через ортогонализацию
```

### Фаза v10.x (после реального опыта v9.x)
```
Написать финальную спецификацию на основе VISION-01 наблюдений.
Конкретные шаги v10.1+ — определить после v9.10.

Ожидаемые направления (уточнить по болям из v9):
- Native CognitiveFact storage (не поверх SQLite, а вместо)
- Insight Layer с audit trail
- Полная ортогонализация CognitiveDistance
- Semantic compression для долгосрочной памяти
```

---

## 📊 KPI — контракт качества

| Метрика | Сейчас | v9.5 цель | v10 цель |
|---------|--------|-----------|----------|
| ⚡ Latency p95 | ~1-2s | <200ms | <100ms |
| 🔎 Relevance | не измерено | >0.85 | >0.90 |
| 📉 Дубли в памяти | не измерено | <10% | <5% |
| ⚠️ Авто-конфликты | нет | detect (не resolve) | detect + suggest |
| 🧪 Тесты на стыках | ~10% | >70% | >95% |
| 🌙 Consolidation | ручная | событийная | nightly + realtime |
| 📝 Orphan код | 43% | <15% | <5% |

---

## 🧠 Архитектура V10 (ASCII)

```
👤 Input
      │
      ▼
🛡️ Perception + Input TruthGate
      │
      ▼
🧬 CognitiveFact (единый атом знания)
      │
  ┌───┴──────────────────────────┐
  ▼                              ▼
🔎 CognitiveDistance         🔗 Relations (нативно)
  (semantic + temporal         (15 типов, в объекте)
   + epistemic + relational
   + usage)
  │                              │
  └──────────────┬───────────────┘
                 ▼
         ⚖️ TruthGate (Validated?)
                 │
                 ▼
         📡 EventBus
         (FactCreated / FactLinked / FactUpdated)
                 │
    ┌────────────┼────────────────┐
    ▼            ▼                ▼
🌙 Consolidation  📊 Reports   🔍 Index update
  (merge, decay,  (из одного    (автоматически
   connect,       store)         по событию)
   detect_conflict)
    │
    ▼
💡 Insight Engine
  (Hypothesized → human review → Supported)
    │
    ▼
✨ Adaptive Exocortex 🌿🧠
```

---

## 💎 Одна строка

```
Сейчас: данные в пяти местах, синхронизация вручную, поиск по трём индексам.
V10:    один объект, одно событие, одно расстояние.
```

---

*Создан: 2026-05-19 | Следующая ревизия: после TASK-08 + TASK-09*  
*Источники: ChatGPT spec + Claude audit + Grok synthesis + реальный код v8.5.1*
