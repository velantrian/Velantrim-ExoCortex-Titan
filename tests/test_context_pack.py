from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.context_pack import (
    ContextNoteKind,
    ContextPackBudget,
    ContextPackBudgetExceeded,
    ContextPackBuilder,
    ContextPackError,
    ContextPackWarningCode,
    conservative_token_upper_bound,
)
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
    WorkingMemoryPlan,
)


def _claim(
    *,
    document_id: str,
    raw_text: str,
    text: str,
    start: int,
    modality: ClaimModality = ClaimModality.OBSERVATION,
    qualifiers: tuple[str, ...] = (),
    uncertainties: tuple[str, ...] = (),
    conditions: tuple[str, ...] = (),
    temporal_scope: str | None = None,
    truth_confidence: float | None = None,
) -> CapsuleClaim:
    end = start + len(text)
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=raw_text,
        start_offset=start,
        end_offset=end,
        source_revision="r1",
    )
    return CapsuleClaim.create(
        text=text,
        modality=modality,
        source_spans=(span,),
        extraction_confidence=1.0,
        truth_confidence=truth_confidence,
        qualifiers=qualifiers,
        uncertainties=uncertainties,
        applicability_conditions=conditions,
        temporal_scope=temporal_scope,
    )


def _capsule(
    *,
    document_id: str,
    raw_text: str,
    claims: tuple[CapsuleClaim, ...],
    essence: str | None = None,
) -> KnowledgeCapsule:
    return KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=essence or " ".join(claim.text for claim in claims),
        claims=claims,
        reader_id="test-reader",
        reader_version="1",
        coverage_score=1.0,
        compression_ratio=1.0,
    )


def _full_cost(capsule: KnowledgeCapsule) -> int:
    parts: list[str] = []
    for claim in capsule.claims:
        parts.append(claim.text)
        parts.extend(claim.qualifiers)
        parts.extend(claim.uncertainties)
        parts.extend(claim.applicability_conditions)
        if claim.temporal_scope is not None:
            parts.append(claim.temporal_scope)
    return sum(len(part) for part in parts) + max(0, len(parts) - 1)


def _decision(
    capsule: KnowledgeCapsule,
    disposition: GateDisposition,
    *,
    rank: int | None,
    reasons: tuple[GateReason, ...],
    score: float = 0.9,
    protected: bool = False,
) -> GateDecision:
    full_cost = _full_cost(capsule)
    compressed_cost = len(capsule.essence)
    reserved = 0
    if disposition is GateDisposition.ACTIVE:
        reserved = full_cost
    elif disposition is GateDisposition.COMPRESS:
        reserved = compressed_cost
    return GateDecision(
        capsule_id=capsule.capsule_id,
        disposition=disposition,
        reasons=reasons,
        attention_score=score,
        protected=protected,
        rank=rank,
        full_char_cost=full_cost,
        compressed_char_cost=compressed_cost,
        reserved_chars=reserved,
    )


def _plan(*decisions: GateDecision) -> WorkingMemoryPlan:
    selected = tuple(
        decision
        for decision in decisions
        if decision.disposition
        in {GateDisposition.ACTIVE, GateDisposition.COMPRESS}
    )
    return WorkingMemoryPlan(
        budget=WorkingMemoryBudget(max_items=32, max_chars=100_000),
        decisions=decisions,
        used_items=len(selected),
        used_chars=sum(decision.reserved_chars for decision in selected),
    )


def test_active_claims_evidence_and_structured_notes_are_preserved() -> None:
    raw = "The server may fail during storms."
    claim = _claim(
        document_id="doc-active",
        raw_text=raw,
        text=raw,
        start=0,
        modality=ClaimModality.HYPOTHESIS,
        qualifiers=("according to the operator",),
        uncertainties=("failure frequency is unknown",),
        conditions=("only during severe storms",),
        temporal_scope="future deployments",
        truth_confidence=None,
    )
    capsule = _capsule(
        document_id="doc-active",
        raw_text=raw,
        claims=(claim,),
    )
    plan = _plan(
        _decision(
            capsule,
            GateDisposition.ACTIVE,
            rank=1,
            reasons=(GateReason.FULL_CONTENT_SELECTED,),
        )
    )

    pack = ContextPackBuilder().build(plan, (capsule,))

    assert len(pack.claims) == 1
    packed = pack.claims[0]
    assert packed.text == raw
    assert packed.modality is ClaimModality.HYPOTHESIS
    assert packed.truth_confidence is None
    assert packed.evidence[0].span_id == claim.source_spans[0].span_id
    assert packed.evidence[0].content_hash == claim.source_spans[0].content_hash
    assert {(note.kind, note.text) for note in pack.notes} == {
        (ContextNoteKind.QUALIFIER, "according to the operator"),
        (ContextNoteKind.UNCERTAINTY, "failure frequency is unknown"),
        (
            ContextNoteKind.APPLICABILITY_CONDITION,
            "only during severe storms",
        ),
        (ContextNoteKind.TEMPORAL_SCOPE, "future deployments"),
    }


