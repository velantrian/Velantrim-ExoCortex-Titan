"""
📝 core/conversation_consolidation.py — Conversation Consolidation (V8.7 Titan)

Двухфазная консолидация диалога:
    Фаза 1 (реал-тайм): WorkingNotebook извлекает key_insights каждые 4-5 сообщений
    Фаза 2 (после завершения): GistSynthesizer анализирует логику и создаёт финальную суть

Результат: структурированный «блокнот диалога» с chat_id, main_topic, goal, key_insights,
conclusion — доступный для поиска «что мы обсуждали по теме X».

Инварианты:
    I-CC1: Только Slow Path. Не блокирует ответ.
    I-CC2: Блокнот хранится в SQLite (та же БД). Не пишет в граф истины.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.conversation_consolidation")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")

_CC_DDL = """
CREATE TABLE IF NOT EXISTS conversation_notebooks (
    chat_id      TEXT PRIMARY KEY,
    main_topic   TEXT NOT NULL DEFAULT '',
    user_goal    TEXT NOT NULL DEFAULT '',
    key_insights TEXT NOT NULL DEFAULT '[]',
    conclusion   TEXT NOT NULL DEFAULT '',
    related_chats TEXT NOT NULL DEFAULT '[]',
    facts_count  INTEGER NOT NULL DEFAULT 0,
    messages_count INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL,
    finalized_at TEXT DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_cc_main_topic ON conversation_notebooks(main_topic);
CREATE INDEX IF NOT EXISTS idx_cc_created ON conversation_notebooks(created_at);
"""


@dataclass
class ConversationNotebook:
    chat_id: str
    main_topic: str = ""
    user_goal: str = ""
    key_insights: List[str] = field(default_factory=list)
    conclusion: str = ""
    related_chats: List[str] = field(default_factory=list)
    facts_count: int = 0
    messages_count: int = 0
    produced_gist: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finalized_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "main_topic": self.main_topic,
            "user_goal": self.user_goal,
            "key_insights": self.key_insights,
            "conclusion": self.conclusion,
            "related_chats": self.related_chats,
            "facts_count": self.facts_count,
            "messages_count": self.messages_count,
            "produced_gist": self.produced_gist,
            "created_at": self.created_at,
        }


class ConversationConsolidator:
    """
    Двухфазная консолидация диалога.

    Использование:
        consolidator = ConversationConsolidator()

        # Фаза 1: записать временные insights
        consolidator.add_insight(chat_id="chat_42", insight="Обсуждаем архитектуру памяти")

        # Фаза 2: финализировать блокнот
        notebook = consolidator.finalize(chat_id="chat_42", summary="Обсудили storage-архитектуру. Решили использовать LadybugDB.")
    """

    def __init__(self, db_path: str = SQLITE_PATH):
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_CC_DDL)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("ConversationConsolidator DDL: %s", exc)

    # ── Фаза 1: Временные записи ──────────────────────────────────────────

    def add_insight(self, *, chat_id: str, insight: str) -> bool:
        """Добавить key_insight во временный блокнот (реал-тайм)."""
        if not chat_id or not insight:
            return False

        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")

            row = conn.execute(
                "SELECT key_insights, messages_count FROM conversation_notebooks WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()

            if row:
                insights = json.loads(row[0] or "[]")
                insights.append(insight[:300])
                msg_count = row[1] + 1
                # FIX (Claude audit 2026-07-28, Low): created_at is meant to
                # record when this notebook was first created (there's a
                # separate finalized_at for phase-2 completion, and
                # idx_cc_created exists for chronological queries) — it was
                # being reset to "now" on every insight append, so an
                # active notebook always looked freshly created.
                conn.execute(
                    "UPDATE conversation_notebooks SET key_insights = ?, messages_count = ? WHERE chat_id = ?",
                    (json.dumps(insights, ensure_ascii=False), msg_count, chat_id),
                )
            else:
                conn.execute(
                    "INSERT INTO conversation_notebooks (chat_id, key_insights, messages_count, created_at) VALUES (?, ?, ?, ?)",
                    (chat_id, json.dumps([insight[:300]], ensure_ascii=False), 1, datetime.now(timezone.utc).isoformat()),
                )
            conn.commit()
            conn.close()
            return True
        except Exception as exc:
            logger.debug("add_insight: %s", exc)
            return False

    # ── Фаза 2: Финальная консолидация ────────────────────────────────────

    def finalize(
        self,
        *,
        chat_id: str,
        summary: str = "",
        main_topic: str = "",
        user_goal: str = "",
        conclusion: str = "",
        facts_count: int = 0,
    ) -> Optional[ConversationNotebook]:
        """
        Финализировать блокнот диалога.

        Args:
            chat_id: ID диалога.
            summary: Gist-суть диалога (от essence/gist.py).
            main_topic: главная тема.
            user_goal: цель пользователя.
            conclusion: итоговый вывод.
            facts_count: сколько фактов использовано.

        Returns:
            ConversationNotebook или None.
        """
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                "SELECT * FROM conversation_notebooks WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()

            finalized_at = datetime.now(timezone.utc).isoformat()

            if row:
                conn.execute(
                    """UPDATE conversation_notebooks
                       SET main_topic = ?, user_goal = ?, conclusion = ?,
                           facts_count = ?, finalized_at = ?
                       WHERE chat_id = ?""",
                    (main_topic or row["main_topic"], user_goal, conclusion or summary[:500],
                     facts_count, finalized_at, chat_id),
                )
            else:
                conn.execute(
                    """INSERT INTO conversation_notebooks
                       (chat_id, main_topic, user_goal, key_insights, conclusion, facts_count, messages_count, created_at, finalized_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (chat_id, main_topic, user_goal, "[]", conclusion or summary[:500],
                     facts_count, 0, finalized_at, finalized_at),
                )

            conn.commit()
            conn.close()

            nb = self.get_notebook(chat_id)
            if nb:
                nb.produced_gist = True
                nb.finalized_at = finalized_at
            return nb
        except Exception as exc:
            logger.debug("finalize: %s", exc)
            return None

    # ── Поиск ─────────────────────────────────────────────────────────────

    def get_notebook(self, chat_id: str) -> Optional[ConversationNotebook]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM conversation_notebooks WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
            conn.close()
            if row:
                return ConversationNotebook(
                    chat_id=row["chat_id"],
                    main_topic=row["main_topic"],
                    user_goal=row["user_goal"],
                    key_insights=json.loads(row["key_insights"] or "[]"),
                    conclusion=row["conclusion"],
                    facts_count=row["facts_count"],
                    messages_count=row["messages_count"],
                    produced_gist=bool(row["finalized_at"]),
                    # FIX (Claude audit 2026-07-28, Low): none of the three
                    # read methods passed the stored created_at through —
                    # ConversationNotebook's dataclass default_factory
                    # silently fabricated a fresh datetime.now() every time,
                    # so the column was never actually readable regardless
                    # of what add_insight()'s SQL wrote.
                    created_at=row["created_at"],
                    finalized_at=row["finalized_at"],
                )
        except Exception:
            pass
        return None

    def search(self, query: str, limit: int = 10) -> List[ConversationNotebook]:
        """Поиск по блокнотам диалогов."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM conversation_notebooks
                   WHERE main_topic LIKE ? OR user_goal LIKE ? OR conclusion LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            conn.close()
            return [
                ConversationNotebook(
                    chat_id=r["chat_id"], main_topic=r["main_topic"],
                    user_goal=r["user_goal"], key_insights=json.loads(r["key_insights"] or "[]"),
                    conclusion=r["conclusion"], facts_count=r["facts_count"],
                    messages_count=r["messages_count"], produced_gist=bool(r["finalized_at"]),
                    created_at=r["created_at"], finalized_at=r["finalized_at"],
                ) for r in rows
            ]
        except Exception:
            return []

    def list_recent(self, limit: int = 10) -> List[ConversationNotebook]:
        """Последние финализированные блокноты."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM conversation_notebooks WHERE finalized_at IS NOT NULL ORDER BY finalized_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            return [
                ConversationNotebook(
                    chat_id=r["chat_id"], main_topic=r["main_topic"],
                    user_goal=r["user_goal"], key_insights=json.loads(r["key_insights"] or "[]"),
                    conclusion=r["conclusion"], facts_count=r["facts_count"],
                    messages_count=r["messages_count"], produced_gist=True,
                    created_at=r["created_at"], finalized_at=r["finalized_at"],
                ) for r in rows
            ]
        except Exception:
            return []

    def stats(self) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            total = conn.execute("SELECT COUNT(*) FROM conversation_notebooks").fetchone()[0]
            finalized = conn.execute("SELECT COUNT(*) FROM conversation_notebooks WHERE finalized_at IS NOT NULL").fetchone()[0]
            conn.close()
            return {"total_notebooks": total, "finalized": finalized}
        except Exception:
            return {"total_notebooks": 0, "finalized": 0}


# Глобальный экземпляр
_consolidator: Optional[ConversationConsolidator] = None


def get_conversation_consolidator() -> ConversationConsolidator:
    global _consolidator
    if _consolidator is None:
        _consolidator = ConversationConsolidator()
    return _consolidator


__all__ = ["ConversationConsolidator", "ConversationNotebook", "get_conversation_consolidator"]
