from __future__ import annotations

from pathlib import Path

from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.file_parsers.base import ParseResult
from core.reader_parse_bridge import resolve_reader_document_format
from core.semantic_reader import RawSource
from scripts.read_document import document_format_for


def test_parser_declared_markdown_overrides_pdf_suffix() -> None:
    resolution = resolve_reader_document_format(
        path_suffix=".pdf",
        structured_data={"format": "markdown", "tables": []},
    )

    assert resolution.document_format is DocumentStructureFormat.MARKDOWN
    assert resolution.reason_code == "parser_declared_markdown"
    assert resolution.parser_declared_format == "markdown"


def test_markdown_filename_remains_markdown_without_parser_metadata() -> None:
    resolution = resolve_reader_document_format(
        path_suffix=".MD",
        structured_data={},
    )

    assert resolution.document_format is DocumentStructureFormat.MARKDOWN
    assert resolution.reason_code == "markdown_filename_suffix"


def test_unknown_or_malformed_parser_format_fails_back_to_plain_text() -> None:
    unknown = resolve_reader_document_format(
        path_suffix=".pdf",
        structured_data={"format": "html"},
    )
    malformed = resolve_reader_document_format(
        path_suffix=".docx",
        structured_data={"format": {"unexpected": "mapping"}},
    )

    assert unknown.document_format is DocumentStructureFormat.PLAIN_TEXT
    assert unknown.reason_code == "plain_text_fallback"
    assert malformed.document_format is DocumentStructureFormat.PLAIN_TEXT
    assert malformed.reason_code == "plain_text_fallback"


def test_parser_declared_markdown_reaches_existing_hierarchy_parser() -> None:
    text = (
        "# Chapter One\n"
        "First chapter content.\n\n"
        "# Chapter Two\n"
        "Second chapter content.\n"
    )
    source = RawSource(document_id="reader-rich-pdf", text=text)
    resolution = resolve_reader_document_format(
        path_suffix=".pdf",
        structured_data={"format": "markdown"},
    )

    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=resolution.document_format,
    )

    assert [section.heading for section in structure.sections] == [
        "Chapter One",
        "Chapter Two",
    ]
    assert structure.sections[0].start_offset == 0
    assert structure.sections[-1].end_offset == len(text)


def test_user_facing_document_format_uses_parse_result_structure_metadata() -> None:
    parsed = ParseResult(
        file_path="book.pdf",
        file_type="pdf",
        extracted_text="# One\nText\n\n# Two\nMore text",
        structured_data={"format": "markdown"},
        extraction_method="Docling (IBM)",
    )

    assert document_format_for(Path("book.pdf"), parsed) is DocumentStructureFormat.MARKDOWN
    assert document_format_for(Path("book.pdf")) is DocumentStructureFormat.PLAIN_TEXT
