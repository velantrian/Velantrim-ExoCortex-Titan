"""Tests for the typed continuity-to-WorkingMemoryGate adapter."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.context_pack import ContextNoteKind, ContextPackBudget, ContextPackBuilder
from core.continuity import (
    ContinuityAdapterOmissionReason,
    ContinuityContextAssembler,
    ContinuityContextItem,
    ContinuityContextPack,
    ContinuityItemGatePolicy,
    ContinuityItemKind,
    ContinuityUncertainty,
    ContinuityWorkingMemoryAdapter,
    ContinuityWorkingMemoryAdapterError,
    ConversationEpisode,
    ThreadWeaver,
)
from core.conversation_consolidation import ConversationNotebook
from core.knowledge_capsule import ClaimModality
from core.working_memory_gate import (
    GateDisposition,
    GateReason,
    WorkingMemoryBudget,
    WorkingMemoryGate,
)


def _episode(
    chat_id: str,
    *,
    goal: str,
    topic: str = "Titan continuity",
    insights: list[str] | None = None,
    conclusion: str = "Keep the projection deterministic",
    related: list[str] | None = None,
    created_at: str = "2026-08-01T10:00:00+00:00",
    finalized_at: str | None = "2026-08-01T11:00:00+00:00",
) -> ConversationEpisode:
    return ConversationEpisode.from_notebook(
        ConversationNotebook(
            chat_id=chat_id,
            main_topic=topic,
            user_goal=goal,
            key_insights=insights or ["Preserve provenance"],
            conclusion=conclusion,
            related_chats=related or [],
            facts_count=2,
            messages_count=5,
            produced_gist=finalized_at is not None,
            created_at=created_at,
            finalized_at=finalized_at,
        )
    )


def _continuity_pack() -> tuple[
    ContinuityContextPack,
    ConversationEpisode,
    ConversationEpisode,
]:
    older = _episode(
        "chat:older",
        goal="Finish the MVP first",
        insights=["Preserve provenance", "Do not create a second ACM"],
        conclusion="Defer the new architecture layer",
    )
    current = _episode(
        "chat:current",
        goal="Add another architecture layer",
        related=["chat:older"],
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    episodes = [older, current]
    weave = ThreadWeaver().weave(episodes)
    result = ContinuityContextAssembler().assemble(
        request_ref="request:working-memory-adapter",
        current_episode=current,
        episodes=episodes,
        weave_result=weave,
    )
    return result.pack, older, current


def _policies(
    pack: ContinuityContextPack,
    *,
    attention_score: float = 0.9,
    recall_allowed: bool = True,
    eligible: bool = True,
    restricted: bool = False,
    erased: bool = False,
    protected: bool = False,
    conflict: bool = False,
) -> tuple[ContinuityItemGatePolicy, ...]:
    return tuple(
        ContinuityItemGatePolicy(
            item_id=item.item_id,
            attention_score=attention_score,
            recall_allowed=recall_allowed,
            eligible=eligible,
            restricted=restricted,
            erased=erased,
            protected=protected,
            conflict=conflict,
        )
        for item in pack.items
        if item.kind is not ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE
    )


def test_adapter_builds_exact_source_capsules_without_truth_upgrade() -> None:
    pack, older, current = _continuity_pack()

    batch = ContinuityWorkingMemoryAdapter().adapt(
        pack,
        episodes=[current, older],
        policies=reversed(_policies(pack)),
    )

    assert len(batch.candidates) == len(pack.items)
    assert len(batch.bindings) == len(pack.items)
    assert batch.omissions == ()
    assert tuple(
        candidate.metadata["continuity_item_id"]
        for candidate in batch.candidates
    ) == tuple(binding.item_id for binding in batch.bindings)

    items_by_id = {item.item_id: item for item in pack.items}
    for candidate, binding in zip(batch.candidates, batch.bindings, strict=True):
        item = items_by_id[binding.item_id]
        capsule = candidate.capsule
        assert capsule.created_at == older.finalized_at
        assert capsule.source_document_id == binding.virtual_document_id
        assert item.source_ref in capsule.source_document_id
        assert len(capsule.claims) == 1
        claim = capsule.claims[0]
        assert claim.text == item.text
        assert claim.extraction_confidence == 1.0
        assert claim.truth_confidence is None
        assert claim.uncertainties == tuple(
            code.value for code in item.uncertainty_codes
        )
        assert claim.source_spans[0].span_id == binding.source_span_id
        assert claim.source_spans[0].verify(item.text)
        expected_modality = (
            ClaimModality.GOAL
            if item.kind is ContinuityItemKind.PRIOR_GOAL_TEXT
            else ClaimModality.INTERPRETATION
        )
        assert claim.modality is expected_modality


def test_adapter_is_order_independent_and_replay_stable() -> None:
    pack, older, current = _continuity_pack()
    policies = _policies(pack)
    adapter = ContinuityWorkingMemoryAdapter()

    forward = adapter.adapt(pack, [older, current], policies)
    reverse = adapter.adapt(pack, [current, older], reversed(policies))

    assert tuple(item.capsule.capsule_id for item in forward.candidates) == tuple(
        item.capsule.capsule_id for item in reverse.candidates
    )
    assert forward.bindings == reverse.bindings
    assert forward.capsules == reverse.capsules

    gate = WorkingMemoryGate()
    budget = WorkingMemoryBudget(max_items=16, max_chars=20_000)
    forward_plan = gate.plan(forward.candidates, budget=budget)
    reverse_plan = gate.plan(reverse.candidates, budget=budget)
    assert forward_plan.to_dict() == reverse_plan.to_dict()


def test_real_gate_and_context_pack_preserve_uncertainty_and_provenance() -> None:
    pack, older, current = _continuity_pack()
    batch = ContinuityWorkingMemoryAdapter().adapt(
        pack,
        [older, current],
        _policies(pack),
    )
    plan = WorkingMemoryGate().plan(
        batch.candidates,
        budget=WorkingMemoryBudget(max_items=16, max_chars=20_000),
    )
    final_pack = ContextPackBuilder().build(
        plan,
        batch.capsules,
        budget=ContextPackBudget(max_tokens=100_000),
    )

    assert len(plan.active) == len(batch.candidates)
    assert len(final_pack.claims) == len(batch.candidates)
    assert all(claim.truth_confidence is None for claim in final_pack.claims)
    assert all(
        claim.disposition is GateDisposition.ACTIVE
        for claim in final_pack.claims
    )
    uncertainty_notes = tuple(
        note for note in final_pack.notes if note.kind is ContextNoteKind.UNCERTAINTY
    )
    assert uncertainty_notes
    assert {
        note.text for note in uncertainty_notes
    } >= {
        ContinuityUncertainty.CURRENTNESS_UNCONFIRMED.value,
        ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION.value,
    }
    bound_documents = {binding.virtual_document_id for binding in batch.bindings}
    assert {
        evidence.document_id
        for claim in final_pack.claims
        for evidence in claim.evidence
    } == bound_documents


def test_adapter_requires_exact_policy_coverage() -> None:
    pack, older, current = _continuity_pack()
    policies = _policies(pack)

    with pytest.raises(
        ContinuityWorkingMemoryAdapterError,
        match="policy/item mismatch",
    ):
        ContinuityWorkingMemoryAdapter().adapt(
            pack,
            [older, current],
            policies[:-1],
        )

    unexpected = ContinuityItemGatePolicy(
        item_id="unexpected:item",
        attention_score=0.5,
        recall_allowed=True,
        eligible=True,
        restricted=False,
        erased=False,
        protected=False,
        conflict=False,
    )
    with pytest.raises(
        ContinuityWorkingMemoryAdapterError,
        match="policy/item mismatch",
    ):
        ContinuityWorkingMemoryAdapter().adapt(
            pack,
            [older, current],
            (*policies, unexpected),
        )


def test_adapter_fails_closed_when_item_is_not_exact_episode_content() -> None:
    pack, older, current = _continuity_pack()
    original = next(
        item
        for item in pack.items
        if item.kind is ContinuityItemKind.PRIOR_GOAL_TEXT
    )
    forged = ContinuityContextItem.create(
        kind=original.kind,
        source_episode_id=original.source_episode_id,
        source_ref=original.source_ref,
        text="A goal that was never present in the episode",
        uncertainty_codes=original.uncertainty_codes,
    )
    forged_pack = ContinuityContextPack.create(
        request_ref=pack.request_ref,
        current_episode_id=pack.current_episode_id,
        thread_id=pack.thread_id,
        episode_ids=pack.episode_ids,
        link_ids=pack.link_ids,
        unresolved_reference_ids=pack.unresolved_reference_ids,
        items=(
            forged,
            *(item for item in pack.items if item.item_id != original.item_id),
        ),
        policy_version=pack.policy_version,
    )

    with pytest.raises(
        ContinuityWorkingMemoryAdapterError,
        match="not exact content",
    ):
        ContinuityWorkingMemoryAdapter().adapt(
            forged_pack,
            [older, current],
            _policies(forged_pack),
        )


def test_unresolved_reference_is_omitted_before_semantic_gate() -> None:
    current = _episode(
        "chat:current",
        goal="Continue the missing chat",
        related=["chat:not-loaded"],
    )
    weave = ThreadWeaver().weave([current])
    result = ContinuityContextAssembler().assemble(
        request_ref="request:unresolved-adapter",
        current_episode=current,
        episodes=[current],
        weave_result=weave,
    )

    batch = ContinuityWorkingMemoryAdapter().adapt(
        result.pack,
        [current],
        policies=(),
    )

    assert batch.candidates == ()
    assert batch.bindings == ()
    assert len(batch.omissions) == 1
    assert batch.omissions[0].reason is (
        ContinuityAdapterOmissionReason.
        UNRESOLVED_REFERENCE_NOT_SEMANTIC_CONTENT
    )


def test_restriction_policy_is_passed_to_existing_gate_without_bypass() -> None:
    pack, older, current = _continuity_pack()
    batch = ContinuityWorkingMemoryAdapter().adapt(
        pack,
        [older, current],
        _policies(pack, restricted=True),
    )

    plan = WorkingMemoryGate().plan(batch.candidates)

    assert len(plan.excluded) == len(batch.candidates)
    assert all(
        GateReason.RESTRICTED in decision.reasons
        for decision in plan.excluded
    )
    assert plan.active == ()
    assert plan.compressed == ()


def test_uncertainty_metadata_cannot_be_dropped_by_compression() -> None:
    older = _episode("chat:older", goal="Finish the MVP first")
    current = _episode(
        "chat:current",
        goal="Do something else",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    item = ContinuityContextItem.create(
        kind=ContinuityItemKind.PRIOR_GOAL_TEXT,
        source_episode_id=older.episode_id,
        source_ref=older.source_ref,
        text=older.user_goal,
        uncertainty_codes=(
            ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION,
            ContinuityUncertainty.CURRENTNESS_UNCONFIRMED,
        ),
    )
    pack = ContinuityContextPack.create(
        request_ref="request:no-lossy-compression",
        current_episode_id=current.episode_id,
        thread_id=None,
        episode_ids=(older.episode_id,),
        link_ids=(),
        unresolved_reference_ids=(),
        items=(item,),
    )
    batch = ContinuityWorkingMemoryAdapter().adapt(
        pack,
        [older],
        _policies(pack),
    )

    plan = WorkingMemoryGate().plan(
        batch.candidates,
        budget=WorkingMemoryBudget(
            max_items=1,
            max_chars=len(item.text),
        ),
    )

    assert len(plan.deferred) == 1
    assert GateReason.COMPRESSED_SEMANTICS_UNSUPPORTED in plan.deferred[0].reasons
    assert plan.compressed == ()


def test_adapter_output_is_immutable_and_has_no_execution_authority() -> None:
    pack, older, current = _continuity_pack()
    batch = ContinuityWorkingMemoryAdapter().adapt(
        pack,
        [older, current],
        _policies(pack),
    )

    with pytest.raises(FrozenInstanceError):
        batch.source_pack_id = "mutated"  # type: ignore[misc]

    for forbidden in (
        "write_canon",
        "promote",
        "execute",
        "advice",
        "action_decision",
        "final_context_pack",
    ):
        assert not hasattr(batch, forbidden)
