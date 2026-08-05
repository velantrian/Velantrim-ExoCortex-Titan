# ADR — Continuity R1 Immutable Foundation

- **Status:** Accepted for PR review
- **Date:** 2026-08-05
- **Scope:** immutable continuity contracts and conformance only
- **Base:** `main@bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`
- **Decision owner:** human maintainer / repository architecture policy

## Context

Titan already has authoritative owners for durable memory, epistemic transitions,
compute routing, working-memory disposition, final context assembly and user-facing
responses. Cross-conversation continuity must not create duplicate authority.

The historical PR #131–#147 stack explored a complete shadow pipeline, but it was built
as a long stacked chain against an older `main`. R1 restarts from current `main` and
accepts only the smallest independently testable foundation.

## Decision

R1 introduces three immutable, deterministic data families:

```text
InteractionEvent
  = neutral evidence that an interaction occurred

AssertionRecord
  = a typed assertion with origin, provenance and validity interval

AssertionRelation
  = explicit evidence-linked relation between immutable assertions
```

Supporting references and enums define actor, subject, visibility, sensitivity, origin,
event type and relation type.

R1 owns only canonical contract construction and validation.

## Existing owners remain authoritative

| Decision | Existing owner |
|---|---|
| Canon admission and durable fact mutation | Titan canonical write / promotion path |
| Epistemic state and TruthGate decisions | existing ESM / TruthGate policy |
| Working-memory disposition | existing `WorkingMemoryGate` |
| Final provider-neutral prompt context | existing `ContextPack` |
| Compute depth and route | existing `ComputeController` |
| Advice form | future separately reviewed Advisory boundary |
| External side effects | explicit policy/capability/action boundary |

R1 does not replace, wrap or silently acquire any of these decisions.

## Epistemic separation

The following axes remain independent:

```text
origin
≠ truth / epistemic disposition
≠ current-state projection status
≠ salience
≠ action permission
```

For example, `MODEL_INFERRED` records where an assertion came from. It does not mean the
assertion is true, current, admitted, important or actionable.

## Contract invariants

1. Records are frozen and slot-based.
2. Canonical text uses Unicode NFC.
3. Datetimes are timezone-aware and serialized as UTC with microseconds.
4. Set-like references are sorted and reject duplicates.
5. Assertion values are immutable JSON scalars only; floats must be finite.
6. IDs and payload hashes are SHA-256 over canonical JSON.
7. Changed hashed content changes identity.
8. Missing provenance fails closed.
9. Relations are explicit records; assertions are never rewritten to embed lifecycle.
10. Self-relations fail closed.
11. Contracts expose no write, admission, response, tool or action capability.
12. Golden vectors pin exact canonical bytes and hashes.

## R1 non-scope

R1 adds no:

- database, event ledger or migration;
- conversation-notebook bridge;
- thread linking;
- current-state reconciliation;
- goal or open-loop projection;
- WorkingMemory or ContextPack adapter;
- compute signal;
- advisory candidate;
- background worker or scheduler;
- `/query` or response-path wiring;
- feature activation;
- Canon, TruthGate, ESM, WriteGate or action call.

## Serialization decision

Deterministic serialization is established before any ledger or cross-language adapter.
Golden vectors are executable compatibility evidence. A schema change that alters
canonical bytes requires:

- a new schema version;
- explicit migration/compatibility decision;
- updated golden vectors;
- review of every producer and consumer.

## Privacy boundary

An interaction event stores references, classifications and hashes, not an unrestricted
copy of message content. A future persistence layer must separately define purpose,
retention, subject scope, visibility enforcement, erasure and audit behavior.

R1 contract existence does not authorize collection or retention of personal data.

## Historical stack recovery

The old PRs are implementation source material, not a merge sequence. Recovery order is:

```text
R1 contracts and conformance
→ R2 ledger, conversation bridge and deterministic thread links
→ R3 state, goals/open loops and WorkingMemory adapters
→ R4 compute signals, replay evaluation and Advisory shadow
→ R5 disabled complete shadow runner
```

Every recovery PR must be independently green on current `main`, move fixes to the layer
that owns them and update GitHub/Notion documentation.

## Alternatives rejected

### Merge #131–#147 sequentially

Rejected because the stack is stale, tightly coupled and contains fixes in child PRs that
belong to parent layers.

### Build a second canonical continuity database

Rejected. Neutral evidence and rebuildable projections must not become a parallel truth
system.

### Add a Central Executive

Rejected for R1. Compute routing remains owned by `ComputeController`; advice and action
remain separate decisions.

### Use mutable assertion status fields

Rejected. Correction, contradiction, retraction and supersession are separate immutable
relations followed by rebuildable projections.

## Consequences

Positive:

- a small independently reviewable foundation;
- deterministic replay and cross-language compatibility target;
- explicit provenance and authority separation;
- no runtime or migration rollback burden.

Costs:

- no user-visible continuity yet;
- later layers require adapters and evaluation;
- schema/version discipline is mandatory.

## Rollback

Remove the R1 package, focused workflow and tests. Because R1 has no persistence,
runtime wiring or feature activation, rollback requires no data migration.
