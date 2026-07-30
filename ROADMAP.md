# 🗺️ Velantrim ExoCortex Titan — Current Roadmap

**Version context:** Titan 9.0  
**Updated:** 2026-07-30  
**Status rule:** only merged code and executable checks count as implementation; research documents have no runtime authority

## Current engineering baseline

Titan currently separates retrieval, evidence, policy, truth admission, write authority and language generation.

```text
query
→ retrieval
→ FactsPack / ContextPack
→ TRACE / provenance
→ Guardian / policy
→ TruthGate
→ controlled answer
```

The local-first path remains mandatory. LLMs, embeddings, graphs and remote providers are optional or replaceable components and do not receive Canon authority.

## Recently completed

### ✅ Synaptic read foundation and shadow evaluation

Merged foundations include:

- provider-neutral `SemanticReader` and source-linked `KnowledgeCapsule` contracts;
- LLM reader hardening with bounded retry and deterministic claim admission;
- deterministic `WorkingMemoryGate` and provenance-preserving `ContextPack`;
- fail-isolated `synaptic_shadow` dispatch with bounded queue and legacy-answer authority;
- deterministic RCO-1 shadow projection with no active route or write authority.

### ✅ Adaptive retrieval execution

PR #91 merged executable retrieval routing:

```text
none    → no retrieval
lexical → NGram + BM25
hybrid  → lexical + dense + RRF + optional reranking
```

The change preserves the existing FactsPack/TRACE/Guardian/TruthGate chain and keeps feature-flag-off behavior compatible. It also adds reusable model/vector caching and reproducible routing benchmarks.

### ✅ Titan-native architecture naming

PRs #93 and #94 define adaptive retrieval and selective-memory work using neutral Titan terminology. External projects remain prior art only.

## Active implementation track — Adaptive Retrieval and Memory

Tracker: issue #92  
Architecture: [`docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md`](docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md)

| Slice | Status | Purpose |
|---|---|---|
| PR-ARM-01 | ✅ merged as #91 | execute `RetrievalPlan.mode`, route metrics and benchmark |
| PR-ARM-02 | 📋 next | rebuildable embedding projection identity, stale detection and reindex hooks |
| PR-ARM-03 | 📋 planned | shadow-only selective memory candidate extractor |
| PR-ARM-04 | ⛔ blocked by evaluation | candidate admission through WorkingMemoryGate and explicit Write Gate |
| PR-ARM-05 | 📋 planned | versioned parallel context assembly and safe cache invalidation |

Non-negotiable gates:

- `truth_gate_bypass_count == 0`;
- `query_path_write_count == 0`;
- lexical fallback remains available without embeddings/providers;
- incompatible embedding versions cannot silently share a projection;
- erasure and revocation invalidate derived projections and caches;
- memory-write authority follows shadow evaluation and explicit approval.

## Active research track — Replayable Evaluation

Contracts:

- [`research/EVALUATION_REPLAY_PROTOCOL.md`](research/EVALUATION_REPLAY_PROTOCOL.md);
- [`research/EXTERNAL_ARCHITECTURE_PATTERNS.md`](research/EXTERNAL_ARCHITECTURE_PATTERNS.md);
- [`research/FUTURE_COMPONENTS.md`](research/FUTURE_COMPONENTS.md).

Priority order:

1. **P0 — Evaluation replay, fork and structural diff**  
   Build fixed corpora, questions, fixtures and machine-readable receipts before designing a general event runtime.

2. **P1 — Temporal evidence**  
   Test valid-time, known-time, supersession and historical queries against the existing bi-temporal baseline.

3. **P2 — Receipt normalization**  
   Evaluate a shared envelope without replacing domain-specific policy, truth or audit contracts.

4. **P3 — Extension manifests**  
   Specify capability requests, locality, persistence, failure and erasure boundaries without loading third-party code.

5. **P4 — Procedural skill candidates**  
   Evaluate human-readable, source-linked procedures as read-only artifacts before any bounded execution.

Research advancement:

```text
contract
→ synthetic fixtures
→ baseline run
→ candidate fork
→ structural diff
→ operator-labelled review
→ shadow prototype
→ explicit Operator GO
```

## RCO / D16 status

- RCO-1 exists as a deterministic, zero-model, shadow-only projection.
- D16 remains a versioned proposal contract, not an active executive controller.
- `LEGACY_QUERY` remains the authoritative route.
- Any active routing slice requires labelled evaluation, approved unsafe-fast and false-defer limits, rollback and separate Operator GO.

Relevant contracts:

- [`research/RAPID_CALIBRATED_ORIENTATION.md`](research/RAPID_CALIBRATED_ORIENTATION.md);
- [`research/D16_EXECUTIVE_CONTROL_CONTRACT.md`](research/D16_EXECUTIVE_CONTROL_CONTRACT.md);
- [`research/FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md`](research/FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md).

## Near-term ordered work

### Phase A — Evidence infrastructure

1. synchronize issue #92 with merged PR #91;
2. define PR-ARM-02 projection identity and stale-vector behavior;
3. create the first synthetic EvaluationPackage;
4. reproduce lexical versus hybrid baseline runs;
5. publish structural diffs and critical-gate results.

### Phase B — Selective memory shadow

1. define immutable memory candidate schema;
2. retain exact source spans, temporal scope and sensitivity flags;
3. run in shadow mode with zero durable writes;
4. measure candidate precision, sensitive blocking and duplicates;
5. request a separate review before Write Gate integration.

### Phase C — Temporal and receipt research

1. add temporal fixture cases for overlapping, corrected and superseding claims;
2. compare current bi-temporal behavior with a read-only EvidenceEpisode view;
3. map existing receipts into a candidate envelope;
4. reject the envelope if it loses domain-specific reason codes or authority identity.

## Deferred until evidence exists

Do not activate merely because a feature is attractive:

- a general production replay/event-sourced runtime;
- automatic graph relation behavior;
- active D16 routing;
- self-modifying policy or truth thresholds;
- direct LLM memory writes;
- mandatory remote providers or embedding models;
- multi-tenant SaaS claims;
- executable procedural skills;
- third-party plugin loading.

Each item requires a concrete workload, simpler baseline, threat review, deterministic tests and measured benefit.

## Verification expectations

For documentation-only PRs:

- relative links resolve;
- status labels match merged GitHub reality;
- no runtime or authority claim is introduced;
- repository-hygiene and branding checks pass.

For future Python implementation PRs:

```text
ruff check core/ --output-format=github
mypy core/ --show-error-codes
python -m pytest tests/ -v --tb=short --timeout=300 -x
Docker and repository-hygiene workflows
```

Benchmarks must include environment metadata and must not be presented as universal performance claims.

## Historical roadmap

The former V8.x roadmap is preserved at [`docs/archive/legacy/ROADMAP_V8_LEGACY_2026-07-30.md`](docs/archive/legacy/ROADMAP_V8_LEGACY_2026-07-30.md). It remains useful as project history but is not the current implementation-status source.

## Core rule

```text
Main tells what exists.
Research states what is being tested.
Roadmap orders work.
Receipts and benchmarks decide promotion.
```
