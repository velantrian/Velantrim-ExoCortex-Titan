# 📍 Current System State

**Verified:** 2026-08-06  
**Current `main`:** `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b`  
**Current verified production-code head:** `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523`  
**Latest accepted architecture checkpoint:** #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b`  
**Latest governance checkpoint:** #222 → `73ef1c5e5d7acf6f60be926636cde67e52c66f24`

Material claims must be verified against exact SHAs, tests, workflows, wiring, configuration and runtime evidence.

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Proposal ≠ Evidence
Evidence ≠ Approval
Approval ≠ Activation
Authentication ≠ Subject authorization
Continuity ≠ Truth
Continuity ≠ Compute authority
Shadow output ≠ User-visible output
```

## Queue status

The historical cleanup and architecture-replacement backlog is closed.

```text
Historical technical/architecture backlog: 0
Accepted source-admission architecture:    1/1 = 100%
Source-admission contract implementation:  0/7 =   0%
Source adapters:                            0/3 =   0%
Runtime-wiring PRs:                         0
```

This post-merge documentation sync is not a production-code workstream.

Historical source PRs closed without merge:

| Historical PR | Accepted replacement | Disposition |
|---:|---:|---|
| #33 | #215 → `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f` | superseded; closed |
| #43 | #216 → `c7827d58822d4541e3bf347b2991e7be2d0a8f98` | superseded; closed |
| #30 | #217 → `7fa0ce2346af0a177d519e87df36bf46228123cd` | superseded; closed |
| #17 | #219 → `9ae253bbc96c951b82e21dab4077ad54c9ebc94c` | archived research source; closed |

## Accepted checkpoints

| Capability | Accepted change | State |
|---|---|---|
| Titan 9 cleanup recovery | #209 → `e6d6002eaf6e771f13d5842db4f083512e0fc0bc` | main, tested |
| Emergency trigger reconstruction tests | #58 → `b9847f0599092ef5eef78d698b58b92ace2eaf98` | main, tests-only evidence |
| Fail-closed production bundle | #210 → `5d4881e6ab1414b3917eb225c55e0f02458af27a` | main, tested, local tooling |
| Blocking core coverage ratchet | #211 → `c7ad5a171ccc6da5015b67b8cefd6d60649d6792` | main, CI-enforced |
| Cognitive Runtime owner reconciliation | #215 → `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f` | main, docs-only |
| LearningProposal ↔ RFC-0084 | #216 → `c7827d58822d4541e3bf347b2991e7be2d0a8f98` | main, docs-only |
| Code Structural Memory placement | #217 → `7fa0ce2346af0a177d519e87df36bf46228123cd` | main, docs-only |
| Trace-hook coverage isolation | #218 → `3c73eab991c305d174f6c2c5805595c7998d4068` | main, CI-only |
| Recovery Authority Placement | #219 → `9ae253bbc96c951b82e21dab4077ad54c9ebc94c` | main, docs-only |
| Continuity typed signal producer | #214 → `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only |
| Continuity defensive hardening | #220 → `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only |
| Continuity merged handoff | #221 → `c5b1c8af9df24a45a0adba10f31131be1c69310c` | main, docs-only |
| Zero-backlog governance checkpoint | #222 → `73ef1c5e5d7acf6f60be926636cde67e52c66f24` | main, docs-only |
| Authenticated source-admission architecture | #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | main, docs-only, no runtime authority |

## CI truth

- accepted measured core-coverage baseline remains approximately `74.12%`;
- blocking floor remains `74%`;
- normal full pytest remains blocking;
- SQLite thread-trace stress tests remain blocking in normal pytest and are excluded only from simultaneous `coverage.py` instrumentation;
- coverage is a floor, not proof of behavioral correctness;
- post-merge `main@73ef1c5e...` run `31082437180` passed guards, Ruff, blocking mypy, full pytest and coverage;
- #223 exact-head run `31083553842` passed the same full matrix.

