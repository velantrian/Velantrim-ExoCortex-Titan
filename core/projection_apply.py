"""Projection policy v1 and version-monotonic FTS apply contract (issue #194).

Resolves two of issue #193's Phase 0 blockers before any dispatcher lease/
retry/ack state machine exists: `ProjectionKind.ALL` had no executable
interpretation, and no projection target stored a version to compare
against, so nothing prevented an older/redelivered intent from regressing a
newer projection.

This module deliberately owns no dispatcher claim/lease/retry/ack, no
background worker or scheduler, and no Canon mutation. `apply_fts_projection()`
is a plain function: it accepts a caller-owned, already-open SQLite
connection/transaction and never calls ``commit``/``rollback`` itself — the
caller (today: tests; later: issue #193's dispatcher) decides the
transaction boundary. Content is never taken from the outbox intent —
every apply re-reads `claim`/`source` fresh from `facts` at apply time.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from core.projection_outbox import (
    LOCAL_PROJECTION_SCOPE_REF,
    PROJECTION_OUTBOX_POLICY_VERSION,
    ProjectionKind,
)

#: The only policy version this module currently interprets — the SAME
#: durable value every ProjectionIntent's own `policy_version` field
#: already carries (core.projection_outbox.PROJECTION_OUTBOX_POLICY_VERSION),
#: not a separate ad-hoc label. A future policy v2 (e.g. activating
#: graph/vector) requires its own reviewed resolver branch and its own
#: new PROJECTION_OUTBOX_POLICY_VERSION-shaped constant, never a widening
#: of this one in place. (Review finding, PR #195: an earlier revision
#: compared against a disconnected literal "v1" that no real intent's
#: policy_version would ever equal, making the resolver unreachable from
#: any actual dispatcher call.)
_POLICY_V1 = PROJECTION_OUTBOX_POLICY_VERSION

#: Policy v1's closed target set for ProjectionKind.ALL — "all targets
#: defined by projection policy v1", not every reserved enum value. Graph
#: and vector are not members because no fact-addressable, idempotent,
#: version-monotonic local apply/remove primitive exists for them yet.
_POLICY_V1_TARGETS: dict[ProjectionKind, tuple[ProjectionKind, ...]] = {
    ProjectionKind.ALL: (ProjectionKind.FTS,),
    ProjectionKind.FTS: (ProjectionKind.FTS,),
}


class UnsupportedPolicyTargetError(RuntimeError):
    """Raised by resolve_projection_targets() for any (policy_version,
    projection_kind) pair policy v1 does not define — an unknown
    policy_version, or an explicit GRAPH/VECTOR request under v1. Never a
    silent skip and never treated as delivered/acknowledged: raising here
    means the caller has nothing it can safely act on."""


class ProjectionApplyContractError(RuntimeError):
    """Raised by apply_fts_projection() when `conn` has no active
    transaction. Without an explicit BEGIN, sqlite3 autocommits each
    statement individually — the checkpoint UPSERT and the FTS write would
    no longer be atomic, so a failure between them could leave the
    checkpoint advanced with no matching FTS content. Fails closed instead
    (review finding, PR #195), mirroring
    core.projection_outbox.append_projection_intent_in_transaction()'s own
    `conn.in_transaction` guard."""


class CanonVersionBehindIntentError(RuntimeError):
    """Fail-closed: apply_fts_projection() found Canon's current
    facts.fact_version behind the intent's own claimed canonical_version —
    a durable inconsistency (an intent should never claim a version Canon
    has not yet reached), never partially applied."""


class ProjectionApplyOutcome(StrEnum):
    """Closed outcome set for apply_fts_projection()."""

    #: FTS content and checkpoint now reflect the current Canon row, at
    #: the current Canon row's own fact_version (which may be higher than
    #: the intent's own canonical_version — see the current-Canon rule).
    APPLIED = "applied"
    #: Canon no longer has this fact_id — any FTS row and checkpoint were
    #: removed. Never resurrects data; a REMOVE-shaped outcome regardless
    #: of the intent's own `operation`.
    MISSING_CANON_REMOVED = "missing_canon_removed"
    #: facts_fts does not exist in this database (missing table, or the
    #: SQLite build lacks FTS5). No checkpoint was written — a future
    #: dispatcher must never acknowledge this as delivered.
    FTS_UNAVAILABLE = "fts_unavailable"


@dataclass(frozen=True, slots=True)
class ProjectionApplyResult:
    """Closed, structured outcome of one apply_fts_projection() call."""

    outcome: ProjectionApplyOutcome
    fact_id: str
    applied_canonical_version: int | None


def resolve_projection_targets(
    policy_version: str, projection_kind: ProjectionKind,
) -> tuple[ProjectionKind, ...]:
    """Deterministic, policy_version-only expansion of `projection_kind`
    into the concrete targets to apply. No environment variable, feature
    flag, or runtime configuration is ever consulted — the target set is a
    pure function of the durable intent's own two fields."""
    if policy_version != _POLICY_V1:
        raise UnsupportedPolicyTargetError(
            f"policy_version {policy_version!r} is not defined by this "
            "resolver — never silently skipped, never delivered"
        )
    targets = _POLICY_V1_TARGETS.get(projection_kind)
    if targets is None:
        raise UnsupportedPolicyTargetError(
            f"projection_kind {projection_kind!r} is not a member of "
            f"policy {policy_version!r} — parked, never acknowledged as "
            "delivered, never silently ignored"
        )
    return targets


# ── A. Low-level FTS SQL helpers — no transaction management, no policy
#      logic. Shared verbatim by core/memory.py's pre-existing best-effort
#      store_fact()/supersede_fact_cas() sync sites and by this module's
#      own strict apply_fts_projection() below. ──────────────────────────

def upsert_fts_row(conn: sqlite3.Connection, fact_id: str, claim: str, source: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO facts_fts(rowid, fact_id, claim, source) "
        "VALUES ((SELECT rowid FROM facts WHERE fact_id=?), ?, ?, ?)",
        (fact_id, fact_id, claim, source),
    )


def remove_fts_row(conn: sqlite3.Connection, fact_id: str) -> None:
    conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))


