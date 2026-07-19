"""
🔗 core/audit_chain.py — Append-only Audit Log с Hash-Chain (v2)
==================================================================
Каждое событие связано с предыдущим через SHA256 хэш.
Подделка любого события математически обнаруживается при verify_chain().

Принцип: как блокчейн, только для памяти AI-агента.

Hash v2 (default for all new events): a versioned canonical JSON envelope
committing to EVERY durable field (including event_id, reason, confidence,
chain_id, chain_sequence) — see canonicalize_audit_event_v2().

Hash v1 (legacy, read-only): the original pipe-delimited algorithm,
reproduced verbatim in compute_audit_hash_v1() so existing v1 rows can
still be verified. New events are never written with v1.

A DB may contain an interleaved v1 → v1 → v2 → v2 chain (the moment the
schema upgrades); verify_chain() dispatches per-row on the stored
hash_version and validates the whole thing as one linear sequence.

Sprint 1a — Этап A3
Stage B — AuditChain Hash v2
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
import uuid
from datetime import UTC, datetime

# ── Типы событий ──────────────────────────────────────────────────────────────

class EventType:
    FACT_CREATED              = "fact_created"
    FACT_UPDATED              = "fact_updated"
    ESM_TRANSITION            = "esm_transition"
    FACT_DEPRECATED           = "fact_deprecated"
    FACT_COLLAPSED            = "fact_collapsed"
    TRUTH_GATE_VERDICT        = "truth_gate_verdict"
    OBSERVER_VERDICT          = "observer_verdict"
    IMMUTABLE_ATTEMPT_BLOCKED = "immutable_attempt_blocked"
    AUDIT_VERIFY              = "audit_verify"
    CACHE_INVALIDATED         = "cache_invalidated"
    INTEGRITY_CHECK           = "integrity_check"


GENESIS_BLOCK = "VELANTRIM_GENESIS_BLOCK"
HASH_DOMAIN = "velantrim.audit.event"
HASH_VERSION_LEGACY = 1
HASH_VERSION_CURRENT = 2
DEFAULT_CHAIN_ID = "memory_events"

# Documented safe upper bound for verify_chain(max_rows=...) — protects
# against unbounded scans; callers needing more must page explicitly.
MAX_VERIFY_ROWS = 1_000_000


class AuditChainError(ValueError):
    """Invalid/malformed audit data that must fail closed (never coerced)."""


class _StaleHeadError(RuntimeError):
    """Internal: the chain head advanced between our read and our
    CAS-guarded update. Retried by AuditChain.log() only when it owns the
    transaction — never retried when participating in a caller's
    transaction, since that would require redoing work we don't own."""


def _sorted_versions(versions: set) -> list:
    """Sort a set of stored hash_version values for a report. Normally
    all ints, sorted numerically — but a tampered row can carry ANY
    stored value (that's the whole point of a hash chain: a tamperer
    doesn't ask permission), so a plain `sorted()` would raise TypeError
    on a set mixing e.g. an int and a str, crashing verify_chain() before
    it can record the failed-verification receipt it owes. Fall back to
    sorting by repr() so reporting never crashes, whatever's actually
    stored."""
    try:
        return sorted(versions)
    except TypeError:
        return sorted(versions, key=repr)


# ── Canonicalization & validation helpers ─────────────────────────────────────

