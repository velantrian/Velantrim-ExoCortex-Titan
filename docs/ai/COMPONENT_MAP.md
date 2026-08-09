# 🗺️ Component and Authority Map

**Repository head inspected:** `main@90e221be2bed8177f4648787d713058df0f29e1f`  
**Implementation baseline:** `9f07db6de8d32683d00bfe4f1673e84493607553` (PR #246)  
**Governance canary checkpoint:** PR #260 → `a733e760732ad2c4ec6496d3f8ea4c5d0383048f`  
**Dependabot checkpoint:** PR #255 → `c9e272d5d9da76219f8e0caaf784892e80046a31`  
**Phase I audit checkpoint:** PR #261 → `90e221be2bed8177f4648787d713058df0f29e1f`  
**Machine state:** [`docs/state/project_state.json`](../state/project_state.json) · schema v2 · `COMPLETE` · `SYNCED` · audit finalization `true`  
**Rule:** presence is not wiring; content-addressed evidence is not runtime authority.

## 1. Canon and core runtime

| Responsibility | Primary owner | State | Authority |
|---|---|---|---|
| Durable facts and ESM | `core/memory.py` / canonical store services | implemented, tested, wired | Canon state owner |
| Truth admission | `core/truth_gate.py`, accepted write services | implemented, tested, partly unified | evidence/confidence decision |
| Hard capability/data-mode policy | `core/policy_kernel.py`, `PolicySnapshot`, `CapabilityLease` | implemented, tested | policy owner |
| Provenance and audit | `core/provenance_chain.py`, `core/audit_chain.py` | implemented, tested | trace and mutation evidence |
| Retrieval coordination | `core/pipeline.py`, `core/hybrid_retriever.py` | implemented, wired | read-side proposal only |
| Projection delivery | projection outbox / dispatcher primitives | implemented, tested, not lifecycle-wired | rebuildable derived state |

No Continuity component owns Canon, TruthGate, PolicyKernel, GoalStack, reminders, tools,
actions or compute routing.

## 2. Continuity accepted lineage

| Layer | Merge SHA | Primary surface | Runtime state |
|---|---|---|---|
| R1 immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | `core/continuity/contracts.py` | tested, unwired |
| R2 read-side / threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | event/bridge/weaver | process-local, unwired |
| R3 projections / WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | context/state/goal-open-loop | rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | `core/compute_controller.py` | shadow-only, unwired |
| R5A replay / Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | evaluation/advisory shadow | shadow-only, unwired |
| R5B disabled runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | `shadow_runner.py` | default-off, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | observations/signal producer | pure shadow producer |
| Source-admission evidence | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | source-admission contracts | evidence only |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | `state_source_adapter.py` | tested, internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | `goal_open_loop.py` | tested contract correction |
| OpenLoop subject binding v2 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | `goal_open_loop.py` | tested contract correction |
| Goal Draft adapter | `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | `goal_source_adapter.py` | tested, internal, unwired |
| OpenLoop Draft adapter | `42aa79338c57e9b9a67c3e3c08dd948b60c5541f` | `open_loop_source_adapter.py` | tested, internal, unwired |
| Admission evaluator | `97fe27a37184c6c7277f54e96acd04d98d583ab3` | `admission_evaluator.py` | tested, internal, unwired |
| Admission-aware facade | `9f07db6de8d32683d00bfe4f1673e84493607553` | `admission_facade.py` | tested, internal, unwired |

## 3. Source-admission path

```text
State / Goal / OpenLoop result
→ deterministic source adapter
→ source envelope + complete Draft set
→ operator-selected represented facade policy
→ exact registry/evaluator/rule identity
→ typed current-decision resolver boundary
→ internal admission-aware facade
→ pure admission evaluator
→ content-addressed evidence-only result
→ STOP
```

The accepted path does not invoke the signal producer, persist admission artifacts, write
Canon, create reminders/actions or change compute routing.

## 4. Decision ownership

| Decision | Accepted owner |
|---|---|
| Canon / ESM state | canonical memory and write services |
| Truth admission | accepted TruthGate/write path |
| hard policy, locality and data mode | PolicyKernel / PolicySnapshot |
| State/Goal/OpenLoop result identity | source component owners |
| source adaptation | deterministic proposal transform only |
| evaluator rules | pure admission evaluator |
| anti-substitution and composition boundary | internal admission facade |
| WorkingMemory disposition | existing `WorkingMemoryGate` |
| prompt context | existing `ContextPackBuilder` |
| legacy compute route | existing `decide_compute_path()` |
| trusted facade/registry deployment selection | no accepted runtime owner yet |
| concrete current-decision evidence composition | not implemented yet |
| runtime activation | no accepted owner |

## 5. Next resolver-composition boundary

A later bounded internal slice must reuse existing owners rather than introduce a second
PolicyKernel, identity system, restriction registry or erasure owner.

```text
operator-selected facade policy + registry
+ accepted principal/authentication owner
+ accepted authorization owner
+ consent/lawful-basis owner
+ restriction owner
+ erasure-domain owner
+ current PolicySnapshot owner
→ complete exact-subject CurrentDecisionEvidence
→ accepted internal facade
→ evidence-only result
→ STOP
```

Missing, stale, unknown, ambiguous, conflicting or partially covered state must reject the
complete evaluation. Silent subject filtering is forbidden.

## 6. Privacy and lifecycle boundary

Before any live-capable path, prove current authorization expiry/withdrawal, lawful basis,
restrictions, erasure-domain state, derived-artifact cleanup, PolicySnapshot compatibility,
complete multi-subject aggregation and durable retention/replay/cleanup semantics.

Historical receipts never override current restriction or erasure state.

## 7. Governance and operations

- ruleset `main-governance` is active on `main` as ID `20601712`;
- PRs, exact aggregate evidence, up-to-date branches and resolved conversations are required;
- force pushes are blocked, deletion is restricted and bypass is empty;
- accepted solo mode uses approvals `0`, Code Owner review OFF, stale dismissal OFF and
  latest-push approval OFF;
- Restrict updates is OFF so valid protected merges remain possible;
- PR #260 completed the non-destructive protected-path canary;
- PR #255 was validated and merged separately as a workflow-pin update;
- PR #261 completed the Phase I retrospective audit and merged as
  `90e221be2bed8177f4648787d713058df0f29e1f`;
- issue #257 is `CLOSED_COMPLETED`;
- the existing Notion page `Velantrim Titan 9.0` records the same audit head, CI,
  aggregate, merge and non-authority boundaries with canonical status `SYNCED` and an
  explicit finalization marker;
- project-state schema v2 pins issue #257, PR #261, exact head/merge and exact Notion page;
- historical schema v1 snapshots remain readable without being misclassified as v2;
- the audit does not backfill historical approvals;
- aggregate success remains automated merge evidence, not independent review;
- projection dispatcher lifecycle remains unwired;
- identity remains legacy/unwired;
- query-path read-only and Canon-writer unification remain open hardening work.

## 8. Current audit checklist

Before the next engineering slice, verify:

1. Is facade/registry selection outside caller-controlled payloads?
2. Are existing policy, identity, restriction and erasure owners reused?
3. Is the complete exact subject set preserved?
4. Do missing, stale, unknown, ambiguous or conflicting states fail closed?
5. Does composition call only the accepted internal facade?
6. Does output remain evidence-only?
7. Are producer invocation, persistence and runtime wiring absent?
8. Are tests and aggregate evidence attached to the exact head?
9. Are GitHub and the intended Notion page synchronized?
10. Are `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` reported separately?
