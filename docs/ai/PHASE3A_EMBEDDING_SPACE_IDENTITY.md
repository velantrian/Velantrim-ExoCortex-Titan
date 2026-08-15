# 🧬 Phase 3A — Embedding Space Identity & Projection Contract Convergence

**Parent:** Issue #53  
**Admission / closure:** Issue #327  
**Implementation PR:** #328 · MERGED  
**Implementation merge:** `4932727c348ec967564d8babf80e25ca82bce8be`  
**Accepted implementation head:** `96f4aad2ae4a65203cc133dbe2af40ed869c99e8`  
**Lifecycle:** `IMPLEMENTED_BOUNDED · TESTED · UNWIRED · NOT ENABLED · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`  
**Documentation impact:** `GITHUB_AND_NOTION`

> This file is the GitHub-side AI hand-off for the closed Phase 3A implementation. It records a bounded contract milestone, not permission to activate semantic execution. Always re-query live GitHub for the current repository head, Issue #53 lifecycle and any later explicitly admitted phase.

## 1. What Phase 3A solved

Titan already had several embedding-related owners before this milestone:

- `core/embedding_registry.py` — historical model-name → expected-dimension registry;
- `core/embedding_store.py` — persistent derived vectors in `gs_vectors`;
- `core/embedding_projection.py` — projection identity, freshness/staleness, explicit rebuild and lexical fallback;
- `core/hybrid_retriever.py` — legacy on-demand `SentenceTransformer` dense retrieval;
- `core/semantic_dedup.py` — separate bounded semantic consumer;
- `core/capability_registry.py` — descriptive provider/capability metadata and deterministic selection explanation;
- `core/policy_kernel.py` — sole capability permission owner.

The gap was therefore not “Titan has no embeddings.” It was the absence of one strict identity sufficient to prove that a stored vector and a query belong to the same semantic space.

The core correctness rule remains:

```text
same dimension
!=
same embedding space
```

## 2. Accepted identity contract

The existing `core/embedding_registry.py` owner was evolved rather than duplicated.

`EmbeddingSpaceDescriptor` binds all compatibility-bearing axes:

```text
provider_id
model
model_revision
dimension
normalization
pooling
distance_metric
chunker_version
preprocessing_version
```

Every axis is identity-bearing. Changing any one creates a different embedding space.

The descriptor is immutable metadata only. It does not load a model, invoke or probe a provider, perform network I/O, grant PolicyKernel permission, route the pipeline, mutate Canon/ESM or enable runtime execution.

## 3. Deterministic `embedding_space_id`

The ID is derived as:

```text
canonical JSON
→ UTF-8
→ SHA-256
→ embedding-space-v1:<digest>
```

The canonical payload contains the contract version plus all nine identity axes. Python's process-salted `hash()` is not used.

Properties proven by tests:

- equivalent independently-created descriptors produce the same ID;
- every identity-axis change changes the ID;
- equal dimensions do not imply compatibility;
- the representation is stable and serializable across process restarts.

## 4. Projection/storage convergence

Phase 3A created no second registry, vector database, table or projection owner.

```text
EmbeddingSpaceDescriptor
        ↓
embedding_space_id
        ↓
EmbeddingProjectionIdentity.model_name
        + fixed descriptor-binding model_version
        ↓
EmbeddingProjectionStore.storage_key()
        ↓
existing EmbeddingStore.model_name TEXT axis
        ↓
existing gs_vectors PK(node_id, model_name)
```

The existing storage contract was sufficient, so **project schema remains v7**. No schema v8 migration was admitted or needed.

### Legacy rows fail closed

Historical rows keyed only by a plain model name do not contain all Phase 3A identity metadata. They are therefore unknown/incompatible, not implicitly compatible.

When a typed space is expected, the historical axis differs from `embedding-space-v1:<sha256>`. The existing projection classifier yields an incompatible/stale state and `resolve_or_fallback()` preserves lexical fallback.

State detection does not rebuild anything. Rebuild remains explicit and bounded.

## 5. Dimension fail-close boundary

Before Phase 3A, legacy dense scoring used a Python expression equivalent to:

```python
sum(a * b for a, b in zip(vec, q_emb))
```

Python `zip()` silently truncates unequal iterables. Phase 3A added a complete candidate-batch dimension preflight **before any similarity multiplication**:

```text
query vector
   +
all candidate vectors
   ↓
validate_pair_dimensions()
   ├─ all equal → scoring may begin
   └─ any mismatch → fail closed; no dense score
```

If one vector mismatches, the existing DenseRetriever failure boundary returns no dense results and HybridRetriever retains its lexical/BM25 fallback. Persistent projection was not wired into that runtime route.

The retained `zip()` dot product is reachable only after dimension equality has been proven for the complete candidate batch.

## 6. Acceptance tests

`tests/test_phase3a_embedding_space.py` proves, without a real provider or network call:

