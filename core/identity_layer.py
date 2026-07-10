"""
🪪 core/identity_layer.py — Identity Layer (V8.7 Titan, из v80.5 F4)

Назначение: хранить НЕ факты о мире, а факты О СЕБЕ.
Ортогонально слоям L0–L6 — один факт может быть одновременно
L3 (долгосрочный граф) И F4 (часть идентичности).

Компоненты (F4 по v80.5):
  • Values      — неизменяемые ценности («я верю в…», «для меня важно…»)
  • Worldview   — картина мира и убеждения («я считаю что…», «мой взгляд на…»)
  • Biography   — автобиографические факты («я родился…», «я работал…»)
  • Compass     — эмоциональный компас («это меня вдохновляет», «это меня бесит»)

Отличие от CoreMemoryBlocks:
  CoreMemoryBlocks — профиль ДЛЯ system prompt (~500 токенов, оперативный).
  Identity Layer   — полная история личности, хранится в SQLite, извлекается
                     по запросу. Может быть 10 000+ записей.

Инварианты:
  I-ID1: Identity факт имеет self_axis (насколько это «Я»: 0..1)
  I-ID2: Identity факт может быть WORLD_FACT + self_axis=1 (факт о мире,
         глубоко связанный с идентичностью)
  I-ID3: Identity факты не подвержены decay (Emotional Ring Zero)
  I-ID4: Изменение identity факта → audit trail + версионирование
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.identity")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db")

_IDENTITY_DDL = """
CREATE TABLE IF NOT EXISTS identity_layer (
    identity_id   TEXT PRIMARY KEY,
    category      TEXT NOT NULL,  -- values | worldview | biography | compass
    content       TEXT NOT NULL,
    self_axis     REAL NOT NULL DEFAULT 1.0,  -- 1.0 = это Я, 0.0 = это мир
    confidence    REAL NOT NULL DEFAULT 0.95,
    emotional_salience REAL NOT NULL DEFAULT 0.85,
    source_message_id TEXT DEFAULT NULL,  -- связь с исходным сообщением
    provenance    TEXT NOT NULL DEFAULT '[]',
    version       INTEGER NOT NULL DEFAULT 1,
    tags          TEXT DEFAULT '[]',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_identity_category
    ON identity_layer(category);
CREATE INDEX IF NOT EXISTS idx_identity_self_axis
    ON identity_layer(self_axis);
"""


# ─── Типы ─────────────────────────────────────────────────────────────────────

class IdentityCategory(str, Enum):
    VALUES    = "values"     # «я верю в…», «для меня важно…»
    WORLDVIEW = "worldview"  # «я считаю что…», «мой взгляд на…»
    BIOGRAPHY = "biography"  # «я родился…», «я работал…», «я жил в…»
    COMPASS   = "compass"    # «это меня вдохновляет», «это меня бесит»


@dataclass
class IdentityFact:
    identity_id: str
    category: str
    content: str
    self_axis: float = 1.0
    confidence: float = 0.95
    emotional_salience: float = 0.85
    source_message_id: Optional[str] = None
    provenance: List[str] = field(default_factory=list)
    version: int = 1
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "category": self.category,
            "content": self.content,
            "self_axis": self.self_axis,
            "confidence": self.confidence,
            "emotional_salience": self.emotional_salience,
            "source_message_id": self.source_message_id,
            "provenance": self.provenance,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ─── Хранилище ────────────────────────────────────────────────────────────────

class IdentityStore:
    """
    Хранилище identity-фактов в SQLite (та же БД что и memory).

    Каждый факт имеет self_axis (0..1):
      1.0 = это про МЕНЯ (ценности, биография)
      0.5 = это про мир, но связано со мной (мой проект, моя работа)
      0.0 = чистый факт о мире — НЕ identity
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
            conn.executescript(_IDENTITY_DDL)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("IdentityStore DDL: %s", exc)

    # ── CRUD ───────────────────────────────────────────────────────────────

    def store(self, fact: IdentityFact) -> bool:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute(
                """INSERT OR REPLACE INTO identity_layer
                   (identity_id, category, content, self_axis, confidence,
                    emotional_salience, source_message_id, provenance, version,
                    tags, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fact.identity_id,
                    fact.category,
                    fact.content,
                    fact.self_axis,
                    fact.confidence,
                    fact.emotional_salience,
                    fact.source_message_id,
                    json.dumps(fact.provenance, ensure_ascii=False),
                    fact.version,
                    json.dumps(fact.tags, ensure_ascii=False),
                    fact.created_at,
                    fact.updated_at,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as exc:
            logger.error("IdentityStore.store: %s", exc)
            return False

    def get(self, identity_id: str) -> Optional[IdentityFact]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM identity_layer WHERE identity_id = ?",
                (identity_id,),
            ).fetchone()
            conn.close()
            if row:
                return self._row_to_fact(dict(row))
        except Exception:
            pass
        return None

    def list_by_category(
        self, category: str, limit: int = 50
    ) -> List[IdentityFact]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM identity_layer WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
            conn.close()
            return [self._row_to_fact(dict(r)) for r in rows]
        except Exception:
            return []

    def list_by_self_axis(
        self, min_axis: float = 0.5, limit: int = 50
    ) -> List[IdentityFact]:
        """Факты с self_axis >= min_axis — «это про меня»."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM identity_layer WHERE self_axis >= ? ORDER BY self_axis DESC LIMIT ?",
                (min_axis, limit),
            ).fetchall()
            conn.close()
            return [self._row_to_fact(dict(r)) for r in rows]
        except Exception:
            return []

    def search(self, query: str, limit: int = 10) -> List[IdentityFact]:
        """Простой текстовый поиск по content."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM identity_layer WHERE content LIKE ? ORDER BY self_axis DESC LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
            conn.close()
            return [self._row_to_fact(dict(r)) for r in rows]
        except Exception:
            return []

    def stats(self) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            total = conn.execute("SELECT COUNT(*) FROM identity_layer").fetchone()[0]
            by_cat = {}
            for cat in ("values", "worldview", "biography", "compass"):
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM identity_layer WHERE category = ?",
                    (cat,),
                ).fetchone()[0]
                by_cat[cat] = cnt
            conn.close()
            return {"total": total, "by_category": by_cat}
        except Exception:
            return {"total": 0, "by_category": {}}

    def _row_to_fact(self, row: Dict[str, Any]) -> IdentityFact:
        return IdentityFact(
            identity_id=row.get("identity_id", ""),
            category=row.get("category", ""),
            content=row.get("content", ""),
            self_axis=float(row.get("self_axis", 1.0)),
            confidence=float(row.get("confidence", 0.95)),
            emotional_salience=float(row.get("emotional_salience", 0.85)),
            source_message_id=row.get("source_message_id"),
            provenance=json.loads(row.get("provenance", "[]")),
            version=int(row.get("version", 1)),
            tags=json.loads(row.get("tags", "[]")),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )


# ─── Классификатор ────────────────────────────────────────────────────────────

def classify_identity(content: str) -> Optional[IdentityCategory]:
    """
    Rule-based классификация: это факт о мире или факт О СЕБЕ?
    0 токенов LLM.
    """
    c = content.lower()

    # Values
    if any(w in c for w in [
        "я верю", "для меня важно", "моя ценность", "я ценю",
        "мой принцип", "я никогда не", "я всегда",
        "i believe", "my value", "important to me",
    ]):
        return IdentityCategory.VALUES

    # Biography
    if any(w in c for w in [
        "я родился", "я вырос", "я жил", "я работал", "я учился",
        "моя семья", "мой отец", "моя мать", "мои дети",
        "i was born", "i grew up", "i lived", "i worked",
    ]):
        return IdentityCategory.BIOGRAPHY

    # Worldview
    if any(w in c for w in [
        "я считаю", "я думаю", "мой взгляд", "по-моему", "на мой взгляд",
        "моё мнение", "я убеждён", "я полагаю",
        "i think", "in my opinion", "i believe that",
    ]):
        return IdentityCategory.WORLDVIEW

    # Compass
    if any(w in c for w in [
        "меня вдохновляет", "меня бесит", "я люблю", "я ненавижу",
        "мне нравится", "меня раздражает", "это прекрасно", "это ужасно",
        "i love", "i hate", "inspires me", "drives me crazy",
        "infuriates", "terrible", "horrible", "makes me angry",
    ]):
        return IdentityCategory.COMPASS

    return None


def is_identity_content(content: str) -> bool:
    """Быстрая проверка: это про меня или про мир?"""
    return classify_identity(content) is not None


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_store: Optional[IdentityStore] = None


def get_identity_store() -> IdentityStore:
    global _store
    if _store is None:
        _store = IdentityStore()
    return _store


__all__ = [
    "IdentityStore",
    "IdentityFact",
    "IdentityCategory",
    "classify_identity",
    "is_identity_content",
    "get_identity_store",
]
