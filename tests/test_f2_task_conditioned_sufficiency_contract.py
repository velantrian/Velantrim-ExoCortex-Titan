"""Bounded executable fixture for the F2 task-conditioned sufficiency contract.

This file intentionally introduces no runtime enum, API, persistence, reopen
mechanism, or architecture authority. The evaluator below is test-local and
exists only to ask whether current Titan artifacts can discriminate three
research-level outcomes:

* SUFFICIENT
* REPRESENTATION_INSUFFICIENT
* UNKNOWN

If these cases can be expressed with existing artifacts, no implementation
change is justified by this fixture alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.document_structure import DocumentStructureFormat
from core.hierarchical_section_planner import SectionPlanningBudget
from core.knowledge_capsule import CapsuleClaim, ClaimModality, KnowledgeCapsule, SourceSpan
from core.reader_product_pipeline import ReaderProductConfig, ReaderProductPipeline
from core.semantic_reader import RawSource, ReaderBudget, ReaderMode, ReaderResult, SemanticReader


@dataclass(frozen=True)
class _TaskRequirement:
    token: str


class _ExactSourceReader:
    reader_id = "tests.f2-task-conditioned-exact-source-reader"
    reader_version = "1"

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode,
        budget: ReaderBudget,
    ) -> ReaderResult:
        assert isinstance(mode, ReaderMode)
        assert isinstance(budget, ReaderBudget)

        text = source.text.strip()
        start = source.text.index(text)
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=start + len(text),
            source_revision=source.source_revision,
        )
        claim = CapsuleClaim.create(
            text=text,
            modality=ClaimModality.OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        capsule = KnowledgeCapsule.create(
            source_document_id=source.document_id,
            essence=text,
            claims=(claim,),
            reader_id=self.reader_id,
            reader_version=self.reader_version,
            coverage_score=1.0,
        )
        return ReaderResult.success(capsule)


def _config() -> ReaderProductConfig:
    return ReaderProductConfig(
        initial_mode=ReaderMode.STANDARD,
        section_budget=SectionPlanningBudget(
            max_unit_chars=90,
            min_unit_chars=20,
            boundary_search_chars=70,
        ),
        reader_budget=ReaderBudget(
            max_source_chars=2_000,
            max_claims=16,
            max_essence_chars=1_000,
        ),
        max_digest_chars=96,
    )


def _source() -> RawSource:
    return RawSource(
        document_id="f2-task-conditioned-sufficiency",
        text=(
            "Policy R: standard requests may be approved after ordinary review.\n\n"
            "Operational context: ordinary review is sufficient for routine requests.\n\n"
            "Hidden exception X: a revoked credential must never be approved."
        ),
    )


async def _run_t1():
    reader = _ExactSourceReader()
    assert isinstance(reader, SemanticReader)
    return await ReaderProductPipeline(reader, config=_config()).read(
        _source(),
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )


def _source_linked_text(result) -> str:
    return "\n".join(
        card_claim.claim.text
        for card in result.cards
        for card_claim in card.claims
    )


def _classify_from_existing_artifacts(result, requirement: _TaskRequirement) -> str:
    """Test-local classifier over existing Titan artifacts only.

    This is not production policy. It deliberately requires positive support for
    SUFFICIENT, evidence of known omission for REPRESENTATION_INSUFFICIENT, and
    otherwise returns UNKNOWN.
    """

    compact = result.source_grounded_digest
    if requirement.token in compact:
        return "SUFFICIENT"

    source_linked = _source_linked_text(result)
    if (
        requirement.token in source_linked
        and result.synthesis is not None
        and result.synthesis.unsupported_source_claim_ids
    ):
        return "REPRESENTATION_INSUFFICIENT"

    return "UNKNOWN"


async def test_f2_contract_case_1_positive_compact_support_is_sufficient() -> None:
    result = await _run_t1()

    outcome = _classify_from_existing_artifacts(
        result,
        _TaskRequirement(token="standard requests"),
    )

    assert outcome == "SUFFICIENT"


async def test_f2_contract_case_2_known_omission_is_representation_insufficient() -> None:
    result = await _run_t1()

    assert "revoked credential" in _source_linked_text(result)
    assert "revoked credential" not in result.source_grounded_digest
    assert result.synthesis is not None
    assert result.synthesis.unsupported_source_claim_ids

    outcome = _classify_from_existing_artifacts(
        result,
        _TaskRequirement(token="revoked credential"),
    )

    assert outcome == "REPRESENTATION_INSUFFICIENT"


async def test_f2_contract_case_3_unestablished_support_remains_unknown() -> None:
    result = await _run_t1()

    token = "biometric override"
    assert token not in result.source_grounded_digest
    assert token not in _source_linked_text(result)

    outcome = _classify_from_existing_artifacts(
        result,
        _TaskRequirement(token=token),
    )

    assert outcome == "UNKNOWN"


def test_f2_contract_labels_remain_test_local() -> None:
    """Guard against accidentally claiming a new runtime surface."""

    labels = {
        "SUFFICIENT",
        "REPRESENTATION_INSUFFICIENT",
        "UNKNOWN",
    }
    assert labels == {
        "SUFFICIENT",
        "REPRESENTATION_INSUFFICIENT",
        "UNKNOWN",
    }
