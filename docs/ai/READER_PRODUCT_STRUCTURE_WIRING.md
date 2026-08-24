# 🔗 Reader Exact Structure Product Wiring — AI Context

## Status

`OWNER REVIEW CLEAN · READY-FOR-REVIEW · NOT IN MAIN · READ-SIDE ONLY · NO AUTHORITY EXPANSION`

Parent dependency PR #381 is merged on `main` as
`6cfe3a9252652fd6439f0ffcd499857e4b549a48`.

This slice is based directly on merged `main` and carries only the bounded product-wiring delta. Fresh bounded owner review is sufficient; current verdict is `P0=0 · P1=0`. No external reviewer is required. Exact-head CI and aggregate merge evidence remain mandatory.

## Purpose

This bounded slice connects an already-proven exact `DocumentStructureMap` to the existing
`ReaderProductPipeline` without changing the ordinary pipeline API or parser behavior.

The wiring is deliberately an adapter:

```text
optional exact DocumentStructureMap
        │
        ├─ absent → existing Markdown / plain-text structure path
        │
        └─ present
             ↓
       exact identity/hash/partition validation
             ↓
       existing HierarchicalSectionPlanner
             ↓
       existing Reader product flow
```

## Fail-closed binding

A prebuilt map is rejected before Reader execution unless all of these match the immutable
`RawSource`:

- `document_id`;
- `source_revision`;
- SHA-256 `content_hash`;
- first section starts at offset `0`;
- final section ends at EOF;
- every adjacent section boundary is exactly contiguous.

No fuzzy alignment or fallback from a *supplied but invalid* map is permitted. Fallback is
only for `structure_map=None`.

## Why a separate adapter

`ReaderProductPipeline` remains unchanged. The adapter substitutes only its existing
parser-compatible seam on a fresh pipeline instance. This keeps ordinary Reader behavior
stable and makes the new path independently removable/reviewable.

## CI remediations

The first main-target run exposed a mypy assignment mismatch because the existing pipeline
field is concretely typed as `DeterministicDocumentStructureParser`. The exact-map adapter
now inherits that existing parser class while fully overriding `parse()`; the same exact
source/map validation still runs before the map is returned.

The next exact-head run exposed a test-fixture defect rather than a product failure: the
negative revision test tried to construct a `DocumentStructureMap` whose map revision and
section revisions disagreed, so the immutable Reader Core contract correctly rejected the
fixture before product wiring was reached. The test now changes the map and all section
revisions together, producing an internally valid map that is nevertheless bound to the
wrong source revision. Product wiring must then reject it with
`ReaderProductStructureWiringError` as intended.

Neither remediation changes the public pipeline API, fallback semantics, exact binding
rules, or authority boundaries.

## Owner review result

The current bounded delta has been reviewed at owner level with `P0=0` and `P1=0`.
The previously remediated parent semantics are inherited from merged main: `Title` remains
the semantic heading signal while Unstructured `Header` stays non-hierarchical `TEXT`.
No external review object is required for this chain.

## Authority boundary

Unchanged: structure is derived navigation metadata, not evidence or truth. This slice
performs no memory/Canon write, ESM transition, TruthGate/Write Gate call, graph mutation,
provider permission change, scheduler/background work, Operator GO, runtime activation, or
production authorization.

## Verification rule

Only exact-head CI for the current PR head counts. Parent/ancestor workflow results are
historical evidence and are not transferred.
