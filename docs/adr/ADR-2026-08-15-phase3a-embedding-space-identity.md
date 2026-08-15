# ADR — Phase 3A Embedding Space Identity & Projection Contract Convergence

**Date:** 2026-08-15  
**Status:** Accepted / implemented through protected-merged PR #328  
**Parent:** #53  
**Admission / closure:** #327  
**Implementation merge:** `4932727c348ec967564d8babf80e25ca82bce8be`

## Context

Titan already had several embedding-related surfaces:

- `core/embedding_registry.py` owns the historical model-name → dimension registry;
- `core/embedding_store.py` owns persistent derived vectors;
- `core/embedding_projection.py` owns projection identity, staleness, explicit rebuild and lexical fallback;
- `core/hybrid_retriever.py` performs legacy on-demand dense retrieval;
- `core/capability_registry.py` describes provider/capability candidates;
- `core/policy_kernel.py` remains the sole permission owner.

The missing contract was not "embeddings exist". The gap was that a persistent vector space was not uniquely identified by every compatibility-bearing axis. Equal dimensions are insufficient: two providers/models/revisions or two normalization/pooling/metric/chunking/preprocessing contracts may emit vectors of the same length while representing incompatible spaces.

A second correctness gap existed in the legacy dense scorer: Python `zip()` silently truncates unequal vectors. That was benign only while corpus/query embeddings were created by one model invocation path. It would be unsafe before future persistent-vector reuse.

## Decision

### 1. One typed embedding-space identity

Evolve the existing `core/embedding_registry.py` owner with a frozen `EmbeddingSpaceDescriptor` containing:

- `provider_id`;
- `model`;
- `model_revision`;
- `dimension`;
- `normalization`;
- `pooling`;
- `distance_metric`;
- `chunker_version`;
- `preprocessing_version`.

All fields are identity-bearing. Changing any field creates a different embedding space.

### 2. Deterministic ID

`embedding_space_id` is derived as SHA-256 over canonical JSON with sorted keys and compact separators. Python's salted `hash()` is not used.

The storage-safe form is:

```text
embedding-space-v1:<sha256>
```

The identifier is deterministic across independently constructed equivalent descriptors and process restarts.

### 3. Reuse existing projection/storage owners

No second registry, vector database or projection owner is introduced.

The full `embedding_space_id` is supplied through the existing `EmbeddingProjectionIdentity.model_name` axis, while a fixed descriptor-binding version is supplied through its `model_version` axis. `EmbeddingProjectionStore` already folds those axes into `EmbeddingStore.model_name`, whose SQLite type is `TEXT` and whose primary key is already `(node_id, model_name)`.

Therefore Phase 3A requires no project schema v8 migration.

### 4. Legacy rows fail closed

Existing projection rows whose axis uses a plain historical model name do not contain all Phase 3A identity dimensions. They are therefore **unknown/incompatible**, not implicitly compatible.

A typed expected identity has a different model axis (`embedding-space-v1:<sha256>`), so the existing projection classifier returns an incompatible/stale state and retrieval falls back lexically. No automatic rebuild occurs.

### 5. Dimension mismatch is rejected before scoring

`DenseRetriever.retrieve()` performs a complete dimension preflight for every candidate vector against the query vector before calculating any dot product. If one vector differs in length, dense retrieval fails closed and returns no dense result; the existing HybridRetriever then retains its lexical/BM25 fallback behavior.

`zip()` remains only after equality has already been proven for the entire candidate batch.

## Authority boundaries

This decision grants no runtime or production authority.

- `PolicyKernel` remains the sole capability permission owner.
- `CapabilityRegistry` remains descriptive/selection metadata only.
- `EmbeddingRegistry` owns compatibility metadata only; it is not a policy engine or provider executor.
- `EmbeddingProjectionStore` remains derived/rebuildable and has no Canon/ESM truth authority.
- `pipeline.py` default routing is unchanged.
- No provider probing/invocation or network call is added.
- No remote embedding provider is activated.
- No background indexing worker, daemon or scheduler is added.
- No automatic projection rebuild is added.

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

## Erasure and deletion

The existing erasure contract remains valid. `EmbeddingStore.purge_node(record_id)` deletes all projection axes for the record, independent of the embedding-space ID encoded into `model_name`. Phase 3A adds no deletion owner or erasure path.

## Consequences

### Positive

- equal dimensions can no longer imply compatibility;
- every declared semantic-space axis participates in deterministic identity;
- legacy vectors are not reused without complete metadata;
- future persistent projection integration has an explicit fail-closed boundary;
- no DB migration or duplicate vector store is required;
- no runtime route changes are needed for Phase 3A.

### Trade-offs

- historical projection rows are not auto-adopted into the new typed space even when a human believes they were produced by the same model; they require explicit bounded rebuild under complete metadata;
- callers that eventually write typed persistent projections must supply all descriptor axes rather than only a model name;
- semantic quality is not established by this contract. A later phase would require separate admission and reproducible Titan-specific benchmarks before quality claims.

## Rejected alternatives

### Create a new EmbeddingRegistry

Rejected: duplicates ownership and creates drift between model dimensions and full-space identity.

### Create a new vector database/table

Rejected: the existing `EmbeddingStore` already provides persistent derived-vector storage and erasure integration.

### Add schema v8 columns for every identity axis

Rejected for Phase 3A: the existing TEXT storage axis safely carries the deterministic full-space ID. A migration would add governance cost without a demonstrated correctness requirement.

### Treat same model name or dimension as compatible

Rejected: provider, revision, normalization, pooling, metric, chunking and preprocessing can all change the vector space while preserving the same dimension.

### Automatically rebuild stale/legacy rows

Rejected: state detection remains read-only and rebuild remains explicit and bounded.

## Acceptance evidence

Final accepted PR candidate:

```text
PR #328 head:              96f4aad2ae4a65203cc133dbe2af40ed869c99e8
base:                      86ed963d2d31b9da174c88f0cf05cc27faced2b9
Full CI:                   #1210 · 31882948349 · SUCCESS
Docker:                    #799  · 31882948356 · SUCCESS
CodeQL:                    #48   · 31882948357 · SUCCESS
READY aggregate:           #1315 · 31883253917 · SUCCESS
```

Protected implementation merge and exact-main evidence:

```text
merge/main:                4932727c348ec967564d8babf80e25ca82bce8be
parent:                    86ed963d2d31b9da174c88f0cf05cc27faced2b9
signature:                 VERIFIED / valid
post-merge Full CI:        #1211 · 31883324866 · SUCCESS
post-merge Docker:         #800  · 31883324890 · SUCCESS
post-merge CodeQL:         #49   · 31883324957 · SUCCESS
post-merge aggregate:      #1316 · 31883324900 · SUCCESS
```

Tests cover identity axes, deterministic hashing, same-dimension incompatibility, legacy-row fail-close, existing storage reuse, erasure preservation and pre-score dimension mismatch. Full CI also passed the blocking mypy gate, full pytest, coverage ratchet ≥74%, dependency audit, reproducible wheel, deterministic SBOM and architecture/project-state/KB guards.

No local CLI result or Codex approval is claimed.

## Follow-up boundary

Phase 3A closure does not admit Phase 3B. Live persistent projection retrieval, provider execution, semantic quality benchmarking or runtime activation require a new explicit admission.
