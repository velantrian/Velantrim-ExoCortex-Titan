"""
EdgeSuggester — HITL-инструмент (Crystal RFC0063 / I64).

Сканирует факты на скрытые связи (token overlap / shared domain),
пишет ТОЛЬКО в suggested_edges. В relations — только после approve().

Скан — Slow Path only. Embeddings не обязательны (lite/standard CPU).
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from core.dual_process import require_slow_path, slow_only
from core.feature_config import get_config

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9_]{3,}")
_STOP = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "are", "was",
    "что", "как", "это", "для", "или", "при", "без", "над", "под",
    "есть", "быть", "был", "была", "были", "также", "если", "когда",
})


def is_edge_suggester_enabled() -> bool:
    return bool(getattr(get_config().app, "enable_edge_suggester", False))


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _tokens(text: str) -> set[str]:
    out: set[str] = set()
    for m in _TOKEN_RE.findall(text or ""):
        t = m.lower()
        if t not in _STOP and not t.isdigit():
            out.add(t)
    return out


def _domain(fact: dict[str, Any]) -> str | None:
    meta = fact.get("metadata") or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except json.JSONDecodeError:
            meta = {}
    if not isinstance(meta, dict):
        return None
    d = meta.get("domain") or meta.get("content_domain")
    return str(d) if d else None


@dataclass
class EdgeSuggestion:
    suggestion_id: str
    from_fact_id: str
    to_fact_id: str
    relation_type: str
    score: float
    reason: str
    evidence: dict[str, Any]
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "from_fact_id": self.from_fact_id,
            "to_fact_id": self.to_fact_id,
            "relation_type": self.relation_type,
            "score": round(self.score, 4),
            "reason": self.reason,
            "evidence": self.evidence,
            "status": self.status,
        }


class EdgeSuggester:
    """I64: никогда не пишет в relations из scan()."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS suggested_edges (
                    suggestion_id     TEXT PRIMARY KEY,
                    from_fact_id      TEXT NOT NULL,
                    to_fact_id        TEXT NOT NULL,
                    relation_type     TEXT NOT NULL DEFAULT 'analogous_to',
                    score             REAL NOT NULL DEFAULT 0.0,
                    reason            TEXT NOT NULL DEFAULT '',
                    evidence_json     TEXT NOT NULL DEFAULT '{}',
                    status            TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'rejected')),
                    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
                    resolved_at       TEXT,
                    resolved_by       TEXT,
                    relation_id       TEXT,
                    CHECK (from_fact_id != to_fact_id)
                );
                CREATE INDEX IF NOT EXISTS idx_suggested_edges_status
                    ON suggested_edges(status, created_at);
                """
            )
            conn.commit()

    def _existing_relation_pairs(self, conn: sqlite3.Connection) -> set[tuple[str, str]]:
        try:
            rows = conn.execute(
                "SELECT from_fact_id, to_fact_id FROM relations"
            ).fetchall()
        except sqlite3.OperationalError:
            return set()
        pairs: set[tuple[str, str]] = set()
        for r in rows:
            a, b = r["from_fact_id"], r["to_fact_id"]
            pairs.add((a, b) if a < b else (b, a))
        return pairs

    def _pending_pairs(self, conn: sqlite3.Connection) -> set[tuple[str, str, str]]:
        rows = conn.execute(
            "SELECT from_fact_id, to_fact_id, relation_type FROM suggested_edges "
            "WHERE status = 'pending'"
        ).fetchall()
        out: set[tuple[str, str, str]] = set()
        for r in rows:
            a, b = r["from_fact_id"], r["to_fact_id"]
            key = (a, b) if a < b else (b, a)
            out.add((key[0], key[1], r["relation_type"]))
        return out

    @slow_only("EdgeSuggester.scan")
    def scan(
        self,
        facts: list[dict[str, Any]],
        *,
        min_shared_tokens: int = 2,
        min_score: float = 0.35,
        limit: int = 50,
        relation_type: str = "analogous_to",
    ) -> list[dict[str, Any]]:
        """Найти кандидатов и сохранить как pending. Не трогает relations."""
        require_slow_path("EdgeSuggester.scan")
        if not facts:
            return []

        prepared: list[tuple[str, set[str], str | None, str]] = []
        for f in facts:
            fid = f.get("fact_id") or f.get("id")
            if not fid:
                continue
            claim = str(f.get("claim") or f.get("content") or "")
            toks = _tokens(claim)
            if len(toks) < min_shared_tokens:
                continue
            prepared.append((str(fid), toks, _domain(f), claim[:200]))

        created: list[dict[str, Any]] = []
        with self._connect() as conn:
            existing = self._existing_relation_pairs(conn)
            pending = self._pending_pairs(conn)
            for i in range(len(prepared)):
                if len(created) >= limit:
                    break
                fid_a, toks_a, dom_a, _ = prepared[i]
                for j in range(i + 1, len(prepared)):
                    if len(created) >= limit:
                        break
                    fid_b, toks_b, dom_b, _ = prepared[j]
                    pair = (fid_a, fid_b) if fid_a < fid_b else (fid_b, fid_a)
                    if pair in existing:
                        continue
                    if (pair[0], pair[1], relation_type) in pending:
                        continue
                    shared = toks_a & toks_b
                    if len(shared) < min_shared_tokens:
                        continue
                    union = toks_a | toks_b
                    jaccard = len(shared) / max(1, len(union))
                    score = jaccard
                    reason_parts = [f"shared_tokens={len(shared)}", f"jaccard={jaccard:.3f}"]
                    if dom_a and dom_b and dom_a == dom_b:
                        score = min(1.0, score + 0.15)
                        reason_parts.append(f"same_domain={dom_a}")
                    if score < min_score:
                        continue
                    sid = f"sugg_{uuid.uuid4().hex[:12]}"
                    evidence = {
                        "shared_tokens": sorted(shared)[:20],
                        "domain_a": dom_a,
                        "domain_b": dom_b,
                    }
                    reason = "; ".join(reason_parts)
                    conn.execute(
                        """
                        INSERT INTO suggested_edges (
                            suggestion_id, from_fact_id, to_fact_id, relation_type,
                            score, reason, evidence_json, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                        """,
                        (
                            sid,
                            pair[0],
                            pair[1],
                            relation_type,
                            score,
                            reason,
                            json.dumps(evidence, ensure_ascii=False),
                            _now(),
                        ),
                    )
                    pending.add((pair[0], pair[1], relation_type))
                    created.append(
                        EdgeSuggestion(
                            suggestion_id=sid,
                            from_fact_id=pair[0],
                            to_fact_id=pair[1],
                            relation_type=relation_type,
                            score=score,
                            reason=reason,
                            evidence=evidence,
                        ).to_dict()
                    )
            conn.commit()
        logger.info("EdgeSuggester.scan: created=%d from facts=%d", len(created), len(facts))
        return created

    def list_suggestions(
        self,
        *,
        status: str = "pending",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT suggestion_id, from_fact_id, to_fact_id, relation_type,
                       score, reason, evidence_json, status, created_at,
                       resolved_at, resolved_by, relation_id
                FROM suggested_edges
                WHERE (? = 'all' OR status = ?)
                ORDER BY score DESC, created_at DESC
                LIMIT ?
                """,
                (status, status, limit),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "suggestion_id": r["suggestion_id"],
                    "from_fact_id": r["from_fact_id"],
                    "to_fact_id": r["to_fact_id"],
                    "relation_type": r["relation_type"],
                    "score": r["score"],
                    "reason": r["reason"],
                    "evidence": json.loads(r["evidence_json"] or "{}"),
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "resolved_at": r["resolved_at"],
                    "resolved_by": r["resolved_by"],
                    "relation_id": r["relation_id"],
                }
            )
        return out

    def reject(self, suggestion_id: str, *, by: str = "auditor") -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM suggested_edges WHERE suggestion_id = ?",
                (suggestion_id,),
            ).fetchone()
            if row is None:
                raise KeyError(suggestion_id)
            if row["status"] != "pending":
                return dict(row)
            conn.execute(
                """
                UPDATE suggested_edges
                SET status = 'rejected', resolved_at = ?, resolved_by = ?
                WHERE suggestion_id = ?
                """,
                (_now(), by, suggestion_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM suggested_edges WHERE suggestion_id = ?",
                (suggestion_id,),
            ).fetchone()
        return {
            "suggestion_id": row["suggestion_id"],
            "status": row["status"],
            "resolved_at": row["resolved_at"],
            "resolved_by": row["resolved_by"],
        }

    def approve(
        self,
        suggestion_id: str,
        *,
        by: str = "auditor",
        write_relation: bool = True,
    ) -> dict[str, Any]:
        """После HITL: пометить approved и опционально создать relation (hypothetical)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM suggested_edges WHERE suggestion_id = ?",
                (suggestion_id,),
            ).fetchone()
            if row is None:
                raise KeyError(suggestion_id)
            if row["status"] == "approved":
                return {
                    "suggestion_id": suggestion_id,
                    "status": "approved",
                    "relation_id": row["relation_id"],
                    "idempotent": True,
                }
            if row["status"] != "pending":
                raise ValueError(f"suggestion {suggestion_id} is {row['status']}")

            relation_id: str | None = None
            if write_relation:
                from core.causal_graph import CausalGraph

                cg = CausalGraph(conn)
                relation_id = cg.add_relation(
                    from_fact_id=row["from_fact_id"],
                    to_fact_id=row["to_fact_id"],
                    relation_type=row["relation_type"],
                    confidence=float(row["score"]),
                    knowledge_status="hypothetical",
                    inference_source="autolinker",
                    truth_status="hypothesis",
                    review_state="pending",
                    metadata={
                        "suggestion_id": suggestion_id,
                        "approved_by": by,
                        "edge_suggester": True,
                    },
                )
                # FIX M6 (Claude audit 2026-07-28): add_relation() uses
                # INSERT OR IGNORE, so approving a second pending
                # suggestion for the same underlying (from, to, type) pair
                # — created by a racing scan() before this approval, or two
                # concurrent approve() calls — silently no-ops against the
                # relations UNIQUE constraint. relation_id above is then a
                # freshly generated uuid that was never actually written:
                # a phantom reference. Detect that and fall back to the
                # real, already-existing relation_id instead of recording
                # a dangling one.
                if cg.get_relation(relation_id) is None:
                    existing = conn.execute(
                        """
                        SELECT relation_id FROM relations
                        WHERE from_fact_id = ? AND to_fact_id = ?
                          AND relation_type = ? AND inference_source = 'autolinker'
                        """,
                        (row["from_fact_id"], row["to_fact_id"], row["relation_type"]),
                    ).fetchone()
                    relation_id = existing["relation_id"] if existing else None

            conn.execute(
                """
                UPDATE suggested_edges
                SET status = 'approved', resolved_at = ?, resolved_by = ?,
                    relation_id = ?
                WHERE suggestion_id = ?
                """,
                (_now(), by, relation_id, suggestion_id),
            )
            conn.commit()

        return {
            "suggestion_id": suggestion_id,
            "status": "approved",
            "relation_id": relation_id,
            "from_fact_id": row["from_fact_id"],
            "to_fact_id": row["to_fact_id"],
            "relation_type": row["relation_type"],
            "resolved_by": by,
        }


_suggester: EdgeSuggester | None = None


def get_edge_suggester(db_path: str | None = None) -> EdgeSuggester:
    global _suggester
    if db_path is not None:
        return EdgeSuggester(db_path)
    if _suggester is None:
        from core.memory import SQLITE_PATH

        _suggester = EdgeSuggester(SQLITE_PATH)
    return _suggester


def reset_edge_suggester() -> None:
    global _suggester
    _suggester = None


__all__ = [
    "EdgeSuggestion",
    "EdgeSuggester",
    "get_edge_suggester",
    "is_edge_suggester_enabled",
    "reset_edge_suggester",
]
