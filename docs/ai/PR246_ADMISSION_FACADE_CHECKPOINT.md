# 🛡️ PR #246 — Internal Admission-Aware Facade Checkpoint

**Status:** `DRAFT · IMPLEMENTED IN OPEN PR · GITHUB_AND_NOTION`  
**Base:** `main@83213048204da0e692abc147fdfad9a326b2b0d6`  
**Current exact code/test head before documentation:** `e631d17489805234cd151a38fe894d3c142ec2a6`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

## Intent

Add the first internal facade boundary above the pure admission evaluator without
creating a live runtime trust boundary.

The facade pins:

- one expected content-addressed evaluator registry;
- one evaluator ID/version and rule ID/version;
- one typed current-decision resolver ID/version;
- exact principal, authorization, tenant, source binding and subject scope;
- explicit evaluation time.

It then invokes only the pure evaluator and returns content-addressed evidence.

## Implemented in the open PR

- `core/continuity/admission_facade.py`;
- `ContinuityCurrentDecisionResolver` typed protocol;
- content-addressed `ContinuityAdmissionFacadePolicy`;
- internal `evaluate_continuity_admission_facade(...)`;
- content-addressed `ContinuityAdmissionFacadeResult`;
- adversarial tests in `tests/test_continuity_admission_facade.py`.

## Facade path

```text
operator-selected represented facade policy
+ expected registry identity
+ expected resolver identity
+ principal / authorization / source / binding evidence
+ complete Draft set
+ explicit evaluated_at
        │
        ▼
registry and resolver identity pinning
cross-contract tenant / subject / receipt checks
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

The facade rejects before or during evaluation when:

- the registry does not match the pinned facade policy;
- evaluator/rule identity is not resolvable in that registry;
- resolver ID/version differs from the pinned policy;
- principal and authorization contexts do not match;
- source envelope and binding receipt do not match;
- tenant or subject scopes are inconsistent;
- source subjects exceed authorization scope;
- the resolver raises an exception;
- the resolver returns an invalid object;
- resolver evidence does not cover the exact principal, authorization, tenant and
  complete authorization subject set;
- the pure evaluator rejects current state or Draft policy.

Resolver exceptions are converted to a controlled
`ContinuitySourceAdmissionError("current decision resolver failed closed")`.

## Important trust boundary

The facade policy is content-addressed represented evidence. This module does not choose
or activate itself as trusted deployment configuration.

The typed resolver protocol defines the boundary but does not implement a real identity,
authorization, consent, restriction, erasure or policy source.

```text
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted resolver implementation
facade result ≠ runtime permission
```

A future deployment composition must own policy selection and concrete resolvers.

## Exact-head validation so far

For code/test head `e631d17489805234cd151a38fe894d3c142ec2a6`:

```text
Continuity contracts  31218761535 PASS
Ruff                  PASS
blocking mypy         PASS
Continuity pytest     511 passed
Docker hardening      31218761260 PASS
Full Titan CI         31218761239 running at checkpoint creation
```

## Explicit non-scope

- no real principal/authentication provider integration;
- no concrete authorization, consent/lawful-basis, restriction, erasure or policy
  resolver implementation;
- no signal-producer invocation;
- no live `AuthorizedContinuityObservationBatch` use;
- no persistence, replay, retention or cleanup lifecycle;
- no public package export;
- no `/query`, startup, worker or scheduler wiring;
- no feature flag, SLO, monitoring, rollback, activation ADR or Operator GO;
- no Canon, ESM, TruthGate, GoalStack or ComputeController mutation;
- no answer, reminder, notification, delivery, tool or action effect.

## Status effect after merge

Current `main` remains:

```text
6/12 = 50.0%
```

Only after exact-head validation, review, GitHub/Notion synchronization and merge may the
internal facade capability advance the canonical implementation readiness to:

```text
7/12 = 58.3%
```

`WIRED`, `ENABLED`, `OBSERVED` and runtime authority remain false. Concrete trusted
resolver integration remains a separate incomplete category.

## Next safe slice after merge

The next engineering slice should implement accepted **current-decision resolver
composition** without wiring it into runtime:

- principal/authentication evidence owner;
- authorization owner;
- consent or lawful-basis owner;
- restriction owner;
- erasure-domain owner;
- current PolicySnapshot compatibility owner;
- complete multi-subject fail-closed aggregation.

Concrete resolver integration must remain internal and must not invoke the signal
producer, persist admission artifacts or alter user-visible behavior.

## Documentation synchronization

```text
Documentation impact:   GITHUB_AND_NOTION
Notion access:           AVAILABLE
Notion target:           Continuity Source Admission — Architecture
Notion synchronization: DRAFT CHECKPOINT REQUIRED
```

Final exact head, final CI, review state and merge SHA must be recorded when available.
