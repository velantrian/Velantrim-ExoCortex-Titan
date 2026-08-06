# 📍 Current System State

**Verified:** 2026-08-06  
**Current verified implementation head:** `c7ad5a171ccc6da5015b67b8cefd6d60649d6792`  
**Current docs-only `main`:** `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f`  
**Active architecture replacement:** PR #216, branch `agent/learning-proposal-rfc0084-reconciliation`

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `PROPOSED`, `MAIN`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` are separate states.

## Accepted governance and architecture checkpoints

| Capability | Accepted change | State |
|---|---|---|
| Titan 9 cleanup recovery | #209 → `e6d6002eaf6e771f13d5842db4f083512e0fc0bc` | main, tested |
| Emergency trigger reconstruction tests | #58 → `b9847f0599092ef5eef78d698b58b92ace2eaf98` | main, tests-only evidence |
| Fail-closed production bundle contract | #210 → `5d4881e6ab1414b3917eb225c55e0f02458af27a` | main, tested, local tooling |
| Blocking core coverage ratchet | #211 → `c7ad5a171ccc6da5015b67b8cefd6d60649d6792` | main, enforced in CI |
| Cognitive Runtime reconciliation | #215 → `3bc3607c503c2a32b7ab4f31753b7f9c10ee620f` | main, docs-only, no runtime authority |

Historical PR #33 is closed without merge as superseded by #215.

### Coverage truth

- measured accepted baseline: `43,398` executable statements, `11,233` missed, approximately `74.12%` covered;
- enforced floor: `74%`;
- coverage is a blocking floor, not proof of behavioral correctness.

## Open pull requests

Exactly five PRs are open at this transition checkpoint:

| PR | Purpose | Current disposition |
|---:|---|---|
| #216 | current-main LearningProposal ↔ RFC-0084 reconciliation | Draft docs-only replacement for #43 |
| #214 | trusted typed producer for `ContinuityComputeSignals` | Draft implementation; two independent-review blockers remain |
| #17 | historical Ring Zero recovery concept | `ARCHIVE_AS_RESEARCH_SOURCE`; placement decision required before closure |
| #30 | historical Code Structural Memory RFC | `REVISE_AND_REPLACE`; accept concept as docs-only first |
| #43 | historical LearningPatch / RFC-0083 implementation | `REVISE_AND_REPLACE`; close only after #216 is merged |

Do not bulk-close these PRs and do not merge stale branches wholesale.

## PR #214 — current blocker status

Current head: `a3ccb5bb12df5168fc38fa775e2837de9bb6877a`.

The branch has moved through temporary review-workflow commits, but direct inspection at the current head still shows:

1. `ContinuitySignalObservation._refs()` iterates scalar `str`/`bytes` collections rather than rejecting them as malformed collection inputs;
2. production `signal_producer.py` was not changed to retain trusted negative boolean observations in per-signal provenance.

These findings are recorded in PR comment `5200768686`.

Current exact-head validation is not sufficient to override the contract defects. The PR remains:

```text
DRAFT
NOT MERGED
SHADOW ONLY
UNWIRED
NO RUNTIME AUTHORITY
```

Required before merge:

- fix both production-code defects;
- add direct regression tests that fail against the old behavior;
- run the complete exact-head CI, Continuity and Docker matrix;
- perform another independent diff review;
- verify no temporary self-mutating workflow remains in the final diff.

Even after acceptance, #214 provides only a deterministic aggregator for already-typed observations. It does not provide raw-conversation extraction, user/model attribution, subject/tenant authorization, consent, retention, erasure or runtime activation.

## PR #216 — LearningProposal reconciliation

Historical PR #43/RFC-0083 is being replaced by a current-main docs-only architecture.

Decision:

```text
LearningProposal = what is proposed
RFC-0084 = sole owner of evaluation, stability, approval, apply and rollback
```

The replacement requires:

- immutable content-addressed proposal identity;
- caller-supplied time;
- typed tagged items;
- producer/source/tenant/subject/purpose/policy/base-version binding;
- separate immutable evaluation receipts;
- item-specific evaluation profiles;
- no proposal status transition to approved/applied;
- no persistence, worker, runtime wiring or user-visible effect.

Historical #43 remains open only as a research source until #216 is merged.

## Code Structural Memory decision

Historical PR #30 has disposition `REVISE_AND_REPLACE`.

Accepted concept:

```text
canonical user/world memory
≠ rebuildable repository structural index
```

Required replacement boundaries include deterministic edge identity, repository-scoped keys and queries, pre-staging lease or generation CAS, cross-repository FK protection, no source-body/secret persistence, no automatic scan and no automatic prompt injection.

Implementation must be a separate default-off Draft PR after the docs-only architecture is accepted.

## Recovery authority decision

Historical PR #17 has disposition `ARCHIVE_AS_RESEARCH_SOURCE`.

Titan must not create a new `Ring Zero` root of trust. A future recovery component may only be an operator-gated coordinator that produces dry-run plans and invokes existing authorised services.

Substrate-level event, reduction, projection and receipt integrity belongs to neutral Native Kernel contracts. Current Titan authority remains with PolicyKernel, mutation gates, SAFE_MODE and existing write/version boundaries.

## Continuity Milestone 1

| Layer | Merge SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compatibility-preserving compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay hard gates and Advisory Shadow v2 | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — complete disabled shadow runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, disabled by default, unwired |

R5B has no startup registration, API route, worker, scheduler, persistence, Canon mutation, answer modification, reminder delivery, tool call, action authorization or user-visible output.

## Quarantined and proposed components

- `core/identity_layer.py` remains `LEGACY/UNWIRED`;
- RFC-0084 remains `Proposed`, unwired and without Canon write authority;
- projection dispatcher remains implemented/tested but unwired;
- Ring Zero is not an accepted Titan owner;
- LearningProposal, Code Structural Memory and recovery placement remain architecture-only until their clean replacement decisions are merged.

## Required before live Continuity activation

- trusted authenticated upstream observation producers;
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
- GitHub and Notion require final synchronization after each replacement merge and historical-PR closure.
