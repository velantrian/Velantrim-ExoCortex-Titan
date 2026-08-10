"""Canonical archival claim-rewrite convergence for Titan.

Issue #284 / parent #50.

``MemoryArchival`` owns archive-payload preparation and eligibility. This module owns
the canonical SQLite mutation only and reuses the existing ``SQLiteGraphStore``
transaction/evidence primitives instead of introducing another general write protocol.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

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

_ARCHIVED_FACTS_DDL = """
CREATE TABLE IF NOT EXISTS archived_facts (
    fact_id        TEXT PRIMARY KEY,
    archive_key    TEXT NOT NULL,
    archived_at    TEXT NOT NULL,
    original_claim TEXT,
    original_state TEXT,
    archive_file   TEXT NOT NULL
);
"""


class ArchivalConcurrentModificationError(RuntimeError):
    """A selected fact changed before the archival transaction committed."""


@dataclass(frozen=True, slots=True)
class ArchivalCandidate:
    fact_id: str
    snapshot: dict
    archive_key: str
    archive_file: str
    audit_subject_id: str

    @classmethod
    def from_snapshot(cls, snapshot: dict, *, archive_key: str, archive_file: str):
        return cls(
            fact_id=str(snapshot["fact_id"]),
            snapshot=snapshot,
            archive_key=archive_key,
            archive_file=archive_file,
            audit_subject_id=str(snapshot.get("audit_subject_id") or uuid.uuid4().hex),
        )


class CanonicalArchivalRewriter:
    """Narrow archival claim-mutation owner over an existing SQLiteGraphStore."""

    def __init__(self, store) -> None:
        self._store = store

    def ensure_schema(self) -> None:
        self._store.ensure_schema()
        with self._store._db() as conn:
            conn.executescript(_ARCHIVED_FACTS_DDL)

    def _prepare_evidence_schema(self, candidates: list[ArchivalCandidate]) -> None:
        VersionStore(self._store.db_path)
        for candidate in candidates:
            chain_id = f"fact-transition:{candidate.audit_subject_id}"
            with self._store._db() as ready_conn:
                AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

    @staticmethod
    def _validate_payloads(candidates: list[ArchivalCandidate]) -> None:
        seen: set[str] = set()
        for candidate in candidates:
            if candidate.fact_id in seen:
                raise ValueError(f"duplicate archival candidate {candidate.fact_id!r}")
            seen.add(candidate.fact_id)
            path = Path(candidate.archive_file)
            if not path.is_file():
                raise FileNotFoundError(
                    f"archive payload missing before canonical mutation: {path}"
                )
            expected_prefix = f"archive://{path.name}#"
            if not candidate.archive_key.startswith(expected_prefix):
                raise ValueError("archive_key does not identify the prepared payload")

    @staticmethod
    def _fts_exists(conn: sqlite3.Connection) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='facts_fts'"
        ).fetchone() is not None

    @staticmethod
    def _archived_claim(archive_key: str) -> str:
        return f"[ARCHIVED: {archive_key}]"

    def _append_projection_intent_if_active(
        self, conn: sqlite3.Connection, *, fact_id: str
    ) -> None:
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if user_version < 20:
            return
        row = conn.execute(
            "SELECT fact_version FROM facts WHERE fact_id = ?", (fact_id,)
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"archival lost canonical fact {fact_id!r} before outbox append"
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
        candidate: ArchivalCandidate,
        *,
        now: str,
    ) -> None:
        snapshot = candidate.snapshot
        if snapshot.get("epistemic_state") == "ImmutableCore":
            raise ValueError("ImmutableCore facts cannot be archived")

        new_claim = self._archived_claim(candidate.archive_key)
        new_metadata = attach_integrity_metadata(
            snapshot.get("metadata") or {},
            claim=new_claim,
            source=snapshot.get("source", "unknown"),
            confidence=float(snapshot.get("confidence", 0.5)),
            epistemic_state=snapshot.get("epistemic_state", "Observed"),
        )
        bump = self._store._fact_version_bump_sql(conn)
        cur = conn.execute(
            f"UPDATE facts SET {bump}claim = ?, metadata = ?, updated_at = ?, "
            "audit_subject_id = COALESCE(audit_subject_id, ?) "
            "WHERE fact_id = ? AND claim = ? AND updated_at = ?",
            (
                new_claim,
                json.dumps(new_metadata, ensure_ascii=False, sort_keys=True),
                now,
                candidate.audit_subject_id,
                candidate.fact_id,
                snapshot.get("claim", ""),
                snapshot.get("updated_at"),
            ),
        )
        if cur.rowcount != 1:
            raise ArchivalConcurrentModificationError(
                f"fact {candidate.fact_id!r} changed before archival commit"
            )

        real_subject = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?",
            (candidate.fact_id,),
        ).fetchone()[0]
        self._store._snapshot_before_change_in_transaction(
            conn,
            candidate.fact_id,
            snapshot,
            caused_by="memory.archive",
            now_iso=now,
        )
        conn.execute(
            """INSERT INTO archived_facts
               (fact_id, archive_key, archived_at, original_claim, original_state, archive_file)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                candidate.fact_id,
                candidate.archive_key,
                now,
                str(snapshot.get("claim", ""))[:500],
                snapshot.get("epistemic_state", ""),
                candidate.archive_file,
            ),
        )
        AuditChain(
            conn,
            chain_id=f"fact-transition:{real_subject}",
            _skip_schema_check=True,
        ).log_in_transaction(
            event_type=EventType.FACT_UPDATED,
            actor=ACTOR_CODE_STORE_FACT,
            to_state=snapshot.get("epistemic_state"),
            reason=REASON_CODE_CAS_GUARDED_WRITE,
        )
        if self._fts_exists(conn):
            upsert_fts_row(
                conn,
                candidate.fact_id,
                new_claim,
                snapshot.get("source", "unknown"),
            )
        self._append_projection_intent_if_active(conn, fact_id=candidate.fact_id)

    def rewrite_batch(self, candidates: list[ArchivalCandidate]) -> int:
        """Commit one selected archive batch atomically in SQLite."""
        if not candidates:
            return 0
        ensure_writes_allowed()
        self.ensure_schema()
        self._validate_payloads(candidates)
        self._store._release_stray_locks()
        self._prepare_evidence_schema(candidates)

        from core.memory import _now

        now = _now()
        with self._store._db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for candidate in candidates:
                self._apply_candidate(conn, candidate, now=now)

        for candidate in candidates:
            self._store._l0_del(candidate.fact_id)
        return len(candidates)


__all__ = [
    "ArchivalCandidate",
    "ArchivalConcurrentModificationError",
    "CanonicalArchivalRewriter",
]
