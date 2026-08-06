# 🗺️ Component and Authority Map

**Verified against:** `main@81836b4f715470c50a4c6c7768a2cde7478568c8`  
Use exact SHAs, callers and tests. Presence is not wiring.

## Continuity accepted lineage

| Layer | Merge SHA | Primary surface | Runtime state |
|---|---|---|---|
| R1 contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | `core/continuity/contracts.py` | unwired |
| R2 read-side / threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | `event_port.py`, `conversation_bridge.py`, `thread_weaver.py` | process-local, unwired |
| R3 projections / WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | `context_pack.py`, `state_reconciler.py`, `goal_open_loop.py`, adapters | rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | `core/compute_controller.py` | shadow-only, unwired |
| R5A replay / Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | `evaluation.py`, `advisory_shadow.py` | shadow-only, unwired |
| R5B complete runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | `shadow_runner.py` | disabled by default, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | `observations.py`, `signal_producer.py` | shadow-only, unwired |
| Source-admission foundation | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | `source_admission*.py` | internal, unwired |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | `state_source_adapter.py` | internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | `goal_open_loop.py` | internal contract correction, unwired |

## Source-admission component map

### Architecture and governance

| Responsibility | Primary surface | Notes |
|---|---|---|
| Accepted admission architecture | `docs/research/CONTINUITY_SOURCE_ADMISSION_ARCHITECTURE.md` | architecture and non-authority boundary |
| Canonical current status | `docs/ai/CURRENT_STATE.md` | exact implementation/test/wiring state |
| Risks and required proof | `docs/ai/KNOWN_RISKS.md` | authority, privacy, erasure, concurrency and sync risks |
| Engineering chronology | `docs/ai/WORK_LOG.md` | intent, decision, evidence, non-scope and remaining work |
| Continuity source-admission handoff | `docs/ai/CONTINUITY_SOURCE_ADMISSION_HANDOFF.md` | current workstream continuation map |

### Primary neutral contracts

| Responsibility | Code | Tests | Authority |
|---|---|---|---|
| Principal, authorization and source binding | `core/continuity/source_admission.py` | `tests/test_continuity_source_admission_foundation.py` | immutable evidence only |
| Source envelope and observation draft | `core/continuity/source_admission_payloads.py` | `tests/test_continuity_source_admission_payloads.py` | proposal evidence only |
| Admission receipt and authorized batch | `core/continuity/source_admission_decisions.py` | `tests/test_continuity_source_admission_decisions.py` | admission evidence only; no runtime permission |

All three modules remain internal and are not exported from `core.continuity.__init__`.

### State source adapter

| Responsibility | Surface |
|---|---|
| Typed source owner | `core/continuity/state_reconciler.py` |
| Explicit Draft adapter | `core/continuity/state_source_adapter.py` |
| Focused adversarial tests | `tests/test_continuity_state_source_adapter.py` |

Authority path:

```text
StateReconciliationResult
→ canonical identity verification
→ complete subject-set verification
→ external SourceBindingReceipt verification
→ ContinuitySourceEnvelope
→ bounded ContinuityObservationDraft values
→ STOP
```

The adapter does not evaluate admission, create an authorized batch, invoke the signal producer, persist data, or call a runtime route.

### Goal projection subject binding

| Responsibility | Surface |
|---|---|
| Snapshot, attestation, projection, decision and result contracts | `core/continuity/goal_open_loop.py` |
| Main Goal/OpenLoop tests | `tests/test_continuity_goal_open_loop.py` |
| Schema-lock regression | `tests/test_continuity_goal_subject_binding.py` |
| Direct-constructor compatibility fixtures | `tests/test_continuity_advisory_shadow.py`, `tests/test_continuity_shadow_runner.py`, WorkingMemory adapter tests |

Current Goal contract:

```text
GoalRecordSnapshot.user_id
→ GoalAttestation.user_id
→ GoalProjection.user_id
→ GoalProjectionDecision.user_id
→ GoalProjectionResult.subject_ids
→ result content-addressed identity
```

`continuity.goal_projection.v2` makes subject identity explicit. No Goal source adapter exists yet.

### OpenLoop subject-binding gap

Start with:

- `core/continuity/goal_open_loop.py`;
- relevant canonicalization / serialization helpers in the same module;
- `tests/test_continuity_goal_open_loop.py`;
- advisory and shadow fixtures constructing `OpenLoopProjection` directly;
- WorkingMemory adapter tests consuming OpenLoop projections.

Required owner boundary:

```text
OpenLoop source contract owns subject identity.
A future adapter may verify and transform it.
The adapter must not invent, infer or authorize it.
```

Current status: OpenLoop projection schema v1 has no tenant/user/subject identity. OpenLoop source admission remains blocked.

### WorkingMemory and advisory consumers

| Responsibility | Existing owner | Constraint |
|---|---|---|
| WorkingMemory disposition | existing `WorkingMemoryGate` | no second gate owner |
| Final prompt context | existing `ContextPackBuilder` | projections are derived evidence |
| Advisory candidate selection | R5A Advisory Shadow | shadow-only, no delivery |
| Complete in-memory composition | R5B disabled runner | no startup/runtime registration |
| Compute route | legacy `decide_compute_path()` | unchanged; Continuity is assessment evidence only |

### Privacy, restriction and erasure boundaries

Before any live-capable facade, locate and integrate the accepted owners for:

- current authorization expiry / withdrawal;
- consent or lawful basis;
- current restrictions;
- erasure-domain state and derived-artifact cleanup;
- current policy snapshot compatibility;
- retention and replay lifecycle.

Historical receipts do not override current restriction or erasure state.

## Decision ownership

- truth and Canon: existing canonical memory / TruthGate paths;
- hard capability and data-mode policy: existing `PolicyKernel` / `PolicySnapshot` / `CapabilityLease`;
- source result ownership: State / Goal / OpenLoop projection owners;
- subject binding: the immutable source evidence object or source-owner receipt;
- source adaptation: deterministic proposal transformation only;
- admission evaluation: no accepted runtime owner exists yet;
- WorkingMemory disposition: existing `WorkingMemoryGate`;
- final prompt context: existing `ContextPackBuilder`;
- legacy compute routing: `decide_compute_path()`;
- Continuity compute evidence: R4 assessment only;
- replay evidence: R5A evaluation;
- runtime activation: no accepted owner exists.

## Audit checklist for the next OpenLoop slice

1. Is subject identity mandatory rather than defaulted?
2. Does subject identity enter canonical payload and content-addressed IDs?
3. Is the schema version advanced explicitly?
4. Do projection, decision and result identities preserve the complete subject set?
5. Are cross-subject and ambiguous records rejected fail-closed?
6. Are all direct constructors and fixtures updated rather than weakening the production model?
7. Are serializers, equality/determinism tests and order-independence tests updated?
8. Is no source adapter included?
9. Is no admission evaluator, batch, producer call, persistence or public export included?
10. Are server, startup, worker, scheduler, feature flag and user-visible effects absent?
11. Does final documentation distinguish `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED`?

## Historical status

The old stacked PR sequence #131–#147 is superseded by current-main recovery PRs #201–#206. Historical branches are not accepted integration targets.

Projection delivery remains implemented/tested but unwired. Identity remains legacy/unwired. API/deployment review starts with `server.py`, API auth, egress, Docker/compose and dependency locks.
