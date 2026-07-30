from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path

import pytest

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import (
    GateDecision,
    GateDisposition,
    GateReason,
    WorkingMemoryBudget,
    WorkingMemoryCandidate,
    WorkingMemoryGate,
)


def _capsule(
    *claim_texts: str,
    essence: str | None = None,
    document_id: str | None = None,
) -> KnowledgeCapsule:
    raw_text = " ".join(claim_texts)
    resolved_document_id = document_id or (
        "doc-" + sha256(raw_text.encode("utf-8")).hexdigest()[:12]
    )
    claims: list[CapsuleClaim] = []
    cursor = 0
    for text in claim_texts:
        start = raw_text.index(text, cursor)
        end = start + len(text)
        span = SourceSpan.from_text(
            document_id=resolved_document_id,
            raw_text=raw_text,
            start_offset=start,
            end_offset=end,
        )
        claims.append(
            CapsuleClaim.create(
                text=text,
                modality=ClaimModality.OBSERVATION,
                source_spans=(span,),
                extraction_confidence=1.0,
            )
        )
        cursor = end
    return KnowledgeCapsule.create(
        source_document_id=resolved_document_id,
        essence=essence or claim_texts[0],
        claims=claims,
        reader_id="test.reader",
        reader_version="1",
    )


def _policy(**flags: bool) -> dict[str, bool]:
    result = {
        "recall_allowed": True,
        "eligible": True,
        "restricted": False,
        "erased": False,
        "protected": False,
        "conflict": False,
    }
    result.update(flags)
    return result


def _candidate(
    text: str,
    *,
    score: float = 1.0,
    essence: str | None = None,
    **flags: bool,
) -> WorkingMemoryCandidate:
    return WorkingMemoryCandidate(
        capsule=_capsule(text, essence=essence),
        attention_score=score,
        **_policy(**flags),
    )


def _candidate_with_claims(
    *claim_texts: str,
    score: float = 1.0,
    essence: str,
    **flags: bool,
) -> WorkingMemoryCandidate:
    return WorkingMemoryCandidate(
        capsule=_capsule(*claim_texts, essence=essence),
        attention_score=score,
        **_policy(**flags),
    )


def _candidate_from_capsule(
    capsule: KnowledgeCapsule, *, score: float
) -> WorkingMemoryCandidate:
    return WorkingMemoryCandidate(
        capsule=capsule,
        attention_score=score,
        **_policy(),
    )


def _decision(plan, candidate: WorkingMemoryCandidate):
    return next(
        item
        for item in plan.decisions
        if item.capsule_id == candidate.capsule.capsule_id
    )


def test_equal_cost_compress_decision_is_rejected() -> None:
    with pytest.raises(ValueError, match="smaller essence"):
        GateDecision(
            capsule_id="capsule-equal-cost",
            disposition=GateDisposition.COMPRESS,
            reasons=(GateReason.ESSENCE_SELECTED,),
            attention_score=1.0,
            protected=False,
            rank=1,
            full_char_cost=5,
            compressed_char_cost=5,
            reserved_chars=5,
        )


def test_delete_is_not_a_disposition() -> None:
    assert "delete" not in {item.value for item in GateDisposition}
    assert set(GateDisposition) == {
        GateDisposition.ACTIVE,
        GateDisposition.COMPRESS,
        GateDisposition.DEFER,
        GateDisposition.QUARANTINE,
        GateDisposition.EXCLUDE,
    }


def test_every_candidate_receives_exactly_one_decision() -> None:
    candidates = [
        _candidate("active"),
        _candidate("deferred", score=0.0),
        _candidate("conflict", conflict=True),
        _candidate("restricted", restricted=True),
    ]
    plan = WorkingMemoryGate().plan(candidates)

    assert len(plan.decisions) == len(candidates)
    assert len({item.capsule_id for item in plan.decisions}) == len(candidates)


def test_erased_and_restricted_override_protection_and_score() -> None:
    candidate = _candidate(
        "sensitive", score=1.0, erased=True, restricted=True, protected=True
    )
    plan = WorkingMemoryGate().plan([candidate])
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.EXCLUDE
    assert decision.reasons == (GateReason.ERASED, GateReason.RESTRICTED)
    assert decision.reserved_chars == 0
    assert plan.used_items == 0
    assert plan.used_chars == 0


