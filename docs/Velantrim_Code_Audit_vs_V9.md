# 🔱 Глубокий аудит: Код vs Velantrim V9 Specification

> **Дата оригинала:** Март-Апрель 2026 · **Аудитор:** Claude Sonnet 4.6
> **Status Update:** Май 2026 (v8.3.1) — добавлена секция закрытий после повторного аудита
> **Файлы:** memory.py · pipeline.py · trace.py · storage.py · test_esm.py · SPRINT_A_V2_ADDITIONAL_PATCHES.md
> **Сравнивается с:** V9.2-audit Specification (§2, §3, §5, §10.3)

---

## 🔄 STATUS UPDATE — Май 2026 (v9.2-audit)

> Этот раздел добавлен после завершения Sprint 1++.
> Оригинальный аудит ниже сохранён без изменений — он ценен как исторический снапшот.
> Здесь фиксируется что из найденного **уже закрыто**, а что **остаётся открытым**.

### ✅ Закрыто в Sprint 1++

| Находка из аудита | Где было | Что сделано | Файл |
|-------------------|----------|-------------|------|
| 🔴 Нет bi-temporal полей (I96) | memory.py v8.1.1 | Добавлены 4 поля `t_*`, `get_fact_at()`, `invalidate_edge()`, auto-migration | `memory.py` v8.2.0 |
| 🔴 Тестовая изоляция не работает | test_esm.py | `make_store()` фабрика, `monkeypatch._GLOBAL_STORE` целиком | все `test_*.py` v2.0 |
| 🔴 GraphStore ABC без bi-temporal методов | storage.py | `get_fact_at()`, `invalidate_edge()`, `search()` добавлены в ABC | `storage.py` v8.1.0 |
| ⚠️ trace.py без параметра `by` | trace.py | `promote_trace(by=...)` + `promoted_by` в каждом элементе | `trace.py` v8.0.4 |
| ⚠️ confidence vs retrieval_score путаница | trace.py | Разделены: `retrieval_score` (BM25) и `source_confidence` (стабильный) | `trace.py` v8.0.4 |
| 🔴 O(N) retrieval (LIMITATIONS P-1) | pipeline.py | `NGramIndex` FTS5 trigram L0 Pre-Filter, O(log N), graceful degradation | `ngram_index.py` v1.0.0 |
| ➕ TRUSTED_SOURCES отсутствуют | — | `TRUSTED_SOURCES` whitelist (I98): ring_zero/domain_seed/system_axiom | `memory.py` v8.3.0 |
| ➕ EmbeddingRegistry отсутствует | — | 17 моделей, `validate()` против numpy.dot dim-mismatch | `embedding_registry.py` v1.0.0 |
| ➕ SleepTimeWorker + CoreMemoryBlocks | — | L1.75: активный `think()`, `suggest_next_step()`, RNE концепция | `sleep_time_worker.py` v1.0.0 |
| 💡 L0 LRU статус занижен в V9 | V9 §3.2 | Обновлён с `⚠️ Hypothesis` на `🟦 Documented` в V9.2 | `Velantrim_V9_Final_Audited.md` |
| 💡 TruthGate нужно разделить | V9 §3.3 | В V9.2 реестре разделены TruthGate.ESM (✅) и TruthGate.Semantic (⚠️) | `Velantrim_V9_Final_Audited.md` |

**Итого закрыто в Sprint 1++: 11 находок. Тест-база выросла с 55 → 130+ тестов.**

### ✅ Дополнительно закрыто в v8.3.1 (Май 2026, аудит-фикс)

После Sprint 1++ был проведён повторный аудит, который обнаружил три реальных бага в существующем коде, а также добавил три новых модуля, закрывающих пункты из секции "Остаётся открытым". Прогон тестов на финальном состоянии: **191 passed / 0 failed, coverage 86%** (было 125 passed / 14 failed на момент аудита).

