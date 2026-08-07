# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-07  
**Repository `main` head at verification:** `9dfbfe5822221550389d95b751c8d85b044f6372`  
**Latest implementation-bearing baseline:** `42aa79338c57e9b9a67c3e3c08dd948b60c5541f`  
**Machine-readable state:** [`docs/state/project_state.json`](../state/project_state.json)

Code and passing tests do not establish wiring, enablement, authority or production safety. Keep `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` separate.

## Closed or materially reduced

- seven primary source-admission contracts are implemented and adversarially tested;
- State, Goal v2 and OpenLoop v2 have deterministic bounded Draft adapters;
- Goal and OpenLoop schemas preserve complete content-addressed subject identity;
- all three adapters validate complete source/binding subjects and authorization subset relationships;
- Goal derives evidence coverage only for active, explicitly attested and included projections;
- OpenLoop derives evidence coverage only for `OPEN` and `OVERDUE`; resolved/future loops derive nothing positive;
- semantic text, priority, deadlines and relations cannot create reminder, action, importance, sensitivity, answer or compute authority;
- aggregate merge evidence and CODEOWNERS are active in `main`;
- PRs #236, #238, #239 and #240 demonstrated exact-head Draft/Ready aggregation;
- recovery workers no longer report terminal results for batches they failed to claim;
- the recovery race passes ordinary and coverage modes before and after the hotfix merge;
- repository-head, implementation-baseline and documentation-checkpoint SHA roles are now represented separately;
- portable `kb_graph.json` preservation and referential-integrity validation have explicit owners and tests without deleting or rewriting the knowledge asset.

The source-adapter family is complete at `IMPLEMENTED · TESTED · INTERNAL · UNWIRED`. Admission, current permission, privacy, facade, persistence, runtime and repository-settings risks remain open.

## P0 — Trusted admission decision boundary remains absent

The existing admission receipt and batch classes can validate a caller-supplied partition. They do not themselves establish that the evaluator, rule or current decision evidence is trusted.

Missing:

- allowlisted evaluator and rule registry;
- deterministic admission evaluator;
- explicit resolved current authentication evidence;
- current tenant, subject and purpose authorization resolution;
- current consent or lawful-basis verification;
- current restriction, erasure and policy compatibility evidence;
- anti-replay/staleness handling for those current decisions.

Consequences:

```text
valid receipt structure ≠ trusted admission decision
historical authorization context ≠ current permission
authorized batch structure ≠ runtime eligibility
```

No caller-supplied evaluator/rule string may be treated as trusted merely because it is identity-bound in a receipt.

## P0 — Runtime authority boundary remains absent

- admission-aware facade does not exist;
- current authorization/privacy/restriction checks are not connected to a composition boundary;
- no admission artifact is wired into `/query`, startup, workers or schedulers;
- bare v1 observations remain structurally usable by the pure shadow producer and require anti-bypass guards before any live path;
- no feature flag, operator approval, SLO, alert, rollback or kill-switch evidence exists;
- no live useful-behavior evidence exists.

```text
IMPLEMENTED + TESTED ≠ WIRED ≠ ENABLED ≠ OBSERVED
```

## P0 — Repository governance is implemented but not enforced

PR #235 provides an active aggregate status and CODEOWNERS. Later PRs prove the status works. `main` is still unprotected and repository rulesets are absent.

Consequences:

- GitHub does not technically require `Titan aggregate merge evidence`;
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

Content-addressed IDs, source bindings, envelopes, Drafts, receipts and batches prove represented evidence integrity and traceability. They do not prove current permission.

Residual risks:

- authentication evidence may be forged, expired, revoked or unresolved;
- authorization or consent may be withdrawn after context creation;
- restriction, policy or erasure state may change;
- evaluator/rule identities are untrusted until resolved and allowlisted;
- structurally valid historical evidence may be stale;
- batch validity time does not by itself re-check current policy or erasure state.

Current deletion, restriction and authorization decisions must dominate historical evidence.

## P1 — Source adapter limitations

### State

Implemented/tested/internal/unwired. Validates deterministic State identity and complete subject binding, but does not authenticate the source owner, decide admission, persist or establish current permission.

### Goal v2

Implemented/tested/internal/unwired. Remaining limitations:

- `user_id` is a legacy vocabulary, not an accepted identity provider;
- external source-binding and authorization evidence are still required;
- current principal, tenant, consent, restriction, erasure and policy are unresolved;
- no admission decision, producer invocation, persistence or runtime effect;
- positive mapping is limited to evidence coverage for active, attested, included projections.

### OpenLoop v2

