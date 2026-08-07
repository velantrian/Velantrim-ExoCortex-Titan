# 📍 Current System State

**Verified:** 2026-08-07  
**Actual GitHub `main`:** `659c30e0e8023c48fdf68be8583401fc042a1ab8`  
**Verified implementation change:** PR #232 — OpenLoop subject binding v2  
**Latest documentation checkpoint in progress:** `agent/continuity-pr232-doc-sync`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

Material claims must be verified against exact SHAs, tests, workflows, wiring, configuration and observed runtime evidence.

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Proposal ≠ Evidence
Evidence ≠ Approval
Integrity ≠ Authorization
Receipt provenance ≠ Current permission
Authorized batch ≠ Runtime permission
Continuity ≠ Truth
Continuity ≠ Compute authority
Shadow output ≠ User-visible output
```

## Current queue

```text
Source-admission architecture:           1/1 = 100%
Primary neutral contracts:               7/7 = 100%
State Draft adapter:                     1/1 = 100%
Goal subject-binding correction:         1/1 = 100%
OpenLoop subject-binding correction:     1/1 = 100%
Goal source adapter:                     0/1 =   0%
OpenLoop source adapter:                 0/1 =   0%
Admission evaluator runtime:             0/1 =   0%
Admission-aware facade:                  0/1 =   0%
Privacy/restriction/erasure integration: 0/1 =   0%
Runtime wiring:                          0/1 =   0%
Runtime enabled:                         0/1 =   0%
Live observed evidence:                  0/1 =   0%
```

Continuity live readiness remains:

```text
Completed: 3/12 = 25%
Remaining: 9/12 = 75%
```

State/Goal/OpenLoop prerequisite completion does not add authentication, admission runtime, privacy closure, wiring, enablement or observed operation.

## Accepted source-admission lineage

| Capability | Accepted change | State |
|---|---|---|
| Architecture and owner map | #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | main, docs-only |
| Principal / authorization / source-binding evidence | #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | main, tested, internal, unwired |
| Source envelope / observation draft | #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | main, tested, internal, unwired |
| Admission receipt / authorized batch | #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | main, tested, internal, unwired |
| State reconciliation → Draft adapter | #229 → `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | main, tested, internal, unwired |
| Goal subject-binding schema v2 | #230 → `81836b4f715470c50a4c6c7768a2cde7478568c8` | main, tested, internal, unwired |
| OpenLoop subject-binding schema v2 | #232 → `659c30e0e8023c48fdf68be8583401fc042a1ab8` | main, tested, internal, unwired |

## PR #232 exact-head evidence

```text
Exact tested head:       909789ee99e169f83aa5fab927ed6312e20cf471
Full Titan CI:           31154197511 PASS
Continuity contracts:    31154197538 PASS
Docker hardening:        31154197912 PASS
Unresolved threads:      0
Merge SHA:               659c30e0e8023c48fdf68be8583401fc042a1ab8
```

The earlier Continuity job on `81e07a8ea59f486da9f5cf147ecc2932044fa024` executed no test steps because GitHub's hosted runner did not acquire the job. The later exact-head run above supplies the missing independent contract evidence.

## Implemented primary contracts

The primary neutral source-admission contract family is complete:

1. `ContinuityPrincipalContext`;
2. `ContinuityAuthorizationContext`;
3. `ContinuitySourceBindingReceipt`;
4. `ContinuitySourceEnvelope`;
5. `ContinuityObservationDraft`;
6. `ContinuityObservationAdmissionReceipt`;
7. `AuthorizedContinuityObservationBatch`.

These values remain internal evidence contracts. They are not current authentication, authorization, storage permission, action permission or runtime authority.

## State Draft adapter

PR #229 provides one explicit deterministic adapter:

```text
StateReconciliationResult
→ recompute result/projection identities
→ validate complete subject set
→ validate source-binding receipt
→ create ContinuitySourceEnvelope
→ derive bounded ObservationDraft proposals
→ STOP
```

It does not authenticate, admit, persist, invoke the signal producer, wire runtime behavior or create user-visible effects.

## Goal subject binding v2

PR #230 binds `user_id` through:

```text
GoalRecordSnapshot
→ GoalAttestation
→ GoalProjection
→ GoalProjectionDecision
→ GoalProjectionResult.subject_ids
→ result identity
```