def _validate_payload_value(value: object, *, _depth: int = 0) -> None:
    if _depth > 64:
        raise AuditChainError("payload nesting too deep")
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AuditChainError(f"payload contains non-finite float: {value!r}")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise AuditChainError(f"payload dict keys must be strings, got {type(k)!r}")
            _validate_payload_value(v, _depth=_depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_payload_value(item, _depth=_depth + 1)
        return
    raise AuditChainError(f"payload contains unsupported type: {type(value)!r}")


def validate_payload(payload: dict | None) -> dict:
    """Validate a payload dict is JSON-safe & finite. Fails closed on
    non-string keys, NaN/±Infinity, bytes, sets, or other custom objects."""
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise AuditChainError(f"payload must be a dict, got {type(payload)!r}")
    _validate_payload_value(payload)
    return payload


def validate_confidence(confidence: object) -> float | None:
    """confidence must be None or a finite numeric — never a bool, never
    NaN/±Infinity."""
    if confidence is None:
        return None
    if isinstance(confidence, bool):
        raise AuditChainError("confidence must not be a bool")
    if not isinstance(confidence, (int, float)):
        raise AuditChainError(f"confidence must be numeric, got {type(confidence)!r}")
    value = float(confidence)
    if not math.isfinite(value):
        raise AuditChainError(f"confidence must be finite, got {confidence!r}")
    return value


def canonicalize_audit_event_v2(
    *,
    chain_id: str,
    chain_sequence: int,
    event_id: str,
    event_type: str,
    fact_id: str | None,
    from_state: str | None,
    to_state: str | None,
    actor: str,
    reason: str | None,
    payload: dict | None,
    confidence: float | None,
    prev_event_hash: str | None,
    created_at: str,
) -> bytes:
    """Build the canonical JSON envelope bytes hashed for hash v2.

    Deterministic: sorted keys, compact separators, no ASCII escaping, no
    NaN/Infinity (allow_nan=False raises rather than silently emitting
    non-JSON `NaN`/`Infinity` tokens). Domain-separated via an embedded
    `domain` field plus an explicit `hash_version` — never delimiter
    concatenation, never repr(), never a DB rowid.
    """
    validated_payload = validate_payload(payload)
    validated_confidence = validate_confidence(confidence)

    envelope = {
        "domain": HASH_DOMAIN,
        "hash_version": HASH_VERSION_CURRENT,
        "chain_id": chain_id,
        "chain_sequence": chain_sequence,
        "event_id": event_id,
        "event_type": event_type,
        "fact_id": fact_id,
        "from_state": from_state,
        "to_state": to_state,
        "actor": actor,
        "reason": reason,
        "payload": validated_payload,
        "confidence": validated_confidence,
        "prev_event_hash": prev_event_hash or GENESIS_BLOCK,
        "created_at": created_at,
    }
    return json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def compute_audit_hash_v2(
    *,
    chain_id: str,
    chain_sequence: int,
    event_id: str,
    event_type: str,
    fact_id: str | None,
    from_state: str | None,
    to_state: str | None,
    actor: str,
    reason: str | None,
    payload: dict | None,
    confidence: float | None,
    prev_event_hash: str | None,
    created_at: str,
) -> str:
    data = canonicalize_audit_event_v2(
        chain_id=chain_id, chain_sequence=chain_sequence, event_id=event_id,
        event_type=event_type, fact_id=fact_id, from_state=from_state,
        to_state=to_state, actor=actor, reason=reason, payload=payload,
        confidence=confidence, prev_event_hash=prev_event_hash,
        created_at=created_at,
    )
    return hashlib.sha256(data).hexdigest()


def compute_audit_hash_v1(
    *,
    event_type: str,
    fact_id: str | None,
    from_state: str | None,
    to_state: str | None,
    actor: str,
    payload: dict | None,
    created_at: str,
    prev_event_hash: str | None,
) -> str:
    """The EXACT historical v1 algorithm, reproduced verbatim — never
    "improved". Required to verify pre-existing v1 rows byte-for-byte.

    SHA256(prev_hash|event_type|fact_id|from_state|to_state|actor
           |payload_json|created_at)
    """
    prev = prev_event_hash or GENESIS_BLOCK
    payload_str = json.dumps(payload or {}, sort_keys=True, ensure_ascii=False)
    data = "|".join([
        prev, event_type, fact_id or "", from_state or "",
        to_state or "", actor, payload_str, created_at,
    ])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ── AuditEvent ────────────────────────────────────────────────────────────────

class AuditEvent:
    """Одно событие в цепочке памяти.

    Hashing is a pure function of the constructor arguments — no reliance
    on mutable state after construction. New events default to hash
    version 2 and require a `chain_sequence` (allocated atomically by
    AuditChain.log()). hash_version=1 exists only so tests/tools can
    construct a byte-identical legacy event for compatibility fixtures;
    AuditChain.log() never produces one itself.
    """

    def __init__(
        self,
        event_type:      str,
        actor:           str,
        fact_id:         str | None = None,
        from_state:      str | None = None,
        to_state:        str | None = None,
        reason:          str | None = None,
        payload:         dict | None = None,
        confidence:      float | None = None,
        prev_event_hash: str | None = None,
        *,
        hash_version:    int = HASH_VERSION_CURRENT,
        chain_id:        str = DEFAULT_CHAIN_ID,
        chain_sequence:  int | None = None,
        event_id:        str | None = None,
        created_at:      str | None = None,
    ) -> None:
        self.event_id        = event_id or f"evt_{uuid.uuid4().hex[:16]}"
        self.event_type      = event_type
        self.fact_id         = fact_id
        self.from_state      = from_state
        self.to_state        = to_state
        self.actor           = actor
        self.reason          = reason
        self.payload         = validate_payload(payload)
        self.confidence      = validate_confidence(confidence)
        self.prev_event_hash = prev_event_hash
        self.created_at      = created_at or datetime.now(UTC).isoformat()
        self.hash_version     = hash_version
        self.chain_id         = chain_id
        self.chain_sequence   = chain_sequence

        if hash_version == HASH_VERSION_CURRENT:
            if chain_sequence is None:
                raise AuditChainError("hash_version=2 requires a chain_sequence")
            self.event_hash = compute_audit_hash_v2(
                chain_id=chain_id, chain_sequence=chain_sequence,
                event_id=self.event_id, event_type=event_type, fact_id=fact_id,
                from_state=from_state, to_state=to_state, actor=actor,
                reason=reason, payload=self.payload, confidence=self.confidence,
                prev_event_hash=prev_event_hash, created_at=self.created_at,
            )
        elif hash_version == HASH_VERSION_LEGACY:
            self.event_hash = compute_audit_hash_v1(
                event_type=event_type, fact_id=fact_id, from_state=from_state,
                to_state=to_state, actor=actor, payload=self.payload,
                created_at=self.created_at, prev_event_hash=prev_event_hash,
            )
        else:
            raise AuditChainError(f"unknown hash_version: {hash_version!r}")

    def to_dict(self) -> dict:
        return {
            "event_id":        self.event_id,
            "event_type":      self.event_type,
            "fact_id":         self.fact_id,
            "from_state":      self.from_state,
            "to_state":        self.to_state,
            "actor":           self.actor,
            "reason":          self.reason,
            "payload":         json.dumps(self.payload, ensure_ascii=False),
            "confidence":      self.confidence,
            "event_hash":      self.event_hash,
            "prev_event_hash": self.prev_event_hash,
            "created_at":      self.created_at,
            "hash_version":    self.hash_version,
            "chain_id":        self.chain_id,
            "chain_sequence":  self.chain_sequence,
        }


# ── AuditChain ────────────────────────────────────────────────────────────────

class AuditChain:
    """
    Append-only audit log с hash-chain верификацией.

    Гарантирует:
    1. Нельзя изменить прошлое незаметно (versioned hash-chain)
    2. Нельзя удалить событие (DB-level TRIGGER)
    3. Любой разрыв цепочки обнаруживается через verify_chain()
    4. Конкурентные writer'ы не могут форкнуть цепочку или потерять append

    Использование:
        chain = AuditChain(db_conn)
        chain.log_esm_transition("f1", "Observed", "Hypothesized", "agent:api")
        report = chain.verify_chain()
    """

    def __init__(self, db_conn, chain_id: str = DEFAULT_CHAIN_ID) -> None:
        self._conn = db_conn
        self.chain_id = chain_id
        self._ensure_schema()

    # ── Schema self-heal (additive only; never touches existing rows) ────────

    def _ensure_schema(self) -> None:
        """Additively self-heal the v2 schema onto whatever this connection
        already has. Mirrors the established self-heal pattern used
        elsewhere in this codebase (ErasureCoordinator, SQLiteGraphStore):
        callers — including test fixtures that build a bare v1
        `memory_events` table by hand — keep working unchanged.

        Never disables/recreates the append-only triggers, never rewrites
        existing rows beyond the new columns' NOT NULL DEFAULT backfill
        (metadata only — hash_version/chain_id, not any hashed field).
        """
        conn = self._conn
        owns_transaction = not conn.in_transaction
        # Only raise a floor of 5s — never lower a caller-configured,
        # longer timeout (e.g. a caller running PRAGMA busy_timeout=30000
        # before constructing us for a known-long-running writer).
        current_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        if current_timeout < 5000:
            conn.execute("PRAGMA busy_timeout=5000")

        has_events_table = bool(conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_events'"
        ).fetchone())

        if has_events_table:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(memory_events)").fetchall()}
            if "hash_version" not in cols:
                self._add_column_if_missing(
                    "memory_events", "hash_version", "INTEGER NOT NULL DEFAULT 1"
                )
            if "chain_id" not in cols:
                self._add_column_if_missing(
                    "memory_events", "chain_id",
                    f"TEXT NOT NULL DEFAULT '{DEFAULT_CHAIN_ID}'",
                )
            if "chain_sequence" not in cols:
                self._add_column_if_missing("memory_events", "chain_sequence", "INTEGER")
            try:
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_events_chain_seq "
                    "ON memory_events(chain_id, chain_sequence) WHERE chain_sequence IS NOT NULL"
                )
            except sqlite3.IntegrityError:
                # The index doesn't exist (e.g. dropped) AND the table
                # already contains a genuine (chain_id, chain_sequence)
                # duplicate — creating it would raise, not silently no-op.
                # This self-heal must never crash verify_chain(): the
                # duplicate is exactly the kind of corruption
                # verify_chain()'s own row-by-row sequence check exists to
                # detect and report, not something schema setup should
                # mask with an unhandled exception. log()'s CAS-guarded
                # append still prevents NEW duplicates without this index.
                pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_chain_heads (
                chain_id        TEXT PRIMARY KEY,
                last_sequence   INTEGER NOT NULL DEFAULT 0,
                last_event_hash TEXT,
                updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS integrity_checks (
                check_id     TEXT PRIMARY KEY,
                check_type   TEXT NOT NULL,
                status       TEXT NOT NULL,
                details      TEXT,
                checked_at   TEXT NOT NULL DEFAULT (datetime('now')),
                checked_by   TEXT NOT NULL DEFAULT 'system'
            )
        """)

        if has_events_table:
            existing_head = conn.execute(
                "SELECT 1 FROM audit_chain_heads WHERE chain_id = ?",
                (self.chain_id,),
            ).fetchone()
            if existing_head is None:
                last_row = conn.execute(
                    "SELECT event_hash, chain_sequence FROM memory_events "
                    "WHERE chain_id = ? ORDER BY rowid DESC LIMIT 1",
                    (self.chain_id,),
                ).fetchone()
                if last_row is None:
                    last_hash, last_seq = None, 0
                else:
                    last_hash, stored_seq = last_row
                    last_seq = stored_seq if stored_seq is not None else 0
                conn.execute(
                    "INSERT OR IGNORE INTO audit_chain_heads "
                    "(chain_id, last_sequence, last_event_hash) VALUES (?, ?, ?)",
                    (self.chain_id, last_seq, last_hash),
                )

        # Only commit if we opened this work ourselves — a caller that
        # already had an open transaction owns its own commit/rollback,
        # and unconditionally committing here would silently finalize
        # whatever unrelated work the caller had pending before it ever
        # gets a chance to roll it back.
        if owns_transaction:
            conn.commit()

    def _add_column_if_missing(self, table: str, column: str, ddl_suffix: str) -> None:
        """ALTER TABLE ADD COLUMN, tolerating a benign race: two
        connections can both see the column missing (via PRAGMA
        table_info) before either ALTER commits, so the loser's ALTER
        would otherwise fail with 'duplicate column name' even though the
        desired end state (column present) was already achieved by the
        winner."""
        try:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_suffix}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc):
                raise

    # ── Запись событий (atomic append) ────────────────────────────────────────

    def log(
        self,
        event_type:  str,
        actor:       str,
        fact_id:     str | None = None,
        from_state:  str | None = None,
        to_state:    str | None = None,
        reason:      str | None = None,
        payload:     dict | None = None,
        confidence:  float | None = None,
    ) -> AuditEvent:
        """Append one event to the chain atomically.

        Head-read, sequence allocation, insert, and head-update happen
        inside a single transaction so concurrent writers can never fork
        the chain, duplicate a sequence position, or lose a successful
        append — a crash between the insert and the head-update leaves
        neither half committed.

        If the caller already owns a transaction on this connection, we
        participate in it (no BEGIN/COMMIT/ROLLBACK of our own, no retry —
        that would silently destroy the caller's uncommitted work). If we
        own the transaction, we use BEGIN IMMEDIATE to acquire the write
        lock up front and retry a bounded number of times on genuine
        concurrent-head contention.
        """
        # Re-run the (idempotent) schema self-heal before every append: if
        # this instance was first constructed inside a caller-owned
        # transaction that later rolled back, our constructor-time
        # self-heal was rolled back with it — audit_chain_heads or the v2
        # columns may no longer exist even though this instance thinks
        # they do. Cheap and safe to repeat (IF NOT EXISTS / column-exists
        # guarded throughout).
        self._ensure_schema()

        conn = self._conn
        validated_payload = validate_payload(payload)
        validated_confidence = validate_confidence(confidence)

        owns_transaction = not conn.in_transaction
        max_attempts = 5 if owns_transaction else 1

        for attempt in range(max_attempts):
            if owns_transaction:
                try:
                    conn.execute("BEGIN IMMEDIATE")
                except sqlite3.OperationalError:
                    if attempt < max_attempts - 1:
                        time.sleep(0.01 * (attempt + 1))
                        continue
                    raise

            try:
                # INSERT OR IGNORE is itself a write — issuing it before the
                # SELECT forces SQLite to upgrade to a write lock even when
                # we're participating in a caller-owned (possibly DEFERRED)
                # transaction, closing the read-then-write race without a
                # separate no-op statement (SQLite has no SELECT ... FOR
                # UPDATE).
                conn.execute(
                    "INSERT OR IGNORE INTO audit_chain_heads "
                    "(chain_id, last_sequence, last_event_hash) VALUES (?, 0, NULL)",
                    (self.chain_id,),
                )
                last_seq, prev_hash = conn.execute(
                    "SELECT last_sequence, last_event_hash FROM audit_chain_heads "
                    "WHERE chain_id = ?",
                    (self.chain_id,),
                ).fetchone()

                new_seq = last_seq + 1
                event = AuditEvent(
                    event_type=event_type,
                    actor=actor,
                    fact_id=fact_id,
                    from_state=from_state,
                    to_state=to_state,
                    reason=reason,
                    payload=validated_payload,
                    confidence=validated_confidence,
                    prev_event_hash=prev_hash,
                    hash_version=HASH_VERSION_CURRENT,
                    chain_id=self.chain_id,
                    chain_sequence=new_seq,
                )

                conn.execute(
                    """
                    INSERT INTO memory_events (
                        event_id, event_type, fact_id, from_state, to_state,
                        actor, reason, payload, confidence,
                        event_hash, prev_event_hash, created_at,
                        hash_version, chain_id, chain_sequence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id, event.event_type, event.fact_id,
                        event.from_state, event.to_state,
                        event.actor, event.reason,
                        json.dumps(event.payload, ensure_ascii=False),
                        event.confidence,
                        event.event_hash, event.prev_event_hash,
                        event.created_at,
                        event.hash_version, event.chain_id, event.chain_sequence,
                    ),
                )

                cur = conn.execute(
                    "UPDATE audit_chain_heads SET last_sequence = ?, last_event_hash = ?, "
                    "updated_at = ? WHERE chain_id = ? AND last_sequence = ?",
                    (new_seq, event.event_hash, event.created_at, self.chain_id, last_seq),
                )
                if cur.rowcount != 1:
                    raise _StaleHeadError(
                        f"chain head for {self.chain_id!r} advanced concurrently"
                    )

                if owns_transaction:
                    conn.commit()
                return event

            except _StaleHeadError:
                if owns_transaction:
                    conn.rollback()
                    if attempt < max_attempts - 1:
                        continue
                raise
            except Exception:
                if owns_transaction:
                    conn.rollback()
                raise

        raise AssertionError(
            "unreachable: AuditChain.log() loop exited without returning or raising"
        )

    # ── Удобные shortcut методы ───────────────────────────────────────────────

    def log_fact_created(
        self, fact_id: str, claim: str, actor: str, confidence: float,
    ) -> AuditEvent:
        return self.log(
            EventType.FACT_CREATED, actor, fact_id=fact_id,
            to_state="Observed", confidence=confidence,
            payload={"claim_preview": claim[:100]},
        )

    def log_esm_transition(
        self,
        fact_id:    str,
        from_state: str,
        to_state:   str,
        actor:      str,
        reason:     str | None = None,
        confidence: float | None = None,
    ) -> AuditEvent:
        event_type = (
            EventType.FACT_DEPRECATED if to_state == "Deprecated"
            else EventType.FACT_COLLAPSED if to_state == "Collapsed"
            else EventType.ESM_TRANSITION
        )
        return self.log(
            event_type, actor, fact_id=fact_id,
            from_state=from_state, to_state=to_state,
            reason=reason, confidence=confidence,
        )

    def log_truth_gate_verdict(
        self,
        fact_id:    str,
        passed:     bool,
        mode:       str,
        actor:      str,
        reason:     str | None = None,
        confidence: float | None = None,
    ) -> AuditEvent:
        return self.log(
            EventType.TRUTH_GATE_VERDICT, actor, fact_id=fact_id,
            reason=reason, confidence=confidence,
            payload={"passed": passed, "mode": mode},
        )

    def log_observer_verdict(
        self,
        decision: str,
        flags:    list | None = None,
        actor:    str = "observer",
        reason:   str | None = None,
    ) -> AuditEvent:
        """Append a passive Observer verdict (allow|warn|gap_notice|reject) + flags."""
        return self.log(
            EventType.OBSERVER_VERDICT, actor,
            reason=reason,
            payload={"decision": decision, "flags": list(flags or [])},
        )

    def log_immutable_blocked(
        self, fact_id: str, actor: str, attempted_state: str,
    ) -> AuditEvent:
        return self.log(
            EventType.IMMUTABLE_ATTEMPT_BLOCKED, actor, fact_id=fact_id,
            payload={"attempted_transition_to": attempted_state},
        )

    def log_cache_invalidated(self, fact_id: str, reason: str) -> AuditEvent:
        return self.log(
            EventType.CACHE_INVALIDATED, "system", fact_id=fact_id,
            reason=reason,
        )

    # ── Верификация цепочки ───────────────────────────────────────────────────

    def verify_chain(
        self,
        fact_id:  str | None = None,
        max_rows: int = 10_000,
    ) -> dict:
        """
        Verify hash-chain integrity for this chain (`self.chain_id`).

        ALWAYS verifies the COMPLETE chain — an interleaved global chain
        cannot be validated from a filtered subset. `fact_id`, if given,
        only annotates the report with fact-scoped context; it never
        removes rows from the integrity check itself (use
        get_fact_history() for a fact-scoped, non-integrity view).

        Dispatches per row on the stored hash_version: v1 rows are
        checked with the exact legacy algorithm, v2 rows with the
        canonical envelope — never by reconstructing a stateful
        AuditEvent with a fresh uuid/timestamp. Unknown hash versions,
        malformed payload JSON, non-finite numerics, and v2
        chain_sequence gaps/duplicates/regressions all fail closed.

        `max_rows` is validated (rejects bools/non-ints/<=0/over the
        documented safe upper bound) and passed as a bound SQL LIMIT
        parameter — never string-interpolated. If the chain is longer
        than `max_rows`, the result is explicitly partial
        (`complete=False`, `truncated=True`, `valid_so_far`) and is NEVER
        recorded as a passed integrity check.

        Every outcome (passed/failed/partial) is durably recorded in
        `integrity_checks` — a failed verification must be observable —
        but verification itself never mutates `memory_events`, and never
        writes an AUDIT_VERIFY event into the chain being verified.
        """
        if isinstance(max_rows, bool) or not isinstance(max_rows, int):
            raise AuditChainError(f"max_rows must be an int, got {max_rows!r}")
        if max_rows <= 0:
            raise AuditChainError(f"max_rows must be positive, got {max_rows!r}")
        if max_rows > MAX_VERIFY_ROWS:
            raise AuditChainError(
                f"max_rows exceeds safe upper bound of {MAX_VERIFY_ROWS}: {max_rows!r}"
            )

        # See log()'s identical call for why: a caller-owned transaction
        # that rolled back after this instance was constructed can take
        # audit_chain_heads/the v2 columns with it. Re-heal (idempotent)
        # before reading OR writing the integrity_checks receipt.
        self._ensure_schema()

        conn = self._conn
        # Pin every read (the row count, the row scan, and the chain-head
        # check at the end) to ONE consistent snapshot. Without this, a
        # concurrent successful append between the row scan and the head
        # check could make a genuinely valid chain look like it diverged
        # from its own head (the scan predates the append, the head read
        # doesn't) — a false-positive failure. If the caller already owns
        # a transaction we participate in its snapshot instead of nesting
        # our own (sqlite3 forbids BEGIN inside an active transaction).
        owns_transaction = not conn.in_transaction
        if owns_transaction:
            conn.execute("BEGIN")

        try:
            return self._verify_chain_locked(
                fact_id=fact_id, max_rows=max_rows, owns_transaction=owns_transaction,
            )
        except Exception:
            if owns_transaction:
                conn.rollback()
            raise

    def _verify_chain_locked(
        self, *, fact_id: str | None, max_rows: int, owns_transaction: bool,
    ) -> dict:
        """The body of verify_chain(), run inside the read snapshot
        established by its caller."""
        conn = self._conn
        total_rows = conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
            (self.chain_id,),
        ).fetchone()[0]

        rows = conn.execute(
            """
            SELECT event_id, event_type, fact_id, from_state, to_state,
                   actor, reason, payload, confidence, event_hash,
                   prev_event_hash, created_at, hash_version, chain_sequence
            FROM memory_events
            WHERE chain_id = ?
            ORDER BY rowid ASC
            LIMIT ?
            """,
            (self.chain_id, max_rows),
        ).fetchall()

        truncated = total_rows > len(rows)
        hash_versions_seen: set = set()
        prev_hash: str | None = None
        expected_next_v2_seq = 1
        seen_v2 = False

        def _fail(position: int, broken_event_id: str | None, message: str) -> dict:
            details = {
                "chain_id": self.chain_id,
                "fact_id_filter": fact_id,
                "events_checked": position,
                "hash_versions_seen": _sorted_versions(hash_versions_seen),
                "broken_at_position": position,
                "first_broken_event": broken_event_id,
                "reason": message,
            }
            # End our own read snapshot BEFORE writing the receipt: the
            # receipt write doesn't need to share the read's snapshot, and
            # writing it as a fresh statement (rather than escalating a
            # still-open reader transaction to a writer) avoids a genuine
            # SQLITE_BUSY lock-upgrade race against concurrent writers
            # that busy_timeout alone doesn't reliably cover.
            if owns_transaction:
                conn.commit()
            self._write_integrity_receipt(
                status="failed", details=details, commit=owns_transaction,
            )
            return {
                "valid": False,
                "complete": True,
                "truncated": False,
                "events_checked": position,
                "first_broken_event": broken_event_id,
                "broken_at_position": position,
                "error": message,
                "chain_id": self.chain_id,
                "fact_id_filter": fact_id,
                "hash_versions_seen": _sorted_versions(hash_versions_seen),
            }

        for i, row in enumerate(rows):
            (
                event_id, event_type, fid, from_state, to_state, actor, reason,
                payload_str, confidence, stored_hash, stored_prev_hash,
                created_at, hash_version, chain_sequence,
            ) = row

            hash_versions_seen.add(hash_version)

            if stored_prev_hash != prev_hash:
                return _fail(
                    i, event_id,
                    f"chain broken at position {i}: expected prev_hash={prev_hash!r}, "
                    f"got {stored_prev_hash!r}",
                )

            try:
                payload_data = json.loads(payload_str)
            except (json.JSONDecodeError, TypeError):
                return _fail(i, event_id, f"malformed payload JSON at position {i}")
            if not isinstance(payload_data, dict):
                # A genuine append always stores a JSON object (json.dumps
                # of a dict, never NULL/"" and never a bare JSON scalar).
                # NULL, "", "null", "[]", etc. are only reachable via
                # tampering with the stored column — treating them as an
                # implicit {} would silently accept that tamper instead
                # of detecting it.
                return _fail(
                    i, event_id, f"stored payload is not a JSON object at position {i}"
                )
            try:
                # json.loads accepts the non-standard NaN/Infinity/-Infinity
                # tokens by default. "non-finite numerics fail closed" is a
                # chain-wide invariant, not a v2-only one — apply it here,
                # before the hash_version dispatch, so a v1 row can't pass
                # verification just because its (v1-only, unvalidated)
                # hash recompute happens to reproduce a NaN-containing
                # stored string byte-for-byte.
                _validate_payload_value(payload_data)
            except AuditChainError as exc:
                return _fail(i, event_id, f"invalid payload data at position {i}: {exc}")

            try:
                # Same reasoning as the payload check above: the v1 hash
                # never committed to confidence at all (one of v1's
                # documented defects), so an Infinity/-Infinity stored
                # confidence on a legacy row would otherwise sail through
                # as "valid" — the finite-numerics invariant is chain-wide.
                validate_confidence(confidence)
            except AuditChainError as exc:
                return _fail(i, event_id, f"invalid confidence at position {i}: {exc}")

            if hash_version == HASH_VERSION_LEGACY:
                if seen_v2:
                    return _fail(
                        i, event_id,
                        f"v1-hashed event found after v2 transition boundary "
                        f"at position {i}",
                    )
                try:
                    expected_hash = compute_audit_hash_v1(
                        event_type=event_type, fact_id=fid, from_state=from_state,
                        to_state=to_state, actor=actor or "", payload=payload_data,
                        created_at=created_at, prev_event_hash=stored_prev_hash,
                    )
                except AuditChainError as exc:
                    return _fail(i, event_id, f"invalid v1 event data at position {i}: {exc}")
            elif hash_version == HASH_VERSION_CURRENT:
                seen_v2 = True
                if chain_sequence is None:
                    return _fail(
                        i, event_id, f"v2 event missing chain_sequence at position {i}"
                    )
                if chain_sequence != expected_next_v2_seq:
                    return _fail(
                        i, event_id,
                        f"chain_sequence discontinuity at position {i}: "
                        f"expected {expected_next_v2_seq}, got {chain_sequence}",
                    )
                expected_next_v2_seq = chain_sequence + 1
                try:
                    expected_hash = compute_audit_hash_v2(
                        chain_id=self.chain_id, chain_sequence=chain_sequence,
                        event_id=event_id, event_type=event_type, fact_id=fid,
                        from_state=from_state, to_state=to_state,
                        # v2 is a brand-new hash with no legacy behavior to
                        # preserve: pass the stored value through exactly
                        # as-is (never coalesce None/"" into one value) so
                        # a tampered NULL actor produces a genuine hash
                        # mismatch instead of silently validating.
                        actor=actor,
                        reason=reason, payload=payload_data, confidence=confidence,
                        prev_event_hash=stored_prev_hash, created_at=created_at,
                    )
                except AuditChainError as exc:
                    return _fail(i, event_id, f"invalid v2 event data at position {i}: {exc}")
            else:
                return _fail(
                    i, event_id, f"unknown hash_version {hash_version!r} at position {i}"
                )

            if expected_hash != stored_hash:
                return _fail(
                    i, event_id,
                    f"hash mismatch at position {i} (event_id={event_id}): "
                    f"stored={stored_hash[:16]}..., computed={expected_hash[:16]}...",
                )

            prev_hash = stored_hash

        if truncated:
            details = {
                "chain_id": self.chain_id,
                "fact_id_filter": fact_id,
                "events_checked": len(rows),
                "hash_versions_seen": _sorted_versions(hash_versions_seen),
                "complete": False,
                "truncated": True,
            }
            if owns_transaction:
                conn.commit()  # end the read snapshot before writing the receipt
            self._write_integrity_receipt(
                status="partial", details=details, commit=owns_transaction,
            )
            return {
                "valid": None,
                "valid_so_far": True,
                "complete": False,
                "truncated": True,
                "events_checked": len(rows),
                "next_sequence": expected_next_v2_seq,
                "next_position": len(rows),
                "first_broken_event": None,
                "broken_at_position": None,
                "error": None,
                "chain_id": self.chain_id,
                "fact_id_filter": fact_id,
                "hash_versions_seen": _sorted_versions(hash_versions_seen),
            }

        # Full chain scanned with no break — cross-check the durable chain
        # head so a diverged/rolled-back head can't silently disagree with
        # the actual chain tail.
        head = conn.execute(
            "SELECT last_sequence, last_event_hash FROM audit_chain_heads WHERE chain_id = ?",
            (self.chain_id,),
        ).fetchone()
        expected_tail_hash = prev_hash
        expected_tail_seq = expected_next_v2_seq - 1

        if head is not None:
            head_seq, head_hash = head
            if head_hash != expected_tail_hash or head_seq != expected_tail_seq:
                return _fail(
                    len(rows), None,
                    f"audit_chain_heads diverges from the actual chain tail "
                    f"for chain_id={self.chain_id!r}",
                )
        elif expected_tail_hash is not None or expected_tail_seq != 0:
            return _fail(
                len(rows), None,
                f"audit_chain_heads row missing for chain_id={self.chain_id!r}",
            )

        details = {
            "chain_id": self.chain_id,
            "fact_id_filter": fact_id,
            "events_checked": len(rows),
            "hash_versions_seen": _sorted_versions(hash_versions_seen),
            "complete": True,
            "truncated": False,
        }
        if owns_transaction:
            conn.commit()  # end the read snapshot before writing the receipt
        self._write_integrity_receipt(
            status="passed", details=details, commit=owns_transaction,
        )

        return {
            "valid": True,
            "complete": True,
            "truncated": False,
            "events_checked": len(rows),
            "first_broken_event": None,
            "broken_at_position": None,
            "error": None,
            "chain_id": self.chain_id,
            "fact_id_filter": fact_id,
            "hash_versions_seen": _sorted_versions(hash_versions_seen),
        }

    def _write_integrity_receipt(
        self, *, status: str, details: dict, commit: bool = True,
    ) -> None:
        """Durably record a verification outcome. Never touches
        memory_events — this is deliberately a separate table so
        verification can never mutate the chain it is checking.

        `commit=False` is used when the caller (verify_chain()) is
        participating in a transaction it doesn't own — committing here
        would prematurely finalize the caller's unrelated pending work;
        the caller's own eventual commit/rollback covers this insert too.

        When `commit=True`, this call is writing under the read snapshot
        verify_chain() opened for itself — the INSERT is the first write
        in that transaction, so SQLite must upgrade its lock at this
        exact statement. Under concurrent writers that can transiently
        contend (SQLITE_BUSY) even with busy_timeout set; retry it a
        bounded number of times before giving up, mirroring log()'s own
        contention handling. The INSERT itself hasn't succeeded on a
        failed attempt, so retrying is safe — never a duplicate row.
        """
        sql = """
            INSERT INTO integrity_checks
            (check_id, check_type, status, details, checked_by)
            VALUES (?, 'audit_chain', ?, ?, 'verify_chain()')
        """
        params = (
            f"ic_{uuid.uuid4().hex[:12]}",
            status,
            json.dumps(details, ensure_ascii=False, default=str),
        )
        if not commit:
            self._conn.execute(sql, params)
            return

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                self._conn.execute(sql, params)
                break
            except sqlite3.OperationalError:
                if attempt < max_attempts - 1:
                    time.sleep(0.01 * (attempt + 1))
                    continue
                raise
        self._conn.commit()

    def get_fact_history(self, fact_id: str) -> list[dict]:
        """Полная история событий для одного факта.

        Fact-scoped convenience view — NOT a substitute for verify_chain()
        (a filtered subset of an interleaved global chain cannot prove
        chain integrity on its own). Scoped to this instance's chain_id,
        same as log()/verify_chain(), so a caller using a non-default
        chain_id never sees another chain's history for the same fact_id."""
        rows = self._conn.execute(
            """
            SELECT event_id, event_type, from_state, to_state,
                   actor, reason, confidence, created_at
            FROM memory_events
            WHERE fact_id = ? AND chain_id = ?
            ORDER BY rowid ASC
            """,
            (fact_id, self.chain_id),
        ).fetchall()
        return [
            {
                "event_id":   r[0],
                "event_type": r[1],
                "from_state": r[2],
                "to_state":   r[3],
                "actor":      r[4],
                "reason":     r[5],
                "confidence": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]

    def stats(self) -> dict:
        """Статистика audit log — scoped to this instance's chain_id, same
        as log()/verify_chain()/get_fact_history(), so a non-default chain
        never reports another chain's event counts."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
            (self.chain_id,),
        ).fetchone()[0]
        by_type = {}
        for row in self._conn.execute(
            "SELECT event_type, COUNT(*) FROM memory_events "
            "WHERE chain_id = ? GROUP BY event_type",
            (self.chain_id,),
        ):
            by_type[row[0]] = row[1]
        return {
            "total_events": total,
            "by_event_type": by_type,
        }
