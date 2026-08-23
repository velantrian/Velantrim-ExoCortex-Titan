# ADR — Reader parser-structure bridge

**Date:** 2026-08-23  
**Status:** DRAFT PR DECISION · NOT MERGED · NO RUNTIME/PRODUCTION AUTHORITY  
**Documentation impact:** `GITHUB_AND_NOTION`

## Context

The merged Reader Product path accepts local PDF/DOCX/EPUB/text files through
`FileIngester`, then passes `ParseResult.extracted_text` into Reader Core.

Some existing parsers already emit Markdown text with explicit
`structured_data["format"] == "markdown"` — notably the PDF Marker and Docling paths.
The product CLI previously selected Reader structure mode only from the original filename
suffix. Therefore a `.pdf` whose parser had already produced structured Markdown was sent
to `DeterministicDocumentStructureParser` as `PLAIN_TEXT`, collapsing the whole extracted
payload to one top-level section before the hierarchy-aware section planner ran.

## Decision

Add one bounded read-side bridge:

```text
FileIngester ParseResult
        ↓
parser-declared output format
        ↓
ReaderParseResolution
        ↓
existing DeterministicDocumentStructureParser
```

Rules:

1. An explicit parser declaration `format=markdown` selects the existing Reader
   `MARKDOWN` mode even when the original file suffix is `.pdf` or `.docx`.
2. Native `.md` / `.markdown` files retain the existing filename-based Markdown path.
3. Unknown, missing, malformed, or unsupported parser format metadata falls back to the
   existing `PLAIN_TEXT` behavior.
4. The bridge does not create headings, offsets, tables, figures, relations, claims, or
   evidence. It only preserves a representation the existing parser already produced.
5. Exact Reader source text and SHA-256 revision semantics remain unchanged.

## Why this slice first

This is the smallest connection that recovers real document hierarchy from existing
Marker/Docling output without introducing a second parser or changing Reader contracts.
It also creates a narrow seam for later exact-offset bridges from typed parser elements,
but those are explicitly outside this PR.

## Alternatives rejected/deferred

### Re-parse every PDF inside Reader

Rejected. Titan already has a file-parser cascade. Duplicating PDF parsing in Reader would
create competing ownership and more dependencies.

### Convert arbitrary structured metadata into guessed headings

Rejected for this slice. Parser metadata that cannot be mapped exactly to the emitted text
must not be promoted into Reader structure by heuristic guesswork.

### Add RAPTOR/PageIndex/GraphRAG now

Deferred. Retrieval projections are not the current bottleneck for this bounded defect.
First preserve structure that Titan already has.

## Authority and safety boundary

Unchanged:

```text
parser structure != evidence
Reader output != truth
GlobalDocumentSynthesis != Canon
retrieval/projection != authority
```

This change adds no:

- memory or Canon write;
- ESM transition;
- TruthGate or Write Gate call;
- graph authority;
- provider selection or network permission;
- worker, scheduler, daemon, or background task;
- Operator GO;
- runtime activation;
- production authorization.

## Verification

Focused tests must prove:

- `.pdf + parser format=markdown` selects Reader Markdown mode;
- native Markdown behavior remains unchanged;
- unknown/malformed metadata fails to plain text;
- parser-declared Markdown reaches the existing deterministic hierarchy parser and
  produces separate chapter sections;
- the user-facing `read_document.py` selector consumes `ParseResult.structured_data`.

Repository CI remains authoritative for the exact PR head.

## Remaining limitations

This PR does **not** yet map:

- Unstructured typed `elements[]` to exact Reader sections;
- PDF page coordinates/bounding boxes;
- DOCX table/figure order when the parser output does not preserve exact text order;
- EPUB chapter metadata into a prebuilt `DocumentStructureMap`;
- structure-aware retrieval or parent/child context expansion;
- durable ReadingSession resume.

Those remain separate bounded follow-up decisions and must preserve exact source binding.
