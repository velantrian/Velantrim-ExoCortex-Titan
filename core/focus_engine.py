"""
L4.5 FocusEngine — живой фокус внимания (RFC0053 MVP).

In-memory FocusVector + опциональный SQLite snapshot.
I29: без LLM для определения фокуса.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.feature_config import get_config

logger = logging.getLogger(__name__)


def is_focus_engine_enabled() -> bool:
    return get_config().app.enable_focus_engine


@dataclass
class FocusVector:
    goal_alignment: float = 0.5
    emotional_salience: float = 0.3
    pattern_of_ask: str = "general"
    domain_drift: str = "unknown"
    exploration_rate: float = 0.15
    updates: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_alignment": round(self.goal_alignment, 3),
            "emotional_salience": round(self.emotional_salience, 3),
            "pattern_of_ask": self.pattern_of_ask,
            "domain_drift": self.domain_drift,
            "exploration_rate": round(self.exploration_rate, 3),
            "updates": self.updates,
        }


class FocusEngine:
    def __init__(self, user_id: str = "default") -> None:
        self.user_id = user_id
        self.vector = FocusVector()
        self._db_path = Path(
            os.getenv("SQLITE_FOCUS_PATH", "./data/focus_engine.db")
        )
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(str(self._db_path))
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS focus_snapshots (
                        user_id TEXT NOT NULL,
                        vector_json TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def update_from_episode(
        self,
        *,
        query_hint: str = "",
        domain: str = "",
        importance: float = 0.5,
    ) -> FocusVector:
        self.vector.updates += 1
        if domain:
            self.vector.domain_drift = domain[:120]
        if query_hint:
            ql = query_hint.lower()
            if "?" in query_hint or ql.startswith(("как", "что", "why", "how")):
                self.vector.pattern_of_ask = "question"
            elif any(w in ql for w in ("ошиб", "баг", "fix", "проблем")):
                self.vector.pattern_of_ask = "debug"
            else:
                self.vector.pattern_of_ask = "statement"
        self.vector.goal_alignment = min(
            1.0, self.vector.goal_alignment * 0.9 + importance * 0.1
        )
        self.vector.emotional_salience = min(
            1.0, self.vector.emotional_salience * 0.85 + importance * 0.15
        )
        return self.vector

    def snapshot(self) -> None:
        with self._lock:
            conn = sqlite3.connect(str(self._db_path))
            try:
                conn.execute(
                    "INSERT INTO focus_snapshots (user_id, vector_json, created_at) VALUES (?,?,?)",
                    (
                        self.user_id,
                        json.dumps(self.vector.to_dict(), ensure_ascii=False),
                        time.time(),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def context_boost_for_entity(self, entity_name: str) -> float:
        """Множитель приоритета для recall (0..0.2)."""
        if not entity_name:
            return 0.0
        if self.vector.domain_drift.lower() in entity_name.lower():
            return 0.15 * self.vector.goal_alignment
        return 0.05 * self.vector.exploration_rate


_engines: dict[str, FocusEngine] = {}


def get_focus_engine(user_id: str = "default") -> FocusEngine:
    if user_id not in _engines:
        _engines[user_id] = FocusEngine(user_id)
    return _engines[user_id]


def reset_focus_engines() -> None:
    _engines.clear()


__all__ = [
    "FocusEngine",
    "FocusVector",
    "get_focus_engine",
    "is_focus_engine_enabled",
    "reset_focus_engines",
]
