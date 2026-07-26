# Velantrim Synaptic Exo-Cortex — Implementation Plan v1.0

**Status:** `PROPOSED · TITAN IMPLEMENTATION PROFILE · FEATURE-FLAGGED`  
**Date:** 2026-07-26  
**Notion mirror:** https://app.notion.com/p/3a9ac84d054781a19cd5c0ee8ac6e063

## 1. Architectural boundary

```text
Native Kernel -> permanent substrate-neutral invariants
Synaptic Exo-Cortex -> cognitive implementation profile
Titan -> experimental runtime and home of the new code
Crystal -> verified admission boundary for Canon
LLM -> replaceable Semantic Reader and answer renderer
```

Titan may understand, compress, route, and propose candidate claims. Crystal must independently verify admission through evidence checks, Guardian, TruthGate, and Receipt/Audit. The Synaptic Profile never receives direct authority to write into Canon.

## 2. Goal

Transform large documents and long histories into source-linked semantic capsules so that the LLM context window is used as working memory rather than permanent storage.

```text
Raw Evidence
-> Semantic Reader
-> Knowledge Capsule
-> Working Memory Gate
-> ContextPack
-> Answer
-> source-span verification
```

## 3. Mandatory invariants

1. Raw evidence is immutable after ingest, except through an explicit erasure/redaction control path.
2. Every extracted claim has exact source spans and verifiable content hashes.
3. `extraction_confidence` is distinct from `truth_confidence`.
4. Qualifiers, uncertainty, temporal scope, and applicability conditions must survive compression.
5. A Knowledge Capsule is a proposal/projection, never Canon by itself.
6. Non-active information defaults to `DEFER`, not deletion.
7. The ordinary query path remains read-only with respect to Canon and ESM.
8. TRACE stores structured provenance and reason codes, not hidden chain-of-thought.
9. Reader interfaces remain provider-neutral.
10. Recall is bounded and cannot loop indefinitely.
11. Working-memory eviction is separate from GDPR erasure.
12. Graph relations derived by a model remain candidates until independently admitted.

## 4. P0 scope

P0 includes:

- immutable `KnowledgeCapsule` contracts;
- provider-neutral `SemanticReader` contract;
- a replaceable LLM reader adapter;
- `WorkingMemoryGate` built on the existing `AttentionRouter` features;
- a budgeted `ContextPack`;
- structured TRACE events;
- shadow integration before active routing;
- one bounded recall round.

P0 excludes:

- Human Context Layer;
- Companion Policy;
- autonomous agency;
- learned gate weights;
- Transformer surgery;
- automatic causal-edge admission;
- a Crystal adapter before the Capsule API stabilizes.

## 5. Pull-request sequence

### PR-SYN-01 — Knowledge Capsule Contract

Files:

```text
core/knowledge_capsule.py
tests/test_knowledge_capsule.py
docs/adr/ADR-SYN-01-profile-boundary.md
```

Deliverables:

- immutable `SourceSpan`, `CapsuleClaim`, and `KnowledgeCapsule`;
- exact offsets and SHA-256 verification;
- stable content identity for deduplication;
- claim-level modality, qualifiers, uncertainty, and temporal scope;
- separate extraction and truth confidence;
- fail-closed validation.

No LLM call, pipeline mutation, graph write, or Canon admission is included.

### PR-SYN-02 — Semantic Reader Contract

Add a provider-neutral interface and deterministic `ExtractiveReader`. This proves span validation, modality preservation, idempotency, and failure handling before introducing a model.

### PR-SYN-03 — LLM Reader Adapter

Add structured output, chunking, merge rules, provider/model/prompt versioning, timeouts, budgets, and mandatory span validation. Model output remains untrusted extraction material.

### PR-SYN-04 — Working Memory Gate

Implement the explicit policy:

```text
Safety -> Eligibility -> Protection -> Ranking -> Budget -> Disposition
```

