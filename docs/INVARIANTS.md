# INVARIANTS.md — Velantrim ExoCortex v8.4.0

> ⚠️ **Статус документа:** исторический реестр части инвариантов V8.x.
> Текущую исполняемую границу проверяйте по `tests/test_invariants.py`, коду
> соответствующего контракта и CI. Общая зрелость Titan 9.0 описана в
> [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

> **Версия:** v8.4.0 · Audit-fixed integration layer
>
> **Золотое правило:** нарушение любого инварианта — это не баг,
> это архитектурная деградация. Открывай RFC, не чини молча.
>
> **Принцип документа:** числа важнее мнений. Каждый инвариант
> либо enforced тестом, либо помечен как pending.
>
> **v8.4.0 обновление:** I101 переведён из 📋 в ✅ enforced с пометкой
> "MVP enforcement через CRUD-only-API". MHI-2 уточнены пороги (см. ниже).
> Добавлен NLI-1-amended: contradiction detection теперь opt-in.

---

## ESM-инварианты (Epistemic State Machine)

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **I1** | `ESMStatesFixed` | Ровно 8 состояний ESM — фиксировано: `Observed`, `Hypothesized`, `Supported`, `Validated`, `Contradicted`, `Deprecated`, `Collapsed`, `ImmutableCore`. Добавление/удаление только через RFC + мажорную версию. | `core/memory.py:ESM_STATES` | ✅ enforced + tested |
| **I2** | `ESMTransitionsMatrix` | Матрица переходов — только **добавлять** рёбра через RFC. Удаление существующего ребра ломает обратную совместимость. | `core/memory.py:ESM_TRANSITIONS` | ✅ enforced + tested |
| **I6** | `RingZeroImmutable` | `VALUES_CORE` и `RING_ZERO` навсегда в `Validated`. `transition_esm()` для них → `ImmutableStateError`. Расширение `IMMUTABLE_FACT_IDS` запрещено без RFC. | `core/memory.py:IMMUTABLE_FACT_IDS` | ✅ enforced + tested |
| **I50** | `ESMOwnership` | `epistemic_state` изменяется **только** через `transition_esm()`. Прямой SQL `SET epistemic_state` или dict-присвоение — архитектурный баг. Исключение: drift protection в `store_fact` (BUG-FIX v8.3.1 — единственное легитимное исключение). | `core/memory.py:store_fact`, `transition_esm` | ✅ enforced + tested |
| **I50-b** | `ImmutableCoreReserved` | Переход в `ImmutableCore` через `transition_esm` запрещён для всех. Только Ring Zero seed в `store_fact`. | `core/memory.py:transition_esm` | ✅ enforced + tested |
| **I68** | `TruthGateGateway` | Единственный путь перевода факта в `Validated` — через `truth_gate()` в pipeline. Обход — архитектурный баг. Sprint 2a: реальный TruthGate из `core/truth_gate.py` с CognitiveMode. | `core/pipeline.py:truth_gate`, `core/truth_gate.py` | ✅ enforced + tested |
| **I104** | `DriftProtectionL0L1Sync` | При срабатывании drift protection (`store_fact` → Contradicted) L0 и L1 **обязаны** быть синхронны. Реализован через `_drift_detected` флаг и отдельный `UPDATE`. Нарушение = split-brain. | `core/memory.py:store_fact` | ✅ enforced + regression test |

---

## Bi-temporal инварианты (I96, V9 Sprint 1 Contract)

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **I96** | `BiTemporalEdges` | Каждый факт в L1 имеет 4 bi-temporal поля: `t_event_valid_start`, `t_event_valid_end`, `t_ingestion_start`, `t_ingestion_end`. `t_*_start` устанавливается при создании и **никогда не обновляется**. `t_*_end` только через `invalidate_edge()` или при Collapsed/Contradicted. ⚠️ SQLite: хранятся как TEXT ISO 8601 UTC — timezone mixing запрещён. | `core/memory.py:store_fact`, `update_state`, `invalidate_edge` | ✅ enforced + tested |
| **I96-a** | `NoDeleteOnlyInvalidate` | Факты **никогда не удаляются** (no DELETE). Инвалидация только через `invalidate_edge()` — выставляет `t_*_end`. | `core/memory.py:invalidate_edge` | ✅ enforced |
| **I96-b** | `TimeZoneUTC` | Все `t_*` поля строго UTC без timezone-суффикса. Пример правильного: `"2026-05-11T12:00:00"`. Пример неправильного: `"2026-05-11T12:00:00+03:00"`. | `core/memory.py:_now()` | ✅ enforced через `_now()` |
| **I97** | `BlackboardOnly` | В production (Neo4j): прямой Cypher CREATE/SET на L3 запрещён вне BlackboardBus. MVP (SQLite): контракт зафиксирован в `GraphStore ABC`. BlackboardBus — Sprint 2c. | `core/storage.py:GraphStore` | 📋 pending Sprint 2c |

---

## Данные и хранение

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **D1** | `FactIdRequired` | Каждый факт обязан иметь `fact_id`. `store_fact` без `fact_id` → `ValueError`. | `core/memory.py:store_fact` | ✅ enforced |
| **D2** | `ConfidenceRange` | `confidence ∈ [0.0, 1.0]`. Нарушение → `ValueError` через `_validate_confidence()`. | `core/memory.py:_validate_confidence` | ✅ enforced |
| **D3** | `DeepCopyOnGet` | `get_fact()` возвращает `deepcopy` — внешняя мутация не корруптирует L0. | `core/memory.py:get_fact` | ✅ enforced + tested |
| **D4** | `L1PrimaryTruth` | При расхождении L0 (RAM) и L1 (SQLite) — L1 является источником истины. L0 — кэш, сброс через рестарт. | `core/memory.py` | ✅ enforced через порядок чтения |
| **D5** | `HistoryAppendOnly` | `history` — append-only JSON-массив. Никаких splice/delete записей истории. | `core/memory.py:update_state` | ✅ enforced |
| **D6** | `SearchIsMVP` | `SQLiteGraphStore.search()` — MVP LIKE по claim. Нарушает семантику полноценного поиска. Не использовать в production без FTS5 или Neo4j. | `core/memory.py:search` | ⚠️ documented limitation |

---

## Pipeline инварианты

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **PL1** | `TraceBeforeValidation` | Trace строится **до** ESM-перехода. Порядок: Retrieve → FactsPack → Trace → Guardian → TruthGate → ESM. | `core/pipeline.py:run` | ✅ enforced |
| **PL2** | `GuardianBeforeTruthGate` | Guardian (структурная проверка) всегда перед TruthGate (семантическая). Разные ответственности. | `core/pipeline.py:run` | ✅ enforced |
| **PL3** | `IdempotentRun` | `pipeline.run()` идемпотентен: повторный вызов с теми же фактами не роняет пайплайн (Validated→Validated пропускается). | `core/pipeline.py:run` | ✅ enforced + tested |
| **PL4** | `ConfidenceFromSource` | `confidence` в FactsPack берётся из источника (стабильная). `retrieval_score` (BM25-балл) — volatile, не персистируется в L1. | `core/pipeline.py:build_facts_pack` | ✅ enforced |

---

## NGramIndex инварианты (v1.0.0, Sprint 2a)

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **I99** | `NGramIndexIsolation` | `NGramIndex` хранит только `(doc_id, content)` — не ESM-состояние, не confidence, не history. Вспомогательный pre-filter, не источник истины. `NGramIndex` не заменяет запись в L1/L3. Graph = Truth сохраняется. | `core/ngram_index.py` | ✅ enforced |
| **I99-a** | `NGramGracefulDegradation` | Если FTS5/trigram недоступен — `NGramIndex.available` (property, не метод) возвращает `False`, `query()` возвращает `[]`. Pipeline делает fallback на полный поиск. Никаких исключений. | `core/ngram_index.py`, `core/pipeline.py` | ✅ enforced |

---

## SleepTimeWorker инварианты

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **I100** | `SlowPathOnly` | `SleepTimeWorker.think()` выполняется только в Slow Path (фоновый asyncio.Task). Запрещено вызывать синхронно из Fast Path. ⚠️ MVP: runtime enforcement — Sprint 2c. | `core/sleep_time_worker.py` | 📋 pending Sprint 2c |
| **I101** | `CoreBlocksExplicit` | `CoreMemoryBlocks.update()` — только явный CRUD через метод `update(name, content)`. LLM не пишет напрямую в БД блоков в обход `update()`. ⚠️ **v8.4.0:** MVP уровень — Truth Gate валидация контента блоков **не реализована** (см. docstring класса). Sprint 2c: добавить TruthGate.validate перед SQLite INSERT. До тех пор атакующий с доступом к API может записать prompt-injection в `current_goals`. | `core/sleep_time_worker.py:CoreMemoryBlocks.update` | ⚠️ enforced (CRUD-only) / 📋 TruthGate pending Sprint 2c |
| **I102** | `NotebookNotL3` | `ResearchNotebook` хранится в отдельной БД. Не пишет напрямую в L3. Продвижение в L3 — через TruthGate (Sprint 2c). | `core/sleep_time_worker.py` | ✅ enforced |
| **I103** | `TaskRefHeld` | `SleepTimeWorker._task` хранит ссылку на asyncio.Task. Без этого task уничтожается GC без уведомления (silent death). | `core/sleep_time_worker.py` | ✅ enforced |

---

## NLI и TruthGate инварианты (v8.4.0 specific)

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **I68-a** | `TruthGateCognitiveMode` | TruthGate поддерживает 4 режима: `PRECISION` (conf≥0.9, ev≥5), `BALANCED` (conf≥0.7, ev≥2), `EXPLORATION` (conf≥0.4, ev≥1), `CREATIVE` (conf≥0.7, ev≥2). Default: `BALANCED`. | `core/truth_gate.py:CognitiveMode` | ✅ enforced |
| **I68-b** | `TruthGateNeverThrows` | `TruthGate.evaluate()` никогда не бросает исключений — только возвращает `TruthGateVerdict(passed=False, ...)`. | `core/truth_gate.py:evaluate` | ✅ enforced |
| **NLI-1** | `NLIContradictionSource` | Обнаружение противоречий через NLI (cross-encoder) находится в ATLAS-OS, не в Velantrim. Velantrim получает результаты через `TruthGate._find_contradictions_nli()`. Прямое использование NLI-модели в pipeline.py запрещено. | `core/truth_gate.py` | 📋 pending Sprint 2c |
| **NLI-1-amended (v8.4.0)** | `ContradictionDetectorExplicit` | TruthGate теперь принимает явный параметр `contradiction_detector` со значениями `"none"\|"naive"\|"nli"`. Default = `"none"` — стадия 4 пропущена. Naive детектор отключён по умолчанию из-за известных false positives на парах с XOR-negation. Использовать `"naive"` только в development. `"nli"` поднимает `NotImplementedError` до Sprint 2c. | `core/truth_gate.py:TruthGate.__init__` | ✅ enforced + tested |

---

## Causal Graph инварианты (Patch 13, PLANNED)

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **CG-1** | `RelationTypes12` | Ровно 12 типов отношений. Добавление через RFC + minor version bump. | `core/causal_graph.py` | 📋 Patch 13 |
| **CG-2** | `NoSelfLoop` | `from_fact_id ≠ to_fact_id` — петли запрещены на уровне CHECK constraint. | `core/causal_graph.py` | 📋 Patch 13 |
| **CG-3** | `KnowledgeStatusSeparateFromConfidence` | `knowledge_status` ('known'/'inferred'/'hypothetical'/'unknown') и `confidence` (float) — разные поля с разной семантикой. Нельзя заменять одно другим. | `core/causal_graph.py` | 📋 Patch 13 |
| **CG-4** | `InverseAutoCreation` | Добавление `causes(A,B)` автоматически создаёт `caused_by(B,A)`. Inverse удаляется при удалении оригинала. | `core/causal_graph.py` | 📋 Patch 13 |
| **CG-5** | `CounterfactualIsolation` | `counterfactual()` создаёт клон подграфа. Клон **не изменяет** оригинальный граф. Все выведенные рёбра в клоне получают `knowledge_status='hypothetical'`. | `core/causal_graph.py` | 📋 Patch 13 |

---

## Memory Health Index инварианты (MHI)

| ID | Имя | Описание | Файл | Статус |
|----|-----|----------|------|--------|
| **MHI-1** | `MHIFormula` | `MHI = 0.30×validated + 0.25×freshness + 0.25×precision + 0.20×graph`. Изменение весов только через RFC. | `core/mhi.py:MHICalculator` | ✅ enforced |
| **MHI-2** | `MHIThresholds` | `HEALTHY ≥ 0.60` / `DEGRADED ≥ 0.30 (включая 0.30–0.50 «тяжёлый DEGRADED» и 0.50–0.60 «лёгкий DEGRADED» через `THRESHOLD_DEGRADED=0.50`)` / `SAFE_MODE < 0.30`. Изменение порогов требует пересчёта SLO. **v8.4.0:** `THRESHOLD_DEGRADED=0.50` теперь реально используется в `_recommendations()` для разделения уровней alert'а — раньше была мёртвой константой. | `core/mhi.py:MHIStatus`, `_status`, `_recommendations` | ✅ enforced + tested (test_mhi_threshold_degraded_is_used) |
| **MHI-3** | `MHINeverThrows` | `MHICalculator.calculate()` никогда не бросает исключений — возвращает `MHIReport` с `status=SAFE_MODE` при ошибке. | `core/mhi.py:calculate` | ✅ enforced |

---

## Семантика bi-temporal полей

```
t_event_valid_start  ← когда факт стал истинным в мире
t_event_valid_end    ← когда факт перестал быть истинным (null = всё ещё истина)
t_ingestion_start    ← когда система узнала об этом факте
t_ingestion_end      ← когда система перестала верить (null = всё ещё верим)

Принцип: НИКОГДА не DELETE — только инвалидируй через invalidate_edge().
Timezone: все поля — строго UTC без суффикса. Пример: "2026-05-11T12:00:00"
```

---

## Сводка по статусам

| Статус | Количество | Смысл |
|--------|-----------|-------|
| ✅ enforced + tested | 16 | Код + тест, нарушение сразу видно |
| ✅ enforced | 6 | Код есть, теста нет — добавить |
| 📋 pending | 8 | Запланировано, не реализовано |
| ⚠️ documented | 1 | Известное ограничение, задокументировано |

**Не задокументировано:** инварианты I3–I49, I51–I67, I69–I95 из V9 JSONL-спеки.
→ Sprint 3: автогенерация из спеки.

---

*Velantrim ExoCortex INVARIANTS.md · v8.4.4 · Май 2026*
*"Нарушение инварианта — это архитектурная деградация, не баг."*
