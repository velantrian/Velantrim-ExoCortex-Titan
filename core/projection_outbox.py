"""Content-minimized transactional projection-outbox foundation.

This module deliberately owns no Canon mutation, projection application,
worker, retry loop, scheduler, network call or commit boundary. A caller that
already owns a SQLite transaction may append one immutable projection intent
through :func:`append_projection_intent_in_transaction`.

The first foundation increment is not runtime-wired. Delivery state and
claim/lease semantics belong to a later, independently reviewed dispatcher
layer rather than this immutable intent table.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Final

PROJECTION_OUTBOX_POLICY_VERSION: Final = "projection-outbox-v1"
_ALLOWED_AGGREGATE_TYPE: Final = "fact"
_TECHNICAL_ID = re.compile(r"^[A-Za-z0-9_.:/-]{1,256}$")
_SCOPE_REF = re.compile(r"^[A-Za-z0-9_.:/-]{1,128}$")
_POLICY_CODE = re.compile(r"^[a-z0-9_.:-]{1,64}$")


class ProjectionOutboxContractError(RuntimeError):
    """The caller or durable row violated the v1 outbox contract."""


class ProjectionKind(StrEnum):
    """Rebuildable projection families addressed by an intent."""

    ALL = "all"
    FTS = "fts"
    GRAPH = "graph"
    VECTOR = "vector"


class ProjectionOperation(StrEnum):
    """Closed v1 operations; neither operation mutates Canon."""

    REFRESH = "refresh"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class ProjectionIntent:
    """One immutable, content-free instruction for a later local projector."""

    aggregate_id: str
    scope_ref: str
    canonical_version: int
    projection_kind: ProjectionKind = ProjectionKind.ALL
    operation: ProjectionOperation = ProjectionOperation.REFRESH
    aggregate_type: str = _ALLOWED_AGGREGATE_TYPE
    policy_version: str = PROJECTION_OUTBOX_POLICY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.aggregate_id, str) or not _TECHNICAL_ID.fullmatch(
            self.aggregate_id
        ):
            raise ValueError("ProjectionIntent.aggregate_id is not a safe identifier")
        if not isinstance(self.scope_ref, str) or not _SCOPE_REF.fullmatch(
            self.scope_ref
        ):
            raise ValueError("ProjectionIntent.scope_ref is not a safe scope reference")
        if (
            not isinstance(self.canonical_version, int)
            or isinstance(self.canonical_version, bool)
            or self.canonical_version < 0
        ):
            raise ValueError("ProjectionIntent.canonical_version must be >= 0")
        if not isinstance(self.projection_kind, ProjectionKind):
            raise TypeError("ProjectionIntent.projection_kind must be ProjectionKind")
        if not isinstance(self.operation, ProjectionOperation):
            raise TypeError("ProjectionIntent.operation must be ProjectionOperation")
        if self.aggregate_type != _ALLOWED_AGGREGATE_TYPE:
            raise ValueError("Projection outbox v1 supports only fact aggregates")
        if (
            not isinstance(self.policy_version, str)
            or not _POLICY_CODE.fullmatch(self.policy_version)
            or self.policy_version != PROJECTION_OUTBOX_POLICY_VERSION
        ):
            raise ValueError("ProjectionIntent.policy_version is not supported")

    @property
    def outbox_id(self) -> str:
        """Deterministic semantic id; creation time is intentionally excluded."""
        canonical = json.dumps(
            {
                "aggregate_id": self.aggregate_id,
                "aggregate_type": self.aggregate_type,
                "canonical_version": self.canonical_version,
                "operation": self.operation.value,
                "policy_version": self.policy_version,
                "projection_kind": self.projection_kind.value,
                "scope_ref": self.scope_ref,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"projection_{hashlib.sha256(canonical).hexdigest()[:32]}"


@dataclass(frozen=True, slots=True)
class ProjectionAppendReceipt:
    """Immediate append result; it is not a delivery acknowledgement."""

    outbox_id: str
    inserted: bool
    idempotent: bool


def append_projection_intent_in_transaction(
    conn: sqlite3.Connection,
    intent: ProjectionIntent,
    *,
    created_at: str | None = None,
) -> ProjectionAppendReceipt:
    """Append one intent using the caller-owned active SQLite transaction.

    No commit, rollback, retry, dispatch or projection mutation occurs here.
    An exact duplicate is an idempotent no-op. A hash collision or durable row
    mismatch fails closed so the caller can roll back its whole transaction.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise TypeError("conn must be sqlite3.Connection")
    if not conn.in_transaction:
        raise ProjectionOutboxContractError(
            "projection outbox append requires an active caller-owned transaction"
        )

    created = created_at or datetime.now(UTC).isoformat()
    if not isinstance(created, str) or not created:
        raise ValueError("created_at must be a non-empty string")

    semantic_values = (
        intent.aggregate_type,
        intent.aggregate_id,
        intent.scope_ref,
        intent.projection_kind.value,
        intent.operation.value,
        intent.canonical_version,
        intent.policy_version,
    )
    cursor = conn.execute(
        "INSERT INTO projection_outbox ("
        "outbox_id, aggregate_type, aggregate_id, scope_ref, projection_kind, "
        "operation, canonical_version, policy_version, created_at"
        ") VALUES (?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(outbox_id) DO NOTHING",
        (intent.outbox_id, *semantic_values, created),
    )
    if cursor.rowcount == 1:
        return ProjectionAppendReceipt(
            outbox_id=intent.outbox_id,
            inserted=True,
            idempotent=False,
        )

    row = conn.execute(
        "SELECT aggregate_type, aggregate_id, scope_ref, projection_kind, "
        "operation, canonical_version, policy_version "
        "FROM projection_outbox WHERE outbox_id = ?",
        (intent.outbox_id,),
    ).fetchone()
    if row is None or tuple(row) != semantic_values:
        raise ProjectionOutboxContractError(
            "projection outbox id collision or durable semantic mismatch"
        )
    return ProjectionAppendReceipt(
        outbox_id=intent.outbox_id,
        inserted=False,
        idempotent=True,
    )


__all__ = [
    "PROJECTION_OUTBOX_POLICY_VERSION",
    "ProjectionAppendReceipt",
    "ProjectionIntent",
    "ProjectionKind",
    "ProjectionOperation",
    "ProjectionOutboxContractError",
    "append_projection_intent_in_transaction",
]
