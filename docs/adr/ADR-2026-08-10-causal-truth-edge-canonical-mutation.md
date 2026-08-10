# ADR — Causal Truth-edge canonical mutation convergence

**Date:** 2026-08-10  
**Status:** Proposed on PR #287 until protected merge  
**Issue:** #286 · parent #50  
**Audited base:** `main@3100952f3dacf268f4d9c9b3f5a738f449663de6`

## Context

Titan currently has several graph-shaped surfaces, but they do not have the same
semantic role and must not be collapsed into one authority:

- `core.causal_graph.CausalGraph` / SQLite `relations` is the causal Truth-edge surface
  consumed by causal traversal, contradiction lookup, graph expansion and ingestion;
- `core.relations.RelationStore` / `fact_relations` is an associative/LTP model with
  strength, LTP/LTD and relation-state semantics;
- optional NetworkX Graph Lab is read-only in-memory structural analytics over
  `relations`;
- optional Neo4j causal persistence is downstream/derived persistence.

The pre-#286 causal Truth-edge surface had multiple durable mutation owners:

- `CausalGraph.add_relation()` inserted and committed forward/inverse rows itself;
- `CausalGraph.remove_relation()` deleted and committed itself;
- `core.kb_graph_build` owned independent bulk INSERT/DELETE/wipe SQL;
- pipeline/admin reset surfaces owned direct `DELETE FROM relations` paths.

Those writes did not share the same WriteGate + same-transaction AuditChain contract used
by other Truth Foundation mutation families.

Caller audit also found a policy defect: an automatic caller could provide
`knowledge_status="inferred"` but omit `truth_status` and `review_state`; the old defaults
stored the relation as `validated/approved`. That allowed inference labels and accepted
Truth labels to diverge.

## Decision

Keep `CausalGraph` as the one canonical mutation owner for SQLite `relations`. Do not
introduce another generalized graph write service, another database, another TruthGate,
or another persistence authority.

Every public causal create/delete/reset operation must:

1. pass the existing WriteGate before durable mutation;
2. validate type/status/source/confidence deterministically;
3. prepare the existing AuditChain schema before opening the relation transaction;
4. own one SQLite `BEGIN IMMEDIATE` transaction;
5. append causal relation lifecycle evidence in that same transaction;
6. roll the causal mutation back if audit evidence fails;
7. create no false success/audit event for duplicate or missing targets.

Each physical `relations` row receives a stable audit chain:

```text
causal-relation:<relation_id>
```

with structured lifecycle events:

```text
relation_created
relation_removed
```

No claim text, prompt text, model output or free-text causal assertion is copied into the
audit payload.

## Create / inverse atomicity

Forward and inverse physical rows form one canonical create unit. A create either commits
all required rows plus their AuditChain evidence or commits none of them.

Semantic duplicate input is idempotent. Repeating the same
`from + to + relation_type + inference_source` returns the durable existing relation ID;
it does not return a generated ID that was ignored by SQLite, and it emits no false audit
success.

If a pre-existing semantic forward row is missing its required inverse companion, the
canonical owner may repair that inverse in the same audited transaction without creating
a duplicate forward row.

## Inference / acceptance boundary

Automatic or non-manual causal input is not accepted Truth by default.

Unless an explicit admission/review path supplies stronger labels:

```text
knowledge_status = inferred / hypothetical / unknown
or inference_source != manual
        ↓
truth_status = hypothesis
review_state = pending
```

Approved causal reasoning reads remain bounded to `review_state='approved'` by default.
Diagnostic surfaces such as `knowledge_summary()` may explicitly inspect pending edges so
the system can report what it still needs to verify.

HITL suggestion approval may authorize persistence of a **hypothesis** without converting
that hypothesis into validated causal truth. Proposal approval and truth validation are
separate decisions.

## Bulk ingest and reset

`core.kb_graph_build` is a normalization/coordinator surface only. It may create the
required SQLite table/index schema on a fresh database, but durable relation rows are
inserted/deleted through `CausalGraph`.

Full reset and administrative reset similarly route through `CausalGraph.reset_relations`
so relation deletion and tamper-evident evidence share one transaction.

The historical `create_inverse=False` half-edge escape hatch is rejected for canonical
causal writes. Canonical Truth-edge creation preserves forward/inverse consistency.

## External / derived persistence

Remote or derived graph persistence is not write authority.

`import_snapshots()` may accept external snapshots only as input to the same local
canonical mutation owner. Imported/derived rows default to inferred/pending unless an
explicit accepted status accompanies the request.

Neo4j persistence remains downstream/derived. NetworkX remains SELECT-only/in-memory.
Neither can overwrite or bypass local canonical mutation evidence.

## RelationStore boundary

`RelationStore` / `fact_relations` is not merged into this mutation family. Its associative
LTP/LTD semantics are materially different from causal Truth-edge semantics. This ADR
makes no claim that the two tables are interchangeable or should be physically merged.

## Versioning boundary

This change does not invent a relation VersionStore merely to copy the fact mutation
model. Public causal relation mutation is create/delete; the live canonical row plus
same-transaction tamper-evident lifecycle events are the bounded evidence contract.

No schema-v8 migration is required by this decision.

## Dependent fact erasure

Relation rows deleted as dependent data inside the already-durable fact-erasure
transaction are not a second causal-delete owner and must not be double-logged merely to
satisfy this ADR. Their authority remains the parent canonical erasure transaction.

## Authority boundary

This decision grants no:

- runtime activation;
- Operator GO;
- runtime authority;
- production authority;
- autonomous graph scheduler/background loop;
- remote graph authority;
- Continuity 13/12 / Phase II.

Continuity remains `12/12`; project-state schema remains `v7`; runtime remains disabled.
Issue #249 remains separate.

## Validation requirements

Before merge, exact-head evidence must prove with real SQLite tests:

- forward + inverse create + audit atomicity;
- forced audit failure rolls the relation mutation back;
- duplicate create returns durable identity and creates no false audit;
- automatic inference defaults to hypothesis/pending and is excluded from approved
  reasoning reads;
- explicitly accepted status is preserved only when supplied intentionally;
- targeted remove + inverse companion + audit are atomic;
- remove miss creates no false audit;
- full reset is audited;
- KB bulk writes/deletes and admin/pipeline resets own no raw relation mutation bypass;
- NetworkX remains read-only;
- optional downstream graph persistence does not become Canon.

Full CI, Docker and protected aggregate merge evidence are required on the final head.

## Residual scope

Parent #50 remains OPEN until a fresh post-merge residual inventory proves no other
meaningful Truth Foundation mutation family remains. Issue #249 remains separate. No
production-readiness claim follows from this convergence.