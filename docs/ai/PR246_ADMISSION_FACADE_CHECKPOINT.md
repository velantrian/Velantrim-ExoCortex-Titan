# 🛡️ PR #246 — Internal Admission-Aware Facade Checkpoint

**Status:** `DRAFT · IMPLEMENTED IN OPEN PR · GITHUB_AND_NOTION`  
**Base:** `main@83213048204da0e692abc147fdfad9a326b2b0d6`  
**Exact validated implementation/ADR head before final evidence commit:** `7028b42908d5c4db66947a64f22872107ea2174b`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

## Intent

Add the first internal facade boundary above the pure admission evaluator without creating a live runtime trust boundary.

The facade pins:

- one expected content-addressed evaluator registry;
- one evaluator ID/version and rule ID/version;
- one typed current-decision resolver ID/version;
- exact principal, authorization, tenant, source binding and subject scope;
- explicit evaluation time.

It invokes only the pure evaluator and returns content-addressed evidence.

## Architecture decision

The architecture-freeze gate correctly classified `ContinuityAdmissionFacadePolicy` as an authority-shaped surface. PR #246 includes:

- `docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`.

The ADR establishes:

- the facade owns safe composition and anti-substitution checks only;
- `PolicyKernel` remains the owner of hard capability/locality/data-mode policy;
- existing components remain the owners of identity, authorization, consent, restriction, erasure and current-policy state;
- the pure evaluator remains the owner of deterministic Draft admission;
- no signal-producer, Canon, action, reminder or compute authority is introduced.

```text
facade policy object ≠ PolicyKernel
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted concrete resolver implementation
facade result ≠ runtime permission
```

## Implemented in the open PR

- `core/continuity/admission_facade.py`;
- `ContinuityCurrentDecisionResolver` typed protocol;
- content-addressed `ContinuityAdmissionFacadePolicy`;
- internal `evaluate_continuity_admission_facade(...)`;
- content-addressed `ContinuityAdmissionFacadeResult`;
- adversarial tests in `tests/test_continuity_admission_facade.py`;
- pre-resolution hardening tests in `tests/test_continuity_admission_facade_hardening.py`;
- ADR for the facade ownership boundary.

## Facade path

```text
operator-selected represented facade policy
+ expected registry identity
+ expected resolver identity
+ principal / authorization / source / binding evidence
+ complete structurally valid Draft set
+ explicit evaluated_at
        │
        ▼
registry and resolver identity pinning
cross-contract tenant / subject / receipt checks
Draft duplicate and cross-envelope checks
current-decision resolution through typed protocol
exact principal / authorization / complete-subject coverage check
pure admission evaluator
        │
        ▼
content-addressed facade result
+ deterministic admission receipt
        │
        ▼
STOP
```

## Fail-closed guarantees

The facade rejects when:

- the registry does not match the pinned facade policy;
- evaluator/rule identity is not resolvable in that registry;
- resolver ID/version differs from the pinned policy;
- reading resolver identity fails;
- principal and authorization contexts do not match;
- source envelope and binding receipt do not match;
- tenant or subject scopes are inconsistent;
- source subjects exceed authorization scope;
- Draft IDs are duplicated;
- a Draft references another source envelope;
- the resolver raises an exception;
- the resolver returns an invalid object;
- resolver evidence does not cover the exact principal, authorization, tenant and complete authorization subject set;
- the pure evaluator rejects current state or Draft policy.

Malformed Draft sets are rejected before the facade invokes the external resolver. Resolver identity failures and resolver execution failures are converted to controlled `ContinuitySourceAdmissionError` results.

## Validation history

Initial code/test head `e631d17489805234cd151a38fe894d3c142ec2a6`:

```text
Continuity contracts  31218761535 PASS
Continuity pytest     511 passed
Docker hardening      31218761260 PASS
```

Self-review added pre-resolution structural rejection and controlled resolver identity handling. Hardened code/test head:

```text
a642ccc3b9f022a2167e14e9d0c151afdc0b1f11
```

Code+checkpoint head `24f64db30859122bcc7b735a73458542d088315e`:

```text
Continuity contracts  31219127190 PASS · 514 passed
Docker hardening      31219127155 PASS
Full Titan CI         31219127212 FAILED at architecture freeze
```

The failure was not a runtime/test defect. The freeze guard required a concrete ADR for the new authority-shaped facade policy. The guard was not bypassed or weakened.

After adding the ADR, exact head `7028b42908d5c4db66947a64f22872107ea2174b` passed:

```text
Full Titan CI + coverage  31219414919 PASS
Continuity contracts      31219414942 PASS
Docker hardening          31219417341 PASS
Architecture freeze       PASS with concrete ADR
Repository guards         PASS
Machine-readable state    PASS
Portable KB integrity     PASS
Ruff                       PASS
Blocking mypy              PASS
Full pytest                PASS
Coverage ratchet ≥74%      PASS
Unresolved review threads  0
```

This documentation evidence commit requires one final exact-head rerun before Ready/merge.

## Explicit non-scope

- no real principal/authentication provider integration;
- no concrete authorization, consent/lawful-basis, restriction, erasure or policy resolver implementation;
- no signal-producer invocation;
- no live `AuthorizedContinuityObservationBatch` use;
- no persistence, replay, retention or cleanup lifecycle;
- no public package export;
- no `/query`, startup, worker or scheduler wiring;
- no feature flag, SLO, monitoring, rollback, activation ADR or Operator GO;
- no Canon, ESM, TruthGate, GoalStack or ComputeController mutation;
- no answer, reminder, notification, delivery, tool or action effect.

## Status effect after merge

Current `main` remains `6/12 = 50.0%`.

Only after final exact-head validation, review, GitHub/Notion synchronization and merge may the internal facade capability advance canonical implementation readiness to `7/12 = 58.3%`.

`WIRED`, `ENABLED`, `OBSERVED` and runtime authority remain false. Concrete trusted resolver integration remains a separate incomplete category.

## Next safe slice after merge

Implement accepted current-decision resolver composition without runtime wiring:

- principal/authentication evidence owner;
- authorization owner;
- consent or lawful-basis owner;
- restriction owner;
- erasure-domain owner;
- current `PolicySnapshot` compatibility owner;
- complete multi-subject fail-closed aggregation.

Concrete resolver integration must remain internal and must not invoke the signal producer, persist admission artifacts or alter user-visible behavior.

## Documentation synchronization

```text
Documentation impact:   GITHUB_AND_NOTION
Notion access:           AVAILABLE
Notion target:           Continuity Source Admission — Architecture
Notion synchronization: SYNCED
```

Final exact head, final CI, review state and merge SHA must be recorded after the final rerun and merge.
