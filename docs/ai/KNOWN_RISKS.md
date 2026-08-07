# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-07  
**Current implementation `main`:** `f0c17de05df6c762c69974775e3c95d9e613cf47`

Code and passing tests do not establish wiring, enablement, authority or production safety. Keep `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` separate.

## Closed or materially reduced

- seven primary source-admission contracts are implemented/tested/internal/unwired;
- State reconciliation has a deterministic bounded Draft adapter;
- Goal and OpenLoop schemas preserve complete content-addressed subject identity;
- Goal has a deterministic bounded Draft adapter;
- the Goal adapter recomputes projection/result identities and validates decisions, complete subjects and evidence;
- active attested goals can derive only `EVIDENCE_COVERAGE_ITEM=True`;
- inactive/excluded goals and semantic text fields cannot create reminder, action, importance or compute authority;
- aggregate merge evidence and CODEOWNERS are active in `main`;
- PR #236 and PR #238 demonstrated Draft→pending and Ready→success exact-head aggregation;
- recovery workers no longer report terminal results for batches they failed to claim;
- the real two-worker race and a deterministic lost-claim case pass under ordinary and coverage modes both before and after hotfix merge.

The Goal source-adapter and recovery-result ownership gaps are closed. OpenLoop admission, current permission, privacy, facade, runtime and repository-settings risks remain open.

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

PR #235 provides an active aggregate status and CODEOWNERS. PR #236 and #238 prove the status works. `main` is still unprotected and repository rulesets are absent.

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
- open/deadline/resolution semantics must not become reminders, actions or current-state authority;
- the result contract does not contain enough original signal/resolution payload to recompute their underlying IDs, so an adapter may only recompute projection/result identities and require signal/resolution IDs as bound evidence unless the input contract is expanded separately.

## P1 — Erasure recovery and concurrency

PR #236 post-merge coverage run `31164988400` exposed a real reporting race:

- one worker owned and completed the batch;
- a losing recovery worker returned the winner's terminal report;
- two callers therefore appeared to have processed one batch.

PR #238 closes the ownership gap:

- recovery (`wait_if_running=False`) returns `None` after any lost claim;
- live/idempotent callers retain cached terminal readback and wait behavior;
- erasure selection, CAS fencing, lease ownership and deletion behavior are unchanged;
- exact-head ordinary pytest and coverage passed in `31166079813`;
- exact-head Docker passed in `31166079825`;
- post-merge ordinary pytest and full coverage passed in `31166699745`;
- post-merge Docker passed in `31166697770`.

Required discipline remains:

- preserve first failures and exact-head/post-merge evidence;
- do not normalize blind retries;
- prefer deterministic fault injection plus real connection/thread races;
- treat result ownership separately from side-effect ownership.

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

## P1 — GitHub ↔ Notion drift

Top snapshots can become stale while historical blocks remain visible. Required control:

- one canonical current snapshot at the top;
- same-cycle GitHub + Notion synchronization;
- structured hand-off only when Notion is unavailable;
- post-merge final SHA and CI checkpoint;
- supersede stale PRs rather than merging documentation from an old base;
- no next implementation slice while canonical status is materially stale.

PR #237 was closed without merge after PR #238 advanced `main`; PR #239 replaces it from the correct hotfix base.

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
