# 🕸️ Community-Aware Graph Retrieval — Bounded Architecture

> Date: 2026-08-24  
> Status: ARCHITECTURE / RESEARCH BOUNDARY — NOT RUNTIME AUTHORIZATION  
> Scope: Titan retrieval only

## Decision

Titan should **not** add a second independent GraphRAG stack beside its existing retrieval and graph machinery.

The preferred future direction is a bounded **community-aware graph retrieval projection** that reuses existing Titan contracts and can be benchmarked against lexical and hybrid retrieval before any runtime activation.

```text
Query
  ↓
existing retrieval routing / budget
  ├─ lexical / BM25
  ├─ dense / hybrid where already authorized
  └─ optional graph projection
          ↓
      candidate subgraph
          ↓
      community-aware ranking
          ↓
      bounded ContextPack
```

## Reuse before addition

The design should reuse, rather than duplicate:

- `GraphStore` backend boundary;
- SQLite as ordinary/default local storage;
- optional Kuzu / embedded graph traversal;
- optional Graphiti / Neo4j integration;
- existing causal/typed relations;
- existing hybrid retrieval and rank-fusion concepts;
- Reader structure and provenance where applicable.

No Microsoft GraphRAG, Graphiti, Neo4j, Kuzu, Louvain implementation, or other graph framework becomes a mandatory Titan dependency by this document.

## Derived projection rule

Communities, graph neighborhoods, centrality, embeddings, summaries, and graph indexes are **derived retrieval projections**.

They are rebuildable and non-authoritative:

```text
graph edge != evidence
community membership != truth
centrality != importance in Canon
similarity != identity
retrieval score != confidence
community summary != Canon
retrieval projection != authority
```

A graph projection may answer **what should be inspected next**. It may not decide **what is true**.

## Candidate architecture

A future bounded implementation may expose a provider-neutral interface such as:

```text
GraphRetrievalProjection
  build(snapshot)
  retrieve(query, budget)
  expand(seed_ids, hop_limit, node_limit)
  communities(seed_ids, community_limit)
```

The interface should return candidates plus provenance sufficient to explain:

- which seed retrieval produced a node;
- which explicit edge/path caused expansion;
- which community projection was used;
- which backend/projection version produced the result;
- what hard node/edge/community budgets were applied.

It must not expose write or truth-promotion authority.

## Community layer

Community detection is useful only as a retrieval/indexing aid. A future implementation may compare Louvain/Leiden or backend-native community detection, but algorithm choice must remain replaceable.

Expected use:

```text
seed candidates
  ↓
local bounded neighborhood
  ↓
community lookup / expansion
  ↓
rank fusion with lexical/dense candidates
  ↓
evidence-preserving context selection
```

Do not generate a global LLM community summary and silently treat it as source evidence. Any generated summary must remain a derived, attributable artifact whose underlying source nodes remain inspectable.

## Temporal / Graphiti boundary

Graphiti-like temporal memory can be useful for:

- episode/event relationships;
- temporal invalidation;
- graph-aware retrieval;
- community construction;
- slow consolidation candidates.

But Graphiti extraction is not a truth oracle. Optional Graphiti/Neo4j remains a backend/integration choice, not Titan's epistemic authority.

## Reader boundary

Reader may later use structure-aware or graph-aware retrieval, but this document does **not** activate it.

```text
Reader proposition/section
  → candidate retrieval
  → optional graph expansion
  → Reader synthesis

Reader output != evidence
Reader synthesis != Canon
parser structure != truth
```

PageIndex, RAPTOR, GraphRAG, Ψ-RAG, parent-child retrieval, and durable cross-process Reader indexing remain separate experiments unless independently authorized.

## Evaluation gate

Before runtime adoption, compare the graph projection against the existing frozen baseline on exact datasets and budgets.

Minimum measurements:

1. recall@K / useful-candidate recall;
2. hard-negative rate;
3. latency and memory cost;
4. graph expansion size and boundedness;
5. deterministic replay where the selected mode is deterministic;
6. degradation behavior when the graph backend is unavailable;
7. provenance completeness;
8. incremental rebuild cost;
9. benefit over lexical/hybrid retrieval, not merely benefit over no retrieval.

Graph/community retrieval should be adopted only when it provides material measured value on graph-shaped questions such as multi-hop relations, clustered concepts, temporal neighborhoods, or cross-document structural links.

## Fail-closed behavior

If a graph backend, projection, community index, or required provenance is missing or stale:

- do not invent edges;
- do not silently promote approximate relations;
- fall back to an already authorized retrieval path when safe;
- otherwise return a bounded degradation signal.

## Non-goals

This architecture does not authorize:

- a second parallel RAG pipeline;
- a second source of truth;
- automatic Canon writes;
- TruthGate/Guardian bypass;
- automatic claim identity from graph proximity;
- automatic contradiction resolution;
- mandatory Neo4j or cloud infrastructure;
- background autonomous graph mutation;
- production activation.

## Recommended sequence

```text
A. Freeze benchmark + graph-shaped query strata
B. Add provider-neutral read-side projection contract
C. Implement smallest local projection first
D. Add bounded community lookup
E. Fuse with existing retrieval using explicit ranking provenance
F. Benchmark
G. Only then decide whether Graphiti/Kuzu/other backend materially improves results
```

## Final position

Titan already has enough graph and retrieval foundations that adding a separate GraphRAG product would create unnecessary duplication.

The desired direction is:

**reuse existing graphs → derive bounded communities → retrieve candidates → fuse ranks → preserve provenance → keep truth authority outside retrieval.**