Implemented/tested/internal/unwired. Remaining limitations:

- source result does not contain full original signal/resolution payloads;
- adapter can recompute projection/result IDs only and requires signal/resolution IDs as complete binding evidence;
- `loop_key`, `related_goal_ref`, summary and deadline are not ownership or authorization evidence;
- `OPEN`/`OVERDUE` only propose evidence coverage; they cannot create reminder, schedule, action, current-state, answer or delivery authority;
- current auth/privacy/policy state is unresolved;
- no admission decision, producer invocation, persistence or runtime effect.

## P1 — Privacy, restriction, retention and erasure

- current consent/lawful-basis evaluation is absent;
- current restriction and erasure-domain integration is absent;
- envelopes, Drafts, receipts and batches have no accepted durable retention/replay/cleanup lifecycle;
- derived State/Goal/OpenLoop artifacts are not proven erasure-addressable end to end;
- deletion during queued, persisted, replayed or partially evaluated work is unproven;
- multi-subject erasure and reappearance handling are unproven;
- persisted-artifact indexes by subject and erasure domain do not exist.

No persistence should be added until discoverability, bounded retention, invalidation and deletion proofs exist.

## P1 — Bare observations and Drafts are not live-authorized

`ContinuityObservationDraft` and `ContinuitySignalObservation` are proposal/evidence values. `AuthorizedContinuityObservationBatch` is a bounded evidence wrapper, still marked `no_runtime_authority`.

Required proof before a live-capable path:

- only an admission-aware facade accepts live-capable input;
- facade accepts complete authorized batches, never bare Drafts/observations;
- evaluator and rules are resolved and allowlisted;
- current authorization, consent, restriction, policy and erasure state are re-checked;
- API, startup, worker, scheduler and advisory paths cannot bypass the facade;
- aggregate output is bound to batch and receipt identity;
- zero user-visible effect is measured in a disabled shadow experiment first.

## P1 — Erasure recovery and concurrency

PR #236 post-merge coverage exposed a reporting race: a losing recovery worker returned the winner's terminal report. PR #238 closes the result-ownership gap while preserving single side-effect execution.

Evidence:

```text
Triggering run:                31164988400 FAILURE
Exact hotfix head:             6cc5899afe98f53a1ee0e7fff665948b0c5a3d92
Hotfix full CI + coverage:     31166079813 PASS
Hotfix Docker:                 31166079825 PASS
Hotfix merge:                  f0c17de05df6c762c69974775e3c95d9e613cf47
Post-merge full CI + coverage: 31166699745 PASS
Post-merge Docker:             31166697770 PASS
```

Required discipline remains: preserve first failures, avoid blind retry normalization, use deterministic fault injection plus real concurrency tests, and distinguish result ownership from side-effect ownership.

## P1 — GitHub ↔ Notion drift

Top snapshots can become stale while historical blocks remain accurate. Required control:

- one canonical current checkpoint at the top;
- same-cycle GitHub + Notion synchronization;
- structured handoff only when Notion is unavailable;
- post-merge final SHA and CI checkpoint;
- supersede stale PRs rather than merging documentation from an old base;
- do not start the next implementation slice while canonical status is materially stale;
- distinguish repository head, implementation baseline and documentation checkpoint in both systems.

The machine-readable state records these SHA roles explicitly. Notion synchronization for this change remains required until its current checkpoint is updated from the final PR evidence.

## P1 — Portable KB integrity is not claim truth or reproducibility proof

`kb_graph.json` is intentionally preserved as a knowledge asset. The portable validator
can prove structural and referential integrity, counts and a file SHA-256. It cannot by
itself prove:

- truth or freshness of every claim;
- complete licensing/provenance for every source;
- deterministic equality with a fresh source rebuild;
- semantic quality of inferred edges;
- admission into Canon or current runtime eligibility;
- erasure/privacy suitability for a specific deployment.

Required next proofs for a regenerated asset include semantic before/after diff,
source/generator revision, provenance changes, graph-quality report and rollback artifact.

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
- shared API key is not end-user, tenant or subject authorization;
- coverage ≥74% is a regression floor, not a correctness proof;
- dependency reproducibility and immutable action-SHA policy remain incomplete;
- `server.py` remains a composition monolith;
- reverse-proxy trust, CSP, worker lifecycle, deployment naming, operational SLOs, backup/recovery rehearsal and independent security testing remain incomplete.

## Risk update rule

A risk closes only when the missing authority, integration, deployment or observed evidence exists. A class, hash, receipt, green test, retry or synchronized document is insufficient by itself.
