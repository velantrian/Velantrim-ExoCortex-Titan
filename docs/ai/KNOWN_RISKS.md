# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-09  
**Repository `main` head at verification:** `28cc8b9ea7b94bf65a0b8cb2a37f30b2187cc6b5`  
**Latest implementation-bearing baseline:** `9f07db6de8d32683d00bfe4f1673e84493607553` (PR #246)  
**Phase I remediation status:** `GOVERNANCE CANARY IN PROGRESS`  
**Governance:** active `main-governance` ruleset, ID `20601712`, accepted solo mode

Code presence and passing tests do not close a risk. Closure requires correct authority
ownership, current evidence, integration controls, activation governance and operational
proof.

## Closed or materially reduced in the current cycle

- source-admission architecture and owner placement are accepted;
- seven primary immutable evidence contracts are implemented and tested;
- State, Goal and OpenLoop source adapters exist as bounded deterministic proposal transformers;
- Goal and OpenLoop subject identity is explicit and content-addressed;
- a pure deterministic evaluator and content-addressed evaluator/rule registry are implemented and tested;
- an internal admission-aware facade pins registry/evaluator/rule/resolver identity and verifies complete cross-contract scope;
- malformed Draft sets fail before resolver access;
- resolver identity/access/execution failures are converted to controlled fail-closed results;
- evaluator and facade outputs remain evidence-only;
- no accepted slice adds runtime, Canon, TruthGate, reminder, tool, action or compute authority;
- `main-governance` is active and requires PR-only changes, exact aggregate evidence,
  up-to-date branches and resolved conversations;
- force pushes are blocked, deletion is restricted and the bypass list is empty.

Continuity implementation readiness remains `7/12 = 58.3%`. This is not live readiness.

## P1 — Solo-mode governance has no independent approval gate

The active ruleset is materially stronger than the previously unprotected repository, but
it intentionally uses `required approvals = 0` for the accepted solo workflow.

Verified controls:

- pull request required before merge;
- exact `Titan aggregate merge evidence` status required;
- branch must be up to date;
- all review conversations must be resolved;
- force pushes blocked;
- deletions restricted;
- bypass list empty;
- Code Owner review OFF;
- Restrict updates OFF so valid protected merges remain possible.

Accepted variance:

- the earlier Stage-1 proposal required one non-author approval, stale-approval dismissal
  and latest-reviewable-push approval;
- GitHub does not count author self-approval;
- the owner selected solo mode rather than adding a second account or broad bypass;
- those three approval controls are therefore OFF and must not be claimed as active.

Residual risk:

- automated checks and resolved threads do not equal independent review;
- a solo maintainer can still approve the substantive decision to merge once configured
  checks pass;
- historical Phase I PRs remain without submitted independent reviews;
- issue #257 therefore remains open for the real retrospective independent audit.

Required handling:

- do not backfill fictional approvals;
- do not describe aggregate `SUCCESS` as independent review;
- record the accepted variance on issues #234 and #258;
- merge PR #260 only on exact-head aggregate `SUCCESS`, zero unresolved threads and the
  expected head SHA;
- keep the no-independent-review limitation visible until issue #257 is completed or
  explicitly deferred with written rationale.

Administrator record:
[`docs/operations/branch-ruleset-admin-handoff.md`](../operations/branch-ruleset-admin-handoff.md).

## P0 — Operator-selected trust root is not deployed

`ContinuityAdmissionFacadePolicy` and `ContinuityAdmissionRegistry` are content-addressed
and internally consistent. They do not select or activate themselves as operator-approved
deployment configuration.

Risks:

- a future caller could supply a permissive but internally valid policy or registry;
- exact evaluator/rule resolution could be mistaken for trusted configuration;
- multiple incompatible deployment roots could create inconsistent admission behavior;
- represented resolver identity could be accepted without a trusted composition owner.

Required proof:

- one explicit deployment/operator owner;
- configured expected facade-policy and registry identity;
- signed/versioned or otherwise controlled configuration lineage;
- fail-closed behavior when identity is missing, stale or unexpected;
- audit evidence for changes;
- no caller-controlled substitution.

## P0 — Concrete current-decision resolver composition is absent

The facade exposes a typed `ContinuityCurrentDecisionResolver` boundary, but no accepted
concrete composition currently obtains authoritative evidence from existing owners.

Still absent:

- principal/authentication evidence composition;
- tenant and subject authorization composition;
- consent or lawful-basis composition;
- restriction composition;
- erasure-domain composition;
- current `PolicySnapshot` compatibility composition;
- complete multi-subject aggregation owner.

Risks:

- forged, stale or incorrectly scoped evidence;
- one blocked subject silently filtered from a multi-subject result;
- historical authorization overriding current withdrawal or erasure;
- resolver disagreement converted into permissive output;
- shared deployment API key mistaken for user identity;
- duplicated policy/identity logic creating a second source of truth.

Required rule:

```text
missing / stale / unknown / conflicting / partially covered current state
→ reject complete evaluation fail-closed
```

The next slice must reuse accepted owners and remain internal, unwired and evidence-only.

## P1 — Content-addressed evidence is not authenticity

Content addressing proves that represented contents match an identifier. It does not
prove:

- who created the evidence;
- whether the source or resolver was authentic;
- whether permission is current;
- whether represented claims are true;
- whether runtime use is permitted.

```text
Integrity ≠ authenticity
Integrity ≠ authorization
Evidence ≠ authority
Receipt ≠ permanent permission
Facade result ≠ runtime permission
```

## P1 — Privacy, restriction, retention and erasure lifecycle

Current gaps:

- no accepted live consent/lawful-basis resolver integration;
- no live restriction registry integration;
- no live erasure-domain validation integration;
- admission artifacts have no accepted durable retention/replay/cleanup lifecycle;
- queued, persisted, replayed and partially evaluated artifacts are not proven erasure-addressable end to end;
- no operator evidence proves multi-subject erasure behavior.

Historical permission must never override current deletion or restriction state.

## P1 — Durable persistence and replay are absent

Current evaluator, facade result and receipts are pure in-memory evidence contracts.

Not proven:

- storage schema and migrations;
- idempotent append and deduplication;
- retention and cleanup;
- replay after restart;
- schema-version compatibility;
- subject/tenant indexing;
- erasure during queued or partially processed work;
- crash consistency and disk-full behavior for admission artifacts;
- operator inspection and reconciliation.

Persistence remains a separate decision after concrete resolver composition is accepted.

## P1 — Runtime wiring and activation remain absent

No source-admission path is wired into:

- `/query`;
- startup;
- workers or schedulers;
- answer generation;
- reminders or notifications;
- tool/action execution;
- compute routing;
- Canon or TruthGate writes.

No feature flag, SLO, alert, rollback or Operator GO exists. This is intentional.

## P1 — Bare observation and producer bypass

`ContinuitySignalObservation` v1 does not bind full tenant, principal, subject, purpose,
retention or erasure state. The merged facade does not yet have live callers or runtime
anti-bypass enforcement.

Required proof before producer use:

- only accepted resolver composition and the admission facade may create live-capable producer input;
- static/runtime guards block bare v1 use from server, startup, workers and advisory paths;
- current authorization, restriction and erasure state are rechecked before producer invocation;
- producer output remains advisory until a separate activation decision.

## P1 — Uncharacterized CAS-contention test failure

PR #247 post-merge Full Titan run `31222680496` on SHA
`294bdfa6a77097e48310872a2e3fae811e8c2c9e` failed attempt 1 in:

```text
tests/test_promotion_projection_outbox_caller.py::
test_cas_contention_yields_exactly_one_winner_and_one_intent[25]
```

Failure: `threading.BrokenBarrierError` at `barrier.wait(timeout=15)`.

Attempt 2 on the unchanged exact SHA passed (`3746 passed, 17 skipped, 1 xfailed`).
Local audit runs reported 30/30 targeted parameterized passes on the same family.

Classification: **uncharacterized CAS-contention test failure**. The barrier timeout
shows that not all 25 contenders reached the synchronization point in time. It does
**not** yet prove whether the cause is runner scheduling, test orchestration, or a
worker exiting or blocking before/during the production pre-CAS path.

Diagnostic harness landed in merged
[PR #250](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/250)
(`e16db600da155c0496a727a56a501c2f984f37fd`, tracked by
[issue #249](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/249)).
That PR does **not** change production CAS semantics and does **not** reclassify the
incident as a proven harness-only flake. Residual diagnostic limit: thread-based
diagnostics do not provide hard process kill for a permanently hung worker.

This family is distinct from fresh-bootstrap ADD COLUMN races and from legacy
embeddings-lock recovery timeouts.

Required follow-up:

- retain attempt 1 in audit history;
- use the merged stage-based diagnostics to identify which contenders stalled and at
  which stage on the next observed failure;
- avoid skip, xfail, flaky markers or unconditional reruns as the only mitigation;
- do not weaken one-winner or one-intent assertions without proven production defect;
- do not close this risk as “harness-only flake” until characterization evidence exists.

## P1 — Intermittent legacy embeddings-lock recovery timeout

PR #246 exact-head Full Titan run `31219904698` had one first-attempt timeout in
`test_drop_legacy_embeddings_lock_owner_process_is_bounded` after 20 seconds. Coverage
passed, and attempt 2 on the unchanged SHA passed the full suite.

This is not attributed to the facade or to the CAS-contention family above. It remains
legacy recovery/concurrency risk evidence because a green retry does not prove the
timeout impossible.

Required follow-up:

- retain the first failure in audit history;
- characterize frequency and environmental sensitivity;
- verify subprocess termination and lock-owner cleanup bounds;
- avoid weakening or excluding the blocking test merely to remove noise.

## P1 — Semantic calibration and resource limits

Deterministic mapping and evaluation do not prove semantic usefulness.

Open questions:

- precision and false-positive rates of State/Goal/OpenLoop Drafts;
- confidence thresholds across workloads;
- bounded batch size and processing time;
- large multi-subject behavior;
- evaluator rule calibration;
- stale-source and stale-current-evidence windows;
- memory and latency cost;
- user correction rate.

Offline and shadow evaluation must precede live activation.

## P1 — Query path and Canon writer ownership

Global Titan hardening remains open:

- legacy query flow may still perform promotion through its own policy;
- promotion/supersession families are not fully unified under one gate/CAS/audit/outbox protocol;
- read-only query invariants are not proven across every path;
- best-effort post-commit relation/provenance windows remain on some legacy paths.

Required direction:

```text
query / retrieval → evidence or typed proposal only
explicit write command → policy → TruthGate → CAS → version/audit/outbox → commit
```

## P1 — Projection lifecycle and observability

Projection outbox and dispatcher primitives are implemented/tested but not fully
runtime-wired.

Still required:

- single lifecycle owner;
- bounded startup and clean shutdown;
- cancellation/backoff/jitter;
- backlog age, retries, parked count and version-lag metrics;
- reconciliation and repair;
- restart/crash tests;
- erasure invalidation across derived projections.

## P1 — Security and deployment

- no independent security audit or penetration test;
- no certified privacy/compliance program;
- shared API key is deployment authentication, not user/tenant identity;
- public internet multi-user deployment is not supported safely by default;
- backup/restore and incident-response rehearsals remain incomplete;
- `server.py` remains a composition monolith;
- supply-chain and artifact reproducibility are improved but not complete for every profile.

## P1 — SQLite and future storage profiles

SQLite remains the accepted local-first Canon profile and has substantial
concurrency/crash/disk-full evidence. It is not proven for multi-node HA, network
filesystems or large multi-tenant server workloads.

PostgreSQL, ANN and distributed profiles remain Research Mode candidates governed by
explicit return triggers. They must not be implemented merely for architectural symmetry.

## P1 — Documentation drift

Code or repository-setting changes can temporarily leave canonical GitHub and Notion
status behind.

Controls:

- per-PR documentation impact classification;
- aggregate merge-evidence metadata check;
- active ruleset requiring the exact aggregate status;
- public AI context pack;
- machine-readable project state;
- direct Notion synchronization or structured handoff;
- per-PR checkpoint documents.

Residual risk:

- repository settings can change manually after documentation is written;
- governance docs must distinguish API-observed configuration from behavior actually
  exercised by a canary;
- PR #260 must complete the current synchronization before issue #258 closes.

## P1 — Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`.

Do not add production callers or use model inference as user attestation. Any future
identity/personalization path requires consent, evidence, contestation, correction,
supersession, retraction, retention and erasure semantics.

## Closed/narrowed evidence notes

- Goal/OpenLoop subject identity gaps are closed by v2 contracts;
- State, Goal and OpenLoop adapter absence is closed;
- deterministic evaluator/rule-registry absence is closed;
- internal facade and typed resolver-boundary absence is closed by PR #246;
- concrete trusted resolver composition remains open;
- repository ruleset absence is closed by active ruleset ID `20601712`;
- independent approval is intentionally absent in solo mode and remains a documented
  governance limitation, not a closed proof;
- a prior erasure-recovery ownership race was fixed without excluding the blocking coverage test;
- the evaluator chronology fixture failure and PR #246 intermittent SQLite timeout remain visible in audit history.

## Risk update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.

A risk is not closed by a file existing, a test passing once, a content-addressed receipt,
a green retry, a Notion update, aggregate success or a research plan. Closure requires the
specific missing owner, integration and operational proof.
