# Cognitive AI Research Intake — 2026-08-22

**Status:** RESEARCH_CANDIDATE · DOCS ONLY · NO RUNTIME / CANON / TRUTHGATE / POLICY AUTHORITY

## Purpose

Capture external cognitive-AI mechanisms that may be useful to Titan, while preserving Titan's research-intake rule: external prior art becomes a Titan research candidate only after ownership discrimination, a Titan-specific measurable problem, and a bounded evaluation plan.

See also `research/COGNITIVE_AI_RESEARCH_WATCH_STATE.md` for delta-oriented watch state and evidence-maturity classification. Presence in either file does not imply adoption.

## Candidate bundle

### RT-COG-RETRIEVAL-01 — Unified retrieval benchmark

Compare, on one controlled corpus and metric surface:

- BM25 / lexical baseline;
- dense retrieval;
- hybrid lexical+dense;
- GraphRAG / community-aware retrieval;
- temporal-graph retrieval / Graphiti-style patterns;
- later REFRAG-style retrieval-context compression;
- later AGRAG-style graph retrieval if it adds coverage beyond simpler baselines.

Measure more than retrieval recall. Candidate metric groups include:

- retrieval quality: Recall@K, Precision@K, MRR, nDCG;
- generation utilization: retrieved-context-used ratio, answer-support coverage, unsupported-answer rate;
- efficiency: retrieved tokens, consumed tokens, latency, cost;
- noise sensitivity: irrelevant-context ratio and answer degradation under additional context;
- provenance resolution: source traceability and chunk-to-source resolution.

Required interpretation boundaries:

```text
HIGH_RECALL != GOOD_ANSWER
MORE_CONTEXT != BETTER_CONTEXT
GRAPH_RETRIEVAL != BETTER_GENERATION
```

**Return trigger:** an accepted workload where current retrieval has measurable recall, precision, latency, cost or context-efficiency limits.

**Promotion evidence:** reproducible benchmark advantage plus negative tests showing no authority/provenance regression.

### RT-COG-DERIVED-STATE-01 — Derived-memory invalidation / non-revival

Research whether source lifecycle changes need explicit dependency propagation across derived read-side representations such as summaries, embeddings, graph projections, context packs or consolidated working-memory artifacts.

Candidate lifecycle:

```text
SOURCE_STATE_CHANGE
→ DERIVED_DEPENDENCY_DISCOVERY
→ IMPACT_CLASSIFICATION
→ INVALIDATE / RECOMPUTE / TOMBSTONE / RETAIN_WITH_MARKER
```

Failure case to test: a deleted, retracted, superseded or corrected source remains recoverable through a stale derivative and silently re-enters retrieval as if current.

**Boundary:** this is a research candidate, not a new Crystal/Titan authority mechanism. Any adoption requires owner-specific review. A derived graph, summary or embedding does not become Canon or evidence admission by existence.

**Cross-project ownership:** Titan may test retrieval/non-revival behavior; Crystal owns evidence/admission semantics; Continuum may own temporal/supersession continuity where applicable.

### RT-COG-SALIENCE-01 — Salience / activation benchmark

Research ACT-R-inspired activation mechanisms using EITI DAAD/ranking/decay as an empirical reference.

Candidate signals may include importance, recency, frequency, novelty, goal relevance, affect relevance and uncertainty.

**Boundary:** salience/accessibility is not epistemic confidence, evidence quality or truth.

**Cross-project ownership:** Titan may benchmark ranking behavior; Soul owns any cognition/affect semantics; Crystal remains evidence/admission owner.

### RT-COG-ROUTING-01 — Role-based model regression / Model Genome

Evaluate model/provider changes by role rather than globally:

- reasoning;
- coding;
- research;
- interaction quality;
- creativity/explanation;
- latency/cost;
- reliability;
- independent verification behavior.

**Boundary:** a model's benchmark score does not grant tool, write, policy, Canon or production authority.

### RT-COG-SYMBOLIC-01 — Symbolic / sparse cognition references

HTM/Numenta, Hyperon/MeTTa, sparse biologically inspired model families and related architectures remain external references unless a concrete Titan workload demonstrates a gap that simpler mechanisms cannot address.

**Return trigger:** fixed workload + measurable baseline deficit + bounded offline experiment.

## Comparative baselines

MemGPT/Letta may be used as context/memory-management baselines, but Titan must not conflate persistent context with trusted memory, belief/identity continuity or functional process continuity.

LIDA/GWT and SOAR may inform bounded orchestration/attention experiments, but Titan does not become the semantic owner of cognition/identity simply because it hosts an experiment.

## Required non-conflation

```text
external research result != Titan Canon
research candidate != engineering priority
benchmark pass != promotion authorization
retrieval != evidence
graph similarity != truth
association strength != epistemic confidence
model inference != user attestation
Titan experiment != Soul belief / identity
Titan integration != Crystal authority transfer
research result != adopted mechanism
adopted mechanism != implemented mechanism
implemented mechanism != tested mechanism
tested mechanism != integrated mechanism
integrated mechanism != authorized mechanism
```

## Intake path

```text
INBOX
→ TRIAGED
→ R0 QUESTION
→ R1 CONTRACT
→ R2 OFFLINE PROTOTYPE
→ R3 SHADOW EVALUATION
→ explicit architecture decision
→ bounded engineering only if separately authorized
```

This note changes no runtime, provider/model activation, TruthGate, PolicyKernel, Canon, ESM, Operator GO, production authority or remote-data consent boundary.