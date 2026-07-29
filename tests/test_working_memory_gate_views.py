from __future__ import annotations

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import WorkingMemoryCandidate, WorkingMemoryGate


def _capsule(document_id: str, text: str) -> KnowledgeCapsule:
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=text,
        start_offset=0,
        end_offset=len(text),
    )
    claim = CapsuleClaim.create(
        text=text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    return KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=text,
        claims=(claim,),
        reader_id="test.reader",
        reader_version="1",
    )


def _candidate(capsule: KnowledgeCapsule, score: float) -> WorkingMemoryCandidate:
    return WorkingMemoryCandidate(
        capsule=capsule,
        attention_score=score,
        recall_allowed=True,
        eligible=True,
        restricted=False,
        erased=False,
        protected=False,
        conflict=False,
    )


def test_active_view_preserves_gate_rank_not_audit_identity_order() -> None:
    first = _capsule("doc-alpha", "alpha")
    second = _capsule("doc-beta", "beta")
    by_identity = sorted((first, second), key=lambda item: item.capsule_id)
    low_identity, high_identity = by_identity

    low_rank = _candidate(low_identity, score=0.7)
    high_rank = _candidate(high_identity, score=0.9)
    plan = WorkingMemoryGate().plan([low_rank, high_rank])

    assert [item.capsule_id for item in plan.decisions] == [
        low_identity.capsule_id,
        high_identity.capsule_id,
    ]
    assert [item.capsule_id for item in plan.active] == [
        high_identity.capsule_id,
        low_identity.capsule_id,
    ]
    assert [item.rank for item in plan.active] == [1, 2]
