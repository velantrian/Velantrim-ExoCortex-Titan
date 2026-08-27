# ADR — Reader exact typed-element structure bridge

**Date:** 2026-08-23  
**Status:** OWNER REVIEW CLEAN · DRAFT PR · NOT MERGED · NO RUNTIME/PRODUCTION AUTHORITY  
**Documentation impact:** `GITHUB_AND_NOTION`

## Lifecycle

The parent Rich Structure Bridge, PR #380, is merged on `main` as
`e2902e3dce893dcf55a29a43bd740c543c0e6d94`.

This PR now carries only the bounded typed-element bridge delta on top of that merged
parent. Fresh bounded owner review is sufficient; current verdict is `P0=0 · P1=0`.
No external reviewer is required. Exact-head CI and aggregate merge evidence remain
mandatory and are not replaced by owner review.

## Context

The merged Rich Structure Bridge preserves parser-declared Markdown so existing
Marker/Docling PDF output can reach the Reader Markdown hierarchy parser.

A separate existing PDF path, Unstructured, already exposes ordered typed elements:

```text
structured_data["elements"] = [
  {"type": type(element).__name__, "text": str(element)},
  ...
]
```

The same adapter constructs `ParseResult.extracted_text` as:

```text
"\n\n".join(str(element) for element in elements)
```

That gives Titan a stronger property than fuzzy text matching: the typed element list can
be reconstructed and compared exactly with the immutable Reader source text.

## Decision

Add a bounded `build_exact_element_structure()` bridge that emits a typed
`DocumentStructureMap` **only when** the ordered parser elements reconstruct
`RawSource.text` exactly.

No substring search, fuzzy alignment, OCR-coordinate inference, generated headings, or
approximate page mapping is permitted.

### Supported conservative element mapping

- `Title` → `HEADING`
- `Header` → `TEXT` (Unstructured `Header` may be a running/page header and is not promoted into Reader hierarchy)
- `Table` → `TABLE`
- `Image` / `Picture` / `Figure` → `FIGURE`
- `FigureCaption` / `ImageCaption` / `Caption` → `CAPTION`
- `Footnote` → `FOOTNOTE`
- `Code` / `CodeBlock` → `CODE`
- `Appendix` → `APPENDIX`
- common narrative/list/address/formula text → `TEXT`
- unknown parser types → `UNKNOWN` plus an explicit parser warning

Known parser labels are mapped only to semantics the upstream label actually supports.
Unknown values are not promoted to a guessed known type, and document/page headers are not
promoted to semantic section headings.

## Exact offset rule

Because the current Unstructured adapter joins elements with exactly two newline
characters, each non-final element owns the following `\n\n` separator. Sections therefore
form one contiguous non-overlapping partition from offset `0` through EOF.

If reconstruction differs from the immutable source by even one character, the bridge
returns no structure map and reports `typed_elements_source_mismatch`.

## Bounded remediation

Owner review previously identified one semantic over-classification risk: Unstructured
`Header` can mean a running/page header and therefore must not be promoted into Reader
hierarchy. The bridge now preserves `Header` as `TEXT` with `level=0`, while `Title`
remains `HEADING`. A focused regression test locks this behavior.

## Why this remains a separate slice

This PR proves only the parser-metadata → exact typed `DocumentStructureMap` contract.
It deliberately does **not** modify `ReaderProductPipeline`. Product wiring remains the
separate bounded follow-up PR #390.

## Deliberately not claimed

This slice does not provide:

- page numbers or bounding boxes;
- table cell semantics;
- figure binary/image identity;
- parent/child hierarchy between typed elements;
- DOCX/EPUB typed-element product activation;
- structure-aware retrieval;
- PageIndex/RAPTOR/GraphRAG;
- durable ReaderSession resume.

Page/bbox metadata must be added only when its source identity and coordinate semantics are
explicitly preserved by the upstream parser contract.

## Authority boundary

Unchanged:

```text
parser element type != evidence
parser structure != truth
Reader artifact != Canon
coverage != correctness
```

The bridge performs no memory/Canon write, ESM transition, TruthGate/Write Gate call,
network/provider call, graph mutation, tool execution, background work, Operator GO,
runtime activation, or production authorization.

## Verification

Focused tests must prove:

- known Unstructured element types map to the intended `ContentKind`;
- `Title` remains a semantic heading while `Header` is preserved without heading promotion;
- emitted sections exactly partition the immutable Reader text;
- source mismatch fails closed with no fuzzy recovery;
- malformed/missing elements create no map;
- unknown future parser types remain `UNKNOWN` with an explicit warning.

Repository CI remains authoritative for the exact PR head. No CI result from PR #380 or an
ancestor SHA is transferred to this slice.
