from __future__ import annotations

from collections import defaultdict
from hashlib import sha256

import pytest

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.reader_benchmark_executor import ReaderLocalBenchmarkCase
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanClaimLabel,
    HumanLabelSet,
    LabelSetRole,
)
from core.reader_product_benchmark_adapter import (
    ReaderProductBenchmarkAdapter,
    ReaderProductBenchmarkAdapterError,
)
from core.reader_product_pipeline import ReaderProductConfig
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    SemanticReader,
)


TEXT = "Alpha is required. Beta is permitted only with approval."


class _ExactQuoteReader:
    reader_id = "tests.reader-product-benchmark"
    reader_version = "1"

    def __init__(self) -> None:
        self.calls: dict[str, int] = defaultdict(int)

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode,
        budget: ReaderBudget,
    ) -> ReaderResult:
        assert isinstance(mode, ReaderMode)
        assert isinstance(budget, ReaderBudget)
        self.calls[source.text] += 1
        claim_text = source.text.strip()
        start = source.text.index(claim_text)
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=start + len(claim_text),
            source_revision=source.source_revision,
        )
        claim = CapsuleClaim.create(
            text=claim_text,
            modality=ClaimModality.OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        return ReaderResult.success(
            KnowledgeCapsule.create(
                source_document_id=source.document_id,
                essence=claim_text,
                claims=(claim,),
                reader_id=self.reader_id,
                reader_version=self.reader_version,
                coverage_score=1.0,
            )
        )


def _descriptor(root) -> CorpusDocumentDescriptor:
    return CorpusDocumentDescriptor.from_file(
        root=root,
        relative_path="doc.txt",
        document_id="doc-a",
        media_type="text/plain; charset=utf-8",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )


def _case(root) -> ReaderLocalBenchmarkCase:
    descriptor = _descriptor(root)
    span = SourceSpan.from_text(
        document_id=descriptor.document_id,
        raw_text=TEXT,
        start_offset=0,
        end_offset=len(TEXT),
        source_revision=descriptor.source_revision,
    )
    claim = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
    )
    gold = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="adjudicator",
        guideline_version="g1",
        label_version="l1",
        role=LabelSetRole.ADJUDICATED,
        claims=(claim,),
    )
    return ReaderLocalBenchmarkCase(
        case_id="case-a",
        descriptor=descriptor,
        gold=gold,
    )


def test_adapter_runs_existing_reader_product_and_normalizes_prediction(tmp_path) -> None:
    (tmp_path / "doc.txt").write_text(TEXT, encoding="utf-8")
    case = _case(tmp_path)
    adapter = ReaderProductBenchmarkAdapter(
        corpus_root=tmp_path,
        reader=_ExactQuoteReader(),
        config=ReaderProductConfig(),
    )

    result = adapter.run_case(case, replay_index=1)

    assert result.prediction.document_descriptor_id == case.descriptor.descriptor_id
    assert result.prediction.document_id == case.descriptor.document_id
    assert result.prediction.source_revision == case.descriptor.source_revision
    assert result.prediction.claims
    assert result.measurement.query_path_write_count == 0
    assert result.measurement.direct_canon_write_count == 0
    assert result.measurement.truth_gate_bypass_count == 0
    assert result.measurement.untrusted_instruction_execution_count == 0
    assert "model_tokens_unavailable_from_reader_product_v1" in result.measurement.warnings
    assert result.run_artifact_ids


def test_adapter_reverifies_exact_corpus_bytes_before_replay(tmp_path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text(TEXT, encoding="utf-8")
    case = _case(tmp_path)
    adapter = ReaderProductBenchmarkAdapter(
        corpus_root=tmp_path,
        reader=_ExactQuoteReader(),
    )

    path.write_text(TEXT + " changed", encoding="utf-8")

    with pytest.raises(
        ReaderProductBenchmarkAdapterError,
        match="no longer matches benchmark descriptor",
    ):
        adapter.run_case(case, replay_index=1)


def test_adapter_rejects_invalid_replay_index(tmp_path) -> None:
    (tmp_path / "doc.txt").write_text(TEXT, encoding="utf-8")
    case = _case(tmp_path)
    adapter = ReaderProductBenchmarkAdapter(
        corpus_root=tmp_path,
        reader=_ExactQuoteReader(),
    )

    with pytest.raises(ReaderProductBenchmarkAdapterError, match="replay_index"):
        adapter.run_case(case, replay_index=3)


def test_descriptor_revision_is_exact_utf8_sha256(tmp_path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text(TEXT, encoding="utf-8")
    descriptor = _descriptor(tmp_path)

    assert descriptor.source_revision == sha256(TEXT.encode("utf-8")).hexdigest()
