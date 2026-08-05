"""Current-main regressions for Continuity R2 recovery."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from core.continuity import (
    ActorKind,
    ActorRef,
    InteractionEvent,
    InteractionEventType,
    LocalShadowLedger,
    SubjectKind,
    SubjectRef,
    ThreadWeaver,
)
from core.conversation_consolidation import ConversationConsolidator


def _event(index: int) -> InteractionEvent:
    occurred = datetime(2026, 8, 5, 12, 0, tzinfo=UTC) + timedelta(seconds=index)
    return InteractionEvent.create(
        event_type=InteractionEventType.MESSAGE,
        actor_ref=ActorRef("operator:test", ActorKind.OPERATOR),
        subject_refs=(SubjectRef("project:titan", SubjectKind.PROJECT),),
        session_ref="session:r2",
        content_ref=f"message:{index}",
        occurred_at=occurred,
        recorded_at=occurred,
    )


def test_conversation_reads_preserve_created_at_and_related_chats(tmp_path: Path) -> None:
    db_path = tmp_path / "conversation.db"
    consolidator = ConversationConsolidator(str(db_path))
    assert consolidator.add_insight(chat_id="chat:r2", insight="Preserve read fidelity")
    notebook = consolidator.finalize(
        chat_id="chat:r2",
        main_topic="Continuity R2",
        user_goal="Keep legacy source evidence exact",
        conclusion="Read-only bridge",
    )
    assert notebook is not None

    expected_created = "2026-08-01T09:30:00+00:00"
    expected_related = ["chat:older", "chat:reference"]
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE conversation_notebooks SET created_at = ?, related_chats = ? WHERE chat_id = ?",
            (expected_created, json.dumps(expected_related), "chat:r2"),
        )
        conn.commit()

    direct = consolidator.get_notebook("chat:r2")
    searched = consolidator.search("Continuity R2")
    recent = consolidator.list_recent()

    assert direct is not None
    assert direct.created_at == expected_created
    assert direct.related_chats == expected_related
    assert searched[0].created_at == expected_created
    assert searched[0].related_chats == expected_related
    assert recent[0].created_at == expected_created
    assert recent[0].related_chats == expected_related


def test_r2_components_expose_no_canon_or_action_surface() -> None:
    ledger = LocalShadowLedger()
    weaver = ThreadWeaver()

    for component in (ledger, weaver):
        for forbidden in (
            "admit",
            "promote",
            "write_canon",
            "truth_gate",
            "answer",
            "advise",
            "execute",
            "send",
            "delete",
            "truncate",
        ):
            assert not hasattr(component, forbidden)


def test_local_shadow_ledger_is_process_local_and_rebuildable() -> None:
    first = LocalShadowLedger()
    second = LocalShadowLedger()
    event = _event(1)

    first.append(event)

    assert first.read(event.event_id) == event
    assert second.read(event.event_id) is None
    assert not hasattr(first, "db_path")
    assert not hasattr(first, "persist")