Allowed dispositions:

- `ACTIVE`
- `COMPRESS`
- `DEFER`
- `QUARANTINE`
- `EXCLUDE`

`DELETE` is intentionally absent.

The gate reuses existing Titan components:

- `AttentionRouter` for explainable ranking features;
- `recall_policy` for safety filtering;
- `GoalFrame` for current intent;
- `ComputeController` for retrieval and compute budgets;
- `CausalGraph` for protected graph-relevant evidence;
- salience only as a secondary signal.

### PR-SYN-05 — ContextPack

Build a compact package containing active claims, compressed capsules, evidence spans, conflicts, uncertainty notes, and deferred pointers within a strict token budget.

### PR-SYN-06 — Shadow Integration

The legacy path continues producing the answer. The Synaptic path builds a preview only.

```text
Retrieval
|- Legacy FactsPack -> current answer
`- Synaptic Gate -> ContextPack preview + metrics
```

Shadow failures must never break `/query` or mutate memory.

### PR-SYN-07 — Active ContextPack

Enable the new context path only behind a feature flag after it meets baseline quality, faithfulness, latency, and rollback requirements.

### PR-SYN-08 — Bounded Recall Controller

Allow at most one additional recall round for deferred capsules, raw source spans, or bounded graph expansion. All retrieval still passes existing safety policy.

### PR-SYN-09 — Crystal Admission Adapter

This is the final stage. The adapter is version/capability-pinned and may submit only candidate claims into `Pending/Observed`. It has no direct-L3 or bypass API.

Forbidden behavior includes:

```text
canonize_directly()
skip_guardian()
skip_truth_gate()
force_validated()
```

## 6. Feature flags

```env
ENABLE_SYNAPTIC_PROFILE=false
ENABLE_SYNAPTIC_SHADOW=false
ENABLE_SEMANTIC_READER=false
ENABLE_WORKING_MEMORY_GATE=false
```

With all flags disabled, Titan must preserve legacy behavior.

## 7. Minimum test matrix

- source offsets and hashes match the original input;
- every claim has provenance;
- conditional statements remain conditional;
- hypotheses do not become absolute world facts;
- identical content produces stable capsule identity;
- malformed model output fails closed;
- restricted or erased data never enters ContextPack;
- `DEFER` never deletes source material;
- query execution never mutates Canon or ESM;
- shadow mode never changes the answer;
- feature flags provide a complete rollback path;
- conflicting claims remain separate and explicit;
- prompt injection inside a document is treated as content, not instruction.

## 8. Metrics

```text
claim_without_span_rate
span_hash_failure_rate
conditionality_preservation_rate
source_coverage
compression_ratio
context_pack_tokens
protected_claim_loss_rate
unsupported_answer_claim_rate
recall_success_rate
legacy_vs_synaptic_quality_delta
latency_delta
```

## 9. Stop conditions

Pause and redesign if any of the following occurs:

- qualifiers are regularly lost;
- source spans or hashes are unreliable;
- restricted data enters active context;
- the Synaptic path mutates Canon;
- flags-off behavior differs from legacy behavior;
- answer faithfulness becomes worse than baseline;
- provider-specific details leak into the capsule schema;
- model-generated graph links are treated as proven causality.

## 10. P0 Definition of Done

```text
Raw document
-> immutable Capsule with exact provenance
-> Working Memory disposition
-> budgeted ContextPack
-> evidence-backed answer
-> optional single raw recall
-> complete structured TRACE
-> zero Canon mutation from query path
```

## 11. First executable action

```text
branch: feature/synaptic-knowledge-capsule
PR-SYN-01: Immutable KnowledgeCapsule with source provenance
commit: feat(synaptic): add immutable knowledge capsule contract
```

The next PR does not start until the previous one passes tests, review, and invariant checks.

> **Titan understands and proposes. Crystal verifies and admits. Kernel preserves invariants. LLM remains replaceable.**
