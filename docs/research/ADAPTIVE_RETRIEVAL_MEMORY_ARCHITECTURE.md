# Adaptive Retrieval and Memory Architecture for Titan

Status: research-to-implementation proposal  
Scope: architecture patterns only; no runtime authority change

## 1. Decision

Titan should improve speed, memory selectivity, fallback behavior, and context assembly without weakening its epistemic kernel.

The authority chain remains unchanged:

```text
Retrieval / Memory Candidate
→ FactsPack / ContextPack
→ TRACE / provenance
→ Guardian
→ TruthGate
→ controlled answer
```

No fast path may bypass this chain or gain direct Canon authority.

## 2. Approved architecture patterns

### 2.1 Cheap-first task and cost routing

```text
deterministic rules
→ ambiguous-only lightweight classifier with timeout
→ route by expected value and cost
```

Map this onto existing Titan components:

- `BudgetPlanner` remains retrieval-cost authority;
- RCO-1 remains orientation and uncertainty observer;
- `ComputeController` remains compute admission boundary;
- optional model classification is allowed only for ambiguous requests and must fail back to deterministic routing.

Required properties:

- bounded timeout;
- deterministic fallback;
- route decision recorded in structured TRACE or metrics;
- no remote classifier call when local policy forbids egress;
- no change to TruthGate authority.

### 2.2 Selective memory candidate extraction

Titan should extract only durable, useful user/project information instead of storing whole conversations.

```text
conversation/event
→ candidate extractor
→ sensitivity and policy filter
→ provenance attachment
→ WorkingMemoryGate disposition
→ Write Gate
→ optional Canon / user-context admission
```

The extractor is proposal-only and cannot write directly.

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

Vector, BM25, and graph indexes are derived acceleration structures, never sources of truth.

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

Independent read-only context sources may be assembled concurrently:

- user context;
- relevant evidence;
- world/schema cache;
- policy context;
- deferred pointers.

Only versioned and safely invalidated data may be cached. Cache entries must include policy/version dependencies and must never hide a revoked or erased record.

## 3. Explicitly rejected patterns

Do not adopt:

- direct LLM-to-memory writes;
- age-only deletion such as keeping only the latest N memories;
- provider-first core architecture;
- a single opaque confidence score;
- unversioned embedding reuse;
- automatic self-modification of system instructions without an admission boundary;
- product UI concerns as kernel responsibilities.

## 4. Implementation slices

### PR-ARM-01 — Routing integration

- execute `RetrievalPlan.mode` in the query pipeline;
- prove lexical mode does not call dense/RRF;
- preserve FactsPack/TRACE/Guardian/TruthGate;
- record chosen mode and reason codes;
- benchmark cold and warm paths.

This may build on or follow draft PR #91.

### PR-ARM-02 — Rebuildable embedding projection contract

- define projection identity: record ID + content hash + embedding model/version;
- separate model lifecycle from per-query candidate sets;
- add stale-vector detection and reindex hooks;
- prove lexical fallback when the projection is unavailable.

No Canon schema authority change.

### PR-ARM-03 — Selective memory candidate extractor (shadow)

- immutable candidate contract;
- exact source spans;
- sensitivity filtering;
- dedup/supersession hints;
- maximum candidate budget;
- shadow-only metrics;
- zero writes to Canon or user memory.

### PR-ARM-04 — Candidate admission integration

Only after shadow evaluation:

- WorkingMemoryGate disposition;
- explicit Write Gate;
- context-specific admission policy;
- revocation and GDPR erasure compatibility;
- audit receipts.

### PR-ARM-05 — Versioned parallel context assembly

- parallel read-only context sources;
- strict final ContextPack budget;
- cache version keys and invalidation;
- cancellation/timeouts;
- no semantic change when cache is disabled.

## 5. Acceptance criteria

- query path remains read-only;
- no fast route bypasses TruthGate;
- every admitted memory has provenance and a policy receipt;
- embedding model changes cannot silently mix incompatible vectors;
- flags OFF preserve legacy behavior;
- lexical fallback remains functional without external providers;
- latency improvement is measured, not asserted;
- shadow evaluation precedes memory-write authority;
- erasure and policy revocation invalidate derived caches and projections.

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

## 7. Prior art

A review of external open-source assistants, including `juanyamels-eng/daya-ai`, helped validate several practical orchestration patterns. Those references remain prior art only. Titan's module names, PR names, contracts, authority model, and implementation remain independent.

## 8. Architectural summary

```text
adaptive routing + selective memory + graceful fallback + rebuildable projections
+
provenance + epistemic status + TRACE + Guardian + TruthGate + Write Gate
```

The goal is to make Titan cheaper, faster, and more responsive without weakening evidence, governance, or local-first boundaries.