# 📍 Current System State

**Verified:** 2026-08-06  
**Current verified implementation head:** `5f1ce06199ebabd6a23f3656ddd91c5c968170fe`  
**Current docs-only `main`:** `c7827d58822d4541e3bf347b2991e7be2d0a8f98`  
**Active architecture replacement:** PR #217, branch `agent/code-structural-memory-reconciliation`

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `PROPOSED`, `MAIN`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` are separate states.

## Accepted checkpoints

| Capability | Accepted change | State |
|---|---|---|
| Titan 9 cleanup recovery | #209 → `e6d6002eaf6e771f13d5842db4f083512e0fc0bc` | main, tested |
| Emergency trigger reconstruction tests | #58 → `b9847f0599092ef5eef78d698b58b92ace2eaf98` | main, tests-only evidence |
| Fail-closed production bundle contract | #210 → `5d4881e6ab1414b3917eb225c55e0f02458af27a` | main, tested, local tooling |
| Blocking core coverage ratchet | #211 → `c7ad5a171ccc6da5015b67b8cefd6d60649d6792` | main, enforced in CI |
| Cognitive Runtime reconciliation | #215 → `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f` | main, docs-only, no runtime authority |
| Trace-hook coverage isolation | #218 → `3c73eab991c305d174f6c2c5805595c7998d4068` | main, CI-only; normal full pytest unchanged |
| Continuity trusted signal producer | #214 → `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only, unwired |
| LearningProposal ↔ RFC-0084 reconciliation | #216 → `c7827d58822d4541e3bf347b2991e7be2d0a8f98` | main, docs-only, no runtime authority |

Historical PRs #33 and #43 are closed without merge as superseded by #215 and #216.

### Coverage truth

- measured accepted baseline: approximately `74.12%` covered;
- enforced floor: `74%`;
- both SQLite trace-hook concurrency stress families remain in the blocking normal pytest job;
- they are excluded only from simultaneous `coverage.py` instrumentation to avoid trace installation races;
- coverage is a blocking floor, not proof of behavioral correctness.

## Open pull requests

Exactly four PRs are open at this transition checkpoint:

| PR | Purpose | Current disposition |
|---:|---|---|
| #217 | current-main Code Structural Memory reconciliation | Draft docs-only replacement for #30 |
| #219 | current-main Recovery Authority Placement | Draft docs-only replacement for #17; merge last |
| #17 | historical Ring Zero recovery concept | `ARCHIVE_AS_RESEARCH_SOURCE`; close only after #219 merge |
| #30 | historical Code Structural Memory RFC | `REVISE_AND_REPLACE`; close only after #217 merge |

Do not merge the historical branches directly.

## Continuity trusted signal producer

PR #214 is merged through `5f1ce06199ebabd6a23f3656ddd91c5c968170fe`.

Exact-head evidence for reviewed head `59d95df099b97ac334a62587cbf8113b27ea3e27`:

- full Titan CI `31076502756` — success;
- Continuity contracts `31076502806` — success;
- Docker hardening `31076502802` — success;
- unresolved review threads — 0.

Implemented:

- immutable content-addressed typed observations;
- explicit trusted producer/source policy;
- deterministic aggregation into unchanged `ContinuityComputeSignals`;
- per-signal provenance and reason-coded rejected observations;
- conservative warning and availability semantics;
- strict iterable/reference validation;
- regression coverage for negative provenance.

Not implemented:

- raw-conversation extraction;
- user/model attribution;
- producer authentication;
- tenant/subject authorization;
- consent/purpose binding;
- retention and erasure;
- persistence or runtime wiring;
- answer, tool, action, Canon, TruthGate or policy authority.

```text
IMPLEMENTED
TESTED
SHADOW-ONLY
UNWIRED
NOT ENABLED
NOT OBSERVED IN LIVE RUNTIME
```

## LearningProposal and RFC-0084

PR #216 is merged through `c7827d58822d4541e3bf347b2991e7be2d0a8f98`; historical #43 is closed.

Accepted decision:

```text
LearningProposal = immutable proposal envelope
RFC-0084 = sole evaluation, stability, approval, apply and rollback lifecycle
```

No proposal implementation, evaluator, apply service, persistence or runtime wiring is accepted by the docs-only decision.

## Code Structural Memory replacement

PR #217 replaces historical #30 with a current-main docs-only architecture.

Accepted concept:

```text
canonical user/world memory
≠ project cognition history
≠ rebuildable repository structural index
```

Required boundaries:

- explicit repository registration and immutable snapshot identity;
- deterministic node and edge IDs;
- non-null normalized qualified names;
- repository-scoped primary/foreign/unique keys and queries;
- same-repository edge endpoints;
- lease-before-staging plus monotonic generation/CAS;
- atomic current-snapshot finalization;
- bounded Python/Tree-sitter first slice;
- no source body, secrets or arbitrary literal persistence;
- no automatic scan, prompt injection, Canon or TruthGate authority;
- separate future default-off implementation PR only after architecture approval.

## Recovery authority placement

PR #219 remains the final docs-only replacement for historical #17.

Titan must not create a new Ring Zero root of trust. A future recovery component may only be an operator-gated coordinator that produces dry-run plans and invokes existing authorised services.

Neutral Native Kernel contracts own substrate event/reduction/projection/receipt integrity. Current Titan authority remains with PolicyKernel, mutation gates, SAFE_MODE and existing write/version services.

## Continuity Milestone 1

| Layer | Merge SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compatibility-preserving compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay hard gates and Advisory Shadow v2 | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — complete disabled shadow runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, disabled by default, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only, unwired |

These components have no startup registration, API route, worker, scheduler, persistence, Canon mutation, answer modification, reminder delivery, tool call, action authorization or user-visible output.

## Quarantined and proposed components

- `core/identity_layer.py` remains `LEGACY/UNWIRED`;
- RFC-0084 remains `Proposed`, unwired and without Canon write authority;
- projection dispatcher remains implemented/tested but unwired;
- Ring Zero is not an accepted Titan owner;
- Code Structural Memory and recovery placement remain architecture-only until their replacement decisions are merged.

## Required before live Continuity activation

- authenticated upstream observation producers;
- explicit user statement versus model-inference attribution;
- subject/tenant authorization and purpose-bound consent;
- accepted policy owner;
- retention, erasure and durable evidence lifecycle;
- adversarial replay corpus and resource bounds;
- calibration, monitoring, rollback and SLOs;
- anti-spam, localization, scheduling and cancellation;
- separate activation ADR and explicit operator approval.

## Other current risks

- production compose profiles remain inconsistent;
- `server.py` remains a broad composition module;
- authentication remains shared API-key rather than per-user/tenant authorization;
- store-wide contention, disk-full and recovery evidence remains incomplete for some surfaces;
- GitHub and Notion require final synchronization after #217/#219 merges and historical-PR closures.