| Находка | Где было | Что сделано | Файл |
|---------|----------|-------------|------|
| 🔴 **BUG-1: Split-brain L0/L1 при drift protection** | `memory.py:245` | Когда drift protection (TASK-02) переводила Validated→Contradicted, L0 кэш получал новое состояние, но SQL `ON CONFLICT DO UPDATE` намеренно исключал `epistemic_state` — L1 оставался Validated. Расхождение слоёв. Фикс: добавлен флаг `_drift_detected` и дополнительный `UPDATE` для синхронизации L1. Это **единственное** легитимное исключение из правила "epistemic_state только через transition_esm". | `memory.py` v8.3.1 |
| 🟡 **BUG-2: Mock LLM возвращал пустую строку для suggest_next_step** | `sleep_time_worker.py:639` | Проверка "цель/goal" в `_llm_complete()` стояла перед "следующий шаг/next_step". Но prompt `suggest_next_step()` содержит оба слова, и более общий паттерн "цель" срабатывал первым, возвращая пустой `current_goal`. Фикс: переставлены проверки — более специфичная "следующий шаг" теперь проверяется первой. | `sleep_time_worker.py` v8.3.1 |
| 🟢 **BUG-3: TruthGate сообщение с неправильным регистром** | `pipeline.py:319` | Тест `test_truth_gate_blocks_low_confidence` проверял `assert "Confidence" in reason`, но reason возвращался как "Нулевая или отрицательная confidence". Фикс: перефразировано на "Confidence нулевая или отрицательная". | `pipeline.py` v8.3.1 |
| 🆕 **TruthGate — реальный gate вместо placeholder** | Был MVP `confidence ≥ 0.5` | Создан `core/truth_gate.py`: проверки source + confidence (mode-aware) + evidence_count + active contradictions в L1. Cognitive Modes (PRECISION/BALANCED/EXPLORATION/CREATIVE) из V9 §12.1. Работает поверх `GraphStore ABC`, не требует Neo4j. Возвращает `TruthGateVerdict` с полным audit trail. 23 теста, 78% coverage. | `truth_gate.py` v1.0.0 |
| 🆕 **HybridRetriever — BM25 + Dense + RRF** | Был только BM25-only | Создан `core/hybrid_retriever.py`: `BM25Retriever` с fallback на naive TF-IDF, `DenseRetriever` через sentence-transformers с graceful degradation, `reciprocal_rank_fusion()` по Cormack et al. (k=60), опциональный `CrossEncoderReranker`. Работает прямо сейчас даже без установки дополнительных зависимостей. 22 теста, 72% coverage. | `hybrid_retriever.py` v1.0.0 |
| 🆕 **MHICalculator — Memory Health Index** | Был stub в Horizons /experimental E2 | Создан `core/mhi.py`: формула `0.30×validated + 0.25×freshness + 0.25×precision + 0.20×graph`. Пороги HEALTHY/DEGRADED/SAFE_MODE из V9 §8 SLO Contract. Автоматические рекомендации для Meta-Supervisor. 14 тестов, 90% coverage. Это перевод RFC0070 из stub в работающий компонент. | `mhi.py` v1.0.0 |
| 🧪 **Обновлён P0.1 тест + добавлен regression-тест для BUG-1** | `test_esm.py` | Старый тест `test_store_fact_preserves_validated_after_upsert` написан до TASK-02 (drift protection) и проходил случайно благодаря split-brain. Теперь он проверяет настоящий P0.1 (UPSERT с тем же claim не откатывает ESM). Добавлен `test_store_fact_drift_protection_keeps_l0_l1_in_sync` — regression для BUG-1. | `test_esm.py` v8.3.1 |

**Итого после v8.3.1: 14 находок закрыто. Тест-база выросла с 130+ → 191 тестов. Coverage 81% → 86%.**

### 🔴 Остаётся открытым (Sprint 2+)

После v8.3.1 список открытых пунктов сократился до семи. Они требуют либо реального LLM, либо Neo4j, либо async-инфраструктуры — то есть полноценного Sprint 2.

| Находка | Статус | Sprint |
|---------|--------|--------|
| EventBus — deque вместо Redis Streams | Остаётся deque MVP. Важно: при подключении использовать `redis.asyncio` из `redis>=4.2.0`, **не `aioredis`** (deprecated, не работает на Python 3.11+) | S2c |
| Canonical Memory Protocol — только 15% | F1-F6.5 и S1-S7 не реализованы | S2-S3 |
| pipeline.py — mock DATABASE из 5 фактов | Нужно подключить реальный L3 через `HybridRetriever.retrieve()` поверх `GraphStore.get_all_facts()` | S2b |
| LLM Generation — string join вместо LLM | F6 не реализован. Архитектура готова — нужен `LLMClientABC` | S2b |
| L1.5 Velum — в коде нет | Только в спецификации | S2 |
| L4 ReasoningBank — в коде нет | Только в спецификации | S2 |
| Slow Path (S1-S7) — полностью отсутствует | Не реализован | S2c |
| ~~TruthGate — MVP confidence floor 0.5~~ | ✅ Закрыто в v8.3.1 через `core/truth_gate.py`. Остаётся cross-graph validation через Neo4j | ✅ Done (Sprint 2 — extension) |
| BlackboardBus (I97) — нет реализации | GraphStore ABC есть, Bus — нет | S2c |
| SleepTimeWorker LLM — mock заглушка | `llm_fn=None` → mock. Архитектура готова — `make_sleep_time_worker(llm_fn=AnthropicClient)` | S2c |

