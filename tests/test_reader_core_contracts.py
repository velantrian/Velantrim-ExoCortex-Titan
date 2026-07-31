from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from core.reader_core_contracts import (
    ContentKind,
    CoverageAxis,
    CoverageValue,
    DocumentSection,
    DocumentStructureMap,
    READER_CORE_SCHEMA_VERSION,
    ReaderCoreContractError,
    ReadingSessionCheckpoint,
    SessionState,
    stable_reader_core_id,
)


def _section(*, order_index: int = 0, start: int = 0, end: int = 10) -> DocumentSection:
    return DocumentSection.create(
        document_id="doc-1",
        source_revision="rev-1",
        order_index=order_index,
        heading=f"Section {order_index}",
        level=1,
        start_offset=start,
        end_offset=end,
        content_kind=ContentKind.TEXT,
    )


def test_stable_id_is_deterministic_and_unicode_normalized_by_caller_payload() -> None:
    payload = {"text": "café", "index": 1}
    assert stable_reader_core_id("example", payload) == stable_reader_core_id("example", payload)
    assert len(stable_reader_core_id("example", payload)) == 64


def test_document_section_is_immutable_and_has_stable_identity() -> None:
    left = _section()
    right = _section()
    assert left.section_id == right.section_id
    with pytest.raises(FrozenInstanceError):
        left.heading = "changed"  # type: ignore[misc]


def test_structure_map_rejects_mismatched_revision() -> None:
    section = DocumentSection.create(
        document_id="doc-1",
        source_revision="other-rev",
        order_index=0,
        heading="Intro",
        level=1,
        start_offset=0,
        end_offset=5,
    )
    with pytest.raises(ReaderCoreContractError, match="source_revision"):
        DocumentStructureMap(
            map_id="map-1",
            schema_version=READER_CORE_SCHEMA_VERSION,
            document_id="doc-1",
            source_revision="rev-1",
            parser_id="plain-text",
            parser_version="1",
            content_hash=sha256(b"hello").hexdigest(),
            sections=(section,),
        )


def test_structure_map_requires_unique_ordered_sections() -> None:
    first = _section(order_index=1, start=10, end=20)
    second = _section(order_index=0, start=0, end=10)
    with pytest.raises(ReaderCoreContractError, match="ordered"):
        DocumentStructureMap(
            map_id="map-1",
            schema_version=READER_CORE_SCHEMA_VERSION,
            document_id="doc-1",
            source_revision="rev-1",
            parser_id="plain-text",
            parser_version="1",
            content_hash=sha256(b"x" * 20).hexdigest(),
            sections=(first, second),
        )


def test_coverage_has_no_false_percentage_when_denominator_unknown() -> None:
    unknown = CoverageValue(
        axis=CoverageAxis.CLAIM,
        processed_units=0,
        known_units=0,
    )
    assert unknown.ratio is None


def test_coverage_rejects_processed_greater_than_known() -> None:
    with pytest.raises(ReaderCoreContractError, match="cannot exceed"):
        CoverageValue(
            axis=CoverageAxis.EXCEPTION,
            processed_units=2,
            known_units=1,
        )


def test_checkpoint_requires_disjoint_completed_and_pending_sets() -> None:
    with pytest.raises(ReaderCoreContractError, match="disjoint"):
        ReadingSessionCheckpoint(
            session_id="session-1",
            document_id="doc-1",
            source_revision="rev-1",
            state=SessionState.READING,
            completed_section_ids=("section-1",),
            pending_section_ids=("section-1",),
        )


def test_contracts_do_not_expose_authority_fields() -> None:
    checkpoint_fields = ReadingSessionCheckpoint.__dataclass_fields__
    structure_fields = DocumentStructureMap.__dataclass_fields__
    forbidden = {
        "canon_write",
        "memory_write",
        "truth_gate_bypass",
        "tool_authority",
        "policy_authority",
    }
    assert forbidden.isdisjoint(checkpoint_fields)
    assert forbidden.isdisjoint(structure_fields)
