# 🧠 Project Cognition & Code Review

**Status:** `RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Scope:** долговременный проектный контекст для coding agents, GitHub review и инженерных задач

> Этот документ описывает целевой сценарий применения Titan. Он не утверждает,
> что текущий runtime уже выполняет полный repository-wide анализ или заменяет
> Codex, Copilot, IDE, компилятор, тесты либо CI.

## 1. Проблема

Обычный coding assistant чаще всего видит ограниченную рабочую область:

- текущий diff;
- несколько открытых файлов;
- фрагменты, найденные retrieval;
- инструкции репозитория;
- результаты отдельных команд и тестов.

Этого достаточно для локальных изменений, но недостаточно для устойчивого
понимания большого проекта. Между сессиями агент может заново выяснять:

- почему был выбран конкретный архитектурный контракт;
- какие модули зависят от изменяемого API;
- какие ограничения уже были обнаружены ревьюерами;
- какие исправления ранее привели к регрессии;
- какие тесты подтверждают конкретный инвариант;
- какие решения являются действующими, устаревшими или только исследуемыми.

```text
Короткий контекст агента
        +
сложный развивающийся репозиторий
        =
повторная ориентация · пропущенные связи · дорогой review
```

## 2. Роль Titan

Titan проектируется не как ещё один генератор кода, а как **project-cognition
layer** между репозиторием и coding agents.

```text
GitHub repository
├── code
├── tests
├── ADR / specifications
├── issues / pull requests
├── review findings
├── CI outcomes
└── runtime evidence
        │
        ▼
🧠 Titan Project Memory
├── source-linked records
├── epistemic status
├── dependency projections
├── decision history
├── task-local working context
└── provenance / TRACE
        │
        ▼
📦 Project ContextPack
        │
        ▼
🤖 Codex · Copilot · IDE agent · human reviewer
```

Titan не должен постоянно помещать весь проект в prompt. Его задача — хранить
структурную память и собирать ограниченный, релевантный и проверяемый контекст
для конкретной инженерной операции.

## 3. Что должно сохраняться

### 3.1 Архитектурная память

- границы модулей и ответственность компонентов;
- публичные API и внутренние контракты;
- ADR, канонические спецификации и причины решений;
- запрещённые зависимости и authority boundaries;
- feature flags, профили и условия активации;
- известный технический долг и ограничения.

### 3.2 История изменений

- commit / pull request / issue identifiers;
- изменённые файлы и символы;
- мотив изменения;
- review findings и ответы на них;
- CI, тестовые и runtime-результаты;
- откат, supersession или последующая коррекция.

### 3.3 Карта зависимостей

```text
file
→ symbol
→ caller / callee
→ module contract
→ tests
→ ADR / requirement
→ runtime surface
```

Граф, BM25, embeddings и caches могут ускорять поиск, но остаются
**перестраиваемыми проекциями**, а не источником канонической истины.

### 3.4 Незакрытая инженерная работа

- активная цель и ограничения задачи;
- проверяемые гипотезы;
- противоречия между кодом, документацией и тестами;
- заблокированные вопросы;
- критерии завершения;
- результаты уже выполненных попыток.

## 4. Поток анализа Pull Request

```text
🔀 PR / commit / issue
        │
        ▼
📄 diff + changed symbols
        │
        ▼
🧭 Repository Orientation
        │
        ├── component ownership
        ├── callers / callees
        ├── tests and invariants
        ├── ADR / previous decisions
        ├── known defects
        └── active task constraints
        │
        ▼
🔍 Project Memory Retrieval
        │
        ▼
📦 Project ContextPack
        │
        ▼
🤖 Coding agent / reviewer
        │
        ▼
💭 Review hypotheses
        │
        ▼
🧪 static analysis · focused tests · CI · runtime evidence
        │
        ▼
🧾 Finding + provenance + TRACE
```

Review comment должен быть не просто утверждением «здесь ошибка», а
проверяемым выводом:

```yaml
finding: "Изменение сигнатуры оставляет legacy caller несовместимым"
status: "supported"
evidence:
  - "changed symbol: core/example.py::new_contract"
  - "caller: api/example_route.py::handle"
  - "test gap: tests/test_example_route.py"
confidence_scope: "repository evidence only"
recommended_check:
  - "добавить regression test"
  - "проверить второй caller"
limitations:
  - "runtime path не наблюдался"
```

## 5. Project ContextPack

`Project ContextPack` — ограниченный пакет контекста для одной задачи. Он не
является копией всего репозитория и не получает authority над Canon.

Предлагаемый состав:

```text
Project ContextPack
├── TaskFrame
│   ├── goal
│   ├── constraints
│   └── definition of done
├── ChangeSet
│   ├── diff summary
│   ├── changed symbols
│   └── affected surfaces
├── DependencySlice
│   ├── direct callers
│   ├── bounded transitive dependencies
│   └── owning tests
├── DecisionSlice
│   ├── active ADR
│   ├── superseded decisions
│   └── known limitations
├── EvidenceSlice
│   ├── source locations
│   ├── CI / test receipts
│   └── runtime observations
└── Uncertainty
    ├── missing evidence
    ├── stale projections
    └── unresolved contradictions
