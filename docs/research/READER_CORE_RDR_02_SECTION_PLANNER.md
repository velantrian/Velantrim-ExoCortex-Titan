# PR-RDR-02 — Hierarchical Section Planner

**Status:** `IMPLEMENTED_IN_BRANCH / SHADOW_FOUNDATION / NO_RUNTIME_WIRING`  
**Depends on:** PR-RDR-00 contracts and PR-RDR-01 `DocumentStructureMap`  
**Authority:** `DERIVED / REBUILDABLE / NO_CANON_OR_MEMORY_AUTHORITY`

## Purpose

PR-RDR-02 converts one exact `DocumentStructureMap` into bounded `ReadingUnit` values suitable for later `SemanticReader` execution. It preserves absolute source offsets and hierarchy while making every continuation and forced boundary visible.

This planner is not the existing LLM adapter chunker. The adapter chunker is provider-execution infrastructure with fixed overlap. PR-RDR-02 is a provider-neutral document-reading plan with hierarchy, receipts, exact source spans, and no overlap in its first version.

## Planning flow

```text
RawSource + DocumentStructureMap
        ↓ validate document, revision, and content hash
iterate source-linked sections in map order
        ↓
section fits budget? ── yes → one ReadingUnit
        │
        no
        ↓
find preferred boundary
paragraph → sentence → line → hard limit
        ↓
ReadingUnits + ContinuationReceipts
        ↓
validate complete overlap-free source partition
```

## Budget

`SectionPlanningBudget` defines:

- `max_unit_chars` — normal maximum unit size;
- `min_unit_chars` — earliest acceptable natural split position;
- `boundary_search_chars` — how far backward from the hard limit natural boundaries are considered.

All measurements use Python Unicode code-point offsets, matching `RawSource`, `DocumentSection`, and `SourceSpan`.

The planner does not estimate tokens. Token budgets are provider-specific execution concerns and may be layered later without replacing exact source coordinates.

## Boundary preference

When a section exceeds the normal maximum, the planner searches the allowed tail window in this order:

1. paragraph boundary;
2. sentence boundary;
3. line boundary;
4. exact hard character limit.

The last available boundary of the highest-priority kind is selected. No content is discarded and no separator gap is created.

A hard-limit split emits:

- `UnitBoundaryKind.HARD_LIMIT`;
- `forced_hard_limit_split` warning;
- `ContinuationReceipt.forced_split == true`.

## Full-partition invariant

The complete plan covers the source exactly once:

```text
first.start_offset == 0
last.end_offset == len(source.text)
previous.end_offset == current.start_offset
```

PR-RDR-02 deliberately uses zero overlap. Overlap changes semantic accounting, duplication, token use, and claim deduplication; it requires a separately versioned and measured policy rather than a hidden default.

## ReadingUnit

Each unit carries:

- deterministic `unit_id`;
- document and source revision;
- structure map and section identity;
- parent section identity;
- global and within-section order;
- exact `SourceSpan` with content hash;
- boundary kind;
- previous and next unit links;
- within-section continuation links;
- explicit warnings.

Unit identity includes planner version, structure-map identity, budget values, section identity, exact offsets, and boundary kind. Unchanged inputs and budgets therefore produce unchanged identities.

## ContinuationReceipt

Every split inside one section produces a deterministic receipt containing:

- source and section identity;
- preceding and following unit IDs;
- exact split offset;
- boundary kind;
- whether the split was forced.

Receipts are execution and provenance metadata. They are not truth, memory, or Canon state.

## Atomic content

The initial atomic kinds are:

- table;
- figure;
- caption;
- footnote;
- code.

These sections are never silently cut. When an atomic section exceeds the normal budget, the planner emits one oversized unit with:

- `UnitBoundaryKind.ATOMIC_OVERSIZE`;
- `atomic_section_exceeds_budget` warning.

This makes the unsupported resource condition visible to later CoverageMap and selective-reread logic. It does not pretend the budget was satisfied.

Current PR-RDR-01 Markdown parsing emits textual sections only. Atomic behavior is implemented now so richer structure parsers can use it without changing planner semantics.

## Input validation

Planning fails closed when:

- document identity differs;
- source revision differs;
- exact source hash differs;
- structure sections do not cover the complete source;
- sections overlap or leave gaps;
- budget values are invalid.

A changed document cannot reuse a stale structure plan merely because the caller supplied the same document name.

## Safety boundary

The planner:

- uses deterministic standard-library logic only;
- performs no model or network call;
- executes no tools;
- persists nothing;
- is not wired into `/query`;
- cannot write Canon or memory;
- cannot call or bypass TruthGate or Write Gate;
- treats source content as untrusted data.

## Executable checks

`tests/test_hierarchical_section_planner.py` verifies:

- full overlap-free source partitioning;
- natural paragraph preference;
- hard-limit fallback and forced receipts;
- hierarchy and continuation preservation;
- exact source-span verification;
- deterministic plan, unit, and receipt identities;
- atomic oversize preservation;
- rejection of stale source/map combinations;
- budget validation.

## Deferred

PR-RDR-02 intentionally does not implement:

- model execution over units;
- parallel scheduling or queues;
- token estimation;
- overlap policies;
- table-cell or code-AST subdivision;
- SectionCards — PR-RDR-03;
- exception and coverage computation — PR-RDR-04;
- selective rereading — PR-RDR-05;
- semantic relations — PR-RDR-06;
- durable session scheduling and leases — PR-RDR-07;
- global synthesis — PR-RDR-08;
- promotion thresholds — PR-RDR-09.
