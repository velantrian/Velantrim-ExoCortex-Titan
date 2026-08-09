# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-09  
**Repository checkpoint inspected:** `main@064845579c520e7464678cd0c41d9b650368dfa8`  
**Continuity:** `9/12 = 75.0%` implementation readiness  
**Runtime:** `UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Governance:** active `main-governance` · solo mode · approvals `0`

A risk is not closed because a file exists, a test passes once, an artifact is
content-addressed, a PR merges, Notion is updated or aggregate evidence is green.
Closure requires the missing owner, integration and operational proof.

## Closed or materially reduced

- PR #264 implemented and tested six-owner current-decision composition;
- PR #267 implemented and tested the internal durable admission-artifact lifecycle;
- deterministic identity, integrity verification and exact-scope replay now fail closed;
- duplicate and concurrent append are idempotent without silent overwrite;
- cross-tenant, principal, authorization-subject-set and policy substitution are rejected;
- bounded explicit-policy cleanup and retry-stable cleanup receipts are present;
- exact externally supplied erasure-owner evidence can atomically neutralize payloads;
- replay and re-append after neutralization are rejected;
- injected partial append and interrupted cleanup/erasure transactions roll back;
- producer/runtime/public-package side effects remain absent;
- governance, Phase I audit identity and the exact Notion target remain pinned.

The former risk “durable retention, replay, cleanup and erasure lifecycle is absent” is
closed at the **internal implementation and test** level only. Runtime integration,
operator selection and live operational proof remain absent.

## P0 — Operator-selected trust root is not deployed

Content-addressed facade policy, registry, resolver, owner snapshots and lifecycle
artifacts do not select or activate themselves as trusted deployment configuration.

Required proof:

- one explicit operator/deployment owner;
- controlled expected facade-policy, registry, resolver, owner and lifecycle identities;
- signed or versioned configuration lineage;
- fail-closed missing, stale or unexpected identity;
- no caller-controlled substitution;
- audit evidence for configuration changes.

## P0 — Concrete live owner adapters are not selected

The six injected read-only current-decision owner ports intentionally have no selected live
adapters for principal, authorization, consent/lawful basis, restriction, erasure or
PolicySnapshot state.

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
- explicit Operator review before runtime wiring.

## P1 — Content-addressed evidence is not authenticity

```text
Integrity ≠ authenticity
Integrity ≠ authorization
Evidence ≠ authority
Receipt ≠ permanent permission
Resolver result ≠ runtime permission
Durable artifact ≠ permission to use it
```

Hashes do not prove who created evidence, whether the source is authentic, whether
permission is still current, whether a claim is true or whether runtime use is allowed.

## P1 — Durable lifecycle is not operationally integrated

PR #267 supplies an internal SQLite owner and adversarial tests, but does not prove:

- deployment selection of the owner or database path;
- startup/shutdown ownership;
- production filesystem permissions and disk-full behavior;
- backup, restore and disaster recovery;
- live retention policy configuration;
- scheduler/worker cleanup execution;
- live erasure-owner integration;
- multi-process contention under deployment topology;
- operational reconciliation, metrics, alerts or runbooks;
- observed restart/crash recovery.

These are integration and operations requirements, not reasons to weaken the internal
artifact contract.

## P1 — Runtime wiring and activation remain absent

Continuity is not wired into `/query`, startup, workers, schedulers, answer generation,
reminders, tools/actions, compute routing or Canon/TruthGate writes.

No feature flag, SLO, alert, rollback or Operator GO exists. This remains intentional.

## P1 — Producer and bare-observation bypass

No live anti-bypass enforcement proves that only the accepted current-decision resolver
composition and lifecycle boundary can form live-capable producer input.

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
- PR #267 has no submitted review objects.

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

The new internal lifecycle does not authorize a distributed or server database migration.

## P1 — Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`. Model inference must not be treated as
user attestation. Future identity work requires consent, evidence, contestation,
correction, supersession, retraction, retention and erasure semantics.

## Risk update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.

A green check, durable receipt, retrospective audit or Notion synchronization never grants
runtime authority by itself.
