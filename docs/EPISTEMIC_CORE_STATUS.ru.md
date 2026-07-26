# 🧠 Velantrim — Эпистемическое ядро: что построено, где в коде, как включить

> **Назначение:** единый источник истины по эпистемическому слою. Прежде чем предлагать
> «FINAL SPEC» по claim_type / source_status / TruthGate / ACID — **прочитай это**: почти
> всё из таких спек УЖЕ реализовано. Здесь — карта инвариантов → код + флаги + как запустить.
> **Дата актуализации:** 2026-07-25 · **Статус:** канон-реестр
> (companion к `POLYGLOT_EPISTEMIC_INVARIANTS.ru.md`).

---

## 0. Главный канон
```
память ≠ знание · чувство ≠ факт мира · опыт ≠ проверенная реальность
важность ≠ истинность · confidence ≠ значимость · оценка ≠ знание · LLM ≠ доказательство
Canonical Local Memory = Truth · retrieval/graph/vector/model output = projection/proposal
```
Реализовано как **3 ортогональные оси** (не смешивать):

| Ось | Поле | Где |
|-----|------|-----|
| Верификация | `epistemic_state` (ESM, 8 состояний) | `core/memory.py` |
| **Модальность** | `claim_type` | `core/validators.py` колонка `facts.claim_type` |
| **Происхождение** | `origin_type` (= спек-`source_status`) | `facts.origin_type` |
| Надёжность | `confidence` | существующее |
| Важность | `salience` (НЕ отдельный `significance_score`) | `core/salience.py` |

---

## 1. Инварианты эпистемики → где в коде (карта «спека I1-I12 → реальность»)

| Инвариант | Где enforced |
|-----------|--------------|
| EMOTION/OPINION/INTERPRETATION не могут стать WORLD_FACT без evidence | `truth_policy.modality_guard` (блок субъективного → ImmutableCore) |
| LLM_OUTPUT сам не доказательство (WORLD_FACT+LLM без evidence ⊘) | `modality_guard` + `write_gate.admit_fact` |
| UNKNOWN не трактуется как WORLD_FACT | `modality_guard` (UNKNOWN-guard) + `recommend_target_state(UNKNOWN)→Observed` |
| significance не меняет truth_status | оси разделены: `salience` ⊥ `confidence`/`epistemic_state` |
| confidence ≠ retrievability | инвариант I202 (`POLYGLOT_EPISTEMIC_INVARIANTS.ru.md`) |
| multi-step write атомарен | `memory.update_state` — одна транзакция (state+history+metadata) |
| no INSERT OR REPLACE для core facts | `memory.py` использует `ON CONFLICT ... DO UPDATE` (UPSERT) |
| write только через контролируемый путь | обязательные `PolicyKernel` + `write_gate.admit_fact`; legacy-флаг не может отключить границу |
| query не изменяет Canon | `pipeline.build_facts_pack/run`: без `store_fact`, ESM promotion, relation writes и reconsolidation |
| слабое внешнее evidence не становится ответом | bounded response `insufficient_validated_local_evidence`; `Observed WORLD_FACT` не используется |
| user report ≠ world truth | canonical `Observed + USER_REPORTED` можно показать только как `UNVERIFIED/reported_only`, без promotion |
| **оценка ≠ знание** (L4/L5 канон) | claim_type разделяет: OPINION/EMOTION хранятся как модальность, не как факт; L5-обучение (когда будет) меняет веса, не факты |

**Type-aware TruthGate:** `core/truth_policy.py` — `modality_guard` (блокирует недопустимый промоушн) + `recommend_target_state` (матрица claim_type × origin_type → ESM-потолок) + `fact_admissible`/`decide` (allow/gap_notice/reject).

---

## 2. ACID-леджер (P0.5) → где
| Гарантия | Реальность |
|----------|-----------|
| WAL | `memory.py:111` |
| foreign_keys=ON | `relations.py`, `causal_graph.py`, `pipeline.py`, `version_store.py` |
| busy_timeout | `memory.py:109` (30 c) |
| **synchronous=FULL** | facts-store (`memory.py`, env `VELANTRIM_SQLITE_SYNCHRONOUS`, default FULL) + `version_store` (всегда FULL) |
| BEGIN IMMEDIATE / атомарность | `update_state` — одна транзакция |
| no INSERT OR REPLACE | UPSERT |

