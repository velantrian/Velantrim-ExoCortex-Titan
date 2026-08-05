"""Tests for the shadow continuity context projection and receipt."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.continuity import (
    ContinuityContextAssembler,
    ContinuityContextError,
    ContinuityDecisionSubject,
    ContinuityDisposition,
    ContinuityItemKind,
    ContinuityReason,
    ContinuityUncertainty,
    ConversationEpisode,
    ThreadWeaver,
)
from core.conversation_consolidation import ConversationNotebook


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


def _assemble(
    current: ConversationEpisode,
    episodes: list[ConversationEpisode],
    *,
    limit: int = 8,
):
    weave = ThreadWeaver().weave(episodes)
    return ContinuityContextAssembler().assemble(
        request_ref="request:continuity-demo",
        current_episode=current,
        episodes=episodes,
        weave_result=weave,
        max_prior_episodes=limit,
    )


def _decision_for(result, subject_ref: str):
    return next(
        decision
        for decision in result.receipt.decisions
        if decision.subject_ref == subject_ref
    )


def test_explicit_thread_builds_source_linked_prior_items_and_receipt() -> None:
    older = _episode(
        "chat:older",
        goal="Finish the MVP first",
        conclusion="Defer the new architecture layer",
    )
    current = _episode(
        "chat:current",
        goal="Add another architecture layer",
        related=["chat:older"],
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )

    result = _assemble(current, [older, current])

    assert result.pack.thread_id is not None
    assert result.pack.episode_ids == (older.episode_id,)
    assert len(result.pack.link_ids) == 1
    assert {item.kind for item in result.pack.items} == {
        ContinuityItemKind.PRIOR_GOAL_TEXT,
        ContinuityItemKind.PRIOR_TOPIC_TEXT,
        ContinuityItemKind.PRIOR_INSIGHT_TEXT,
        ContinuityItemKind.PRIOR_CONCLUSION_TEXT,
    }
    assert all(item.source_episode_id == older.episode_id for item in result.pack.items)
    assert all(
        ContinuityUncertainty.CURRENTNESS_UNCONFIRMED
        in item.uncertainty_codes
        for item in result.pack.items
    )
    assert all(
        ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION
        in item.uncertainty_codes
        for item in result.pack.items
    )

    older_decision = _decision_for(result, older.episode_id)
    assert older_decision.disposition is ContinuityDisposition.INCLUDED
    assert ContinuityReason.EXPLICIT_LINK_PRESENT in older_decision.reason_codes
    assert ContinuityReason.PRIOR_TO_CURRENT in older_decision.reason_codes

    current_decision = _decision_for(result, current.episode_id)
    assert current_decision.disposition is ContinuityDisposition.EXCLUDED
    assert current_decision.reason_codes == (ContinuityReason.CURRENT_EPISODE,)
    assert result.receipt.pack_id == result.pack.pack_id


def test_input_order_does_not_change_pack_or_receipt_identity() -> None:
    older = _episode("chat:older", goal="Ship the MVP")
    current = _episode(
        "chat:current",
        goal="Ship the MVP",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )

    forward = _assemble(current, [older, current])
    reverse = _assemble(current, [current, older])

    assert forward.pack.pack_id == reverse.pack.pack_id
    assert forward.pack.canonical_bytes() == reverse.pack.canonical_bytes()
    assert forward.receipt.receipt_id == reverse.receipt.receipt_id


def test_unrelated_episodes_are_excluded_and_pack_remains_empty() -> None:
    unrelated = _episode("chat:unrelated", goal="Plan another project")
    current = _episode(
        "chat:current",
        goal="Continue Titan",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )

    result = _assemble(current, [unrelated, current])

    assert result.pack.thread_id is None
    assert result.pack.episode_ids == ()
    assert result.pack.items == ()
    unrelated_decision = _decision_for(result, unrelated.episode_id)
    assert unrelated_decision.disposition is ContinuityDisposition.EXCLUDED
    assert unrelated_decision.reason_codes == (
        ContinuityReason.NOT_IN_CURRENT_THREAD,
    )


def test_future_episode_is_never_loaded_as_prior_context() -> None:
    older = _episode("chat:older", goal="Shared goal")
    current = _episode(
        "chat:current",
        goal="Shared goal",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    future = _episode(
        "chat:future",
        goal="Shared goal",
        created_at="2026-08-03T10:00:00+00:00",
        finalized_at="2026-08-03T11:00:00+00:00",
    )

    result = _assemble(current, [future, current, older])

    assert result.pack.episode_ids == (older.episode_id,)
    future_decision = _decision_for(result, future.episode_id)
    assert future_decision.disposition is ContinuityDisposition.EXCLUDED
    assert future_decision.reason_codes == (ContinuityReason.AFTER_CURRENT,)


def test_local_limit_keeps_newest_prior_episode_and_receipts_exclusion() -> None:
    first = _episode("chat:first", goal="Shared goal")
    second = _episode(
        "chat:second",
        goal="Shared goal",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    current = _episode(
        "chat:current",
        goal="Shared goal",
        created_at="2026-08-03T10:00:00+00:00",
        finalized_at="2026-08-03T11:00:00+00:00",
    )

    result = _assemble(current, [current, first, second], limit=1)

    assert result.pack.episode_ids == (second.episode_id,)
    first_decision = _decision_for(result, first.episode_id)
    assert first_decision.disposition is ContinuityDisposition.EXCLUDED
    assert first_decision.reason_codes == (ContinuityReason.LOCAL_SAFETY_LIMIT,)


def test_unresolved_explicit_reference_is_preserved_with_uncertainty() -> None:
    current = _episode(
        "chat:current",
        goal="Continue a prior chat",
        related=["chat:not-loaded"],
    )

    result = _assemble(current, [current])

    assert len(result.pack.unresolved_reference_ids) == 1
    assert len(result.pack.items) == 1
    item = result.pack.items[0]
    assert item.kind is ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE
    assert item.text == "chat:not-loaded"
    assert ContinuityUncertainty.TARGET_NOT_LOADED in item.uncertainty_codes

    decision = next(
        value
        for value in result.receipt.decisions
        if value.subject_kind is ContinuityDecisionSubject.UNRESOLVED_REFERENCE
    )
    assert decision.disposition is ContinuityDisposition.INCLUDED
    assert decision.reason_codes == (
        ContinuityReason.UNRESOLVED_EXPLICIT_REFERENCE,
    )


def test_current_episode_must_be_present_in_input() -> None:
    current = _episode("chat:current", goal="Current goal")
    other = _episode("chat:other", goal="Other goal")
    weave = ThreadWeaver().weave([other])

    with pytest.raises(ContinuityContextError, match="current_episode must match"):
        ContinuityContextAssembler().assemble(
            request_ref="request:missing-current",
            current_episode=current,
            episodes=[other],
            weave_result=weave,
        )


def test_conflicting_snapshots_for_one_chat_fail_closed() -> None:
    first = _episode("chat:same", goal="First goal")
    conflicting = _episode("chat:same", goal="Second goal")
    weave = ThreadWeaver().weave([first])

    with pytest.raises(ContinuityContextError, match="conflicting snapshots"):
        ContinuityContextAssembler().assemble(
            request_ref="request:conflict",
            current_episode=first,
            episodes=[first, conflicting],
            weave_result=weave,
        )


def test_projection_is_immutable_and_not_a_final_prompt_pack() -> None:
    older = _episode("chat:older", goal="Ship the MVP")
    current = _episode(
        "chat:current",
        goal="Ship the MVP",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    result = _assemble(current, [older, current])

    with pytest.raises(FrozenInstanceError):
        result.pack.pack_id = "mutated"  # type: ignore[misc]

    for forbidden in (
        "claims",
        "max_tokens",
        "attention_score",
        "truth_status",
        "epistemic_status",
        "advice",
        "action_decision",
    ):
        assert not hasattr(result.pack, forbidden)
