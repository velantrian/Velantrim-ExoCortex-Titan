# 🧠 Titan: Epistemic Dynamics + Cognitive Runtime Control

**Статус:** RESEARCH SPEC · DOCS-ONLY · NOT RUNTIME-WIRED · NO DIRECT CANON WRITES · REQUIRES RFC + TESTS BEFORE IMPLEMENTATION

Этот документ фиксирует архитектурный итог обсуждений об абдуктивном мышлении, эпистемической динамике, рабочей памяти, prospective memory и исполнительном управлении Titan.

Он не утверждает, что описанные механизмы уже реализованы в runtime. Документ определяет границы, сущности, инварианты и порядок будущей реализации.

---

## 1. Главная формула

```text
Наблюдать
→ предположить
→ предсказать проверяемые следствия
→ собрать свидетельства
→ пересмотреть гипотезы
→ подтвердить / опровергнуть / оставить неразрешённым
→ сохранить путь познания
```

Ключевой принцип Velantrim сохраняется:

```text
Автономен в работе.
Ограничен в истине.
Ограничен в действии.
Проверяем в памяти.
```

---

# 🔍 Глава A. Epistemic Dynamics

## 2. Абдуктивно-эпистемический цикл

Titan должен уметь работать при неполных и неоднозначных данных.

Пример:

```text
Наблюдения:
- ощущается запах гари;
- небо необычно затемнено;
- источник не виден.

Рабочие гипотезы:
- лесной пожар;
- промышленный пожар;
- промышленный выброс;
- погодное явление;
- вулканический пепел.
```

Система не должна выбирать одну версию как факт. Она должна:

1. выделить наблюдаемое;
2. отделить сообщение источника от состояния мира;
3. построить несколько минимально достаточных гипотез;
4. сформировать проверяемые следствия;
5. искать подтверждающие и опровергающие данные;
6. пересматривать весь набор гипотез;
7. честно сообщать границы знания.

---

## 3. Эпистемические типы

Тип объекта и его состояние не должны смешиваться в один enum.

### 3.1. Типы объектов

```text
OBSERVATION   — непосредственно зафиксированное наблюдение
CLAIM         — утверждение пользователя или другого источника
HYPOTHESIS    — возможное объяснение наблюдаемого
ASSUMPTION    — явно принятое допущение
INFERENCE     — логический или статистический вывод
PREDICTION    — ожидаемое будущее наблюдение или состояние
EVIDENCE      — свидетельство за или против утверждения
FACT          — отдельный проверенный объект знания
MODEL         — более широкая объяснительная структура
```

### 3.2. Состояния обработки

```text
PROPOSED
ACTIVE
INVESTIGATING
SUPPORTED
WEAKENED
RESOLVED
UNRESOLVED
STALE
```

### 3.3. Результаты разрешения гипотезы

```text
CONFIRMED
REFUTED
PARTIALLY_CONFIRMED
INCONCLUSIVE
```

### 3.4. Уровень допуска в durable truth

```text
NOT_ADMITTED
PROVISIONAL
VALIDATED
CANONICAL
RETRACTED
```

`CANONICAL` — не тип гипотезы и не обычный статус рассуждения. Это результат отдельного допуска через TruthGate.

---

## 4. Гипотеза не превращается в факт

Запрещённая модель:

```text
HYPOTHESIS → FACT
```

Правильная модель:

```text
Observation O-1
  ↓ generates
Hypothesis H-1
  ↓ tested_by
Predictions P-1..P-n
  ↓ evaluated_with
Evidence E-1..E-n
  ↓ resolution
H-1 = CONFIRMED / REFUTED / INCONCLUSIVE
  ↓ may_support_creation_of
Fact F-1
```

Гипотеза остаётся историческим объектом. Факт создаётся отдельно и содержит:

```text
derived_from_hypothesis
observation_refs
evidence_refs
truthgate_receipt
admission_policy_version
```

Это позволяет отозвать факт, не переписывая историю рассуждения.

---

## 5. Быстрый и аналитический контуры

### ⚡ Fast path

- выделяет ситуацию и наблюдения;
- извлекает похожие эпизоды;
- создаёт ограниченное число гипотез;
- выбирает временно ведущую версию;
- формирует быстрый ответ с явной неопределённостью.

