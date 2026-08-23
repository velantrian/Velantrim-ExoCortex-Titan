# 📐 Reader Typed Elements Bridge — AI Context

## Status

`STACKED DRAFT · NOT IN MAIN · NO PRODUCT WIRING YET · GITHUB_AND_NOTION`

Parent implementation dependency:

`PR #380 head@9d971c928d80398d8d56ea973073208ec2a70abc`

This slice starts from the exact head of the Rich Structure Bridge so it can be reviewed
without changing PR #380.

## What this slice adds

`core/reader_structured_elements_bridge.py` converts existing parser-owned ordered
`elements[]` metadata into a typed Reader `DocumentStructureMap`, but only after proving
that the element texts reconstruct the immutable `RawSource.text` exactly with the same
`\n\n` separator used by Titan's current Unstructured PDF adapter.

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

The map builder exists and is tested, but this stacked slice **does not yet feed the map
into `ReaderProductPipeline`**. That wiring is intentionally deferred to the next bounded
slice after review of exact alignment semantics.

Therefore do not describe typed tables/figures as active ordinary-user Reader behavior yet.
The active product behavior remains the parent PR #380 Markdown-preservation path when that
PR is eventually accepted/merged.

## Mapping policy

Known parser element classes map conservatively to existing Reader `ContentKind` values.
Unknown parser classes remain `UNKNOWN` with an explicit warning. There is no semantic
classifier, model call, fuzzy match, or type guessing.

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
- DOCX/EPUB typed bridges;
- structure-aware retrieval;
- PageIndex/RAPTOR/GraphRAG;
- session persistence.

## Authority

`parser structure != evidence · Reader output != truth · synthesis != Canon`.

No memory/Canon write, TruthGate/Write Gate, ESM transition, graph authority, provider
permission, background worker, Operator GO, runtime activation, or production authorization
is added.
