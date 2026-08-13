# ModelFreeCore Phase-1 contract — review/operations note

Tracking: #295  
Parent architecture: #53  
Authoritative baseline: `main@2699963547a42c4fbcd6b0273125c890a038654b`

## Purpose

This note defines the review boundary for the first implementation slice of the
local-first adaptive architecture. It is **not a runtime activation guide**.

The candidate `ModelFreeCore` is a typed read facade over mechanisms already present on
`main`. It makes the no-model baseline explicit without changing the default server
pipeline.

## Expected execution

```text
L2Query
  -> QueryRouter (rules)
  -> lexical-only pipeline retrieval
  -> FactsPack
  -> Guardian
  -> TruthGate
  -> optional local CausalGraph READ
  -> deterministic renderer
  -> L2Result
```

Expected result metadata:

```text
execution_mode = model_free
retrieval_mode = lexical
optional_capabilities_used = []
```

## Forbidden calls in this bounded slice

A `ModelFreeCore.query()` execution must not invoke:

- `DenseRetriever`;
- reciprocal-rank fusion;
- cross-encoder/reranker;
- LLM/model provider;
- remote/network egress;
- ADAO or CapabilityRegistry;
- canonical fact/ESM/relation mutation.

The general Titan runtime may still contain those optional modules elsewhere. Their
existence is not evidence that this facade used them.

## Evidence behavior

The renderer does not synthesize new factual claims. It restates evidence rows that
survived the existing FactsPack, Guardian and TruthGate path.

If lexical retrieval finds nothing, policy excludes the candidates, Guardian rejects the
pack, or TruthGate rejects it, the facade returns:

```text
Недостаточно подтверждённых локальных данных.
```

with a machine-readable reason code.

Known local causal rows may be returned as typed read evidence. A `contradicts` row is
also exposed in the `conflicts` collection. The facade never calls `CausalGraph`
mutation methods.

## Verification checklist

Before review:

- [ ] focused `tests/test_model_free_core.py` green;
- [ ] existing `tests/test_retrieval_routing.py` remains green;
- [ ] Ruff on changed Python files green;
- [ ] no server/runtime/config wiring added;
- [ ] no default retrieval-mode change;
- [ ] no Canon/ESM/relation mutation from query tests;
- [ ] exact candidate SHA recorded;
- [ ] Full CI and applicable Docker checks green;
- [ ] GitHub AI docs reconciled;
- [ ] existing `Velantrim Titan 9.0` Notion page REVIEW sync/read-back complete.

After protected merge, rerun applicable post-merge evidence and write FINAL Notion
evidence before closing #295. Parent #53 remains open for later phases.

## Fixed invariants

Continuity remains `12/12`, schema remains `v7`, runtime enabled remains `false`,
Operator GO remains `false`, runtime authority remains `false`, and production authority
remains `false`.