def test_compressed_capsule_includes_only_complete_essence_claims() -> None:
    raw = "Alpha Beta"
    alpha = _claim(
        document_id="doc-compress",
        raw_text=raw,
        text="Alpha",
        start=0,
    )
    beta = _claim(
        document_id="doc-compress",
        raw_text=raw,
        text="Beta",
        start=6,
    )
    capsule = _capsule(
        document_id="doc-compress",
        raw_text=raw,
        claims=(alpha, beta),
        essence="Alpha",
    )
    plan = _plan(
        _decision(
            capsule,
            GateDisposition.COMPRESS,
            rank=1,
            reasons=(
                GateReason.FULL_CONTENT_OVER_BUDGET,
                GateReason.ESSENCE_SELECTED,
            ),
        )
    )

    pack = ContextPackBuilder().build(plan, (capsule,))

    assert [claim.text for claim in pack.claims] == ["Alpha"]
    assert pack.claims[0].disposition is GateDisposition.COMPRESS
    assert pack.claims[0].evidence[0].start_offset == 0
    assert "Beta" not in pack.to_prompt_json()


def test_ambiguous_compressed_essence_provenance_fails_closed() -> None:
    raw = "Echo Echo"
    first = _claim(
        document_id="doc-ambiguous",
        raw_text=raw,
        text="Echo",
        start=0,
    )
    second = _claim(
        document_id="doc-ambiguous",
        raw_text=raw,
        text="Echo",
        start=5,
    )
    capsule = _capsule(
        document_id="doc-ambiguous",
        raw_text=raw,
        claims=(first, second),
        essence="Echo",
    )
    plan = _plan(
        _decision(
            capsule,
            GateDisposition.COMPRESS,
            rank=1,
            reasons=(
                GateReason.FULL_CONTENT_OVER_BUDGET,
                GateReason.ESSENCE_SELECTED,
            ),
        )
    )

    with pytest.raises(ContextPackError, match="ambiguous"):
        ContextPackBuilder().build(plan, (capsule,))


def test_conflicts_are_pointer_only_and_excluded_content_never_serializes() -> None:
    conflict_text = "Conflicting secret proposition"
    excluded_text = "Restricted secret proposition"
    conflict_claim = _claim(
        document_id="doc-conflict",
        raw_text=conflict_text,
        text=conflict_text,
        start=0,
    )
    excluded_claim = _claim(
        document_id="doc-excluded",
        raw_text=excluded_text,
        text=excluded_text,
        start=0,
    )
    conflict = _capsule(
        document_id="doc-conflict",
        raw_text=conflict_text,
        claims=(conflict_claim,),
    )
    excluded = _capsule(
        document_id="doc-excluded",
        raw_text=excluded_text,
        claims=(excluded_claim,),
    )
    plan = _plan(
        _decision(
            conflict,
            GateDisposition.QUARANTINE,
            rank=None,
            reasons=(GateReason.CONFLICT,),
        ),
        _decision(
            excluded,
            GateDisposition.EXCLUDE,
            rank=None,
            reasons=(GateReason.RESTRICTED,),
        ),
    )

    pack = ContextPackBuilder().build(plan, (excluded, conflict))
    payload = pack.to_prompt_json()

    assert len(pack.conflicts) == 1
    assert pack.conflicts[0].capsule_id == conflict.capsule_id
    assert conflict_text not in payload
    assert excluded_text not in payload
    assert excluded.capsule_id not in payload
    assert pack.excluded_count == 1