---

---

## 🗺️ Общая картина — что код реально говорит о системе

Прежде чем идти по файлам — главный вывод, который виден только если смотреть на всё вместе.

Код реализует **другой, более ранний вариант пайплайна**, чем тот, что описан в V9. Это не плохо — это честная картина MVP-стадии. Но разрыв между «что обещает спецификация» и «что запустится прямо сейчас» значительно больше, чем можно подумать, читая только V9.

Конкретно: `pipeline.py` реализует цепочку `BM25 search → FactsPack → Guardian → TruthGate → ESM → join-ответ`. Canonical Memory Protocol V9 §10.3 описывает цепочку `F1 Validation Loop → F1.5 Velum Hint → F2 L0 Goal Stack → F3 FTS5 → F4 Neo4j → F5 Context Builder → F6 LLM → F6.5 OutputFaithfulness`. Это принципиально разные системы: код — это MVP-скаффолд, а спецификация описывает production-архитектуру. Осознать этот разрыв критично перед Sprint 1.

---

## 🧠 1. memory.py (v8.1.1) — Самый зрелый файл

### ✅ Что точно совпадает с V9

`memory.py` — лучший из всех файлов по соответствию спецификации. ESM-матрица из 8 состояний (Observed, Hypothesized, Supported, Validated, Contradicted, Deprecated, Collapsed, ImmutableCore) полностью соответствует V9 §5, таблице инвариантов. Матрица переходов `ESM_TRANSITIONS` корректна: терминальные Collapsed и ImmutableCore — пустые множества, Validated может идти в Contradicted (критично для конфликтов), Deprecated только в Collapsed (без возврата). Это доказывает I1 и частично I6.

Инвариант I50 реализован правильно и строго: `store_fact()` создаёт новые факты только в состоянии Observed, единственное исключение — Ring Zero seed (VALUES_CORE, RING_ZERO) который может стартовать в Validated. Попытка создать факт в любом другом состоянии — `ValueError`. Это точная реализация того, что написано в §5.

L0 LRU-кэш на 128 слотов через `OrderedDict` реализован корректно: `_l0_put` делает move_to_end при попадании, `_l0_get` делает move_to_end при чтении, eviction через `popitem(last=False)` вытесняет наименее недавно используемый элемент. `get_fact()` возвращает `copy.deepcopy()` — защита от mutable aliasing, что подтверждает тест `test_get_fact_returns_deepcopy_not_reference`. Это прямая реализация инварианта «L0 не корруптируется внешней мутацией».

Атомарность обновления ESM-состояния (TASK-04) решена элегантно: `transition_esm()` содержит бизнес-логику (валидация матрицы, Ring Zero guard), `update_state()` содержит только IO-логику (SQL + L0 sync). Разделение чистое. Для SQLite >= 3.38.0 используется `json_insert(history, '$[#]', json(?))` — атомарное добавление к JSON-массиву без read-modify-write цикла. Для старых версий — корректный fallback.

Защита от Semantic Drift (TASK-02) реализована в `store_fact()`: если claim изменился у Validated факта — автоматический переход в Contradicted с записью в history. Это нетривиальная и правильная логика.

### 🔴 Критическое несоответствие: нет bi-temporal полей

V9 §2.1 — основной архитектурный контракт Sprint 1 — требует, чтобы каждое ребро L3 имело 4 timestamp поля: `t_event_valid_start`, `t_event_valid_end`, `t_ingestion_start`, `t_ingestion_end`. Инвариант I96: «Каждое ребро L3 имеет 4 поля времени».

Реальная схема SQLite в `memory.py`:
```sql
CREATE TABLE IF NOT EXISTS facts (
    fact_id TEXT PRIMARY KEY,
    claim TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    epistemic_state TEXT DEFAULT 'Observed',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    history TEXT DEFAULT '[]'
)
```

Здесь только `created_at` и `updated_at` — это не bi-temporal. Bi-temporal требует разделения между «когда факт стал истинным в мире» и «когда система узнала о нём». Без этого невозможен time-travel запрос «что я знал на момент T». Это первый контракт Sprint 1, и он не реализован в коде.

💡 **Предложение:** миграция `velantrim_migrate_v3_1.py` уже существует в наборе файлов и, скорее всего, предназначена именно для этого. Нужно убедиться что она добавляет все 4 bi-temporal поля к `facts` таблице и что `update_state()` корректно заполняет `t_ingestion_end` при инвалидации (не DELETE — только SET).

### 🔴 Критическое несоответствие: SQLite вместо Neo4j