Пример:

> Вероятно, наблюдается пожар или сильное задымление, но источник пока не подтверждён. Промышленный выброс и погодное явление также остаются возможными версиями.

### 🔬 Deliberative path

- строит план различения гипотез;
- ищет supporting и contradicting evidence;
- проверяет независимость источников;
- обновляет ранги гипотез;
- останавливается по формальному stopping rule;
- передаёт подтверждённый candidate claim в TruthGate.

Быстрый ответ не должен блокироваться глубоким анализом, но не должен скрывать provisional-статус.

---

## 6. Диагностические предсказания

Абдуктивный слой отвечает:

```text
Что могло вызвать наблюдаемое состояние?
```

VPWM отвечает:

```text
Что ещё должно наблюдаться, если гипотеза верна?
Что произойдёт дальше?
Как изменится состояние при действии?
```

Пример:

```text
H1: промышленный пожар.

Ожидаемые следствия:
- сообщения экстренных служб;
- дым со стороны промышленной зоны;
- совпадение направления ветра;
- тепловая аномалия;
- возможное движение пожарной техники.
```

VPWM не определяет истину. Он генерирует проверяемые сценарии и последствия.

---

## 7. Information-gathering actions и Value of Information

Planner должен различать:

```text
TASK_ACTION         — непосредственно изменяет мир ради цели
INFORMATION_ACTION  — уменьшает неопределённость
MIXED_ACTION        — одновременно продвигает цель и собирает данные
RECOVERY_ACTION     — восстанавливает состояние после сбоя
```

Информационное действие может иметь нулевой прямой reward, но высокий epistemic value.

Пример:

```text
Не изменять конфигурацию сразу,
а сначала выполнить ограниченный диагностический probe.
```

Критическое правило:

```text
read-only ≠ автоматически безопасно
```

Read-only действие всё равно проходит:

- policy check;
- privacy check;
- permission check;
- resource/rate-limit check;
- audit logging.

---

## 8. Source Profile без learned reputation

Запрещено использовать обучаемую репутацию источника как автоматический множитель admission:

```text
learned_source_score
→ evidence_weight multiplier
→ TruthGate admission
```

Это создаёт самоподдерживающийся bias.

Допустим описательный профиль:

```text
source_class
domain
claim_type
authentication
freshness
independence_group
known_limitations
review_flags
```

`independence_group` обязателен для защиты от двойного подсчёта одной публикации, перепечатанной несколькими источниками.

TruthGate использует детерминированные правила пригодности evidence, а не непрозрачный динамический авторитет.

---

## 9. Каталог failure modes

Минимальный набор:

```text
CONFIRMATION_SEARCH_BIAS
SINGLE_SOURCE_DEPENDENCY
ANCHOR_LOCK
BASE_RATE_NEGLECT
AVAILABILITY_DOMINANCE
OVERCONFIDENCE
PREMATURE_CLOSURE
HYPOTHESIS_PROLIFERATION
ANALYSIS_LOOP
EVIDENCE_DOUBLE_COUNTING
FEEDBACK_CONTAMINATION
SELF_CONFIRMING_ACTION
```

Каждый failure mode должен иметь:

```text
detection_signal
severity
required_mitigation
audit_event
```

Пример:

```text
EVIDENCE_DOUBLE_COUNTING

Detection:
несколько evidence items имеют одинаковый independence_group.

Mitigation:
свернуть их в один evidence cluster.
```

---

# 🎛️ Глава B. Cognitive Runtime Control

## 10. Executive Control Contract

Новый самостоятельный `Cognitive Executive` не создаётся.

Исполнительные функции уже распределены между:

```text
MetaSupervisor / C7-MC candidate
Scheduler / Orchestrator
Observer
Working Memory Manager
General Planner
Guardian / Ring Zero
```

Нужен единый **Executive Control Contract**, а не новый C-уровень или god-object.

### 10.1. Управляющие решения

```text
ROUTE_FAST
ROUTE_DELIBERATE
CONTINUE
STOP
PAUSE
PREEMPT
CHECKPOINT
COMPACT_WORKING_SET
REQUEST_EVIDENCE
ESCALATE
ACTIVATE_INTENTION
DEFER
```

