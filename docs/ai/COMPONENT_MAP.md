# 🗺️ Component and Authority Map

**Verified implementation baseline entering Phase 2A:** `main@51058f2d5662edfdb91b037a46dce9297c441a1b`  
**Continuity:** `12/12 = 100%`  
**Machine state:** schema v7  
**Runtime:** `CURRENTLY DISABLED · CURRENT OPERATOR GO ABSENT · HISTORICAL OBSERVED=true · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`

This file is an orientation map. Re-query live GitHub before treating the SHA above or a
review branch as current repository truth. Keep `main` truth separate from Draft PR
candidate truth.

## 1. Global authority rules

```text
local Canon
  > derived projections/caches
  > model/provider output

hard policy / WriteGate / TruthGate / ESM
  > routing or optimization preference

explicit authorization
  > configuration or historical observation
```

No green CI run, descriptor, health flag, preset, `auto` selection, provider preference,
historical canary or Notion record grants runtime/production authority.

## 2. Continuity ownership

| Capability | Primary surface | Authority boundary |
|---|---|---|
| source adapters | state/goal/open-loop adapters | deterministic proposals only |
| admission evaluator/facade | admission evaluator + facade | bounded admission; no owner substitution |
| current-decision resolver | six-owner evidence composition | no accepted live deployment adapters selected |
| durable lifecycle | admission artifact lifecycle | internal SQLite artifact persistence/replay only |
| runtime composition | `runtime_composition.py` | wired internally |
| controlled enablement | `controlled_enablement.py` | exact finite gate; current runtime disabled |
| bounded observation | `bounded_observation.py` | content-free read-only evidence; historical canary only |
| composition root | FastAPI lifespan | startup/shutdown composition; not current activation authority |

Current facts:

```text
Continuity                         12/12
runtime currently enabled          false
current Operator GO                false
operator authorization present     false
observed                           true (historical rolled-back canary)
runtime authority                  false
production authority               false
user-visible runtime activation    false
```

## 3. Canon / Truth Foundation ownership

| Mutation family | Accepted owner | Current status |
|---|---|---|
| canonical fact create/update | existing `SQLiteGraphStore` canonical methods | CONVERGED |
| ESM transitions / invalidation / restriction | existing `SQLiteGraphStore` mutation methods | CONVERGED |
| physical fact erasure | `ErasureCoordinator.erase_fact_durable()` | CONVERGED; forgetting adapter is legacy |
| PII claim redaction | `CanonicalPiiRedactor` over canonical store | CONVERGED |
| archival claim rewrite | `CanonicalArchivalRewriter` over canonical store | CONVERGED |
| async fact mutations | `AsyncSQLiteStore` → synchronous canonical owner | CONVERGED ADAPTER; native async SQL disabled |
| causal relation create/delete/reset | `CausalGraph` / SQLite `relations` | CONVERGED + #297 HARDENED |
| post-create raw provenance | `SQLiteGraphStore.link_raw_to_fact()` | CONVERGED |
| initial raw provenance | canonical fact-create parent transaction | CONVERGED |
| smart-KB fact admission/ESM | existing batch/ESM owners | CONVERGED; builder is orchestration only |
| associative/LTP relation model | `RelationStore` / `fact_relations` | SEPARATE NON-CAUSAL MODEL |
| optional Neo4j persistence | `causal_persistence.py` | DERIVED · NOT CANON |
| optional NetworkX graph lab | `graph_lab.py` | READ-ONLY PROJECTION |

Truth Foundation parent #50 is `CLOSED_COMPLETED`; the final residual inventory reached
`REAL_GAP=0`. That does not imply runtime or production authority.

## 4. ModelFreeCore read-side ownership

Phase 1 was introduced by #295/#296 and post-merge hardened by #297.

```text
L2Query
  → existing QueryRouter
  → lexical-only retrieval
  → existing FactsPack
  → Guardian
  → TruthGate
  → optional READ-ONLY CausalGraph
  → deterministic evidence renderer
  → L2Result
```

Key files:

- `core/model_free_core.py` — explicit model-free read-side facade;
- existing QueryRouter / FactsPack / Guardian / TruthGate owners — reused, not duplicated;
- `core/causal_graph.py` — optional causal evidence owner, read-only from ModelFreeCore;
- `core/pipeline.py` — existing pipeline ownership; Phase 1 did not replace the default
  runtime route.

#297 closed the bounded failure-path lane around lexical-only enforcement, absent/present
graph semantics, malformed physical relation rows, reciprocal inverse identity,
endpoint recall-policy rechecks, provenance preservation, FactsPack policy, typed input
and verified-vs-attributed rendering.

Final #297 evidence is recorded in `WORK_LOG.md` and the merged PR. #298 subsequently
reconciled GitHub/Notion public truth surfaces.

## 5. Policy authority

`core/policy_kernel.py` is the existing deterministic permission owner for:

- `EffectivePolicy`;
- `PolicySnapshot`;
- `PolicyDecision`;
- `CapabilityLease`;
- network deny/ask/allow;
- remote-data bounds;
- local-only canonical-write policy;
- mandatory WriteGate / fail-closed decisions;
- stable reason codes.

The process-wide owner is obtained through `get_policy_kernel()`.

