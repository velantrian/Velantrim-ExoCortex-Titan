"""
🔧 core/kb_graph_build.py — устойчивая пакетная запись KB-рёбер в SQLite.

Issue #286 / parent #50: массовый ingest больше не владеет raw INSERT/DELETE
операциями над canonical ``relations``. Он нормализует KB edge proposals и делегирует
их единственному causal mutation owner — ``CausalGraph``.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from core.causal_graph import CausalGraph

KB_BUILD_META_KEY = "kb_build"
KB_BUILD_TAG = "world_skills_core_v1"


def ensure_relations_table(conn: sqlite3.Connection) -> None:
    """Create the causal storage required by a fresh KB graph build.

    Schema bootstrap is not mutation authority. Durable relation rows are created and
    removed only through ``CausalGraph`` below.
    """
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
    conn.commit()


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
    """Удалить KB-рёбра через canonical causal mutation owner."""
    ensure_relations_table(conn)
    graph = CausalGraph(conn)
    if wipe_all:
        return graph.reset_relations()

    rows = conn.execute("SELECT relation_id, metadata FROM relations").fetchall()
    to_delete: list[str] = []
    for relation_id, raw in rows:
        try:
            meta = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            meta = {}
        if meta.get(KB_BUILD_META_KEY) is True:
            to_delete.append(str(relation_id))
    if not to_delete:
        return 0
    return graph.remove_relations(to_delete)


def _proposal_from_edge(edge: dict[str, Any]) -> dict[str, Any] | None:
    src = str(edge.get("source_id", ""))
    tgt = str(edge.get("target_id", ""))
    rtype = str(edge.get("relation_type", ""))
    if not src or not tgt or src == tgt or not rtype:
        return None
    return {
        "from_fact_id": src,
        "to_fact_id": tgt,
        "relation_type": rtype,
        "confidence": edge.get("confidence", 0.6),
        "knowledge_status": str(edge.get("knowledge_status", "inferred")),
        "inference_source": edge.get("inference_source"),
        "truth_status": edge.get("truth_status"),
        "review_state": edge.get("review_state"),
        "evidence_ref": edge.get("evidence_ref"),
        "metadata": edge_metadata(edge),
    }


def batch_insert_edges(
    conn: sqlite3.Connection,
    edges: list[dict[str, Any]],
    *,
    batch_size: int = 500,
    create_inverse: bool = True,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, int]:
    """Пакетная запись через ``CausalGraph.add_relations_batch``.

    Canonical Truth edges require forward/inverse consistency. The historical
    ``create_inverse=False`` test-only escape hatch is therefore rejected instead of
    creating an unaudited half-edge.
    """
    if not create_inverse:
        raise ValueError(
            "create_inverse=False is incompatible with canonical causal relation integrity"
        )
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    slice_edges = edges[offset:]
    if limit is not None:
        slice_edges = slice_edges[:limit]
    stats = {"attempted": len(slice_edges), "inserted": 0, "skipped": 0}
    if not slice_edges:
        return stats

    ensure_relations_table(conn)
    graph = CausalGraph(conn)
    for start in range(0, len(slice_edges), batch_size):
        chunk = slice_edges[start:start + batch_size]
        proposals: list[dict[str, Any]] = []
        malformed = 0
        for edge in chunk:
            proposal = _proposal_from_edge(edge)
            if proposal is None:
                malformed += 1
                continue
            proposals.append(proposal)

        stats["skipped"] += malformed
        if not proposals:
            continue

        result = graph.add_relations_batch(proposals)
        stats["inserted"] += int(result["created"])
        stats["skipped"] += int(result["existing"])
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
