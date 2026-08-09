# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-09  
**Repository `main` head inspected:** `c9e272d5d9da76219f8e0caaf784892e80046a31`  
**Latest implementation-bearing baseline:** `9f07db6de8d32683d00bfe4f1673e84493607553` (PR #246)  
**Governance:** active `main-governance` · ID `20601712` · accepted solo mode  
**Retrospective audit:** completed; see [`phase-i-retrospective-audit-2026-08-09.md`](../audits/phase-i-retrospective-audit-2026-08-09.md)

A risk is not closed by a file existing, a test passing once, a green retry, a Notion
update, aggregate success or a research plan. Closure requires the missing owner,
integration and operational proof.

## Closed or materially reduced

- the repository now requires PRs, the exact aggregate status, an up-to-date branch and
  resolved conversations;
- force pushes are blocked, deletion is restricted and the bypass list is empty;
- the solo-mode variance is public and no inactive approval setting is claimed;
- the governance canary merged through the protected path in PR #260;
- Phase I exact-head CI and aggregate evidence were retrospectively checked for PRs
  #254/#250/#251/#252/#253/#256;
- the requested issue #257 audit was performed without fabricating historical approvals;
- frozen `uv.lock` CI installation and full-SHA GitHub Actions pinning are active;
- source-admission architecture, seven evidence contracts, three source adapters, the
  evaluator and the internal admission facade remain implemented and tested.

Continuity readiness remains `7/12 = 58.3%`. It is not live readiness.

## P1 — Solo governance has no independent approval gate

The active ruleset intentionally uses `required approvals = 0`.

Current controls:

- PR required;
- exact `Titan aggregate merge evidence` required;
- branch up to date;
- conversation resolution required;
- force pushes blocked;
- deletion restricted;
- bypass empty;
- Code Owner review OFF;
- stale-approval dismissal OFF;
- latest-push approval OFF;
- Restrict updates OFF.

Residual risk:

- automated checks are not independent review;
- a solo maintainer remains the final substantive merge decision owner;
- the six earlier Phase I PRs have no submitted review objects.

The retrospective audit closes the request to inspect the range. It does **not** backfill
approvals or change the historical review state.

Required handling:

- never state that aggregate `SUCCESS` is independent review;
- do not create approval metadata after the fact;
- introduce a real second reviewer only through an explicit future governance change;
- keep the current solo model documented until that change is actually adopted.

## P0 — Operator-selected trust root is not deployed

`ContinuityAdmissionFacadePolicy` and `ContinuityAdmissionRegistry` are content-addressed
and internally consistent. They do not select or activate themselves as trusted deployment
configuration.

Required proof:

- one explicit operator/deployment owner;
- controlled expected facade-policy and registry identity;
- versioned or signed configuration lineage;
- fail-closed behavior for missing, stale or unexpected identity;
- no caller-controlled substitution;
- audit evidence for configuration changes.

## P0 — Concrete current-decision resolver composition is absent

No accepted concrete composition currently obtains authoritative evidence for:

- principal/authentication;
- tenant and subject authorization;
- consent or lawful basis;
- restrictions;
- erasure-domain state;
- current `PolicySnapshot` compatibility;
- complete multi-subject aggregation.

Required rule:

```text
missing / stale / unknown / ambiguous / conflicting / partially covered state
→ reject the complete evaluation fail-closed
```

The next slice must reuse accepted owners and remain internal, unwired and evidence-only.

## P1 — Content-addressed evidence is not authenticity

```text
Integrity ≠ authenticity
Integrity ≠ authorization
Evidence ≠ authority
Receipt ≠ permanent permission
Facade result ≠ runtime permission
```

Content addressing does not prove who created evidence, whether the source is authentic,
whether permission is current, whether the claim is true, or whether runtime use is
allowed.

## P1 — Privacy, restriction, retention and erasure lifecycle

Still absent:

- live consent/lawful-basis resolver integration;
- live restriction and erasure-domain integration;
- accepted durable retention, replay and cleanup lifecycle;
- end-to-end erasure-addressability for queued, persisted or derived artifacts;
- operator proof for multi-subject erasure behavior.

Historical permission must never override current withdrawal, restriction or deletion.

## P1 — Durable persistence and replay are absent

Not proven for admission artifacts:

- schema and migrations;
- idempotent append and deduplication;
- crash consistency and disk-full behavior;
- replay after restart;
- schema-version compatibility;
- retention and cleanup;
- subject/tenant indexing;
- erasure during queued or partially evaluated work;
- operator reconciliation.

Persistence remains a separate architecture and implementation decision.

## P1 — Runtime wiring and activation remain absent

Continuity source admission is not wired into `/query`, startup, workers, schedulers,
answer generation, reminders, tools/actions, compute routing or Canon/TruthGate writes.

No feature flag, SLO, alert, rollback or Operator GO exists. This is intentional.

## P1 — Bare observation and producer bypass

`ContinuitySignalObservation` v1 does not bind full tenant, principal, subject, purpose,
retention or erasure state. No live caller or runtime anti-bypass enforcement exists.

Before producer use, prove that:

- only accepted resolver composition and the admission facade can form live-capable input;
- static/runtime guards block bare v1 use from server/startup/workers/advisory paths;
- current authorization, restriction and erasure state are rechecked;
- producer output remains advisory until a separate activation decision.

## P1 — Uncharacterized CAS-contention test failure

PR #247 post-merge run `31222680496` failed its first attempt in
`test_cas_contention_yields_exactly_one_winner_and_one_intent[25]` with
`threading.BrokenBarrierError`; the unchanged SHA passed on attempt 2.

PR #250 added stage diagnostics but did not change production CAS semantics. The incident
remains tracked by issue #249 and is not classified as harness-only.

Residual limitation: thread-based diagnostics do not provide hard process kill for a
permanently hung worker.

Required follow-up:

- retain the first failure in audit history;
- use stage diagnostics on the next observed failure;
- do not weaken one-winner or one-intent assertions;
- do not use skip/xfail/flaky markers or unconditional reruns as the only mitigation.

## P1 — Intermittent legacy embeddings-lock recovery timeout

PR #246 exact-head run `31219904698` had one first-attempt timeout in
`test_drop_legacy_embeddings_lock_owner_process_is_bounded`; the unchanged SHA later
passed.

Required follow-up:

- preserve the failed attempt;
- characterize frequency and environmental sensitivity;
- verify subprocess termination and lock-owner cleanup bounds;
- do not exclude the blocking test merely to remove noise.

## P1 — Semantic calibration and resource limits

Deterministic mapping does not prove semantic usefulness. Open questions include
precision, false positives, confidence thresholds, stale-evidence windows, batch bounds,
latency, memory cost and user correction rate.

Offline and shadow evaluation must precede live activation.

## P1 — Query path and Canon writer ownership

Open hardening work:

- legacy query flows may still promote through separate policy paths;
- promotion/supersession families are not fully unified under one gate/CAS/audit/outbox protocol;
- read-only query invariants are not proven across every path;
- some legacy post-commit relation/provenance windows remain best-effort.

Required direction:

```text
query / retrieval → evidence or typed proposal only
explicit write command → policy → TruthGate → CAS → version/audit/outbox → commit
```

## P1 — Projection lifecycle and observability

Projection outbox and dispatcher primitives are implemented/tested but not fully
runtime-wired.

Still required: one lifecycle owner, bounded startup/shutdown, cancellation, backoff,
backlog/retry/parked/version-lag metrics, reconciliation, restart/crash tests and erasure
invalidation of derived projections.

## P1 — Security and deployment

- no independent security audit or penetration test;
- no certified privacy/compliance program;
- shared API key is deployment authentication, not user/tenant identity;
- public multi-user internet deployment is not safely supported by default;
- backup/restore and incident-response rehearsals remain incomplete;
- `server.py` remains a composition monolith;
- Docker dependency resolution remains separate from the frozen-uv CI path;
- supply-chain reproducibility is improved but not complete for every profile.

## P1 — SQLite and future storage profiles

SQLite remains the accepted local-first Canon profile. It is not proven for multi-node HA,
network filesystems or large multi-tenant server workloads.

PostgreSQL, ANN and distributed profiles remain Research Mode candidates with explicit
return triggers. They must not be implemented for symmetry alone.

## P1 — Documentation drift

The retrospective audit found a real post-merge drift: status files at
`main@c9e272d5d9da76219f8e0caaf784892e80046a31` still described PR #260 as open and PR
#255 as pending.

This corrective audit PR updates the canonical GitHub files and the existing Titan Notion
page. Historical sections may preserve old states, but the newest dated section must be
clearly authoritative.

Controls:

- explicit documentation-impact classification;
- aggregate metadata enforcement;
- machine-readable project state;
- exact dated audit/checkpoint documents;
- direct Notion synchronization or a structured handoff;
- post-merge verification before claiming final synchronization.

## P1 — Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`.

Do not add production callers or treat model inference as user attestation. Any future
identity/personalization path requires consent, evidence, contestation, correction,
supersession, retraction, retention and erasure semantics.

## Risk update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.

A green check, content-addressed receipt, retrospective audit or Notion update never grants
runtime authority by itself.
