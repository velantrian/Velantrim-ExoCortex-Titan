# 🗺️ Component and Authority Map

**Repository head verified:** `main@97fe27a37184c6c7277f54e96acd04d98d583ab3`  
**Implementation baseline:** `97fe27a37184c6c7277f54e96acd04d98d583ab3`  
**Machine-readable state:** [`docs/state/project_state.json`](../state/project_state.json)  
**Rule:** presence is not wiring; content-addressed evidence is not runtime authority.

## 1. Canon and core runtime

| Responsibility | Primary owner | State | Authority |
|---|---|---|---|
| Durable facts and ESM | `core/memory.py` / canonical store services | implemented, tested, wired | Canon state owner |
| Truth admission | `core/truth_gate.py`, accepted write services | implemented, tested, partly unified | evidence/confidence decision |
| Hard capability/data-mode policy | `core/policy_kernel.py` / `PolicySnapshot` / `CapabilityLease` | implemented, tested | policy owner |
| Provenance and audit | `core/provenance_chain.py`, `core/audit_chain.py` | implemented, tested | trace and mutation evidence |
| Retrieval coordination | `core/pipeline.py`, `core/hybrid_retriever.py` | implemented, wired | read-side proposal only |
| Projection delivery | projection outbox / dispatcher primitives | implemented, tested, not lifecycle-wired | rebuildable derived state |

No Continuity component owns Canon, TruthGate, PolicyKernel, GoalStack, reminders, tools, actions or compute routing.

## 2. Continuity accepted lineage

| Layer | Merge SHA | Primary surface | Runtime state |
|---|---|---|---|
| R1 immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | `core/continuity/contracts.py` | tested, unwired |
| R2 read-side / threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | `event_port.py`, `conversation_bridge.py`, `thread_weaver.py` | process-local, unwired |
| R3 projections / WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | `context_pack.py`, `state_reconciler.py`, `goal_open_loop.py` | rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | `core/compute_controller.py` | shadow-only, unwired |
| R5A replay / Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | `evaluation.py`, `advisory_shadow.py` | shadow-only, unwired |
| R5B disabled runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | `shadow_runner.py` | default-off, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | `observations.py`, `signal_producer.py` | pure shadow producer |
| Producer hardening | `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | producer validation | tested, unwired |
| Source-admission contracts | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | `source_admission*.py` | evidence only |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | `state_source_adapter.py` | tested, internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | `goal_open_loop.py` | tested contract correction |
| OpenLoop subject binding v2 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | `goal_open_loop.py` | tested contract correction |
| Goal Draft adapter | `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | `goal_source_adapter.py` | tested, internal, unwired |
| OpenLoop Draft adapter | `42aa79338c57e9b9a67c3e3c08dd948b60c5541f` | `open_loop_source_adapter.py` | tested, internal, unwired |
| Admission evaluator | `97fe27a37184c6c7277f54e96acd04d98d583ab3` | `admission_evaluator.py` | tested, internal, unwired |

## 3. Source-admission contracts

### Primary evidence contracts

| Responsibility | Code | Authority |
|---|---|---|
| Principal, authorization and source binding | `core/continuity/source_admission.py` | immutable represented evidence |
| Source envelope and observation Draft | `core/continuity/source_admission_payloads.py` | proposal evidence only |
| Admission receipt and authorized batch | `core/continuity/source_admission_decisions.py` | admission evidence only; no runtime permission |

Primary modules remain internal and are not a public live trust boundary.

### Source adapters

```text
StateReconciliationResult
GoalProjectionResult v2
OpenLoopProjectionResult v2
        │
        ▼
source/result identity verification
complete exact subject-set verification
binding + authorization compatibility
bounded semantic derivation
        │
        ▼
ContinuitySourceEnvelope + ContinuityObservationDraft
        │
        ▼
STOP
```

| Source | Adapter | Positive derivation boundary |
|---|---|---|
| State | `state_source_adapter.py` | context degraded, active contradiction, context freshness |
| Goal | `goal_source_adapter.py` | bounded active attested evidence-coverage proposals |
| OpenLoop | `open_loop_source_adapter.py` | bounded open/overdue evidence-coverage proposals |

Adapters do not admit, persist, call the signal producer or create reminders/actions.

