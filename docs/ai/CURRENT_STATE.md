# 📍 Current System State

**Verified:** 2026-08-06  
**Current verified implementation head:** `c7ad5a171ccc6da5015b67b8cefd6d60649d6792`  
**Current docs-only `main`:** `adfccb02f88b290aac8411e94aac69417defbafe`  
**Cognitive reconciliation candidate:** branch `agent/cognitive-runtime-reconciliation`

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `PROPOSED`, `MAIN`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` are separate states.

## Governance and release hardening completed

| Capability | Accepted change | State |
|---|---|---|
| Titan 9 cleanup recovery | #209 → `e6d6002eaf6e771f13d5842db4f083512e0fc0bc` | main, tested |
| Emergency trigger reconstruction tests | #58 → `b9847f0599092ef5eef78d698b58b92ace2eaf98` | main, tests-only evidence |
| Fail-closed production bundle contract | #210 → `5d4881e6ab1414b3917eb225c55e0f02458af27a` | main, tested, local tooling |
| Blocking core coverage ratchet | #211 → `c7ad5a171ccc6da5015b67b8cefd6d60649d6792` | main, enforced in CI |

### Coverage truth

The repository runs a dedicated blocking full-core coverage job.

- measured accepted baseline: `43,398` executable statements, `11,233` missed, approximately `74.12%` covered;
- enforced floor: `74%`;
- accepted final CI run: `31046470206` — success;
- accepted Docker hardening run: `31046469060` — success;
- coverage XML artifact: `8946843485`;
- normal full pytest remains blocking and includes the per-thread trace-hook stress test;
- that single stress test is excluded only from simultaneous `coverage.py` tracing because the two tracing systems interfere.

## Open pull requests

Exactly five PRs are currently open. Four are intentional architecture/research drafts; one is an active Continuity implementation draft:

| PR | Purpose | Current disposition |
|---:|---|---|
| #214 | Trusted typed producer for `ContinuityComputeSignals` | keep Draft; exact-head CI green but final review found two remaining audit blockers |
| #17 | Ring Zero recovery-kernel research concept | requires placement/trust-boundary decision |
| #30 | Code Structural Memory Adapter RFC | requires architecture approval; implementation must be separate |
| #33 | historical Epistemic and Cognitive Runtime specification | `REVISE_AND_REPLACE`; do not merge stale branch |
| #43 | EITI-derived LearningPatch shadow contract | reconcile with RFC-0084; no parallel governance lifecycle |

Do not bulk-close these PRs and do not merge stale branches wholesale.

### PR #214 exact-head status

Reviewed head: `ea968d1de80b455bb36ce88e1e6a46631640b21f`.

Passing workflows at that head:

- full Titan CI `31052141426`;
- Continuity contracts `31052141682`;
- Docker hardening `31052141462`.

Remaining independent-review blockers, recorded in PR comment `5200768686`:

1. scalar `str`/`bytes` can be misinterpreted as character collections for observation `evidence_refs` / `reason_codes`;
2. trusted negative boolean observations disappear from per-signal provenance, creating an audit mismatch.

Required state: `DRAFT · NOT MERGED · SHADOW ONLY · UNWIRED` until fixes, new exact-head CI and another independent review.

### PR #33 reconciliation

The old 742-line specification predates accepted ownership boundaries. A clean docs-only replacement is being rebuilt from `main@adfccb02...`:

- `docs/research/TITAN_COGNITIVE_RUNTIME_RECONCILIATION.md`;
- old PR disposition: `REVISE_AND_REPLACE`;
- existing owners retained for truth, policy, compute, working memory, goals, Continuity and adaptation;
- no runtime activation, Canon write, worker, scheduler or new root of trust.

## Cleanup disposition

- #10 closed without merge because its generated KB artifact contained confirmed trust-label, graph-coverage and parser defects;
- #20 and #22 closed as already superseded by stronger implementations in `main`;
- #1, #19 and #21 closed only after their useful work was rebuilt and merged through #209, #211 and #210;
- #58 was revalidated on current `main` and merged rather than discarded.

## Continuity Milestone 1

Continuity Milestone 1 remains in `main` through independently reviewed recovery layers:

| Layer | Merge SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compatibility-preserving compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay hard gates and Advisory Shadow v2 | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — complete disabled shadow runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, disabled by default, unwired |

R5B is not a live continuity feature. It has no startup registration, API route, worker, scheduler, persistence, Canon mutation, answer modification, reminder delivery, tool call, action authorization or user-visible output.

PR #214, even after eventual acceptance, would add only a typed deterministic observation aggregator. It does not provide raw-conversation extraction, user/model attribution, subject/tenant authorization, consent, retention, erasure or runtime activation.

## Quarantined and proposed components

- `core/identity_layer.py` is formally `LEGACY/UNWIRED`; mandatory repository guidance prohibits production callers or writes until a candidate/evidence/approval/version/receipt/rollback design is accepted;
- RFC-0084 remains `Proposed`, has no runtime wiring, forbids Canon writes and requires operator approval;
- the projection dispatcher is implemented and tested but remains unwired; current production callers do not exist and startup wiring requires a separate reviewed change;
- Ring Zero remains research and must not be assumed to be an accepted policy owner.

## Required before live Continuity activation

- trusted and authenticated upstream observation producers;
- explicit user statement versus model-inference attribution;
- subject/tenant authorization and purpose-bound consent;
- one accepted policy owner;
- retention, erasure and durable evidence lifecycle;
- bounded input/resource policy and adversarial replay corpus;
- calibration, monitoring, rollback and operational SLOs;
- anti-spam, localization, scheduling and cancellation;
- separate activation ADR and explicit operator approval.

## Other current risks

- production compose profiles remain inconsistent;
- `server.py` remains a broad composition module;
- authentication remains shared API-key rather than per-user/tenant authorization;
- store-wide contention, disk-full and recovery evidence remains incomplete for some surfaces;
- coverage is enforced but remains a floor, not proof of behavioral correctness;
- GitHub and Notion must be synchronized again after the replacement PR receives its final number and head SHA.
