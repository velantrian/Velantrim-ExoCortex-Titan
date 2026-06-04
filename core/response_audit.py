"""
L4.5 ResponseAuditWorker — аудит ответов (RFC0052 MVP).

I28: только Slow Path через EventBus (не блокирует Fast Path).
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.feature_config import get_config

logger = logging.getLogger(__name__)


def is_response_audit_enabled() -> bool:
    return get_config().app.enable_response_audit


@dataclass
class ResponseAuditRecord:
    audit_id: str
    conversation_id: str
    response_id: str
    human_summary: str
    importance_score: float
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: str = "NEW"
    faithfulness_score: float | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "audit_id": self.audit_id,
            "conversation_id": self.conversation_id,
            "response_id": self.response_id,
            "human_summary": self.human_summary,
            "importance_score": round(self.importance_score, 3),
            "tags": self.tags,
            "dependencies": self.dependencies,
            "status": self.status,
            "created_at": self.created_at,
        }
        if self.faithfulness_score is not None:
            out["faithfulness_score"] = round(self.faithfulness_score, 4)
        return out


class ResponseAuditStore:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init()

    def _init(self) -> None:
        with self._lock:
            conn = sqlite3.connect(str(self._path))
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS response_audits (
                        audit_id TEXT PRIMARY KEY,
                        conversation_id TEXT,
                        response_id TEXT,
                        human_summary TEXT,
                        importance_score REAL,
                        tags_json TEXT,
                        deps_json TEXT,
                        status TEXT,
                        faithfulness_score REAL,
                        created_at TEXT
                    )
                    """
                )
                cols = {
                    r[1] for r in conn.execute("PRAGMA table_info(response_audits)").fetchall()
                }
                if "faithfulness_score" not in cols:
                    conn.execute(
                        "ALTER TABLE response_audits ADD COLUMN faithfulness_score REAL"
                    )
                conn.commit()
            finally:
                conn.close()

    def save(self, rec: ResponseAuditRecord) -> None:
        import json

        with self._lock:
            conn = sqlite3.connect(str(self._path))
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO response_audits
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        rec.audit_id,
                        rec.conversation_id,
                        rec.response_id,
                        rec.human_summary,
                        rec.importance_score,
                        json.dumps(rec.tags, ensure_ascii=False),
                        json.dumps(rec.dependencies, ensure_ascii=False),
                        rec.status,
                        rec.faithfulness_score,
                        rec.created_at,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def list_recent(self, *, limit: int = 20) -> list[dict[str, Any]]:
        import json

        with self._lock:
            conn = sqlite3.connect(str(self._path))
            try:
                rows = conn.execute(
                    """
                    SELECT audit_id, conversation_id, response_id, human_summary,
                           importance_score, tags_json, deps_json, status, created_at
                    FROM response_audits
                    ORDER BY created_at DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                out = []
                for row in rows:
                    out.append(
                        {
                            "audit_id": row[0],
                            "conversation_id": row[1],
                            "response_id": row[2],
                            "human_summary": row[3],
                            "importance_score": row[4],
                            "tags": json.loads(row[5] or "[]"),
                            "dependencies": json.loads(row[6] or "[]"),
                            "status": row[7],
                            "created_at": row[8],
                        }
                    )
                return out
            finally:
                conn.close()


_store: ResponseAuditStore | None = None


def get_audit_store() -> ResponseAuditStore:
    global _store
    if _store is None:
        import os

        path = Path(os.getenv("SQLITE_AUDIT_PATH", "./data/response_audit.db"))
        _store = ResponseAuditStore(path)
    return _store


async def audit_response_generated(
    *,
    conversation_id: str,
    response_id: str,
    reply_preview: str,
    fact_ids: list[str] | None = None,
    source_facts: list[dict[str, Any]] | None = None,
) -> ResponseAuditRecord | None:
    """
    Фаза 1–2 MVP: эвристика без LLM.
    """
    if not is_response_audit_enabled():
        return None

    text = (reply_preview or "").strip()
    importance = min(1.0, 0.3 + len(text) / 2000.0)
    tags: list[str] = []
    if "?" in text:
        tags.append("question")
    if len(text) > 400:
        tags.append("long_form")

    faith_score: float | None = None
    try:
        from core.output_faithfulness import check_response_faithfulness

        if source_facts:
            fr = check_response_faithfulness(text, source_facts)
            if fr is not None:
                faith_score = fr.score
    except Exception as exc:
        logger.debug("audit faithfulness: %s", exc)

    rec = ResponseAuditRecord(
        audit_id=f"aud_{uuid.uuid4().hex[:12]}",
        conversation_id=conversation_id,
        response_id=response_id,
        human_summary=text[:280],
        importance_score=importance,
        tags=tags,
        dependencies=list(fact_ids or []),
        faithfulness_score=faith_score,
    )
    get_audit_store().save(rec)
    logger.debug(
        "ResponseAudit: id=%s importance=%.2f",
        rec.audit_id,
        rec.importance_score,
    )
    return rec


def reset_response_audit() -> None:
    global _store
    _store = None


__all__ = [
    "ResponseAuditRecord",
    "audit_response_generated",
    "get_audit_store",
    "is_response_audit_enabled",
    "reset_response_audit",
]