SQLite — постоянный ACID-леджер; **не заменять на Kuzu** (Kuzu/граф = слой связей, см. I200).

---

## 3. Query / ingestion / policy — явные границы

```text
QueryPipeline (read-only)
retrieval → canonical resolve → FactsPack → Guardian → evidence checks → answer/proposal

Ingestion/maintenance (write authority)
candidate → schema/provenance/policy → TruthGate/ESM → canonical transaction
```

`QueryPipeline` не выполняет «удобный» re-store результата retrieval, не
продвигает `Observed → Validated`, не создаёт causal/cross-domain relation и не
запускает reconsolidation, которая обновляет metadata. Causal discovery на
чтении возвращает детерминированный `proposal_id` с
`disposition=proposal_only`; `relation_id` отсутствует до отдельного принятия.

`core/policy_kernel.py` выдаёт неизменяемые:

- `EffectivePolicy`;
- `PolicySnapshot`;
- `PolicyDecision`;
- `CapabilityLease`.

Снимок фиксирует version, stable id, supervisor mode, source и reason code.
При недоступном конфиге или MetaSupervisor canonical write блокируется с
`policy_dependency_unavailable`. Последняя проверенная локальная политика может
сохранить ограничения, но не разрешает high-risk write при неизвестном текущем
состоянии. Network и remote data по умолчанию `deny/never`; remote canonical
write не получает lease.

Подробный исполнимый контракт: `docs/QUERY_POLICY_BOUNDARY.ru.md`.

---

## 4. Опциональные capabilities и диагностические настройки

| Флаг (env) | Что включает | Где |
|------------|--------------|-----|
| `ENABLE_TRUTH_POLICY` | modality-aware honest labeling на query-path; **не** promotion | `pipeline.py`, `truth_policy.py` |
| `ENABLE_ESSENCE` | ответ «по сути» (gist + цепочка) вместо склейки | `essence.py` |
| `ENABLE_GRAPH_EXPANSION` | тянуть граф-соседей в цепочку (multi-hop рассуждение) | `pipeline._expand_with_graph_neighbors` |
| `VELANTRIM_GRAPH_EXPANSION_DEPTH` | глубина обхода (1..3, default 1) | `pipeline._graph_expansion_depth` |
| `ENABLE_TASK_ROUTING` | роутинг по типу запроса (WHY/HOW → граф, FACT → прямо) | `core/task_type.py` |
| `ENABLE_WRITE_GATE` | legacy readout; `0` логируется и игнорируется, потому что gate обязателен | `core/policy_kernel.py`, `core/write_gate.py` |
| `ENABLE_CAUSAL_GRAPH` | причинный граф (рёбра) | `causal_graph.py` |
| `VELANTRIM_EMBEDDING_MODEL` | модель эмбеддингов (default мультиязычная `paraphrase-multilingual-MiniLM-L12-v2`) | `hybrid_retriever.py` |

---

## 5. Как запустить «умный» режим
```powershell
.\scripts\build_kb_graph.py        # связный граф знаний из KB (повторяй после батчей Codex)
.\scripts\serve_smart_kb.ps1       # сервер со всеми флагами ON на графе знаний
python scripts\eval_reasoning.py   # измерить долю рассуждений + связность (сам скажет: данные/код)
```

---

## 6. Что НЕ реализовано осознанно (не предлагать как «новое»)
- `significance_score` как поле — **дубль** существующего `salience`.
- Полиглот (Qdrant/DuckDB/Neo4j-as-core), Kuzu export, episodic PERSON/PLACE/EVENT граф, L2-таблица — преждевременно (см. I200, roadmap).
- Thompson Sampling / Concept Emergence / Prediction Error — P3 roadmap; часть уже есть за флагами (`concept_emergence.py`, `reasoning_bank.py`).
- L6 automation — только после стабилизации L4+L5.

---

## 7. Главный нераскрытый рычаг — ДАННЫЕ, не код
Связность KB ~20% (факты-острова). Доля рассуждений 60%. Рычаг: **ID-связи в батчах Codex** + рост KB к 50k → `build_kb_graph` достроит рёбра. `eval_reasoning.py` сам диагностирует «узкое место = данные/код».

> *Canon хранит утверждённое состояние. Query только читает и объясняет.
> Изменения проходят отдельный policy/truth/write protocol. Граф и модели
> предлагают связи и язык, но не получают скрытого права записи.*