## Continuity shadow stack

| Layer | Accepted SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compatibility-preserving compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay gates and Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — disabled runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, default-off, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only, unwired |
| Producer defensive hardening | `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only, unwired |

Producer guarantees:

- immutable content-addressed typed observations;
- explicit producer/source/confidence/evidence policy;
- deterministic aggregation into unchanged `ContinuityComputeSignals`;
- per-signal provenance and reason-coded rejection;
- conservative warning and availability semantics;
- canonical observation-ID verification;
- controlled malformed categorical-value failure;
- unique-scope contradiction counting with complete trusted provenance.

Producer non-capabilities:

- no raw-conversation extraction;
- no user/model attribution;
- no authenticated principal or tenant directory;
- no subject authorization;
- no consent/purpose owner;
- no retention/erasure integration;
- no persistence;
- no `/query`, startup, worker or scheduler wiring;
- no answer, reminder, tool, action, Canon, TruthGate or policy authority;
- no live calibration, SLO or rollback evidence.

## Accepted Continuity source-admission architecture

PR #223 accepts a trust-boundary design, not implementation.

### Audit findings

1. `StateReconciliationResult` may contain projections for multiple typed `SubjectRef` values. Admission must validate the complete subject set and reject the entire source result if any subject is unauthorized. Silent subset filtering is forbidden.
2. `GoalRecordSnapshot` contains `user_id`, but `GoalProjection` and `GoalProjectionResult` do not preserve it. `goal_ref` is not subject-ownership proof.
3. `OpenLoopSignal`, `OpenLoopProjection` and `OpenLoopProjectionResult` carry no tenant/user/subject identity. `related_goal_ref` is not authorization evidence.
4. `ContinuitySignalObservation` v1 has no principal, tenant, subject, purpose, retention, erasure or PolicySnapshot binding.
5. `ContinuitySignalPolicy` is aggregation policy, not user/tenant authorization.
6. `server.require_api_key` proves possession of one deployment secret, not end-user identity.
7. `PolicyKernel` remains the hard capability/locality/data-mode authority and is not replaced.
8. Durable erasure exists, but no generic accepted consent/restriction registry was found; live admission remains blocked until an owner/receipt contract exists.

### Accepted contracts for future implementation

1. `ContinuityPrincipalContext`
2. `ContinuityAuthorizationContext`
3. `ContinuitySourceBindingReceipt`
4. `ContinuitySourceEnvelope`
5. `ContinuityObservationDraft`
6. `ContinuityObservationAdmissionReceipt`
7. `AuthorizedContinuityObservationBatch`

### Accepted composition rule

```text
bare ContinuitySignalObservation v1
→ valid pure shadow input
→ NOT live-authorized

