"""Neutral append-only event port and local shadow ledger.

The ledger records validated ``InteractionEvent`` objects without interpreting
truth, salience, goals, advice, or Canon state.  It is a transition adapter for
a future Native Kernel implementation, not a second canonical memory store.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from threading import RLock
from typing import Protocol, runtime_checkable

from .contracts import InteractionEvent


class LedgerPortError(ValueError):
    """Raised when a ledger read request is structurally invalid."""


class AppendStatus(str, Enum):
    APPENDED = "appended"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    INTEGRITY_CONFLICT = "integrity_conflict"
    INVALID_EVENT = "invalid_event"


class IntegrityStatus(str, Enum):
    VERIFIED = "verified"
    MISSING = "missing"
    HASH_MISMATCH = "hash_mismatch"


@dataclass(frozen=True, slots=True)
class StreamPosition:
    sequence: int

    def __post_init__(self) -> None:
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int):
            raise LedgerPortError("sequence must be an integer")
        if self.sequence < 0:
            raise LedgerPortError("sequence must be >= 0")


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    sequence: int
    event: InteractionEvent
    idempotency_key: str

    def __post_init__(self) -> None:
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int):
            raise LedgerPortError("sequence must be an integer")
        if self.sequence <= 0:
            raise LedgerPortError("ledger entry sequence must be > 0")
        if not isinstance(self.event, InteractionEvent):
            raise LedgerPortError("event must be an InteractionEvent")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key.strip():
            raise LedgerPortError("idempotency_key must be a non-empty string")


@dataclass(frozen=True, slots=True)
class AppendResult:
    status: AppendStatus
    event_id: str | None
    sequence: int | None
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class EventPage:
    entries: tuple[LedgerEntry, ...]
    next_position: StreamPosition
    has_more: bool


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    status: IntegrityStatus
    event_id: str
    sequence: int | None
    expected_hash: str | None
    actual_hash: str | None


@runtime_checkable
class NeutralEventPort(Protocol):
    """Transport-neutral append/read contract consumed by Titan."""

    def append(
        self,
        event: InteractionEvent,
        *,
        idempotency_key: str | None = None,
    ) -> AppendResult:
        """Append one immutable event or report an idempotent/conflicting replay."""
        ...

    def read(self, event_id: str) -> InteractionEvent | None:
        """Read one event by its deterministic identifier."""
        ...

    def scan(self, *, after_sequence: int = 0, limit: int = 100) -> EventPage:
        """Read events in ascending sequence order."""
        ...

    def head(self) -> StreamPosition:
        """Return the current append position."""
        ...

    def verify(self, event_id: str) -> IntegrityResult:
        """Recompute the canonical event hash and report integrity."""
        ...


class LocalShadowLedger:
    """Thread-safe, in-memory, append-only implementation of ``NeutralEventPort``.

    The adapter is intentionally disposable and rebuildable.  It does not
    expose delete, truncate, flush, subscribe, or canonical promotion methods.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: list[LedgerEntry] = []
        self._events_by_id: dict[str, LedgerEntry] = {}
        self._idempotency_index: dict[str, str] = {}

    def append(
        self,
        event: InteractionEvent,
        *,
        idempotency_key: str | None = None,
    ) -> AppendResult:
        if not isinstance(event, InteractionEvent):
            return AppendResult(
                status=AppendStatus.INVALID_EVENT,
                event_id=None,
                sequence=None,
                reason_code="EVENT_TYPE_INVALID",
            )

        resolved_key = idempotency_key or event.event_id
        if not isinstance(resolved_key, str) or not resolved_key.strip():
            return AppendResult(
                status=AppendStatus.INVALID_EVENT,
                event_id=event.event_id,
                sequence=None,
                reason_code="IDEMPOTENCY_KEY_INVALID",
            )

        with self._lock:
            keyed_event_id = self._idempotency_index.get(resolved_key)
            if keyed_event_id is not None:
                existing = self._events_by_id[keyed_event_id]
                if self._same_event(existing.event, event):
                    return AppendResult(
                        status=AppendStatus.IDEMPOTENT_REPLAY,
                        event_id=existing.event.event_id,
                        sequence=existing.sequence,
                        reason_code="IDEMPOTENCY_KEY_REPLAY",
                    )
                return AppendResult(
                    status=AppendStatus.INTEGRITY_CONFLICT,
                    event_id=event.event_id,
                    sequence=existing.sequence,
                    reason_code="IDEMPOTENCY_KEY_CONFLICT",
                )

            existing = self._events_by_id.get(event.event_id)
            if existing is not None:
                if self._same_event(existing.event, event):
                    self._idempotency_index[resolved_key] = event.event_id
                    return AppendResult(
                        status=AppendStatus.IDEMPOTENT_REPLAY,
                        event_id=event.event_id,
                        sequence=existing.sequence,
                        reason_code="EVENT_ID_REPLAY",
                    )
                return AppendResult(
                    status=AppendStatus.INTEGRITY_CONFLICT,
                    event_id=event.event_id,
                    sequence=existing.sequence,
                    reason_code="EVENT_ID_CONFLICT",
                )

            sequence = len(self._entries) + 1
            entry = LedgerEntry(
                sequence=sequence,
                event=event,
                idempotency_key=resolved_key,
            )
            self._entries.append(entry)
            self._events_by_id[event.event_id] = entry
            self._idempotency_index[resolved_key] = event.event_id
            return AppendResult(
                status=AppendStatus.APPENDED,
                event_id=event.event_id,
                sequence=sequence,
            )

    def read(self, event_id: str) -> InteractionEvent | None:
        if not isinstance(event_id, str) or not event_id.strip():
            return None
        with self._lock:
            entry = self._events_by_id.get(event_id)
            return entry.event if entry is not None else None

    def scan(self, *, after_sequence: int = 0, limit: int = 100) -> EventPage:
        self._validate_scan(after_sequence=after_sequence, limit=limit)
        with self._lock:
            selected = tuple(self._entries[after_sequence : after_sequence + limit])
            next_sequence = selected[-1].sequence if selected else after_sequence
            return EventPage(
                entries=selected,
                next_position=StreamPosition(next_sequence),
                has_more=next_sequence < len(self._entries),
            )

    def head(self) -> StreamPosition:
        with self._lock:
            return StreamPosition(len(self._entries))

    def verify(self, event_id: str) -> IntegrityResult:
        with self._lock:
            entry = self._events_by_id.get(event_id)
            if entry is None:
                return IntegrityResult(
                    status=IntegrityStatus.MISSING,
                    event_id=event_id,
                    sequence=None,
                    expected_hash=None,
                    actual_hash=None,
                )

            actual_hash = sha256(entry.event.canonical_bytes()).hexdigest()
            if (
                actual_hash == entry.event.payload_hash
                and actual_hash == entry.event.event_id
                and event_id == entry.event.event_id
            ):
                status = IntegrityStatus.VERIFIED
            else:
                status = IntegrityStatus.HASH_MISMATCH
            return IntegrityResult(
                status=status,
                event_id=event_id,
                sequence=entry.sequence,
                expected_hash=entry.event.payload_hash,
                actual_hash=actual_hash,
            )

    @staticmethod
    def _same_event(left: InteractionEvent, right: InteractionEvent) -> bool:
        return (
            left.event_id == right.event_id
            and left.payload_hash == right.payload_hash
            and left.canonical_bytes() == right.canonical_bytes()
        )

    @staticmethod
    def _validate_scan(*, after_sequence: int, limit: int) -> None:
        if (
            isinstance(after_sequence, bool)
            or not isinstance(after_sequence, int)
            or after_sequence < 0
        ):
            raise LedgerPortError("after_sequence must be an integer >= 0")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise LedgerPortError("limit must be an integer in [1, 1000]")

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


__all__ = [
    "AppendResult",
    "AppendStatus",
    "EventPage",
    "IntegrityResult",
    "IntegrityStatus",
    "LedgerEntry",
    "LedgerPortError",
    "LocalShadowLedger",
    "NeutralEventPort",
    "StreamPosition",
]
