# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-10  
**Repository checkpoint:** `main@456b762b1e752a2f5fb22762869336be9fed42a4`  
**Continuity:** `11/12 = 91.7%` implementation readiness (unchanged by this checkpoint)  
**Runtime:** `CONTROLLED-ENABLEMENT + OBSERVATION MECHANISMS WIRED · CURRENTLY DISABLED · OPERATOR GO ABSENT · NOT OBSERVED · NO RUNTIME AUTHORITY · BLOCKED_ON_OPERATOR_GO`  
**Governance:** active `main-governance` · solo mode · approvals `0`

A canonical manifest, persisted decision, persisted observation evidence, green
aggregate or Notion update does not prove operator authenticity, current permission,
observation or production authority.

## Closed or materially reduced

- controlled enablement now has one explicit deployment-owned decision contract;
- exact schema, canonical JSON and SHA-256 integrity are validated;
- decisions bind to exact configuration, lifecycle owner/version, tenant, content-free
  storage identity and one internal scope;
- enable leases are finite; disable decisions are explicit and monotonic;
- duplicate decisions are idempotent; stale/conflicting decisions fail closed;
- concurrent enable/disable converges through serialized in-process application and
  SQLite uniqueness constraints;
- decision evidence remains in the existing tenant-bound SQLite database;
- persisted evidence is revalidated and is never restart permission;
- runtime configuration without a current enable decision stays disabled;
- only existing explicit append/replay methods are gated;
- `/query`, producer and all forbidden side effects remain absent;
- a bounded, content-free **observation mechanism** now exists (PR #276): it can
  record deterministic evidence of configuration/storage/owner binding stability,
  lease validity while enabled, and absence of runtime/side-effect authority, and can
  reduce a session to one deterministic `rollback_verified` result — proven with a
  synthetic operator decision in 34 focused/adversarial tests.

The former risk “controlled-enablement mechanism is absent” is closed only at the bounded
implementation/test/wiring level. The former risk “no observation mechanism exists at
all” is likewise closed only at the implementation/test/wiring level — see the P0 risk
below for what remains open.

## P0 — No current Operator GO or deployed activation

No activation manifest is committed or supplied by this repository checkpoint.
`runtime currently enabled=false`, `operator authorization present=false`, and
`operator_go=false`.

Before any real deployment may enable the runtime, an operator must provide a current
exact decision through deployment-owned controls and independently establish the
identity/authority of that operator. Manifest SHA-256 proves integrity, not authenticity.

## P0 — Concrete live current-decision owner adapters remain unselected

The six current-decision ports still have no accepted live deployment adapters for
principal, authorization, consent/lawful basis, restriction, erasure and PolicySnapshot.
Controlled enablement does not replace those owners.

Required proof before any side-effect-capable producer:

- authentic owner APIs and deployment identities;
- bounded current-state reads and configuration lineage;
- adversarial tests against accepted owner stores;
- current restriction/erasure/authorization rechecks;
- explicit operator decision under deployment governance.

## P0 — Real observed evidence is BLOCKED_ON_OPERATOR_GO

No production deployment, traffic, telemetry, monitoring, alerting or observed user
behavior exists. This is the final separate Continuity capability. Neither the
controlled-enablement mechanism (PR #273) nor the bounded-observation mechanism (PR
#276) implies it: a mechanism that *can* record evidence is not evidence.

Producing real `observed=true` evidence requires an actual operator-authorized bounded
activation against a real deployment — a committed activation manifest, an operator
whose identity/authority is independently established outside this repository, and
someone running the observation session against that real activation. None of that
exists in this repository checkpoint, and an AI agent has no authority to self-issue
Operator GO on its own initiative.

**Status: `BLOCKED_ON_OPERATOR_GO`.** Tracking issue #275 remains open until this is
resolved; it must not be closed as completing Continuity 12/12 on mechanism evidence
alone.

## P1 — Operational scope remains bounded

Not proved:

- multi-process decision contention;
- live crash recovery, backup/restore or disaster recovery;
- disk-full and filesystem-permission behavior in production;
- external audit service, SLO/SLA, alerting or rollback orchestration;
- public multi-user rollout.

## P1 — Solo governance has no independent approval gate

PR #273 and PR #276 each had zero submitted reviews. Codex did not run on either because
its usage limit was reached. Unresolved review threads were zero on both. Independent
review is **NOT CLAIMED**.

## P1 — Uncharacterized CAS-contention failure

Issue #249 remains open and untouched. Do not weaken one-winner/one-intent assertions,
skip the failure or reclassify it without evidence.

## P1 — Legacy and unrelated risks remain separate

- the historical embeddings-lock timeout remains unresolved evidence;
- legacy query/promotion hardening remains separate;
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
RUNTIME CURRENTLY ENABLED
OPERATOR AUTHORIZATION PRESENT
OPERATOR GO
OBSERVED
PRODUCTION-AUTHORITATIVE
```

Never infer a later state from an earlier one.
