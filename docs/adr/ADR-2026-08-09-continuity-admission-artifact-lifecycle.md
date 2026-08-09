# ADR-2026-08-09: Durable lifecycle for Continuity admission artifacts

- Status: Proposed for the bounded implementation tracked by issue #266
- Date: 2026-08-09
- Repository baseline: `main@6b7334eba9e00309ff8f54ce4391e251373332b7`
- Scope: Continuity internal evidence lifecycle only
- Runtime status: unwired, not enabled, not observed, no runtime authority

## Context

Continuity already has a deterministic source-admission chain:

```text
principal evidence
+ authorization evidence
+ source binding receipt
+ source envelope
+ observation Drafts
+ six current-decision owner snapshots
+ current-decision evidence
+ pinned evaluator registry and facade policy
→ admission evaluation and receipt
```

The accepted facade result is content-addressed and fail-closed, but the current
implementation intentionally stops before persistence. There is no accepted owner for:

- durable append of the complete admission evidence graph;
- restart-safe deterministic replay;
- bounded retention cleanup;
- erasure-addressability;
- integrity revalidation after storage;
- partial-write or interrupted-cleanup recovery.

That missing lifecycle is the ninth bounded Continuity implementation capability. It
must not be confused with runtime composition or controlled enablement.

## Decision

Add one internal module:

`core/continuity/admission_artifact_lifecycle.py`

The module owns only the storage lifecycle of an already-completed accepted admission
result. It remains intentionally unexported from `core.continuity` and is invoked only
by explicit callers.

### Lifecycle

```text
accepted ContinuityAdmissionFacadeResult
        │
        ▼
complete canonical evidence payload
        │
        ├── SHA-256 integrity digest
        ├── deterministic artifact identity
        └── exact tenant/principal/authorization/subject binding
        │
        ▼
SQLite BEGIN IMMEDIATE + append-only active row
        │
        ├── idempotent duplicate append
        ├── deterministic verified replay
        ├── explicit bounded retention cleanup
        └── injected erasure-owner decision
        │
        ▼
atomic payload removal + addressable tombstone receipt
```

### Complete evidence payload

The artifact retains the full deterministic graph, not a lossy summary:

- principal context;
- authorization context and complete authorization subject set;
- source binding receipt;
- source envelope;
- complete Draft set;
- six current-decision owner snapshots;
- current-decision evidence;
- evaluator registry;
- facade policy;
- facade result, evaluation and admission receipt;
- retention policy;
- schema manifest and lifecycle timestamps.

The active row also stores indexed scope metadata. Every replay reconstructs the
artifact contract, validates canonical JSON, verifies its digest and deterministic ID,
and compares the exact caller scope.

### Retention

Retention is never inferred from a default. An explicit content-addressed
`ContinuityRetentionPolicy` must match the authorization retention class and supplies:

- positive bounded retention duration;
- positive bounded cleanup batch size;
- deterministic policy identity.

Expiry is fail-closed at `replayed_at >= retained_until`. Cleanup selects only rows for
one exact tenant and exact retention-policy ID where `retained_until <= effective_at`.
Ordering is deterministic by `(retained_until, artifact_id)`.

Each cleanup request is itself deterministic and recorded transactionally, including
an empty result, so a retry cannot silently broaden the completed request.

### Erasure authority

The lifecycle store does not decide whether erasure is permitted and does not select a
live adapter. It accepts an injected `ContinuityErasureOwner` protocol and requires one
content-addressed decision bound exactly to:

- owner ID and version;
- artifact ID;
- tenant;
- principal context;
- authorization context;
- complete subject set;
- erasure-domain references;
- current validity interval.

Only an explicit `ALLOW` decision is accepted. `BLOCK`, `UNKNOWN`, stale, malformed,
substituted, owner-failure or owner-identity mutation states fail closed.

### Neutralization receipt

Retention cleanup and erasure atomically remove the active payload and insert a
content-addressed tombstone. The tombstone intentionally omits `payload_json` while
preserving the minimum addressability and evidence required to prove what happened:

