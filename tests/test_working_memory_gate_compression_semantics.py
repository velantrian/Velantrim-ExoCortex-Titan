from __future__ import annotations

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import (
    GateDisposition,
    GateReason,
    WorkingMemoryBudget,
    WorkingMemoryCandidate,
    WorkingMemoryGate,
)


def _claim(document_id: str, raw_text: str, text: str, start: int, **kwargs) -> CapsuleClaim:
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=raw_text,
        start_offset=start,
        end_offset=start + len(text),
    )
    return CapsuleClaim.create(
        text=text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
        **kwargs,
    )


def _candidate(capsule: KnowledgeCapsule) -> WorkingMemoryCandidate:
    return WorkingMemoryCandidate(
        capsule=capsule,
        attention_score=1.0,
        recall_allowed=True,
        eligible=True,
        restricted=False,
        erased=False,
        protected=False,
        conflict=False,
    )


def _only_decision(capsule: KnowledgeCapsule, max_chars: int):
    plan = WorkingMemoryGate().plan(
        [_candidate(capsule)],
        budget=WorkingMemoryBudget(max_items=1, max_chars=max_chars),
    )
    return plan.decisions[0]


def test_claim_annotations_block_compression_until_contextpack_can_preserve_them() -> None:
    document_id = "doc-qualified"
    text = "If approved, deploy the release."
    qualifier = "If approved"
    claim = _claim(
        document_id,
        text,
        text,
        0,
        qualifiers=(qualifier,),
        applicability_conditions=(qualifier,),
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=text,
        claims=(claim,),
        reader_id="test.reader",
        reader_version="1",
    )

    decision = _only_decision(capsule, max_chars=len(text))

    assert decision.disposition is GateDisposition.DEFER
    assert GateReason.FULL_CONTENT_OVER_BUDGET in decision.reasons
    assert GateReason.COMPRESSED_SEMANTICS_UNSUPPORTED in decision.reasons
    assert GateReason.ESSENCE_NOT_SOURCE_LINKED not in decision.reasons


def test_top_level_semantic_metadata_blocks_compression() -> None:
    document_id = "doc-entity"
    first = "Alice approved the release."
    second = "Deployment starts tomorrow."
    raw_text = f"{first} {second}"
    first_claim = _claim(document_id, raw_text, first, 0)
    second_claim = _claim(document_id, raw_text, second, len(first) + 1)
    capsule = KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=first,
        claims=(first_claim, second_claim),
        reader_id="test.reader",
        reader_version="1",
        entities=("Alice",),
    )

    decision = _only_decision(capsule, max_chars=len(first))

    assert decision.disposition is GateDisposition.DEFER
    assert GateReason.FULL_CONTENT_OVER_BUDGET in decision.reasons
    assert GateReason.COMPRESSED_SEMANTICS_UNSUPPORTED in decision.reasons