def _facts_fts_available(conn: sqlite3.Connection) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'facts_fts'",
    ).fetchone() is not None


def _remove_checkpoint(conn: sqlite3.Connection, fact_id: str) -> None:
    conn.execute(
        "DELETE FROM projection_checkpoints WHERE aggregate_type = 'fact' "
        "AND aggregate_id = ? AND scope_ref = ? AND projection_kind = 'fts'",
        (fact_id, LOCAL_PROJECTION_SCOPE_REF),
    )


def _upsert_checkpoint_monotonic(conn: sqlite3.Connection, fact_id: str, version: int) -> int:
    """Insert-or-advance the checkpoint to `version`, never regressing an
    already-higher stored value — an explicit UPSERT ... WHERE monotonic
    guard, not a plain INSERT OR REPLACE. Returns the checkpoint's actual
    final value after the attempt (== `version` if this call's write won
    or tied; higher if a concurrent/earlier writer already advanced past
    `version`)."""
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO projection_checkpoints "
        "(aggregate_type, aggregate_id, scope_ref, projection_kind, "
        "applied_canonical_version, updated_at) "
        "VALUES ('fact', ?, ?, 'fts', ?, ?) "
        "ON CONFLICT(aggregate_type, aggregate_id, scope_ref, projection_kind) "
        "DO UPDATE SET applied_canonical_version = excluded.applied_canonical_version, "
        "updated_at = excluded.updated_at "
        "WHERE excluded.applied_canonical_version > projection_checkpoints.applied_canonical_version",
        (fact_id, LOCAL_PROJECTION_SCOPE_REF, version, now),
    )
    row = conn.execute(
        "SELECT applied_canonical_version FROM projection_checkpoints "
        "WHERE aggregate_type = 'fact' AND aggregate_id = ? "
        "AND scope_ref = ? AND projection_kind = 'fts'",
        (fact_id, LOCAL_PROJECTION_SCOPE_REF),
    ).fetchone()
    return row[0]


# ── B. Strict projection-apply helper — Canon/version/policy aware. ────────

def apply_fts_projection(
    conn: sqlite3.Connection, *, fact_id: str, intent_canonical_version: int,
) -> ProjectionApplyResult:
    """Apply one FTS refresh for `fact_id`, strictly against CURRENT Canon
    (never the intent's own captured content), never regressing a
    checkpoint already at or beyond the version this call would write.

    Does not commit, rollback, retry, sleep, or make any network call.
    Does not mutate Canon. Raises CanonVersionBehindIntentError (fail
    closed, no partial write) if Canon's current fact_version is behind
    `intent_canonical_version` — a durable inconsistency the caller's own
    transaction must roll back whole.
    """
    if not conn.in_transaction:
        raise ProjectionApplyContractError(
            "apply_fts_projection requires an active caller-owned transaction"
        )

    if not _facts_fts_available(conn):
        return ProjectionApplyResult(ProjectionApplyOutcome.FTS_UNAVAILABLE, fact_id, None)

    canon_row = conn.execute(
        "SELECT fact_version, claim, source FROM facts WHERE fact_id = ?", (fact_id,),
    ).fetchone()

    if canon_row is None:
        remove_fts_row(conn, fact_id)
        _remove_checkpoint(conn, fact_id)
        return ProjectionApplyResult(ProjectionApplyOutcome.MISSING_CANON_REMOVED, fact_id, None)

    current_version, claim, source = canon_row
    if current_version < intent_canonical_version:
        raise CanonVersionBehindIntentError(
            f"fact '{fact_id}': Canon fact_version={current_version} is "
            f"behind intent canonical_version={intent_canonical_version}"
        )

    final_version = _upsert_checkpoint_monotonic(conn, fact_id, current_version)
    if final_version == current_version:
        # This call's own fresh Canon read is the (tied-for-)newest —
        # safe to write. If final_version is higher, a concurrent/earlier
        # writer already advanced past what this call read; its own
        # (now-stale) content must never overwrite that newer state.
        upsert_fts_row(conn, fact_id, claim, source)

    return ProjectionApplyResult(ProjectionApplyOutcome.APPLIED, fact_id, final_version)


__all__ = [
    "CanonVersionBehindIntentError",
    "ProjectionApplyContractError",
    "ProjectionApplyOutcome",
    "ProjectionApplyResult",
    "UnsupportedPolicyTargetError",
    "apply_fts_projection",
    "remove_fts_row",
    "resolve_projection_targets",
    "upsert_fts_row",
]
