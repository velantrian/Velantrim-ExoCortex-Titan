# RFC-0083 — EITI Learning Patch & Adaptive Cognition Shadow

> **Статус:** `DRAFT · SHADOW_ONLY · NOT_RUNTIME_WIRED · NO_DIRECT_CANON_WRITES`  
> **Дата:** 2026-07-24  
> **Источник эксперимента:** `velantrian/velantrim-eiti`  
> **Связи:** RFC-0081 Fast Path, RFC-0082 Slow Path, TruthGate, RelationStore, CuriosityEngine.

---

## 1. Коротко

EITI показывает рабочий локальный цикл обучения из диалога: модель предлагает новые факты, MOSC-связи, intent-patterns и параметры retrieval. Titan не должен копировать этот цикл как прямую запись в память. Он принимает только безопасную форму идеи:

```text
Conversation
    ↓
Dialogue analysis
    ↓
LearningPatch (proposal only)
    ↓
Schema validation + provenance
    ↓
Shadow evaluation
    ↓
External policy / Operator decision
    ↓
Future admitted events and derived projections
```

В первом срезе реализован только типизированный `LearningPatch` и детерминированная валидация. Нет хранилища, фонового worker, API endpoint, автоматического применения или записи в Canon.

---

## 2. Почему это полезно Titan

Titan уже имеет память, ESM, TruthGate, типизированные relations, Hebbian strength/LTP/LTD, decay, CuriosityEngine и Slow Path. Не хватало единого контракта, который отвечает на вопрос:

> Что именно система предлагает изменить после разговора, прежде чем эти изменения попадут в какой-либо рабочий слой?

`LearningPatch` закрывает эту границу. Он отделяет вывод анализатора от доверенного состояния системы.

```text
LLM output ≠ admitted memory
repeated phrase ≠ truth
retrieval success ≠ evidence
lexical association ≠ canonical relation
policy proposal ≠ active policy
```

---

## 3. Что подтверждено в EITI

Исходный EITI-контракт `eitiApplyAnalysis()` обрабатывает четыре секции:

- `kb` — предложения новых фактов;
- `vb` — intent + regex patterns;
- `mosc` — связи слово/фраза → концепт с весом;
- `fl` — обновления retrieval-настроек.

Тесты EITI фиксируют полезные свойства:

- ошибочный regex не должен обрушать остальные секции;
- частичное retrieval-обновление сохраняет нетронутые поля;
- MOSC-рёбра объединяются с существующими;
- source/timestamp сохраняются;
- pending-analysis очищается после применения.

Для Titan это источник инженерного паттерна, а не доказательство готовности production-механизма.

---

## 4. Карта переноса

| EITI | Titan | Статус в RFC-0083 |
|---|---|---|
| `kb` | `ClaimProposal` | реализован typed contract |
| MOSC | `LexicalAssociationProposal` → будущий `MOSCIndex` | proposal only |
| Velantrim Brain regex | `IntentPatternProposal` → будущий deterministic router | proposal only |
| `fl` | `RetrievalPolicyProposal` | переименовано; proposal only |
| PKG weight | `ChargeSignalProposal` + существующий relation strength | signal only |
| Full Context | fallback/debug/export mode | documented, not implemented |

Название `FL` не используется, потому что проверенный механизм EITI не является federated learning и не обучает параметры нейросети. Корректное название: **Adaptive Retrieval Policy Proposal**.

---

## 5. LearningPatch schema

`core/learning_patch.py` определяет:

### 5.1 Provenance

```text
conversation_id
actor
model (optional)
message_ids[]
observed_at
```

Provenance объясняет, откуда возникло предложение. Она не делает предложение истинным.

### 5.2 ClaimProposal

```text
text
confidence
knowledge_type
evidence_refs[]
```

`ClaimProposal` — кандидат на дальнейший admission flow. Он не имеет ESM-state и не является Fact.

### 5.3 LexicalAssociationProposal

