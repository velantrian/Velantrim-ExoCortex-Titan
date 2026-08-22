# 📚 Reader Product Pipeline — AI Context

## Status

`PR #374 READY FOR REVIEW · NOT IN MAIN · GITHUB_AND_NOTION`

Exact base at branch creation:

`aab1fbca55e35577fd09cc88fa8872be901fd25f`

`main` may move independently while the PR is open. The authoritative current PR head, current `main`, mergeability, and exact-head CI evidence live in PR metadata / the synchronized Notion record rather than being self-referentially hard-coded into this in-branch file.

This document describes the candidate in PR #374. It is **not** evidence that `main` contains or enables the capability until protected merge and post-merge verification occur.

## Problem

Titan already had mature Reader Core primitives, and Titan V1 already had a user-facing file ingestion helper, but the two were not one safe product path.

The existing `scripts/ingest_file.py` intentionally sends extracted file text through `/ingest/text`, which is the governed memory/write path. Long-document reading should not require memory admission first.

## Candidate solution

PR #374 adds:

- `core/reader_product_pipeline.py` — explicit foreground orchestration over existing Reader Core components;
- `scripts/read_document.py` — ordinary-user file → Reader Core CLI;
- `tests/test_reader_product_pipeline.py` — bounded orchestration/fail-closed tests;
- `docs/READER_DOCUMENT_PATH.ru.md` — user-facing guide;
- `docs/adr/ADR-2026-08-22-reader-product-pipeline.md` — durable design decision.

## Data flow

```text
FileIngester
→ RawSource
→ DeterministicDocumentStructureParser
→ HierarchicalSectionPlanner
→ SemanticReader
→ SectionCardBuilder
→ DeterministicCriticalExceptionScanner
→ CoverageMapBuilder
→ SelectiveReReadPlanner
→ at most one explicit bounded reread round for tasks with planner-assigned ReaderMode
→ ReadingSession
→ DeterministicSectionRelationBuilder (no inferred relations in v1)
→ GlobalDocumentSynthesis candidate
```

A queued reread task is not automatically an LLM call. Only tasks carrying an explicit `ReaderMode` from the existing planner are executed through `SemanticReader`. Tasks with `reader_mode=None` represent non-reader follow-up actions and remain explicit open work; the product bridge must not coerce them into `DEEP` or any other hidden provider call.

## Failure and product-status semantics

The initial pass may leave units without accepted cards. Existing CoverageMap + SelectiveReReadPlanner then produces bounded reread tasks.

PR #374 executes at most one reader-capable reread round. If any reading unit remains unresolved:

- valid cards and coverage remain observable;
- `ReadingSession` becomes `DEGRADED`;
- `GlobalDocumentSynthesis` is not created;
- remaining reread work stays explicit;
- no fake complete-reading claim is emitted.

The user-facing CLI distinguishes:

- `COMPLETE` — all reading units processed and no remaining/deferred reread work;
- `COMPLETE_WITH_OPEN_WORK` — all reading units processed and synthesis may exist, but explicit non-reader/advisory follow-up remains;
- `DEGRADED` — one or more reading units remain unprocessed after the bounded attempt.

This product distinction does not redefine the underlying RDR-07 `ReadingSession.COMPLETED` state; it prevents that state from being presented to an ordinary user as proof that every exception, relation or follow-up question has been resolved.

## Synthesis provenance

The digest is a bounded deterministic rollup of accepted `SectionCard.local_essence` values, not unconstrained model prose.

The product bridge builds digest text and its supporting claim correspondence together. A source claim may be listed in `synthesis.supporting_claim_ids` only when the complete exact claim text is present in the actually retained fragment of that claim's own SectionCard essence. Claims omitted by an upstream essence budget or cut by `max_digest_chars` remain unrepresented and are left to the existing `GlobalDocumentSynthesisBuilder` as `unsupported_source_claim_ids`.

This is fail-closed provenance: truncation may reduce declared support, but it must never create support that the visible bounded digest does not contain.

## Authority boundary

The candidate does not:

- call `/ingest/text`;
- call `store_fact()`;
- call TruthGate or Write Gate;
- transition ESM;
- write memory or Canon;
- write Crystal;
- add graph authority;
- add a worker, queue, scheduler or background reader;
- add a provider/network bypass;
- authorize canary, live runtime or production.

`Reader output != truth` and `GlobalDocumentSynthesis != Canon` remain invariant.

## Resource-accounting boundary

`ReadingSessionUsage` on this product bridge is intentionally partial/card-centric observability, not complete provider cost accounting.

- `processed_units` describes recorded cards/units, not provider-call count;
- `source_chars` describes the source spans represented by recorded cards and does not claim cumulative reread transport volume;
- `model_tokens` may remain unavailable/default when the existing `SemanticReader` contract does not expose provider usage to this bridge.

The bridge must not invent token/cost precision that its existing contracts do not provide. `reader_attempts` and `reread_attempts` remain the explicit execution-count signals exposed by this product layer.

## Current deliberate limitations

- ReadingSession durability/cross-process resume remains unwired.
- Product v1 does not infer cross-section relations automatically.
- One explicit invocation does not attempt to resolve non-reader follow-up actions.
- JSON open-work detail is sufficient to expose status/counts but richer downstream UI metadata remains a non-blocking follow-up.
- Issue #120 remains external-evidence blocked and is not closed by this PR.

## Review / merge checklist

Before merge of this ready-for-review candidate:

1. exact-head Ruff / blocking mypy / focused tests / full pytest as applicable are green;
2. no hidden memory/Canon/write path is reachable from the new pipeline/CLI;
3. incomplete reading cannot create global synthesis;
4. digest truncation cannot overclaim `supporting_claim_ids`;
5. reread work is bounded and foreground-only, and `reader_mode=None` never becomes a hidden Reader call;
6. user-facing status exposes remaining/deferred work instead of presenting it as fully resolved;
7. GitHub docs and existing `Velantrim Titan 9.0` Notion page are synchronized/read back;
8. current PR head/base are revalidated;
9. merge still requires the appropriate owner decision and does not authorize production/runtime or close Issue #120.