```

Обязательные свойства:

- строгий budget;
- provenance для существенных утверждений;
- version / commit identity;
- stale-context detection;
- явное разделение факта, гипотезы и интерпретации;
- отсутствие скрытой записи в Canon;
- возможность воспроизвести retrieval и review evidence.

## 6. Взаимодействие с Codex и Copilot

Titan не заменяет coding agent.

| Слой | Ответственность |
|---|---|
| 🤖 Codex / Copilot | анализирует задачу, предлагает код, тесты и review comments |
| 🧠 Titan | предоставляет долговременный project context и историю решений |
| 🕸️ Dependency projection | связывает файлы, символы, тесты и контракты |
| 🧪 Tooling / CI | проверяет компиляцию, lint, типы, тесты и сборку |
| 👤 Operator / maintainer | принимает изменения и определяет authority |

```text
Coding agent proposes.
Titan supplies project memory and evidence.
Tools test the hypothesis.
Maintainer authorizes the change.
```

## 7. Типы обнаруживаемых проблем

Целевой контур может помогать выявлять:

- изменение API без обновления всех callers;
- нарушение архитектурной границы;
- несовместимость со старой схемой данных;
- отсутствие regression test;
- расхождение кода и ADR;
- повторное появление ранее исправленного дефекта;
- использование устаревшего решения;
- скрытый write effect в read-only path;
- обход policy, TruthGate или remote-egress boundary;
- изменение без достаточного evidence или runtime proof.

Это не гарантирует обнаружение всех дефектов. Результат остаётся гипотезой до
проверки тестами, статическим анализом, CI или runtime evidence.

## 8. Связь с существующими компонентами Titan

Предлагаемый сценарий должен переиспользовать существующие границы:

- `GoalFrame` / `GoalStack` — цель и ограничения;
- `WorkingNotebook` — временная рабочая ориентация;
- `KnowledgeCapsule` / `SemanticReader` — source-linked извлечение;
- `AttentionRouter` — bounded selection;
- `FactsPack` / `ContextPack` — ограниченный контекст;
- ESM — статус утверждений;
- provenance / TRACE / AuditChain — доказательный след;
- Recall Policy — контролируемое чтение памяти;
- Write Gate / TruthGate — явная запись и promotion;
- rebuildable graph / lexical / dense projections — ускорение retrieval;
- Working Desk research — task-aware композиция без отдельной authority.

## 9. Границы безопасности и истины

Project Cognition не должен:

- предоставлять coding agent прямую запись в Canon;
- считать review comment доказанным фактом;
- сохранять скрытый chain-of-thought;
- доверять документации больше, чем коду, тестам и runtime evidence;
- превращать граф или embedding index в источник истины;
- автоматически менять архитектурные контракты;
- смешивать task status с epistemic status;
- скрывать отсутствие repository coverage;
- выдавать локальный diff-анализ за полное понимание проекта.

## 10. Текущий честный статус

### Уже существует как основание

- local-first проверяемая память;
- provenance и TRACE;
- ESM и контролируемые write boundaries;
- lexical / hybrid retrieval;
- source-linked knowledge capsules;
- bounded context concepts;
- graph и другие rebuildable projections;
- Working Desk и Rapid Orientation research contracts.

### Ещё требуется для полноценного сценария

- GitHub event ingestion contract;
- repository and symbol indexing;
- versioned dependency projection;
- test-to-symbol ownership map;
- ADR / issue / PR decision linking;
- stale projection and branch divergence handling;
- Project ContextPack schema;
- review finding contract;
- shadow evaluation against diff-only agents;
- measurable precision, recall, latency and cost evidence;
- explicit operator-approved integration with GitHub review APIs.

Поэтому capability имеет статус:

```text
🔬 RESEARCH / PROPOSED
foundation partly available
repository-wide runtime not implemented or validated
```

## 11. Предлагаемый roadmap

### PC-01 — Repository Orientation Contract

- repository identity + commit / branch identity;
- file and symbol inventory;
- deterministic source pointers;
- no Canon writes.

### PC-02 — Dependency Projection

- imports, callers, callees and public surfaces;
- tests linked to symbols and contracts;
- rebuild and stale detection;
- bounded traversal.

### PC-03 — Project Memory Ingestion

- ADR, issues, PRs, review findings and CI receipts;
- deduplication and supersession;
- sensitivity and retention policy;
- provenance for every admitted record.

### PC-04 — Project ContextPack

- task-specific retrieval;
- strict token / evidence budget;
- branch-aware versioning;
- uncertainty and coverage report.

### PC-05 — Shadow Review Intelligence

- no automatic comments;
- compare findings with human, Copilot and Codex review;
- measure false positives and missed defects;
- preserve exact evidence paths.

### PC-06 — Controlled GitHub Integration

Only after shadow validation:

- operator-approved review comments;
- idempotent event processing;
- audit receipts;
- revocation and deletion coverage;
- no merge, write or authority expansion by default.

## 12. Acceptance criteria

- every finding points to repository evidence;
- branch and commit identity are explicit;
- stale context cannot be silently reused;
- missing coverage is reported;
- graph/index loss does not imply knowledge loss;
- no review path writes to Canon;
- no agent comment is treated as validated truth;
- flags OFF preserve current behavior;
- shadow evaluation precedes active review comments;
- measured benefit exceeds the cost of context assembly.

## 13. Навигация

- [🏠 README](../../README.md)
- [🗺️ Living System Atlas](../../SYSTEM_OVERVIEW.md)
- [📊 Project Status](../PROJECT_STATUS.md)
- [🔍 Reviewer Guide](../REVIEWER_README.md)
- [🤖 Agent Rules](../../AGENTS.md)
- [⚡ Adaptive Retrieval & Memory](../research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md)
- [🗂️ Working Desk Research](../../research/WORKING_DESK_RESEARCH_MODE.md)

## Core rule

```text
Titan не должен запоминать весь проект как бесформенный prompt.
Он должен хранить проверяемую структуру проекта и выдавать агенту
ровно тот контекст, который нужен для конкретного изменения.
```
