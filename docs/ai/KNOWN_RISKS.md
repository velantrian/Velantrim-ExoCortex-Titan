# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-09  
**Repository checkpoint:** `main@802e833fa251a8831add8a6b802a5ebb57533549`  
**Continuity:** `10/12 = 83.3%` implementation readiness  
**Runtime:** `WIRED INTERNALLY · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Governance:** active `main-governance` · solo mode · approvals `0`

A merged implementation, durable receipt, successful replay, green aggregate or Notion
update does not grant permission, authenticity, enablement or production authority.

## Closed or materially reduced

- one deployment-owned internal composition boundary now exists;
- owner identity/version are exact and unknown values fail closed;
- SQLite location is derived internally from a canonical absolute storage root;
- caller-selected database path, owner and tenant substitution are rejected;
- startup/shutdown are deterministic, idempotent and restartable;
- concurrent startup creates one logical initialization;
- only complete facade-bound accepted evidence can enter persistence;
- append/replay failures and incompatible schema propagate fail closed;
- `/query`, producer, Canon, ESM, TruthGate, GoalStack, reminder, notification, action and
  tool side effects remain absent;
- post-merge full CI, Continuity, Docker and aggregate push evidence are green.

The former risk “runtime wiring is absent” is closed only at the bounded internal
implementation/test level.

## P0 — Controlled enablement and Operator GO are absent

Internal wiring does not authorize use. No feature enablement, activation policy,
Operator GO, rollout, rollback, SLO, alert or user-facing capability exists.

Required proof before 11/12:

- separate enablement decision and owner;
- explicit Operator GO;
- current authorization/restriction/erasure rechecks;
- bounded rollout and rollback semantics;
- metrics and fail-closed operational controls;
- proof that disabled remains the default.

## P0 — Concrete live decision-owner adapters are not selected

The six current-decision ports still have no accepted live deployment adapters for
principal, authorization, consent/lawful basis, restriction, erasure and PolicySnapshot.
The new lifecycle owner does not replace them.

Required proof:

- authentic accepted owner APIs and deployment identities;
- bounded current-state reads and configuration lineage;
- adversarial tests against real owner stores;
- explicit Operator decision before activation.

## P1 — Integrity is not authenticity or permission

```text
Hash integrity ≠ authentic provenance
Stored evidence ≠ current permission
Replay success ≠ authorization
Accepted admission ≠ action permission
Runtime wiring ≠ enablement
```

Current permission can become stale after storage. A future producer must re-evaluate the
accepted current owner state rather than treating an artifact as a token.

## P1 — Recovery remains bounded and internal

Proved: after clean restart, the owner can revalidate configuration/schema and perform
explicit exact-scope replay.

Not proved:

- live crash recovery;
- backup/restore or disaster recovery;
- multi-process deployment contention;
- disk-full and filesystem-permission behavior in production;
- automatic self-healing;
- SLO/SLA or observed operational recovery.

## P1 — No live observation

No production deployment, traffic, monitoring, alerting or observed user behavior exists.
This is the final separate Continuity capability after controlled enablement.

## P1 — Solo governance has no independent approval gate

PR #270 had zero submitted reviews. Codex did not run because its usage limit was reached.
Unresolved review threads were zero, but independent review is **NOT CLAIMED**.

## P1 — Uncharacterized CAS-contention failure

Issue #249 remains open and untouched. Do not weaken one-winner/one-intent assertions,
skip the failure or reclassify it without evidence.

## P1 — Legacy embeddings-lock timeout

The historical first-attempt timeout in PR #246 remains unresolved risk evidence. It is
outside this block.

## P1 — Query/Canon ownership and projection lifecycle

Legacy query/promotion hardening and projection dispatcher lifecycle/observability remain
separate work. This bounded Continuity composition does not alter those paths.

## P1 — Security and deployment

No independent security audit, penetration test, certified privacy program, public
multi-user deployment proof or complete incident-response rehearsal exists.

## Risk update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.
Never collapse these states or infer authority from a green check.
