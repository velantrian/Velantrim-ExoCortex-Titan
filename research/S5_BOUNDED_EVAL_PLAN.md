# RT-RETRIEVAL-GRAPH-01 — Bounded Evaluation Plan for GraphRAG / LightRAG Ideas

**Status:** `R0 QUESTION · RESEARCH_CANDIDATE`  
**Lane:** `RESEARCH_CANDIDATE`  
**Runtime authority:** none  
**Canon / ESM / Policy write authority:** none  
**Parent:** S5 in `TITAN_COGNITIVE_DEVELOPMENT_MAP.md`  
**Related:** Issue #510, PR #509 (distinct facts), PR #515 (evidence labels), #512 (claim support)  
**Created:** 2026-11-10  
**Baseline:** `main@6b45854f57ca90516b86b2c48b284c88857bc2c2`

## 1. Origin

Audit and architecture discussion (2026-11-10). Operator noted that Titan was assembled with awareness of modern retrieval systems (GraphRAG, LightRAG, CAG, agentic RAG, CRAG, Self-RAG) yet none are present in runtime. This card formalizes the existing S5 research question into a bounded evaluation plan so it stops being a note and becomes a measurable track.

## 2. Problem / opportunity

Current hybrid retrieval (BM25 + optional dense) can lose suitable records under specific conditions (#510: BM25 `s > 0` filter on small corpora without a dense model). Graph-based community summaries or incremental entity graphs are proposed as potential complementary signals. The open question is whether any GraphRAG/LightRAG idea produces a measurable improvement **beyond** Titan’s own graph/retrieval primitives without violating invariants.

## 3. Current evidence

- #510 reproduces on `main` and on the combined #509+#514+#515 tree (5 known test failures).
- Dense path is optional and graceful-degrades to BM25-only.
- No GraphRAG, LightRAG, CAG, CRAG, Self-RAG or agentic-RAG code or tests exist in `core/` or `tests/`.
- Research documents already record the non-conflation rules: `graph retrieval ≠ system of record`, `retrieval ≠ evidence`, `graph similarity ≠ truth`.

## 4. Why this is research

No accepted Titan-native contract exists for community-summary or incremental-graph retrieval. Ownership, value, failure modes and authority boundary are not yet measured. Adoption would require a bounded evaluation plan (this document) and reproducible evidence.

## 5. Affected owners

- Retrieval (`core/hybrid_retriever.py`, `core/pipeline.py`)
- Graph primitives (existing causal / knowledge graph surfaces)
- TruthGate / Observer / evidence labels
- Research registry only — no new Canon, PolicyKernel or runtime route owner

## 6. Authority risks

- Graph summaries could be mistaken for evidence or Canon.
- Community-level text could leak into prompts without provenance.
- Incremental graph updates could create a second write path.

**Mitigation:** SHADOW LAB only. Graph output remains a proposal. No write, no answer authority, no evidence-label promotion.

## 7. Privacy / erasure risks

Graph structures derived from user facts must be rebuildable and erasable. No persistent graph may outlive the source facts.

## 8. Cheapest useful experiment (offline, deterministic)

**Corpus:** 500–1000 facts drawn from the real Titan knowledge base (Russian + English mix) with 30–50 control queries that have known ground-truth supporting records.

**Two modes:**
- Clean: all records present.
- Degraded: 20 % of records artificially removed (simulation of #510).

**Candidates:**
- A — baseline hybrid (BM25 + dense when available)
- B — + simple entity-link graph (existing primitives only)
- C — + community-summary style aggregation (offline prototype)
- D — + LightRAG-style incremental graph idea (offline)
- E — negative control (random additional signal)

**Metrics (all measured, no real LLM calls):**
1. Recall@10 of ground-truth records
2. Faithfulness proxy (fraction of retrieved records that actually support the control claim — bridges to #512)
3. Latency p95 on CPU-only
4. Authority leakage check (graph text never appears in evidence map or Canon)
5. Erasure completeness (derived graph nodes disappear after source erasure)

## 9. Return trigger

#510 is closed **or** a reproducible workload demonstrates that current hybrid retrieval systematically misses multi-hop or community-level relations that a graph signal would recover, **and** the operator explicitly allocates research capacity.

## 10. Promotion evidence

Candidate must beat baseline on Recall@10 **and** faithfulness proxy on the clean corpus **and** not be worse on the degraded corpus. Authority leakage must be zero. Result is an evaluation report + frozen artifacts. Promotion to engineering requires a separate ADR and bounded PR; this card itself grants none.

## 11. Status and decision history

- 2026-11-10: captured as formal R0 bounded evaluation plan. Status remains RESEARCH_CANDIDATE. No runtime change.

## 12. Explicit out-of-scope

- CAG (Cache-Augmented Generation) — conflicts with local-first / weak-hardware invariant.
- Agentic RAG, CRAG, Self-RAG loops — non-deterministic multi-call paths; TruthGate is designed for a single verifiable pass.
- Any production route, Crystal integration, or Operator GO.

## Non-conflation (mandatory)

```text
graph retrieval ≠ system of record
graph similarity ≠ truth
community summary ≠ evidence
incremental graph ≠ Canon write path
research result ≠ adopted mechanism
adopted ≠ implemented ≠ enabled ≠ observed
```

---

**This document is a research card only. It does not authorize implementation.**
