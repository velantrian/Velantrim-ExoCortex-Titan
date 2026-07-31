"""Immutable, resumable ReadingSession foundation for Reader Core PR-RDR-07.

The session layer tracks progress, resource accounting, checkpoints, fenced
worker ownership, and revision-aware reuse proposals. It performs no I/O,
schedules no work, and grants no Canon, memory, policy, graph, tool, TruthGate,
or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Iterable

from core.hierarchical_section_planner import HierarchicalSectionPlan, ReadingUnit
from core.reader_core_contracts import SessionState, stable_reader_core_id
from core.section_card import SectionCard
from core.semantic_reader import RawSource

READING_SESSION_SCHEMA_VERSION = "reader-core.reading-session.v1"


class ReadingSessionError(ValueError):
    """Raised when a ReadingSession invariant or transition is invalid."""


class ReadingSessionBudgetExceeded(ReadingSessionError):
    """Raised before a transition would exceed an immutable resource budget."""


class SessionEventKind(str, Enum):
    CREATED = "created"
    LEASE_CLAIMED = "lease_claimed"
    LEASE_RENEWED = "lease_renewed"
    STARTED = "started"
    RESUMED = "resumed"
    CARDS_RECORDED = "cards_recorded"
    ARTIFACTS_ATTACHED = "artifacts_attached"
    PAUSED = "paused"
    DEGRADED = "degraded"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STALE = "stale"
    REVISION_REBASED = "revision_rebased"


class SessionArtifactKind(str, Enum):
    CURRENT_CARD = "current_card"
    REUSED_CARD = "reused_card"


@dataclass(frozen=True, slots=True)
class ReadingSessionBudget:
    max_processed_units: int = 10_000
    max_source_chars: int = 100_000_000
    max_model_tokens: int = 10_000_000
    max_wall_time_ms: int = 86_400_000
    max_receipts: int = 100_000

    def __post_init__(self) -> None:
        for name in (
            "max_processed_units",
            "max_source_chars",
            "max_model_tokens",
            "max_wall_time_ms",
            "max_receipts",
        ):
            _positive_int(getattr(self, name), name)

    def identity_payload(self) -> dict[str, int]:
        return {
            "max_processed_units": self.max_processed_units,
            "max_source_chars": self.max_source_chars,
            "max_model_tokens": self.max_model_tokens,
            "max_wall_time_ms": self.max_wall_time_ms,
            "max_receipts": self.max_receipts,
        }


@dataclass(frozen=True, slots=True)
class ReadingSessionUsage:
    """Measured resource use, never a quality or truth score."""

    processed_units: int = 0
    source_chars: int = 0
    model_tokens: int = 0
    wall_time_ms: int = 0
    receipts_emitted: int = 0

    def __post_init__(self) -> None:
        for name in (
            "processed_units",
            "source_chars",
            "model_tokens",
            "wall_time_ms",
            "receipts_emitted",
        ):
            _nonnegative_int(getattr(self, name), name)

    def plus(self, other: ReadingSessionUsage) -> ReadingSessionUsage:
        if not isinstance(other, ReadingSessionUsage):
            raise ReadingSessionError("usage delta must be ReadingSessionUsage")
        return ReadingSessionUsage(
            processed_units=self.processed_units + other.processed_units,
            source_chars=self.source_chars + other.source_chars,
            model_tokens=self.model_tokens + other.model_tokens,
            wall_time_ms=self.wall_time_ms + other.wall_time_ms,
            receipts_emitted=self.receipts_emitted + other.receipts_emitted,
        )

    def identity_payload(self) -> dict[str, int]:
        return {
            "processed_units": self.processed_units,
            "source_chars": self.source_chars,
            "model_tokens": self.model_tokens,
            "wall_time_ms": self.wall_time_ms,
            "receipts_emitted": self.receipts_emitted,
        }


@dataclass(frozen=True, slots=True)
class SessionLease:
    runner_id: str
    generation: int
    expires_at_ms: int
    lease_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.runner_id, "runner_id")
        _positive_int(self.generation, "generation")
        _positive_int(self.expires_at_ms, "expires_at_ms")
        expected = stable_reader_core_id(
            "reading-session-lease",
            {
                "runner_id": self.runner_id,
                "generation": self.generation,
                "expires_at_ms": self.expires_at_ms,
            },
        )
        if self.lease_id:
            if self.lease_id != expected:
                raise ReadingSessionError("lease_id does not match lease content")
        else:
            object.__setattr__(self, "lease_id", expected)

    def identity_payload(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "runner_id": self.runner_id,
            "generation": self.generation,
            "expires_at_ms": self.expires_at_ms,
        }


@dataclass(frozen=True, slots=True)
class SessionUnitArtifact:
    unit_id: str
    artifact_id: str
    kind: SessionArtifactKind
    artifact_source_revision: str

    def __post_init__(self) -> None:
        _require_text(self.unit_id, "unit_id")
        _require_text(self.artifact_id, "artifact_id")
        _require_text(self.artifact_source_revision, "artifact_source_revision")
        if not isinstance(self.kind, SessionArtifactKind):
            raise ReadingSessionError("kind must be a SessionArtifactKind")

    def identity_payload(self) -> dict[str, str]:
        return {
            "unit_id": self.unit_id,
            "artifact_id": self.artifact_id,
            "kind": self.kind.value,
            "artifact_source_revision": self.artifact_source_revision,
        }


@dataclass(frozen=True, slots=True)
class ReadingSessionReceipt:
    session_id: str
    sequence: int
    previous_receipt_id: str | None
    event_kind: SessionEventKind
    from_state: SessionState | None
    to_state: SessionState
    reason_code: str
    affected_unit_ids: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    usage_delta: ReadingSessionUsage
    lease_generation: int
    receipt_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.session_id, "session_id")
        _nonnegative_int(self.sequence, "sequence")
        if self.previous_receipt_id is not None:
            _require_text(self.previous_receipt_id, "previous_receipt_id")
        if not isinstance(self.event_kind, SessionEventKind):
            raise ReadingSessionError("event_kind must be SessionEventKind")
        if self.from_state is not None and not isinstance(self.from_state, SessionState):
            raise ReadingSessionError("from_state must be SessionState or None")
        if not isinstance(self.to_state, SessionState):
            raise ReadingSessionError("to_state must be SessionState")
        _require_text(self.reason_code, "reason_code")
        units = _unique_text_tuple(self.affected_unit_ids, "affected_unit_id")
        artifacts = _unique_text_tuple(self.artifact_ids, "artifact_id")
        if not isinstance(self.usage_delta, ReadingSessionUsage):
            raise ReadingSessionError("usage_delta must be ReadingSessionUsage")
        _nonnegative_int(self.lease_generation, "lease_generation")
        object.__setattr__(self, "affected_unit_ids", units)
        object.__setattr__(self, "artifact_ids", artifacts)
        expected = stable_reader_core_id(
            "reading-session-receipt",
            {
                "session_id": self.session_id,
                "sequence": self.sequence,
                "previous_receipt_id": self.previous_receipt_id,
                "event_kind": self.event_kind.value,
                "from_state": (
                    self.from_state.value if self.from_state is not None else None
                ),
                "to_state": self.to_state.value,
                "reason_code": self.reason_code,
                "affected_unit_ids": list(units),
                "artifact_ids": list(artifacts),
                "usage_delta": self.usage_delta.identity_payload(),
                "lease_generation": self.lease_generation,
            },
        )
        if self.receipt_id:
            if self.receipt_id != expected:
                raise ReadingSessionError("receipt_id does not match receipt content")
        else:
            object.__setattr__(self, "receipt_id", expected)


@dataclass(frozen=True, slots=True)
class ReadingSession:
    session_id: str
    manager_version: str
    session_key_hash: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    state: SessionState
    revision_generation: int
    all_unit_ids: tuple[str, ...]
    pending_unit_ids: tuple[str, ...]
    completed_unit_ids: tuple[str, ...]
    unit_artifacts: tuple[SessionUnitArtifact, ...]
    coverage_map_id: str | None
    reread_plan_id: str | None
    relation_set_id: str | None
    unresolved_question_refs: tuple[str, ...]
    resource_budget: ReadingSessionBudget
    resource_usage: ReadingSessionUsage
    policy_snapshot_id: str
    policy_version: str
    capability_lease_ref: str | None
    lease_generation: int
    active_lease: SessionLease | None
    receipts: tuple[ReadingSessionReceipt, ...]
    warnings: tuple[str, ...] = ()
    schema_version: str = READING_SESSION_SCHEMA_VERSION
    snapshot_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "session_id",
            "manager_version",
            "session_key_hash",
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
            "policy_snapshot_id",
            "policy_version",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != READING_SESSION_SCHEMA_VERSION:
            raise ReadingSessionError("unsupported ReadingSession schema_version")
        if len(self.session_key_hash) != 64 or any(
            char not in "0123456789abcdef" for char in self.session_key_hash
        ):
            raise ReadingSessionError("session_key_hash must be lowercase SHA-256 hex")
        if not isinstance(self.state, SessionState):
            raise ReadingSessionError("state must be SessionState")
        _nonnegative_int(self.revision_generation, "revision_generation")
        all_units = _unique_text_tuple(self.all_unit_ids, "all_unit_id")
        pending = _unique_text_tuple(self.pending_unit_ids, "pending_unit_id")
        completed = _unique_text_tuple(self.completed_unit_ids, "completed_unit_id")
        if set(pending) & set(completed):
            raise ReadingSessionError("pending and completed units must be disjoint")
        if set(pending) | set(completed) != set(all_units):
            raise ReadingSessionError(
                "pending and completed units must partition all_unit_ids"
            )
        if tuple(unit for unit in all_units if unit in pending) != pending:
            raise ReadingSessionError("pending units must follow plan order")
        if tuple(unit for unit in all_units if unit in completed) != completed:
            raise ReadingSessionError("completed units must follow plan order")

        artifacts = tuple(self.unit_artifacts)
        if any(not isinstance(item, SessionUnitArtifact) for item in artifacts):
            raise ReadingSessionError("invalid unit_artifacts value")
        if tuple(item.unit_id for item in artifacts) != completed:
            raise ReadingSessionError(
                "unit_artifacts must match completed units in plan order"
            )
        if len({item.artifact_id for item in artifacts}) != len(artifacts):
            raise ReadingSessionError("unit artifact IDs must be unique")
        for artifact in artifacts:
            if (
                artifact.kind is SessionArtifactKind.CURRENT_CARD
                and artifact.artifact_source_revision != self.source_revision
            ):
                raise ReadingSessionError(
                    "current card revision must match session revision"
                )

        for name in ("coverage_map_id", "reread_plan_id", "relation_set_id"):
            value = getattr(self, name)
            if value is not None:
                _require_text(value, name)
        questions = _unique_text_tuple(
            self.unresolved_question_refs,
            "unresolved_question_ref",
        )
        if not isinstance(self.resource_budget, ReadingSessionBudget):
            raise ReadingSessionError("resource_budget must be ReadingSessionBudget")
        if not isinstance(self.resource_usage, ReadingSessionUsage):
            raise ReadingSessionError("resource_usage must be ReadingSessionUsage")
        _validate_usage(self.resource_usage, self.resource_budget)
        if self.capability_lease_ref is not None:
            _require_text(self.capability_lease_ref, "capability_lease_ref")
        _nonnegative_int(self.lease_generation, "lease_generation")
        if self.active_lease is not None:
            if not isinstance(self.active_lease, SessionLease):
                raise ReadingSessionError("active_lease must be SessionLease or None")
            if self.active_lease.generation != self.lease_generation:
                raise ReadingSessionError("active lease generation mismatch")

        receipts = tuple(self.receipts)
        if not receipts:
            raise ReadingSessionError("a session requires at least one receipt")
        if any(not isinstance(item, ReadingSessionReceipt) for item in receipts):
            raise ReadingSessionError("invalid receipts value")
        if tuple(item.sequence for item in receipts) != tuple(range(len(receipts))):
            raise ReadingSessionError("receipt sequences must start at zero")
        for index, receipt in enumerate(receipts):
            expected_previous = None if index == 0 else receipts[index - 1].receipt_id
            if receipt.session_id != self.session_id:
                raise ReadingSessionError("receipt session_id mismatch")
            if receipt.previous_receipt_id != expected_previous:
                raise ReadingSessionError("receipt hash chain is discontinuous")
        if receipts[-1].to_state != self.state:
            raise ReadingSessionError("last receipt state must equal session state")
        if self.resource_usage.receipts_emitted != len(receipts):
            raise ReadingSessionError("receipt accounting mismatch")
        warnings = _unique_text_tuple(self.warnings, "warning")

        object.__setattr__(self, "all_unit_ids", all_units)
        object.__setattr__(self, "pending_unit_ids", pending)
        object.__setattr__(self, "completed_unit_ids", completed)
        object.__setattr__(self, "unit_artifacts", artifacts)
        object.__setattr__(self, "unresolved_question_refs", questions)
        object.__setattr__(self, "receipts", receipts)
        object.__setattr__(self, "warnings", warnings)
        expected = _session_snapshot_id(self)
        if self.snapshot_id:
            if self.snapshot_id != expected:
                raise ReadingSessionError("snapshot_id does not match session content")
        else:
            object.__setattr__(self, "snapshot_id", expected)


@dataclass(frozen=True, slots=True)
class RevisionReusePair:
    old_unit_id: str
    new_unit_id: str
    old_artifact_id: str
    old_source_revision: str
    source_text_hash: str

    def __post_init__(self) -> None:
        for name in (
            "old_unit_id",
            "new_unit_id",
            "old_artifact_id",
            "old_source_revision",
            "source_text_hash",
        ):
            _require_text(getattr(self, name), name)

    def identity_payload(self) -> dict[str, str]:
        return {
            "old_unit_id": self.old_unit_id,
            "new_unit_id": self.new_unit_id,
            "old_artifact_id": self.old_artifact_id,
            "old_source_revision": self.old_source_revision,
            "source_text_hash": self.source_text_hash,
        }


@dataclass(frozen=True, slots=True)
class RevisionReusePlan:
    document_id: str
    old_source_revision: str
    new_source_revision: str
    old_plan_id: str
    new_plan_id: str
    pairs: tuple[RevisionReusePair, ...]
    invalidated_old_unit_ids: tuple[str, ...]
    pending_new_unit_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    reuse_plan_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "document_id",
            "old_source_revision",
            "new_source_revision",
            "old_plan_id",
            "new_plan_id",
        ):
            _require_text(getattr(self, name), name)
        if self.old_source_revision == self.new_source_revision:
            raise ReadingSessionError("revision reuse requires a changed revision")
        pairs = tuple(self.pairs)
        if any(not isinstance(item, RevisionReusePair) for item in pairs):
            raise ReadingSessionError("invalid revision reuse pair")
        if len({item.old_unit_id for item in pairs}) != len(pairs):
            raise ReadingSessionError("old reuse unit IDs must be unique")
        if len({item.new_unit_id for item in pairs}) != len(pairs):
            raise ReadingSessionError("new reuse unit IDs must be unique")
        invalidated = _unique_text_tuple(
            self.invalidated_old_unit_ids,
            "invalidated_old_unit_id",
        )
        pending = _unique_text_tuple(
            self.pending_new_unit_ids,
            "pending_new_unit_id",
        )
        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "pairs", pairs)
        object.__setattr__(self, "invalidated_old_unit_ids", invalidated)
        object.__setattr__(self, "pending_new_unit_ids", pending)
        object.__setattr__(self, "warnings", warnings)
        expected = stable_reader_core_id(
            "reading-session-revision-reuse-plan",
            {
                "document_id": self.document_id,
                "old_source_revision": self.old_source_revision,
                "new_source_revision": self.new_source_revision,
                "old_plan_id": self.old_plan_id,
                "new_plan_id": self.new_plan_id,
                "pairs": [item.identity_payload() for item in pairs],
                "invalidated_old_unit_ids": list(invalidated),
                "pending_new_unit_ids": list(pending),
                "warnings": list(warnings),
            },
        )
        if self.reuse_plan_id:
            if self.reuse_plan_id != expected:
                raise ReadingSessionError("reuse_plan_id does not match content")
        else:
            object.__setattr__(self, "reuse_plan_id", expected)


@dataclass(frozen=True, slots=True)
class ReadingSessionCheckpoint:
    session: ReadingSession
    checkpoint_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.session, ReadingSession):
            raise ReadingSessionError("session must be ReadingSession")
        expected = stable_reader_core_id(
            "reading-session-checkpoint",
            {
                "session_id": self.session.session_id,
                "snapshot_id": self.session.snapshot_id,
                "revision_generation": self.session.revision_generation,
                "last_receipt_id": self.session.receipts[-1].receipt_id,
            },
        )
        if self.checkpoint_id:
            if self.checkpoint_id != expected:
                raise ReadingSessionError("checkpoint_id does not match content")
        else:
            object.__setattr__(self, "checkpoint_id", expected)

    def restore(self) -> ReadingSession:
        return self.session


class ReadingSessionManager:
    manager_version = "1.0.0"

    def create(
        self,
        reading_plan: HierarchicalSectionPlan,
        *,
        session_key: str,
        resource_budget: ReadingSessionBudget | None = None,
        policy_snapshot_id: str,
        policy_version: str,
        capability_lease_ref: str | None = None,
    ) -> ReadingSession:
        if not isinstance(reading_plan, HierarchicalSectionPlan):
            raise ReadingSessionError("reading_plan must be HierarchicalSectionPlan")
        _require_text(session_key, "session_key")
        _require_text(policy_snapshot_id, "policy_snapshot_id")
        _require_text(policy_version, "policy_version")
        if capability_lease_ref is not None:
            _require_text(capability_lease_ref, "capability_lease_ref")
        budget = resource_budget or ReadingSessionBudget()
        session_key_hash = sha256(session_key.encode("utf-8")).hexdigest()
        session_id = stable_reader_core_id(
            "reading-session",
            {
                "session_key_hash": session_key_hash,
                "document_id": reading_plan.document_id,
                "source_revision": reading_plan.source_revision,
                "structure_map_id": reading_plan.structure_map_id,
                "plan_id": reading_plan.plan_id,
            },
        )
        unit_ids = tuple(unit.unit_id for unit in reading_plan.units)
        delta = ReadingSessionUsage(receipts_emitted=1)
        receipt = self._receipt(
            session_id=session_id,
            receipts=(),
            event_kind=SessionEventKind.CREATED,
            from_state=None,
            to_state=SessionState.CREATED,
            reason_code="session_created",
            affected_unit_ids=unit_ids,
            artifact_ids=(),
            usage_delta=delta,
            lease_generation=0,
        )
        return ReadingSession(
            session_id=session_id,
            manager_version=self.manager_version,
            session_key_hash=session_key_hash,
            document_id=reading_plan.document_id,
            source_revision=reading_plan.source_revision,
            structure_map_id=reading_plan.structure_map_id,
            plan_id=reading_plan.plan_id,
            state=SessionState.CREATED,
            revision_generation=0,
            all_unit_ids=unit_ids,
            pending_unit_ids=unit_ids,
            completed_unit_ids=(),
            unit_artifacts=(),
            coverage_map_id=None,
            reread_plan_id=None,
            relation_set_id=None,
            unresolved_question_refs=(),
            resource_budget=budget,
            resource_usage=delta,
            policy_snapshot_id=policy_snapshot_id,
            policy_version=policy_version,
            capability_lease_ref=capability_lease_ref,
            lease_generation=0,
            active_lease=None,
            receipts=(receipt,),
        )

    def claim(
        self,
        session: ReadingSession,
        *,
        runner_id: str,
        expires_at_ms: int,
        now_ms: int,
    ) -> ReadingSession:
        self._session(session)
        _require_text(runner_id, "runner_id")
        _positive_int(expires_at_ms, "expires_at_ms")
        _nonnegative_int(now_ms, "now_ms")
        if expires_at_ms <= now_ms:
            raise ReadingSessionError("lease expiry must be in the future")
        if session.state in {
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.CANCELLED,
        }:
            raise ReadingSessionError("terminal sessions cannot be claimed")
        if session.active_lease is not None and session.active_lease.expires_at_ms > now_ms:
            raise ReadingSessionError("session already has an unexpired lease")
        generation = session.lease_generation + 1
        lease = SessionLease(
            runner_id=runner_id,
            generation=generation,
            expires_at_ms=expires_at_ms,
        )
        delta = ReadingSessionUsage(receipts_emitted=1)
        receipt = self._receipt(
            session_id=session.session_id,
            receipts=session.receipts,
            event_kind=SessionEventKind.LEASE_CLAIMED,
            from_state=session.state,
            to_state=session.state,
            reason_code="session_lease_claimed",
            affected_unit_ids=(),
            artifact_ids=(),
            usage_delta=delta,
            lease_generation=generation,
        )
        usage = session.resource_usage.plus(delta)
        _validate_usage(usage, session.resource_budget)
        return replace(
            session,
            snapshot_id="",
            lease_generation=generation,
            active_lease=lease,
            resource_usage=usage,
            receipts=(*session.receipts, receipt),
        )

    def renew_lease(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        expires_at_ms: int,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if expires_at_ms <= max(now_ms, lease.expires_at_ms):
            raise ReadingSessionError("renewed lease must extend current expiry")
        renewed = SessionLease(
            runner_id=lease.runner_id,
            generation=lease.generation,
            expires_at_ms=expires_at_ms,
        )
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.LEASE_RENEWED,
            to_state=session.state,
            reason_code="session_lease_renewed",
            active_lease=renewed,
        )

    def start(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state not in {
            SessionState.CREATED,
            SessionState.PAUSED,
            SessionState.DEGRADED,
        }:
            raise ReadingSessionError("session cannot start from current state")
        event = (
            SessionEventKind.STARTED
            if session.state is SessionState.CREATED
            else SessionEventKind.RESUMED
        )
        reason = "session_started" if event is SessionEventKind.STARTED else "session_resumed"
        return self._simple_transition(
            session,
            event_kind=event,
            to_state=SessionState.READING,
            reason_code=reason,
        )

    def record_cards(
        self,
        session: ReadingSession,
        lease: SessionLease,
        cards: Iterable[SectionCard],
        *,
        usage_delta: ReadingSessionUsage,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state is not SessionState.READING:
            raise ReadingSessionError("cards may be recorded only while READING")
        card_tuple = tuple(cards)
        if not card_tuple:
            raise ReadingSessionError("cards must not be empty")
        if any(not isinstance(card, SectionCard) for card in card_tuple):
            raise ReadingSessionError("cards must contain SectionCard values")
        if len({card.unit_id for card in card_tuple}) != len(card_tuple):
            raise ReadingSessionError("one card per unit is allowed")
        pending = set(session.pending_unit_ids)
        cards_by_unit: dict[str, SectionCard] = {}
        for card in card_tuple:
            if (
                card.document_id != session.document_id
                or card.source_revision != session.source_revision
                or card.structure_map_id != session.structure_map_id
                or card.plan_id != session.plan_id
            ):
                raise ReadingSessionError("card identity must match session")
            if card.unit_id not in pending:
                raise ReadingSessionError("card unit must be pending")
            cards_by_unit[card.unit_id] = card
        if usage_delta.processed_units != len(card_tuple):
            raise ReadingSessionError("processed_units must equal card count")
        if usage_delta.receipts_emitted != 0:
            raise ReadingSessionError("caller delta must exclude receipt accounting")
        full_delta = usage_delta.plus(ReadingSessionUsage(receipts_emitted=1))
        usage = session.resource_usage.plus(full_delta)
        _validate_usage(usage, session.resource_budget)
        existing = {item.unit_id: item for item in session.unit_artifacts}
        for card in card_tuple:
            existing[card.unit_id] = SessionUnitArtifact(
                unit_id=card.unit_id,
                artifact_id=card.card_id,
                kind=SessionArtifactKind.CURRENT_CARD,
                artifact_source_revision=card.source_revision,
            )
        completed_set = set(session.completed_unit_ids) | set(cards_by_unit)
        completed = tuple(
            unit for unit in session.all_unit_ids if unit in completed_set
        )
        new_pending = tuple(
            unit for unit in session.all_unit_ids if unit not in completed_set
        )
        artifacts = tuple(existing[unit] for unit in completed)
        ordered_cards = tuple(
            cards_by_unit[unit]
            for unit in session.all_unit_ids
            if unit in cards_by_unit
        )
        receipt = self._receipt(
            session_id=session.session_id,
            receipts=session.receipts,
            event_kind=SessionEventKind.CARDS_RECORDED,
            from_state=session.state,
            to_state=session.state,
            reason_code="section_cards_recorded",
            affected_unit_ids=tuple(card.unit_id for card in ordered_cards),
            artifact_ids=tuple(card.card_id for card in ordered_cards),
            usage_delta=full_delta,
            lease_generation=session.lease_generation,
        )
        return replace(
            session,
            snapshot_id="",
            pending_unit_ids=new_pending,
            completed_unit_ids=completed,
            unit_artifacts=artifacts,
            resource_usage=usage,
            receipts=(*session.receipts, receipt),
        )

    def attach_artifacts(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        coverage_map_id: str | None = None,
        reread_plan_id: str | None = None,
        relation_set_id: str | None = None,
        unresolved_question_refs: Iterable[str] | None = None,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state not in {
            SessionState.READING,
            SessionState.PAUSED,
            SessionState.DEGRADED,
        }:
            raise ReadingSessionError("artifacts cannot be attached in this state")
        next_coverage = coverage_map_id or session.coverage_map_id
        next_reread = reread_plan_id or session.reread_plan_id
        next_relation = relation_set_id or session.relation_set_id
        for name, value in (
            ("coverage_map_id", next_coverage),
            ("reread_plan_id", next_reread),
            ("relation_set_id", next_relation),
        ):
            if value is not None:
                _require_text(value, name)
        questions = (
            session.unresolved_question_refs
            if unresolved_question_refs is None
            else _unique_text_tuple(
                unresolved_question_refs,
                "unresolved_question_ref",
            )
        )
        delta = ReadingSessionUsage(receipts_emitted=1)
        usage = session.resource_usage.plus(delta)
        _validate_usage(usage, session.resource_budget)
        artifact_ids = tuple(
            value
            for value in (next_coverage, next_reread, next_relation)
            if value is not None
        )
        receipt = self._receipt(
            session_id=session.session_id,
            receipts=session.receipts,
            event_kind=SessionEventKind.ARTIFACTS_ATTACHED,
            from_state=session.state,
            to_state=session.state,
            reason_code="derived_artifacts_attached",
            affected_unit_ids=(),
            artifact_ids=artifact_ids,
            usage_delta=delta,
            lease_generation=session.lease_generation,
        )
        return replace(
            session,
            snapshot_id="",
            coverage_map_id=next_coverage,
            reread_plan_id=next_reread,
            relation_set_id=next_relation,
            unresolved_question_refs=questions,
            resource_usage=usage,
            receipts=(*session.receipts, receipt),
        )

    def pause(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        reason_code: str,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state not in {SessionState.READING, SessionState.DEGRADED}:
            raise ReadingSessionError("only active sessions may be paused")
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.PAUSED,
            to_state=SessionState.PAUSED,
            reason_code=reason_code,
            active_lease=None,
        )

    def degrade(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        reason_code: str,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state is not SessionState.READING:
            raise ReadingSessionError("only READING sessions may degrade")
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.DEGRADED,
            to_state=SessionState.DEGRADED,
            reason_code=reason_code,
        )

    def complete(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state not in {SessionState.READING, SessionState.DEGRADED}:
            raise ReadingSessionError("session cannot complete from current state")
        if session.pending_unit_ids:
            raise ReadingSessionError("session cannot complete with pending units")
        if session.coverage_map_id is None:
            raise ReadingSessionError("session completion requires a CoverageMap")
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.COMPLETED,
            to_state=SessionState.COMPLETED,
            reason_code="session_completed",
            active_lease=None,
        )

    def fail(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        reason_code: str,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state in {
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.CANCELLED,
        }:
            raise ReadingSessionError("terminal session cannot fail again")
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.FAILED,
            to_state=SessionState.FAILED,
            reason_code=reason_code,
            active_lease=None,
        )

    def cancel(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        reason_code: str,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state in {
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.CANCELLED,
        }:
            raise ReadingSessionError("terminal session cannot be cancelled")
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.CANCELLED,
            to_state=SessionState.CANCELLED,
            reason_code=reason_code,
            active_lease=None,
        )

    def mark_stale(
        self,
        session: ReadingSession,
        lease: SessionLease,
        *,
        reason_code: str,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state in {SessionState.FAILED, SessionState.CANCELLED}:
            raise ReadingSessionError("failed or cancelled sessions cannot become stale")
        return self._simple_transition(
            session,
            event_kind=SessionEventKind.STALE,
            to_state=SessionState.STALE,
            reason_code=reason_code,
            active_lease=None,
        )

    def plan_revision_reuse(
        self,
        session: ReadingSession,
        old_source: RawSource,
        old_plan: HierarchicalSectionPlan,
        new_source: RawSource,
        new_plan: HierarchicalSectionPlan,
    ) -> RevisionReusePlan:
        self._session(session)
        _validate_source_plan(old_source, old_plan)
        _validate_source_plan(new_source, new_plan)
        if (
            session.document_id != old_plan.document_id
            or session.source_revision != old_plan.source_revision
            or session.plan_id != old_plan.plan_id
        ):
            raise ReadingSessionError("old plan must match session")
        if old_plan.document_id != new_plan.document_id:
            raise ReadingSessionError("revision plans must share document_id")
        if old_plan.source_revision == new_plan.source_revision:
            raise ReadingSessionError("new plan must use a changed revision")
        old_units = {unit.unit_id: unit for unit in old_plan.units}
        new_by_fingerprint = _units_by_fingerprint(new_source, new_plan.units)
        artifacts = {item.unit_id: item for item in session.unit_artifacts}
        old_by_fingerprint: dict[
            str,
            list[tuple[ReadingUnit, SessionUnitArtifact]],
        ] = {}
        for unit_id in session.completed_unit_ids:
            unit = old_units[unit_id]
            old_by_fingerprint.setdefault(
                _unit_fingerprint(old_source, unit),
                [],
            ).append((unit, artifacts[unit_id]))

        pairs: list[RevisionReusePair] = []
        ambiguous = False
        for fingerprint in sorted(old_by_fingerprint):
            old_matches = old_by_fingerprint[fingerprint]
            new_matches = new_by_fingerprint.get(fingerprint, [])
            if len(old_matches) != 1 or len(new_matches) != 1:
                if new_matches:
                    ambiguous = True
                continue
            old_unit, artifact = old_matches[0]
            new_unit = new_matches[0]
            old_text = old_source.text[old_unit.start_offset : old_unit.end_offset]
            new_text = new_source.text[new_unit.start_offset : new_unit.end_offset]
            if old_text != new_text:
                continue
            pairs.append(
                RevisionReusePair(
                    old_unit_id=old_unit.unit_id,
                    new_unit_id=new_unit.unit_id,
                    old_artifact_id=artifact.artifact_id,
                    old_source_revision=artifact.artifact_source_revision,
                    source_text_hash=old_unit.source_span.text_hash,
                )
            )
        old_reused = {item.old_unit_id for item in pairs}
        new_reused = {item.new_unit_id for item in pairs}
        invalidated = tuple(
            unit
            for unit in session.completed_unit_ids
            if unit not in old_reused
        )
        pending_new = tuple(
            unit.unit_id for unit in new_plan.units if unit.unit_id not in new_reused
        )
        warnings = (
            ("ambiguous_identical_unit_text_not_reused",) if ambiguous else ()
        )
        return RevisionReusePlan(
            document_id=session.document_id,
            old_source_revision=old_plan.source_revision,
            new_source_revision=new_plan.source_revision,
            old_plan_id=old_plan.plan_id,
            new_plan_id=new_plan.plan_id,
            pairs=tuple(pairs),
            invalidated_old_unit_ids=invalidated,
            pending_new_unit_ids=pending_new,
            warnings=warnings,
        )

    def rebase_revision(
        self,
        session: ReadingSession,
        lease: SessionLease,
        new_plan: HierarchicalSectionPlan,
        reuse_plan: RevisionReusePlan,
        *,
        policy_snapshot_id: str,
        policy_version: str,
        now_ms: int,
    ) -> ReadingSession:
        self._lease(session, lease, now_ms)
        if session.state is not SessionState.STALE:
            raise ReadingSessionError("only STALE sessions may be revision-rebased")
        if not isinstance(new_plan, HierarchicalSectionPlan):
            raise ReadingSessionError("new_plan must be HierarchicalSectionPlan")
        if not isinstance(reuse_plan, RevisionReusePlan):
            raise ReadingSessionError("reuse_plan must be RevisionReusePlan")
        if (
            reuse_plan.document_id != session.document_id
            or reuse_plan.old_source_revision != session.source_revision
            or reuse_plan.old_plan_id != session.plan_id
            or reuse_plan.new_source_revision != new_plan.source_revision
            or reuse_plan.new_plan_id != new_plan.plan_id
        ):
            raise ReadingSessionError("reuse plan does not match session and new plan")
        _require_text(policy_snapshot_id, "policy_snapshot_id")
        _require_text(policy_version, "policy_version")
        pairs = {item.new_unit_id: item for item in reuse_plan.pairs}
        all_units = tuple(unit.unit_id for unit in new_plan.units)
        completed = tuple(unit for unit in all_units if unit in pairs)
        pending = tuple(unit for unit in all_units if unit not in pairs)
        artifacts = tuple(
            SessionUnitArtifact(
                unit_id=unit,
                artifact_id=pairs[unit].old_artifact_id,
                kind=SessionArtifactKind.REUSED_CARD,
                artifact_source_revision=pairs[unit].old_source_revision,
            )
            for unit in completed
        )
        delta = ReadingSessionUsage(receipts_emitted=1)
        usage = session.resource_usage.plus(delta)
        _validate_usage(usage, session.resource_budget)
        receipt = self._receipt(
            session_id=session.session_id,
            receipts=session.receipts,
            event_kind=SessionEventKind.REVISION_REBASED,
            from_state=session.state,
            to_state=SessionState.CREATED,
            reason_code="source_revision_rebased",
            affected_unit_ids=completed,
            artifact_ids=tuple(item.artifact_id for item in artifacts),
            usage_delta=delta,
            lease_generation=session.lease_generation,
        )
        return replace(
            session,
            snapshot_id="",
            document_id=new_plan.document_id,
            source_revision=new_plan.source_revision,
            structure_map_id=new_plan.structure_map_id,
            plan_id=new_plan.plan_id,
            state=SessionState.CREATED,
            revision_generation=session.revision_generation + 1,
            all_unit_ids=all_units,
            pending_unit_ids=pending,
            completed_unit_ids=completed,
            unit_artifacts=artifacts,
            coverage_map_id=None,
            reread_plan_id=None,
            relation_set_id=None,
            unresolved_question_refs=(),
            resource_usage=usage,
            policy_snapshot_id=policy_snapshot_id,
            policy_version=policy_version,
            receipts=(*session.receipts, receipt),
            warnings=tuple(dict.fromkeys((*session.warnings, *reuse_plan.warnings))),
        )

    @staticmethod
    def checkpoint(session: ReadingSession) -> ReadingSessionCheckpoint:
        return ReadingSessionCheckpoint(session=session)

    def _simple_transition(
        self,
        session: ReadingSession,
        *,
        event_kind: SessionEventKind,
        to_state: SessionState,
        reason_code: str,
        active_lease: SessionLease | None | object = ..., 
    ) -> ReadingSession:
        _require_text(reason_code, "reason_code")
        delta = ReadingSessionUsage(receipts_emitted=1)
        usage = session.resource_usage.plus(delta)
        _validate_usage(usage, session.resource_budget)
        receipt = self._receipt(
            session_id=session.session_id,
            receipts=session.receipts,
            event_kind=event_kind,
            from_state=session.state,
            to_state=to_state,
            reason_code=reason_code,
            affected_unit_ids=(),
            artifact_ids=(),
            usage_delta=delta,
            lease_generation=session.lease_generation,
        )
        next_lease = session.active_lease if active_lease is ... else active_lease
        if next_lease is not None and not isinstance(next_lease, SessionLease):
            raise ReadingSessionError("active_lease must be SessionLease or None")
        return replace(
            session,
            snapshot_id="",
            state=to_state,
            active_lease=next_lease,
            resource_usage=usage,
            receipts=(*session.receipts, receipt),
        )

    @staticmethod
    def _receipt(
        *,
        session_id: str,
        receipts: tuple[ReadingSessionReceipt, ...],
        event_kind: SessionEventKind,
        from_state: SessionState | None,
        to_state: SessionState,
        reason_code: str,
        affected_unit_ids: tuple[str, ...],
        artifact_ids: tuple[str, ...],
        usage_delta: ReadingSessionUsage,
        lease_generation: int,
    ) -> ReadingSessionReceipt:
        return ReadingSessionReceipt(
            session_id=session_id,
            sequence=len(receipts),
            previous_receipt_id=(receipts[-1].receipt_id if receipts else None),
            event_kind=event_kind,
            from_state=from_state,
            to_state=to_state,
            reason_code=reason_code,
            affected_unit_ids=affected_unit_ids,
            artifact_ids=artifact_ids,
            usage_delta=usage_delta,
            lease_generation=lease_generation,
        )

    @staticmethod
    def _session(session: ReadingSession) -> None:
        if not isinstance(session, ReadingSession):
            raise ReadingSessionError("session must be ReadingSession")

    def _lease(
        self,
        session: ReadingSession,
        lease: SessionLease,
        now_ms: int,
    ) -> None:
        self._session(session)
        if not isinstance(lease, SessionLease):
            raise ReadingSessionError("lease must be SessionLease")
        _nonnegative_int(now_ms, "now_ms")
        if session.active_lease is None:
            raise ReadingSessionError("session has no active lease")
        if lease != session.active_lease:
            raise ReadingSessionError("lease does not own this session snapshot")
        if lease.generation != session.lease_generation:
            raise ReadingSessionError("lease fencing generation mismatch")
        if lease.expires_at_ms <= now_ms:
            raise ReadingSessionError("session lease has expired")


def _session_snapshot_id(session: ReadingSession) -> str:
    return stable_reader_core_id(
        "reading-session-snapshot",
        {
            "schema_version": session.schema_version,
            "session_id": session.session_id,
            "manager_version": session.manager_version,
            "session_key_hash": session.session_key_hash,
            "document_id": session.document_id,
            "source_revision": session.source_revision,
            "structure_map_id": session.structure_map_id,
            "plan_id": session.plan_id,
            "state": session.state.value,
            "revision_generation": session.revision_generation,
            "all_unit_ids": list(session.all_unit_ids),
            "pending_unit_ids": list(session.pending_unit_ids),
            "completed_unit_ids": list(session.completed_unit_ids),
            "unit_artifacts": [
                item.identity_payload() for item in session.unit_artifacts
            ],
            "coverage_map_id": session.coverage_map_id,
            "reread_plan_id": session.reread_plan_id,
            "relation_set_id": session.relation_set_id,
            "unresolved_question_refs": list(session.unresolved_question_refs),
            "resource_budget": session.resource_budget.identity_payload(),
            "resource_usage": session.resource_usage.identity_payload(),
            "policy_snapshot_id": session.policy_snapshot_id,
            "policy_version": session.policy_version,
            "capability_lease_ref": session.capability_lease_ref,
            "lease_generation": session.lease_generation,
            "active_lease": (
                session.active_lease.identity_payload()
                if session.active_lease is not None
                else None
            ),
            "receipt_ids": [item.receipt_id for item in session.receipts],
            "warnings": list(session.warnings),
        },
    )


def _validate_usage(
    usage: ReadingSessionUsage,
    budget: ReadingSessionBudget,
) -> None:
    checks = (
        (usage.processed_units, budget.max_processed_units, "processed units"),
        (usage.source_chars, budget.max_source_chars, "source characters"),
        (usage.model_tokens, budget.max_model_tokens, "model tokens"),
        (usage.wall_time_ms, budget.max_wall_time_ms, "wall time"),
        (usage.receipts_emitted, budget.max_receipts, "receipts"),
    )
    for actual, maximum, label in checks:
        if actual > maximum:
            raise ReadingSessionBudgetExceeded(
                f"session {label} budget would be exceeded"
            )


def _validate_source_plan(
    source: RawSource,
    plan: HierarchicalSectionPlan,
) -> None:
    if not isinstance(source, RawSource):
        raise ReadingSessionError("source must be RawSource")
    if not isinstance(plan, HierarchicalSectionPlan):
        raise ReadingSessionError("plan must be HierarchicalSectionPlan")
    revision = source.source_revision
    if revision is None:
        revision = f"sha256:{sha256(source.text.encode('utf-8')).hexdigest()}"
    if source.document_id != plan.document_id:
        raise ReadingSessionError("source document_id must match plan")
    if revision != plan.source_revision:
        raise ReadingSessionError("source revision must match plan")
    for unit in plan.units:
        if not unit.source_span.verify(source.text):
            raise ReadingSessionError("plan unit span must verify against source")


def _units_by_fingerprint(
    source: RawSource,
    units: tuple[ReadingUnit, ...],
) -> dict[str, list[ReadingUnit]]:
    result: dict[str, list[ReadingUnit]] = {}
    for unit in units:
        result.setdefault(_unit_fingerprint(source, unit), []).append(unit)
    return result


def _unit_fingerprint(source: RawSource, unit: ReadingUnit) -> str:
    text = source.text[unit.start_offset : unit.end_offset]
    return stable_reader_core_id(
        "reading-session-unit-fingerprint",
        {
            "text_hash": unit.source_span.text_hash,
            "char_count": unit.char_count,
            "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
        },
    )


def _positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ReadingSessionError(f"{field_name} must be a positive integer")
    return value


def _nonnegative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReadingSessionError(f"{field_name} must be an integer >= 0")
    return value


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReadingSessionError(f"{field_name} must be a non-empty string")
    return value


def _unique_text_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise ReadingSessionError(f"{field_name} values must be unique")
    return result


__all__ = [
    "READING_SESSION_SCHEMA_VERSION",
    "ReadingSession",
    "ReadingSessionBudget",
    "ReadingSessionBudgetExceeded",
    "ReadingSessionCheckpoint",
    "ReadingSessionError",
    "ReadingSessionManager",
    "ReadingSessionReceipt",
    "ReadingSessionUsage",
    "RevisionReusePair",
    "RevisionReusePlan",
    "SessionArtifactKind",
    "SessionEventKind",
    "SessionLease",
    "SessionUnitArtifact",
]