V9 §3.2 заявляет «L3 Knowledge Graph (Neo4j) 🟢 Production». В коде L3 — это `SQLiteGraphStore`, а Neo4j — TODO в `storage.py` (`# TODO Sprint 2c: добавить Neo4jGraphStore`). Это не баг в коде — это правильный MVP-подход. Но это означает, что verification_layer для L3 Knowledge Graph должен быть `⚠️ Hypothesis` или `🟦 Documented`, но не `🟢 Production`. Спецификация завышает статус.

Принципиальное следствие: все bi-temporal Cypher-запросы из V9 §2.1 невозможно выполнить на SQLite в их нативном виде. Neo4j имеет встроенную поддержку datetime типов; SQLite хранит их как TEXT и требует приложной логики для сравнения.

### ⚠️ Проблема: нет BlackboardBus

V9 §2.2 и инвариант I97 требуют: «Прямой Cypher CREATE/SET на L3 запрещён вне репозиториев BlackboardBus». В `memory.py` функции `store_fact()`, `get_fact()`, `transition_esm()` — это прямые функции уровня модуля, без BlackboardBus. Это не нарушение I97 в буквальном смысле (Cypher только для Neo4j), но архитектурно это ровно то, что BlackboardBus призван инкапсулировать: единая точка записи.

💡 **Предложение:** `GraphStore ABC` в `storage.py` — уже правильный шаг в направлении BlackboardBus. При переходе на Neo4j этот ABC нужно расширить до полноценного BlackboardModule с методами `read_signals()` и `write_observation()` из V9 §2.2.

### ⚠️ Проблема: глобальный синглтон `_GLOBAL_STORE`

```python
_GLOBAL_STORE = SQLiteGraphStore(SQLITE_PATH)
_L0 = _GLOBAL_STORE._l0
_DDL_INITIALIZED = _GLOBAL_STORE._ddl_initialized_paths
```

Это «мост обратной совместимости» с TODO «удалить в Sprint 2c». Проблема в том, что этот глобальный синглтон инициализируется при импорте модуля с захардкоженным путём. При переходе на Dependency Injection весь код, использующий модульные функции `store_fact()`, `get_fact()`, `transition_esm()`, нужно переписать на вызовы через инстанс `SQLiteGraphStore`. Это технический долг, который растёт с каждым тестом и компонентом, использующим глобальные функции.

### ⚠️ Нет Evidence узлов

Инвариант MGL (из V8 §Formal Invariants, унаследованный в V9): «∀ fact ∈ Graph: ∃ evidence (:Evidence node)». В схеме SQLite нет таблицы Evidence и нет поля `evidence_id` в `facts`. Confidence и source есть, но формальный граф провенанса через Evidence узлы отсутствует.

---

## 🔄 2. pipeline.py (v8.0.3-p0) — Самое большое расхождение с V9

### Карта расхождений: Canonical Memory Protocol vs реальный код

V9 §10.3 описывает Fast Path как 7 шагов. Вот как они соотносятся с `pipeline.run()`:

| Шаг протокола | Описание | Статус в pipeline.py |
|---------------|----------|---------------------|
| F1 Validation Loop L4 | DECISION / VALIDATION / SELF-CHECK | 🔴 Отсутствует |
| F1.5 Velum Context Hint | Velum.get_neighbors() → seed для Etir | 🔴 Отсутствует |
| F2 L0 update | Goal Stack + Ring Zero + Project State Card | 🔴 Отсутствует |
| F3 L1 FTS5 search | SQLite FTS5, recency bias, 1-2 кандидата | 🔴 Отсутствует |
| F4 Graphiti → Neo4j | Hybrid semantic + keyword + graph traversal | 🔴 Заменён mock DATABASE |
| F5 Context Builder | 4±1 чанка, token_budget=2000, typed tags | 🔴 Отсутствует |
| F6 LLM Generation | Единственный вызов LLM на Fast Path | 🔴 Заменён string join |
| F6.5 OutputFaithfulnessChecker | keyword overlap ≥40% | 🔴 Отсутствует |

И весь **Slow Path (S1-S7) отсутствует полностью**: нет EventBus публикации, нет L1 Buffer Processing, нет ConflictResolutionWorker, нет L2 Consolidation, нет TruthGate Slow Path, нет ReasoningBank update, нет ResponseAuditWorker (I28).

Это не критика кода — это кристально честный MVP. Но это означает, что текущий `pipeline.py` реализует примерно 15% от того пайплайна, который описывает V9 §10.3. Оставшиеся 85% — это Sprint 2 и далее.

### ✅ Что работает правильно в pipeline.py