## 4. Pure admission evaluator

### Primary surface

| Responsibility | Surface |
|---|---|
| Rule definition | `ContinuityAdmissionRuleDefinition` |
| Evaluator definition | `ContinuityAdmissionEvaluatorDefinition` |
| Exact allowlist registry | `ContinuityAdmissionRegistry` |
| Current decision evidence | `ContinuityCurrentDecisionEvidence` |
| Evaluation function | `evaluate_continuity_admission(...)` |
| Result evidence | `ContinuityAdmissionEvaluationResult` |
| Adversarial tests | `tests/test_continuity_admission_evaluator.py` |

### Evaluation path

```text
SourceEnvelope + complete Draft set
+ binding and authorization evidence
+ explicit current-decision evidence
+ operator-selected evaluator/rule identity
+ explicit evaluated_at
        │
        ▼
registry resolution
current evidence compatibility and validity
rule/source/adapter/purpose/handling/retention checks
Draft signal/rule/confidence/age checks
        │
        ▼
complete deterministic admitted/rejected partition
ContinuityObservationAdmissionReceipt
        │
        ▼
STOP
```

### Authority boundary

- Registry identity verifies represented contents; it does not select itself as trusted.
- Current-decision evidence verifies represented status; it does not authenticate its external resolver.
- The evaluator reads no DB, environment, network or implicit clock.
- It creates no runtime permission, producer call, persistence or side effect.
- A future facade must resolve accepted owners and prevent bypass.

## 5. Decision ownership

- Canon and ESM: canonical memory/write services;
- truth admission: accepted TruthGate/write paths;
- hard policy/locality/data mode: PolicyKernel and PolicySnapshot;
- source result identity: State / Goal / OpenLoop owners;
- source adaptation: deterministic proposal transformation only;
- evaluator definitions and rule logic: pure admission evaluator;
- trusted evaluator registry selection: **no accepted runtime owner yet**;
- current principal/authorization/consent/restriction/erasure/policy resolution: **no accepted facade integration yet**;
- WorkingMemory disposition: existing `WorkingMemoryGate`;
- prompt context: existing `ContextPackBuilder`;
- legacy compute route: existing `decide_compute_path()`;
- runtime activation: **no accepted owner**.

## 6. Next facade boundary

The next internal facade must depend on typed protocols instead of creating new policy or identity owners.

Expected shape:

```text
accepted registry selector
+ principal resolver
+ authorization resolver
+ lawful-basis/consent resolver
+ restriction resolver
+ erasure resolver
+ current policy resolver
        │
        ▼
complete exact-subject CurrentDecisionEvidence
        │
        ▼
pure admission evaluator
        │
        ▼
evidence-only receipt / optional authorized batch
        │
        ▼
STOP
```

The first facade slice must not invoke the signal producer, persist data, register with startup or change `/query`.

## 7. Privacy and erasure boundaries

Before any live-capable path, the accepted owners must prove:

- current authorization expiry and withdrawal;
- consent or lawful basis;
- current restrictions;
- erasure-domain state and derived-artifact cleanup;
- current PolicySnapshot compatibility;
- complete multi-subject aggregation without silent filtering;
- retention, replay and cleanup lifecycle.

Historical receipts never override current restriction or erasure state.

## 8. Governance and operations

- aggregate merge evidence is implemented and observed;
- `main` branch protection/ruleset remains unenforced; issue #234;
- projection dispatcher remains implemented/tested but not lifecycle-wired;
- identity layer remains legacy/unwired;
- query-path read-only and Canon writer unification remain open hardening work;
- research candidates are governed separately by `research/IDEA_INTAKE_PROTOCOL.md`.

## 9. Audit checklist for the next slice

1. Is the trusted registry selected outside caller-controlled payloads?
2. Do resolver protocols point to accepted owners rather than duplicate policy/identity logic?
3. Is the complete exact subject set preserved?
4. Do missing, stale, unknown or conflicting current states fail closed?
5. Does the facade call only the pure evaluator?
6. Does output remain evidence-only?
7. Are bare Draft/observation/producer bypasses guarded?
8. Are persistence, runtime wiring and activation absent?
9. Are exact-head tests and Notion synchronization complete?
10. Are `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` reported separately?