authorized batch + source-binding receipts + admission receipts
→ eligible only for a future disabled admission-aware experiment
```

A future live-capable path must use an admission-aware facade that:

1. accepts only an `AuthorizedContinuityObservationBatch`;
2. validates batch/envelope/binding/admission identities;
3. re-checks current authorization expiry/withdrawal;
4. re-checks current restriction and erasure state;
5. validates tenant and complete subject scope;
6. validates current policy compatibility;
7. only then invokes the existing pure aggregator;
8. binds aggregate output to batch and receipt IDs.

The existing bare producer remains a pure shadow/test API and cannot be used as a live trust boundary.

### Source eligibility

| Source | Current disposition |
|---|---|
| `StateReconciliationResult` | conditionally eligible after complete-set subject validation |
| `GoalProjectionResult` | blocked until new subject-bound schema or immutable source-owner binding receipt |
| `OpenLoopProjectionResult` | blocked until new subject-bound schema or immutable source-owner binding receipt |

### Architecture progress

```text
Source-boundary audit:               1/1 = 100%
Architecture contract:               1/1 = 100%
Neutral contract implementation:     0/7 =   0%
State adapter:                       0/1 =   0%
Goal subject-binding correction:     0/1 =   0%
OpenLoop subject-binding correction: 0/1 =   0%
Goal/OpenLoop adapters:              0/2 =   0%
Authorization integration:           0/1 =   0%
Privacy/erasure integration:          0/1 =   0%
Admission-aware facade:              0/1 =   0%
Runtime wiring:                      0/1 =   0%
Runtime enabled:                     0/1 =   0%
Live observed evidence:              0/1 =   0%
```

## Continuity live readiness

Architecture acceptance does not increase live readiness.

```text
Completed: 3/12 = 25%
Remaining: 9/12 = 75%
```

Completed:

- shadow contracts;
- deterministic replay/tests;
- disabled-by-default authority boundary.

Still required:

- neutral source-admission contract implementation;
- an accepted authenticated principal/tenant/subject authorization owner;
- consent/purpose and current restriction owner;
- State source adapter;
- subject-binding corrections before Goal/OpenLoop adapters;
- retention/erasure integration;
- monitoring and SLOs;
- rollback/disable operations;
- activation ADR and explicit operator approval;
- live disabled-shadow evidence.

## Other accepted architecture boundaries

### Cognitive Runtime

Existing owners remain authoritative for truth, policy, compute routing, working memory, context packing, goals, Continuity and RFC-0084 adaptation. No second cognitive executive, route authority, truth root or audit root is accepted.

### LearningProposal and RFC-0084

```text
LearningProposal = immutable proposal envelope
RFC-0084 = sole evaluation, stability, approval, apply and rollback lifecycle
```

Proposal implementation, evaluator, persistence, apply service and wiring remain 0%.

### Code Structural Memory

```text
canonical user/world memory
≠ project cognition history
≠ rebuildable repository structural index
```

Schema/contracts, scanner, read APIs and wiring remain 0%.

### Recovery Authority Placement

```text
Titan Ring Zero runtime root = rejected
Native Kernel = neutral event/reduction/projection/receipt integrity
Titan PolicyKernel + mutation gates + SAFE_MODE = current runtime authority
Future Recovery Coordinator = proposal-only and operator-gated
```

Recovery contracts, coordinator, fault-injection corpus and wiring remain 0%.

## Other governed components

### Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`.

```text
Governance checklist: 1/9 = 11.1%
Runtime wiring: 0%
```

### RFC-0084

RFC-0084 remains proposed, unwired, without Canon-write authority.

```text
Implementation checklist: 1/13 = 7.7%
Runtime wiring: 0%
```

### Projection dispatcher

The dispatcher remains implemented/tested but unwired. Runtime ownership, policy gate, metrics, alerts, startup/scheduler, backpressure, retention, parked/dead-letter operations and rollback procedure remain absent.

```text
Implementation/readiness checklist: 4/13 = 30.8%
Runtime wiring: 0%
```

## Global non-authority statement

No accepted checkpoint authorizes:

- direct Canon write or TruthGate bypass;
- `/query` behavior change;
- startup registration, worker or scheduler;
- policy expansion;
- tool/action execution;
- automatic reminders or advice;
- automatic identity or learning admission;
- treating a shared API key as end-user identity;
- cross-tenant or cross-subject aggregation;
- Goal/OpenLoop admission without immutable subject binding;
- bare v1 observations as a live trust boundary.

## Next phase

The next safe implementation slice is **neutral source-admission contracts only**:

- immutable frozen dataclasses;
- content-addressed identity;
- caller-supplied timezone-aware timestamps;
- deterministic canonical serialization;
- validation and unit/property tests;
- no adapters, persistence, server integration, environment/clock/network/global-state access, feature flag or runtime call.

Every implementation, adapter, facade, persistence, wiring, activation and live-evidence step requires a separate narrowly scoped Draft PR, exact-head CI, final review, merge by expected SHA and GitHub ↔ Notion synchronization.
