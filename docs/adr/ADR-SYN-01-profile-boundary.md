# ADR-SYN-01 — Knowledge Capsule boundary

**Status:** Proposed  
**Date:** 2026-07-26  
**Profile:** Velantrim Synaptic Exo-Cortex  

## Context

Titan needs a compact, source-linked representation of meaning before a Semantic Reader or Working Memory Gate can be integrated safely. The representation must not silently become Canon, must preserve exact provenance, and must remain independent of any LLM provider.

## Decision

Add immutable stdlib-only contracts in `core/knowledge_capsule.py`:

- `SourceSpan` identifies an exact Unicode character range in one source revision and verifies it with SHA-256.
- `CapsuleClaim` separates extraction confidence from truth confidence and preserves modality, qualifiers, uncertainty, applicability conditions, and temporal scope.
- `KnowledgeCapsule` is a deterministic content-addressed extraction proposal. Its identity excludes timestamps, caller-provided claim IDs, Reader metadata, and quality metrics.

## Invariants

1. Every claim has at least one valid source span.
2. A span uses Python Unicode code-point offsets and a lowercase SHA-256 digest of the exact UTF-8 encoded substring.
3. A capsule is immutable after construction.
4. `extraction_confidence` and `truth_confidence` are distinct values.
5. A hypothesis cannot be created with `truth_confidence=1.0`.
6. Every span in a capsule belongs to the capsule source document.
7. A supplied `capsule_id` must equal the deterministic content identity.
8. A capsule is a proposal/projection, never Canon by itself.

## Consequences

- The contract is testable without an LLM, database, graph backend, or network.
- Reprocessing identical extraction output produces the same capsule identity for deduplication, even when the replaceable Reader provider changes.
- Changing provenance or semantic content changes capsule identity.
- Semantic Reader integration remains blocked until it can produce contract-valid capsules.

## Out of scope

- LLM calls or prompt design;
- persistence schema;
- graph relation admission;
- query-pipeline integration;
- Crystal admission;
- Canon or ESM mutation.

## Canon/Profile boundary

Titan may create a capsule and later propose candidate claims. Crystal remains responsible for evidence review, Guardian, TruthGate, and any admission into Canon.
