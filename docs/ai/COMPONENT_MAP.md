# 🗺️ Component and Authority Map

**Verified implementation checkpoint:** `main@c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca`  
**Continuity:** `12/12 = 100%`  
**Machine state:** schema v7  
**Runtime:** `CURRENTLY DISABLED · CURRENT OPERATOR GO ABSENT · HISTORICAL OBSERVED=true · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`

This file is an orientation map. Re-query live GitHub before treating the SHA above as
current repository truth.

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

#297 closed the bounded failure-path lane. #298 reconciled GitHub/Notion public truth.

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

### Existing owner: `core/provider_catalog.py`

This remains a console-facing LLM provider/model catalogue. It may describe model names for
UI/config purposes. It is **not** the generic permission authority, provider-health owner
or runtime router.

### Merged Phase 2A owner: `core/capability_registry.py`

Tracking issue #299 / merged PR #300 converged the bounded metadata contract at
`main@c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca`.

Ownership is limited to:

- stable provider/capability descriptors;
- capability-specific declared `data_mode`;
- explicitly supplied provider health (`UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE`);
- deterministic candidate evaluation;
- separate health and policy/selection reason codes;
- selection/no-selection explanation;
- trace-ready metadata returned to a future authorized caller.

Authority chain:

```text
ProviderDescriptor + CapabilityDescriptor + ProviderHealth
                       |
                       v
              CapabilityRegistry()
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

The merged contract:

- exposes no alternate policy/leaser constructor injection;
- does not instantiate a second PolicyKernel;
- does not probe providers;
- does not invoke providers/models;
- performs no network I/O;
- is not wired into `pipeline.py` or server runtime;
- performs no Canon/ESM/TRACE/Audit mutation;
- fails closed on missing/unavailable health, malformed typed metadata, policy exceptions
  and policy snapshot/version changes during a single selection pass;
- cannot let explicit preference or `auto` override policy denial.

Final #300 evidence:

```text
exact tested head:       f0b893bac1b6fe1f58a71c70ac631f3c14becb59
protected squash merge:  c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
Full CI:                  #1105 · 31735939941 · SUCCESS
Docker:                   #723 · 31735939929 · SUCCESS
READY aggregate:          #981 · 31736858130 · SUCCESS
post-merge Full CI:       #1106 · 31736925690 · SUCCESS
post-merge Docker:        #724 · 31736925695 · SUCCESS
post-merge aggregate:     #982 · 31736925705 · SUCCESS
```

## 7. Compute/config/resource ownership

Existing compute-profile and configuration mechanisms remain their own owners. The Phase
2A registry does not replace:

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

Vector/embedding execution was explicitly outside #299/#300 and remains unauthorized by
that merge.

## 9. Trace / audit ownership

Existing TRACE/AnalysisTrace and AuditChain owners remain unchanged.

Phase 2A `SelectionResult.as_trace_metadata()` returns bounded metadata only. It does not
persist TRACE, append AuditChain receipts or create a new provenance authority.

A future separately authorized caller may attach:

- capability kind and preference;
- selected capability id or no-selection result;
- candidate provider id;
- provider health + `health_reason_code`;
- policy/selection reason;
- PolicyKernel snapshot id/version.

## 10. Anti-bypass guarantees

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

## 11. Phase 2A files

```text
#299                                           tracking / closure issue
#300                                           MERGED implementation PR
core/capability_registry.py                    merged metadata contract
tests/test_capability_registry.py              adversarial contract tests
docs/adr/ADR-2026-08-13-phase2a-capability-registry.md
docs/operations/capability-registry-contract.md
docs/ai/PHASE2A_CAPABILITY_REGISTRY.md
```

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
