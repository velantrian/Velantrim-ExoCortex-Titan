# 📍 Current System State

**Verified:** 2026-08-06  
**Current `main` / verified production-code head:** `4adde7997ec0b2a3d1957224c72131d8c4d35ff2`  
**Source-admission architecture:** #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b`  
**Source-admission foundation:** #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237`  
**Source-admission payloads:** #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178`  
**Source-admission decisions/batch:** #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2`

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
Content-addressed ≠ Authenticated
Admission receipt ≠ Current authorization
Authorized batch ≠ Runtime permission
Continuity ≠ Truth
Continuity ≠ Compute authority
Shadow output ≠ User-visible output
```

## Queue status

The historical cleanup/replacement backlog is closed. The primary neutral source-admission contract family is complete.

```text
Historical technical/architecture backlog: 0
Source-admission architecture:              1/1 = 100%
Primary neutral contracts:                  7/7 = 100%
State source adapter:                       0/1 =   0%
Goal subject-binding correction:            0/1 =   0%
OpenLoop subject-binding correction:        0/1 =   0%
Goal/OpenLoop adapters:                     0/2 =   0%
Admission evaluator runtime:                0/1 =   0%
Admission-aware facade:                     0/1 =   0%
Privacy/erasure integration:                0/1 =   0%
Runtime wiring:                             0/1 =   0%
Runtime enabled:                            0/1 =   0%
Live observed evidence:                     0/1 =   0%
```

This documentation sync is not a runtime or authority change.

## Accepted source-admission lineage

| Capability | Accepted change | State |
|---|---|---|
| Architecture and owner map | #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | main, docs-only |
| Principal / authorization / source-binding evidence | #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | main, tested, unwired |
| Source envelope / observation draft | #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | main, tested, unwired |
| Admission receipt / authorized batch | #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | main, tested, unwired |

### Exact-head validation

| PR | Continuity gate | Full Titan CI | Docker hardening |
|---:|---:|---:|---:|
| #225 | `31085072694` ✅ | `31085072968` ✅ | `31085073144` ✅ |
| #226 | `31086056715` ✅ | `31086057276` ✅ | `31086056949` ✅ |
| #227 | `31088287882` ✅ | `31088288821` ✅ | `31088287992` ✅ |

All three implementation PRs passed Ruff, blocking mypy, focused Continuity tests, normal full pytest, the blocking `core ≥74%` coverage ratchet and Docker runtime/secret checks on their exact final heads.

## Seven implemented primary contracts

1. `ContinuityPrincipalContext`
2. `ContinuityAuthorizationContext`
3. `ContinuitySourceBindingReceipt`
4. `ContinuitySourceEnvelope`
5. `ContinuityObservationDraft`
6. `ContinuityObservationAdmissionReceipt`
7. `AuthorizedContinuityObservationBatch`

Helper evidence contracts:

- `ContinuityDraftRejection`;
- `ContinuityDraftObservationLink`;
- `ContinuityAdmissionDisposition`.

These modules remain internal and are not exported through `core.continuity.__init__`.

## Implemented guarantees

### Foundational evidence

- frozen slot-based dataclasses;
- SHA-256 content-addressed identity over canonical JSON;
- UTC-normalized caller-supplied timezone-aware timestamps;
- direct-constructor ID recomputation and tamper rejection;
- Unicode/whitespace normalization;
- collection copying, sorting, duplicate rejection and one-shot iterable support;
- scalar strings/bytes rejected where collections are required;
- no environment, network, database, singleton, wall-clock or mutable-global reads;
- no raw credential serialization.

### Source envelope and Draft

- binding tenant must equal authorization tenant;
- complete source subjects must be a subset of authorized subjects;
- source ID/digest/policy/evidence are copied from immutable binding evidence rather than caller-redeclared;
- envelope creation follows source/binding chronology and lies inside authorization validity;
- Draft signal values follow the existing v1 structural vocabulary;
- Draft confidence is finite, bool-excluded and bounded;
- Draft evidence is mandatory and restricted to envelope evidence;
- Draft remains proposal-only and is not a v1 observation.

### Admission receipt

- every Draft is accounted for exactly once as admitted or rejected;
- admitted/rejected sets are disjoint and complete;
- disposition is derived as `admitted`, `partial` or `rejected`;
- unknown, duplicate and cross-envelope Drafts fail closed;
- envelope, source-binding evidence and authorization context are cross-validated by content as well as IDs;
- source adapter and admission evaluator are separate provenance axes;
- receipt identity requires:
  - source adapter ID/version;
  - admission evaluator ID/version;
  - admission rule ID;
  - nonempty evaluation evidence refs;
- content-addressed ID collections require lowercase SHA-256 shape;
- receipt authority is evidence-only.

### Authorized observation batch

- receipt/envelope/binding/admitted-Draft sets must match exactly;
- rejected Drafts cannot enter observations;
- admitted Drafts are deterministically converted into existing v1 `ContinuitySignalObservation` objects;
- immutable Draft→Observation links preserve traceability;
- two distinct Drafts cannot silently collapse into one v1 observation;
- batch subjects are unioned only from source-binding evidence and remain within authorization scope;
- batch creation/expiry remains inside authorization validity;
- `no_runtime_authority=True` is invariant.

## Explicit limitations

The contracts make evidence immutable and tamper-evident. They do **not** prove that referenced evidence is authentic, approved, current or unrevoked.

Not implemented:

- authentication-receipt verification;
- evaluator/rule registry or allowlist;
- current tenant/subject authorization lookup;
- consent/lawful-basis verification;
- current restriction registry;
- current erasure-domain check;
- current PolicySnapshot compatibility evaluation;
- source freshness policy evaluation;
- State/Goal/OpenLoop source adapters;
- admission-aware facade;
- persistence or replay store;
- public package export;
- `/query`, startup, worker or scheduler wiring;
- feature flag, enablement, SLO, alert or rollback operation;
- answer, reminder, tool, action, Canon, TruthGate, GoalStack or compute-route authority.

A caller can construct a structurally valid receipt only if it supplies all required evidence fields. Structural validity is not approval. A future gate must resolve and allowlist evaluator/rule identities and re-check current policy, authorization, restriction and erasure state.

## Source eligibility

| Source | Current disposition |
|---|---|
| `StateReconciliationResult` | conditionally eligible for a future explicit Draft adapter after complete subject-set validation |
| `GoalProjectionResult` | blocked: `GoalRecordSnapshot.user_id` is not preserved in the projection result |
| `OpenLoopProjectionResult` | blocked: no tenant/user/subject identity is present |

Required State invariant:

```text
subjects(source result) == subjects(source binding receipt)
subjects(source result) ⊆ subjects(authorization)
```

If one State projection belongs to an unauthorized subject, the whole source result is rejected. Silent pre-authorization filtering is forbidden.

`goal_ref` and `related_goal_ref` are not subject-ownership evidence.

## Required future admission-aware facade

The existing pure producer remains a shadow/test API. Bare v1 observations cannot form a live trust boundary.

A future facade must accept only a complete `AuthorizedContinuityObservationBatch` and must:

1. resolve every principal, authorization, binding, admission and evaluator reference;
2. verify evaluator/rule allowlists;
3. re-check current authorization expiry/withdrawal;
4. re-check current consent/lawful basis;
5. re-check current restriction and erasure state;
6. validate tenant and complete subject scope;
7. validate current policy compatibility;
8. validate batch/receipt/envelope/object identities;
9. only then invoke the existing pure signal producer;
10. bind aggregate output to the batch and receipt IDs;
11. remain disabled and produce zero user-visible effect until a separate activation ADR and operator approval.

No such facade exists yet.

## Continuity live readiness

Contract completion does not increase live readiness by itself.

```text
Completed: 3/12 = 25%
Remaining: 9/12 = 75%
```

Completed:

- shadow contracts;
- deterministic replay/tests;
- disabled-by-default authority boundary.

Still required:

- accepted authentication/tenant/subject owner;
- accepted consent/current-restriction owner;
- admission evaluator/allowlist runtime;
- State source adapter;
- subject-binding corrections before Goal/OpenLoop adapters;
- privacy/retention/erasure integration;
- admission-aware facade;
- monitoring, SLOs and anti-bypass guards;
- rollback/disable operations;
- activation ADR and explicit operator approval;
- measured disabled-shadow evidence.

## Existing Continuity shadow stack

| Layer | Accepted SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay gates / Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — disabled runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, default-off, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only, unwired |
| Producer hardening | `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only, unwired |
| Source-admission primary contracts | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | main, tested, internal, unwired |