BM25 Okapi реализован полноценно: Robertson IDF (`log((N-df+0.5)/(df+0.5)+1)`), TF с насыщением через k1=1.5, нормализация длины документа через b=0.75, параметры Elasticsearch/Lucene. Это лучше BM25-lite и соответствует spirit V9, хотя и применяется к mock-данным.

Guardian правильно разделён с TruthGate: Guardian — структурная проверка (fact_id, claim, source, trace coverage), TruthGate — семантическая (confidence floor). Это точная реализация принципа разделения ответственностей, описанного в TASK-06.

Идемпотентность pipeline.run() — исправленный баг v8.0.2: если факт уже Validated, transition_esm пропускается (Validated→Validated нет в матрице и бросил бы ValueError). Это корректно.

### 🔴 Критическая проблема: TruthGate — placeholder, а не Truth Gate

Комментарий в коде честен: «MVP использует confidence-floor 0.5. Это placeholder, не полноценный TruthGate (нет evidence_count, нет cross-validation). Полная реализация — Sprint 2 (RFC0001 evidence chain)».

V9 §3.3 заявляет Truth Gate + ESM как `🟢 Production, ✅ Verified (Patch P2-4 atomic_split)`. Но `atomic_split` — это атомарность ESM-перехода, а не полный Truth Gate. Сам Truth Gate в коде — это `min_confidence=0.5` проверка и проверка наличия source. Это не то, что описывает V9 §10.4 Token Contract («evidence_count ≥ 3, truth_gate_coverage ≥ 0.7»).

💡 **Предложение:** verification_layer для Truth Gate должен быть разделён на два компонента: `transition_esm() ✅ Verified` (это Patch P2-4) и `truth_gate() ⚠️ Hypothesis / MVP placeholder`. Сейчас они слиты в одну строку реестра.

### ⚠️ Confidence semantics: конфликт между pipeline.py и trace.py

В `pipeline.py retrieve()` комментарий P1.3 говорит: «confidence берётся из источника (стабильная), retrieval_score — BM25-балл, query-dependent, не персистируется в L1».

В `trace.py build_trace()` поле `confidence` в trace-элементе берётся из `item.get("retrieval_score", 0.5)` — то есть BM25-балл, query-зависимый. Получается: `FactsPack.fact.confidence = source confidence (stable)`, но `Trace.element.confidence = retrieval_score (BM25, volatile)`. Два разных числа называются одним словом в двух местах структуры, описывающей один и тот же факт. Это семантическая неконсистентность, которая создаст путаницу при анализе audit trail.

### ⚠️ DATABASE — глобальный список в модуле

```python
DATABASE = [
    {"id": "f1", "text": "Water boils at 100°C..."},
    ...
]
_BM25_INDEX = BM25(_DB_TOKENS)  # строится один раз при загрузке модуля
```

BM25 индекс строится при импорте модуля на статических данных. Когда DATABASE будет заменена на GraphStore.search() в Sprint 2c, весь механизм пересборки индекса нужно переделывать. Кроме того, глобальный `_BM25_INDEX` не потокобезопасен для обновления.

---

## 🧬 3. trace.py (v8.0.3-p0) — Хорошая основа, два точечных бага

### ✅ Что работает правильно

Двухпроходная атомарность `promote_trace()` — элегантное решение: Pass 1 полностью валидирует все переходы без мутации, Pass 2 мутирует только если Pass 1 прошёл без исключений. Это гарантирует что trace либо полностью обновлён, либо полностью остаётся в предыдущем состоянии. Идемпотентность (skip если уже в целевом состоянии) реализована.

### ⚠️ Проблема: нет параметра `by` в promote_trace

`transition_esm()` имеет параметр `by: str` который записывается в history и позволяет понять кто инициировал ESM-переход. `promote_trace()` такого параметра не имеет — переход не атрибутирован. С точки зрения audit trail (Audit Layer §11.3) это пробел: `GET /memory/audit/strategy` должен показывать «какая стратегия выбрана», но trace-элементы не несут информацию о том, кто их промотировал.

💡 **Предложение:** добавить `by: str = "pipeline.promote_trace"` параметр в `promote_trace()` и записывать его в поле `promoted_by` при мутации в Pass 2. Это строка кода.

### ⚠️ Проблема: нет bi-temporal полей в trace

Когда bi-temporal миграция (V9 §2.1) будет применена к L3, trace-элементы тоже должны будут нести `t_event_valid_start` и `t_ingestion_start` — иначе невозможно воспроизвести «что я знал и когда» из Audit Layer. Сейчас в trace только `retrieved_at` — один timestamp без bi-temporal семантики.

---

## 📦 4. storage.py (v8.0.3-p0) — Правильный ABC, но неполный контракт

### ✅ Что правильно