```text
surface
concept
weight
language
domain
```

Это будущий derived lexical routing index. Он не должен записываться как `SUPPORTS`, `CAUSES` или другая canonical relation.

### 5.4 IntentPatternProposal

```text
intent
pattern
confidence
language
```

Regex компилируется только для проверки синтаксиса. Модуль не исполняет pattern над пользовательскими данными и не включает его в live router.

### 5.5 RetrievalPolicyProposal

```text
mode?
threshold?
max_items?
graph_depth?
reason
```

Предложение может быть частичным. Даже валидная структура не даёт права менять active retrieval configuration.

### 5.6 ChargeSignalProposal

```text
target_id
signal_type
magnitude
note
```

Допустимые сигналы первого среза:

- `REPETITION`;
- `RECENCY`;
- `SUCCESSFUL_USE`;
- `EXPLICIT_PRIORITY`;
- `TASK_RELEVANCE`.

Charge влияет только на доступность/приоритет после отдельной оценки. Он не является confidence, truth_status или evidence.

---

## 6. Инварианты

| ID | Инвариант |
|---|---|
| LP-01 | LearningPatch — предложение, не Fact и не evidence |
| LP-02 | Модуль не пишет в storage, TruthGate, RelationStore или Canon |
| LP-03 | MOSC/VB/Charge не повышают epistemic state |
| LP-04 | Retrieval-policy требует shadow comparison и внешнего решения |
| LP-05 | Ошибочные поля возвращаются как validation findings |
| LP-06 | В patch нет метода `apply()` |
| LP-07 | `SHADOW_VALID` означает только успешную shadow-проверку |
| LP-08 | Operator GO остаётся внешним по отношению к объекту patch |
| LP-09 | Utility/repetition не становятся truth evidence |
| LP-10 | Main runtime не подключается этим PR |

---

## 7. MOSC в Titan

Правильная роль MOSC:

```text
user phrase
    ↓
lexical association lookup
    ↓
intent/domain priors
    ↓
SituationModel / SearchSignal
    ↓
normal retrieval and policy checks
```

MOSC полезен как дешёвый объяснимый pre-router и offline fallback. Он не заменяет semantic retrieval, causal graph или reasoning.

Будущая запись `MOSCIndex` должна иметь:

- source patch id;
- observation count;
- positive/negative outcome counters;
- language/domain;
- created/last-used timestamps;
- decay policy;
- status `proposed / shadow / active / suppressed`;
- tenant/user scope;
- rollback version.

Медицинские, эмоциональные и safety-sensitive маршруты требуют отдельной политики и не могут активироваться только по одному слову.

---

## 8. Velantrim Brain / deterministic intent layer

VB-patterns полезны для:

- пользовательских сокращений;
- локальных команд;
- offline intent bootstrap;
- объяснимого routing;
- стабильного распознавания повторяющихся формулировок.

Но regex не является «мозгом». Будущий router должен иметь:

- длину и complexity limits;
- безопасный regex engine или timeout;
- positive/negative examples;
- scope и expiry;
- provenance;
- conflict resolution;
- ручное выключение;
- shadow metrics до активации.

---

## 9. Adaptive Retrieval Policy

Предложения должны оцениваться по task/domain profile, а не глобально:

```text
baseline policy
    vs
candidate policy
    ↓
replay corpus / shadow queries
    ↓
precision, recall, conflict coverage, latency, token cost
    ↓
accept / reject / request review
```

Минимальные критерии будущего promotion:

- не ухудшает retrieval precision;
- не теряет relevant conflict/evidence;
- не обходит Safe Recall Boundary;
- не раскрывает restricted/erased facts;
- имеет version + rollback;
- решение зарегистрировано в audit trail.

---

## 10. Связь с существующим Hebbian layer

`RelationStore` уже содержит `strength`, `ltp_count`, `ltd_count`. RFC-0083 не создаёт второй граф весов.

