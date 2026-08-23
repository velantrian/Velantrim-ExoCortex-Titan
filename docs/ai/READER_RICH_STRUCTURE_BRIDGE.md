# 📚 Reader Rich Structure Bridge — AI Context

## Status

`PR #380 · DRAFT · NOT IN MAIN · GITHUB_AND_NOTION`

Exact branch base:

`main@a138a622820fabe45ed32273bca0884e6651d9a8`

This record describes only the bounded parser-structure bridge proposed by PR #380. It does not modify or supersede the merged lifecycle of Reader Product PR #374.

## Problem

The merged Reader Product path already runs local documents through `FileIngester`, but `scripts/read_document.py` previously selected Reader structure mode only from the original filename suffix.

Existing PDF parser paths can already emit Markdown:

- Marker returns Markdown text and declares `structured_data["format"] = "markdown"`;
- Docling exports Markdown text and declares the same format.

A `.pdf` therefore could contain a hierarchy-preserving Markdown representation after parsing but still be sent to `DeterministicDocumentStructureParser` as `PLAIN_TEXT`. The existing plain-text mode intentionally creates one top-level document section, so headings already recovered by the parser were not reused by Reader Core.

## Bounded implementation

PR #380 adds `core/reader_parse_bridge.py` and routes the user-facing Reader CLI through it:

```text
FileIngester ParseResult
        ↓
structured_data.format
        ↓
ReaderParseResolution
        ↓
existing DocumentStructureFormat
        ↓
existing DeterministicDocumentStructureParser
```

Resolution rules:

- explicit parser declaration `format=markdown` → existing Reader `MARKDOWN` mode;
- native `.md` / `.markdown` → existing Reader `MARKDOWN` mode;
- missing, malformed, or unsupported parser format → existing `PLAIN_TEXT` fallback.

The bridge never invents headings, pages, tables, figures, offsets, claims, evidence, or relations. It only preserves a representation the existing parser already emitted.

## What this technically changes

For Marker/Docling PDF output that contains Markdown headings, Reader Core can now preserve those headings as deterministic sections before `HierarchicalSectionPlanner` creates bounded reading units.

Markdown table text remains part of the corresponding section text. This PR does **not** yet materialize tables/figures/captions as typed `ContentKind.TABLE/FIGURE/CAPTION` sections.

Exact `RawSource` text and SHA-256 source revision remain unchanged, so existing SectionCard/source-span provenance continues to bind to the actual text passed into Reader.

## Tests

Focused tests cover:

- `.pdf + format=markdown` selects Reader Markdown mode;
- native Markdown behavior remains unchanged;
- unknown/malformed metadata fails back to plain text;
- parser-declared Markdown reaches the existing deterministic hierarchy parser and yields separate chapter sections;
- `scripts/read_document.py` consumes `ParseResult.structured_data`.

Exact-head GitHub CI remains the authoritative execution evidence. No green status should be transferred from PR #374 or another head.

## Authority boundary

Unchanged:

```text
parser structure != evidence
Reader output != truth
GlobalDocumentSynthesis != Canon
```

PR #380 adds no:

- memory or Canon write;
- ESM transition;
- TruthGate or Write Gate call;
- graph authority;
- provider/network permission;
- worker, scheduler, daemon, or background reader;
- Operator GO;
- runtime activation;
- production authorization.

Issue #120 remains the separate Reader production-evidence program.

## Deliberately deferred

Separate bounded follow-up work is required for:

- exact-offset mapping of typed Unstructured elements into `DocumentStructureMap`;
- page/bounding-box provenance;
- typed tables, figures, captions, footnotes, and code blocks;
- DOCX table/figure order when emitted representations do not preserve exact source order;
- EPUB chapter metadata → exact Reader structure map;
- structure-aware retrieval / parent-child context expansion;
- durable cross-process ReadingSession resume;
- PageIndex/RAPTOR/Ψ-RAG experiments.

The next slice must not infer or guess source structure when exact binding to the emitted Reader text is unavailable.
