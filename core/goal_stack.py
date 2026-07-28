"""
Innenwelt MVP — стек целей пользователя (SQLite, та же БД что memory).
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")

_GOALS_DDL = """
CREATE TABLE IF NOT EXISTS user_goals (
    goal_id     TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL DEFAULT 'default',
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'active',
    priority    INTEGER NOT NULL DEFAULT 0,
    keywords    TEXT NOT NULL DEFAULT '[]',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_goals_user_status
    ON user_goals(user_id, status);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Goal:
    goal_id: str
    user_id: str
    title: str
    description: str = ""
    status: str = "active"
    priority: int = 0
    keywords: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def search_terms(self) -> list[str]:
        terms: list[str] = []
        for part in (self.title, self.description):
            for w in part.lower().split():
                if len(w) >= 3:
                    terms.append(w)
        terms.extend(k.lower() for k in self.keywords if k)
        return list(dict.fromkeys(terms))


class GoalStack:
    def __init__(self, db_path: str = SQLITE_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(_GOALS_DDL)

    def create(
        self,
        *,
        user_id: str = "default",
        title: str,
        description: str = "",
        priority: int = 0,
        keywords: list[str] | None = None,
        goal_id: str | None = None,
    ) -> Goal:
        # FIX M1 (Claude audit 2026-07-28): SAFE_MODE is documented as
        # blocking ALL writes — this path never checked.
        from core.write_gate import ensure_writes_allowed

        ensure_writes_allowed()
        gid = goal_id or f"goal_{uuid.uuid4().hex[:12]}"
        now = _now()
        kw = json.dumps(keywords or [], ensure_ascii=False)
        goal = Goal(
            goal_id=gid,
            user_id=user_id or "default",
            title=title.strip(),
            description=(description or "").strip(),
            priority=int(priority),
            keywords=list(keywords or []),
            created_at=now,
            updated_at=now,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_goals
                (goal_id, user_id, title, description, status, priority,
                 keywords, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.goal_id,
                    goal.user_id,
                    goal.title,
                    goal.description,
                    goal.status,
                    goal.priority,
                    kw,
                    goal.created_at,
                    goal.updated_at,
                ),
            )
        return goal

    def list_goals(
        self,
        user_id: str = "default",
        *,
        status: str | None = "active",
        limit: int = 50,
    ) -> list[Goal]:
        q = "SELECT * FROM user_goals WHERE user_id = ?"
        params: list[Any] = [user_id or "default"]
        if status:
            q += " AND status = ?"
            params.append(status)
        q += " ORDER BY priority DESC, updated_at DESC LIMIT ?"
        params.append(max(1, min(limit, 200)))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(q, params).fetchall()
        return [self._row_to_goal(r) for r in rows]

    def get(self, goal_id: str) -> Goal | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM user_goals WHERE goal_id = ?", (goal_id,)
            ).fetchone()
        return self._row_to_goal(row) if row else None

    def update_status(self, goal_id: str, status: str) -> Goal | None:
        # FIX M1 (Claude audit 2026-07-28): see create() above.
        from core.write_gate import ensure_writes_allowed

        ensure_writes_allowed()
        allowed = {"active", "done", "cancelled"}
        if status not in allowed:
            raise ValueError(f"status должен быть одним из: {allowed}")
        now = _now()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                UPDATE user_goals SET status = ?, updated_at = ?
                WHERE goal_id = ?
                """,
                (status, now, goal_id),
            )
            if cur.rowcount == 0:
                return None
        return self.get(goal_id)

    def _row_to_goal(self, row: sqlite3.Row) -> Goal:
        kw_raw = row["keywords"] if row["keywords"] else "[]"
        try:
            keywords = json.loads(kw_raw)
        except json.JSONDecodeError:
            keywords = []
        if not isinstance(keywords, list):
            keywords = []
        return Goal(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            title=row["title"],
            description=row["description"] or "",
            status=row["status"],
            priority=int(row["priority"]),
            keywords=[str(k) for k in keywords],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


_stack: GoalStack | None = None


def get_goal_stack() -> GoalStack:
    global _stack
    path = os.getenv("VELANTRIM_DB_PATH", SQLITE_PATH)
    if _stack is None or _stack.db_path != path:
        _stack = GoalStack(path)
    return _stack


def reset_goal_stack() -> None:
    global _stack
    _stack = None


__all__ = ["Goal", "GoalStack", "get_goal_stack", "reset_goal_stack"]