def test_deferred_pointer_omission_is_explicit_and_ranked() -> None:
    capsules: list[KnowledgeCapsule] = []
    decisions: list[GateDecision] = []
    for index in range(3):
        text = f"Deferred {index}"
        capsule = _capsule(
            document_id=f"doc-deferred-{index}",
            raw_text=text,
            claims=(
                _claim(
                    document_id=f"doc-deferred-{index}",
                    raw_text=text,
                    text=text,
                    start=0,
                ),
            ),
        )
        capsules.append(capsule)
        decisions.append(
            _decision(
                capsule,
                GateDisposition.DEFER,
                rank=index + 1,
                reasons=(GateReason.ITEM_BUDGET_EXHAUSTED,),
                score=0.3,
            )
        )

    pack = ContextPackBuilder().build(
        _plan(*decisions),
        tuple(reversed(capsules)),
        budget=ContextPackBudget(
            max_tokens=16_384,
            max_deferred_pointers=1,
        ),
    )

    assert len(pack.deferred) == 1
    assert pack.deferred[0].rank == 1
    assert pack.deferred_total == 3
    assert len(pack.warnings) == 1
    assert (
        pack.warnings[0].code
        is ContextPackWarningCode.DEFERRED_POINTERS_OMITTED
    )
    assert pack.warnings[0].omitted_count == 2


def test_mandatory_selected_payload_overflow_fails_closed() -> None:
    raw = "A mandatory source-linked claim."
    capsule = _capsule(
        document_id="doc-budget",
        raw_text=raw,
        claims=(
            _claim(
                document_id="doc-budget",
                raw_text=raw,
                text=raw,
                start=0,
            ),
        ),
    )
    plan = _plan(
        _decision(
            capsule,
            GateDisposition.ACTIVE,
            rank=1,
            reasons=(GateReason.FULL_CONTENT_SELECTED,),
        )
    )

    with pytest.raises(ContextPackBudgetExceeded):
        ContextPackBuilder().build(
            plan,
            (capsule,),
            budget=ContextPackBudget(max_tokens=64),
        )


def test_pack_is_deterministic_and_valid_json_under_budget() -> None:
    raw_a = "Alpha"
    raw_b = "Beta"
    alpha = _capsule(
        document_id="doc-a",
        raw_text=raw_a,
        claims=(
            _claim(
                document_id="doc-a",
                raw_text=raw_a,
                text=raw_a,
                start=0,
            ),
        ),
    )
    beta = _capsule(
        document_id="doc-b",
        raw_text=raw_b,
        claims=(
            _claim(
                document_id="doc-b",
                raw_text=raw_b,
                text=raw_b,
                start=0,
            ),
        ),
    )
    plan = _plan(
        _decision(
            beta,
            GateDisposition.ACTIVE,
            rank=2,
            reasons=(GateReason.FULL_CONTENT_SELECTED,),
        ),
        _decision(
            alpha,
            GateDisposition.ACTIVE,
            rank=1,
            reasons=(GateReason.FULL_CONTENT_SELECTED,),
        ),
    )
    budget = ContextPackBudget(max_tokens=16_384)

    first = ContextPackBuilder().build(plan, (alpha, beta), budget=budget)
    second = ContextPackBuilder().build(plan, (beta, alpha), budget=budget)

    assert first.pack_id == second.pack_id
    assert first.to_prompt_json() == second.to_prompt_json()
    assert [claim.text for claim in first.claims] == ["Alpha", "Beta"]
    assert json.loads(first.to_prompt_json())["pack_id"] == first.pack_id
    assert first.token_cost == conservative_token_upper_bound(
        first.to_prompt_json()
    )
    assert first.token_cost <= first.max_tokens


def test_plan_capsule_mismatch_and_duplicate_capsules_fail_closed() -> None:
    raw = "Alpha"
    capsule = _capsule(
        document_id="doc-mismatch",
        raw_text=raw,
        claims=(
            _claim(
                document_id="doc-mismatch",
                raw_text=raw,
                text=raw,
                start=0,
            ),
        ),
    )
    plan = _plan(
        _decision(
            capsule,
            GateDisposition.ACTIVE,
            rank=1,
            reasons=(GateReason.FULL_CONTENT_SELECTED,),
        )
    )

    with pytest.raises(ContextPackError, match="mismatch"):
        ContextPackBuilder().build(plan, ())
    with pytest.raises(ContextPackError, match="duplicate capsule_id"):
        ContextPackBuilder().build(plan, (capsule, capsule))


def test_context_pack_module_has_no_authority_or_remote_imports() -> None:
    module_path = Path("core/context_pack.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
    banned_fragments = {
        "sqlite",
        "persistence",
        "truth_gate",
        "esm",
        "llm_router",
        "remote_egress",
        "httpx",
        "requests",
        "server",
        "api",
    }

    assert not any(
        fragment in imported_name.lower()
        for imported_name in imported
        for fragment in banned_fragments
    )
