# 🔗 Reader Exact Structure Product Wiring — AI Context

## Status

`STACKED DRAFT · NOT IN MAIN · READ-SIDE ONLY · NO AUTHORITY EXPANSION`

Parent dependency: PR #381 exact typed-element structure bridge.

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

## Authority boundary

Unchanged: structure is derived navigation metadata, not evidence or truth. This slice
performs no memory/Canon write, ESM transition, TruthGate/Write Gate call, graph mutation,
provider permission change, scheduler/background work, Operator GO, runtime activation, or
production authorization.
