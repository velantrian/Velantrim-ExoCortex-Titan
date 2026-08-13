# ModelFreeCore Phase-1 contract — operations and audit note

Tracking: #295  
Parent architecture: #53  
Protected implementation: PR #296 · `main@e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96`

## Purpose

This note defines the review boundary for the first implementation slice of the
local-first adaptive architecture. It is **not a runtime activation guide**.

`ModelFreeCore` is a typed read facade over mechanisms already present on `main`. It
makes the no-model baseline explicit without changing the default server pipeline. A
post-merge audit hardening candidate closes logical gaps not detected by #296 CI.

## Expected execution

```text
L2Query
  -> QueryRouter (rules)
  -> lexical-only pipeline retrieval (cognitive rerank explicitly disabled)
  -> FactsPack
  -> Guardian
  -> TruthGate
  -> optional already-open local CausalGraph READ (no initializer/DDL)
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
mutation methods or the DDL-capable graph initializer. An absent optional graph is
non-blocking; an already-present graph that raises during a read produces bounded
insufficient evidence.

`VERIFIED` facts and `UNVERIFIED` attributed reports use separate renderer headings.
Passing Guardian/TruthGate establishes policy eligibility for the response; it does not
upgrade a user report into a verified world fact.

## Verification checklist

Before review:

- [x] focused `tests/test_model_free_core.py` green locally;
- [x] relevant pipeline tests green locally;
- [x] Ruff and focused mypy on changed Python files green locally;
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