GraphStore ABC — правильный архитектурный паттерн. Разделение `store_fact`, `get_fact`, `get_all_facts`, `update_state` на абстрактные методы создаёт чёткую границу для подмены SQLite на Neo4j без изменения вызывающего кода. Комментарий «I50: epistemic_state изменяется ТОЛЬКО через update_state()» в docstring — хорошая документация инварианта прямо в коде.

### 🔴 Отсутствует bi-temporal интерфейс

Для реализации V9 §2.1 контракта нужны методы которых в ABC нет:

```python
# Нет этих методов в GraphStore ABC:
def get_fact_at(self, fact_id: str, known_at: datetime, world_at: datetime) -> Optional[Dict]: ...
def invalidate_edge(self, fact_id: str, t_event_valid_end: datetime) -> bool: ...
def search(self, query: str, mode: str, limit: int) -> List[Dict]: ...
```

`get_fact_at()` нужен для time-travel запросов. `invalidate_edge()` нужен для принципа «никогда не DELETE, только SET t_*_end». `search()` нужен для замены mock DATABASE в pipeline.py. Без этих методов в ABC любая реализация (SQLiteGraphStore, будущий Neo4jGraphStore) будет вынуждена добавлять их вне контракта.

### ⚠️ Нет методов для BlackboardBus

V9 §2.2 описывает `BlackboardModule` с двумя методами: `read_signals()` и `write_observation()`. Текущий `GraphStore ABC` — это хранилище, не blackboard. При реализации Neural Blackboard Pattern (V9 Contract Sprint 1) придётся либо создавать отдельный `BlackboardBus` поверх `GraphStore`, либо расширять ABC. Архитектурное решение нужно принять до Sprint 1.

---

## 🧪 5. test_esm.py — Отличное покрытие с критическим структурным багом

### ✅ Покрытие инвариантов

Тесты покрывают 21 сценарий и все ключевые инварианты: I1 (8 состояний), I6 (Ring Zero), I50 (Observed-only initial state), LRU поведение (cap, evict oldest, read refreshes recency), история (empty, append, persist across L0 clear, by param), confidence (negative, >1, boundary), deepcopy (no aliasing), UPSERT (preserves state), get_all_facts (filter, no filter). Это хорошее тестовое покрытие для MVP-уровня.

### 🔴 Критический баг: тестовая изоляция не работает

Фикстура `isolated_db` делает следующее:

```python
@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    from core import memory
    memory._L0.clear()
    memory._DDL_INITIALIZED.clear()
    monkeypatch.setattr(memory, "SQLITE_PATH", str(tmp_path / "test.db"))
    yield
    memory._L0.clear()
    memory._DDL_INITIALIZED.clear()
```

Проблема: `_GLOBAL_STORE` создаётся при импорте модуля с оригинальным `SQLITE_PATH = "./data/velantrim_memory.db"`. После `monkeypatch.setattr(memory, "SQLITE_PATH", ...)` модульная переменная изменена, но `_GLOBAL_STORE.db_path` по-прежнему указывает на оригинальный путь. Все вызовы `store_fact()`, `get_fact()`, `transition_esm()` через глобальные функции пишут в `_GLOBAL_STORE._db()` → `self.db_path` → оригинальный файл.

Последствие: тесты **не изолированы** друг от друга на уровне SQLite. Факты, записанные в тесте A, видны в тесте B если они используют один и тот же `_GLOBAL_STORE`. Тест `test_store_fact_preserves_validated_after_upsert` делает `sqlite3.connect(memory.SQLITE_PATH)` — после монкипатча это `tmp_path / "test.db"` (пустой файл), тогда как реальные данные записаны в оригинальный файл. Этот конкретный тест может давать ложноположительный результат.

💡 **Исправление:** вместо монкипатча модульной переменной нужно заменить `_GLOBAL_STORE` целиком:

```python
@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    from core import memory
    fresh_store = memory.SQLiteGraphStore(str(tmp_path / "test.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh_store)
    monkeypatch.setattr(memory, "_L0", fresh_store._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh_store._ddl_initialized_paths)
    yield
```

### ⚠️ Непокрытые сценарии

Дрейф claim (TASK-02): когда claim меняется у Validated факта, происходит автоматический переход в Contradicted. Этот сценарий в `store_fact()` реализован и важен, но тест для него отсутствует. TASK-11 double-close: метод `close()` идемпотентен, но не тестируется. Concurrent access: SQLite с `BEGIN EXCLUSIVE` транзакцией обещает serialization, но конкурентных тестов нет. Bi-temporal поля: когда будут добавлены, нужны тесты time-travel запросов.

---

## ⚡ 6. SPRINT_A_V2_ADDITIONAL_PATCHES.md — Важные находки

### Полная карта патчей A1-A10

