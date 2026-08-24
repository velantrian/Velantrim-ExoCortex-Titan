# 📐 Reader Typed Elements Bridge — AI Context

## Status

`OWNER REVIEW CLEAN · DRAFT PR · NOT IN MAIN · NO PRODUCT WIRING YET · GITHUB_AND_NOTION SYNCED`

Parent implementation dependency PR #380 is merged on `main` as
`e2902e3dce893dcf55a29a43bd740c543c0e6d94`.

This slice is now based directly on merged `main` and carries only the exact typed-element
bridge delta. Fresh bounded owner review is sufficient; current verdict is `P0=0 · P1=0`.
No external reviewer is required. Exact-head CI and aggregate merge evidence remain
mandatory.

## What this slice adds

`core/reader_structured_elements_bridge.py` converts existing parser-owned ordered
`elements[]` metadata into a typed Reader `DocumentStructureMap`, but only after proving
that the element texts reconstruct the immutable `RawSource.text` exactly with the same
`\n\n` separator used by Titan's current Unstructured adapter.

```text
Unstructured elements[]
        ↓
exact reconstruction == RawSource.text ?
        ├─ no  → no typed map / fail closed
        └─ yes
             ↓
exact offsets + conservative ContentKind mapping
             ↓
DocumentStructureMap candidate
```

## Important current limitation

The map builder exists and is tested, but this slice **does not yet feed the map into
`ReaderProductPipeline`**. That wiring remains the separate bounded follow-up PR #390.

Therefore do not describe typed tables/figures as active ordinary-user Reader behavior yet.
The active merged product behavior at this layer is only PR #380 Markdown preservation.

## Mapping policy

Known parser element classes map conservatively to existing Reader `ContentKind` values.
`Title` maps to `HEADING`, while Unstructured `Header` is preserved as `TEXT` at level 0
because it can represent a running/page header and does not itself prove semantic hierarchy.
Unknown parser classes remain `UNKNOWN` with an explicit warning. There is no semantic
classifier, model call, fuzzy match, or type guessing.

The prior owner-review finding about `Header` over-classification is closed by this
conservative mapping and a focused regression test.

## Provenance rule

Every emitted section is a contiguous slice of the exact immutable source revision.
Non-final elements own the exact `\n\n` separator used by the upstream adapter so the
sections form a complete non-overlapping partition through EOF.

Any source mismatch returns `typed_elements_source_mismatch` and emits no map.

## Not included

- product pipeline wiring;
- page/bbox semantics;
- table cells or figure payload identity;
- parent-child element hierarchy;
- DOCX/EPUB typed-element product activation;
- structure-aware retrieval;
- PageIndex/RAPTOR/GraphRAG;
- session persistence.

## Authority

`parser structure != evidence · Reader output != truth · synthesis != Canon`.

No memory/Canon write, TruthGate/Write Gate, ESM transition, graph authority, provider
permission, background worker, Operator GO, runtime activation, or production authorization
is added.

## Verification rule

Only exact-head CI for the current PR head counts. Parent/ancestor workflow results are
historical evidence and are not transferred.