- artifact and receipt IDs;
- reason and request/decision ID;
- tenant, principal and authorization IDs;
- complete subject set;
- erasure-domain references;
- policy snapshot ID;
- neutralization time;
- integrity/policy/decision evidence references;
- erasure owner identity when applicable.

The tombstone blocks resurrection under the same artifact identity.

## Atomicity and recovery

All mutations use a dedicated SQLite transaction with `BEGIN IMMEDIATE`.

- Active append and append receipt are committed together.
- Tombstone insertion and active-payload deletion are committed together.
- Cleanup-request completion is committed in the same transaction as all bounded
  neutralizations.
- Any contract failure or SQLite failure rolls back.
- Fault-injection seams prove rollback after an inserted active row and after a
  tombstone insertion before commit.

This slice does not implement the separate high-contention CAS harness tracked by issue
#249.

## Authority matrix

| Concern | Owner after this ADR | Explicitly not owned here |
|---|---|---|
| Authentication identity | Existing principal owner | Lifecycle store |
| Authorization and purpose | Existing authorization owner | Lifecycle store |
| Consent/lawful basis | Existing owner domain | Lifecycle store |
| Restriction state | Existing owner domain | Lifecycle store |
| Erasure eligibility | Injected existing erasure owner | Lifecycle store |
| Policy validity | Existing policy snapshot owner | Lifecycle store |
| Admission evaluation | Existing registry/evaluator/facade | Lifecycle store |
| Durable artifact lifecycle | New internal SQLite owner | Runtime/API/worker |
| Canon/ESM/TruthGate/GoalStack writes | Existing authorities | Lifecycle store |
| Runtime activation | Operator-controlled future work | This slice |

## Failure policy

The implementation has no permissive fallback.

It rejects:

- duplicate IDs with conflicting content;
- malformed or non-canonical JSON;
- corrupted integrity digests;
- unknown lifecycle or evidence schema manifests;
- missing or substituted subjects;
- cross-tenant, cross-principal or cross-authorization reuse;
- stale policy-snapshot scope;
- missing or duplicate owner domains;
- expired replay;
- re-append after neutralization;
- storage exceptions;
- erasure-owner exceptions or non-ALLOW decisions.

## Non-scope

This ADR does not add or change:

- `/query`;
- API, server or startup wiring;
- worker or scheduler wiring;
- live owner adapter selection;
- controlled enablement or user-visible feature flags;
- Operator GO;
- SLOs, alerts or rollback control;
- answers, reminders, notifications, tools or actions;
- Canon/ESM/TruthGate/GoalStack write authority;
- Phase II, ADAO or Research Copilot lifecycle;
- issue #249.

## Evidence required before acceptance

The implementation PR must provide:

1. focused adversarial tests for append, replay, corruption, substitution, retention,
   cleanup, erasure, concurrency and rollback;
2. Ruff and blocking mypy success;
3. full pytest and coverage success on the exact final head;
4. all repository-required workflows and exact aggregate merge evidence;
5. zero unresolved review threads and resolution of confirmed Codex findings;
6. protected squash merge by the verified head SHA;
7. post-merge CI and aggregate evidence.

Only after that merge may a separate status-synchronization PR introduce historical
project-state schema v4, advance Continuity to `9/12 = 75.0%`, and synchronize the
confirmed checkpoint to the existing Notion page `Velantrim Titan 9.0`.

## Consequences

### Positive

- Accepted admission evidence survives restart with deterministic verification.
- Replay cannot cross tenant, principal, authorization, subject or policy scope.
- Cleanup is explicit, bounded, ordered and retry-safe.
- Erasure remains externally authorized while becoming artifact-addressable.
- Partial writes and interrupted neutralization roll back atomically.
- Stored evidence still grants no runtime permission.

### Costs and limits

- SQLite is the bounded internal owner for this slice; no distributed storage claim is
  made.
- Tombstones preserve addressability metadata, not the erased payload.
- No runtime path consumes these artifacts yet.
- No production, observation, SLO or enablement claim follows from this ADR.
