# Velantrim Exo-Cortex Titan — состояние проекта

> **FOR HUMAN**
>
> Этот документ предназначен для человека. Если вы — AI/agent, используйте соседний файл `FOR_AI.json` как основной компактный контекст и обращайтесь к этому документу только если человеку требуется объяснение формулировок.

**Снимок:** 2026-08-21  
**Репозиторий:** `velantrian/Velantrim-ExoCortex-Titan`  
**Базовый main на момент создания снимка:** `a0292c4d138b1ef76840c7d37ed5aa5cbde178e3`

## 0. Как читать этот документ

Это **обзор состояния**, а не новый Canon и не источник runtime-authority.

Порядок доверия для текущего состояния:

1. Live GitHub state и exact SHA.
2. Код и тесты на exact SHA.
3. Валидируемые project-state contracts, ADR и lifecycle records.
4. Этот обзор.

Если этот документ расходится с live GitHub, **live GitHub имеет приоритет**.

Проценты ниже — инженерная оценка зрелости, а не формальная метрика допуска в production.

---

# 1. Где Titan находится сейчас

Titan находится не на стадии «строим фундамент с нуля», а на стадии **архитектурного укрепления, закрытия остаточных дефектов и подготовки к более цельному продукту**.

Большая часть ключевых архитектурных границ уже определена и защищается тестами и governance-механизмами. При этом система ещё не должна интерпретироваться как полностью завершённый production-продукт или как система с разрешённой автономной властью над Canon.

### Оценка зрелости

| Измерение | Оценка | Что это означает |
|---|---:|---|
| Архитектурное ядро и основные контракты | **~80–85%** | Большинство ключевых границ, lifecycle и governance-механизмов уже построены; остаются отдельные authority-sensitive gaps и integration decisions. |
| Готовность к сильному локальному/ограниченному пилоту | **~70–80%** | База сильная, но перед пилотом нужны закрытые review-gaps, ясные activation boundaries, эксплуатационные проверки и выбранные сценарии использования. |
| Готовность как законченного пользовательского продукта | **~55–65%** | Кроме ядра нужны UX, onboarding, installation/upgrade path, observability, error handling, supportability, release discipline и интеграционные проверки. |
| Готовность для high-assurance / regulated deployment | **ниже продуктовой зрелости** | Потребуются отдельные assurance-процессы, threat models, эксплуатационные доказательства, governance и внешние требования конкретной отрасли. |

**Важно:** проценты не суммируются и не означают «столько строк кода осталось». Titan может быть архитектурно зрелым, но продуктово ещё требовать значительного доведения.

---

# 2. Что уже сделано хорошо

## Архитектурные границы

Titan последовательно сохраняет различия:

- `research != runtime`
- `spec != implementation`
- `implementation != Canon`
- `retrieval != evidence`
- `validation != admission`
- `admission != promotion authorization`
- `receipt != truth`
- `receipt != authority`
- `identity != authority`
- `model output != Canon`
- `CI green != production authorization`
- `merge != runtime activation`

Это одна из наиболее важных частей зрелости проекта: система не должна незаметно получать больше права, чем было явно разрешено.

## Governance и проверяемость

У проекта есть:

- protected/default-branch workflow discipline;
- aggregate merge evidence mechanism;
- CodeQL, Docker hardening, dependency audit, reproducible wheel, deterministic SBOM, coverage ratchet;
- machine-readable `docs/state/project_state.json` с отдельным validator;
- ADR/lifecycle records для критичных slices;
- независимые bounded reviews для authority-sensitive изменений.

## Continuity

Существующий `docs/state/project_state.json` фиксирует Continuity как **12/12 capabilities complete**, при этом одновременно явно сохраняет:

- `runtime_authority = false`;
- `operator_go = false`;
- `enabled = false` для текущего runtime state;
- исторический bounded observation не является текущим production authorization.

Это хороший пример того, почему «компонент завершён» не равно «вся система завершена».

## Evidence Reference

PR #355 уже merged и post-merge closed. Он дал Titan безопасный typed contract для локальной ссылки на evidence и локальной проверки целостности, но не дал права объявлять evidence истинным, независимым или допущенным в Canon.

---

# 3. Что происходит прямо сейчас

## PR #357 — parser hardening

Текущий рабочий поток связан с `EvidenceReference.from_mapping()`.

Исходный review обнаружил, что часть исключений hostile/stateful custom `Mapping` могла выходить наружу вне контролируемой error taxonomy.

