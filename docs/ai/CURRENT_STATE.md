# 📍 Current System State

**Verified:** 2026-08-06  
**Current `main`:** `73ef1c5e5d7acf6f60be926636cde67e52c66f24`  
**Current verified implementation head:** `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523`  
**Architecture decision checkpoint:** `9ae253bbc96c951b82e21dab4077ad54c9ebc94c`  
**Continuity documentation checkpoint:** `c5b1c8af9df24a45a0adba10f31131be1c69310c`  
**Final zero-backlog governance checkpoint:** #222 → `73ef1c5e5d7acf6f60be926636cde67e52c66f24`  
**Active architecture workstream:** PR #223, branch `agent/continuity-source-admission-architecture`

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `PROPOSED`, `MAIN`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` are separate states.

## Queue status

The historical cleanup and replacement-document backlog reached zero through PR #222. One new narrowly scoped architecture PR is now open:

| PR | Purpose | State |
|---:|---|---|
| #223 | authenticated Continuity source admission and authorization boundary | Draft, docs-only, no runtime authority |

```text
Historical technical/architecture backlog: 0
New architecture workstreams:              1
Implementation PRs from #223:              0
Runtime-wiring PRs from #223:               0
```

Historical source PRs closed without merge:

| Historical PR | Accepted replacement | Final disposition |
|---:|---:|---|
| #33 | #215 → `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f` | superseded; closed |
| #43 | #216 → `c7827d58822d4541e3bf347b2991e7be2d0a8f98` | superseded; closed |
| #30 | #217 → `7fa0ce2346af0a177d519e87df36bf46228123cd` | superseded; closed |
| #17 | #219 → `9ae253bbc96c951b82e21dab4077ad54c9ebc94c` | archived research source; closed |

```text
Architecture decisions:       4/4 = 100%
Replacement documents merged: 4/4 = 100%
Historical sources closed:     4/4 = 100%
```

## Accepted engineering checkpoints

| Capability | Accepted change | State |
|---|---|---|
| Titan 9 cleanup recovery | #209 → `e6d6002eaf6e771f13d5842db4f083512e0fc0bc` | main, tested |
| Emergency trigger reconstruction tests | #58 → `b9847f0599092ef5eef78d698b58b92ace2eaf98` | main, tests-only evidence |
| Fail-closed production bundle contract | #210 → `5d4881e6ab1414b3917eb225c55e0f02458af27a` | main, tested, local tooling |
| Blocking core coverage ratchet | #211 → `c7ad5a171ccc6da5015b67b8cefd6d60649d6792` | main, enforced in CI |
| Cognitive Runtime ownership reconciliation | #215 → `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f` | main, docs-only |
| Trace-hook coverage isolation | #218 → `3c73eab991c305d174f6c2c5805595c7998d4068` | main, CI-only; normal pytest unchanged |
| Continuity typed signal producer | #214 → `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only |
| Continuity defensive hardening | #220 → `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only |
| LearningProposal ↔ RFC-0084 reconciliation | #216 → `c7827d58822d4541e3bf347b2991e7be2d0a8f98` | main, docs-only |
| Code Structural Memory reconciliation | #217 → `7fa0ce2346af0a177d519e87df36bf46228123cd` | main, docs-only |
| Recovery Authority Placement | #219 → `9ae253bbc96c951b82e21dab4077ad54c9ebc94c` | main, docs-only |
| Continuity final merged handoff | #221 → `c5b1c8af9df24a45a0adba10f31131be1c69310c` | main, docs-only |
| Final zero-backlog checkpoint | #222 → `73ef1c5e5d7acf6f60be926636cde67e52c66f24` | main, docs-only; post-merge CI green |

## Coverage truth

- accepted measured baseline remains approximately `74.12%`;
- blocking floor remains `74%`;
- normal full pytest remains blocking;
- both SQLite thread-trace concurrency stress families remain in normal full pytest;
- those families are excluded only from simultaneous `coverage.py` instrumentation because Python trace-hook installation collides;
- coverage is a floor, not proof of behavioral correctness;
- post-merge `main@73ef1c5e...` run `31082437180` passed guards, Ruff, blocking mypy, full pytest and the coverage ratchet.

## Continuity current state

