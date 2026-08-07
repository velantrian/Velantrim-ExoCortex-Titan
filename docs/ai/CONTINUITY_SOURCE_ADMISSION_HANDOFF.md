# 🔐 Continuity Source Admission — Current Hand-off

**Verified:** 2026-08-07  
**Current implementation `main`:** `97fe27a37184c6c7277f54e96acd04d98d583ab3`  
**Status:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Continuity readiness:** `6/12 = 50.0%`

## Current accepted state

```text
accepted architecture                         ✅
seven primary immutable evidence contracts    ✅
State Draft adapter                            ✅
Goal subject identity + Draft adapter          ✅
OpenLoop subject identity + Draft adapter      ✅
pure admission evaluator + allowlist registry ✅
trusted current-state resolver boundary        ❌
admission-aware facade                         ❌
durable lifecycle                              ❌
runtime wiring                                 ❌
enablement / Operator GO                       ❌
live observed evidence                         ❌
```

## Latest implementation checkpoint

PR #244 merged as `97fe27a37184c6c7277f54e96acd04d98d583ab3` from exact tested head `52fdc9b0ef0ff7833c091a64c35d0754874cedb8`.

```text
Full Titan CI + coverage  31215957409 PASS
Continuity contracts      31215957406 PASS · 502 passed
Docker hardening          31215957402 PASS
Aggregate merge evidence  31216560826 SUCCESS
Review threads             0
```

The initial evaluator test head produced one failure because a test fixture created a Draft earlier than its SourceEnvelope. The existing production contract correctly rejected the invalid chronology. The fixture was corrected without weakening validation; the final exact head passed all required gates.

## Accepted evaluator boundary

```text
SourceEnvelope + complete Draft set
+ exact binding and authorization evidence
+ explicit current-decision evidence
+ exact evaluator/rule identity
+ immutable registry
+ explicit evaluated_at
        │
        ▼
pure deterministic evaluation
        │
        ▼
complete admitted/rejected partition
+ ContinuityObservationAdmissionReceipt
        │
        ▼
STOP
```

Implemented evidence types:

- `ContinuityAdmissionRuleDefinition`;
- `ContinuityAdmissionEvaluatorDefinition`;
- `ContinuityAdmissionRegistry`;
- `ContinuityCurrentDecisionEvidence`;
- `ContinuityAdmissionReason`;
- `ContinuityAdmissionEvaluationResult`.

## What the evaluator proves

- exact evaluator/rule definitions resolve inside the supplied registry;
- registry and evidence contents match their content-addressed IDs;
- current-decision evidence exactly matches authorization context;
- explicit validity intervals include `evaluated_at`;
- authorization and lawful basis are represented as active;
- restriction and erasure are represented as clear;
- source type, adapter, purpose, data mode and retention are allowed;
- derivation rule, signal type, confidence and age satisfy the selected rule;
- every Draft is admitted or rejected exactly once;
- output is deterministic and evidence-only.

## What it does not prove

- that the registry is the operator-approved trusted registry;
- that the current-state resolver was authentic;
- that an authentication receipt is valid outside represented evidence;
- that current policy/consent/restriction/erasure sources are authoritative;
- that the receipt may be used at runtime;
- that producer invocation, persistence, reminders, actions or answers are allowed.

```text
content-addressed registry ≠ trusted runtime root
current evidence ≠ authenticated resolver
receipt ≠ runtime permission
```

## Next bounded implementation slice

Implement an internal **admission-aware facade and resolver boundary only**.

### Required inputs

- operator-selected expected registry identity;
- complete source envelope and Draft set;
- binding and authorization contexts;
- typed principal resolver;
- typed authorization resolver;
- typed consent/lawful-basis resolver;
- typed restriction resolver;
- typed erasure resolver;
- typed current-policy resolver;
- explicit evaluation time.

### Required behavior

1. Verify that the supplied registry matches the operator-selected expected identity.
2. Resolve current state through typed protocols owned by accepted components.
3. Aggregate the complete exact subject set fail-closed.
4. Reject missing, stale, unknown, contradictory or partially covered evidence.
5. Construct `ContinuityCurrentDecisionEvidence`.
6. Invoke the pure evaluator.
7. Return evidence-only receipt and optional authorized-batch proposal.
8. Stop.

### Explicit non-scope for the next slice

- no signal-producer invocation;
- no persistence or replay store;
- no public export;
- no `/query`, startup, worker or scheduler registration;
- no feature flag or activation;
- no Canon, ESM, TruthGate, GoalStack or compute mutation;
- no answer, reminder, notification, delivery, tool or action effect.

## Multi-subject rule

A facade must preserve the complete subject set:

```text
subjects(source result)
== subjects(binding receipt)
⊆ subjects(authorization)
== subjects(current-decision aggregation)
```

If one subject is blocked, erased, unknown or missing, the facade rejects the complete evaluation. Silent filtering is forbidden.

## Current global blockers

- branch ruleset not administrator-enforced; issue #234;
- no trusted registry selection owner;
- no accepted live current-state resolver integration;
- no durable lifecycle;
- no runtime activation governance;
- query path read-only and Canon writer unification remain open global hardening work;
- independent security audit and compliance program remain absent.

## Documentation and Notion

- PR #244 checkpoint: `docs/ai/PR244_ADMISSION_EVALUATOR_CHECKPOINT.md`;
- Notion record: `🔐 Continuity Source Admission — Architecture`;
- Notion status: synchronized with merge `97fe27a37184c6c7277f54e96acd04d98d583ab3`;
- canonical docs checkpoint: `docs/continuity-admission-evaluator-checkpoint`.

## Re-entry checklist

Before starting the facade PR:

1. re-read `AGENTS.md` and `docs/ai/README.md`;
2. verify current `main` and open PRs;
3. inspect evaluator contracts and tests;
4. identify accepted resolver owners rather than duplicating policy/identity logic;
5. define exact failure semantics for missing/unknown/conflicting evidence;
6. keep the PR internal, unwired and evidence-only;
7. synchronize GitHub and Notion in the same work cycle;
8. require exact-head CI, Continuity, Docker when applicable, aggregate success and zero unresolved threads.