```text
EITI PKG signal
    ↓
ChargeSignalProposal
    ↓
shadow evaluation
    ↓
future use of existing relation strength / Charge projection
```

Главное разделение:

```text
EpistemicState ≠ relation strength ≠ Charge ≠ utility ≠ preference
```

Повторяемая ошибка может иметь высокий retrieval priority, но остаётся ошибкой.

---

## 11. Full Context

EITI Full Context агрегирует notes, KB и personal memory и изолирует сбой одного источника. Для Titan это допустимо только как:

- debugging;
- migration/export;
- emergency fallback;
- provider-switch continuity;
- evaluation baseline.

Он не должен стать стандартным agent-facing retrieval, потому что bulk injection:

- увеличивает token cost;
- смешивает релевантное и нерелевантное;
- повышает риск stale/restricted context;
- не формирует честный selection Receipt.

---

## 12. Threat model

Основные риски:

1. **Prompt-to-memory injection** — LLM предлагает ложный Claim.
2. **Regex abuse** — сложный pattern создаёт ReDoS или ложные intents.
3. **Policy drift** — threshold/max_items постепенно ухудшают retrieval.
4. **Popularity-to-truth leak** — repetition ошибочно повышает доверие.
5. **Cross-tenant learning** — персональная ассоциация попадает другому пользователю.
6. **Sensitive routing** — эмоциональное/медицинское слово вызывает неправильный режим.
7. **Silent partial apply** — часть patch применена, часть потеряна.
8. **Unbounded growth** — MOSC и patterns растут без pruning/versioning.

Первый PR устраняет главный риск прямой записи: объект не имеет apply/persistence path.

---

## 13. Этапы rollout

### Stage A — Typed contract

- `LearningPatch` dataclasses;
- deterministic validation;
- normalization для MOSC duplicates;
- shadow result status;
- focused tests;
- no wiring.

### Stage B — Shadow store

После завершения текущего hardening-order:

- отдельный append-only shadow journal;
- tenant scope;
- idempotency key;
- immutable source envelope;
- no Canon projection.

### Stage C — Evaluators

- replay corpus;
- retrieval A/B comparison;
- regex safety checks;
- MOSC precision/coverage;
- policy drift alarms;
- Observer warnings.

### Stage D — Controlled projections

Только отдельным Operator GO:

- derived MOSCIndex;
- deterministic intent router;
- versioned policy profiles;
- Charge signals into existing non-epistemic mechanics.

### Stage E — Admission bridge

Только после отдельного RFC/threat model:

- ClaimProposal → TruthGate/admission candidate;
- provenance and evidence verification;
- atomic event write;
- rollback/replay;
- no direct LLM-to-Canon path.

---

## 14. Acceptance gates

Этот RFC не считается live integration, пока не выполнены отдельно:

- current production-hardening queue завершена;
- full test suite and CI green;
- shadow journal designed and threat-modeled;
- tenant erasure applies to all derived indexes;
- Safe Recall Boundary covers new retrieval paths;
- policy evaluator has objective metrics;
- regex execution has bounded resource policy;
- Operator explicitly approves runtime wiring.

---

## 15. Current implementation truth

В текущем draft реализовано:

- typed LearningPatch contract;
- provenance envelope;
- five proposal families;
- deterministic bounds and regex syntax validation;
- MOSC association normalization/deduplication;
- `PROPOSED / SHADOW_VALID / SHADOW_REJECTED` lifecycle;
- tests that assert absence of `apply()` and separation of Charge from evidence.

Не реализовано:

- Dialogue Analyzer;
- automatic patch generation;
- storage/API/worker;
- MOSCIndex runtime;
- live intent routing;
- active retrieval-policy mutation;
- Canon/TruthGate bridge;
- Native Kernel event integration.

**Reading rule:** presence of a schema in `core/learning_patch.py` means that the proposal contract exists. It does not mean the proposed capability is active in Titan runtime.