### Accepted shadow stack

| Layer | Merge SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compatibility-preserving compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay hard gates and Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — complete disabled runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, default-off, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only, unwired |
| Producer defensive hardening | `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only, unwired |

### Producer guarantees

Implemented and tested:

- immutable content-addressed typed observations;
- explicit trusted producer/source policy;
- deterministic aggregation into the unchanged `ContinuityComputeSignals` contract;
- per-signal provenance and reason-coded rejections;
- warning OR semantics and fail-conservative availability handling;
- strict iterable/reference validation;
- canonical observation-ID recomputation before trust;
- controlled ID/content mismatch rejection;
- controlled categorical-value failure rather than raw lookup exceptions;
- unique-scope contradiction counting while retaining every trusted contributor in provenance.

Not implemented:

- extraction from raw conversations;
- user statement versus model-inference attribution;
- upstream producer authentication;
- subject and tenant authorization;
- consent and purpose binding;
- retention and erasure lifecycle;
- durable persistence/replay;
- startup, worker, scheduler or `/query` wiring;
- answer, reminder, tool, action, Canon, TruthGate or policy authority;
- live calibration, monitoring or rollback evidence.

```text
Shadow implementation contracts: 8/8 = 100%
Runtime wiring:                  0/1 =   0%
Runtime enabled:                 0/1 =   0%
Live observed evidence:          0/1 =   0%
```

### Active source-admission architecture — PR #223

Audit result:

- existing projections contain typed `SubjectRef` or legacy `user_id` context;
- `ContinuitySignalObservation` v1 binds producer/source/evidence but not tenant, subject, principal, purpose, consent, retention, erasure or PolicySnapshot;
- `ContinuitySignalPolicy` trusts producer/source type/confidence/evidence/scope but is not a subject-authorization policy;
- `server.require_api_key` authenticates one shared deployment secret and cannot identify an end user or tenant;
- `PolicyKernel` owns hard capability/locality/data-mode decisions but does not provide a user/tenant authorization directory;
- durable erasure exists, therefore future derived admission artifacts must be erasure-addressable and invalidated by current restriction/erasure state.

PR #223 proposes only:

- authenticated principal context;
- tenant/subject/purpose authorization context;
- immutable source envelope;
- observation drafts;
- immutable admission receipt;
- authorized observation batch;
- deterministic State/Goal/OpenLoop adapter boundaries;
- v1 compatibility through batch-scoped live eligibility.

It adds no implementation, persistence, endpoint, source adapter, runtime call, feature flag, worker, scheduler or authority.

```text
Source-boundary audit:             1/1 = 100%
Architecture document Draft:       1/1 = 100%
Neutral contract implementation:   0/6 =   0%
Source adapters:                   0/3 =   0%
Authorization integration:         0/1 =   0%
Privacy/erasure integration:        0/1 =   0%
Runtime wiring:                    0/1 =   0%
Runtime enabled:                   0/1 =   0%
Live observed evidence:            0/1 =   0%
```

### Live readiness

The typed aggregator does not satisfy the broader “trusted live producer” requirement by itself. PR #223 is architecture-only and does not increase live readiness.

```text
Completed: 3/12 = 25%
Remaining: 9/12 = 75%
```

Completed:

- shadow contracts;
- deterministic replay/tests;
- disabled-by-default authority boundary.

Still required:

- accepted authenticated source-admission architecture;
- neutral admission-contract implementation;
- authenticated upstream source adapters;
- subject/tenant authorization;
- consent and purpose binding;
- retention/erasure lifecycle;
- monitoring and SLOs;
- rollback/disable operations;
- advisory anti-spam, localization and scheduling;
- activation ADR;
- explicit operator approval.

## Accepted architecture decisions

### Cognitive Runtime

Accepted owner map:

- Truth/Canon — existing TruthGate, TruthPolicy, WriteGate and PromotionGateway;
- hard policy — PolicyKernel, PolicySnapshot, CapabilityLease and mutation gates;
- legacy compute route — `ComputeController`;
- executive route vocabulary — D16 proposal-only contract;
- working-memory disposition — `WorkingMemoryGate`;
- final bounded context — `ContextPackBuilder`;
- durable goals — `GoalStack`;
- conversational continuity — Continuity attestations/open loops/projections;
- adaptation — RFC-0084.

No new cognitive executive, second route authority, second audit root or automatic intention authority is accepted.

```text
Architecture: 1/1 = 100%
Implementation from this decision: 0/5 = 0%
Wiring: 0/1 = 0%
Runtime readiness: 0/1 = 0%
```

### LearningProposal and RFC-0084

Accepted rule:

```text
LearningProposal = immutable proposal envelope
RFC-0084 = sole evaluation, stability, approval, apply and rollback lifecycle
```

No proposal implementation, evaluator, persistence, apply service or runtime wiring is accepted by the docs-only decision.

```text
Architecture: 1/1 = 100%
Proposal implementation: 0/5 = 0%
Evaluator implementation: 0/5 = 0%
Wiring: 0/1 = 0%
Runtime readiness: 0/1 = 0%
```

### Code Structural Memory

Accepted rule:

```text
canonical user/world memory
≠ project cognition history
≠ rebuildable repository structural index
```

Accepted architecture includes deterministic repository-scoped identity, same-repository edge constraints, lease-before-staging, monotonic generation/CAS, atomic finalization, bounded parsing and no automatic prompt/Canon authority.

No schema, parser dependency, scanner, read API, worker, endpoint or runtime wiring is implemented by the docs-only decision.

```text
Architecture: 1/1 = 100%
Schema/contracts: 0/5 = 0%
Scanner: 0/8 = 0%
Security/test corpus: 0/8 = 0%
Wiring: 0/1 = 0%
Runtime readiness: 0/1 = 0%
```

### Recovery Authority Placement

Accepted rule:

```text
Titan Ring Zero runtime root = rejected
Native Kernel = neutral event/reduction/projection/receipt integrity
Titan PolicyKernel + mutation gates + SAFE_MODE = current runtime authority
Future Recovery Coordinator = proposal-only and operator-gated
```

Recovery must preserve current erasure/restriction/policy state, prefer deterministic forward reconstruction, separate external compensation and prevent self-approval.

No recovery contracts, coordinator, checkpoint service, fault-injection corpus, automatic rollback or runtime wiring is implemented by the docs-only decision.

```text
Architecture placement: 1/1 = 100%
Neutral contracts: 0/5 = 0%
Dry-run coordinator: 0/5 = 0%
Fault-injection corpus: 0/8 = 0%
Wiring: 0/1 = 0%
Runtime readiness: 0/1 = 0%
```

## Other governed components

### Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`.

