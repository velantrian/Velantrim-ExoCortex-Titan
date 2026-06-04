"""
Umwelt MVP — хранилище perception-записей (layer 99) в SQLite.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")
UMWELT_LAYER = 99
DEFAULT_SEED_PATH = Path(__file__).resolve().parents[1] / "docs" / "seed" / "umwelt_mvp_seed.json"

_DDL = """
CREATE TABLE IF NOT EXISTS umwelt_perceptions (
    perception_id   TEXT PRIMARY KEY,
    object_key      TEXT NOT NULL,
    object_label_ru TEXT DEFAULT '',
    perceiver_id    TEXT NOT NULL,
    perceiver         TEXT NOT NULL,
    perceiver_category TEXT DEFAULT '',
    statement       TEXT NOT NULL,
    affordances     TEXT NOT NULL DEFAULT '[]',
    knowledge_status TEXT NOT NULL DEFAULT 'interpreted',
    confidence      REAL NOT NULL DEFAULT 0.8,
    layer           INTEGER NOT NULL DEFAULT 99,
    source          TEXT DEFAULT 'umwelt',
    related_json    TEXT DEFAULT '[]',
    metadata_json   TEXT DEFAULT '{}',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_umwelt_object ON umwelt_perceptions(object_key);
CREATE INDEX IF NOT EXISTS idx_umwelt_perceiver ON umwelt_perceptions(perceiver_id);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class UmweltPerception:
    perception_id: str
    object_key: str
    statement: str
    perceiver_id: str
    perceiver: str
    object_label_ru: str = ""
    perceiver_category: str = ""
    affordances: list[str] = field(default_factory=list)
    knowledge_status: str = "interpreted"
    confidence: float = 0.8
    layer: int = UMWELT_LAYER
    source: str = "umwelt"
    related_perceptions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["domain"] = "perception"
        return d


class UmweltStore:
    def __init__(self, db_path: str = SQLITE_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(_DDL)

    def upsert(self, p: UmweltPerception) -> UmweltPerception:
        now = _now()
        if not p.created_at:
            p.created_at = now
        p.updated_at = now
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO umwelt_perceptions (
                    perception_id, object_key, object_label_ru, perceiver_id,
                    perceiver, perceiver_category, statement, affordances,
                    knowledge_status, confidence, layer, source,
                    related_json, metadata_json, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(perception_id) DO UPDATE SET
                    object_key=excluded.object_key,
                    object_label_ru=excluded.object_label_ru,
                    perceiver_id=excluded.perceiver_id,
                    perceiver=excluded.perceiver,
                    perceiver_category=excluded.perceiver_category,
                    statement=excluded.statement,
                    affordances=excluded.affordances,
                    knowledge_status=excluded.knowledge_status,
                    confidence=excluded.confidence,
                    source=excluded.source,
                    related_json=excluded.related_json,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (
                    p.perception_id,
                    p.object_key,
                    p.object_label_ru,
                    p.perceiver_id,
                    p.perceiver,
                    p.perceiver_category,
                    p.statement,
                    json.dumps(p.affordances, ensure_ascii=False),
                    p.knowledge_status,
                    float(p.confidence),
                    int(p.layer),
                    p.source,
                    json.dumps(p.related_perceptions, ensure_ascii=False),
                    json.dumps(p.metadata, ensure_ascii=False),
                    p.created_at,
                    p.updated_at,
                ),
            )
        return p

    def get(self, perception_id: str) -> UmweltPerception | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM umwelt_perceptions WHERE perception_id = ?",
                (perception_id,),
            ).fetchone()
        return self._row_to_perception(row) if row else None

    def list_by_object(
        self,
        object_key: str,
        *,
        perceiver_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[UmweltPerception]:
        q = "SELECT * FROM umwelt_perceptions WHERE object_key = ?"
        params: list[Any] = [object_key]
        if perceiver_ids:
            placeholders = ",".join("?" * len(perceiver_ids))
            q += f" AND perceiver_id IN ({placeholders})"
            params.extend(perceiver_ids)
        q += " ORDER BY confidence DESC LIMIT ?"
        params.append(max(1, min(limit, 100)))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(q, params).fetchall()
        return [self._row_to_perception(r) for r in rows]

    def list_objects(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT object_key, MAX(object_label_ru) AS label_ru,
                       COUNT(*) AS perception_count
                FROM umwelt_perceptions
                GROUP BY object_key
                ORDER BY object_key
                """
            ).fetchall()
        return [
            {
                "object_key": r[0],
                "object_label_ru": r[1] or r[0],
                "perception_count": r[2],
            }
            for r in rows
        ]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM umwelt_perceptions"
            ).fetchone()
        return int(row[0]) if row else 0

    def _row_to_perception(self, row: sqlite3.Row) -> UmweltPerception:
        aff = json.loads(row["affordances"] or "[]")
        rel = json.loads(row["related_json"] or "[]")
        meta = json.loads(row["metadata_json"] or "{}")
        return UmweltPerception(
            perception_id=row["perception_id"],
            object_key=row["object_key"],
            object_label_ru=row["object_label_ru"] or "",
            perceiver_id=row["perceiver_id"],
            perceiver=row["perceiver"],
            perceiver_category=row["perceiver_category"] or "",
            statement=row["statement"],
            affordances=aff if isinstance(aff, list) else [],
            knowledge_status=row["knowledge_status"],
            confidence=float(row["confidence"]),
            layer=int(row["layer"]),
            source=row["source"] or "umwelt",
            related_perceptions=rel if isinstance(rel, list) else [],
            metadata=meta if isinstance(meta, dict) else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


_store: UmweltStore | None = None


def get_umwelt_store() -> UmweltStore:
    global _store
    path = os.getenv("VELANTRIM_DB_PATH", SQLITE_PATH)
    if _store is None or _store.db_path != path:
        _store = UmweltStore(path)
    return _store


def reset_umwelt_store() -> None:
    global _store
    _store = None


def perception_from_seed_record(rec: dict[str, Any]) -> UmweltPerception:
    pid = rec.get("id") or f"perception_{uuid.uuid4().hex[:12]}"
    return UmweltPerception(
        perception_id=pid,
        object_key=str(rec.get("object", "unknown")),
        object_label_ru=str(rec.get("object_label_ru", "")),
        perceiver_id=str(rec.get("perceiver_id", "agent:unknown")),
        perceiver=str(rec.get("perceiver", "unknown")),
        perceiver_category=str(rec.get("perceiver_category", "")),
        statement=str(rec.get("statement", "")),
        affordances=list(rec.get("affordances") or []),
        knowledge_status=str(rec.get("knowledge_status", "interpreted")),
        confidence=float(rec.get("confidence", 0.8)),
        source=str(rec.get("source", "umwelt_seed")),
        related_perceptions=list(rec.get("related_perceptions") or []),
        metadata={"domain": "perception", "layer": UMWELT_LAYER},
    )


def load_seed_file(path: Path | None = None) -> dict[str, Any]:
    """Загрузить JSON seed в umwelt_perceptions."""
    seed_path = path or DEFAULT_SEED_PATH
    if not seed_path.is_file():
        raise FileNotFoundError(f"Seed не найден: {seed_path}")
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    records = data.get("perceptions") or []
    store = get_umwelt_store()
    loaded = 0
    for rec in records:
        store.upsert(perception_from_seed_record(rec))
        loaded += 1
    return {"loaded": loaded, "path": str(seed_path), "total_in_db": store.count()}


def perception_to_fact_dict(p: UmweltPerception) -> dict[str, Any]:
    """Маппинг в L1 факт с layer=99 (CognitiveFact-совместимый metadata)."""
    meta = {
        "layer": UMWELT_LAYER,
        "domain": "perception",
        "object": p.object_key,
        "object_label_ru": p.object_label_ru,
        "perceiver_id": p.perceiver_id,
        "perceiver": p.perceiver,
        "perceiver_category": p.perceiver_category,
        "affordances": p.affordances,
        "knowledge_status": p.knowledge_status,
        "related_perceptions": p.related_perceptions,
        "umwelt_perception_id": p.perception_id,
    }
    meta.update(p.metadata or {})
    return {
        "fact_id": p.perception_id,
        "claim": p.statement,
        "source": p.source,
        "confidence": p.confidence,
        "metadata": meta,
    }


def sync_perceptions_to_memory(
    object_key: str | None = None,
) -> dict[str, int]:
    """Опционально: продублировать perceptions как Observed-факты в memory."""
    store = get_umwelt_store()
    from core.memory import get_fact

    if object_key:
        items = store.list_by_object(object_key)
    else:
        items = []
        for obj in store.list_objects():
            items.extend(store.list_by_object(obj["object_key"], limit=50))

    created = skipped = 0
    from core.cognitive_store import is_cognitive_store_enabled, save_fact_dict
    from core.memory import store_fact

    use_store = is_cognitive_store_enabled()
    for p in items:
        if get_fact(p.perception_id):
            skipped += 1
            continue
        payload = perception_to_fact_dict(p)
        if use_store:
            save_fact_dict(payload, ensure_raw=False, link_provenance=False)
        else:
            store_fact(payload)
        created += 1
    return {"created": created, "skipped": skipped, "total": len(items)}


__all__ = [
    "UMWELT_LAYER",
    "UmweltPerception",
    "UmweltStore",
    "get_umwelt_store",
    "load_seed_file",
    "perception_from_seed_record",
    "perception_to_fact_dict",
    "reset_umwelt_store",
    "sync_perceptions_to_memory",
]