- stable canonical SHA-256 identity;
- all nine axes affect identity;
- same-dimension different spaces are incompatible;
- typed identity reuses the existing projection/store owner;
- exact typed identity can classify `FRESH`;
- same-dimension incompatible space cannot reuse the vector;
- legacy plain-model rows are not auto-compatible;
- incompatible/legacy rows preserve lexical fallback;
- vector dimension mismatch raises before scoring;
- sentinel multiplication proves no similarity multiplication occurs after mismatch;
- equal-dimension legacy dense scoring still works;
- `purge_node(record_id)` still removes every projection axis for the record.

Existing projection tests continue to prove that projection reads do not mutate Canon, rebuild is explicit/idempotent/bounded, corrupt metadata classifies invalid rather than successful, the projection feature flag defaults off, and stale projection routing falls back lexically.

## 7. Exact accepted evidence

### Final PR candidate before protected merge

```text
PR:                       #328
head:                     96f4aad2ae4a65203cc133dbe2af40ed869c99e8
base:                     86ed963d2d31b9da174c88f0cf05cc27faced2b9
Full CI:                  #1210 · 31882948349 · SUCCESS
Docker:                   #799  · 31882948356 · SUCCESS
CodeQL:                   #48   · 31882948357 · SUCCESS
READY aggregate:          #1315 · 31883253917 · SUCCESS
reviews:                  0 submitted
review threads:           0
PR comments:              0
Notion synchronization:   SYNCED after same-page read-back
```

### Protected implementation merge

```text
merge/main:               4932727c348ec967564d8babf80e25ca82bce8be
parent:                   86ed963d2d31b9da174c88f0cf05cc27faced2b9
signature:                VERIFIED / valid
accepted PR head:         96f4aad2ae4a65203cc133dbe2af40ed869c99e8
```

### Exact implementation post-merge evidence

```text
Full CI:                  #1211 · 31883324866 · SUCCESS
Docker:                   #800  · 31883324890 · SUCCESS
CodeQL:                   #49   · 31883324957 · SUCCESS
aggregate merge evidence: #1316 · 31883324900 · SUCCESS
```

Full CI #1211 includes the blocking mypy gate, full pytest, core coverage ratchet ≥74%, dependency audit, reproducible wheel, deterministic SBOM and architecture/project-state/KB guards.

No local CLI result and no Codex approval are claimed. Exact GitHub workflow evidence is the acceptance basis.

## 8. Authority and runtime state

Phase 3A changes compatibility metadata and a pre-score correctness guard only.

```text
Implemented:                    yes
Tested:                         yes
Persistent projection wired:    no
Semantic execution enabled:     no
Provider invocation/probing:    no
Network activation:             no
Default pipeline route changed: no
Canon mutation:                 no
ESM mutation:                   no
Runtime authority:              false
Production authority:           false
```

Frozen project state remains:

```text
Continuity:             12/12
schema:                 v7
runtime enabled:        false
Operator GO:            false
runtime authority:      false
production authority:   false
Canon:                   local
remote Canon:            forbidden
```

Ownership remains unchanged:

- `PolicyKernel` is the sole permission owner;
- `CapabilityRegistry` is descriptive/selection metadata only;
- `EmbeddingRegistry` owns embedding compatibility metadata, not policy or execution;
- `EmbeddingProjectionStore` remains derived/rebuildable projection state without truth authority;
- `EmbeddingStore` remains the existing persistent vector-store owner for this path;
- `pipeline.py` remains the runtime-route owner and was not modified by Phase 3A.

## 9. Parallel CSM isolation

Issue #325 / PR #326 is a separate Code Structural Memory workstream and explicitly excludes embeddings/semantic search. No CSM changes were mixed into #327/#328.

## 10. What Phase 3A does not prove

Phase 3A makes **no semantic retrieval-quality claim**.

`benchmarks/bench_embedding_projection.py` measures projection-contract overhead with a synthetic embedder. `benchmarks/bench_retrieval_routing.py` measures lifecycle/cost behavior of the existing Hybrid/Dense path. Neither proves Titan-specific semantic quality.

Any live persistent projection integration, provider execution or semantic-quality benchmark belongs to a separately admitted later phase.

## 11. Explicitly not authorized

```text
persistent projection live retrieval wiring
pipeline.py default-route replacement
remote embeddings
OpenAI/Gemini/Cohere provider calls
provider probing/invocation
network activation
reranker integration
LLM execution
ADAO / ARM-04
autonomous/background indexing
new API endpoint
Operator GO
runtime authority
production authority
Canon or ESM mutation
remote Canon
schema v8
Continuity 13/12
semantic-quality marketing claims
```

## 12. Closure semantics

When this reconciliation is read from `main`, Phase 3A's GitHub technical record is reconciled as **IMPLEMENTED_BOUNDED**. The existing Notion page must carry the same final lifecycle and exact evidence before Issue #327 is finally closed as completed.

Parent Issue #53 remains a separate open architecture line. Phase 3A closure does **not** admit or start Phase 3B.
