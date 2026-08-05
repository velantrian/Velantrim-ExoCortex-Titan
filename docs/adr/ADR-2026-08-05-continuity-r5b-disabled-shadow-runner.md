# ADR-2026-08-05: Disabled complete Continuity shadow runner

- **Status:** ACCEPTED FOR SHADOW-ONLY RECOVERY
- **Scope:** Continuity R5B in-memory orchestration
- **Date:** 2026-08-05
- **Runtime activation:** forbidden by this ADR

## Context

R1–R5A now exist independently on current `main`, but no accepted component
composes the full path in one deterministic evaluation. Historical PR #147 did
so against stale R4/R5 APIs. In particular, it called a historical
`decide_compute_path(..., continuity=...)` signature that current R4 explicitly
rejected to preserve compatibility.

## Decision

R5B adds one `CompleteShadowRunner` that is disabled by default and has no
runtime registration. When an explicit caller creates `ShadowRunnerConfig` with
`enabled=True` and supplies fully typed inputs, it performs two in-memory
passes:

```text
ConversationEpisode
→ ThreadWeaver
→ ContinuityContextAssembler
→ state / goal / open-loop projections
→ Continuity + projection WorkingMemory adapters
→ existing WorkingMemoryGate
→ existing ContextPackBuilder
→ R4 assess_compute_with_continuity()
→ R5A ShadowRunSnapshot
→ reversed-order replay
→ ReplayEvaluationReport
→ R5A AdvisoryShadowGate
→ immutable result + receipt
```

The runner records the final R4 assessment decision in the R5A snapshot. It
does not execute that decision.

## Disabled boundary

The default call returns before validating or executing pipeline input. Its
receipt includes:

- `FEATURE_DISABLED`;
- `MAIN_ANSWER_UNTOUCHED`;
- `CANON_UNCHANGED`;
- `ADVISORY_SHADOW_ONLY`;
- `NO_RUNTIME_AUTHORITY`.

`enabled=True` is a local evaluation permission on an explicitly constructed
object. It is not a feature flag, startup hook, service registration or live
runtime configuration.

## Input boundary

R5B accepts only typed records. It does not create them from raw conversation
text. `AdvisoryIntent` performs exact semantic-reference resolution after
projections exist; it does not infer relevance. A target must resolve to exactly
one projection or the run fails closed.

Gate policy fields are caller-supplied facts. R5B copies them into typed adapter
policies but does not become their policy owner.

## Authority boundary

R5B adds no:

- startup registration, server route, worker, scheduler or daemon;
- persistence, database schema or durable queue;
- raw-text extraction or psychological inference;
- retrieval, Canon, ESM, TruthGate or policy mutation;
- answer generation or answer-path modification;
- reminder delivery, notification scheduling or tool calls;
- action authorization or user-visible output;
- network interface or provider call.

The result may contain Advisory shadow text, but no method can display, send or
apply it.

## Replay rule

Baseline and replay execute independently with reversed external input order.
Equal semantic input must produce equal snapshots. Replay divergence or any R5A
hard-gate violation prevents a reminder-shaped candidate and yields a text-free
Advisory `DEFER`.

## Rejected alternatives

### Copy historical #147 unchanged

Rejected because it depends on a removed compute signature and historical
Advisory contracts.

### Register the runner in `/query` or startup

Rejected. Producer trust, consent, tenant authorization, retention, erasure,
monitoring, rollback, anti-spam and operator approval remain unresolved.

### Let the runner infer Advisory relevance

Rejected. Relevance remains an explicit typed input resolved exactly to a
projection.

## Validation

Required before merge:

- disabled short-circuit before component execution;
- full current R1–R5A pipeline execution;
- reversed-order replay equality;
- R4 VERIFY escalation represented but not executed;
- R5A hard-gate defer and shared-audience silence;
- exact Advisory target resolution;
- deterministic receipt/result identity;
- immutable outputs and absence of runtime interfaces;
- focused Continuity, full Titan CI and Docker hardening;
- independent final-head review;
- GitHub and Notion synchronization.

## Consequences

After R5B, Milestone 1 continuity exists as a tested, complete, disabled shadow
composition. This does not authorize live continuity. The next phase is not
more recovery: it is trusted producer, privacy, policy, operational and runtime
governance design under separate approval.