Cross-subject attestations fail closed. No Goal source adapter exists.

## OpenLoop subject binding v2

PR #232 advances the schema to `continuity.open_loop_projection.v2`:

```text
OpenLoopSignal.user_id
→ OpenLoopResolution.user_id
→ OpenLoopProjection.user_id
→ OpenLoopProjectionResult.subject_ids
→ result identity
```

Implemented guarantees:

- subject identity is mandatory for signals and resolutions;
- subject identity enters signal, resolution, projection and result identities;
- result carries the complete sorted subject set;
- cross-subject resolution fails closed with actionable mismatch details;
- direct fixtures were migrated without a placeholder subject;
- a dedicated regression test proves that changing only `user_id` changes `signal_id`, `resolution_id`, `projection_id` and `result_id`.

No OpenLoop source adapter exists.

## Source eligibility

| Source | Current subject binding | Current disposition |
|---|---|---|
| `StateReconciliationResult` | typed subjects plus complete-set adapter validation | Draft adapter implemented/tested; internal and unwired |
| `GoalProjectionResult` v2 | explicit `user_id` and complete content-addressed `subject_ids` | prerequisite complete; Goal adapter absent |
| `OpenLoopProjectionResult` v2 | explicit `user_id` and complete content-addressed `subject_ids` | prerequisite complete; OpenLoop adapter absent |

For every future source adapter:

```text
subjects(source result) == subjects(source binding receipt)
subjects(source result) ⊆ subjects(current authorization)
```

`goal_ref`, `related_goal_ref`, `loop_key` and shared deployment API keys are not subject-ownership or authorization evidence.

## Explicit limitations

Not implemented:

- Goal source adapter;
- OpenLoop source adapter;
- evaluator/rule registry or allowlist;
- current principal, tenant and subject authorization resolution;
- consent or lawful-basis verification;
- current restriction and erasure-domain checks;
- policy compatibility evaluation;
- admission evaluator runtime;
- admission-aware facade;
- durable retention, persistence, replay and cleanup lifecycle for admission artifacts;
- public package export;
- `/query`, startup, worker or scheduler wiring;
- feature flag, operator workflow, SLO, alert or rollback;
- answer, reminder, tool, action, Canon, TruthGate, GoalStack or compute-route authority;
- live observed evidence.

A structurally valid receipt proves represented payload integrity, not current permission.

## Required future admission-aware facade

Bare `ContinuitySignalObservation` values cannot form a live trust boundary. A future facade must accept only a complete `AuthorizedContinuityObservationBatch`, resolve every referenced evidence object, allowlist evaluator/rule identities, re-check current authorization/consent/restriction/erasure/policy state and only then call the existing pure signal producer.

The facade must remain disabled and produce no user-visible effect until a separate activation ADR and operator approval.

## Existing Continuity shadow stack

| Layer | Accepted SHA | State |
|---|---|---|
| R1 immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 process-local read side | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, unwired |
| R3 projections / WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A advisory/replay gates | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B disabled composition | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, default-off, unwired |
| Trusted signal producer | `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only, unwired |
| Source-admission contracts | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | main, tested, internal, unwired |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | main, tested, internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | main, tested, internal, unwired |
| OpenLoop subject binding v2 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | main, tested, internal, unwired |

## Global non-authority statement

No accepted checkpoint authorizes direct Canon write, TruthGate bypass, `/query` behavior changes, startup registration, worker/scheduler execution, policy expansion, automatic reminders, tool/action execution, compute-route ownership, automatic identity inference or treating receipts/batches as permanent runtime permission.

## Next safe implementation slice

The next code PR should implement **one source adapter only**, preferably the Goal source adapter first because Goal subject binding v2 is already accepted and its source semantics are narrower than runtime admission.

It must end at:

```text
IMPLEMENTED · TESTED · INTERNAL · UNWIRED
NO ADMISSION DECISION
NO PERSISTENCE
NO PRODUCER INVOCATION
NO RUNTIME OR USER-VISIBLE AUTHORITY
```

Goal and OpenLoop adapters remain separate PRs. Admission evaluation, privacy/erasure integration, facade, persistence, runtime composition and activation remain later independent stages.