### 10.2. Границы ответственности

Executive Control не может:

- писать в Canon;
- подтверждать гипотезу как факт;
- обходить Ring Zero;
- увеличивать собственные права;
- изменять policy;
- владеть содержанием фактов и evidence;
- скрыто изменять confidence;
- создавать неограниченную функцию внутренней награды.

### 10.3. Инварианты

```text
ECR-1: No policy bypass.
ECR-2: No truth admission.
ECR-3: Every control decision leaves an audit event.
ECR-4: Resource redistribution stays inside hard budgets.
ECR-5: Meta-control failure falls back to safe bounded mode.
ECR-6: Control state and epistemic content remain separated.
ECR-7: No self-expanding authority.
ECR-8: Control decisions are recoverable and explainable.
```

Safe fallback:

```text
READ_ONLY
BOUNDED
NO_BACKGROUND_EXPANSION
REQUIRE_EXPLICIT_APPROVAL
```

---

## 11. Attention budgets

Для первой версии используются детерминированные квоты:

```text
max_active_hypotheses
max_retrieval_queries
max_external_requests
max_scenario_depth
max_runtime
max_cost
```

Отклонено:

```text
negative attention drift
```

Задача не теряет приоритет только потому, что долго исследуется.

Допустимые механизмы:

- hard quotas;
- aging;
- fairness;
- starvation prevention;
- preemption;
- deadlines;
- checkpointing.

Bounded adaptation допустима только после eval и только внутри неизменяемых hard limits.

---

## 12. Working Set Eviction and Compaction

Термин `forced forgetting` не используется.

При переполнении working set система должна:

1. определить активную значимость;
2. создать смысловой chunk/gist;
3. сохранить ссылки на оригинальные артефакты;
4. выгрузить детали из активного контекста;
5. оставить checkpoint для продолжения задачи.

Инварианты:

```text
WM-1: нельзя удалять единственную ссылку на источник.
WM-2: нельзя смешивать факт и гипотезу.
WM-3: нельзя объединять противоречащие утверждения в один summary.
WM-4: chunk сохраняет provenance refs.
WM-5: незавершённое обязательство требует Intention или checkpoint.
WM-6: восстановление должно возвращать достаточный task state.
```

---

## 13. D15 — Intention Registry

`Intention` — новая сущность Cognitive Runtime, но не VPWM и не Truth Store.

Она хранит незавершённое обязательство, которое должно снова активироваться при наступлении времени или события.

Пример:

```text
После завершения CI
→ повторно оценить PR
→ предложить следующее действие
```

### 13.1. Минимальный контракт

```text
intention_id
description
goal_ref
plan_ref
trigger_condition
activation_mode
priority
status
expires_at
required_freshness
required_permissions
revision
```

### 13.2. Жизненный цикл

```text
PENDING
ARMED
TRIGGERED
ACKNOWLEDGED
EXECUTED
```

Боковые состояния:

```text
MISSED
BLOCKED
CANCELLED
EXPIRED
SUPERSEDED
UNKNOWN_EXECUTION_STATE
```

`EXECUTED_BUT_NOT_RECORDED` не является обычным состоянием Intention. Это возможный вердикт Recovery Worker после проверки внешних следов.

### 13.3. Разделение ролей

```text
Intention Registry
→ хранит обязательство

Trigger Evaluator
→ определяет наступление условия

Executive Control
→ решает, активировать ли его сейчас

Planner
→ строит план

Ring Zero
→ проверяет допустимость

Presence
→ сообщает пользователю или предлагает действие
```

---

## 14. Hard policy и soft optimization

Этика, приватность и безопасность не сводятся к одной числовой функции.

Правильный порядок:

```text
Candidate actions
→ Ring Zero hard policy
→ ALLOW / DENY / REQUIRE_APPROVAL / REQUIRE_MORE_EVIDENCE
→ только затем soft optimization среди допустимых действий
```

Жёсткие запреты не торгуются с reward.

После допуска Planner может оптимизировать:

- стоимость;
- задержку;
- обратимость;
- прозрачность;
- остаточный риск;
- минимальность доступа.

---

## 15. Единый Audit Ledger

Не создаются независимые конкурирующие источники истории для hypotheses, predictions и intentions.

Используется один append-only Titan Audit Ledger с типизированными событиями:

```text
OBSERVATION_RECORDED
CLAIM_RECEIVED
HYPOTHESIS_PROPOSED
HYPOTHESIS_RANK_CHANGED
INVESTIGATION_STARTED
EVIDENCE_REQUESTED
EVIDENCE_ATTACHED
HYPOTHESIS_RESOLVED
PREDICTION_ISSUED
PREDICTION_RESOLVED
INTENTION_CREATED
INTENTION_TRIGGERED
INTENTION_RESOLVED
CONTROL_DECISION_RECORDED
META_FAILURE_DETECTED
FACT_PROPOSED
FACT_ADMITTED
FACT_RETRACTED
```

Поверх него строятся проекции:

```text
Hypothesis View
Prediction View
Intention View
Truth View
Recovery View
Learning View
```

---

# 🔭 Research Annex

Следующие механизмы не входят в P0 runtime:

```text
bounded curiosity
intrinsic epistemic reward
concept extraction
cross-domain analogies
cached / habit strategies
adaptive attention allocation
ensemble / collective reasoning
```

Ограничения:

- curiosity создаёт только exploration proposal;
- аналогия является cross-domain hypothesis, но не evidence;
- успешный эпизод не продвигается автоматически в Canon;
- cached strategy требует fresh context и policy check;
- адаптивные бюджеты не выходят за hard limits;
- ансамбль учитывает коррелированные ошибки, а не простое голосование.

---

# 📌 Архитектурные решения

## D15 — Intention Registry

```text
GO
Новая сущность Cognitive Runtime.
Вне ядра VPWM.
```

## D16 — Executive Control Contract

```text
GO, REVISED
Не новый модуль.
Не новый C-уровень.
Формальный control-plane contract над существующими компонентами.
```

## D17 — структура спецификации

```text
GO
Глава A — Epistemic Dynamics
Глава B — Cognitive Runtime Control
Research Annex
```

---

# 🚫 Уточнённый журнал отклонённых механизмов

```text
❌ learned source reputation как admission multiplier
✅ описательный Source Profile + deterministic evidence rules

❌ числовая этика до policy filtering
✅ hard policy first, soft optimization second

❌ negative attention drift
✅ quotas + fairness + aging + preemption

❌ auto-promotion успешного эпизода в Canon
✅ candidate lesson → validation → ReasoningBank / TruthGate по типу объекта

❌ read-only = automatically safe
✅ read-only проходит privacy, permission, resource и audit checks

❌ Cognitive Executive как новый god-object
✅ Executive Control Contract над существующим control plane
```

---

# 🚦 Рекомендуемый порядок реализации

## P0 — contracts and invariants

1. Эпистемические типы и раздельные статусы.
2. Hypothesis lineage без mutation в Fact.
3. Executive Control Contract.
4. Working Set Eviction and Compaction.
5. Attention hard budgets.
6. Intention Registry.
7. Audit event types.
8. Failure-mode detectors.
9. JSON Schemas и replay tests.

## P1 — controlled reasoning

1. Diagnostic predictions.
2. Information actions и VoI.
3. Evidence plans.
4. Source Profile metadata.
5. Domain-scoped calibration.
6. Recovery integration.

## P2 — experience transfer

1. Concepts and schemas.
2. Cross-domain analogy records.
3. Cached strategy proposals.
4. Context-drift detection.
5. Consolidation policies.

## P3 — research functions

1. Bounded curiosity.
2. Intrinsic epistemic value.
3. Adaptive allocation inside hard bounds.
4. Specialized ensembles.

---

# 🔱 Каноническая формула

```text
Интеллект Titan
≠ максимальное количество рассуждений

Интеллект Titan
= умение выбрать:
  что заметить,
  что предположить,
  что проверить,
  сколько ресурсов потратить,
  когда остановиться,
  что сделать,
  что оставить неразрешённым,
  что сохранить как опыт.
```