## Other accepted architecture boundaries

### Cognitive Runtime

Existing owners remain authoritative for truth, policy, compute routing, working memory, context packing, goals, Continuity and RFC-0084 adaptation. No second cognitive executive, route authority, truth root or audit root is accepted.

### LearningProposal / RFC-0084

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

- Identity layer remains `LEGACY/UNWIRED`; governance checklist `1/9 = 11.1%`.
- RFC-0084 remains proposed/unwired; implementation checklist `1/13 = 7.7%`.
- Projection dispatcher remains implemented/tested but unwired; readiness checklist `4/13 = 30.8%`.

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
- trusting evaluator/rule strings without resolution and allowlisting;
- cross-tenant or cross-subject aggregation;
- Goal/OpenLoop admission without immutable subject binding;
- bare v1 observations as a live trust boundary;
- treating an authorized batch as runtime permission.

## Next safe implementation slice

A future Draft PR may implement **StateReconciliationResult → ContinuityObservationDraft** only if it remains explicitly invoked, internal and unwired.

It must:

- enumerate and validate the complete State subject set before any semantic derivation;
- reject the entire result on any unauthorized subject;
- require an externally supplied immutable source-binding receipt;
- generate deterministic Draft proposals only;
- use bounded explicit derivation rules;
- create no admission receipt or batch by itself;
- perform no policy/auth/consent/erasure evaluation;
- call no producer, server, store, worker, scheduler or runtime route;
- create no user-visible effect.

Every adapter, evaluator, facade, persistence, wiring, activation and live-evidence step requires a separate narrowly scoped Draft PR, exact-head CI, final review, merge by expected SHA and GitHub ↔ Notion synchronization.
