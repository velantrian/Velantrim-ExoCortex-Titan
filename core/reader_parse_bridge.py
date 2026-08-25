"""Bounded bridge from file-parser structure metadata into Reader Core.

The bridge does not parse documents, call models, write memory/Canon, or create a
second structure authority. It only decides whether the text already produced by
``FileIngester`` may be interpreted by the existing deterministic Reader structure
parser as Markdown.

Parser-declared structure is advisory. Unknown or malformed metadata falls back to
the existing plain-text Reader path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.document_structure import DocumentStructureFormat


@dataclass(frozen=True, slots=True)
class ReaderParseResolution:
    """Read-side structure decision for one already-extracted text payload."""

    document_format: DocumentStructureFormat
    reason_code: str
    parser_declared_format: str | None = None


_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})


def resolve_reader_document_format(
    *,
    path_suffix: str,
    structured_data: Mapping[str, Any] | None,
) -> ReaderParseResolution:
    """Resolve the existing Reader parser mode without inventing structure.

    A file parser may emit Markdown even when the original filename is ``.pdf`` or
    ``.docx``. Marker and Docling already do this in Titan. When that explicit
    parser declaration is present, the Reader should preserve the headings and
    other Markdown structure instead of flattening the text solely because of the
    original file extension.

    Any unknown/malformed declaration fails safely to the legacy filename rule and
    ultimately to ``PLAIN_TEXT``.
    """

    suffix = path_suffix.strip().lower() if isinstance(path_suffix, str) else ""
    declared: str | None = None
    if isinstance(structured_data, Mapping):
        raw_declared = structured_data.get("format")
        if isinstance(raw_declared, str) and raw_declared.strip():
            declared = raw_declared.strip().lower()

    if declared == "markdown":
        return ReaderParseResolution(
            document_format=DocumentStructureFormat.MARKDOWN,
            reason_code="parser_declared_markdown",
            parser_declared_format=declared,
        )

    if suffix in _MARKDOWN_SUFFIXES:
        return ReaderParseResolution(
            document_format=DocumentStructureFormat.MARKDOWN,
            reason_code="markdown_filename_suffix",
            parser_declared_format=declared,
        )

    return ReaderParseResolution(
        document_format=DocumentStructureFormat.PLAIN_TEXT,
        reason_code="plain_text_fallback",
        parser_declared_format=declared,
    )


__all__ = [
    "ReaderParseResolution",
    "resolve_reader_document_format",
]
