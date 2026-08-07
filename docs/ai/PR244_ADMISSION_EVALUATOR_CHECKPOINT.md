# 🔐 PR #244 — Pure Continuity Admission Evaluator Checkpoint

**Status:** `DRAFT · IMPLEMENTED IN OPEN PR · GITHUB_AND_NOTION`  
**Base:** `main@2655ecabab400dda4b350ed90142510cf5a4f49c`  
**Initial implementation head:** `ddf2b03b53e80ca7e9156ee17fa1de29f883730c`  
**Current code/test head before documentation:** `e064e9b36c3a647200353bfe5cb4fa2a269f0482`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

## Intent

Implement the next bounded Continuity source-admission capability without creating a
runtime trust boundary: immutable evaluator/rule definitions, an explicit allowlist
registry, explicit current-decision evidence and a pure deterministic Draft partition.

## Implemented in the open PR

- `core/continuity/admission_evaluator.py`;
- content-addressed `ContinuityAdmissionRuleDefinition`;
- content-addressed `ContinuityAdmissionEvaluatorDefinition`;
- immutable `ContinuityAdmissionRegistry`;
- content-addressed `ContinuityCurrentDecisionEvidence`;
- stable `ContinuityAdmissionReason` codes;
- pure `evaluate_continuity_admission(...)`;
- evidence-only `ContinuityAdmissionEvaluationResult`;
- adversarial tests in `tests/test_continuity_admission_evaluator.py`.

## Decision path

```text
validated SourceEnvelope + complete Draft set
+ exact evaluator ID/version
+ exact rule ID/version
+ immutable registry resolution
+ explicit current principal/authorization/purpose/policy/privacy evidence
+ explicit evaluated_at
→ deterministic complete admitted/rejected partition
→ ContinuityObservationAdmissionReceipt
→ STOP
```

## Fail-closed checks

The evaluator rejects or refuses evaluation for:

- unknown or non-allowlisted evaluator/rule pairs;
- evaluator-specific rule mismatch;
- current evidence that does not exactly match the authorization context;
- stale or future current-decision evidence;
- expired/withdrawn authorization;
- inactive lawful basis or consent;
- blocked or unknown restriction state;
- blocked or unknown erasure state;
- unsupported source type or source adapter;
- unsupported derivation rule or signal type;
- wrong purpose, data-handling mode or retention class;
- low-confidence or stale Drafts;
- duplicate Draft IDs, cross-envelope Drafts and malformed inputs.

## Trust boundary

The registry and current-decision evidence are content-addressed evidence. Their presence
does not establish a trusted runtime owner. A later admission-aware facade/operator
configuration must select the accepted registry and obtain current evidence from accepted
identity, authorization, consent, restriction, erasure and policy owners.

```text
content-addressed registry ≠ operator-selected trusted registry
current-decision evidence object ≠ proof that its external resolver is trusted
valid receipt ≠ runtime permission
```

For a multi-subject authorization, current status applies to the complete exact subject
set. A future resolver must aggregate per-subject state fail-closed; it may not silently
filter a blocked or erased subject.

## Validation evidence

Initial head `ddf2b03...`:

- Ruff PASS;
- blocking mypy PASS;
- Continuity: `503 passed, 1 failed`;
- failure cause: the test attempted to construct a Draft earlier than its SourceEnvelope,
  which the existing payload contract correctly rejected before evaluator execution.

Corrected head `e064e9b...`:

- invalid test chronology removed without weakening production validation;
- stale behavior is now tested with a valid Draft and a stricter bounded-age rule;
- Continuity contracts run `31215677370` PASS;
- Docker hardening run `31215677760` PASS;
- full Titan CI/coverage run `31215677563` pending at the time of this checkpoint.

The first failed test run remains visible and is not described as an infrastructure or
production-code failure.

## Explicit non-scope

- no current-state resolver or external identity/provider integration;
- no signal-producer invocation;
- no `AuthorizedContinuityObservationBatch` live consumer;
- no admission-aware facade or anti-bypass guard;
- no persistence, retention, replay or cleanup lifecycle;
- no public package export;
- no `/query`, startup, worker or scheduler wiring;
- no feature flag, SLO, alert, rollback, activation ADR or Operator GO;
- no Canon, ESM, TruthGate, GoalStack or ComputeController mutation;
- no answer, reminder, notification, delivery, tool, action or compute-route authority.

## Status effect after merge

Only after exact-head validation, review, GitHub/Notion synchronization and merge may the
bounded evaluator capability advance the Continuity readiness score from:

```text
5/12 = 41.7%
```

to:

```text
6/12 = 50.0%
```

`WIRED`, `ENABLED`, `OBSERVED` and runtime authority remain false.

## Next safe slice after merge

The next slice must not jump directly to `/query` or user-visible behavior. It should
define an internal admission-aware facade that:

1. accepts only complete authorized evidence, never bare Drafts/observations;
2. resolves the operator-selected evaluator registry;
3. obtains current principal/authorization/privacy/policy evidence from accepted owners;
4. invokes the pure evaluator;
5. optionally constructs an evidence-only authorized batch;
6. stops before signal producer invocation and any runtime/user-visible effect.

Current-state owner integrations, durable persistence, runtime wiring and activation
remain separate later decisions.

## Documentation synchronization

```text
Documentation impact:   GITHUB_AND_NOTION
Notion access:           AVAILABLE
Notion target:           Continuity Source Admission — Architecture
Notion synchronization: DRAFT CHECKPOINT REQUIRED
```

Final exact head, final CI, review status and merge SHA must be added after they exist.
