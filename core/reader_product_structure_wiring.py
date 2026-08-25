"""Bounded product wiring for exact prebuilt Reader structure maps.

This module composes the existing ``ReaderProductPipeline`` instead of changing its
public API. A prebuilt ``DocumentStructureMap`` is accepted only when its document
identity, source revision, content hash, and exact contiguous partition match the
immutable ``RawSource`` supplied to Reader.

No parser inference, fuzzy alignment, memory/Canon write, TruthGate/Write Gate call,
graph mutation, runtime activation, or production authority is introduced.
"""

from __future__ import annotations

from hashlib import sha256

from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.reader_core_contracts import DocumentStructureMap
from core.reader_product_pipeline import (
    ReaderProductConfig,
    ReaderProductPipeline,
    ReaderProductPipelineError,
    ReaderProductResult,
)
from core.semantic_reader import RawSource, SemanticReader


class ReaderProductStructureWiringError(ReaderProductPipelineError):
    """Raised when a prebuilt structure cannot bind exactly to Reader source."""


class _ExactPrebuiltStructureParser(DeterministicDocumentStructureParser):
    """Parser-compatible adapter returning one already-validated immutable map."""

    def __init__(self, structure_map: DocumentStructureMap) -> None:
        self._structure_map = structure_map

    def parse(
        self,
        source: RawSource,
        *,
        document_format: DocumentStructureFormat,
    ) -> DocumentStructureMap:
        del document_format
        _validate_exact_structure(source, self._structure_map)
        return self._structure_map


class StructuredReaderProductPipeline(ReaderProductPipeline):
    """Existing Reader product pipeline with one exact prebuilt structure map bound."""

    def __init__(
        self,
        reader: SemanticReader,
        *,
        structure_map: DocumentStructureMap,
        config: ReaderProductConfig | None = None,
    ) -> None:
        if not isinstance(structure_map, DocumentStructureMap):
            raise ReaderProductStructureWiringError(
                "structure_map must be a DocumentStructureMap"
            )
        super().__init__(reader, config=config)
        self._structure_parser = _ExactPrebuiltStructureParser(structure_map)


async def read_with_optional_exact_structure(
    reader: SemanticReader,
    source: RawSource,
    *,
    structure_map: DocumentStructureMap | None,
    document_format: DocumentStructureFormat = DocumentStructureFormat.PLAIN_TEXT,
    config: ReaderProductConfig | None = None,
    session_key: str | None = None,
) -> ReaderProductResult:
    """Use exact prebuilt structure when available; otherwise preserve current path."""

    if structure_map is None:
        return await ReaderProductPipeline(reader, config=config).read(
            source,
            document_format=document_format,
            session_key=session_key,
        )

    _validate_exact_structure(source, structure_map)
    return await StructuredReaderProductPipeline(
        reader,
        structure_map=structure_map,
        config=config,
    ).read(
        source,
        document_format=document_format,
        session_key=session_key,
    )


def _validate_exact_structure(
    source: RawSource,
    structure_map: DocumentStructureMap,
) -> None:
    if not isinstance(source, RawSource):
        raise ReaderProductStructureWiringError("source must be a RawSource")
    if not isinstance(structure_map, DocumentStructureMap):
        raise ReaderProductStructureWiringError(
            "structure_map must be a DocumentStructureMap"
        )
    if not source.text.strip():
        raise ReaderProductStructureWiringError("source text must not be blank")

    digest = sha256(source.text.encode("utf-8")).hexdigest()
    source_revision = source.source_revision or f"sha256:{digest}"
    if structure_map.document_id != source.document_id:
        raise ReaderProductStructureWiringError(
            "structure_map document_id does not match Reader source"
        )
    if structure_map.source_revision != source_revision:
        raise ReaderProductStructureWiringError(
            "structure_map source_revision does not match Reader source"
        )
    if structure_map.content_hash != digest:
        raise ReaderProductStructureWiringError(
            "structure_map content_hash does not match Reader source"
        )

    sections = structure_map.sections
    if sections[0].start_offset != 0 or sections[-1].end_offset != len(source.text):
        raise ReaderProductStructureWiringError(
            "structure_map must cover Reader source from offset 0 through EOF"
        )
    for previous, current in zip(sections, sections[1:]):
        if previous.end_offset != current.start_offset:
            raise ReaderProductStructureWiringError(
                "structure_map sections must be contiguous and non-overlapping"
            )


__all__ = [
    "ReaderProductStructureWiringError",
    "StructuredReaderProductPipeline",
    "read_with_optional_exact_structure",
]
