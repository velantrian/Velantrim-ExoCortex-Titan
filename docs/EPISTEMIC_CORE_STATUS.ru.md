# 🧠 Velantrim — Эпистемическое ядро: что построено, где в коде, как включить

> **Назначение:** единый источник истины по эпистемическому слою. Прежде чем предлагать
> «FINAL SPEC» по claim_type / source_status / TruthGate / ACID — **прочитай это**: почти
> всё из таких спек УЖЕ реализовано. Здесь — карта инвариантов → код + флаги + как запустить.
> **Дата:** 2026-06-03 · **Статус:** канон-реестр (companion к `POLYGLOT_EPISTEMIC_INVARIANTS.ru.md`).

---

## 0. Главный канон
```
память ≠ знание · чувство ≠ факт мира · опыт ≠ проверенная реальность
важность ≠ истинность · confidence ≠ значимость · оценка ≠ знание · LLM ≠ доказательство
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
| write только через контролируемый путь | `write_gate.admit_fact` (за флагом `ENABLE_WRITE_GATE`) |
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

## 3. Флаги «ума» (всё за флагами, default OFF — поведение прежнее)

| Флаг (env) | Что включает | Где |
|------------|--------------|-----|
| `ENABLE_TRUTH_POLICY` | modality-aware промоушн в шаге 6 (EMOTION≠VERIFIED) + honest verdict | `pipeline.py`, `truth_policy.py` |
| `ENABLE_ESSENCE` | ответ «по сути» (gist + цепочка) вместо склейки | `essence.py` |
| `ENABLE_GRAPH_EXPANSION` | тянуть граф-соседей в цепочку (multi-hop рассуждение) | `pipeline._expand_with_graph_neighbors` |
| `VELANTRIM_GRAPH_EXPANSION_DEPTH` | глубина обхода (1..3, default 1) | `pipeline._graph_expansion_depth` |
| `ENABLE_TASK_ROUTING` | роутинг по типу запроса (WHY/HOW → граф, FACT → прямо) | `core/task_type.py` |
| `ENABLE_WRITE_GATE` | эпистемический гейт на записи (WORLD_FACT нужен провенанс) | `core/write_gate.py` |
| `ENABLE_CAUSAL_GRAPH` | причинный граф (рёбра) | `causal_graph.py` |
| `VELANTRIM_EMBEDDING_MODEL` | модель эмбеддингов (default мультиязычная `paraphrase-multilingual-MiniLM-L12-v2`) | `hybrid_retriever.py` |

---

## 4. Как запустить «умный» режим
```powershell
.\scripts\build_kb_graph.py        # связный граф знаний из KB (повторяй после батчей Codex)
.\scripts\serve_smart_kb.ps1       # сервер со всеми флагами ON на графе знаний
python scripts\eval_reasoning.py   # измерить долю рассуждений + связность (сам скажет: данные/код)
```

---

## 5. Что НЕ реализовано осознанно (не предлагать как «новое»)
- `significance_score` как поле — **дубль** существующего `salience`.
- Полиглот (Qdrant/DuckDB/Neo4j-as-core), Kuzu export, episodic PERSON/PLACE/EVENT граф, L2-таблица — преждевременно (см. I200, roadmap).
- Thompson Sampling / Concept Emergence / Prediction Error — P3 roadmap; часть уже есть за флагами (`concept_emergence.py`, `reasoning_bank.py`).
- L6 automation — только после стабилизации L4+L5.

---

## 6. Главный нераскрытый рычаг — ДАННЫЕ, не код
Связность KB ~20% (факты-острова). Доля рассуждений 60%. Рычаг: **ID-связи в батчах Codex** + рост KB к 50k → `build_kb_graph` достроит рёбра. `eval_reasoning.py` сам диагностирует «узкое место = данные/код».

> *Графовый/рассуждающий слой готов. Истину присваивает TruthGate (на чтении и записи).
> Связи строит граф. Язык даёт LLM. Не хватает плотности связей — это трек сбора, не кода.*
