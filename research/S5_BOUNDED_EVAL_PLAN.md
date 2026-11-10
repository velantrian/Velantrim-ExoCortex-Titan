# S5 Bounded Evaluation Plan — GraphRAG / LightRAG Ideas

**Status:** RESEARCH_CANDIDATE · DOCS ONLY · NO RUNTIME / CANON / TRUTHGATE / POLICY AUTHORITY
**Date:** 2026-11-10
**Base SHA:** 6b45854f57ca90516b86b2c48b284c88857bc2c2
**Branch:** research/s5-bounded-eval-plan

## 1. Titan-specific problem

#510 — BM25 with `s > 0` threshold drops relevant records on small corpora without dense model. A graph layer built on top of leaky retrieval would measure the hole, not the graph.

**Gate:** #510 must be closed (or at least reproduced and tracked) before S5 evaluation starts. Otherwise results are confounded.

## 2. Corpus

- 500–1000 facts from the real Titan knowledge base.
- Russian + English mix (multilingual coverage).
- 30–50 control queries with known ground-truth answer sets (fact_id lists).
- Ground truth constructed independently of any retrieval method (human or cross-model agreement, recorded with provenance).

## 3. Candidates under test

| ID | Approach | Notes |
|----|----------|-------|
| A | Titan baseline: BM25 only | Current default fallback |
| B | Titan baseline: BM25 + Dense (RRF) | Requires sentence-transformers installed |
| C | GraphRAG-style: community detection + global summaries | Neo4j or networkx; Leiden/Louvain |
| D | LightRAG-style: entity-relation graph + dual-level retrieval | Lightweight, incremental |
| E | Temporal-graph (Graphiti-style) | If corpus has timestamps |

All candidates run on the **same** corpus, same queries, same hardware profile.

## 4. Metrics

| Metric | Definition | Pass threshold (draft) |
|--------|-----------|------------------------|
| Retrieval recall@10 | % of ground-truth fact_ids in top-10 | > baseline + 10 pp |
| Generation faithfulness | % of answer sentences supported by retrieved facts (claim-level, per #512 logic) | > 0.8 |
| Provenance resolution | % of retrieved items with valid fact_id → source trace | 1.0 |
| Latency p95 | End-to-end query time | < 2× baseline |
| RAM peak | Peak resident memory during eval | < 2 GB on dev hardware |

## 5. Controls

- Same LLM stub / fixture provider for generation (no real models).
- Same embedding model for B/C/D/E dense paths.
- Frozen corpus snapshot (git-tracked fixture).
- Independent repeats: ≥ 3 runs per candidate, report mean ± std.
- Negative controls: queries with no relevant facts in corpus.

## 6. Classification outcomes

Per IDEA_INTAKE_PROTOCOL:

- **ADOPT** — measurable gain on ≥ 3 of 5 metrics, no invariant violation.
- **ADAPT** — gain on 1–2 metrics, or gain only after adaptation to Titan invariants.
- **REJECT** — no measurable gain, or violates `retrieval != evidence` / `graph retrieval != system of record`.
- **DEFER** — inconclusive; needs larger corpus or different hardware class.

## 7. Non-conflation reminders (from COGNITIVE_AI_RESEARCH_WATCH_STATE)

- graph retrieval ≠ system of record
- retrieval improvement ≠ evidence authority
- graph similarity ≠ truth
- retrieval ≠ evidence

## 8. Out of scope

- CAG / context caching (S6, separate plan).
- Agentic RAG loops (real model calls; violates local-first + no-real-models boundary).
- CRAG / Self-RAG (require real model judgment; same boundary).
- Any runtime wiring, Canon writes, or TruthGate changes.

## 9. Next steps

1. Close or formally track #510.
2. Build the 500–1000 fact corpus fixture with ground truth.
3. Implement candidate C and D as shadow experiments (no runtime route).
4. Run metrics, record in this file or a dated follow-up.
5. Human review before any ADOPT/ADAPT decision.
