"""Exact typed-element bridge from FileIngester metadata into Reader structure.

This module does not parse files or infer structure. It accepts only parser elements
whose text sequence reconstructs the exact ``RawSource.text`` byte-for-byte at the
Python string level using the same separator used by the existing Unstructured PDF
adapter. If that binding cannot be proven, the bridge returns a fail-closed result and
the caller can keep the existing format-based Reader path.

The emitted ``DocumentStructureMap`` is derived/read-side only. It grants no memory,
Canon, TruthGate, Write Gate, tool, graph, runtime, or production authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from core.reader_core_contracts import (
    ContentKind,
    DocumentSection,
    DocumentStructureMap,
    READER_CORE_SCHEMA_VERSION,
    stable_reader_core_id,
)
from core.semantic_reader import RawSource


@dataclass(frozen=True, slots=True)
class StructuredElementResolution:
    """Result of attempting an exact typed-element structure binding."""

    structure_map: DocumentStructureMap | None
    reason_code: str
    element_count: int = 0


_ELEMENT_KIND_BY_TYPE = {
    "title": ContentKind.HEADING,
    # Unstructured Header can represent a running/page header rather than a
    # semantic document heading. Preserve the parser-owned text without
    # promoting it into hierarchy that the source metadata does not prove.
    "header": ContentKind.TEXT,
    "table": ContentKind.TABLE,
    "image": ContentKind.FIGURE,
    "picture": ContentKind.FIGURE,
    "figure": ContentKind.FIGURE,
    "figurecaption": ContentKind.CAPTION,
    "imagecaption": ContentKind.CAPTION,
    "caption": ContentKind.CAPTION,
    "footnote": ContentKind.FOOTNOTE,
    "code": ContentKind.CODE,
    "codeblock": ContentKind.CODE,
    "appendix": ContentKind.APPENDIX,
    "narrativetext": ContentKind.TEXT,
    "text": ContentKind.TEXT,
    "listitem": ContentKind.TEXT,
    "address": ContentKind.TEXT,
    "emailaddress": ContentKind.TEXT,
    "formula": ContentKind.TEXT,
    "uncategorizedtext": ContentKind.TEXT,
}


class StructuredElementBridgeError(ValueError):
    """Raised only for invalid direct API use, not ordinary parser mismatch."""


def build_exact_element_structure(
    source: RawSource,
    structured_data: Mapping[str, Any] | None,
) -> StructuredElementResolution:
    """Build a typed structure map only when parser elements exactly bind to source.

    Titan's current Unstructured PDF adapter builds ``extracted_text`` as
    ``"\n\n".join(str(element) for element in elements)`` and stores the same ordered
    strings in ``structured_data["elements"]``. That gives this bridge a deterministic
    reconstruction test. No substring search, fuzzy matching, generated headings, or
    coordinate guessing is permitted.
    """

    if not isinstance(source, RawSource):
        raise StructuredElementBridgeError("source must be a RawSource")
    if not source.text.strip():
        raise StructuredElementBridgeError("source text must not be blank")
    if not isinstance(structured_data, Mapping):
        return StructuredElementResolution(None, "structured_data_unavailable")

    raw_elements = structured_data.get("elements")
    if not isinstance(raw_elements, Sequence) or isinstance(raw_elements, (str, bytes)):
        return StructuredElementResolution(None, "typed_elements_unavailable")
    if not raw_elements:
        return StructuredElementResolution(None, "typed_elements_empty")

    elements: list[tuple[str, str]] = []
    for raw in raw_elements:
        if not isinstance(raw, Mapping):
            return StructuredElementResolution(None, "typed_element_malformed")
        raw_type = raw.get("type")
        raw_text = raw.get("text")
        if not isinstance(raw_type, str) or not raw_type.strip():
            return StructuredElementResolution(None, "typed_element_type_missing")
        if not isinstance(raw_text, str) or not raw_text:
            return StructuredElementResolution(None, "typed_element_text_missing")
        elements.append((raw_type.strip(), raw_text))

    reconstructed = "\n\n".join(text for _, text in elements)
    if reconstructed != source.text:
        return StructuredElementResolution(
            None,
            "typed_elements_source_mismatch",
            element_count=len(elements),
        )

    content_hash = sha256(source.text.encode("utf-8")).hexdigest()
    source_revision = source.source_revision or f"sha256:{content_hash}"
    section_ids = tuple(
        _section_id_for_element(
            source=source,
            source_revision=source_revision,
            index=index,
            element_type=element_type,
            start_offset=_element_start_offset(elements, index),
            end_offset=_element_end_offset(elements, index),
        )
        for index, (element_type, _) in enumerate(elements)
    )

    sections: list[DocumentSection] = []
    cursor = 0
    for index, (element_type, element_text) in enumerate(elements):
        start_offset = cursor
        end_offset = start_offset + len(element_text)
        if index + 1 < len(elements):
            end_offset += 2  # exact "\n\n" separator belongs to the preceding element
        cursor = end_offset
        kind = _content_kind(element_type)
        warnings = () if kind is not ContentKind.UNKNOWN else (
            f"unrecognized_element_type:{element_type}",
        )
        sections.append(
            DocumentSection(
                section_id=section_ids[index],
                document_id=source.document_id,
                source_revision=source_revision,
                order_index=index,
                heading=_section_heading(kind, element_type, element_text, index),
                level=1 if kind is ContentKind.HEADING else 0,
                start_offset=start_offset,
                end_offset=end_offset,
                content_kind=kind,
                previous_section_id=section_ids[index - 1] if index > 0 else None,
                next_section_id=(
                    section_ids[index + 1] if index + 1 < len(section_ids) else None
                ),
                parser_warnings=warnings,
            )
        )

    if cursor != len(source.text):
        return StructuredElementResolution(
            None,
            "typed_elements_partition_mismatch",
            element_count=len(elements),
        )

    parser_id = "reader-core.structure.unstructured-elements"
    parser_version = "1.0.0"
    map_id = stable_reader_core_id(
        "document-structure-map",
        {
            "schema_version": READER_CORE_SCHEMA_VERSION,
            "document_id": source.document_id,
            "source_revision": source_revision,
            "parser_id": parser_id,
            "parser_version": parser_version,
            "content_hash": content_hash,
            "section_ids": [section.section_id for section in sections],
        },
    )
    structure = DocumentStructureMap(
        map_id=map_id,
        schema_version=READER_CORE_SCHEMA_VERSION,
        document_id=source.document_id,
        source_revision=source_revision,
        parser_id=parser_id,
        parser_version=parser_version,
        content_hash=content_hash,
        sections=tuple(sections),
        warnings=("exact_parser_elements_reused",),
    )
    return StructuredElementResolution(
        structure,
        "exact_typed_elements",
        element_count=len(elements),
    )


def _content_kind(element_type: str) -> ContentKind:
    return _ELEMENT_KIND_BY_TYPE.get(element_type.replace("_", "").lower(), ContentKind.UNKNOWN)


def _section_heading(
    kind: ContentKind,
    element_type: str,
    element_text: str,
    index: int,
) -> str:
    if kind is ContentKind.HEADING:
        heading = next((line.strip() for line in element_text.splitlines() if line.strip()), "")
        if heading:
            return heading
    return f"{element_type} {index + 1}"


def _element_start_offset(elements: list[tuple[str, str]], index: int) -> int:
    return sum(len(text) + 2 for _, text in elements[:index])


def _element_end_offset(elements: list[tuple[str, str]], index: int) -> int:
    end = _element_start_offset(elements, index) + len(elements[index][1])
    if index + 1 < len(elements):
        end += 2
    return end


def _section_id_for_element(
    *,
    source: RawSource,
    source_revision: str,
    index: int,
    element_type: str,
    start_offset: int,
    end_offset: int,
) -> str:
    kind = _content_kind(element_type)
    return stable_reader_core_id(
        "document-section",
        {
            "document_id": source.document_id,
            "source_revision": source_revision,
            "order_index": index,
            "heading": _section_heading(kind, element_type, source.text[start_offset:end_offset], index),
            "level": 1 if kind is ContentKind.HEADING else 0,
            "start_offset": start_offset,
            "end_offset": end_offset,
            "content_kind": kind.value,
        },
    )


__all__ = [
    "StructuredElementBridgeError",
    "StructuredElementResolution",
    "build_exact_element_structure",
]
