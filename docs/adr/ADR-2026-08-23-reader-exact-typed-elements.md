# ADR — Reader exact typed-element structure bridge

**Date:** 2026-08-23  
**Status:** DRAFT STACKED PR DECISION · NOT MERGED · NO RUNTIME/PRODUCTION AUTHORITY  
**Documentation impact:** `GITHUB_AND_NOTION`

## Context

The first Rich Structure Bridge preserves parser-declared Markdown so existing
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

- `Title` / `Header` → `HEADING`
- `Table` → `TABLE`
- `Image` / `Picture` / `Figure` → `FIGURE`
- `FigureCaption` / `ImageCaption` / `Caption` → `CAPTION`
- `Footnote` → `FOOTNOTE`
- `Code` / `CodeBlock` → `CODE`
- `Appendix` → `APPENDIX`
- common narrative/list/address/formula text → `TEXT`
- unknown parser types → `UNKNOWN` plus an explicit parser warning

Unknown values are not promoted to a guessed known type.

## Exact offset rule

Because the current Unstructured adapter joins elements with exactly two newline
characters, each non-final element owns the following `\n\n` separator. Sections therefore
form one contiguous non-overlapping partition from offset `0` through EOF.

If reconstruction differs from the immutable source by even one character, the bridge
returns no structure map and reports `typed_elements_source_mismatch`.

## Why this is a separate stacked slice

This PR proves only the parser-metadata → exact typed `DocumentStructureMap` contract.
It deliberately does **not** modify `ReaderProductPipeline` yet. Product wiring should be a
small follow-up after independent review of exact source binding and content-kind mapping.

This avoids combining:

1. provenance/alignment correctness;
2. Reader orchestration behavior;
3. coverage/reread semantics

in one difficult-to-review change.

## Deliberately not claimed

This slice does not provide:

- page numbers or bounding boxes;
- table cell semantics;
- figure binary/image identity;
- parent/child hierarchy between typed elements;
- DOCX/EPUB typed-element support;
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
- emitted sections exactly partition the immutable Reader text;
- source mismatch fails closed with no fuzzy recovery;
- malformed/missing elements create no map;
- unknown future parser types remain `UNKNOWN` with an explicit warning.

Repository CI remains authoritative for the exact PR head.