В Draft PR #357 был применён bounded fix:

- ordinary `Exception` при snapshot-read нормализуется в `EvidenceReferenceError`;
- `MemoryError` сохраняется как отдельный resource-exhaustion signal;
- `KeyboardInterrupt`, `SystemExit`, `GeneratorExit` не поглощаются;
- добавлен adversarial regression coverage;
- TruthGate, Evidence Admission, runtime и Canon authority не затронуты.

**Текущий review-target после исправления:** `c477500245c8df319fb6c873f8cc510e1f33ec43`.

Следующее действие по этому workstream:

1. дождаться завершения exact-head CI;
2. провести новый independent **REVIEW ONLY**;
3. при результате `APPROVE_FOR_OWNER_MERGE_DECISION` — отдельно принять owner merge decision;
4. после merge заново прочитать exact `main`.

---

# 4. Что осталось сделать

## A. Закрыть текущий bounded hardening

Сначала полностью завершить PR #357. Нельзя использовать green CI как автоматическое разрешение merge.

## B. Legacy TruthGate cardinality — D1

После #357 отдельным approval-gated workstream остаётся старый дефект:

> повторение одного legacy evidence token не должно искусственно увеличивать evidence cardinality.

Например, `['r', 'r', 'r', 'r', 'r']` не должно становиться пятью независимыми единицами поддержки.

Предпочтительное узкое решение D1:

- отдельный legacy normalizer;
- exact-string identity в первой версии;
- совместимость C1 как стартовая рекомендация;
- bounded list/token limits после измерения реальных fixtures/corpus;
- **без** EvidenceReference/EvidenceRegistry wiring.

До начала реализации нужны explicit owner decisions OD-1…OD-4.

## C. Evidence Admission — D2, намного позже

Это отдельная программа, не продолжение D1.

В будущем возможна цепочка:

`LEGACY → OBSERVE → VERIFY → ENFORCE`

Но она требует отдельной архитектуры ownership/policy/receipts и не авторизована текущими PR.

## D. Продуктовая завершённость

Даже после authority-sensitive fixes останется слой продукта:

- понятный installation/onboarding path;
- UX и operator surfaces;
- release/update/rollback workflow;
- эксплуатационная observability;
- failure recovery и supportability;
- производительность на целевых сценариях;
- документация для пользователя и оператора;
- сценарии end-to-end acceptance;
- security/threat review на уровне целевого deployment;
- packaging и deployment ergonomics.

Именно поэтому архитектурная зрелость выше, чем продуктовая.

---

# 5. Что сейчас НЕ надо делать

Не нужно ускорять завершение проекта за счёт скрытого расширения власти.

Пока не должно происходить:

- silent EvidenceReference → TruthGate integration;
- EvidenceValidationReceipt как bearer capability;
- automatic Evidence Admission;
- Canon/ESM mutation из evidence subsystem;
- runtime activation только потому, что CI зелёный;
- смешивание Notion monitor workstream с Evidence/TruthGate;
- превращение этого status-документа во второй Canon.

---

# 6. Практический маршрут к завершённости

```text
PR #357 parser hardening
        ↓
exact-head review
        ↓
owner merge decision
        ↓
re-read main
        ↓
D1 legacy TruthGate duplicate-cardinality fix
        ↓
review + merge
        ↓
architecture/product gap audit
        ↓
bounded pilot-readiness programme
        ↓
product hardening: UX / ops / release / observability
        ↓
limited pilot
        ↓
measured feedback + reliability hardening
        ↓
production-readiness decision
```

D2 Evidence Admission идёт отдельной дорожкой и не должен автоматически блокировать каждый возможный неавторитетный режим продукта.

---

# 7. Человеческий смысл

Проект уже прошёл огромную часть самой сложной работы: он не просто получил функции, а научился **различать способность и право**.

Оставшаяся работа делится на две категории:

1. **Закрыть несколько узких архитектурных/authority-sensitive gaps.**
2. **Превратить сильное инженерное ядро в удобный, наблюдаемый и поддерживаемый продукт.**

Поэтому ощущение, что работа идёт долго, не означает, что Titan «всё ещё в начале». Напротив: значительная часть текущей работы — это стоимость перехода от работающей сложной системы к системе, которой можно доверять.

---

# 8. Связанные источники

Для AI-контекста используйте: `docs/project_status/FOR_AI.json`.

Для существующего валидируемого machine contract используйте: `docs/state/project_state.json`.

Для текущих фактов GitHub всегда выполняйте live verification.
