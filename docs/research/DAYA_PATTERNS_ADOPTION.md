# DAYA Patterns Adoption Plan for Titan

Status: research-to-implementation proposal  
Reviewed source: `juanyamels-eng/daya-ai` (`main`, 2026-07-30)  
License note: DAYA is MIT-licensed. This document adopts architectural patterns only; any future code reuse must preserve attribution and license obligations.

## 1. Decision

DAYA is not an alternative to Titan's epistemic kernel. It is a useful reference for product-facing orchestration, selective memory, graceful retrieval degradation, and model-cost routing.

Titan keeps its existing authority chain:

```text
Retrieval / Memory Candidate
→ FactsPack / ContextPack
→ TRACE / provenance
→ Guardian
→ TruthGate
→ controlled answer
```

No DAYA-inspired fast path may bypass this chain or gain direct Canon authority.

## 2. Patterns approved for adaptation

### 2.1 Cheap-first task and cost routing

Adopt the pattern:

```text
deterministic rules
→ ambiguous-only lightweight classifier with timeout
→ route by expected value and cost
```

Map it onto existing Titan components instead of adding a new service:

- `BudgetPlanner` remains the retrieval-cost authority;
- RCO-1 remains the orientation and uncertainty observer;
- `ComputeController` remains the compute admission boundary;
- optional model classification is allowed only for ambiguous requests and must fail back to deterministic routing.

Required properties:

- bounded timeout;
- deterministic fallback;
- route decision recorded in structured TRACE or metrics;
- no remote classifier call when local policy forbids egress;
- no change to TruthGate authority.

### 2.2 Selective memory candidate extraction

Adopt the idea of extracting only durable, useful user/project information instead of storing whole conversations.

Titan-specific flow:

```text
conversation/event
→ candidate extractor
→ sensitivity and policy filter
→ provenance attachment
→ WorkingMemoryGate disposition
→ Write Gate
→ optional Canon / user-context admission
```

The extractor is proposal-only. It cannot write directly.

Candidate requirements:

- short normalized claim;
- subject/context ID;
- source message spans;
- extraction confidence separated from truth confidence;
- sensitivity flags;
- temporal scope;
- duplicate/supersession hints;
- reason for retention.

### 2.3 Derived indexes as rebuildable projections

Adopt the principle that vector, BM25, and graph indexes are derived acceleration structures, never the source of truth.

```text
Canon / Evidence Store
├── BM25 projection
├── embedding projection
├── graph projection
└── caches
```

Required properties:

- rebuild from authoritative records;
- model/version identity stored with vectors;
- reindex required when embedding model changes;
- stale projection detection;
- fail-safe lexical fallback;
- projection loss must not imply knowledge loss.

### 2.4 Graceful lexical fallback

If embeddings, ANN, or a provider are unavailable, Titan must retain a deterministic lexical route.

```text
lexical: NGram/BM25
hybrid: lexical + dense + RRF
bounded deep: hybrid + permitted graph expansion
```

The selected mode must come from `RetrievalPlan`, not an ad-hoc caller decision.

### 2.5 Parallel context assembly with versioned cache

Independent context sources may be assembled concurrently:

- user context;
- relevant evidence;
- world/schema cache;
- policy context;
- deferred pointers.

Only versioned and safely invalidated data may be cached. Cache entries must include policy/version dependencies and must never hide a revoked or erased record.

## 3. Patterns explicitly rejected

Do not adopt:

- direct LLM-to-memory writes;
- age-only deletion such as keeping only the latest N memories;
- provider-first core architecture;
- a single opaque confidence score;
- unversioned embedding reuse;
- automatic self-modification of system instructions without an admission boundary;
- product UI concerns as kernel responsibilities.

## 4. Implementation slices

### PR-DAYA-01 — Routing integration

Scope:

- execute `RetrievalPlan.mode` in the query pipeline;
- prove lexical mode does not call dense/RRF;
- preserve FactsPack/TRACE/Guardian/TruthGate;
- record the chosen mode and reason codes;
- benchmark cold and warm paths.

This may build on or follow the retrieval-routing contract work in draft PR #91.

### PR-DAYA-02 — Rebuildable embedding projection contract

Scope:

- define projection identity: record ID + content hash + embedding model/version;
- separate model lifecycle from per-query candidate sets;
- add stale-vector detection and reindex hooks;
- prove lexical fallback when the projection is unavailable.

No Canon schema authority change.

### PR-DAYA-03 — Selective memory candidate extractor (shadow)

Scope:

- immutable candidate contract;
- exact source spans;
- sensitivity filtering;
- dedup/supersession hints;
- maximum candidate budget;
- shadow-only metrics;
- zero writes to Canon or user memory.

### PR-DAYA-04 — Candidate admission integration

Only after shadow evaluation:

- WorkingMemoryGate disposition;
- explicit Write Gate;
- context-specific admission policy;
- revocation and GDPR erasure compatibility;
- audit receipts.

### PR-DAYA-05 — Versioned parallel context assembly

Scope:

- parallel read-only context sources;
- strict final ContextPack budget;
- cache version keys and invalidation;
- cancellation/timeouts;
- no semantic change when cache is disabled.

## 5. Acceptance criteria

The work is acceptable only if:

- query path remains read-only;
- no fast route bypasses TruthGate;
- every admitted memory has provenance and a policy receipt;
- embedding model changes cannot silently mix incompatible vectors;
- flags OFF preserve legacy behavior;
- lexical fallback remains functional without external providers;
- latency improvement is measured, not asserted;
- shadow evaluation precedes memory-write authority;
- erasure and policy revocation invalidate all derived caches and projections.

## 6. Metrics

```text
route_distribution
route_reason_codes
lexical_latency_ms
hybrid_latency_ms
dense_call_count
retriever_rebuild_count
projection_cache_hit_rate
projection_stale_rate
memory_candidate_rate
memory_candidate_rejection_rate
memory_duplicate_rate
memory_sensitive_block_rate
context_cache_hit_rate
truth_gate_bypass_count = 0
query_path_write_count = 0
```

## 7. Architectural summary

```text
DAYA contributes practical orchestration patterns:
fast routing + selective memory + graceful fallback + rebuildable indexes

Titan contributes the authority model:
provenance + epistemic status + TRACE + Guardian + TruthGate + Write Gate
```

The integration goal is not to make Titan look like DAYA. The goal is to make Titan cheaper and more responsive without weakening its evidence and governance boundaries.
