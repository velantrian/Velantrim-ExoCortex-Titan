# Query Read-Side Purity — Block A Evidence

**Date:** 2026-08-15  
**Issue:** #330  
**PR:** #331  
**Base:** `main@185d91be70e63eafde819c3bb0c5d15a5f974caa`  
**Documentation impact:** `GITHUB_ONLY`

## Problem

The legacy/default query path could request causal evidence through the initializing
`_get_causal_graph()` helper. On a valid store with no causal schema yet, that helper may
open SQLite, execute `_RELATIONS_DDL`, commit, and install the process singleton. A logical
query could therefore mutate persistent SQLite schema even though the query path does not
own Canon fact/ESM or causal-relation mutation.

The live caller audit found three query-facing initialization sites in `core/pipeline.py`:

1. contradiction extraction in `run()`;
2. `_expand_with_graph_neighbors()`;
3. `_essence_relations_for()` when no graph is supplied.

The server lifecycle already has an explicit migration owner. Query execution does not need
to act as a hidden fallback migrator.

## Bounded fix

Reuse the existing non-initializing `_peek_causal_graph()` boundary already used by
`ModelFreeCore`:

```text
explicit lifecycle / setup / reset / mutation
  -> _get_causal_graph() may initialize

query-side causal evidence
  -> _peek_causal_graph()
  -> already-open graph when available
  -> otherwise bounded no-graph fallback
```

No graph manager, schema, authority owner, runtime flag, Canon path or Phase 3B capability
is added.

## Regression contract

`tests/test_pipeline.py` now proves that a default query on an isolated seeded database with
no open causal singleton:

- returns a normal bounded answer;
- leaves the non-internal `sqlite_master` snapshot byte-for-byte equivalent at the SQL-row
  level (`schema_after == schema_before`);
- does not create `relations`, `relation_paths`, `idx_relations_from`, or
  `idx_relations_to`;
- leaves `(fact_id, epistemic_state)` unchanged;
- leaves the causal singleton detached.

The graph-expansion no-graph regression also makes `_get_causal_graph()` raise if called,
proving the read helper cannot silently fall back to initialization. Existing positive
graph tests explicitly initialize graph state before reading it. The Essence causal-chain
test injects the read-only peek hook.

## Exact implementation evidence

Production commit:

`393225fc4a0b7c977098e3555c8c61035ff2314c`

The production diff is limited to the three query-side causal-read sites in
`core/pipeline.py`.

Test commits:

- `b750ac1d0b291f81142c6e9b1c033e274392df8c` — schema/ESM/no-init regressions and graph
  fixture cleanup;
- `ead6bde638f1399ab7293091f4d0f1e4847486cd` — Essence test uses the read-only hook.

At preliminary exact head `ead6bde638f1399ab7293091f4d0f1e4847486cd`:

- CodeQL #61 — **SUCCESS**;
- Docker #807 — **SUCCESS**;
- CI #1223 — **IN PROGRESS** at the time this checkpoint was authored;
- architecture freeze guard — **SUCCESS**;
- machine-readable project-state guard — **SUCCESS**;
- Ruff — **SUCCESS**;
- blocking mypy — **SUCCESS**;
- full pytest / coverage — pending at this checkpoint.

This evidence is preliminary because adding this documentation file creates a new PR head.
Final merge eligibility must be established only from the final exact head after all
applicable workflows and the aggregate merge-evidence gate complete.

## Diff hygiene note

The connector-only file replacement used for the test update introduced one formatting-only
extra space in an unrelated pre-existing dictionary literal in `tests/test_pipeline.py`.
It is semantically inert and Ruff accepts it. Removing that single space through the
available GitHub contents API would require another complete replacement of the large test
file, increasing mutation surface for no behavioral gain. It is therefore explicitly
recorded rather than hidden or represented as a functional change.

## Authority / non-goals

Unchanged:

- Canon ownership;
- ESM ownership;
- causal-relation mutation ownership;
- TruthGate and PolicyKernel;
- embedding Phase 3A posture;
- CSM posture;
- schema v7 semantics;
- runtime enabled = `false`;
- Operator GO = `false`;
- runtime authority = `false`;
- production authority = `false`;
- Phase 3B = `NOT ADMITTED / NOT STARTED`.

Direct GraphLab lifecycle/signature repair, IndexCoordinator repair, storage observability,
multilingual lifecycle hygiene, broad truth-surface cleanup, Notion history cleanup and
Issue #249 characterization remain separate bounded workstreams.

## Completion rule

This file is **not** closure evidence by itself. Block A is complete only after:

1. final exact-head CI / Docker / CodeQL and required aggregate evidence;
2. review-thread / mergeability reconciliation;
3. protected merge;
4. post-merge exact-main acceptance;
5. Issue #330 closure/read-back.
