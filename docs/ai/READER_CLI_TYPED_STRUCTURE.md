# 📚 Reader CLI Typed Structure Auto-Selection — AI Context

## Status

`STACKED DRAFT · NOT IN MAIN · READ-SIDE ONLY · NO AUTHORITY EXPANSION`

Parent dependency: PR #390 exact structure product wiring.

## Purpose

This final bounded connection makes the ordinary local Reader CLI attempt to reuse exact typed parser elements automatically before falling back to the existing Markdown/plain-text structure path.

```text
FileIngester ParseResult
        ↓
RawSource(extracted_text)
        ↓
exact elements reconstruction?
   ├─ yes → typed DocumentStructureMap → existing product wiring
   └─ no  → existing parser-declared Markdown / suffix / plain-text path
```

## Safety behavior

The CLI does not search for approximate text, infer coordinates, or repair malformed parser metadata. `build_exact_element_structure()` remains the only typed-map admission point. A mismatch simply means the typed projection is unavailable; the Reader uses its previous deterministic structure route and emits a boundary warning for non-trivial typed-element failures.

If an exact map is produced, the product-wiring layer independently revalidates document ID, source revision, SHA-256 content hash, and the complete contiguous source partition before Reader execution.

## What becomes active

For the existing Unstructured parser contract where `elements[]` exactly reconstruct `extracted_text`, the ordinary local Reader path can now preserve existing Reader `ContentKind` values such as `TABLE`, `FIGURE`, `CAPTION`, `FOOTNOTE`, and `CODE`. The existing hierarchical planner already treats those atomic kinds as indivisible reading sections.

Parser-declared Markdown from Marker/Docling remains supported through the earlier Rich Structure Bridge. Native Markdown and plain-text fallback remain unchanged.

## Deliberately not included

- no page/bbox semantics;
- no table cell model;
- no binary figure identity;
- no OCR authority;
- no structure-aware retrieval or parent-child retrieval;
- no PageIndex/RAPTOR/GraphRAG;
- no durable ReaderSession resume;
- no memory/Canon write or production authorization.

## Boundary

`parser structure != evidence · retrieval projection != truth · Reader output != Canon`.
