# 🧬 EITI → Titan: карта полезных механизмов

> **Статус:** `RESEARCH_MAPPING · SHADOW_ONLY · NO_LIVE_WIRING`  
> **Главный RFC:** [RFC-0083](./RFC-0083_EITI_LEARNING_PATCH_SHADOW.md)

## Быстрое понимание

```text
EITI                         Titan
────────────────────────────────────────────────────────────
post-chat JSON          →    LearningPatch proposal
MOSC word→concept       →    derived lexical routing index
VB intent regex         →    bounded deterministic intent layer
FL retrieval weights   →    Adaptive Retrieval Policy Proposal
PKG Hebbian weights     →    Charge signals + existing relation strength
Full Context            →    fallback/debug/export, not normal retrieval
```

Titan не копирует монолитный browser runtime. Он забирает только проверяемые архитектурные контракты и помещает их за provenance, validation, shadow evaluation и Operator gate.

---

## 1. LearningPatch

### Что было в EITI

После диалога анализатор возвращает структурированный набор `kb / vb / mosc / fl`, который затем применяется к локальной памяти.

### Что берёт Titan

Единый immutable proposal envelope:

```text
LearningPatch
├── provenance
├── claims[]
├── lexical_associations[]
├── intent_patterns[]
├── retrieval_policy?
└── charge_signals[]
```

### Почему это важно

До этого разные механизмы могли предлагать изменения в разных формах. LearningPatch создаёт одну audit-friendly границу между «модель считает, что этому надо научиться» и «система действительно изменила доверенное состояние».

### Текущий статус

`core/learning_patch.py` существует, валидируется и тестируется, но не подключён к диалогу, памяти, API или worker.

---

## 2. MOSC

### Что было в EITI

Большой словарь/граф вида:

```text
surface phrase → concept/action : weight
```

Он помогает определить, что означает пользовательская формулировка и какой режим/действие может быть релевантно.

### Правильная роль в Titan

MOSC — не Truth Graph. Это derived lexical association index для:

- intent/domain priors;
- SearchSignal;
- SituationModel;
- offline routing;
- explainable pre-selection;
- персональной лексики пользователя.

### Что запрещено

- превращать MOSC-edge в canonical fact;
- повышать confidence по частоте фразы;
- использовать эмоциональное/медицинское слово как единственный safety decision;
- смешивать tenant/user associations;
- бесконтрольно наращивать граф.

### Будущий объект

```text
MOSCRecord
├── surface
├── concept
├── weight
├── language / domain / tenant
├── source_patch_id
├── observed_count
├── success / failure counts
├── created_at / last_used_at
├── decay_policy
└── status: proposed | shadow | active | suppressed
```

---

## 3. Velantrim Brain patterns

### Что было в EITI

LLM может предложить `intent + regex`. Ошибочный regex отбрасывается, не ломая остальные секции.

### Правильная роль в Titan

Это deterministic intent helper, а не самостоятельный brain:

```text
phrase
  ↓
pattern candidates
  ↓
MOSC + task context + policy
  ↓
SituationModel intent candidate
```

### Обязательные ограничения будущего runtime

- max pattern length;
- bounded execution time / safe regex engine;
- positive and negative examples;
- scope, language, tenant and expiry;
- conflicts between patterns;
- provenance and rollback;
- manual suppression;
- shadow precision before activation.

В первом срезе выполняется только syntax compilation during validation. Pattern не запускается над пользовательским вводом.

---

## 4. Adaptive Retrieval Policy

### Почему не `FL`

Проверенный EITI-механизм меняет `mode`, `threshold` и `maxFacts`. Это не federated learning и не обучение neural weights.

### Titan contract

```text
RetrievalPolicyProposal
├── mode?
├── threshold?
├── max_items?
├── graph_depth?
└── reason
```

Partial proposal разрешён. Активировать его только после replay/shadow evaluation.

### Метрики будущего evaluator

- relevant fact recall;
- precision;
- conflict/evidence coverage;
- restricted-data leakage;
- latency;
- context size and token cost;
- answer faithfulness;
- stability across domains.

Каждая принятая policy должна иметь version, scope, reason, metrics, audit record и rollback.

---

## 5. PKG, Hebbian weights и Charge

Titan уже имеет relation `strength`, `ltp_count` и `ltd_count`. Поэтому второй независимый Hebbian graph не создаётся.

EITI-сигналы переводятся в proposal-форму:

```text
ChargeSignalProposal
├── target_id
├── signal_type
├── magnitude
└── note
```

Допустимые классы первого среза:

- repetition;
- recency;
- successful use;
- explicit priority;
- task relevance.

### Неприкосновенное разделение

```text
truth/confidence/evidence
        ≠
relation strength / Charge / salience / utility
```

Пользователь может часто повторять ложное утверждение. Это повышает вероятность необходимости его вспомнить или проверить, но не делает его истинным.

---

## 6. Full Context

EITI показывает полезные свойства bulk context builder:

- labelled sections;
- source caps;
- filtering deleted/empty items;
- failure isolation per source;
- continuity при смене AI provider.

Для Titan Full Context допустим как:

- debug snapshot;
- migration/export;
- emergency fallback;
- evaluation baseline;
- provider-switch continuity.

Стандартный agent-facing путь должен использовать task-specific retrieval, temporal/policy filters, conflicts, provenance и Receipt.

---

## 7. Где это располагается в Titan

```text
Cognitive / Research input
        │
        ▼
core.learning_patch
        │ typed proposal only
        ▼
future Shadow Journal
        │
        ├── MOSC evaluator
        ├── intent-pattern evaluator
        ├── retrieval-policy evaluator
        └── Charge evaluator
        │
        ▼
Operator / Policy Gate
        │
        ├── derived cognitive projections
        └── future Claim admission through TruthGate
```

Не размещать:

- внутри TruthGate как learned multiplier;
- внутри canonical RelationStore без admission;
- в stable `/query` до отдельного decision gate;
- как прямую запись из LLM output;
- как обязательную зависимость Native Kernel или Crystal.

---

## 8. Что уже реализовано в draft

- typed provenance;
- Claim, MOSC, intent, retrieval-policy и Charge proposal types;
- deterministic validation;
- bounded item count and field values;
- regex syntax validation;
- MOSC normalization/deduplication;
- explicit shadow lifecycle;
- focused tests;
- отсутствие `apply()`.

## 9. Что остаётся исследовательским

- автоматический Dialogue Analyzer;
- durable Shadow Journal;
- idempotency and replay;
- tenant erasure closure;
- MOSCIndex;
- live intent router;
- policy A/B evaluator;
- runtime Charge bridge;
- ClaimProposal → TruthGate admission;
- Native Kernel event envelope.

## 10. Правило для людей и ИИ

Наличие типа в коде означает только, что Titan умеет **представить и проверить предложение**. Оно не означает, что Titan автоматически обучается, изменяет retrieval, пишет факты, активирует MOSC/VB или подключён к EITI runtime.
