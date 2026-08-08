# 🔐 Continuity Source Admission — Current Hand-off

**Verified:** 2026-08-08  
**Repository head at verification:** `c14916214a920802c9ce6187be79ebe74ddfadfc`  
**Implementation baseline:** `9f07db6de8d32683d00bfe4f1673e84493607553` (PR #246)  
**Status:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Continuity readiness:** `7/12 = 58.3%`

## Current accepted state

```text
accepted architecture                         ✅
seven primary immutable evidence contracts    ✅
State Draft adapter                            ✅
Goal subject identity + Draft adapter          ✅
OpenLoop subject identity + Draft adapter      ✅
pure admission evaluator + allowlist registry ✅
internal admission-aware facade                ✅
concrete current-decision resolver composition ❌
durable lifecycle                              ❌
runtime wiring                                 ❌
enablement / Operator GO                       ❌
live observed evidence                         ❌
```

## Latest implementation checkpoint

PR #246 merged as `9f07db6de8d32683d00bfe4f1673e84493607553` from exact tested head `ec2966ed336ba619e987dfc1e99d45fdf87907b5`.

```text
Full Titan CI + coverage  31219904698 PASS on attempt 2, unchanged SHA
Continuity contracts      31219904684 PASS · 514 passed
Docker hardening          31219904770 PASS
Aggregate merge evidence  31221208768 SUCCESS
Review threads             0
```

Attempt 1 of the Full Titan run retained one existing SQLite recovery timeout in `test_drop_legacy_embeddings_lock_owner_process_is_bounded`; coverage passed. Attempt 2 on the unchanged SHA passed. The timeout remains risk evidence and is not attributed to the facade.

The architecture-freeze guard initially required a concrete ADR for the authority-shaped facade policy. PR #246 added `docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`; the guard was not bypassed.

## PR #247 docs checkpoint

PR #247 merged as `294bdfa6a77097e48310872a2e3fae811e8c2c9e`.

```text
Full Titan CI + coverage  31222680496
  Attempt 1:              FAILED · test_cas_contention[25] · BrokenBarrierError
  Attempt 2:              PASS · 3746 passed, 17 skipped, 1 xfailed
Aggregate push evidence  31222680550 SUCCESS
Review threads             0
Checkpoint               docs/ai/PR247_ADMISSION_FACADE_POSTMERGE_CHECKPOINT.md (FINAL)
```

The attempt-1 failure is an uncharacterized CAS-contention test failure
(`BrokenBarrierError`). Stage-based harness work is diagnostic only
(issue #249 / draft PR #250). It is separate from the legacy embeddings-lock timeout on
PR #246 run `31219904698` and from historical fresh-bootstrap ADD COLUMN races.

## Accepted facade boundary

```text
operator-selected represented facade policy
+ exact registry/evaluator/rule identity
+ exact resolver identity
+ complete SourceEnvelope and Draft set
+ binding and authorization evidence
+ explicit evaluated_at
        │
        ▼
structural and cross-contract validation
current-decision resolution through typed protocol
complete exact-subject compatibility
pure admission evaluator
        │
        ▼
content-addressed facade result
+ deterministic admission receipt
        │
        ▼
STOP
```

Implemented facade surfaces:

- `ContinuityAdmissionFacadePolicy`;
- `ContinuityCurrentDecisionResolver` protocol;
- `evaluate_continuity_admission_facade(...)`;
- `ContinuityAdmissionFacadeResult`.

## What the facade proves

- supplied facade-policy, registry, evaluator/rule and resolver identities match expected represented values;
- source envelope, binding, authorization and Drafts have consistent principal, tenant and subject scope;
- Draft IDs are unique and reference the same source envelope;
- malformed Draft sets are rejected before external resolver access;
- resolver identity/access/execution failures become controlled fail-closed errors;
- returned current-decision evidence covers the exact principal, authorization, tenant and complete subject set;
- only the pure evaluator is invoked;
- output is deterministic, content-addressed and evidence-only.

## What it does not prove

- that facade policy or registry was selected by an approved deployment owner;
- that a concrete resolver implementation is authentic or authoritative;
- that identity, authorization, consent, restriction, erasure or policy evidence was obtained from accepted owners;
- that producer invocation, persistence or runtime use is permitted;
- that any answer, reminder, delivery, tool, action, Canon write or compute decision is allowed.

```text
facade policy object ≠ PolicyKernel
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted concrete resolver implementation
facade result ≠ runtime permission
```

## Next bounded implementation slice

Implement **concrete current-decision resolver composition through accepted owners only**.

### Required owner inputs

- operator/deployment-selected facade-policy and registry identity;
- principal/authentication evidence from the accepted identity boundary;
- tenant and subject authorization evidence;
- consent or lawful-basis evidence;
- restriction evidence;
- erasure-domain evidence;
- current `PolicySnapshot` compatibility evidence;
- explicit evaluation time.

### Required behavior

1. Reuse accepted owners; do not create a second PolicyKernel, identity system or erasure registry.
2. Bind the expected facade-policy and registry identity outside caller-controlled payloads.
3. Aggregate the complete exact subject set.
4. Reject missing, stale, unknown, contradictory or partially covered evidence.
5. Construct valid `ContinuityCurrentDecisionEvidence`.
6. Invoke the merged internal facade.
7. Return evidence-only output.
8. Stop.

### Explicit non-scope

- no signal-producer invocation;
- no persistence, replay or retention store;
- no public package export;
- no `/query`, startup, worker or scheduler registration;
- no feature flag or activation;
- no Canon, ESM, TruthGate, GoalStack or compute mutation;
- no answer, reminder, notification, delivery, tool or action effect.

## Multi-subject rule

```text
subjects(source result)
== subjects(binding receipt)
⊆ subjects(authorization)
== subjects(current-decision aggregation)
```

If one subject is blocked, erased, unknown, conflicting or missing, reject the complete evaluation. Silent filtering is forbidden.

## Current global blockers

- branch ruleset not administrator-enforced; issue #234;
- no deployment-selected facade-policy/registry trust root;
- no accepted concrete current-state resolver composition;
- no durable admission-artifact lifecycle;
- no runtime activation governance;
- query-path read-only and Canon writer unification remain open;
- uncharacterized CAS-contention test failure requires characterization (issue #249 / draft PR #250);
- intermittent legacy SQLite lock-owner recovery timeout requires characterization;
- independent security audit and compliance program remain absent.

## Documentation and Notion

- PR #246 checkpoint: `docs/ai/PR246_ADMISSION_FACADE_CHECKPOINT.md`;
- PR #247 checkpoint: `docs/ai/PR247_ADMISSION_FACADE_POSTMERGE_CHECKPOINT.md` (FINAL);
- facade ADR: `docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`;
- Notion record: `🔐 Continuity Source Admission — Architecture`;
- Notion status: SYNCED — FINAL correction verified on Continuity Source Admission page (2026-08-08);

## Re-entry checklist

Before starting resolver composition:

1. re-read `AGENTS.md` and `docs/ai/README.md`;
2. verify current `main`, open PRs and post-merge CI;
3. inspect facade policy, resolver protocol, evaluator and adversarial tests;
4. map every evidence field to an accepted owner;
5. define exact failure semantics for missing/unknown/conflicting state;
6. preserve the complete subject set;
7. keep the PR internal, unwired and evidence-only;
8. synchronize GitHub and Notion in the same work cycle;
9. require exact-head CI, Continuity, Docker when applicable, aggregate success and zero unresolved threads.