**Do not create another global policy/permission engine.** Selection, provider health,
presets, budgets and `auto` may restrict or order candidates; none may weaken a
PolicyKernel denial.

## 6. Provider catalogue vs Phase 2A registry

### Existing current-main owner: `core/provider_catalog.py`

This is a console-facing LLM provider/model catalogue. It may describe available model
names for UI/config purposes. It is **not** the generic permission authority, provider
health owner or runtime router.

### Draft #300 candidate: `core/capability_registry.py`

Tracking issue #299 admits a narrow Phase 2A implementation. Until #300 is protected-merged,
this section describes a **review-stage candidate**, not current-main implementation.

Candidate ownership is limited to:

- stable provider/capability descriptors;
- capability-specific declared `data_mode`;
- explicitly supplied provider health (`UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE`);
- deterministic candidate evaluation;
- separate health and policy/selection reason codes;
- selection/no-selection explanation;
- trace-ready metadata returned to a future authorized caller.

Candidate authority chain:

```text
ProviderDescriptor + CapabilityDescriptor + ProviderHealth
                       |
                       v
               CapabilityRegistry
                       |
                       | lease request only
                       v
          existing get_policy_kernel()
                       |
                  allow / deny
                       |
                       v
                SelectionResult
```

The candidate:

- does not instantiate a second PolicyKernel by default;
- does not probe providers;
- does not invoke providers/models;
- performs no network I/O;
- is not wired into `pipeline.py` or server runtime;
- performs no Canon/ESM/TRACE/Audit mutation;
- fails closed on missing/unavailable health, malformed typed metadata, policy exceptions
  and policy snapshot/version changes during a single selection pass;
- cannot let explicit preference or `auto` override policy denial.

Read `PHASE2A_CAPABILITY_REGISTRY.md`, the Phase 2A ADR and exact PR #300 evidence before
working in this area.

## 7. Compute/config/resource ownership

Existing compute-profile and configuration mechanisms remain their own owners. Phase 2A
registry metadata does not replace:

- `core/compute_profile.py` defaults/features;
- existing config precedence;
- existing budget/resource mechanisms;
- runtime enablement gates.

These surfaces may later feed a bounded selector only under a separate admitted milestone.
A preset or resource preference cannot grant network, provider or Canon authority.

## 8. Projection authority

FTS, graph/vector indexes, caches, summaries, NetworkX analytics, Neo4j copies and
projection-outbox workers are derived/rebuildable surfaces. Projection state never wins
over Canon and cannot grant write or answer authority by itself.

Vector/embedding execution is explicitly outside #299/#300.

## 9. Trace / audit ownership

Existing TRACE/AnalysisTrace and AuditChain owners remain unchanged.

Phase 2A `SelectionResult.as_trace_metadata()` returns bounded metadata only. It does not
persist TRACE, append AuditChain receipts or create a new provenance authority.

A future authorized caller may attach:

- capability kind and preference;
- selected capability id or no-selection result;
- candidate provider id;
- provider health + `health_reason_code`;
- policy/selection reason;
- PolicyKernel snapshot id/version.

No secret or prohibited payload belongs in registry metadata.

## 10. Anti-bypass guarantees

Current-main guarantees plus the #300 candidate boundary require:

- one canonical store/write protocol;
- one PolicyKernel permission owner;
- no second QueryRouter or TruthGate;
- no raw-SQL Canon bypass;
- remote provider metadata cannot hide network requirement;
- capability `data_mode` is declarative PolicyKernel input, never consent;
- missing health cannot default to healthy;
- unavailable providers cannot be selected;
- healthy candidates outrank degraded candidates before preference;
- explicit preference cannot override lease denial;
- a policy evaluation exception cannot fall back to permission;
- mixed policy snapshots cannot be composed into one successful selection;
- registry/provider state cannot grant Operator GO or runtime authority.

## 11. Review-stage Phase 2A files

```text
#299                                           tracking / admission
#300                                           Draft implementation PR
core/capability_registry.py                    candidate implementation
tests/test_capability_registry.py              adversarial contract tests
docs/adr/ADR-2026-08-13-phase2a-capability-registry.md
docs/operations/capability-registry-contract.md
docs/ai/PHASE2A_CAPABILITY_REGISTRY.md
```

The PR must remain Draft until final exact-head CI/Docker, required review/thread closure,
review-stage Notion synchronization and read-back are complete. After Ready, require a
fresh `Titan aggregate merge evidence` result on the unchanged head before protected
merge.

## 12. Explicitly unauthorized by Phase 2A

```text
embeddings/vector execution       OUT_OF_SCOPE
reranker execution                OUT_OF_SCOPE
LLM invocation                    OUT_OF_SCOPE
ADAO execution                    OUT_OF_SCOPE
ARM-04                            NOT_AUTHORIZED
remote consent implementation     OUT_OF_SCOPE
provider probing                  OUT_OF_SCOPE
network activation                OUT_OF_SCOPE
runtime route replacement         OUT_OF_SCOPE
runtime enablement                false
Operator GO                       false
runtime authority                 false
production authority              false
remote Canon                      forbidden
schema v8                         not created
Continuity 13/12                  not created
```

Before any later wiring or activation, re-audit live `main`, preserve the owners above,
and require a separate bounded admission decision.