def test_recall_denied_and_ineligible_are_excluded() -> None:
    candidate = _candidate(
        "not recallable", recall_allowed=False, eligible=False, protected=True
    )
    decision = _decision(WorkingMemoryGate().plan([candidate]), candidate)

    assert decision.disposition is GateDisposition.EXCLUDE
    assert GateReason.RECALL_DENIED in decision.reasons
    assert GateReason.INELIGIBLE in decision.reasons


def test_conflict_is_quarantined_without_consuming_budget() -> None:
    candidate = _candidate("conflicting claim", conflict=True)
    plan = WorkingMemoryGate().plan([candidate])
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.QUARANTINE
    assert decision.reasons == (GateReason.CONFLICT,)
    assert plan.used_items == 0
    assert plan.used_chars == 0


def test_complete_claim_content_becomes_active_when_it_fits() -> None:
    candidate = _candidate("complete claim", score=0.9)
    budget = WorkingMemoryBudget(max_items=1, max_chars=len("complete claim"))
    plan = WorkingMemoryGate().plan([candidate], budget=budget)
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.ACTIVE
    assert decision.reserved_chars == len("complete claim")
    assert GateReason.FULL_CONTENT_SELECTED in decision.reasons


def test_source_linked_complete_claim_essence_is_used_under_budget_pressure() -> None:
    first = "first complete claim"
    second = "second complete claim"
    candidate = _candidate_with_claims(first, second, essence=first)
    budget = WorkingMemoryBudget(max_items=1, max_chars=len(first))
    plan = WorkingMemoryGate().plan([candidate], budget=budget)
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.COMPRESS
    assert decision.reserved_chars == len(first)
    assert GateReason.FULL_CONTENT_OVER_BUDGET in decision.reasons
    assert GateReason.ESSENCE_SELECTED in decision.reasons


def test_free_summary_prose_cannot_be_used_for_compression() -> None:
    candidate = _candidate("a much longer complete claim", essence="short")
    plan = WorkingMemoryGate().plan(
        [candidate], budget=WorkingMemoryBudget(max_items=1, max_chars=len("short"))
    )
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.DEFER
    assert GateReason.FULL_CONTENT_OVER_BUDGET in decision.reasons
    assert GateReason.ESSENCE_NOT_SOURCE_LINKED in decision.reasons
    assert decision.reserved_chars == 0


def test_neither_representation_is_truncated_when_budget_is_too_small() -> None:
    first = "first complete claim"
    second = "second complete claim"
    candidate = _candidate_with_claims(first, second, essence=first)
    plan = WorkingMemoryGate().plan(
        [candidate], budget=WorkingMemoryBudget(max_items=1, max_chars=3)
    )
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.DEFER
    assert decision.reserved_chars == 0
    assert GateReason.CHAR_BUDGET_EXHAUSTED in decision.reasons


def test_item_budget_exhaustion_defers_lower_ranked_candidate() -> None:
    first = _candidate("high score", score=0.9)
    second = _candidate("lower score", score=0.8)
    plan = WorkingMemoryGate().plan(
        [second, first], budget=WorkingMemoryBudget(max_items=1, max_chars=100)
    )

    assert _decision(plan, first).disposition is GateDisposition.ACTIVE
    second_decision = _decision(plan, second)
    assert second_decision.disposition is GateDisposition.DEFER
    assert GateReason.ITEM_BUDGET_EXHAUSTED in second_decision.reasons


def test_protection_changes_order_and_selection_but_cannot_change_safety() -> None:
    protected = _candidate("protected low score", score=0.0, protected=True)
    ordinary = _candidate("ordinary high score", score=1.0)
    excluded = _candidate(
        "protected erased", score=1.0, protected=True, erased=True
    )
    plan = WorkingMemoryGate().plan(
        [ordinary, excluded, protected],
        budget=WorkingMemoryBudget(max_items=1, max_chars=100),
    )

    assert _decision(plan, protected).disposition is GateDisposition.ACTIVE
    assert GateReason.PROTECTED in _decision(plan, protected).reasons
    assert _decision(plan, ordinary).disposition is GateDisposition.DEFER
    assert _decision(plan, excluded).disposition is GateDisposition.EXCLUDE


def test_score_below_active_can_compress_only_under_real_budget_pressure() -> None:
    first = "first complete claim"
    second = "second complete claim"
    candidate = _candidate_with_claims(
        first, second, score=0.4, essence=first
    )
    plan = WorkingMemoryGate().plan(
        [candidate],
        budget=WorkingMemoryBudget(max_items=1, max_chars=len(first)),
    )
    decision = _decision(plan, candidate)

    assert decision.disposition is GateDisposition.COMPRESS
    assert GateReason.SCORE_BELOW_ACTIVE in decision.reasons
    assert GateReason.FULL_CONTENT_OVER_BUDGET in decision.reasons
    assert GateReason.ESSENCE_SELECTED in decision.reasons


