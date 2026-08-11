"""
Operational memory layer for VELANTRIM.

This module adds the first v10-style workbench primitives around the existing
fact store without changing the semantics of L0/L1 memory:

- SourceRegistry: explicit source identities and trust hints.
- FactInbox: pending claims before promotion into the canonical facts table.
- ReasoningTrace: compact traces explaining which facts supported an answer.
- MemoryDiff: a read model for "what changed since ...".
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")

INBOX_STATUSES = {"pending", "accepted", "rejected", "promoted", "archived"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json_load(raw: Any, default: Any) -> Any:
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


def _json_dump(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _source_id(source_type: str, label: str, uri: str = "") -> str:
    seed = f"{source_type.strip().lower()}|{label.strip()}|{uri.strip()}"
    return f"src_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def _validate_confidence(value: float, context: str) -> float:
    from core.validators import assert_confidence

    return assert_confidence(value, context=context)


class MemoryOpsStore:
    """Small SQLite-backed operational layer around the canonical fact store."""

    def __init__(self, db_path: str = SQLITE_PATH) -> None:
        self.db_path = str(db_path)
        self._initialized = False

    @contextmanager
    def _db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            pass
        if not self._initialized:
            self._init_schema(conn)
            self._initialized = True
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_registry (
                source_id   TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                label       TEXT NOT NULL,
                uri         TEXT DEFAULT '',
                trust       REAL DEFAULT 0.5,
                metadata    TEXT DEFAULT '{}',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_source_registry_type
            ON source_registry(source_type)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fact_inbox (
                inbox_id         TEXT PRIMARY KEY,
                claim            TEXT NOT NULL,
                source_id        TEXT,
                raw_id           TEXT,
                status           TEXT NOT NULL DEFAULT 'pending',
                confidence       REAL DEFAULT 0.5,
                metadata         TEXT DEFAULT '{}',
                promoted_fact_id TEXT,
                created_at       TEXT NOT NULL,
                updated_at       TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_fact_inbox_status
            ON fact_inbox(status, updated_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reasoning_traces (
                trace_id          TEXT PRIMARY KEY,
                query             TEXT NOT NULL,
                answer            TEXT DEFAULT '',
                mode              TEXT DEFAULT '',
                response_lens     TEXT DEFAULT '',
                source_fact_ids   TEXT DEFAULT '[]',
                rejected_fact_ids TEXT DEFAULT '[]',
                notes             TEXT DEFAULT '',
                metadata          TEXT DEFAULT '{}',
                created_at        TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reasoning_traces_created
            ON reasoning_traces(created_at)
            """
        )

    def register_source(
        self,
        *,
        source_type: str,
        label: str,
        uri: str = "",
        trust: float = 0.5,
        metadata: dict[str, Any] | None = None,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("memory_ops.register_source")
        if not source_type.strip():
            raise ValueError("source_type is required")
        if not label.strip():
            raise ValueError("label is required")
        trust = _validate_confidence(trust, "memory_ops.register_source")
        sid = source_id or _source_id(source_type, label, uri)
        now = _now()
        payload = {
            "source_id": sid,
            "source_type": source_type.strip().lower(),
            "label": label.strip(),
            "uri": uri.strip(),
            "trust": trust,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        with self._db() as conn:
            row = conn.execute(
                "SELECT created_at FROM source_registry WHERE source_id = ?",
                (sid,),
            ).fetchone()
            if row:
                payload["created_at"] = row["created_at"]
            conn.execute(
                """
                INSERT INTO source_registry
                    (source_id, source_type, label, uri, trust, metadata, created_at, updated_at)
                VALUES
                    (:source_id, :source_type, :label, :uri, :trust, :metadata_json,
                     :created_at, :updated_at)
                ON CONFLICT(source_id) DO UPDATE SET
                    source_type = excluded.source_type,
                    label       = excluded.label,
                    uri         = excluded.uri,
                    trust       = excluded.trust,
                    metadata    = excluded.metadata,
                    updated_at  = excluded.updated_at
                """,
                {**payload, "metadata_json": _json_dump(payload["metadata"])},
            )
        return payload

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM source_registry WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        return self._source_from_row(row) if row else None

    def list_sources(
        self,
        *,
        source_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: list[Any] = []
        where = ""
        if source_type:
            where = "WHERE source_type = ?"
            params.append(source_type.strip().lower())
        with self._db() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM source_registry {where}",
                params,
            ).fetchone()[0]
            rows = conn.execute(
                f"""
                SELECT * FROM source_registry {where}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "sources": [self._source_from_row(r) for r in rows],
        }

    def enqueue_fact(
        self,
        *,
        claim: str,
        source_id: str | None = None,
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
        raw_id: str | None = None,
        inbox_id: str | None = None,
    ) -> dict[str, Any]:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("memory_ops.enqueue_fact")
        if not claim.strip():
            raise ValueError("claim is required")
        confidence = _validate_confidence(confidence, "memory_ops.enqueue_fact")
        iid = inbox_id or f"inbox_{uuid.uuid4().hex[:12]}"
        now = _now()
        payload = {
            "inbox_id": iid,
            "claim": claim.strip(),
            "source_id": source_id,
            "raw_id": raw_id,
            "status": "pending",
            "confidence": confidence,
            "metadata": metadata or {},
            "promoted_fact_id": None,
            "created_at": now,
            "updated_at": now,
        }
        with self._db() as conn:
            if source_id:
                source = conn.execute(
                    "SELECT source_id FROM source_registry WHERE source_id = ?",
                    (source_id,),
                ).fetchone()
                if not source:
                    raise ValueError(f"unknown source_id: {source_id}")
            conn.execute(
                """
                INSERT INTO fact_inbox
                    (inbox_id, claim, source_id, raw_id, status, confidence,
                     metadata, promoted_fact_id, created_at, updated_at)
                VALUES
                    (:inbox_id, :claim, :source_id, :raw_id, :status, :confidence,
                     :metadata_json, :promoted_fact_id, :created_at, :updated_at)
                """,
                {**payload, "metadata_json": _json_dump(payload["metadata"])},
            )
        return payload

    def list_inbox(
        self,
        *,
        status: str | None = "pending",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: list[Any] = []
        where = ""
        if status:
            self._validate_status(status)
            where = "WHERE status = ?"
            params.append(status)
        with self._db() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM fact_inbox {where}",
                params,
            ).fetchone()[0]
            rows = conn.execute(
                f"""
                SELECT * FROM fact_inbox {where}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [self._inbox_from_row(r) for r in rows],
        }

    def get_inbox_item(self, inbox_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM fact_inbox WHERE inbox_id = ?",
                (inbox_id,),
            ).fetchone()
        return self._inbox_from_row(row) if row else None

    def set_inbox_status(
        self,
        inbox_id: str,
        status: str,
        *,
        reason: str = "",
    ) -> dict[str, Any] | None:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("memory_ops.set_inbox_status")
        self._validate_status(status)
        now = _now()
        with self._db() as conn:
            row = conn.execute(
                "SELECT metadata FROM fact_inbox WHERE inbox_id = ?",
                (inbox_id,),
            ).fetchone()
            if not row:
                return None
            meta = _json_load(row["metadata"], {})
            if reason:
                meta["status_reason"] = reason
            conn.execute(
                """
                UPDATE fact_inbox
                SET status = ?, metadata = ?, updated_at = ?
                WHERE inbox_id = ?
                """,
                (status, _json_dump(meta), now, inbox_id),
            )
        return self.get_inbox_item(inbox_id)

    def promote_inbox_item(
        self,
        inbox_id: str,
        *,
        fact_id: str | None = None,
        epistemic_state: str = "Observed",
    ) -> dict[str, Any]:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("memory_ops.promote_inbox_item")
        item = self.get_inbox_item(inbox_id)
        if not item:
            raise ValueError(f"inbox item not found: {inbox_id}")
        if item["status"] == "promoted" and item.get("promoted_fact_id"):
            existing = self._load_fact(item["promoted_fact_id"])
            return {
                "created": False,
                "inbox_item": item,
                "fact": existing,
            }

        sid = item.get("source_id")
        source = self.get_source(sid) if sid else None
        source_label = source["label"] if source else "fact_inbox"
        fid = fact_id or f"fact_{uuid.uuid4().hex[:12]}"
        meta = dict(item.get("metadata") or {})
        meta.update(
            {
                "inbox_id": item["inbox_id"],
                "source_registry_id": sid,
                "promoted_from": "fact_inbox",
            }
        )
        if source:
            meta["source_trust"] = source["trust"]
            meta["source_type"] = source["source_type"]

        raw_id = item.get("raw_id")
        raw_created_here = False
        if not raw_id:
            from core.memory import store_raw_text

            raw_id = store_raw_text(item["claim"], source_label, "fact_inbox")
            raw_created_here = True

        # Issue #288: raw provenance is not pre-populated in the fact payload.
        # SQLiteGraphStore.link_raw_to_fact() below owns the first canonical
        # facts.derived_from mutation and its VersionStore/provenance/AuditChain
        # evidence transaction after the fact write itself is accepted.
        fact = {
            "fact_id": fid,
            "claim": item["claim"],
            "source": f"source_registry:{sid}" if sid else source_label,
            "confidence": item["confidence"],
            "epistemic_state": epistemic_state,
            "metadata": meta,
        }
        from core.memory import get_fact, link_raw_to_fact, store_fact_result
        from core.write_result import ACCEPTED_WRITE_STATUSES

        result = store_fact_result(fact)
        accepted = result.status in ACCEPTED_WRITE_STATUSES
        now = _now()

        # PR-C1: raw_id (immutable, append-only L0) is persisted onto the
        # inbox row regardless of the promotion outcome below — it must
        # never be lost/re-derived, and it is not itself the thing that can
        # be "rejected".
        if raw_created_here:
            with self._db() as conn:
                conn.execute(
                    "UPDATE fact_inbox SET raw_id = COALESCE(raw_id, ?), updated_at = ? "
                    "WHERE inbox_id = ?",
                    (raw_id, now, inbox_id),
                )

        if not accepted:
            # PR-C1 (evidence report, hardened): a rejection/failure must NOT
            # mark this item 'promoted' (the early-return guard above treats
            # any 'promoted' status as terminal — that would permanently
            # strand it) and must NOT link provenance — even when
            # result.canonical_exists is True because an *old* canonical
            # fact already existed under this fid before this rejected
            # attempt (a rejected update, not a rejected create; gating on
            # canonical_exists alone would wrongly treat that as accepted).
            # status stays whatever it already was (pending) so a retry is
            # always possible; only a safe diagnostic trail is recorded.
            diag_meta = dict(item.get("metadata") or {})
            diag_meta.update({
                "last_promotion_status": result.status.value,
                "last_promotion_reason_code": result.safe_reason_code,
                "last_promotion_at": now,
            })
            with self._db() as conn:
                conn.execute(
                    "UPDATE fact_inbox SET metadata = ?, updated_at = ? WHERE inbox_id = ?",
                    (_json_dump(diag_meta), now, inbox_id),
                )
            return {
                "created": False,
                "inbox_item": self.get_inbox_item(inbox_id),
                "fact": None,
            }

        if raw_id:
            link_raw_to_fact(raw_id, fid, derivation_type="fact_inbox_promotion")

        with self._db() as conn:
            conn.execute(
                """
                UPDATE fact_inbox
                SET status = 'promoted',
                    promoted_fact_id = ?,
                    raw_id = COALESCE(raw_id, ?),
                    updated_at = ?
                WHERE inbox_id = ?
                """,
                (fid, raw_id, now, inbox_id),
            )
        return {
            "created": result.created,
            "inbox_item": self.get_inbox_item(inbox_id),
            "fact": get_fact(fid),
        }

    def save_trace(
        self,
        *,
        query: str,
        answer: str = "",
        mode: str = "",
        response_lens: str = "",
        source_fact_ids: Iterable[str] | None = None,
        rejected_fact_ids: Iterable[str] | None = None,
        notes: str = "",
        metadata: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("memory_ops.save_trace")
        if not query.strip():
            raise ValueError("query is required")
        tid = trace_id or f"trace_{uuid.uuid4().hex[:12]}"
        now = _now()
        payload = {
            "trace_id": tid,
            "query": query.strip(),
            "answer": answer or "",
            "mode": mode or "",
            "response_lens": response_lens or "",
            "source_fact_ids": list(source_fact_ids or []),
            "rejected_fact_ids": list(rejected_fact_ids or []),
            "notes": notes or "",
            "metadata": metadata or {},
            "created_at": now,
        }
        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO reasoning_traces
                    (trace_id, query, answer, mode, response_lens,
                     source_fact_ids, rejected_fact_ids, notes, metadata, created_at)
                VALUES
                    (:trace_id, :query, :answer, :mode, :response_lens,
                     :source_fact_ids_json, :rejected_fact_ids_json,
                     :notes, :metadata_json, :created_at)
                """,
                {
                    **payload,
                    "source_fact_ids_json": _json_dump(payload["source_fact_ids"]),
                    "rejected_fact_ids_json": _json_dump(payload["rejected_fact_ids"]),
                    "metadata_json": _json_dump(payload["metadata"]),
                },
            )
        return payload

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM reasoning_traces WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()
        return self._trace_from_row(row) if row else None

    def list_traces(self, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        with self._db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM reasoning_traces").fetchone()[0]
            rows = conn.execute(
                """
                SELECT * FROM reasoning_traces
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "traces": [self._trace_from_row(r) for r in rows],
        }

    def memory_diff(self, *, since: str | None = None, limit: int = 100) -> dict[str, Any]:
        """Return a compact read model for recent memory changes."""
        self._parse_since(since)
        facts = self._recent_facts(since, limit)
        inbox = self._recent_inbox(since, limit)
        sources = self._recent_sources(since, limit)
        raw = self._recent_raw(since, limit)
        traces = self._recent_traces(since, limit)

        facts_inserted = [
            f for f in facts if since and (f.get("created_at") or "") >= since
        ]
        facts_updated = [
            f
            for f in facts
            if since
            and (f.get("updated_at") or "") >= since
            and (f.get("created_at") or "") < since
        ]
        return {
            "since": since,
            "limit": limit,
            "counts": {
                "facts_seen": len(facts),
                "facts_inserted": len(facts_inserted) if since else len(facts),
                "facts_updated": len(facts_updated) if since else 0,
                "inbox_changed": len(inbox),
                "sources_changed": len(sources),
                "raw_entries": len(raw),
                "reasoning_traces": len(traces),
            },
            "facts": facts,
            "inbox": inbox,
            "sources": sources,
            "raw": raw,
            "reasoning_traces": traces,
        }

    def _recent_facts(self, since: str | None, limit: int) -> list[dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if since:
            where = "WHERE created_at >= ? OR updated_at >= ?"
            params.extend([since, since])
        with self._db() as conn:
            if not self._table_exists(conn, "facts"):
                return []
            rows = conn.execute(
                f"""
                SELECT fact_id, claim, source, confidence, epistemic_state,
                       created_at, updated_at, metadata
                FROM facts
                {where}
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [
            {
                **dict(r),
                "metadata": _json_load(r["metadata"], {}),
            }
            for r in rows
        ]

    def _recent_inbox(self, since: str | None, limit: int) -> list[dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if since:
            where = "WHERE created_at >= ? OR updated_at >= ?"
            params.extend([since, since])
        with self._db() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM fact_inbox
                {where}
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [self._inbox_from_row(r) for r in rows]

    def _recent_sources(self, since: str | None, limit: int) -> list[dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if since:
            where = "WHERE created_at >= ? OR updated_at >= ?"
            params.extend([since, since])
        with self._db() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM source_registry
                {where}
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [self._source_from_row(r) for r in rows]

    def _recent_raw(self, since: str | None, limit: int) -> list[dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if since:
            where = "WHERE created_at >= ?"
            params.append(since)
        with self._db() as conn:
            if not self._table_exists(conn, "l0_raw_memory"):
                return []
            rows = conn.execute(
                f"""
                SELECT raw_id, source, source_type, language, char_count,
                       word_count, created_at
                FROM l0_raw_memory
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [dict(r) for r in rows]

    def _recent_traces(self, since: str | None, limit: int) -> list[dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if since:
            where = "WHERE created_at >= ?"
            params.append(since)
        with self._db() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM reasoning_traces
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [self._trace_from_row(r) for r in rows]

    @staticmethod
    def _source_from_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = _json_load(data.get("metadata"), {})
        return data

    @staticmethod
    def _inbox_from_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = _json_load(data.get("metadata"), {})
        return data

    @staticmethod
    def _trace_from_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["source_fact_ids"] = _json_load(data.get("source_fact_ids"), [])
        data["rejected_fact_ids"] = _json_load(data.get("rejected_fact_ids"), [])
        data["metadata"] = _json_load(data.get("metadata"), {})
        return data

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in INBOX_STATUSES:
            allowed = ", ".join(sorted(INBOX_STATUSES))
            raise ValueError(f"status must be one of: {allowed}")

    @staticmethod
    def _parse_since(since: str | None) -> None:
        if since:
            datetime.fromisoformat(since.replace("Z", "+00:00"))

    @staticmethod
    def _load_fact(fact_id: str) -> dict[str, Any] | None:
        from core.memory import get_fact

        return get_fact(fact_id)

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
        row = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table,),
        ).fetchone()
        return row is not None


_GLOBAL_MEMORY_OPS: MemoryOpsStore | None = None


def get_memory_ops(db_path: str | None = None) -> MemoryOpsStore:
    global _GLOBAL_MEMORY_OPS
    target = str(db_path or os.getenv("VELANTRIM_DB_PATH", SQLITE_PATH))
    if _GLOBAL_MEMORY_OPS is None or _GLOBAL_MEMORY_OPS.db_path != target:
        _GLOBAL_MEMORY_OPS = MemoryOpsStore(target)
    return _GLOBAL_MEMORY_OPS


def reset_memory_ops() -> None:
    global _GLOBAL_MEMORY_OPS
    _GLOBAL_MEMORY_OPS = None


def memory_ops_status(db_path: str | None = None) -> dict[str, Any]:
    store = get_memory_ops(db_path)
    path = Path(store.db_path)
    return {
        "enabled": True,
        "db_path": str(path),
        "db_exists": path.exists(),
        "tables": [
            "source_registry",
            "fact_inbox",
            "reasoning_traces",
        ],
    }


__all__ = [
    "INBOX_STATUSES",
    "MemoryOpsStore",
    "get_memory_ops",
    "memory_ops_status",
    "reset_memory_ops",
]
