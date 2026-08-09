# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-09  
**Repository checkpoint inspected:** `main@dc30817f2c4abb1afcaab2f127e679d5f9b884d7`  
**Continuity:** `8/12 = 66.7%` implementation readiness  
**Runtime:** `UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Governance:** active `main-governance` · solo mode · approvals `0`

A risk is not closed because a file exists, a test passes once, a receipt is
content-addressed, a PR merges, Notion is updated or aggregate evidence is green.
Closure requires the missing owner, integration and operational proof.

## Closed or materially reduced

- PR #264 implemented and tested the six-owner current-decision resolver composition;
- exact owner, principal, authorization, source, tenant, complete-subject and domain-scope
  bindings now fail closed on substitution;
- owner identity is pinned before and after owner resolution;
- missing, duplicate, stale, future-effective, malformed and extra-domain snapshots fail
  closed;
- represented negative and unknown decisions are preserved rather than softened;
- the resolver remains internal, unexported, injected and evidence-only;
- governance, Phase I audit identity and Notion target remain explicitly pinned.

The former risk “concrete current-decision resolver composition is absent” is closed at the
**internal implementation** level only. Live owner adapters and authenticity are not solved.

## P0 — Operator-selected trust root is not deployed

Content-addressed facade policy, registry, resolver and owner snapshots do not select or
activate themselves as trusted deployment configuration.

Required proof:

- one explicit operator/deployment owner;
- controlled expected facade-policy, registry, resolver and owner identities;
- signed or versioned configuration lineage;
- fail-closed missing, stale or unexpected identity;
- no caller-controlled substitution;
- audit evidence for configuration changes.

## P0 — Concrete live owner adapters are not selected

PR #264 defines six injected read-only owner ports. It intentionally does not choose
concrete live adapters for principal, authorization, consent/lawful basis, restriction,
erasure or PolicySnapshot state.

Residual risk:

- a future adapter may read stale, ambiguous or unauthenticated state;
- content hashes prove integrity, not authentic owner provenance;
- deployment composition could select the wrong owner implementation;
- no live multi-subject owner aggregation has been observed.

Required proof:

- accepted owner APIs and deployment identities;
- bounded current-state reads;
- authenticity and configuration lineage;
- adversarial integration tests against real owner stores;
- explicit Operator review before any runtime wiring.

## P1 — Content-addressed evidence is not authenticity

```text
Integrity ≠ authenticity
Integrity ≠ authorization
Evidence ≠ authority
Receipt ≠ permanent permission
Resolver result ≠ runtime permission
```

Hashes do not prove who created evidence, whether the source is authentic, whether
permission is still current, whether a claim is true or whether runtime use is allowed.

## P1 — Durable retention, replay, cleanup and erasure lifecycle is absent

Still unimplemented for admission artifacts:

- schema and migrations;
- idempotent append and deduplication;
- crash consistency and disk-full behavior;
- replay after restart;
- version compatibility;
- retention and cleanup;
- tenant/subject indexing;
- erasure during queued or partially evaluated work;
- reconciliation and operator evidence.

This is the next permitted bounded engineering slice.

## P1 — Runtime wiring and activation remain absent

Continuity is not wired into `/query`, startup, workers, schedulers, answer generation,
reminders, tools/actions, compute routing or Canon/TruthGate writes.

No feature flag, SLO, alert, rollback or Operator GO exists. This remains intentional.

## P1 — Producer and bare-observation bypass

No live anti-bypass enforcement proves that only the accepted current-decision resolver
composition and admission facade can form live-capable producer input.

Before any producer use:

- static/runtime guards must block bare observation use from server, startup, workers and
  advisory paths;
- current authorization, restriction and erasure state must be rechecked;
- output must remain advisory until a separate activation decision.

## P1 — Solo governance has no independent approval gate

The active ruleset intentionally uses required approvals `0`.

Current controls include PRs, exact aggregate evidence, up-to-date branches, conversation
resolution, blocked force pushes, restricted deletion and empty bypass.

Residual risk:

- automated checks are not independent review;
- a solo maintainer remains the final substantive merge decision owner;
- PR #264 has no submitted review objects.

Never claim that aggregate success is independent review.

## P1 — Uncharacterized CAS-contention failure

Issue #249 remains open. The first failure in workflow `31222680496` must remain in audit
history. PR #250 added diagnostics but did not prove the event harness-only.

Do not weaken one-winner/one-intent assertions or hide the event with skip, xfail or
unconditional reruns.

## P1 — Intermittent legacy embeddings-lock recovery timeout

The historical first-attempt timeout in PR #246 remains unresolved risk evidence.
Characterize frequency, subprocess termination and lock-owner cleanup bounds before
reclassification.

## P1 — Query path and Canon writer ownership

Open hardening work remains:

- some legacy query flows may promote through separate policy paths;
- promotion/supersession families are not fully unified;
- read-only query invariants are not proven across every path;
- some post-commit relation/provenance windows remain best-effort.

## P1 — Projection lifecycle and observability

Projection outbox and dispatcher primitives remain not fully lifecycle-wired. Required:
bounded startup/shutdown, cancellation, backoff, backlog/retry/parked/version-lag metrics,
reconciliation, restart/crash tests and erasure invalidation.

## P1 — Security and deployment

- no independent security audit or penetration test;
- no certified privacy/compliance program;
- shared API key is not user/tenant identity;
- public multi-user internet deployment is not safely supported by default;
- backup/restore and incident-response rehearsals remain incomplete;
- Docker dependency resolution is not identical to every frozen-uv CI profile.

## P1 — SQLite and future storage profiles

SQLite remains the accepted local-first profile. PostgreSQL, ANN and distributed profiles
remain research candidates with explicit return triggers; they must not be added for
symmetry alone.

## P1 — Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`. Model inference must not be treated as
user attestation. Future identity work requires consent, evidence, contestation,
correction, supersession, retraction, retention and erasure semantics.

## Risk update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.

A green check, content-addressed receipt, retrospective audit or Notion synchronization
never grants runtime authority by itself.
