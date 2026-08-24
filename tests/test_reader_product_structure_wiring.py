from __future__ import annotations

from dataclasses import replace

import pytest

from core.document_structure import DocumentStructureFormat
from core.reader_product_structure_wiring import (
    ReaderProductStructureWiringError,
    read_with_optional_exact_structure,
)
from core.reader_structured_elements_bridge import build_exact_element_structure
from core.readers.extractive import ExtractiveReader
from core.semantic_reader import RawSource, ReaderMode
from core.reader_product_pipeline import ReaderProductConfig


def _source_and_map():
    text = "Overview.\n\nMetric | Value\n42 | stable.\n\nFigure 1 caption."
    source = RawSource(
        document_id="doc:typed-product",
        text=text,
        source_revision="rev:typed-product",
    )
    resolution = build_exact_element_structure(
        source,
        {
            "elements": [
                {"type": "Title", "text": "Overview."},
                {"type": "Table", "text": "Metric | Value\n42 | stable."},
                {"type": "FigureCaption", "text": "Figure 1 caption."},
            ]
        },
    )
    assert resolution.structure_map is not None
    return source, resolution.structure_map


@pytest.mark.asyncio
async def test_exact_typed_structure_reaches_product_planner_as_atomic_units() -> None:
    source, structure = _source_and_map()
    result = await read_with_optional_exact_structure(
        ExtractiveReader(),
        source,
        structure_map=structure,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
        config=ReaderProductConfig(initial_mode=ReaderMode.FAST),
    )

    assert result.reading_plan.structure_map_id == structure.map_id
    assert len(result.reading_plan.units) == 3
    assert [
        (unit.start_offset, unit.end_offset)
        for unit in result.reading_plan.units
    ] == [
        (section.start_offset, section.end_offset)
        for section in structure.sections
    ]


@pytest.mark.asyncio
async def test_missing_prebuilt_structure_preserves_existing_plain_text_path() -> None:
    source = RawSource(
        document_id="doc:fallback",
        text="One complete sentence. Another complete sentence.",
        source_revision="rev:fallback",
    )
    result = await read_with_optional_exact_structure(
        ExtractiveReader(),
        source,
        structure_map=None,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
        config=ReaderProductConfig(initial_mode=ReaderMode.FAST),
    )

    assert result.total_units >= 1
    assert result.reading_plan.document_id == source.document_id


@pytest.mark.asyncio
async def test_mismatched_structure_revision_fails_before_reader_execution() -> None:
    source, structure = _source_and_map()
    bad = replace(structure, source_revision="rev:wrong")

    with pytest.raises(
        ReaderProductStructureWiringError,
        match="source_revision",
    ):
        await read_with_optional_exact_structure(
            ExtractiveReader(),
            source,
            structure_map=bad,
            config=ReaderProductConfig(initial_mode=ReaderMode.FAST),
        )
