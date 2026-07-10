"""
🔧 core/kb_graph_build.py — устойчивая пакетная запись KB-рёбер в SQLite.

Отделяет массовый ingest рёбер от медленного per-edge CausalGraph.add_relation().
Перед записью удаляет только ранее сгенерированные KB-рёбра (metadata.kb_build=true),
не трогая разговорные/ручные связи.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from core.causal_graph import FORWARD_RELATION_TYPES, INVERSE_RELATIONS, VALID_RELATION_TYPES

KB_BUILD_META_KEY = "kb_build"
KB_BUILD_TAG = "world_skills_core_v1"


def ensure_relations_table(conn: sqlite3.Connection) -> None:
    """Create the causal storage required by a fresh KB graph build."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS relations (
            relation_id TEXT PRIMARY KEY,
            from_fact_id TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
            to_fact_id TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
            relation_type TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.8,
            knowledge_status TEXT NOT NULL DEFAULT 'known',
            inference_source TEXT DEFAULT NULL,
            truth_status TEXT DEFAULT 'validated',
            review_state TEXT DEFAULT 'approved',
            evidence_ref TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            valid_from TEXT NOT NULL DEFAULT (datetime('now')),
            valid_to TEXT,
            metadata TEXT,
            CHECK (from_fact_id != to_fact_id),
            UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
        );
        CREATE INDEX IF NOT EXISTS idx_relations_from
            ON relations(from_fact_id, relation_type);
        CREATE INDEX IF NOT EXISTS idx_relations_to
            ON relations(to_fact_id, relation_type);
    """)


def edge_metadata(edge: dict[str, Any]) -> dict[str, Any]:
    """Нормализовать metadata ребра для SQLite."""
    meta: dict[str, Any] = {
        KB_BUILD_META_KEY: True,
        "kb_build_tag": KB_BUILD_TAG,
        "edge_basis": edge.get("edge_basis", "unknown"),
    }
    if edge.get("semantic_score") is not None:
        meta["semantic_score"] = edge["semantic_score"]
    if edge.get("matched_terms"):
        meta["matched_terms"] = edge["matched_terms"]
    if edge.get("evidence"):
        meta["evidence"] = edge["evidence"]
    if edge.get("source_file"):
        meta["source_file"] = edge["source_file"]
    if edge.get("source_line") is not None:
        meta["source_line"] = edge["source_line"]
    return meta


def delete_kb_generated_edges(conn: sqlite3.Connection, *, wipe_all: bool = False) -> int:
    """Удалить автогенерированные KB-рёбра (и их inverse-пары).

    wipe_all=True — очистить всю таблицу relations (только для выделенных KB-БД).
    """
    ensure_relations_table(conn)
    if wipe_all:
        cur = conn.execute("DELETE FROM relations")
        conn.commit()
        return cur.rowcount

    rows = conn.execute("SELECT relation_id, metadata FROM relations").fetchall()
    to_delete: list[str] = []
    for relation_id, raw in rows:
        try:
            meta = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            meta = {}
        if meta.get(KB_BUILD_META_KEY) is True:
            to_delete.append(relation_id)
    if not to_delete:
        return 0
    chunk = 500
    deleted = 0
    for i in range(0, len(to_delete), chunk):
        part = to_delete[i:i + chunk]
        placeholders = ",".join("?" * len(part))
        cur = conn.execute(
            f"DELETE FROM relations WHERE relation_id IN ({placeholders})",
            part,
        )
        deleted += cur.rowcount
    conn.commit()
    return deleted


def _insert_one(
    conn: sqlite3.Connection,
    *,
    from_fact_id: str,
    to_fact_id: str,
    relation_type: str,
    confidence: float,
    knowledge_status: str,
    inference_source: str | None,
    metadata: dict[str, Any],
    now: str,
    create_inverse: bool,
) -> int:
    if from_fact_id == to_fact_id:
        return 0
    if relation_type not in FORWARD_RELATION_TYPES:
        return 0
    relation_id = f"rel_{uuid.uuid4().hex[:12]}"
    meta_json = json.dumps(metadata, ensure_ascii=False)
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            truth_status, review_state,
            evidence_ref, created_at, valid_from, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'validated', 'approved', NULL, ?, ?, ?)
        """,
        (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            now, now, meta_json,
        ),
    )
    added = cur.rowcount
    if added and create_inverse:
        inverse_type = INVERSE_RELATIONS.get(relation_type)
        if inverse_type and inverse_type in VALID_RELATION_TYPES:
            inverse_id = f"rel_{uuid.uuid4().hex[:12]}"
            inv_meta = {**metadata, "inverse_of": relation_id}
            conn.execute(
                """
                INSERT OR IGNORE INTO relations (
                    relation_id, from_fact_id, to_fact_id, relation_type,
                    confidence, knowledge_status, inference_source,
                    truth_status, review_state,
                    evidence_ref, created_at, valid_from, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'validated', 'approved', NULL, ?, ?, ?)
                """,
                (
                    inverse_id, to_fact_id, from_fact_id, inverse_type,
                    confidence, knowledge_status, inference_source,
                    now, now, json.dumps(inv_meta, ensure_ascii=False),
                ),
            )
    return added


def batch_insert_edges(
    conn: sqlite3.Connection,
    edges: list[dict[str, Any]],
    *,
    batch_size: int = 500,
    create_inverse: bool = True,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, int]:
    """Пакетная запись рёбер в одной транзакции на batch."""
    slice_edges = edges[offset:]
    if limit is not None:
        slice_edges = slice_edges[:limit]
    stats = {"attempted": len(slice_edges), "inserted": 0, "skipped": 0}
    if not slice_edges:
        return stats
    now = datetime.now(UTC).isoformat()
    conn.execute("PRAGMA foreign_keys = ON")
    for start in range(0, len(slice_edges), batch_size):
        chunk = slice_edges[start:start + batch_size]
        conn.execute("BEGIN")
        for edge in chunk:
            src = str(edge.get("source_id", ""))
            tgt = str(edge.get("target_id", ""))
            rtype = str(edge.get("relation_type", ""))
            if not src or not tgt or src == tgt:
                stats["skipped"] += 1
                continue
            added = _insert_one(
                conn,
                from_fact_id=src,
                to_fact_id=tgt,
                relation_type=rtype,
                confidence=float(edge.get("confidence", 0.6)),
                knowledge_status=str(edge.get("knowledge_status", "inferred")),
                inference_source=edge.get("inference_source"),
                metadata=edge_metadata(edge),
                now=now,
                create_inverse=create_inverse,
            )
            if added:
                stats["inserted"] += 1
            else:
                stats["skipped"] += 1
        conn.commit()
    return stats


def load_checkpoint(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def save_checkpoint(path: str, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


__all__ = [
    "KB_BUILD_META_KEY",
    "KB_BUILD_TAG",
    "batch_insert_edges",
    "delete_kb_generated_edges",
    "edge_metadata",
    "load_checkpoint",
    "save_checkpoint",
]
