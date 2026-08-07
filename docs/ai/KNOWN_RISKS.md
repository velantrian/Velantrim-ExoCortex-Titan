# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-07  
**Current verified implementation head:** `659c30e0e8023c48fdf68be8583401fc042a1ab8`

Code presence and tests do not establish wiring, enablement, authority or production safety. Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.

## Closed or materially reduced in the current Continuity cycle

- seven primary source-admission contracts are implemented, tested, internal and unwired;
- State reconciliation has a deterministic Draft adapter with complete-subject validation;
- Goal projection schema v2 preserves subject identity through attestation, projection, decision and result identity;
- OpenLoop projection schema v2 preserves subject identity through signal, resolution, projection and result identity;
- cross-subject Goal attestations and OpenLoop resolutions fail closed;
- a direct OpenLoop hash-regression test proves `user_id` changes every content-addressed identity in the chain;
- these slices add no runtime, Canon, TruthGate, action, reminder or compute-route authority.

The former P0 OpenLoop subject-identity gap is closed. Authorization, privacy, admission, runtime and operational risks remain open.

## P0 — Runtime authority boundary remains absent

- Goal and OpenLoop source adapters do not exist;
- admission evaluator runtime does not exist;
- admission-aware facade does not exist;
- current authorization, consent/lawful-basis, restriction, policy and erasure checks are not connected;
- source-admission artifacts are not wired into `/query`, startup, workers or schedulers;
- no feature flag, operator approval workflow, SLO, alert, rollback or kill-switch evidence exists;
- no live evidence demonstrates safe or useful behavior.

```text
IMPLEMENTED + TESTED
≠ WIRED
≠ ENABLED
≠ OBSERVED
```

## P0 — Repository governance is not enforced

`main` remains unprotected and repository rulesets are absent.

Consequences:

- GitHub does not require PR review or resolved conversations;
- failed, cancelled, missing or stale checks do not technically block merge;
- direct push and force-push restrictions are not enforced by repository settings;
- documentation synchronization remains a process rule rather than a merge gate.

Required control:

- require pull requests and at least one approval;
- dismiss stale approvals;
- require conversation resolution;
- require an always-present aggregate merge gate;
- require branch up to date;
- block force pushes and deletion;
- restrict direct pushes;
- add CODEOWNERS for Canon, policy, Continuity, migrations, workflows and security/deployment surfaces.

## P1 — Evidence is not current authority

Content-addressed IDs and immutable receipts prove represented payload integrity. They do not prove current permission.

Residual risks:

- authentication evidence may be forged, expired, revoked or unresolved;
- evaluator/rule identifiers are untrusted until resolved and allowlisted;
- authorization may expire or be withdrawn after receipt creation;
- consent or lawful basis may no longer apply;
- policy may be incompatible with historical evidence;
- a subject may be restricted or erased after an artifact was issued;
- source evidence may be stale despite structural validity.

```text
Integrity ≠ Authorization
Admission receipt ≠ Permanent permission
Authorized batch ≠ Runtime permission
```

## P1 — Bare observations are not live-authorized

`ContinuitySignalObservation` remains valid only for deterministic shadow aggregation. It does not carry the complete current tenant, principal, purpose, consent, restriction, retention or erasure decision needed for live use.

Required proof:

- only an admission-aware facade may accept live-capable input;
- the facade accepts a complete `AuthorizedContinuityObservationBatch`, never bare observations;
- static/runtime guards prevent bypass from API, startup, worker, scheduler and advisory paths;
- current authorization, restriction, policy and erasure state are re-checked before producer invocation.

## P1 — Privacy, restriction, retention and erasure

- current consent/lawful-basis evaluation is absent;
- current restriction and erasure-domain integration is absent;
- admission artifacts have no accepted durable retention/replay/cleanup lifecycle;
- derived State/Goal/OpenLoop artifacts are not proven erasure-addressable end to end;
- no proof covers deletion during queued, persisted, replayed or partially evaluated admission work;
- multi-subject erasure and reappearance handling are not proven for future Continuity stores.

Historical permission must never override current deletion or restriction state.

## P1 — Source adapter limitations

