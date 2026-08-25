from __future__ import annotations

from core.file_parsers.base import ParseResult
from core.reader_core_contracts import ContentKind
from scripts.read_document import exact_structure_for, raw_source_for, selected_structure_map


def _parsed_with_elements(text: str, elements: list[dict[str, str]]) -> ParseResult:
    return ParseResult(
        file_path="book.pdf",
        file_type="pdf",
        extracted_text=text,
        structured_data={"elements": elements},
        extraction_method="Unstructured",
    )


def test_cli_selects_exact_typed_structure_when_elements_reconstruct_source() -> None:
    elements = [
        {"type": "Title", "text": "Chapter One"},
        {"type": "NarrativeText", "text": "A claim."},
        {"type": "Table", "text": "A | B\n1 | 2"},
    ]
    text = "\n\n".join(item["text"] for item in elements)
    parsed = _parsed_with_elements(text, elements)
    source = raw_source_for(parsed.file_path, text)

    resolution = exact_structure_for(parsed, source)
    structure = selected_structure_map(parsed, source)

    assert resolution.reason_code == "exact_typed_elements"
    assert structure is not None
    assert [section.content_kind for section in structure.sections] == [
        ContentKind.HEADING,
        ContentKind.TEXT,
        ContentKind.TABLE,
    ]
    assert structure.sections[0].start_offset == 0
    assert structure.sections[-1].end_offset == len(text)


def test_cli_falls_back_when_typed_elements_do_not_exactly_match_source() -> None:
    text = "Chapter One\n\nActual text."
    parsed = _parsed_with_elements(
        text,
        [
            {"type": "Title", "text": "Chapter One"},
            {"type": "NarrativeText", "text": "Different text."},
        ],
    )
    source = raw_source_for(parsed.file_path, text)

    resolution = exact_structure_for(parsed, source)

    assert resolution.reason_code == "typed_elements_source_mismatch"
    assert resolution.structure_map is None
    assert selected_structure_map(parsed, source) is None


def test_cli_does_not_invent_typed_structure_when_elements_are_absent() -> None:
    parsed = ParseResult(
        file_path="book.pdf",
        file_type="pdf",
        extracted_text="Plain extracted text.",
        structured_data={"format": "markdown"},
        extraction_method="Docling (IBM)",
    )
    source = raw_source_for(parsed.file_path, parsed.extracted_text)

    resolution = exact_structure_for(parsed, source)

    assert resolution.reason_code == "typed_elements_unavailable"
    assert resolution.structure_map is None
    assert selected_structure_map(parsed, source) is None
