"""Canonical, privacy-safe PII claim redaction for Titan facts.

Issue #282 / parent #50.

This module is the single mutation owner for PII claim redaction.  It does
not own physical erasure, ESM transitions, TruthGate policy, background
execution, or runtime activation.  ``ForgettingEngine`` remains a legacy
compatibility surface and delegates here.

Privacy exception to ordinary VersionStore history
--------------------------------------------------
A normal canonical mutation preserves the exact pre-image in ``fact_versions``.
Doing that for a privacy redaction would re-persist the very PII the caller
asked to remove.  Redaction therefore follows a narrower privacy rule:

* current Canon is redacted;
* any historical ``fact_versions.claim`` value for the same fact is redacted
  in the same transaction and its integrity metadata/checksum is recomputed;
* the VersionStore row created for the redaction boundary is itself sanitized
  before insertion, so no new plaintext PII pre-image is retained;
* AuditChain records a content-free FACT_UPDATED event;
* FTS is refreshed synchronously when present, and the transactional outbox
  receives a content-free refresh intent when migration 020 is active.

This is claim-surface redaction, not a claim that every raw origin or external
projection has been physically erased.  Full data-subject erasure belongs to
the durable erasure coordinators.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from core.audit_chain import (
    ACTOR_CODE_STORE_FACT,
    REASON_CODE_CAS_GUARDED_WRITE,
    AuditChain,
    EventType,
)
from core.fact_integrity import attach_integrity_metadata
from core.projection_apply import upsert_fts_row
from core.projection_outbox import (
    LOCAL_PROJECTION_SCOPE_REF,
    ProjectionIntent,
    ProjectionKind,
    ProjectionOperation,
    append_projection_intent_in_transaction,
)
from core.version_store import VersionStore
from core.write_gate import ensure_writes_allowed

if TYPE_CHECKING:
    from core.memory import SQLiteGraphStore


class PiiRedactionConcurrentModificationError(RuntimeError):
    """A fact changed after the redaction candidate snapshot was prepared."""


# Compatibility name used by the legacy adapter/tests in this bounded PR.
PiiRedactionConcurrentModification = PiiRedactionConcurrentModificationError


@dataclass(frozen=True, slots=True)
class PiiRedactionResult:
    status: str
    redacted_count: int
    scanned_count: int


@dataclass(frozen=True, slots=True)
class _Candidate:
    fact_id: str
    snapshot: dict
    redacted_claim: str
    audit_subject_id: str


class CanonicalPiiRedactor:
    """One canonical PII-claim redaction authority over ``SQLiteGraphStore``."""

    def __init__(self, store: SQLiteGraphStore) -> None:
        self._store = store

    @staticmethod
    def _decode_fact_row(row: sqlite3.Row) -> dict:
        data = dict(row)
        metadata = data.get("metadata")
        if isinstance(metadata, str):
            data["metadata"] = json.loads(metadata or "{}")
        history = data.get("history")
        if isinstance(history, str):
            data["history"] = json.loads(history or "[]")
        return data

    @staticmethod
    def _redacted_metadata(snapshot: dict, redacted_claim: str) -> dict:
        return attach_integrity_metadata(
            snapshot.get("metadata") or {},
            claim=redacted_claim,
            source=snapshot.get("source", "unknown"),
            confidence=float(snapshot.get("confidence", 0.5)),
            epistemic_state=snapshot.get("epistemic_state", "Observed"),
        )

    def _candidate(self, snapshot: dict, redacted_claim: str) -> _Candidate:
        return _Candidate(
            fact_id=str(snapshot["fact_id"]),
            snapshot=snapshot,
            redacted_claim=redacted_claim,
            audit_subject_id=(
                snapshot.get("audit_subject_id") or uuid.uuid4().hex
            ),
        )

    def _prepare_evidence_schema(self, candidates: list[_Candidate]) -> None:
        # VersionStore schema and AuditChain schema are deliberately warmed
        # outside the canonical mutation transaction.  Their transactional
        # APIs explicitly forbid DDL/self-heal inside that transaction.
        VersionStore(self._store.db_path)
        for candidate in candidates:
            chain_id = f"fact-transition:{candidate.audit_subject_id}"
            with self._store._db() as ready_conn:
                AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

    @staticmethod
    def _fts_exists(conn: sqlite3.Connection) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='facts_fts'"
        ).fetchone() is not None

    @staticmethod
    def _sanitize_historical_versions(
        conn: sqlite3.Connection,
        *,
        fact_id: str,
        redactor: Callable[[str], str],
    ) -> None:
        """Remove matching PII from already-retained version claims.

        Redaction is intentionally allowed to rewrite the privacy-sensitive
        fields of historical version rows.  The temporal coordinates and
        provenance remain intact; integrity metadata/checksum is recomputed
        so VersionStore.verify_versions_integrity() continues to verify the
        sanitized history.
        """
        rows = conn.execute(
            "SELECT * FROM fact_versions WHERE fact_id = ? ORDER BY version_id",
            (fact_id,),
        ).fetchall()
        for row in rows:
            old_claim = row["claim"] or ""
            new_claim = redactor(old_claim)
            if new_claim == old_claim:
                continue
            metadata = json.loads(row["metadata"] or "{}")
            new_metadata = attach_integrity_metadata(
                metadata,
                claim=new_claim,
                source=row["source"] or "unknown",
                confidence=float(row["confidence"] or 0.0),
                epistemic_state=row["epistemic_state"] or "Observed",
            )
            checksum_data = {
                "fact_id": row["fact_id"],
                "claim": new_claim,
                "source": row["source"],
                "confidence": row["confidence"],
                "epistemic_state": row["epistemic_state"],
                "metadata": new_metadata,
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
            }
            checksum = VersionStore._checksum(
                checksum_data,
                int(row["version_num"]),
                row["superseded_at"],
            )
            conn.execute(
                "UPDATE fact_versions SET claim = ?, metadata = ?, checksum = ? "
                "WHERE version_id = ?",
                (
                    new_claim,
                    json.dumps(new_metadata, ensure_ascii=False, sort_keys=True),
                    checksum,
                    row["version_id"],
                ),
            )

    def _append_projection_intent_if_active(
        self,
        conn: sqlite3.Connection,
        *,
        fact_id: str,
    ) -> None:
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if user_version < 20:
            return
        row = conn.execute(
            "SELECT fact_version FROM facts WHERE fact_id = ?", (fact_id,)
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"PII redaction lost canonical fact {fact_id!r} before outbox append"
            )
        append_projection_intent_in_transaction(
            conn,
            ProjectionIntent(
                aggregate_id=fact_id,
                scope_ref=LOCAL_PROJECTION_SCOPE_REF,
                canonical_version=int(row[0]),
                projection_kind=ProjectionKind.ALL,
                operation=ProjectionOperation.REFRESH,
            ),
        )

    def _apply_candidate(
        self,
        conn: sqlite3.Connection,
        candidate: _Candidate,
        *,
        redactor: Callable[[str], str],
        now: str,
    ) -> None:
        snapshot = candidate.snapshot
        new_metadata = self._redacted_metadata(snapshot, candidate.redacted_claim)
        bump = self._store._fact_version_bump_sql(conn)
        cur = conn.execute(
            f"UPDATE facts SET {bump}claim = ?, metadata = ?, updated_at = ?, "
            "audit_subject_id = COALESCE(audit_subject_id, ?) "
            "WHERE fact_id = ? AND claim = ? AND updated_at = ?",
            (
                candidate.redacted_claim,
                json.dumps(new_metadata, ensure_ascii=False, sort_keys=True),
                now,
                candidate.audit_subject_id,
                candidate.fact_id,
                snapshot.get("claim", ""),
                snapshot.get("updated_at"),
            ),
        )
        if cur.rowcount != 1:
            raise PiiRedactionConcurrentModification(
                f"fact {candidate.fact_id!r} changed before PII redaction commit"
            )

        real_audit_subject_id = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?",
            (candidate.fact_id,),
        ).fetchone()[0]

        # Privacy wins over recoverable plaintext history: scrub existing
        # historical claims first, then append a SANITIZED boundary snapshot.
        self._sanitize_historical_versions(
            conn,
            fact_id=candidate.fact_id,
            redactor=redactor,
        )
        sanitized_snapshot = copy.deepcopy(snapshot)
        sanitized_snapshot["claim"] = candidate.redacted_claim
        sanitized_snapshot["metadata"] = new_metadata
        self._store._snapshot_before_change_in_transaction(
            conn,
            candidate.fact_id,
            sanitized_snapshot,
            caused_by="privacy.redact_pii",
            now_iso=now,
        )

        chain = AuditChain(
            conn,
            chain_id=f"fact-transition:{real_audit_subject_id}",
            _skip_schema_check=True,
        )
        chain.log_in_transaction(
            event_type=EventType.FACT_UPDATED,
            actor=ACTOR_CODE_STORE_FACT,
            to_state=snapshot.get("epistemic_state"),
            reason=REASON_CODE_CAS_GUARDED_WRITE,
        )

        # Claim-bearing FTS is privacy-sensitive and must not wait for the
        # currently non-runtime-wired dispatcher.  Refresh it synchronously
        # inside the same SQLite transaction when the table exists.
        if self._fts_exists(conn):
            upsert_fts_row(
                conn,
                candidate.fact_id,
                candidate.redacted_claim,
                snapshot.get("source", "unknown"),
            )

        # Other rebuildable projections receive a content-minimized refresh
        # intent when the outbox contract is active.  Missing/corrupt activated
        # outbox schema fails closed and rolls the whole redaction back.
        self._append_projection_intent_if_active(
            conn,
            fact_id=candidate.fact_id,
        )

    def redact_fact(
        self,
        fact_id: str,
        redactor: Callable[[str], str],
    ) -> PiiRedactionResult:
        ensure_writes_allowed()
        self._store.ensure_schema()
        self._store._release_stray_locks()
        snapshot = self._store.get_fact_durable(fact_id)
        if snapshot is None:
            self._store._l0_del(fact_id)
            return PiiRedactionResult("fact_not_found", 0, 0)

        redacted_claim = redactor(snapshot.get("claim", ""))
        if redacted_claim == snapshot.get("claim", ""):
            return PiiRedactionResult("no_pii_found", 0, 1)

        candidate = self._candidate(snapshot, redacted_claim)
        self._prepare_evidence_schema([candidate])

        from core.memory import _now

        now = _now()
        with self._store._db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._apply_candidate(conn, candidate, redactor=redactor, now=now)

        self._store._l0_del(fact_id)
        return PiiRedactionResult("redacted", 1, 1)

    def redact_batch(
        self,
        limit: int,
        redactor: Callable[[str], str],
    ) -> PiiRedactionResult:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ValueError("PII redaction batch limit must be a non-negative int")
        ensure_writes_allowed()
        self._store.ensure_schema()
        self._store._release_stray_locks()

        with self._store._db() as conn:
            rows = conn.execute(
                "SELECT * FROM facts ORDER BY rowid LIMIT ?", (limit,)
            ).fetchall()
        snapshots = [self._decode_fact_row(row) for row in rows]
        candidates: list[_Candidate] = []
        for snapshot in snapshots:
            redacted_claim = redactor(snapshot.get("claim", ""))
            if redacted_claim != snapshot.get("claim", ""):
                candidates.append(self._candidate(snapshot, redacted_claim))

        if not candidates:
            return PiiRedactionResult("batch_redacted", 0, len(snapshots))

        self._prepare_evidence_schema(candidates)
        from core.memory import _now

        now = _now()
        with self._store._db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for candidate in candidates:
                self._apply_candidate(conn, candidate, redactor=redactor, now=now)

        for candidate in candidates:
            self._store._l0_del(candidate.fact_id)
        return PiiRedactionResult(
            "batch_redacted",
            len(candidates),
            len(snapshots),
        )


__all__ = [
    "CanonicalPiiRedactor",
    "PiiRedactionConcurrentModification",
    "PiiRedactionConcurrentModificationError",
    "PiiRedactionResult",
]
