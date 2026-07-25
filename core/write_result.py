# core/write_result.py
# PR-C1 — explicit, structured write outcome.
#
# store_fact() (core/memory.py) has always returned a plain bool: True for a
# genuine new INSERT, False for everything else — no-op-existing, a real
# update of an existing fact, and WriteProtocolGate rejection all collapse
# to the same False. Callers that discard this bool (or discard it after
# capturing it) have historically reported success to the client even when
# nothing durable was written (see PR-C1 evidence report).
#
# WriteResult/WriteStatus is an explicit, non-boolean-coercible alternative
# for call sites that need to react differently to each outcome. It is
# additive: store_fact()'s own bool contract is unchanged (see
# core/memory.py::SQLiteGraphStore.store_fact / store_fact_result).
#
# Deliberately no __bool__ — a caller must write `result.status is
# WriteStatus.CREATED`, not `if result:`. An implicit truthy/falsy reading
# would silently re-collapse CREATED/UPDATED/NOOP_EXISTING/REJECTED_* into
# the same ambiguity this module exists to remove.
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WriteStatus(Enum):
    """Outcome of a single store_fact_result() call."""

    CREATED = "created"
    UPDATED = "updated"
    NOOP_EXISTING = "noop_existing"
    REJECTED_WRITE_GATE = "rejected_write_gate"
    REJECTED_SAFE_MODE = "rejected_safe_mode"
    REJECTED_BUDGET = "rejected_budget"
    REJECTED_VALIDATION = "rejected_validation"
    FAILED_STORAGE = "failed_storage"
    FAILED_INTERNAL = "failed_internal"


# Statuses for which a canonical `facts` row exists after the call returns.
# NOTE: this is NOT the same question as "did THIS call's write get
# accepted?" — see ACCEPTED_WRITE_STATUSES below. A rejection of a write to
# an *existing* fact_id (e.g. REJECTED_WRITE_GATE on an update attempt)
# leaves a stale-but-real canonical row in place: WriteResult.canonical_exists
# is True for that call even though the call itself was rejected. Do not use
# `result.canonical_exists` as a proxy for "this write succeeded".
CANONICAL_EXISTS_STATUSES = frozenset((
    WriteStatus.CREATED,
    WriteStatus.UPDATED,
    WriteStatus.NOOP_EXISTING,
))

# Statuses for which this call performed a durable SQL write (INSERT/UPDATE).
DURABLE_WRITE_STATUSES = frozenset((
    WriteStatus.CREATED,
    WriteStatus.UPDATED,
))

# PR-C1 hardening: statuses for which THIS call's write attempt was accepted
# (as opposed to rejected/failed). Use `result.status in ACCEPTED_WRITE_STATUSES`
# to gate provenance linking, event emission, and "promoted"/"created"
# side effects — never `result.canonical_exists`, which can be True on a
# rejected call to an existing fact_id (see CANONICAL_EXISTS_STATUSES above).
ACCEPTED_WRITE_STATUSES = frozenset((
    WriteStatus.CREATED,
    WriteStatus.UPDATED,
    WriteStatus.NOOP_EXISTING,
))


@dataclass(frozen=True)
class WriteResult:
    """Structured outcome of a write attempt.

    Client-facing fields are limited to `safe_reason_code` / `safe_message`
    — never populate these (or log them upstream) with a traceback, raw SQL,
    an absolute path, a secret, or the verbatim text of an internal
    exception. Full exception detail belongs in the server-side log only.
    """

    status: WriteStatus
    fact_id: str | None
    created: bool
    canonical_exists: bool
    durable_write: bool
    safe_reason_code: str | None = None
    safe_message: str | None = None
