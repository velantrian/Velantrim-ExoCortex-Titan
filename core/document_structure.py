"""Deterministic source-to-structure parsing for Reader Core PR-RDR-01.

The parser consumes immutable ``RawSource`` text directly so every emitted
section offset remains anchored to the original source revision. It performs no
model calls, network access, persistence, memory admission, or runtime wiring.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import re

from core.reader_core_contracts import (
    ContentKind,
    DocumentSection,
    DocumentStructureMap,
    READER_CORE_SCHEMA_VERSION,
    stable_reader_core_id,
)
from core.semantic_reader import RawSource


class DocumentStructureParseError(ValueError):
    """Raised when deterministic structure extraction cannot produce a map."""


class DocumentStructureFormat(str, Enum):
    """Formats implemented by the first deterministic structure slice."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"


@dataclass(frozen=True, slots=True)
class _HeadingMarker:
    start_offset: int
    level: int
    heading: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _SectionDraft:
    heading: str
    level: int
    start_offset: int
    end_offset: int
    parent_index: int | None = None
    warnings: tuple[str, ...] = ()


_ATX_HEADING_RE = re.compile(r"^[ \t]{0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
_FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
_TRAILING_HASHES_RE = re.compile(r"[ \t]+#+[ \t]*$")


class DeterministicDocumentStructureParser:
    """Build source-linked structure maps for plain text and Markdown."""

    parser_version = "1.0.0"

    def parse(
        self,
        source: RawSource,
        *,
        document_format: DocumentStructureFormat,
    ) -> DocumentStructureMap:
        """Parse one immutable source revision into a deterministic structure map."""

        if not isinstance(source, RawSource):
            raise DocumentStructureParseError("source must be a RawSource")
        if not isinstance(document_format, DocumentStructureFormat):
            raise DocumentStructureParseError(
                "document_format must be a DocumentStructureFormat"
            )
        if not source.text.strip():
            raise DocumentStructureParseError(
                "document text must contain at least one non-whitespace character"
            )

        content_hash = sha256(source.text.encode("utf-8")).hexdigest()
        source_revision = source.source_revision or f"sha256:{content_hash}"

        if document_format is DocumentStructureFormat.MARKDOWN:
            drafts, map_warnings = self._markdown_drafts(source.text)
        else:
            drafts = (
                _SectionDraft(
                    heading="Document",
                    level=0,
                    start_offset=0,
                    end_offset=len(source.text),
                    warnings=("plain_text_single_section",),
                ),
            )
            map_warnings = ("plain_text_single_section",)

        self._validate_full_partition(drafts, source_length=len(source.text))
        parser_id = f"reader-core.structure.{document_format.value}"
        sections = self._materialize_sections(
            drafts,
            document_id=source.document_id,
            source_revision=source_revision,
        )
        map_id = stable_reader_core_id(
            "document-structure-map",
            {
                "schema_version": READER_CORE_SCHEMA_VERSION,
                "document_id": source.document_id,
                "source_revision": source_revision,
                "parser_id": parser_id,
                "parser_version": self.parser_version,
                "content_hash": content_hash,
                "section_ids": [section.section_id for section in sections],
            },
        )
        return DocumentStructureMap(
            map_id=map_id,
            schema_version=READER_CORE_SCHEMA_VERSION,
            document_id=source.document_id,
            source_revision=source_revision,
            parser_id=parser_id,
            parser_version=self.parser_version,
            content_hash=content_hash,
            sections=sections,
            warnings=map_warnings,
        )

    def _markdown_drafts(
        self, text: str
    ) -> tuple[tuple[_SectionDraft, ...], tuple[str, ...]]:
        markers = self._markdown_heading_markers(text)
        if not markers:
            warning = "markdown_without_atx_headings_single_section"
            return (
                (
                    _SectionDraft(
                        heading="Document",
                        level=0,
                        start_offset=0,
                        end_offset=len(text),
                        warnings=(warning,),
                    ),
                ),
                (warning,),
            )

        drafts: list[_SectionDraft] = []
        if markers[0].start_offset > 0:
            preamble = text[: markers[0].start_offset]
            preamble_warnings = (
                ("whitespace_only_preamble",) if not preamble.strip() else ()
            )
            drafts.append(
                _SectionDraft(
                    heading="Preamble",
                    level=0,
                    start_offset=0,
                    end_offset=markers[0].start_offset,
                    warnings=preamble_warnings,
                )
            )

        heading_stack: list[tuple[int, int]] = []
        for marker_index, marker in enumerate(markers):
            while heading_stack and heading_stack[-1][0] >= marker.level:
                heading_stack.pop()
            parent_index = heading_stack[-1][1] if heading_stack else None
            end_offset = (
                markers[marker_index + 1].start_offset
                if marker_index + 1 < len(markers)
                else len(text)
            )
            draft_index = len(drafts)
            drafts.append(
                _SectionDraft(
                    heading=marker.heading,
                    level=marker.level,
                    start_offset=marker.start_offset,
                    end_offset=end_offset,
                    parent_index=parent_index,
                    warnings=marker.warnings,
                )
            )
            heading_stack.append((marker.level, draft_index))

        return tuple(drafts), ()

    def _markdown_heading_markers(self, text: str) -> tuple[_HeadingMarker, ...]:
        markers: list[_HeadingMarker] = []
        offset = 0
        fence_character: str | None = None
        fence_length = 0

        for line in text.splitlines(keepends=True):
            line_without_ending = line.rstrip("\r\n")
            left_trimmed = line_without_ending.lstrip(" \t")

            if fence_character is not None:
                closing_re = re.compile(
                    rf"^{re.escape(fence_character)}{{{fence_length},}}[ \t]*$"
                )
                if closing_re.fullmatch(left_trimmed):
                    fence_character = None
                    fence_length = 0
                offset += len(line)
                continue

            fence_match = _FENCE_OPEN_RE.match(line_without_ending)
            if fence_match is not None:
                fence_token = fence_match.group(1)
                fence_character = fence_token[0]
                fence_length = len(fence_token)
                offset += len(line)
                continue

            heading_match = _ATX_HEADING_RE.match(line_without_ending)
            if heading_match is not None:
                level = len(heading_match.group(1))
                raw_heading = heading_match.group(2) or ""
                heading = _TRAILING_HASHES_RE.sub("", raw_heading).strip()
                warnings: tuple[str, ...] = ()
                if not heading:
                    heading = f"Untitled heading {len(markers) + 1}"
                    warnings = ("empty_atx_heading",)
                markers.append(
                    _HeadingMarker(
                        start_offset=offset,
                        level=level,
                        heading=heading,
                        warnings=warnings,
                    )
                )

            offset += len(line)

        return tuple(markers)

    def _materialize_sections(
        self,
        drafts: tuple[_SectionDraft, ...],
        *,
        document_id: str,
        source_revision: str,
    ) -> tuple[DocumentSection, ...]:
        section_ids = tuple(
            DocumentSection.create(
                document_id=document_id,
                source_revision=source_revision,
                order_index=index,
                heading=draft.heading,
                level=draft.level,
                start_offset=draft.start_offset,
                end_offset=draft.end_offset,
                content_kind=ContentKind.TEXT,
                parser_warnings=draft.warnings,
            ).section_id
            for index, draft in enumerate(drafts)
        )

        sections = tuple(
            DocumentSection.create(
                document_id=document_id,
                source_revision=source_revision,
                order_index=index,
                heading=draft.heading,
                level=draft.level,
                start_offset=draft.start_offset,
                end_offset=draft.end_offset,
                content_kind=ContentKind.TEXT,
                parent_section_id=(
                    section_ids[draft.parent_index]
                    if draft.parent_index is not None
                    else None
                ),
                previous_section_id=section_ids[index - 1] if index > 0 else None,
                next_section_id=(
                    section_ids[index + 1] if index + 1 < len(section_ids) else None
                ),
                parser_warnings=draft.warnings,
            )
            for index, draft in enumerate(drafts)
        )
        return sections

    @staticmethod
    def _validate_full_partition(
        drafts: tuple[_SectionDraft, ...], *, source_length: int
    ) -> None:
        if not drafts:
            raise DocumentStructureParseError("parser produced no sections")
        if drafts[0].start_offset != 0 or drafts[-1].end_offset != source_length:
            raise DocumentStructureParseError(
                "sections must cover the source from offset 0 through EOF"
            )
        for previous, current in zip(drafts, drafts[1:], strict=True):
            if previous.end_offset != current.start_offset:
                raise DocumentStructureParseError(
                    "sections must form a contiguous non-overlapping partition"
                )


__all__ = [
    "DeterministicDocumentStructureParser",
    "DocumentStructureFormat",
    "DocumentStructureParseError",
]
