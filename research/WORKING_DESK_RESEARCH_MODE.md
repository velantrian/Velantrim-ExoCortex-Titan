# 🗂️ Working Desk — Research Mode Registry

**Status:** `RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Date:** 2026-07-29  
**Scope:** Titan private research track; not stable runtime, not grant claim

## Decision

Working Desk is preserved as the task-aware operating concept for Titan, but its
full implementation is deferred until the currently approved Synaptic
Exo-Cortex foundations are integrated and evaluated.

This is not a rejection of the idea. It prevents an unfinished composite layer
from creating a second task store, second epistemic state machine, second audit
history, or duplicate attention/context components.

```text
Working Desk vision
→ RESEARCH / PROPOSED

Approved Synaptic foundations
→ ACTIVE ENGINEERING ROADMAP
```

## Why it was not originally planned as a separate layer

The canonical Synaptic plan already decomposes the immediate work into smaller
provider-neutral boundaries:

```text
KnowledgeCapsule
→ SemanticReader
→ LLM Reader Adapter
→ Working Memory Gate
→ ContextPack
→ shadow evaluation
→ active query integration
```

Working Desk appeared later as a useful name for the broader task-operating
composition: persistent task state, focus, completion, archive and operator
escalation. Implementing that composition before the underlying Reader, gate
and ContextPack contracts settle would force premature schemas and duplicate
existing Titan mechanisms.

## Existing Titan components to reuse

Working Desk must compose existing mechanisms rather than replace them:

- `GoalStack` — durable user goals;
- `GoalFrame` — request-level intent and constraints;
- `WorkingNotebook` — session-local working orientation;
- `KnowledgeCapsule` — source-linked extracted meaning;
- `SemanticReader` / `ExtractiveReader` — provider-neutral extraction;
- `AttentionRouter` — deterministic ranking;
- `FactsPack` and planned `ContextPack` — LLM-facing context;
- `promotion_policy` and TruthGate — epistemic promotion;
- Recall Policy — fail-closed memory retrieval;
- `AuditChain` — append-only audit history;
- `ErasureCoordinator` — durable erasure saga;
- remote-egress boundary — mandatory policy lease for remote models.

## Research scope being deferred

The following remain research questions and must not be wired into production
runtime yet:

- Working Desk as a single runtime facade;
- persistent Task Registry and Task Run schema;
- Goal versus Task ownership;
- task-aware Attention View;
- Completion Projection;
- Stagnation Projection;
- Task Archive and archive replay;
- What-If task branches;
- Replay Debugger;
- task-local operator escalation;
- automatic abstraction across completed tasks;
- UI working board;
- adaptive or learned attention weights.

## Work that remains active

The following are not deferred because they are already approved foundations of
the Synaptic Exo-Cortex path:

1. finish and merge the remote-egress / epistemic boundary;
2. implement PR-SYN-03 — LLM Reader Adapter;
3. implement PR-SYN-04 — Working Memory Gate;
4. implement PR-SYN-05 — ContextPack;
5. evaluate existing components in shadow mode;
6. produce a verified gap report before designing Task Registry persistence.

## Invariant versus composite boundary

### Invariant boundary

These mechanisms define safety and truth boundaries. Composite research may
call them but must not bypass or redefine them:

- ESM transition rules;
- TruthGate and canonical admission policy;
- Recall Policy;
- AuditChain append-only semantics;
- ErasureCoordinator completeness semantics;
- remote-egress policy;
- canonical write integrity.

### Composite research boundary

These may be experimented with behind feature flags and shadow evaluation:

- WorkingNotebook composition;
- task projections;
- Attention View;
- ContextPack assembly;
- Completion and Stagnation diagnostics;
- dashboards and operator views.

This distinction is architectural documentation, not a request to reorganize
`core/` directories now.

## Correlation model to research

A single universal `correlation_id` is too broad. The preferred future contract
is:

```text
logical_action_id
→ required for an auditable multi-step logical action

