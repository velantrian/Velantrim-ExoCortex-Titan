# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-06  
**Current verified implementation head:** `81836b4f715470c50a4c6c7768a2cde7478568c8`

Code presence and test coverage do not close a risk. Closure requires correct authority ownership, focused and full validation, wiring, activation controls and operational evidence.

## Closed or materially reduced in the current Continuity cycle

- the seven primary source-admission contracts are implemented, tested, internal and unwired;
- State reconciliation now has an explicit deterministic Draft adapter with exact complete-subject validation;
- Goal projection schema v2 preserves explicit subject identity through attestation, projection, decision and result identity;
- cross-subject Goal attestations fail closed;
- the State and Goal slices add no runtime, Canon, TruthGate, action, reminder or compute-route authority.

These improvements reduce evidence-integrity gaps. They do not close authorization, privacy, runtime or operational risks.

## P0 — Runtime authority remains absent

- admission evaluator runtime does not exist;
- admission-aware facade does not exist;
- current authorization, consent/lawful-basis, restriction, policy and erasure re-checks are not connected;
- Continuity source-admission artifacts are not wired into `/query`, startup, workers, schedulers or another production route;
- no feature flag, operational enablement, SLO, alert, rollback or operator approval workflow exists;
- no live runtime evidence demonstrates safe or useful behavior.

Required interpretation:

```text
IMPLEMENTED + TESTED
≠ WIRED
≠ ENABLED
≠ OBSERVED
```

## P0 — OpenLoop subject identity

`OpenLoopSignal`, `OpenLoopProjection` and `OpenLoopProjectionResult` still lack explicit tenant/user/subject identity.

Risks:

- source ownership can be lost between layers;
- `related_goal_ref` can be mistaken for authorization evidence;
- a result digest cannot prove which subject owns the result;
- a future adapter could silently infer or widen scope;
- multi-subject or ambiguous data could cross an authorization boundary.

Required next correction:

- mandatory explicit subject identity;
- schema-version update;
- subject included in canonical payload and content-addressed IDs;
- complete result subject set;
- fail-closed ambiguous and cross-subject handling;
- no adapter or runtime wiring in the same PR.

## P1 — Evidence is not current authority

Content-addressed IDs and immutable receipts prove integrity of represented payloads. They do not prove that permission is current.

Residual risks:

- authentication receipts may be forged, expired, revoked or unresolved;
- evaluator and rule identifiers are caller-supplied evidence until resolved and allowlisted;
- authorization may have expired or been withdrawn after receipt creation;
- consent or lawful basis may no longer apply;
- current policy may be incompatible with historical policy evidence;
- a subject may be restricted or erased after an artifact was issued;
- source evidence may be stale even when structurally valid.

Rules:

```text
Integrity ≠ Authorization
Evidence ≠ Authority
Admission receipt ≠ Permanent permission
Authorized batch ≠ Runtime permission
```

## P1 — Bare v1 observations are not live-authorized

`ContinuitySignalObservation` v1 does not bind tenant, subject, principal, purpose, retention or erasure state.

It remains valid for pure deterministic shadow aggregation only.

Risks:

- a future caller may bypass the batch/receipt boundary;
- producer allowlists may be misused as subject authorization;
- independently persisted or transported v1 observations may lose required scope evidence;
- bare producer calls may be wired as a false trust boundary.

Required proof before live use:

- only an admission-aware facade accepts live-capable input;
- the facade accepts a complete `AuthorizedContinuityObservationBatch`, not bare v1 values;
- static/runtime guards prevent bypass from `/query`, startup, workers, schedulers and advisory paths;
- current authorization, restriction and erasure state are re-checked before producer invocation.

## P1 — Privacy, restriction, retention and erasure

- current consent/lawful-basis evaluation is absent;
- current restriction registry integration is absent;
- current erasure-domain validation is absent;
- admission artifacts have no accepted durable retention/replay/cleanup lifecycle;
- derived State/Goal/OpenLoop artifacts are not yet proven erasure-addressable end to end;
- no proof exists for erasure during queued, persisted, replayed or partially evaluated admission work.

Historical permission must never override current deletion or restriction state.

## P1 — State Draft adapter limitations

PR #229 is implemented and tested, but remains internal and unwired.

Residual risks:

- source-owner authenticity is not independently established by the adapter;
- binding-receipt evidence can be structurally valid without current authorization;
- bounded derivation rules need future semantic calibration;
- large input/resource limits are not an accepted live policy;
- no evaluator decides whether a Draft may become an admitted observation;
- no persistence, replay or operator visibility exists.

The adapter must remain a deterministic proposal producer, not an admission evaluator.

## P1 — Goal projection limitations