### State

The State Draft adapter is internal and unwired. It validates structural identity and complete subject binding, but does not authenticate the source owner, decide admission, persist artifacts or establish current authorization.

### Goal

Goal subject binding v2 is complete, but:

- no Goal source adapter exists;
- `user_id` remains a legacy string vocabulary rather than an accepted end-user identity provider;
- subject binding does not establish tenant, principal, purpose, consent or current permission;
- future adapters must validate the complete subject set and must not infer ownership from `goal_ref`.

### OpenLoop

OpenLoop subject binding v2 is complete, but:

- no OpenLoop source adapter exists;
- subject binding does not establish tenant, principal, purpose, consent or current permission;
- future adapters must validate the complete subject set and must not infer ownership from `loop_key` or `related_goal_ref`;
- schema v2 compatibility must be preserved in future serializers, adapters and replay fixtures.

## P1 — Concurrency and flaky evidence

An existing erasure recovery test has shown an intermittent race during coverage instrumentation. A later unchanged exact head passed on retry, but the first failure remains risk evidence.

Required action:

- preserve blocking tests where instrumentation permits;
- record first failure, unchanged-head retry and final result;
- investigate recurrence rather than normalizing repeated retries;
- prefer deterministic synchronization and fault injection over timing-based assertions.

## P1 — GitHub ↔ Notion drift

PR #229/#230 and the initial state of PR #232 demonstrated that code, GitHub AI context and Notion can temporarily disagree.

Risks:

- agents repeat completed work;
- reviewers use superseded eligibility matrices;
- current SHA and readiness counters become inaccurate;
- historical Draft blocks appear to be current truth.

Required control:

- one current snapshot at the top of GitHub and Notion records;
- same-cycle synchronization for `GITHUB_AND_NOTION` changes;
- explicit structured handoff only when Notion is unavailable;
- post-merge checkpoint with final merge SHA and CI;
- no new implementation slice while canonical status is materially stale.

## P1 — Existing Continuity shadow stack

R1–R5B and the signal producer are tested shadow components, not a live cognitive runtime.

Residual risks:

- typed records may be semantically wrong despite valid hashes;
- trusted source adapters and current authorization are absent;
- replay equality proves determinism, not usefulness or correctness;
- process-local outputs have no durable retention/erasure lifecycle;
- `ThreadWeaver` may remain expensive for large batches;
- careless future wiring could convert advisory evidence into unintended authority.

## P1 — Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`. A shared deployment API key is not end-user, tenant or subject authorization. Do not create a parallel identity-admission path without an accepted owner, lifecycle, receipts, rollback and erasure model.

## P1 — Projections and adaptive memory

- projection dispatcher is implemented/tested but lacks startup lifecycle, backlog monitoring and observed operation;
- GRAPH/VECTOR projection targets and executable REMOVE semantics are not active;
- ARM-03 remains heuristic, proposal-only, default-off and unwired;
- ARM-04 admission and ARM-05 parallel context assembly remain absent;
- persistent embedding projection is not the canonical live dense read path.

## P1 — Coverage and supply-chain posture

- the `core ≥74%` floor is a regression ratchet, not a security or correctness proof;
- aggregate coverage can hide critical low-coverage modules;
- concurrency instrumentation requires explicit treatment;
- dependency constraints remain broad and no complete lock/reproducibility policy is established;
- GitHub Actions use major-version tags rather than immutable action SHAs.

## P1 — Other repository risks

- `server.py` remains a composition monolith;
- reverse-proxy trust and client-IP rate limiting require an explicit deployment contract;
- Content Security Policy is absent from current security headers;
- background/shadow worker lifecycle ownership is incomplete;
- storage metadata cache invalidation and the unwired `IndexCoordinator` API mismatch remain technical debt;
- production compose naming and defaults remain ambiguous;
- durable answer/retrieval/policy replay and operational SLOs remain incomplete;
- independent security audit and penetration testing have not been completed.

## Risk update rule

A risk is not closed by a class existing, a test passing once, a retry becoming green, a receipt being content-addressed or a Notion page being current. Closure requires the specific missing authority, integration, deployment and observed evidence.
