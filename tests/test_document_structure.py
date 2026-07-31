from hashlib import sha256
from pathlib import Path

import pytest

from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
    DocumentStructureParseError,
)
from core.semantic_reader import RawSource


FIXTURES = Path(__file__).parent / "fixtures" / "reader_core"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_plain_text_is_one_exact_source_partition() -> None:
    text = _fixture("rdr_01_plain_text.txt")
    structure = DeterministicDocumentStructureParser().parse(
        RawSource(document_id="plain-doc", text=text),
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )

    assert structure.source_revision == f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"
    assert structure.content_hash == sha256(text.encode("utf-8")).hexdigest()
    assert structure.warnings == ("plain_text_single_section",)
    assert len(structure.sections) == 1
    section = structure.sections[0]
    assert section.heading == "Document"
    assert section.start_offset == 0
    assert section.end_offset == len(text)
    assert text[section.start_offset : section.end_offset] == text
    assert section.previous_section_id is None
    assert section.next_section_id is None
    assert section.parent_section_id is None


def test_markdown_builds_hierarchy_links_and_exact_offsets() -> None:
    text = _fixture("rdr_01_markdown.md")
    structure = DeterministicDocumentStructureParser().parse(
        RawSource(
            document_id="markdown-doc",
            text=text,
            source_revision="revision-1",
        ),
        document_format=DocumentStructureFormat.MARKDOWN,
    )

    sections = structure.sections
    assert [section.heading for section in sections] == [
        "Preamble",
        "Root",
        "Child",
        "Grandchild",
        "Second Root",
    ]
    assert [section.start_offset for section in sections] == [
        0,
        text.index("# Root"),
        text.index("## Child"),
        text.index("### Grandchild"),
        text.index("# Second Root"),
    ]
    assert sections[-1].end_offset == len(text)
    assert sections[1].parent_section_id is None
    assert sections[2].parent_section_id == sections[1].section_id
    assert sections[3].parent_section_id == sections[2].section_id
    assert sections[4].parent_section_id is None

    for index, section in enumerate(sections):
        expected_previous = sections[index - 1].section_id if index > 0 else None
        expected_next = sections[index + 1].section_id if index + 1 < len(sections) else None
        assert section.previous_section_id == expected_previous
        assert section.next_section_id == expected_next

    for previous, current in zip(sections, sections[1:]):
        assert previous.end_offset == current.start_offset
    assert sections[0].start_offset == 0
    assert sections[-1].end_offset == len(text)


def test_markdown_ignores_heading_syntax_inside_fenced_code() -> None:
    text = _fixture("rdr_01_markdown.md")
    structure = DeterministicDocumentStructureParser().parse(
        RawSource(document_id="markdown-doc", text=text),
        document_format=DocumentStructureFormat.MARKDOWN,
    )

    assert "Not a heading" not in {
        section.heading for section in structure.sections
    }


def test_structure_identity_is_deterministic() -> None:
    text = _fixture("rdr_01_markdown.md")
    source = RawSource(
        document_id="markdown-doc",
        text=text,
        source_revision="revision-1",
    )
    parser = DeterministicDocumentStructureParser()

    first = parser.parse(source, document_format=DocumentStructureFormat.MARKDOWN)
    second = parser.parse(source, document_format=DocumentStructureFormat.MARKDOWN)

    assert first.map_id == second.map_id
    assert [section.section_id for section in first.sections] == [
        section.section_id for section in second.sections
    ]


def test_markdown_without_atx_headings_degrades_to_one_section() -> None:
    text = "A title\n=======\n\nBody without ATX syntax.\n"
    structure = DeterministicDocumentStructureParser().parse(
        RawSource(document_id="setext-doc", text=text),
        document_format=DocumentStructureFormat.MARKDOWN,
    )

    assert len(structure.sections) == 1
    assert structure.sections[0].start_offset == 0
    assert structure.sections[0].end_offset == len(text)
    assert structure.warnings == (
        "markdown_without_atx_headings_single_section",
    )


def test_empty_or_whitespace_only_document_is_rejected() -> None:
    parser = DeterministicDocumentStructureParser()

    with pytest.raises(DocumentStructureParseError, match="non-whitespace"):
        parser.parse(
            RawSource(document_id="empty-doc", text="  \n\t"),
            document_format=DocumentStructureFormat.PLAIN_TEXT,
        )