PR #230 closes subject identity loss in the projection contract, but:

- no Goal source adapter exists;
- `user_id` vocabulary is still a legacy string rather than an accepted end-user identity provider;
- subject binding does not establish tenant, principal, purpose, consent or current permission;
- multi-subject result admission rules remain future work;
- schema v2 compatibility must be preserved across every future serializer, fixture and adapter.

A future Goal adapter must validate the complete subject set against binding and authorization evidence. It must not infer ownership from `goal_ref`.

## P1 — Concurrency and flaky evidence

An existing erasure recovery concurrency test has demonstrated an intermittent race during a coverage-instrumented run.

PR #229 exact head passed all required workflows after retry, but the first failure must remain visible.

Risks:

- retry can hide real scheduling-sensitive defects;
- `coverage.py` instrumentation can interact with thread trace hooks;
- a green retry does not prove unconditional first-attempt stability;
- erasure/recovery behavior under concurrent load remains a high-value stress surface.

Required action:

- preserve the test as blocking where instrumentation permits;
- record first failure, retry, exact unchanged head and final result;
- investigate recurrence rather than normalizing repeated retries;
- add or refine deterministic synchronization/fault evidence if the race repeats.

## P1 — GitHub ↔ Notion documentation drift

Code-only merges can temporarily leave public GitHub documentation behind an already updated Notion record.

Observed example:

- PR #229 and #230 were recorded in Notion;
- `CURRENT_STATE.md`, `WORK_LOG.md`, `COMPONENT_MAP.md` and `KNOWN_RISKS.md` still described the pre-#229/#230 state.

Risks:

- AI agents may repeat completed work;
- reviewers may misclassify source eligibility;
- current `main` SHA and live-readiness counters may be wrong;
- private/workspace history may appear more current than the public canonical technical record.

Required control:

- documentation impact classification on every PR;
- same-cycle updates for `GITHUB_AND_NOTION` changes;
- post-merge checkpoint when final merge SHA or CI evidence was unavailable before merge;
- GitHub remains sufficient without Notion access;
- no implementation slice starts while material canonical docs are known stale.

## P1 — Existing Continuity shadow stack

R1–R5B and the trusted signal producer are in `main`, tested and independently reviewed. The complete path exists only as a disabled deterministic in-memory shadow composition.

Residual risks:

- typed records can still be wrong or forged without trusted/authenticated producers;
- caller-supplied Gate policy facts have no accepted single live owner;
- Advisory intent resolution does not authenticate subject or tenant;
- replay equality proves deterministic artifacts, not semantic correctness;
- externally supplied safety counters can under-report effects;
- no accepted bounded input/resource policy exists for large batches;
- `ThreadWeaver` remains potentially O(n²);
- process-local results and receipts have no durable retention/erasure lifecycle;
- careless future wiring could convert evaluation into unintended authority.

## P1 — Identity

`core/identity_layer.py` remains formally quarantined as `LEGACY/UNWIRED`. It lacks the accepted candidate/evidence/approval/version/receipt/rollback lifecycle. Do not add production callers, persistence authority or a parallel identity-admission path.

A shared deployment API key is not end-user, tenant or subject authorization.

## P1 — Adaptive updates and projections

- RFC-0084 remains `PROPOSED`, has no implementation module or runtime wiring, forbids Canon writes and requires operator approval;
- projection dispatcher startup/runtime wiring remains deliberately absent;
- outbox growth, retry/dead-letter operations and long-horizon operational metrics require explicit ownership before activation.

## P1 — Coverage and CI

The `74%` floor is real and blocking, but it is only a regression ratchet:

- high aggregate coverage can hide low-coverage critical modules;
- coverage does not prove semantic correctness, security or realistic production behavior;
- instrumentation-sensitive concurrency tests require honest separate treatment;
- optional dependency installation is heavy and may consume excessive CI time/bandwidth;
- the floor should rise only with executable tests and must not be lowered silently.

## P1 — Other repository risks

- projection dispatcher is implemented and tested but not runtime-wired or operationally observed;
- production compose contracts remain materially inconsistent;
- store-wide contention, crash/restart and disk-full evidence remains incomplete on some storage paths;
- build and artifact reproducibility is improved but not complete across every supported artifact;
- Canon mutation ownership is not proven unified across every family;
- `server.py` remains a composition monolith;
- wheel and container require separately supported artifact contracts;
- ARM-03 remains heuristic, proposal-only, default-off and unwired.

## Risk update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED`.

A risk is not closed by a class existing, a test passing once, a retry becoming green, a receipt being content-addressed, or a Notion page being current. Closure requires the specific missing authority, integration and operational proof.
