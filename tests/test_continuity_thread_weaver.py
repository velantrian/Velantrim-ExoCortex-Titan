"""Tests for the deterministic continuity thread weaver."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.continuity import ConversationEpisode
from core.continuity.thread_weaver import (
    ContinuityThread,
    ThreadLinkStrength,
    ThreadRelation,
    ThreadSignal,
    ThreadWeaver,
    ThreadWeaverError,
)
from core.conversation_consolidation import ConversationNotebook


def _episode(
    chat_id: str,
    *,
    goal: str = "Ship the continuity milestone",
    topic: str = "Titan continuity",
    related: list[str] | None = None,
    created_at: str = "2026-08-01T10:00:00+00:00",
    finalized_at: str | None = "2026-08-01T11:00:00+00:00",
    conclusion: str = "Keep the projection deterministic",
) -> ConversationEpisode:
    return ConversationEpisode.from_notebook(
        ConversationNotebook(
            chat_id=chat_id,
            main_topic=topic,
            user_goal=goal,
            key_insights=["Preserve provenance"],
            conclusion=conclusion,
            related_chats=related or [],
            facts_count=2,
            messages_count=5,
            produced_gist=finalized_at is not None,
            created_at=created_at,
            finalized_at=finalized_at,
        )
    )


def test_explicit_related_chat_reference_creates_reference_link() -> None:
    older = _episode("chat:older")
    newer = _episode(
        "chat:newer",
        related=["chat:older"],
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )

    result = ThreadWeaver().weave([older, newer])

    assert len(result.links) == 1
    link = result.links[0]
    assert link.source_chat_id == "chat:newer"
    assert link.target_chat_id == "chat:older"
    assert link.relation is ThreadRelation.REFERENCES
    assert link.strength is ThreadLinkStrength.EXPLICIT
    assert link.signals == (ThreadSignal.EXPLICIT_RELATED_CHAT_REF,)
    assert len(result.threads) == 1
    assert result.unresolved_references == ()


def test_exact_normalized_goal_creates_structural_continuation() -> None:
    older = _episode("chat:older", goal="Ship the MVP", topic="Architecture")
    newer = _episode(
        "chat:newer",
        goal="  SHIP   THE MVP  ",
        topic=" architecture ",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )

    result = ThreadWeaver().weave([newer, older])

    assert len(result.links) == 1
    link = result.links[0]
    assert link.relation is ThreadRelation.CONTINUES
    assert link.strength is ThreadLinkStrength.STRUCTURAL
    assert link.source_chat_id == "chat:newer"
    assert link.target_chat_id == "chat:older"
    assert link.signals == (
        ThreadSignal.EXACT_NOTEBOOK_GOAL_TEXT,
        ThreadSignal.EXACT_NOTEBOOK_TOPIC_TEXT,
    )


def test_topic_and_time_alone_never_create_a_link() -> None:
    first = _episode("chat:first", goal="Design storage", topic="Memory")
    second = _episode(
        "chat:second",
        goal="Plan a release",
        topic="Memory",
        created_at="2026-08-01T12:00:00+00:00",
        finalized_at="2026-08-01T13:00:00+00:00",
    )

    result = ThreadWeaver().weave([first, second])

    assert result.links == ()
    assert result.threads == ()


def test_explicit_reference_dominates_structural_goal_match() -> None:
    older = _episode("chat:older", goal="Ship the MVP")
    newer = _episode(
        "chat:newer",
        goal="Ship the MVP",
        related=["chat:older"],
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )

    result = ThreadWeaver().weave([older, newer])

    assert len(result.links) == 1
    assert result.links[0].relation is ThreadRelation.REFERENCES
    assert result.links[0].strength is ThreadLinkStrength.EXPLICIT


def test_missing_explicit_target_is_preserved_as_unresolved_projection() -> None:
    source = _episode("chat:source", related=["chat:not-loaded"])

    result = ThreadWeaver().weave([source])

    assert result.links == ()
    assert result.threads == ()
    assert len(result.unresolved_references) == 1
    reference = result.unresolved_references[0]
    assert reference.source_chat_id == "chat:source"
    assert reference.target_chat_ref == "chat:not-loaded"
    assert reference.signal is ThreadSignal.EXPLICIT_RELATED_CHAT_REF


def test_input_order_does_not_change_links_threads_or_unresolved_ids() -> None:
    first = _episode("chat:first", goal="Goal A")
    second = _episode(
        "chat:second",
        goal="goal a",
        related=["chat:missing"],
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    third = _episode(
        "chat:third",
        goal="Goal B",
        related=["chat:second"],
        created_at="2026-08-03T10:00:00+00:00",
        finalized_at="2026-08-03T11:00:00+00:00",
    )

    forward = ThreadWeaver().weave([first, second, third])
    reverse = ThreadWeaver().weave([third, second, first])

    assert tuple(link.link_id for link in forward.links) == tuple(
        link.link_id for link in reverse.links
    )
    assert tuple(thread.thread_id for thread in forward.threads) == tuple(
        thread.thread_id for thread in reverse.threads
    )
    assert tuple(ref.reference_id for ref in forward.unresolved_references) == tuple(
        ref.reference_id for ref in reverse.unresolved_references
    )


def test_connected_links_form_one_chronological_thread() -> None:
    first = _episode("chat:first", goal="Goal A")
    second = _episode(
        "chat:second",
        goal="Goal A",
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    third = _episode(
        "chat:third",
        goal="Goal B",
        related=["chat:second"],
        created_at="2026-08-03T10:00:00+00:00",
        finalized_at="2026-08-03T11:00:00+00:00",
    )

    result = ThreadWeaver().weave([third, first, second])

    assert len(result.threads) == 1
    thread = result.threads[0]
    assert thread.chat_ids == ("chat:first", "chat:second", "chat:third")
    assert len(thread.link_ids) == 2


def test_identical_duplicate_episode_is_deduplicated() -> None:
    episode = _episode("chat:one")

    result = ThreadWeaver().weave([episode, episode])

    assert result.links == ()
    assert result.threads == ()


def test_conflicting_duplicate_episode_fails_closed() -> None:
    first = _episode("chat:duplicate", goal="First goal")
    conflicting = _episode("chat:duplicate", goal="Second goal")

    with pytest.raises(ThreadWeaverError, match="conflicting episode snapshots"):
        ThreadWeaver().weave([first, conflicting])


def test_self_reference_fails_closed() -> None:
    episode = _episode("chat:self", related=["chat:self"])

    with pytest.raises(ThreadWeaverError, match="references itself"):
        ThreadWeaver().weave([episode])


def test_relation_taxonomy_is_present_but_not_inferred_without_typed_evidence() -> None:
    assert {relation.value for relation in ThreadRelation} == {
        "continues",
        "references",
        "updates",
        "supersedes",
        "reopens",
        "contradicts",
        "blocks",
        "resolves",
        "depends_on",
        "belongs_to",
    }

    first = _episode("chat:first", goal="Goal A", conclusion="Decision X")
    second = _episode("chat:second", goal="Goal B", conclusion="Decision Y")
    assert ThreadWeaver().weave([first, second]).links == ()


def test_thread_projection_is_immutable_and_has_no_epistemic_or_action_authority() -> None:
    older = _episode("chat:older")
    newer = _episode(
        "chat:newer",
        related=["chat:older"],
        created_at="2026-08-02T10:00:00+00:00",
        finalized_at="2026-08-02T11:00:00+00:00",
    )
    thread = ThreadWeaver().weave([older, newer]).threads[0]

    assert isinstance(thread, ContinuityThread)
    with pytest.raises(FrozenInstanceError):
        thread.thread_id = "mutated"  # type: ignore[misc]

    for forbidden in (
        "truth_status",
        "epistemic_status",
        "confirmed",
        "salience",
        "advice",
        "action_decision",
    ):
        assert not hasattr(thread, forbidden)
