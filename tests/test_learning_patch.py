from __future__ import annotations

import pytest

from core.learning_patch import (
    ChargeSignalProposal,
    ClaimProposal,
    IntentPatternProposal,
    LearningPatch,
    LexicalAssociationProposal,
    PatchProvenance,
    PatchStatus,
    RetrievalPolicyProposal,
)


def provenance() -> PatchProvenance:
    return PatchProvenance(
        conversation_id="chat-42",
        actor="dialogue_analyzer",
        model="test-model",
        message_ids=("m1", "m2"),
    )


def test_valid_mixed_patch_serializes_without_applying() -> None:
    patch = LearningPatch(
        provenance=provenance(),
        claims=(
            ClaimProposal(
                text="Пользователь предпочитает краткие ответы",
                confidence=0.7,
                evidence_refs=("m2",),
                knowledge_type="preference",
            ),
        ),
        lexical_associations=(
            LexicalAssociationProposal(
                surface="как работает",
                concept="question.mechanism",
                weight=0.85,
                language="ru",
            ),
        ),
        intent_patterns=(
            IntentPatternProposal(
                intent="explain_mechanism",
                pattern=r"как\s+работает",
                confidence=0.8,
                language="ru",
            ),
        ),
        retrieval_policy=RetrievalPolicyProposal(
            threshold=0.65,
            max_items=12,
            reason="shadow experiment",
        ),
        charge_signals=(
            ChargeSignalProposal(
                target_id="claim-1",
                signal_type="EXPLICIT_PRIORITY",
                magnitude=0.9,
            ),
        ),
    )

    assert patch.validate().is_valid
    assert patch.status is PatchStatus.PROPOSED
    assert not hasattr(patch, "apply")
    assert patch.to_dict()["status"] == "PROPOSED"


def test_invalid_regex_is_reported_without_losing_valid_claim() -> None:
    patch = LearningPatch(
        provenance=provenance(),
        claims=(ClaimProposal(text="valid proposal", confidence=0.5),),
        intent_patterns=(
            IntentPatternProposal(intent="broken", pattern="(", confidence=0.8),
        ),
    )

    findings = patch.validate().findings

    assert any(item.code == "LP_PATTERN_INVALID" for item in findings)
    assert not any(item.path.startswith("claims") for item in findings)


def test_partial_retrieval_policy_is_allowed_and_bounds_are_enforced() -> None:
    valid = LearningPatch(
        provenance=provenance(),
        retrieval_policy=RetrievalPolicyProposal(threshold=0.4),
    )
    invalid = LearningPatch(
        provenance=provenance(),
        retrieval_policy=RetrievalPolicyProposal(
            mode="unknown", threshold=1.2, max_items=0, graph_depth=9
        ),
    )

    assert valid.validate().is_valid
    codes = {item.code for item in invalid.validate().findings}
    assert {
        "LP_RETRIEVAL_MODE",
        "LP_UNIT_INTERVAL",
        "LP_RETRIEVAL_MAX_ITEMS",
        "LP_RETRIEVAL_GRAPH_DEPTH",
    } <= codes


def test_normalization_deduplicates_associations_and_keeps_highest_weight() -> None:
    patch = LearningPatch(
        provenance=provenance(),
        lexical_associations=(
            LexicalAssociationProposal(" Чай ", "Напиток", 0.4, "RU"),
            LexicalAssociationProposal("чай", "напиток", 0.9, "ru"),
        ),
    )

    normalized = patch.normalized()

    assert len(normalized.lexical_associations) == 1
    association = normalized.lexical_associations[0]
    assert (association.surface, association.concept, association.weight) == (
        "чай",
        "напиток",
        0.9,
    )


def test_empty_patch_is_rejected() -> None:
    patch = LearningPatch(provenance=provenance())

    assert any(item.code == "LP_EMPTY" for item in patch.validate().findings)
    with pytest.raises(ValueError, match="invalid LearningPatch"):
        patch.assert_valid()


def test_charge_signal_has_no_truth_or_evidence_fields() -> None:
    patch = LearningPatch(
        provenance=provenance(),
        charge_signals=(
            ChargeSignalProposal(
                target_id="claim-7",
                signal_type="SUCCESSFUL_USE",
                magnitude=0.6,
                note="retrieval utility only",
            ),
        ),
    )

    charge = patch.to_dict()["charge_signals"][0]

    assert patch.validate().is_valid
    assert "confidence" not in charge
    assert "evidence_refs" not in charge


def test_shadow_result_changes_status_but_never_applies_patch() -> None:
    patch = LearningPatch(
        provenance=provenance(),
        claims=(ClaimProposal(text="candidate", confidence=0.5),),
    )

    assert patch.with_shadow_result(accepted=True).status is PatchStatus.SHADOW_VALID
    assert patch.with_shadow_result(accepted=False).status is PatchStatus.SHADOW_REJECTED
    assert patch.status is PatchStatus.PROPOSED
    assert not hasattr(patch, "apply")