```text
Governance checklist: 1/9 = 11.1%
Runtime wiring: 0%
```

### RFC-0084

RFC-0084 remains `Proposed`, unwired, without Canon write authority and requiring operator approval.

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

## Global invariants

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Proposal ≠ Evidence
Evidence ≠ Approval
Approval ≠ Activation
Recurrence ≠ Identity
Authentication ≠ Subject authorization
Continuity ≠ Truth
Continuity ≠ Compute authority
Shadow output ≠ User-visible output
```

No accepted checkpoint or Draft PR authorizes:

- direct Canon write;
- TruthGate bypass;
- `/query` behavior change;
- startup registration;
- background worker or scheduler;
- policy expansion;
- tool/action execution;
- automatic user advice/reminders;
- automatic identity or learning admission;
- treating a shared API key as end-user identity;
- cross-tenant or cross-subject observation aggregation.

## Next phase

The historical PR-cleanup and architecture-replacement phase is complete.

PR #223 is the active current-main docs-only architecture review. It must pass exact-head CI and independent review before any merge decision.

No contract implementation may begin until the admission owner map, v1 compatibility, subject/tenant authorization, current erasure/restriction dominance and staged no-wiring plan are accepted.

Subsequent priority candidates remain:

1. Continuity source-admission neutral contracts — only after #223 acceptance;
2. Identity Pattern Admission neutral contracts;
3. RFC-0084 proposal/evaluator contracts;
4. dispatcher operational ownership;
5. optional Code Structural Memory schema/contracts Draft;
6. recovery contracts only when a concrete approved recovery need exists.

Every future change still requires exact-head CI, final review, merge by expected SHA and GitHub ↔ Notion synchronization.