| Патч | Компонент | Проблема | Решение |
|------|-----------|---------|---------|
| A1 | raw_memory_store | — | ✅ Идемпотентные вставки |
| A2 | memory_guardian | Инъекция параметров | ✅ Строгие Cypher контракты |
| A3 | pii_redaction | Overlap matching | ✅ Span deduplication |
| A4 | truth_gate | NULL handling | ✅ coalesce() индексирование |
| A5 | fractal_similarity | CPU overload | ✅ Bounded concurrency (Semaphore) |
| A6 | event_bus | Queue overflow (maxlen=None) | ✅ Backpressure + DLQ (deque maxlen=10K) |
| A7 | graph_transactions | Deadlock risk | ✅ Lock ordering + timeout |
| A8 | memory_gc | L3 никогда не уменьшается | ✅ Soft→Hard delete lifecycle |
| A9 | llm_calls | Rate limit cascade | ✅ Token budget + timeout + bounded retry |
| A10 | redis_pool | Connection leak | ✅ Bounded pool + timeout |

### 🔴 Критическое противоречие: EventBus (A6) — deque, а не Redis Streams

V9 §3.1 заявляет: «EventBus (Redis Streams) 🟢 Production, 🟦 Documented». Патч A6 реализует EventBus через `collections.deque(maxlen=10_000)` — in-memory Python очередь, не Redis Streams.

Это означает две вещи. Во-первых, EventBus не персистентен — при рестарте процесса все события в очереди теряются. Redis Streams сохраняют события на диске. Во-вторых, EventBus не масштабируется на несколько процессов — `asyncio.Lock` работает только внутри одного event loop. Redis Streams работают между процессами и нодами.

Redis в системе есть — это патч A10 (`redis_connection_pool.py`), но он реализует только `get()` / `set()` операции, а не Streams consumer groups. Фактически Redis используется только как key-value кэш, не как event bus.

💡 **Предложение:** обновить V9 §3.1 verification_layer для EventBus: `🟦 Documented` → `⚠️ Hypothesis` с примечанием «реализован как in-memory deque (A6); Redis Streams — Sprint 2». RFC0036 (Persistent Event Fallback Queue) частично реализован через DLQ в A6, но персистентность на SQLite из V8 не перенесена.

### ✅ A7 Graph Transaction Safety — правильная идея, ограниченная область

`GraphTransactionBounds` через in-memory asyncio.Lock с алфавитным упорядочиванием node_id — корректное решение для предотвращения deadlock внутри одного процесса. Это закрывает конкурентную запись ConsolidationEngine + Observer на Neo4j внутри одного сервиса.

Ограничение: при Distributed Velantrim (V9 Horizons §V6) in-memory блокировки не работают. Но для Sprint 1 это приемлемо.

### ✅ A9 LLM Call Safety — полноценный production класс

`SafeLLMCaller` с `LLMBounds` (concurrent_calls=10, timeout=120s, max_retries=3, backoff exponential) и `TokenBucket` rate limiter — это полноценный production-уровень. Это именно то, что нужно перед тем как pipeline.py получит реальный LLM вызов в F6. Важная деталь: `aioredis` deprecated на Python 3.11+, правильно заменён на `redis.asyncio` из `redis-py >= 4.2.0` (прямо указано в A10).

---

## 📊 7. Сводная матрица: Specification vs Code Reality

| Компонент V9 | Статус V9 | Реальность в коде | Разрыв |
|-------------|-----------|-------------------|--------|
| ESM (8 состояний) | 🟢 ✅ Verified | ✅ Реализован полностью | Нет |
| L0 LRU кэш (128 слотов) | 🟢 ⚠️ Hypothesis | ✅ Реализован, протестирован | V9 занижает — должен быть 🟦 Documented |
| L1 SQLite + FTS5 | 🟢 ⚠️ Hypothesis | ⚠️ SQLite есть, FTS5 — нет | Частичный |
| L1.5 Velum | 🟢 ✅ Verified | 🔴 В коде нет | Отсутствует |
| L3 Knowledge Graph (Neo4j) | 🟢 ⚠️ Hypothesis | 🔴 SQLite заглушка, TODO Sprint 2c | Статус завышен |
| L4 ReasoningBank | 🟡 ✅ Verified (P3-D) | 🔴 В pipeline.py нет | Отсутствует в коде |
| Truth Gate (полный) | 🟢 ✅ Verified | ⚠️ MVP: confidence floor 0.5 | Placeholder |
| Truth Gate (ESM атомарность) | 🟢 ✅ Verified (P2-4) | ✅ transition_esm() атомарен | Совпадает |
| EventBus (Redis Streams) | 🟢 🟦 Documented | ⚠️ deque in-memory (A6), не Redis | Тип хранилища другой |
| Canonical Memory Protocol | ✅ В Specification | 🔴 15% реализовано | Огромный разрыв |
| Bi-Temporal Validity (I96) | 🟢 + bi-temporal | 🔴 Нет в схеме | Sprint 1 контракт не выполнен |
| Neural Blackboard (I97) | 🟢 + Blackboard | 🔴 Прямые функции store_fact | Sprint 1 контракт не выполнен |
| Memory Guardian | 🟦 Documented §11 | ⚠️ Упомянут в A2, не в коде core/ | Частично |
| PII Redaction | 🟦 Documented §12 | ⚠️ Упомянут в A3, не в core/ | Частично |
| OutputFaithfulnessChecker | 🟡 Beta | 🔴 В pipeline.py нет | Отсутствует |
| Slow Path (S1-S7) | Specification §10.3 | 🔴 Полностью отсутствует | Не реализован |
| LLM Generation (F6) | Specification §10.3 | 🔴 Заменён string join | Sprint 2 |