task_id
→ required only when an event is scoped to a task
```

Task identifiers do not themselves implement erasure. Any persistent Task
Registry or archive must add explicit ErasureCoordinator adapters in the same
implementation PR.

## Task-state boundary

Task lifecycle state must remain separate from epistemic state.

Candidate task states:

```text
OPEN
ACTIVE
PAUSED
BLOCKED
COMPLETED
ARCHIVED
CANCELLED
```

Candidate blocking reasons:

```text
NEEDS_OPERATOR
SOURCE_EXHAUSTED
POLICY_DENIED
BUDGET_EXHAUSTED
UNRESOLVED_CONFLICT
DEPENDENCY_PENDING
```

The Working Desk may report that a task-local question is resolved. It may not
assign `Validated`, modify ESM, or treat high confidence as permission to
promote knowledge.

## Progress and budget research

Budget analysis, if implemented, must remain a read-only projection rather
than an autonomous controller.

Preferred task-local metrics:

```text
tokens_spent
tool_calls
new_source_backed_evidence
resolved_questions
resolved_conflicts
criteria_satisfied / criteria_total
evidence_gain_per_1000_tokens
```

The projection may recommend operator attention. It may not change confidence,
weights, ESM, priorities, task state or Canon.

## Stagnation Projection — deferred diagnostic

A future Stagnation Projection may calculate deterministic signals such as:

```text
no_new_evidence_cycles
repeated_action_pattern
question_churn
unresolved_conflict_age
budget_burn_without_progress
source_exhaustion
```

Its only permitted output is a diagnostic report and a proposed operator
question. Any transition to `BLOCKED` remains a separate auditable controller
decision.

## Forbidden effects

Working Desk research must not:

- write directly to Canon;
- assign or remap ESM states;
- auto-promote based on confidence;
- create a second physical audit ledger;
- roll back or delete AuditChain history;
- bypass Recall Policy;
- bypass remote-egress policy;
- retain hidden chain-of-thought;
- learn or adjust attention weights automatically;
- select a hypothesis as true because it completed faster;
- create a persistent archive without erasure coverage.

## Exit criteria from Research Mode

Working Desk may move to `IMPLEMENTATION_CANDIDATE` only after all of the
following are true:

1. remote-egress boundary is merged;
2. PR-SYN-03, PR-SYN-04 and PR-SYN-05 are merged;
3. authoritative ownership of task state is decided;
4. `logical_action_id` and optional `task_id` contracts are defined;
5. task lifecycle is reviewed;
6. recall access is tested through public Recall Policy APIs;
7. erasure design covers every proposed task store and archive;
8. no parallel ESM or physical audit ledger is introduced;
9. at least two end-to-end shadow scenarios show measurable benefit;
10. an Operator GO explicitly authorizes a bounded implementation slice.

## First permitted implementation slice

After the exit criteria are met, the first slice should be shadow-only:

```text
GoalStack
→ one Task Run
→ WorkingNotebook binding
→ KnowledgeCapsule references
→ ContextPack preview
→ operator-visible CompletionReport
```

Explicitly excluded from the first slice:

- active answer control;
- Task Archive;
- Stagnation controller;
- What-If branches;
- replay branches;
- autonomous promotion;
- learned policy changes.

## Responsibility split

### Work suitable for ChatGPT with connected tools

- maintain Notion research pages and cross-links;
- maintain GitHub research/design documents;
- inspect current repository files, PR metadata and architectural mappings;
- prepare ADR drafts, ownership tables, checklists and Claude Code briefs;
- review resulting PRs and CI metadata through the GitHub connector;
- keep research claims synchronized with implemented GitHub reality.

### Work requiring Claude Code or an equivalent local coding agent

- rebase, edit and validate PR #59 locally;
- run complete grep/call-site audits over the checkout;
- implement PR-SYN-03/04/05 runtime code and tests;
- add migrations, CAS semantics and concurrency tests;
- run full pytest, mypy, Ruff and Docker workflows;
- implement Task Registry or erasure adapters after explicit Operator GO;
- perform local diff review, commit, push and resolve inline review findings.

## Return triggers

Revisit this research item when:

- PR #59 is merged;
- PR-SYN-03/04/05 reach `main`;
- a shadow ContextPack exists;
- a real long-running task demonstrates loss of state between sessions;
- a persistent task store is proposed;
- an archive or stagnation mechanism is proposed;
- an Operator asks for the first bounded Working Desk vertical slice.

## Core rule

```text
Research Mode preserves the Working Desk vision.
The Synaptic roadmap builds the prerequisites.
GitHub main remains implementation truth.
Operator GO remains explicit and auditable.
```
