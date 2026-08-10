# Canonical causal relation mutation — operator/developer contract

**Issue:** #286 · parent #50  
**PR:** #287 · review-stage until protected merge  
**Audited base:** `3100952f3dacf268f4d9c9b3f5a738f449663de6`

## Purpose

This record describes the bounded canonical mutation contract for Titan causal Truth
edges. It is not runtime-enablement documentation and does not grant Operator GO.

## Authority map

| Surface | Role | Canonical write authority? |
|---|---|---|
| `CausalGraph` / SQLite `relations` | causal Truth-edge storage and traversal | YES, bounded owner for this mutation family |
| `RelationStore` / `fact_relations` | associative/LTP model | NO for causal Truth edges |
| NetworkX Graph Lab | in-memory structural analytics | NO · SELECT/read-only |
| Neo4j causal persistence | downstream/derived persistence | NO |
| external causal snapshots | import input/proposal | NO until admitted by local owner |

Do not merge these surfaces merely because all of them are graph-shaped.

## Canonical create

A causal create request follows:

```text
caller
  ↓
CausalGraph
  ↓
WriteGate
  ↓
validate relation/status/source/confidence
  ↓
prepare AuditChain schema before transaction
  ↓
BEGIN IMMEDIATE
  ↓
forward row
  + relation_created audit
  + required inverse row
  + relation_created audit
  ↓
COMMIT
```

Any exception in the canonical row or audit append rolls the transaction back.

### Idempotency

The semantic identity used to detect an existing relation is:

```text
from_fact_id + to_fact_id + relation_type + inference_source
```

Duplicate input is a true no-op for the existing semantic row and returns its durable
`relation_id`. No phantom generated ID and no false `relation_created` event are allowed.

## Proposal / truth boundary

Automatic inference is not accepted causal truth.

Default policy:

```text
non-manual source OR knowledge_status != known
→ truth_status=hypothesis
→ review_state=pending
```

Reasoning/traversal reads default to approved relations only. Diagnostic code may opt in
to pending rows explicitly.

An HITL action can approve **recording a hypothesis** without validating the hypothesis as
truth. Stronger `validated/approved` labels require an explicit accepted admission path;
they are never inferred from model output alone.

## Canonical remove

Targeted removal resolves the requested physical row and its inverse companion inside one
transaction:

```text
BEGIN IMMEDIATE
→ determine physical relation IDs
→ DELETE each selected row
→ append relation_removed for each row
→ COMMIT
```

Missing targets are true no-ops and create no removal evidence.

## Full reset

Admin/pipeline/KB wipe surfaces do not execute independent `DELETE FROM relations` SQL.
They call `CausalGraph.reset_relations()`.

Reset enumerates the physical relation IDs, deletes them, appends one structured
`relation_removed` lifecycle event for each removed physical row, and commits as one
canonical transaction.

This is a destructive administrative operation, not an autonomous maintenance loop.

## KB graph build

`core/kb_graph_build.py` may ensure that the base `relations` table/index schema exists
for a fresh local database. It does not own durable causal row mutation.

KB generated edges are normalized then passed to `CausalGraph.add_relations_batch()`.
KB generated deletion selects relation IDs then delegates to
`CausalGraph.remove_relations()`; wipe delegates to `reset_relations()`.

`create_inverse=False` is rejected for canonical writes because it produces a half-edge
outside the forward/inverse integrity contract.

## Snapshot import / remote persistence

`CausalGraph.import_snapshots()` treats external rows as input to local admission, not as
remote canonical truth. The local owner applies the same WriteGate, policy defaults,
transaction and AuditChain evidence.

Neo4j and any other external graph copy remain derived. Failure or availability of a
remote graph cannot grant local write authority or accepted-truth status.

## NetworkX boundary

NetworkX Graph Lab loads a bounded subgraph from `relations` with SELECT and computes
in-memory structural analytics. It does not insert, update or delete Canon and does not
promote truth status.

## Failure semantics

| Condition | Required result |
|---|---|
| WriteGate denies | no relation mutation |
| invalid type/status/confidence | no relation mutation |
| duplicate create | durable existing ID; no false audit |
| AuditChain append failure | canonical transaction rollback |
| remove miss | no-op; no false audit |
| automatic inferred input | hypothesis/pending unless explicitly accepted |
| remote/derived graph failure | cannot replace local Canon |

## Evidence boundary

AuditChain relation events are structural/tamper-evident evidence. They are not Operator
permission, current runtime authorization or production authority.

The audit chain identity is stable per physical relation row:

```text
causal-relation:<relation_id>
```

The event does not store prompt/claim/model text.

## Explicit non-scope

- `RelationStore` / `fact_relations` redesign or merge;
- relation VersionStore invention;
- #249 contention characterization;
- ADAO / ARM-04;
- runtime activation or wider rollout;
- scheduler/background causal learning loop;
- schema v8;
- Continuity 13/12.

## Review / merge checklist

Before this record can be treated as current-main truth:

- issue #286 scope is unchanged;
- exact PR head is frozen;
- real-SQLite adversarial tests pass;
- Full CI succeeds;
- Docker succeeds;
- review-stage Notion evidence is synchronized and read back;
- PR is ready with zero unresolved threads;
- `Titan aggregate merge evidence` succeeds;
- protected merge uses the expected exact head;
- post-merge Full CI, Docker and aggregate succeed;
- FINAL Notion reconciliation is written and read back.

Until then this document is review-stage evidence only.