---

## 🎯 8. Приоритизированные рекомендации

### 🔴 До начала Sprint 1 (блокеры)

**Исправить тестовую изоляцию** в `test_esm.py`. Текущий `monkeypatch.setattr(memory, "SQLITE_PATH", ...)` не изолирует тесты на уровне БД. Нужно заменить `_GLOBAL_STORE` через monkeypatch (см. §5). Без этого нельзя доверять тестам при параллельном запуске.

**Уточнить статус EventBus в V9 реестре**. Текущий код — deque, не Redis Streams. Строка V9 «EventBus (Redis Streams) 🟢 Production» создаёт ложную уверенность. Нужно либо реализовать Redis Streams (если это Sprint 1 задача), либо обновить статус на «deque MVP, Redis Streams — Sprint 2».

**Добавить bi-temporal поля в схему** как первый шаг Sprint 1. `velantrim_migrate_v3_1.py` из набора файлов скорее всего для этого и предназначен — нужно проверить что он корректно добавляет все 4 поля и что `store_fact()` / `update_state()` их заполняют.

### ⚠️ В течение Sprint 1

Добавить в `GraphStore ABC` три метода: `get_fact_at(fact_id, known_at, world_at)`, `invalidate_edge(fact_id, t_event_valid_end)`, `search(query, mode, limit)`. Без них нельзя реализовать ни bi-temporal queries, ни замену mock DATABASE в pipeline.py.

Добавить тест для TASK-02 drift protection: создать Validated факт, вызвать `store_fact()` с изменённым claim, проверить что состояние стало Contradicted и history содержит запись.

Добавить параметр `by` в `promote_trace()` и `promoted_by` поле в trace элементы — для полноты audit trail.

### 💡 Structural decisions для V9.2

Определить архитектуру BlackboardBus до рефакторинга модулей. Варианта два: расширить `GraphStore ABC` до `BlackboardModule` (один класс), или создать отдельный `BlackboardBus` поверх `GraphStore` (два класса). Первый вариант проще для MVP, второй лучше соответствует V9 §2.2.

Обновить verification_layer в V9 для L0 LRU кэша с `⚠️ Hypothesis` на `🟦 Documented` — есть и код, и тесты, и это работает. Это честнее.

Разделить Truth Gate в реестре на два компонента с разными статусами: `TruthGate.ESM (✅ Verified P2-4)` и `TruthGate.Semantic (⚠️ Hypothesis — MVP placeholder)`.

---

## 🔱 Итог

Код — честный, хорошо написанный MVP с правильными архитектурными решениями на уровне которого он находится. `memory.py` — самый зрелый файл, заслуживает доверия. `test_esm.py` — хорошее покрытие, один структурный баг в изоляции. Патчи A1-A10 — Production-hardening реальных проблем. `pipeline.py` и `trace.py` — правильный скаффолд для будущей системы.

Главная проблема не в коде, а в зазоре между кодом и спецификацией. V9 описывает систему которая примерно в 5-6 раз сложнее того что сейчас запущено. Это нормально для стратегического документа — но аудит Sprint 1 должен начинаться с честного признания этого разрыва, а не с предположения что V9 описывает текущую реальность.

Sprint 1 фактически должен включить три параллельных трека: **архитектурные контракты** (bi-temporal schema, blackboard pattern), **заполнение реестровых пробелов** (L1.5 Velum в коде, ReasoningBank в коде, EventBus как Redis Streams) и **тестовая инфраструктура** (изоляция, bi-temporal тесты, integration тесты пайплайна). Это три разные работы, и шесть недель Sprint 1 хватит только если они идут параллельно.
