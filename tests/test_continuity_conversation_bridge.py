"""Tests for the read-only conversation continuity bridge."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.continuity import (
    ConversationBridge,
    ConversationBridgeError,
    ConversationEpisode,
)
from core.conversation_consolidation import ConversationConsolidator, ConversationNotebook

_CREATED = "2026-08-01T10:00:00+00:00"
_FINALIZED = "2026-08-01T11:00:00+00:00"


def _notebook(
    *,
    chat_id: str = "chat:42",
    topic: str = "Titan continuity",
    goal: str = "Design a read-only bridge",
    insights: list[str] | None = None,
    related_chats: list[str] | None = None,
    created_at: str = _CREATED,
    finalized_at: str | None = _FINALIZED,
) -> ConversationNotebook:
    return ConversationNotebook(
        chat_id=chat_id,
        main_topic=topic,
        user_goal=goal,
        key_insights=insights or ["Keep source evidence separate from projection"],
        conclusion="Use immutable deterministic snapshots",
        related_chats=related_chats or [],
        facts_count=3,
        messages_count=8,
        produced_gist=finalized_at is not None,
        created_at=created_at,
        finalized_at=finalized_at,
    )


class SpyNotebookReader:
    def __init__(self, notebooks: list[ConversationNotebook]) -> None:
        self.notebooks = notebooks
        self.read_calls: list[tuple[object, ...]] = []

    def get_notebook(self, chat_id: str) -> ConversationNotebook | None:
        self.read_calls.append(("get_notebook", chat_id))
        return next((item for item in self.notebooks if item.chat_id == chat_id), None)

    def search(self, query: str, limit: int = 10) -> list[ConversationNotebook]:
        self.read_calls.append(("search", query, limit))
        return self.notebooks[:limit]

    def list_recent(self, limit: int = 10) -> list[ConversationNotebook]:
        self.read_calls.append(("list_recent", limit))
        return self.notebooks[:limit]

    def add_insight(self, **_: object) -> bool:
        raise AssertionError("bridge must never call add_insight")

    def finalize(self, **_: object) -> ConversationNotebook | None:
        raise AssertionError("bridge must never call finalize")


def test_get_episode_reads_only_and_detaches_from_mutable_notebook() -> None:
    notebook = _notebook(insights=["First insight"])
    source = SpyNotebookReader([notebook])
    bridge = ConversationBridge(source)

    episode = bridge.get_episode("chat:42")

    assert episode is not None
    assert episode.key_insights == ("First insight",)
    assert source.read_calls == [("get_notebook", "chat:42")]

    notebook.key_insights.append("Later mutation")
    assert episode.key_insights == ("First insight",)

    with pytest.raises(FrozenInstanceError):
        episode.main_topic = "mutated"  # type: ignore[misc]


def test_projection_is_deterministic_and_normalizes_set_like_related_chats() -> None:
    first = _notebook(
        related_chats=[" chat:z ", "chat:a", "chat:z"],
        insights=[" A  stable   insight "],
    )
    second = _notebook(
        related_chats=["chat:a", "chat:z"],
        insights=["A stable insight"],
    )

    first_episode = ConversationEpisode.from_notebook(first)
    second_episode = ConversationEpisode.from_notebook(second)

    assert first_episode.related_chat_refs == ("chat:a", "chat:z")
    assert first_episode.episode_id == second_episode.episode_id
    assert first_episode.payload_hash == second_episode.payload_hash
    assert first_episode.canonical_bytes() == second_episode.canonical_bytes()


def test_episode_carries_no_truth_salience_or_action_authority() -> None:
    episode = ConversationEpisode.from_notebook(_notebook())

    for forbidden in (
        "truth_status",
        "epistemic_status",
        "confirmed",
        "salience",
        "advice",
        "action_decision",
    ):
        assert not hasattr(episode, forbidden)


def test_search_is_deterministic_and_deduplicates_identical_snapshots() -> None:
    older = _notebook(
        chat_id="chat:older",
        created_at="2026-07-31T09:00:00+00:00",
        finalized_at="2026-07-31T10:00:00+00:00",
    )
    newer = _notebook(chat_id="chat:newer")
    source = SpyNotebookReader([older, newer, newer])

    episodes = ConversationBridge(source).search_episodes("continuity", limit=10)

    assert tuple(item.chat_id for item in episodes) == ("chat:newer", "chat:older")
    assert source.read_calls == [("search", "continuity", 10)]


def test_conflicting_duplicate_chat_snapshots_fail_closed() -> None:
    source = SpyNotebookReader(
        [
            _notebook(chat_id="chat:duplicate", topic="First topic"),
            _notebook(chat_id="chat:duplicate", topic="Conflicting topic"),
        ]
    )

    with pytest.raises(ConversationBridgeError, match="conflicting snapshots"):
        ConversationBridge(source).list_recent()


def test_invalid_or_naive_source_timestamp_is_rejected() -> None:
    with pytest.raises(ConversationBridgeError, match="timezone-aware"):
        ConversationEpisode.from_notebook(
            _notebook(created_at="2026-08-01T10:00:00", finalized_at=None)
        )


@pytest.mark.parametrize("limit", [0, 101, True])
def test_invalid_limits_are_rejected(limit: int) -> None:
    bridge = ConversationBridge(SpyNotebookReader([]))
    with pytest.raises(ConversationBridgeError):
        bridge.list_recent(limit=limit)


def test_real_consolidator_bridge_read_does_not_change_notebook_state(tmp_path: Path) -> None:
    consolidator = ConversationConsolidator(str(tmp_path / "conversation.db"))
    consolidator.add_insight(chat_id="chat:integration", insight="Read source only")
    notebook = consolidator.finalize(
        chat_id="chat:integration",
        main_topic="Continuity bridge",
        user_goal="Preserve existing notebooks",
        conclusion="Projection remains rebuildable",
        facts_count=2,
    )
    assert notebook is not None

    before = consolidator.get_notebook("chat:integration")
    assert before is not None

    episode = ConversationBridge(consolidator).get_episode("chat:integration")

    after = consolidator.get_notebook("chat:integration")
    assert episode is not None
    assert episode.chat_id == "chat:integration"
    assert episode.created_at.tzinfo is UTC
    assert after is not None
    assert before.to_dict() == after.to_dict()
