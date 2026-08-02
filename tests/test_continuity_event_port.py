"""Tests for the neutral event port and append-only shadow ledger."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from core.continuity import (
    ActorKind,
    ActorRef,
    AppendStatus,
    IntegrityStatus,
    InteractionEvent,
    InteractionEventType,
    LedgerPortError,
    LocalShadowLedger,
    NeutralEventPort,
    StreamPosition,
    SubjectKind,
    SubjectRef,
)

_BASE_TIME = datetime(2026, 8, 2, 6, 0, 0, tzinfo=UTC)


def _event(index: int) -> InteractionEvent:
    occurred_at = _BASE_TIME + timedelta(seconds=index * 2)
    return InteractionEvent.create(
        event_type=InteractionEventType.MESSAGE,
        actor_ref=ActorRef("operator:ruslan", ActorKind.OPERATOR),
        subject_refs=(SubjectRef("project:titan", SubjectKind.PROJECT),),
        session_ref="chat:ledger-test",
        content_ref=f"message:{index:04d}",
        occurred_at=occurred_at,
        recorded_at=occurred_at + timedelta(seconds=1),
    )


def test_shadow_ledger_implements_neutral_event_port() -> None:
    assert isinstance(LocalShadowLedger(), NeutralEventPort)


def test_append_read_head_and_verify() -> None:
    ledger = LocalShadowLedger()
    event = _event(1)

    result = ledger.append(event, idempotency_key="request:1")

    assert result.status is AppendStatus.APPENDED
    assert result.event_id == event.event_id
    assert result.sequence == 1
    assert ledger.read(event.event_id) == event
    assert ledger.head() == StreamPosition(1)
    assert ledger.verify(event.event_id).status is IntegrityStatus.VERIFIED


def test_same_event_is_idempotent_and_does_not_grow_ledger() -> None:
    ledger = LocalShadowLedger()
    event = _event(1)

    first = ledger.append(event, idempotency_key="request:1")
    replay = ledger.append(event, idempotency_key="request:1")
    replay_with_alias = ledger.append(event, idempotency_key="request:1:retry")

    assert first.status is AppendStatus.APPENDED
    assert replay.status is AppendStatus.IDEMPOTENT_REPLAY
    assert replay_with_alias.status is AppendStatus.IDEMPOTENT_REPLAY
    assert first.sequence == replay.sequence == replay_with_alias.sequence == 1
    assert len(ledger) == 1


def test_idempotency_key_conflict_is_rejected_without_append() -> None:
    ledger = LocalShadowLedger()
    first_event = _event(1)
    conflicting_event = _event(2)

    ledger.append(first_event, idempotency_key="request:shared")
    conflict = ledger.append(conflicting_event, idempotency_key="request:shared")

    assert conflict.status is AppendStatus.INTEGRITY_CONFLICT
    assert conflict.reason_code == "IDEMPOTENCY_KEY_CONFLICT"
    assert len(ledger) == 1
    assert ledger.read(conflicting_event.event_id) is None


def test_scan_is_monotonic_deterministic_and_paginated() -> None:
    ledger = LocalShadowLedger()
    events = tuple(_event(index) for index in range(1, 4))
    for event in events:
        ledger.append(event)

    first_page = ledger.scan(limit=2)
    second_page = ledger.scan(after_sequence=first_page.next_position.sequence, limit=2)

    assert tuple(entry.sequence for entry in first_page.entries) == (1, 2)
    assert tuple(entry.event for entry in first_page.entries) == events[:2]
    assert first_page.next_position == StreamPosition(2)
    assert first_page.has_more is True

    assert tuple(entry.sequence for entry in second_page.entries) == (3,)
    assert tuple(entry.event for entry in second_page.entries) == events[2:]
    assert second_page.next_position == StreamPosition(3)
    assert second_page.has_more is False


def test_verify_reports_missing_and_detects_tampering() -> None:
    ledger = LocalShadowLedger()
    missing = ledger.verify("missing-event")
    assert missing.status is IntegrityStatus.MISSING

    event = _event(1)
    ledger.append(event)
    object.__setattr__(event, "payload_hash", "0" * 64)

    result = ledger.verify(event.event_id)
    assert result.status is IntegrityStatus.HASH_MISMATCH
    assert result.actual_hash != result.expected_hash


def test_invalid_append_is_reported_without_exception() -> None:
    ledger = LocalShadowLedger()
    invalid = ledger.append(cast(InteractionEvent, object()))

    assert invalid.status is AppendStatus.INVALID_EVENT
    assert invalid.reason_code == "EVENT_TYPE_INVALID"
    assert len(ledger) == 0


@pytest.mark.parametrize(
    ("after_sequence", "limit"),
    [(-1, 1), (0, 0), (0, 1001), (True, 1), (0, False)],
)
def test_scan_rejects_invalid_bounds(after_sequence: int, limit: int) -> None:
    with pytest.raises(LedgerPortError):
        LocalShadowLedger().scan(after_sequence=after_sequence, limit=limit)


def test_shadow_ledger_exposes_no_destructive_or_pubsub_api() -> None:
    ledger = LocalShadowLedger()
    assert not hasattr(ledger, "delete")
    assert not hasattr(ledger, "flush")
    assert not hasattr(ledger, "truncate")
    assert not hasattr(ledger, "subscribe")


def test_concurrent_replays_append_exactly_once() -> None:
    ledger = LocalShadowLedger()
    event = _event(1)

    def append_once(_: int) -> AppendStatus:
        return ledger.append(event, idempotency_key="request:concurrent").status

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = tuple(executor.map(append_once, range(32)))

    assert statuses.count(AppendStatus.APPENDED) == 1
    assert statuses.count(AppendStatus.IDEMPOTENT_REPLAY) == 31
    assert len(ledger) == 1
    assert ledger.head() == StreamPosition(1)
