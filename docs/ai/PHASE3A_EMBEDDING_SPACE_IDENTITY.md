# 🧬 Phase 3A — Embedding Space Identity & Projection Contract Convergence

**Parent:** Issue #53  
**Admission:** Issue #327  
**Implementation PR:** #328 · DRAFT  
**Lifecycle:** IMPLEMENTED_CANDIDATE · TESTED_CODE_CHECKPOINT · UNWIRED · NOT ENABLED · NO RUNTIME AUTHORITY  
**Documentation impact:** `GITHUB_AND_NOTION`

> This file records the complete GitHub-side AI hand-off for Phase 3A. It is orientation and review evidence, not permission to activate semantic execution. Re-query live GitHub for the current PR head, base, reviews and workflow conclusions before treating any SHA below as the final merge candidate.

## 1. Why Phase 3A exists

Titan already had several embedding-related owners before this milestone:

- `core/embedding_registry.py` — historical model-name → expected-dimension registry;
- `core/embedding_store.py` — persistent derived vectors in `gs_vectors`;
- `core/embedding_projection.py` — projection identity, freshness/staleness, explicit rebuild and lexical fallback;
- `core/hybrid_retriever.py` — legacy on-demand `SentenceTransformer` dense retrieval;
- `core/semantic_dedup.py` — separate bounded semantic consumer;
- `core/capability_registry.py` — descriptive provider/capability metadata and deterministic selection explanation;
- `core/policy_kernel.py` — sole capability permission owner.

Therefore the real gap was **not** “Titan has no embeddings.” The gap was that these surfaces did not share one strict embedding-space identity sufficient to decide whether a persistent vector is actually compatible with the query space.

The central correctness rule is:

```text
same dimension
!=
same embedding space
```

A 384-dimensional vector from model/provider/revision A cannot be reused merely because another semantic path also produces 384 dimensions.

## 2. Live admission result

The pre-mutation audit classified the relevant requirements as follows:

| Requirement | Admission classification |
|---|---|
| historical model name + dimension | ALREADY_CONVERGED |
| model revision | PARTIAL |
| provider | REAL_GAP |
| normalization | REAL_GAP |
| pooling | REAL_GAP |
| distance metric | REAL_GAP |
| chunker version | REAL_GAP |
| preprocessing version | REAL_GAP |
| deterministic complete space ID | REAL_GAP |
| storage identity | PARTIAL |
| legacy-row compatibility | PARTIAL |
| lexical fallback | ALREADY_CONVERGED |
| erasure | ALREADY_CONVERGED |
| dimension fail-close before scoring | REAL_GAP |
| PolicyKernel ownership | ALREADY_CONVERGED |
| persistent projection runtime wiring | OUT_OF_SCOPE |

Because `REAL_GAP > 0`, Issue #327 admitted a bounded implementation. No duplicate Phase 3A child issue/branch existed when admission was created.

## 3. Accepted embedding-space identity

The existing `core/embedding_registry.py` owner is evolved rather than duplicated.

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

Every axis is identity-bearing. Changing any one produces a different space.

The descriptor is immutable metadata only. It does not:

- load or invoke an embedding model;
- probe a provider;
- perform network I/O;
- grant PolicyKernel permission;
- route the pipeline;
- mutate Canon or ESM;
- enable runtime execution.

## 4. Deterministic `embedding_space_id`

The ID is derived from canonical JSON containing the contract version and all nine axes:

```text
canonical JSON
→ UTF-8
→ SHA-256
→ embedding-space-v1:<digest>
```

Properties:

- deterministic across process restarts;
- deterministic across independently-created equivalent descriptors;
- stable field semantics;
- serializable;
- no Python process-salted `hash()`;
- no compatibility inference from dimension alone.

## 5. Projection/storage convergence

Phase 3A does **not** create a second vector database, table or store owner.

The existing chain remains:

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

This reuses the existing storage contract. No project schema v8 migration is required by the admitted implementation.

### Legacy rows

A historical row keyed by a plain model name does not contain the complete Phase 3A identity metadata. It is therefore **unknown/incompatible**, not auto-compatible.

When a typed space is expected, the historical axis differs from the `embedding-space-v1:<sha256>` axis. Existing projection classification therefore yields `STALE_MODEL`, and `resolve_or_fallback()` selects lexical fallback.

There is no automatic rebuild. Rebuild remains explicit and bounded.

## 6. Dimension fail-close boundary

Before Phase 3A, `DenseRetriever.retrieve()` computed normalized-vector similarity with a Python expression equivalent to:

```python
sum(a * b for a, b in zip(vec, q_emb))
```

Python `zip()` silently truncates to the shorter iterable. That could become a correctness defect once persistent vectors are reused across independently-described spaces.

Phase 3A adds a complete candidate-batch dimension preflight **before any similarity multiplication**:

```text
query vector
   +
all candidate vectors
   ↓
validate_pair_dimensions()
   ├─ all equal → scoring may begin
   └─ any mismatch → fail closed; no dense score
```

If a mismatch occurs, the existing `DenseRetriever` failure boundary returns no dense results; `HybridRetriever` retains the lexical/BM25 path. Persistent projection is still not wired into that runtime path.

The retained `zip()` dot product is now reached only after equality has been proven for the full candidate batch.

## 7. Acceptance evidence implemented in tests

`tests/test_phase3a_embedding_space.py` proves the new contract without a real provider or network call:

- stable canonical SHA-256 identity;
- changing each of the nine axes changes the space ID;
- same dimension with different spaces is incompatible;
- typed identity is stored through the existing projection/store owner;
- a typed exact match can be `FRESH`;
- a different same-dimension space cannot reuse that persistent vector;
- legacy plain-model rows are not auto-compatible;
- incompatible/legacy rows resolve to lexical fallback;
- vector dimension mismatch raises before scoring;
- a sentinel multiplication object proves no similarity multiplication occurs after dimension mismatch;
- equal-dimension legacy dense scoring still works;
- `purge_node(record_id)` still removes all embedding axes for the record.