def test_score_below_active_does_not_compress_when_full_content_fits() -> None:
    candidate = _candidate("complete text", score=0.4)
    decision = _decision(WorkingMemoryGate().plan([candidate]), candidate)

    assert decision.disposition is GateDisposition.DEFER
    assert decision.reasons == (GateReason.SCORE_BELOW_ACTIVE,)


def test_score_below_compress_is_deferred_even_when_space_exists() -> None:
    candidate = _candidate("complete text", score=0.1)
    decision = _decision(WorkingMemoryGate().plan([candidate]), candidate)

    assert decision.disposition is GateDisposition.DEFER
    assert GateReason.SCORE_BELOW_COMPRESS in decision.reasons


def test_duplicate_capsule_ids_fail_closed() -> None:
    capsule = _capsule("same capsule")
    first = _candidate_from_capsule(capsule, score=0.9)
    second = _candidate_from_capsule(capsule, score=0.8)

    with pytest.raises(ValueError, match="duplicate capsule_id"):
        WorkingMemoryGate().plan([first, second])


def test_shuffled_input_produces_identical_plan() -> None:
    candidates = [
        _candidate("one", score=0.9),
        _candidate("two", score=0.4),
        _candidate("three", score=0.1),
        _candidate("four", conflict=True),
    ]
    gate = WorkingMemoryGate()
    budget = WorkingMemoryBudget(max_items=2, max_chars=20)

    forward = gate.plan(candidates, budget=budget)
    reverse = gate.plan(reversed(candidates), budget=budget)

    assert forward == reverse
    assert forward.to_dict() == reverse.to_dict()


def test_tie_score_uses_stable_capsule_identity() -> None:
    first = _candidate("alpha", score=0.8)
    second = _candidate("beta", score=0.8)
    plan = WorkingMemoryGate().plan(
        [second, first], budget=WorkingMemoryBudget(max_items=1, max_chars=100)
    )
    expected = min((first, second), key=lambda item: item.capsule.capsule_id)
    other = second if expected is first else first

    assert _decision(plan, expected).rank == 1
    assert _decision(plan, expected).disposition is GateDisposition.ACTIVE
    assert _decision(plan, other).disposition is GateDisposition.DEFER


def test_policy_markers_are_required_fail_closed_inputs() -> None:
    with pytest.raises(TypeError):
        WorkingMemoryCandidate(  # type: ignore[call-arg]
            capsule=_capsule("claim"), attention_score=1.0
        )


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -0.1, 1.1, True])
def test_invalid_attention_scores_fail_closed(score: float) -> None:
    with pytest.raises(ValueError, match="attention_score"):
        _candidate_from_capsule(_capsule("claim"), score=score)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_items": 0}, "max_items"),
        ({"max_items": True}, "max_items"),
        ({"max_chars": 0}, "max_chars"),
        ({"max_chars": True}, "max_chars"),
    ],
)
def test_invalid_budgets_fail_closed(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        WorkingMemoryBudget(**kwargs)


@pytest.mark.parametrize("invalid", [False, 0, object()])
def test_plan_rejects_non_budget_values_instead_of_using_defaults(invalid: object) -> None:
    with pytest.raises(ValueError, match="budget must"):
        WorkingMemoryGate().plan([], budget=invalid)  # type: ignore[arg-type]


def test_invalid_threshold_order_fails_closed() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        WorkingMemoryGate(min_active_score=0.2, min_compress_score=0.3)


def test_capsules_are_not_mutated() -> None:
    capsule = _capsule("immutable claim")
    before = capsule
    candidate = _candidate_from_capsule(capsule, score=1.0)

    WorkingMemoryGate().plan([candidate])

    assert candidate.capsule is before
    assert candidate.capsule == before


def test_module_has_no_authority_or_transport_imports() -> None:
    path = Path(__file__).parents[1] / "core" / "working_memory_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = {
        "sqlite3",
        "core.memory",
        "core.working_memory",
        "core.truth_gate",
        "core.truth_policy",
        "core.write_gate",
        "core.esm",
        "core.llm_router",
        "core.remote_egress",
    }
    assert imported.isdisjoint(forbidden)
    assert not any(
        name.startswith("http") or name.startswith("requests") for name in imported
    )
