# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-07  
**Current implementation `main`:** `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d`

Code and passing tests do not establish wiring, enablement, authority or production safety. Keep `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` separate.

## Closed or materially reduced

- seven primary source-admission contracts are implemented/tested/internal/unwired;
- State reconciliation has a deterministic bounded Draft adapter;
- Goal and OpenLoop schemas preserve complete content-addressed subject identity;
- Goal now has a deterministic bounded Draft adapter;
- Goal adapter recomputes source identities, validates complete decision/subject/evidence coverage and rejects stale bindings;
- active attested goals can derive only `EVIDENCE_COVERAGE_ITEM=True`;
- inactive/excluded goals and semantic text fields cannot create reminder, action, importance or compute authority;
- aggregate merge evidence and CODEOWNERS are in `main`;
- PR #236 demonstrated Draft→pending and exact-head Ready→success aggregation across CI, Continuity and Docker.

The Goal source-adapter gap is closed. OpenLoop admission, current permission, privacy, facade, runtime and operator-enforcement risks remain open.

## P0 — Runtime authority boundary remains absent

- OpenLoop source adapter does not exist;
- admission evaluator and trusted evaluator/rule registry do not exist;
- admission-aware facade does not exist;
- current authorization, consent/lawful basis, restriction, erasure and policy checks are not connected;
- no admission artifacts are wired into `/query`, startup, workers or schedulers;
- no feature flag, operator approval, SLO, alert, rollback or kill-switch evidence exists;
- no live useful-behavior evidence exists.

```text
IMPLEMENTED + TESTED ≠ WIRED ≠ ENABLED ≠ OBSERVED
```

## P0 — Repository governance is implemented but not enforced

PR #235 provides an active aggregate status and CODEOWNERS. PR #236 proves the status works. `main` is still unprotected and repository rulesets are absent.

Consequences:

- GitHub does not technically require the aggregate status;
- approvals, stale-approval dismissal and resolved conversations are not enforced;
- direct push, force-push and deletion restrictions are not enforced;
- CODEOWNERS review is advisory until required by branch rules.

Administrator action tracked by issue #234:

- protect `main`;
- require pull requests and at least one approval;
- dismiss stale approvals;
- require conversation resolution and up-to-date branches;
- require `Titan aggregate merge evidence`;
- require CODEOWNERS review;
- restrict direct pushes and bypass;
- block force pushes and deletion.

## P1 — Evidence is not current authority

Content-addressed IDs, source bindings and envelopes prove represented evidence integrity. They do not prove current permission.

Residual risks:

- authentication evidence may be forged, expired, revoked or unresolved;
- authorization or consent may be withdrawn after receipt creation;
- restriction, policy or erasure state may change;
- evaluator/rule identities are untrusted until resolved and allowlisted;
- structurally valid historical evidence may be stale.

```text
Integrity ≠ Authorization
Admission receipt ≠ Permanent permission
Authorized batch ≠ Runtime permission
```

## P1 — Source adapter limitations

### State

Internal/unwired. It validates structural identity and complete subject binding but does not authenticate the source owner, decide admission, persist or establish current authorization.

### Goal

Implemented/tested/internal/unwired, but:

- `user_id` remains a legacy string vocabulary, not an accepted identity provider;
- adapter input still depends on externally issued source-binding and authorization evidence;
- it does not resolve current principal, tenant, consent, restrictions, erasure or policy;
- it does not create admission receipts or authorized batches;
- it does not invoke the signal producer or persist output;
- its only positive mapping is evidence coverage for active explicitly attested projections.

### OpenLoop

Subject binding v2 is complete, but:

- no source adapter exists;
- no bounded signal mapping has been accepted;
- no complete binding/evidence validation exists at the adapter boundary;
- future code must not infer ownership from `loop_key` or `related_goal_ref`;
- open/deadline/resolution semantics must not become reminders, actions or current-state authority.

## P1 — Privacy, restriction, retention and erasure

- current consent/lawful-basis evaluation is absent;
- current restriction and erasure-domain integration is absent;
- admission artifacts have no accepted durable retention/replay/cleanup lifecycle;
- derived State/Goal/OpenLoop artifacts are not proven erasure-addressable end to end;
- deletion during queued, persisted, replayed or partially evaluated work is unproven;
- multi-subject erasure and reappearance handling are unproven.

Historical permission must never override current deletion or restriction state.

## P1 — Bare observations and Drafts are not live-authorized

`ContinuityObservationDraft` and `ContinuitySignalObservation` are proposal/evidence values. They do not carry the complete current authorization decision required for live use.

Required proof:

- only an admission-aware facade accepts live-capable input;
- facade accepts complete `AuthorizedContinuityObservationBatch`, never bare Drafts/observations;
- evaluator/rules are resolved and allowlisted;
- current authorization, consent, restriction, policy and erasure state are re-checked;
- API, startup, worker, scheduler and advisory paths cannot bypass the facade.

## P1 — Concurrency and flaky evidence

An erasure recovery test has shown an intermittent race under coverage instrumentation. Preserve first failures, unchanged-head retries and final results; investigate recurrence rather than normalizing retries.

## P1 — GitHub ↔ Notion drift

Top snapshots can become stale while historical blocks remain visible. Required control:

- one canonical current snapshot at the top;
- same-cycle GitHub + Notion synchronization;
- structured hand-off only when Notion is unavailable;
- post-merge final SHA and CI checkpoint;
- no next implementation slice while canonical status is materially stale.

## P1 — Existing shadow/runtime infrastructure

- R1–R5B and the signal producer remain shadow/unwired;
- typed records may be semantically wrong despite valid hashes;
- replay equality proves determinism, not correctness or usefulness;
- process-local outputs lack durable retention/erasure lifecycle;
- careless wiring could convert advisory evidence into authority;
- projection dispatcher lacks startup lifecycle and observed operation;
- GRAPH/VECTOR targets and executable REMOVE remain inactive;
- ARM-04 admission and ARM-05 context assembly remain absent.

## P1 — Identity, supply chain and operations

- `core/identity_layer.py` remains legacy/unwired;
- shared API key is not end-user/tenant/subject authorization;
- coverage ≥74% is a regression floor, not a correctness proof;
- dependency reproducibility and immutable action-SHA policy remain incomplete;
- `server.py` remains a composition monolith;
- reverse-proxy trust, CSP, worker lifecycle, deployment naming, operational SLOs, backup/recovery rehearsal and independent security testing remain incomplete.

## Risk update rule

A risk closes only when the missing authority, integration, deployment or observed evidence exists. A class, hash, receipt, passing test, green retry or current Notion page is insufficient by itself.
