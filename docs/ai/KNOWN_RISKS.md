# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-10  
**Repository checkpoint:** `main@39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e`  
**Continuity:** `12/12 = 100%` — complete  
**Runtime:** `MECHANISMS WIRED · CURRENTLY DISABLED · OPERATOR GO ABSENT (CURRENT) · OBSERVED=TRUE (HISTORICAL, ONE ROLLED-BACK CANARY) · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`  
**Governance:** active `main-governance` · solo mode · approvals `0`

A canonical manifest, persisted decision, persisted observation evidence, a completed
canary, a green aggregate, or a Notion update does not prove operator authenticity,
current permission, or production authority. Continuity 12/12 is not a
production-readiness claim.

## Closed or materially reduced

- controlled enablement has one explicit deployment-owned decision contract; exact
  schema, canonical JSON and SHA-256 integrity are validated; decisions bind to exact
  configuration, lifecycle owner/version, tenant, content-free storage identity and
  one internal scope; enable leases are finite; disable decisions are explicit and
  monotonic; duplicate decisions are idempotent; stale/conflicting decisions fail
  closed; concurrent enable/disable converges through serialized in-process
  application and SQLite uniqueness constraints; decision evidence remains in the
  existing tenant-bound SQLite database; persisted evidence is revalidated and is
  never restart permission; `/query`, producer and all forbidden side effects remain
  absent;
- a bounded, content-free **observation mechanism** exists (PR #276): it records
  deterministic evidence of configuration/storage/owner binding stability, lease
  validity while enabled, and absence of runtime/side-effect authority, and reduces a
  session to one deterministic `rollback_verified` result;
- **real observed evidence now exists** (tracking issue #275): one
  human-operator-authorized bounded canary was executed against
  `main@39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e` using the real production
  composition functions — enable, observe, disable, verified post-disable rejection,
  clean shutdown, restart with no silent re-enable, `rollback_verified=true`. See
  `docs/adr/ADR-2026-08-10-continuity-12-12-bounded-observation-canary.md`.

The former risk “no observation mechanism exists at all” and the former risk “real
observed evidence is absent” are both closed. **This does not close or replace any of
the risks below.**

## P0 — No current Operator GO or deployed activation

No activation manifest is committed by this repository checkpoint. The canary's
Operator GO was single-use, scoped to one exact SHA, and is now **exhausted**.
`runtime currently enabled=false`, `operator authorization present=false`, and
`operator_go=false` remain the current facts. Before any future real activation, a
new operator must supply a new current exact decision and a new, separately scoped
Operator GO. Manifest SHA-256 proves integrity, not authenticity.

## P0 — Concrete live current-decision owner adapters remain unselected

The six current-decision ports still have no accepted live deployment adapters for
principal, authorization, consent/lawful basis, restriction, erasure and PolicySnapshot.
Controlled enablement and the bounded canary do not replace those owners.

Required proof before any side-effect-capable producer:

- authentic owner APIs and deployment identities;
- bounded current-state reads and configuration lineage;
- adversarial tests against accepted owner stores;
- current restriction/erasure/authorization rechecks;
- explicit operator decision under deployment governance.

## P1 — Continuity 12/12 is not production readiness

Completing all twelve bounded Continuity capabilities proves the internal mechanism
chain end to end under one narrow, operator-authorized, rolled-back canary. It does
not prove:

- production deployment, real user traffic, or production telemetry/monitoring;
- concrete live current-decision owner adapters (see P0 above);
- SLOs, alerting, backup/restore, disaster recovery, or rollback orchestration at
  production scale;
- public multi-user rollout or wider enablement;
- independent security review.

No claim of production-readiness, production authority, or safe autonomous deployment
is made by this checkpoint.

## P1 — Operational scope remains bounded

Not proved:

- multi-process decision contention;
- live crash recovery, backup/restore or disaster recovery under real production load;
- disk-full and filesystem-permission behavior in production;
- external audit service, SLO/SLA, alerting or rollback orchestration;
- public multi-user rollout.

## P1 — Solo governance has no independent approval gate

PR #273 and PR #276 each had zero submitted reviews. Codex did not run on either
because its usage limit was reached. Unresolved review threads were zero on both.
Independent review is **NOT CLAIMED** for the mechanism, and no independent review
was performed on the canary execution itself (single human operator authorization).

## P1 — Uncharacterized CAS-contention failure

Issue #249 remains open and untouched. Do not weaken one-winner/one-intent assertions,
skip the failure or reclassify it without evidence.

## P1 — PII claim redaction is not full physical erasure

Issue #282 / PR #283 hardens one specific #50 mutation family: PII found in a canonical
fact's **claim**. The privacy contract intentionally sanitizes the affected
`fact_versions.claim` history instead of retaining a recoverable plaintext pre-image,
and records a content-free AuditChain event. That closes the specific risk of the
redaction operation re-persisting its own removed claim in ordinary VersionStore
history.

Residual scope remains explicit. Claim redaction does not prove removal from arbitrary
metadata, immutable/raw origins, every graph/vector/external backend, backups,
third-party systems, or historical logs created by unrelated legacy paths. Full
Art. 17-style physical erasure remains a separate durable-erasure contract. No
certified GDPR/compliance claim follows from PII claim redaction.

Until PR #283 is protected-merged and post-merge verified, this paragraph describes a
review-stage contract, not current `main` implementation truth.

## P1 — Legacy and unrelated risks remain separate

- the historical embeddings-lock timeout remains unresolved evidence;
- remaining #50 archival/causal-relation and any live async mutation-family hardening
  remain separate from PII redaction;
- projection dispatcher lifecycle/observability remains separate;
- no independent security audit, penetration test, certified privacy program or complete
  incident-response rehearsal exists.

## Risk update rule

Use exact states:

```text
IMPLEMENTED
TESTED
WIRED
ENABLEMENT MECHANISM IMPLEMENTED
OBSERVATION MECHANISM IMPLEMENTED
RUNTIME CURRENTLY ENABLED           <- current
OPERATOR AUTHORIZATION PRESENT      <- current
OPERATOR GO                         <- current, single-use grants are exhausted after use
OBSERVED                            <- durable historical evidence, not current state
RUNTIME AUTHORITY                   <- current
PRODUCTION AUTHORITY                <- current
PRODUCTION-READY                    <- never implied by OBSERVED or by 12/12
```

Never infer a later state from an earlier one. Never infer current runtime authority
from historical observation evidence.