Existing `tests/test_embedding_projection.py` continues to prove additional unchanged boundaries:

- projection reads do not mutate Canon;
- TruthGate remains reachable because projection is not wired into `pipeline.run()`;
- rebuild is explicit, bounded, idempotent and deterministic;
- corrupt projection metadata classifies `INVALID` rather than becoming semantic success;
- the projection feature flag defaults off;
- stale projection routing falls back lexically;
- coexisting projection axes classify deterministically and do not shadow exact matches.

## 8. Code-bearing exact-head evidence

The first complete code-bearing candidate after the mypy correction was:

```text
head:                     bf32ba7b41c70a0ffb606ae79d6b555b01e1b7f0
base main:                86ed963d2d31b9da174c88f0cf05cc27faced2b9
Full CI:                  #1207 · 31882546887 · SUCCESS
Ruff:                     SUCCESS
Mypy blocking gate:       SUCCESS
Pytest:                   SUCCESS
Coverage ratchet ≥74%:    SUCCESS
Dependency audit:         SUCCESS
Reproducible wheel:       SUCCESS
Deterministic SBOM:       SUCCESS
Docker:                   #796 · 31882546902 · SUCCESS
CodeQL:                   #45 · 31882546888 · SUCCESS
```

An earlier candidate failed the blocking mypy gate because `SentenceTransformer.encode()[0]` is typed as a Tensor while the first validator signature accepted only `Sequence[float]`. The implementation was corrected to a structural vector-like contract requiring only `__len__`, preserving strict dimension checking for Tensor/ndarray/list without weakening the fail-closed boundary.

Because this documentation commit necessarily moves the PR head, the evidence above becomes a **historical code-bearing checkpoint**. A fresh exact-head workflow set on the final PR head is mandatory before Ready/merge.

## 9. Authority and runtime state

Phase 3A changes compatibility metadata and a pre-score correctness guard only.

```text
Implemented contract:       yes, candidate in PR #328
Tested code checkpoint:     yes
Persistent projection wired:no
Semantic execution enabled: no
Provider invocation:        no
Network activation:         no
Default pipeline route:     unchanged
Canon mutation:             no
ESM mutation:               no
Runtime authority:          false
Production authority:       false
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

### Ownership remains unchanged

- `PolicyKernel` is still the sole permission owner.
- `CapabilityRegistry` is still descriptive/selection metadata, not permission authority.
- `EmbeddingRegistry` owns embedding compatibility metadata, not policy.
- `EmbeddingProjectionStore` is derived/rebuildable projection state, not truth authority.
- `EmbeddingStore` remains the sole existing persistent vector store owner for this path.
- `pipeline.py` remains the existing runtime route owner and is not modified by Phase 3A.

## 10. Parallel CSM isolation

Issue #325 / Draft PR #326 is a separate Code Structural Memory workstream and explicitly excludes embeddings/semantic search.

```text
#325 / #326 CSM
    └─ embeddings OUT OF SCOPE

#327 / #328 Phase 3A
    └─ CSM OUT OF SCOPE
```

Do not combine these diffs. If parallel work changes `main` before Phase 3A merge, rebase/update the Phase 3A branch and re-run exact-head evidence.

## 11. What Phase 3A does not prove

This milestone makes **no semantic retrieval-quality claim**.

Existing benchmark surfaces have different meanings:

- `benchmarks/bench_embedding_projection.py` measures projection-contract overhead with a synthetic embedder;
- `benchmarks/bench_retrieval_routing.py` measures lifecycle/cost behavior of the existing Hybrid/Dense route.

Neither proves Titan-specific semantic quality.

Any future claim about persistent semantic retrieval quality belongs to a separately admitted later phase with a reproducible Titan-specific benchmark.

## 12. Explicitly out of scope

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
autonomous indexing
background daemon / scheduler / worker
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

## 13. Review / readiness checklist

Before PR #328 can become Ready:

- [x] live baseline and owners re-audited;
- [x] `REAL_GAP > 0` demonstrated;
- [x] bounded child Issue #327 created;
- [x] implementation isolated to dedicated branch / Draft PR #328;
- [x] deterministic full-space identity implemented;
- [x] same-dimension incompatible spaces fail closed;
- [x] legacy projection rows fail closed;
- [x] dimension mismatch fails before scoring;
- [x] erasure semantics preserved;
- [x] no runtime/Canon/policy authority introduced;
- [x] code-bearing checkpoint Full CI / Docker / CodeQL green;
- [x] ADR added;
- [x] existing Notion page received a DRAFT admission snapshot and read-back;
- [ ] final GitHub documentation candidate committed;
- [ ] fresh exact-head CI/Docker/CodeQL evaluated on final candidate;
- [ ] current review threads/comments/submitted reviews re-audited;
- [ ] current `main` re-fetched and base drift resolved if present;
- [ ] existing Notion page updated to the final candidate head and read back;
- [ ] PR metadata marks Notion synchronization `SYNCED` only after that read-back;
- [ ] Ready aggregate `Titan aggregate merge evidence` succeeds.

## 14. Post-merge boundary

Protected merge is not the end of evidence collection. After merge, verify the resulting `main`, parent, signature and actual post-merge workflows. Update GitHub lifecycle truth if needed, update the **same existing** Notion page to FINAL, read it back, then close Issue #327 as completed.

Do **not** start Phase 3B automatically.

A possible later Phase 3B may evaluate local embedding execution / persistent projection runtime integration plus a Titan-specific semantic benchmark, but it requires a fresh explicit admission.
