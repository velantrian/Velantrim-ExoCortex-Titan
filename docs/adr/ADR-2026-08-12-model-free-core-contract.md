# ADR — Explicit ModelFreeCore contract for #53 Phase 1

- Status: Proposed
- Date: 2026-08-12
- Tracking: #295
- Parent architecture: #53
- Prerequisite: #50 CLOSED_COMPLETED
- Baseline main: `2699963547a42c4fbcd6b0273125c890a038654b`

## Context

Issue #53 requires Titan to remain useful when embeddings, rerankers, LLMs, GPU
acceleration and the network are unavailable. A live audit after Truth Foundation #50
closure found that current `main` already contains most required model-free primitives,
but does not expose them as one explicit typed contract.

The existing primitives are intentionally retained:

- `QueryRouter` performs deterministic rule-based classification without an LLM;
- `pipeline._retrieve_from_store(..., retrieval_mode="lexical")` uses the existing
  bounded candidate narrowing + BM25 path and does not build the HybridRetriever;
- `build_facts_pack()`, `guardian()` and `truth_gate()` remain the evidence/policy path;
- `CausalGraph` remains the already-converged causal owner and is read only by this slice;
- canonical mutation ownership remains exactly the Truth Foundation #50 contract.

The general pipeline and `HybridRetriever` are not redefined. In particular, this ADR
does not change the current runtime default route or activate any optional capability.

## Decision

Introduce `core/model_free_core.py` as a **read-side facade**, not a new router or
control plane.

The facade defines typed `L2Query`, `L2Evidence`, `L2Relation`, and `L2Result`
contracts and composes the existing primitives in this order:

```text
L2Query
  -> existing QueryRouter classification
  -> existing lexical-only retrieval path
  -> existing FactsPack
  -> existing Guardian
  -> existing TruthGate
  -> existing local CausalGraph reads when requested
  -> deterministic evidence-only renderer
  -> L2Result
```

`ModelFreeCore` never selects DenseRetriever, reciprocal-rank fusion, a cross-encoder,
an LLM, a remote provider, ADAO, or CapabilityRegistry. It owns no canonical mutation
method.

The deterministic renderer may only restate claims that survived the existing
FactsPack + Guardian + TruthGate path. When evidence is absent or rejected it returns the
bounded message `Недостаточно подтверждённых локальных данных.` with a reason code.

`L2Result` intentionally excludes volatile timestamps so equivalent canonical state and
equivalent query inputs can produce a stable serializable contract.

## Authority boundary

This decision grants **read/output composition only**.

It does not create or change authority for:

- canonical fact creation/update;
- ESM transition, invalidation, restriction, promotion or erasure;
- causal relation creation/deletion/reset;
- projection application;
- provider/model selection;
- network/remote egress;
- runtime activation or server wiring.

All canonical writes continue through the owners proven by parent #50.

## Alternatives rejected

### Reuse `HybridRetriever` as the ModelFreeCore API

Rejected. It contains optional Dense/RRF/reranker behavior and therefore does not express
an unambiguous model-free contract even though it can degrade to BM25.

### Build a second lexical retriever or second query router

Rejected. Current `main` already has the required lexical ranking and deterministic
QueryRouter. Duplicating them would create drift and a second decision owner.

### Change the runtime default to lexical/model-free in this slice

Deferred. Phase 1 proves an explicit baseline contract only. Runtime/provider selection,
policy precedence and adaptive routing belong to later #53 phases and require their own
bounded decision.

### Implement CapabilityRegistry or richer embedding-space identity now

Deferred to later #53 phases. Existing narrow embedding code is not expanded by this ADR.

## Verification requirements

Focused acceptance tests must prove:

- optional model/network paths are not invoked;
- typed lexical evidence can be returned from canonical local memory;
- existing local contradictions/relations are observable read-only;
- insufficient/policy-ineligible evidence fails boundedly;
- repeated equivalent reads serialize deterministically;
- no fact, ESM or relation mutation occurs during ModelFreeCore queries;
- the facade exposes no write/escalation API.

Full repository CI and all applicable protected merge gates remain required.

## Fixed project state

This ADR does not change:

- Continuity: `12/12`;
- project-state schema: `v7`;
- runtime enabled: `false`;
- Operator GO: `false`;
- runtime authority: `false`;
- production authority: `false`.

No Phase II, Continuity 13/12, schema v8, ADAO activation, ARM-04, remote Canon,
new generalized TruthGate, scheduler/control plane or production rollout follows from
this decision.
