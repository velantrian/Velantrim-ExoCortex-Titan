# 🗺️ Component and Authority Map

**Verified against:** `main@42aa79338c57e9b9a67c3e3c08dd948b60c5541f`  
Use exact SHAs, callers and tests. Presence is not wiring; passing tests are not runtime authority.

## Continuity accepted lineage

| Layer | Merge SHA | Primary surface | Runtime state |
|---|---|---|---|
| R1 contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | `core/continuity/contracts.py` | unwired |
| R2 read-side / threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | event port, bridge, weaver | process-local, unwired |
| R3 projections / WM adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | context, state, Goal/OpenLoop projections | rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | `core/compute_controller.py` | shadow-only, unwired |
| R5A replay / Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | evaluation and advisory shadow | shadow-only, unwired |
| R5B complete runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | `shadow_runner.py` | disabled, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | observations and pure producer | shadow-only, unwired |
| Source-admission contracts | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | `source_admission*.py` | internal, unwired |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | `state_source_adapter.py` | internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | `goal_open_loop.py` | contract correction, unwired |
| OpenLoop subject binding v2 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | `goal_open_loop.py` | contract correction, unwired |
| Goal Draft adapter | `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | `goal_source_adapter.py` | internal, unwired |
| OpenLoop Draft adapter | `42aa79338c57e9b9a67c3e3c08dd948b60c5541f` | `open_loop_source_adapter.py` | internal, unwired |

## Architecture and governance

| Responsibility | Primary surface | Current owner/state |
|---|---|---|
| Accepted admission architecture | `docs/research/CONTINUITY_SOURCE_ADMISSION_ARCHITECTURE.md` | decision and non-authority boundary |
| Canonical current status | `docs/ai/CURRENT_STATE.md` | exact implementation/test/wiring state |
| Risks and required proof | `docs/ai/KNOWN_RISKS.md` | authority, privacy, erasure and operations |
| Current continuation map | `docs/ai/CONTINUITY_SOURCE_ADMISSION_HANDOFF.md` | next bounded slice |
| Merge evidence | `.github/workflows/aggregate-merge-evidence.yml` | active, observed, not required by ruleset |
| Authority-sensitive ownership | `.github/CODEOWNERS` | advisory until branch rules require review |

## Primary neutral contracts

| Responsibility | Code | Authority |
|---|---|---|
| Principal, authorization and source binding | `core/continuity/source_admission.py` | immutable external evidence only |
| Source envelope and observation draft | `core/continuity/source_admission_payloads.py` | proposal evidence only |
| Rejection, admission receipt and authorized batch | `core/continuity/source_admission_decisions.py` | admission evidence only; no runtime permission |

These modules remain internal and are not exported as a live public boundary.

## Source adapter map

### State

| Responsibility | Surface |
|---|---|
| Typed result owner | `core/continuity/state_reconciler.py` |
| Explicit Draft adapter | `core/continuity/state_source_adapter.py` |
| Adversarial tests | `tests/test_continuity_state_source_adapter.py` |

```text
StateReconciliationResult
→ canonical identity verification
→ complete subject-set verification
→ external binding/authorization evidence
→ ContinuitySourceEnvelope
→ bounded ContinuityObservationDraft values
→ STOP
```

### Goal v2

| Responsibility | Surface |
|---|---|
| Snapshot, attestation, projection, decision and result | `core/continuity/goal_open_loop.py` |
| Explicit Draft adapter | `core/continuity/goal_source_adapter.py` |
| Main tests | `tests/test_continuity_goal_open_loop.py` |
| Adapter tests | `tests/test_continuity_goal_source_adapter.py` |

```text
GoalRecordSnapshot.user_id
→ GoalAttestation.user_id
→ GoalProjection.user_id
→ GoalProjectionDecision.user_id
→ GoalProjectionResult.subject_ids
→ complete binding/evidence validation
→ active + attested + included Goal
→ EVIDENCE_COVERAGE_ITEM Draft
→ STOP
```

Completed, cancelled and excluded goals derive no positive Draft. Title, description, priority and keywords grant no importance, reminder, answer, tool, action or compute authority.

### OpenLoop v2

| Responsibility | Surface |
|---|---|
| Signal, resolution, projection and result contracts | `core/continuity/goal_open_loop.py` |
| Explicit Draft adapter | `core/continuity/open_loop_source_adapter.py` |
| Main adversarial suite | `tests/test_continuity_open_loop_source_adapter.py` |
| Receipt chronology regression | `tests/test_continuity_open_loop_source_adapter_receipt_boundary.py` |
| Result `as_of` ownership regression | `tests/test_continuity_open_loop_source_adapter_result_boundary.py` |

```text
OpenLoopSignal.user_id
→ OpenLoopResolution.user_id
→ OpenLoopProjection.user_id
→ OpenLoopProjectionResult.subject_ids
→ projection/result identity recomputation
→ canonical status/reason/time validation
→ complete binding and signal/resolution reference evidence
→ OPEN or OVERDUE
→ EVIDENCE_COVERAGE_ITEM Draft
→ STOP
```

`RESOLVED` and `NOT_YET_OPEN` derive no positive Draft. Deadlines do not authorize reminders, schedules or notification. `related_goal_ref` and `loop_key` are relations, not ownership proof.

The result does not embed the complete original signal/resolution payloads. The adapter therefore recomputes only projection/result identities and requires every signal/resolution ID as bound evidence.

## Common adapter authority boundary

All three adapters:

- validate deterministic source identity and complete subjects;
- require source binding and authorization evidence;
- construct immutable envelope and Draft values;
- stop before admission evaluation;
- do not persist, replay, invoke the signal producer or call runtime composition;
- do not write Canon, ESM, TruthGate, GoalStack or ComputeController;
- do not answer, remind, notify, schedule, call tools or execute actions.

```text
subjects(source result) == subjects(binding receipt)
subjects(source result) ⊆ subjects(authorization context)
```

## Decision ownership

| Concern | Accepted owner | Constraint |
|---|---|---|
| Truth and Canon | existing Canon / TruthGate / promotion paths | no source-admission promotion |
| Hard capability/data policy | `PolicyKernel`, `PolicySnapshot`, `CapabilityLease` | no second policy root |
| Source result | State / Goal / OpenLoop owners | adapter cannot invent source identity |
| Subject binding | typed source contract + source-owner receipt | relations/text/API key are insufficient |
| Source adaptation | deterministic source adapter | proposal transformation only |
| Admission evaluation | **absent** | next bounded slice; must use allowlisted rules and explicit current evidence |
| Current auth/privacy/restriction | accepted external owners not yet integrated | historical receipt is insufficient |
| WorkingMemory disposition | existing `WorkingMemoryGate` | no second disposition owner |
| Final prompt context | existing `ContextPackBuilder` | no direct Draft injection |
| Signal aggregation | existing pure signal producer | bare observations never become live authorization |
| Runtime activation | absent | separate facade, ADR, flag, operator and evidence required |

## Next bounded component: admission evaluator

The next PR may add only an internal deterministic evaluator/rule registry that:

1. accepts one validated envelope and its complete Draft set;
2. resolves an explicitly allowlisted evaluator/rule definition;
3. accepts explicit current decision evidence instead of reading network, environment, DB or wall clock;
4. partitions every Draft into admitted or reason-coded rejected;
5. creates `ContinuityObservationAdmissionReceipt`;
6. may compose `AuthorizedContinuityObservationBatch` only from admitted Drafts and complete receipts;
7. stops before producer invocation or runtime facade.

It must fail closed for missing, stale, unknown, mismatched or non-allowlisted evaluator/rule, policy, authorization, restriction or erasure evidence.

## Still absent

- trusted evaluator/rule registry;
- current principal/tenant/subject resolution;
- consent/lawful-basis verification;
- current restriction and erasure checks;
- durable admission retention/replay/cleanup;
- admission-aware facade and anti-bypass guards;
- `/query`, startup, worker or scheduler wiring;
- feature flag, activation ADR, metrics, SLO, alert and rollback;
- live useful-behavior evidence;
- administrator-enforced branch/ruleset protection.

## Historical status

Earlier stacked PRs and historical handoffs remain provenance only. Current integration targets are exact merged SHAs in this file and `CURRENT_STATE.md`.
