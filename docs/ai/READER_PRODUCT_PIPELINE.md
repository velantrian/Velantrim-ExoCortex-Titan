# 📚 Reader Product Pipeline — AI Context

## Status

`PR #374 DRAFT CANDIDATE · NOT IN MAIN · GITHUB_AND_NOTION`

Exact base at branch creation:

`aab1fbca55e35577fd09cc88fa8872be901fd25f`

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
→ at most one explicit bounded reread round
→ ReadingSession
→ DeterministicSectionRelationBuilder (no inferred relations in v1)
→ GlobalDocumentSynthesis candidate
```

## Failure semantics

The initial pass may leave units without accepted cards. Existing CoverageMap + SelectiveReReadPlanner then produces bounded reread tasks.

PR #374 executes at most one reread round. If any unit remains unresolved:

- valid cards and coverage remain observable;
- `ReadingSession` becomes `DEGRADED`;
- `GlobalDocumentSynthesis` is not created;
- remaining reread work stays explicit;
- no fake complete-reading claim is emitted.

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

## Current deliberate limitations

- ReadingSession durability/cross-process resume remains unwired.
- Product v1 does not infer cross-section relations automatically.
- The digest is a bounded deterministic rollup of source-grounded SectionCard essences, not unconstrained model prose.
- Issue #120 remains external-evidence blocked and is not closed by this PR.

## Review checklist

Before this candidate may leave Draft:

1. exact-head Ruff / blocking mypy / focused tests / full pytest as applicable are green;
2. no hidden memory/Canon/write path is reachable from the new pipeline/CLI;
3. incomplete reading cannot create global synthesis;
4. reread work is bounded and foreground-only;
5. GitHub docs and existing `Velantrim Titan 9.0` Notion page are synchronized/read back;
6. current PR head/base are revalidated.
