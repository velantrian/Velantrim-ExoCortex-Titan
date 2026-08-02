"""Small separate notes store for the web console.

Notes are intentionally kept outside the facts table. They are editable user
cards, not epistemic claims managed by TruthGate.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


def _default_db_path() -> str:
    return os.getenv("VELANTRIM_NOTES_DB", "./data/velantrim_notes.db")


class ConsoleNotesStore:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or _default_db_path()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS console_notes (
                    note_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )

    def _row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        try:
            data["tags"] = json.loads(data.get("tags") or "[]")
        except Exception:
            data["tags"] = []
        return data

    def list_notes(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM console_notes ORDER BY updated_at DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [self._row(r) for r in rows]

    def get_note(self, note_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM console_notes WHERE note_id = ?", (note_id,)
            ).fetchone()
        return self._row(row) if row else None

    def create_note(
        self,
        content: str,
        title: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("console_notes.create")
        now = int(time.time() * 1000)
        clean_content = " ".join((content or "").split())
        clean_title = " ".join((title or "").split()) or clean_content[:60] or "Note"
        note_id = f"note_{uuid.uuid4().hex[:10]}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO console_notes (note_id, title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (note_id, clean_title, clean_content, json.dumps(tags or [], ensure_ascii=False), now, now),
            )
        return self.get_note(note_id) or {"note_id": note_id, "title": clean_title, "content": clean_content}

    def update_note(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any] | None:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("console_notes.update")
        note = self.get_note(note_id)
        if not note:
            return None
        new_title = note["title"] if title is None else " ".join(title.split())
        new_content = note["content"] if content is None else " ".join(content.split())
        new_tags = note["tags"] if tags is None else tags
        now = int(time.time() * 1000)
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE console_notes
                SET title = ?, content = ?, tags = ?, updated_at = ?
                WHERE note_id = ?
                """,
                (new_title, new_content, json.dumps(new_tags, ensure_ascii=False), now, note_id),
            )
        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        from core.mutation_gate import ensure_user_mutations_allowed

        ensure_user_mutations_allowed("console_notes.delete")
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM console_notes WHERE note_id = ?", (note_id,))
            return cur.rowcount > 0


def apply_note_instruction(note: dict[str, Any], instruction: str) -> dict[str, str]:
    """Deterministic edit fallback; LLM can be added later without changing storage."""
    text = (instruction or "").strip()
    content = note.get("content", "")
    title = note.get("title", "")
    low = text.lower()
    if not text:
        return {"title": title, "content": content}
    if low.startswith(("замени на", "replace with")):
        repl = re_sub_prefix(text, ["замени на", "replace with"]).strip(" :—-")
        return {"title": title, "content": repl or content}
    if low.startswith(("добавь", "append", "add")):
        add = re_sub_prefix(text, ["добавь", "append", "add"]).strip(" :—-")
        return {"title": title, "content": (content + "\n" + add).strip()}
    if low.startswith(("переименуй", "rename")):
        new_title = re_sub_prefix(text, ["переименуй", "rename"]).strip(" :—-")
        return {"title": new_title or title, "content": content}
    return {"title": title, "content": (content + "\n" + text).strip()}


def re_sub_prefix(text: str, prefixes: list[str]) -> str:
    low = text.lower()
    for prefix in prefixes:
        if low.startswith(prefix):
            return text[len(prefix):]
    return text

