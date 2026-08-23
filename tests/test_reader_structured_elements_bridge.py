from __future__ import annotations

from core.reader_core_contracts import ContentKind
from core.reader_structured_elements_bridge import build_exact_element_structure
from core.semantic_reader import RawSource


def _source(text: str) -> RawSource:
    return RawSource(
        document_id="typed-elements-doc",
        text=text,
        source_revision="sha256:" + "a" * 64,
    )


def test_exact_unstructured_elements_materialize_typed_reader_sections() -> None:
    elements = [
        {"type": "Title", "text": "Chapter One"},
        {"type": "NarrativeText", "text": "Intro text."},
        {"type": "Table", "text": "A | B\n1 | 2"},
        {"type": "FigureCaption", "text": "Figure 1. Architecture"},
        {"type": "Footnote", "text": "1. Source note"},
        {"type": "CodeBlock", "text": "print('hello')"},
    ]
    text = "\n\n".join(item["text"] for item in elements)

    resolution = build_exact_element_structure(
        _source(text),
        {"elements": elements, "strategy": "hi_res"},
    )

    assert resolution.reason_code == "exact_typed_elements"
    assert resolution.element_count == len(elements)
    assert resolution.structure_map is not None
    structure = resolution.structure_map
    assert [section.content_kind for section in structure.sections] == [
        ContentKind.HEADING,
        ContentKind.TEXT,
        ContentKind.TABLE,
        ContentKind.CAPTION,
        ContentKind.FOOTNOTE,
        ContentKind.CODE,
    ]
    assert [section.order_index for section in structure.sections] == list(range(6))
    assert structure.sections[0].start_offset == 0
    assert structure.sections[-1].end_offset == len(text)
    assert all(
        left.end_offset == right.start_offset
        for left, right in zip(structure.sections, structure.sections[1:])
    )


def test_exact_offsets_slice_back_to_element_text_plus_owned_separator() -> None:
    elements = [
        {"type": "NarrativeText", "text": "alpha"},
        {"type": "Table", "text": "beta"},
        {"type": "NarrativeText", "text": "gamma"},
    ]
    text = "alpha\n\nbeta\n\ngamma"
    resolution = build_exact_element_structure(_source(text), {"elements": elements})

    assert resolution.structure_map is not None
    sections = resolution.structure_map.sections
    assert text[sections[0].start_offset : sections[0].end_offset] == "alpha\n\n"
    assert text[sections[1].start_offset : sections[1].end_offset] == "beta\n\n"
    assert text[sections[2].start_offset : sections[2].end_offset] == "gamma"


def test_source_mismatch_fails_closed_without_fuzzy_alignment() -> None:
    source = _source("alpha\n\nBETA")
    resolution = build_exact_element_structure(
        source,
        {
            "elements": [
                {"type": "NarrativeText", "text": "alpha"},
                {"type": "Table", "text": "beta"},
            ]
        },
    )

    assert resolution.structure_map is None
    assert resolution.reason_code == "typed_elements_source_mismatch"
    assert resolution.element_count == 2


def test_missing_or_malformed_elements_do_not_create_structure() -> None:
    missing = build_exact_element_structure(_source("text"), {"format": "plain_text"})
    malformed = build_exact_element_structure(
        _source("text"),
        {"elements": [{"type": "Table", "text": None}]},
    )

    assert missing.structure_map is None
    assert missing.reason_code == "typed_elements_unavailable"
    assert malformed.structure_map is None
    assert malformed.reason_code == "typed_element_text_missing"


def test_unknown_element_type_is_preserved_but_not_promoted_to_known_kind() -> None:
    resolution = build_exact_element_structure(
        _source("mystery"),
        {"elements": [{"type": "FutureParserThing", "text": "mystery"}]},
    )

    assert resolution.structure_map is not None
    section = resolution.structure_map.sections[0]
    assert section.content_kind is ContentKind.UNKNOWN
    assert section.parser_warnings == ("unrecognized_element_type:FutureParserThing",)
