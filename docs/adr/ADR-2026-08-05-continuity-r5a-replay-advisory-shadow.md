# ADR-2026-08-05: Continuity R5A replay gates and Advisory Shadow

- **Status:** ACCEPTED FOR SHADOW-ONLY RECOVERY
- **Scope:** deterministic replay evidence and low-risk advisory proposals
- **Date:** 2026-08-05
- **Runtime activation:** forbidden by this ADR

## Context

Continuity R1–R4 provide immutable evidence contracts, a process-local read-side,
rebuildable projections, WorkingMemory adapters and a compatibility-preserving
compute assessment. None of those layers proves that a repeated run is stable,
that privacy/provenance/budget boundaries were preserved, or that a proposed
reminder is allowed for the current audience.

Historical PRs #145 and #146 attempted to add replay evaluation and an Advisory
Shadow. The architecture was useful, but the #146 GitHub workflow failed on a
mypy assignment error and the old stack depended on historical branch state.
R5A rebuilds these concerns independently on current `main`.

## Decision

R5A adds two strictly ordered layers:

```text
already-built shadow artifacts
  → ShadowRunSnapshot
  → ReplayEvaluationReport
  → zero-tolerance hard gates
  → explicit private-audience AdvisorySignal
  → AdvisoryShadowGate
  → shadow-only candidate + receipt
```

No Advisory candidate may be evaluated before a typed
`ReplayEvaluationReport`. A failing report always yields a shadow `DEFER`
candidate with no proposed text.

## Replay hard gates

The following counters are zero-tolerance:

- privacy leakage;
- inference represented as fact;
- missing provenance;
- budget overflow;
- query-time Canon write;
- replay divergence;
- silent overwrite.

Snapshots record content identities, not mutable runtime objects. Evaluation is
read-only and produces deterministic hashes and structured counters.

R4 integration is explicit: callers may snapshot the final
`ContinuityComputeAssessment.decision`. R5A does not wire or execute that
decision.

## Advisory admission

An Advisory candidate requires all of:

1. a passed replay report;
2. `PRIVATE` audience;
3. an explicit typed `AdvisorySignal`;
4. an exact matching current-state, goal or open-loop projection;
5. an active/actionable projection status;
6. caller permission for reminders or confirmation questions;
7. source-linked basis references;
8. `shadow_only=True`.

The gate never receives raw request text and cannot infer relevance itself.

## Allowed v2 candidate actions

- `ASK_CONFIRMATION` for an explicitly signalled contested priority/state;
- `REMIND` for an explicitly signalled active attested goal;
- `REMIND` for an explicitly signalled open/overdue typed open loop;
- `DEFER` when replay hard gates fail;
- `SILENCE` when audience, permission, target or actionability rules fail.

`AdvisoryAction.DEFER` is a shadow candidate disposition. It is **not** a
`ComputePath`, does not allocate or cancel work, and does not reintroduce the
rejected historical `DEFER_PATH`.

## Deterministic priority

When several explicit signals are present:

```text
priority change
→ blocker
→ open loop
→ goal
```

Input ordering does not change the selected candidate or receipt.

## Authority boundary

R5A adds no:

- runtime/startup/worker/query integration;
- raw-text motive, psychology, goal, open-loop or relevance inference;
- reminder delivery or notification scheduling;
- answer modification or user-visible output;
- persistence or durable advisory queue;
- Canon, ESM, TruthGate, memory or policy mutation;
- tool calls or action authorization;
- automatic feature activation.

The Russian `proposed_text` field is an inspectable shadow proposal only.

## Rejected alternatives

### Recover historical #146 unchanged

Rejected. Its final GitHub workflow failed mypy and skipped tests. R5A uses a
smaller v2 contract and removes unused action/assumption surface.

### Produce reminders directly

Rejected. Delivery requires a separate runtime owner, consent policy,
anti-spam limits, localization, scheduling, cancellation and operator approval.

### Infer relevance from raw conversation text

Rejected. R5A consumes typed relevance signals only.

### Treat advisory DEFER as compute DEFER

Rejected. Advisory and compute ownership remain separate.

## Validation

Required before merge:

- replay equality/divergence and every hard gate;
- R4 final-decision snapshot compatibility;
- private/shared audience behavior;
- explicit-signal and exact-target requirements;
- status/permission filtering;
- deterministic priority and input-order invariance;
- mypy regression for candidate selection;
- no runtime/authority fields;
- focused Continuity, full Titan CI and Docker hardening;
- independent final-head review;
- GitHub and Notion synchronization.

## Consequences

R5A can evaluate and inspect low-risk proposals, but it cannot show, send or act
on them. The complete disabled orchestration runner remains a separate R5B
review. Any live advisory path requires a new ADR and explicit operator approval.
