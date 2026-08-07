#!/usr/bin/env python3
"""Validate the portable ``kb_graph.json`` knowledge asset.

This validator does not decide whether a claim is true and grants no runtime or
Canon authority. It verifies only artifact structure, referential integrity,
count consistency and deterministic graph hygiene.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_GRAPH_PATH = Path("kb_graph.json")
EDGE_ENDPOINT_PAIRS = (
    ("source_id", "target_id"),
    ("from_fact_id", "to_fact_id"),
    ("source", "target"),
)


class KnowledgeGraphValidationError(ValueError):
    """Raised when the portable KB graph cannot be validated safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _endpoint_pair(edge: dict[str, Any]) -> tuple[str, str] | None:
    for source_key, target_key in EDGE_ENDPOINT_PAIRS:
        source = edge.get(source_key)
        target = edge.get(target_key)
        if isinstance(source, str) and isinstance(target, str):
            return source, target
    return None


def validate_graph(data: Any, *, max_errors: int = 100) -> dict[str, Any]:
    """Return a deterministic integrity report for a decoded portable graph."""

    if not isinstance(data, dict):
        raise KnowledgeGraphValidationError("graph root must be an object")
    meta = data.get("meta")
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(meta, dict):
        raise KnowledgeGraphValidationError("meta must be an object")
    if not isinstance(nodes, list):
        raise KnowledgeGraphValidationError("nodes must be an array")
    if not isinstance(edges, list):
        raise KnowledgeGraphValidationError("edges must be an array")

    errors: list[str] = []
    node_ids: set[str] = set()
    duplicate_node_ids = 0
    invalid_nodes = 0

    def record(message: str) -> None:
        if len(errors) < max_errors:
            errors.append(message)

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            invalid_nodes += 1
            record(f"nodes[{index}] must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            invalid_nodes += 1
            record(f"nodes[{index}].id must be a non-empty string")
            continue
        if node_id in node_ids:
            duplicate_node_ids += 1
            record(f"duplicate node id: {node_id}")
        node_ids.add(node_id)

    dangling_edges = 0
    self_edges = 0
    duplicate_edges = 0
    invalid_edges = 0
    seen_edges: set[tuple[str, str, str]] = set()

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            invalid_edges += 1
            record(f"edges[{index}] must be an object")
            continue
        endpoints = _endpoint_pair(edge)
        if endpoints is None:
            invalid_edges += 1
            record(
                f"edges[{index}] must contain one supported endpoint pair: "
                "source_id/target_id, from_fact_id/to_fact_id or source/target"
            )
            continue
        source, target = endpoints
        relation = edge.get("relation_type", edge.get("type", edge.get("relation", "")))
        if not isinstance(relation, str) or not relation.strip():
            invalid_edges += 1
            record(f"edges[{index}] relation type must be a non-empty string")
            continue
        if source not in node_ids or target not in node_ids:
            dangling_edges += 1
            record(f"dangling edge: {source} -[{relation}]-> {target}")
        if source == target:
            self_edges += 1
            record(f"self edge: {source} -[{relation}]-> {target}")
        key = (source, target, relation)
        if key in seen_edges:
            duplicate_edges += 1
            record(f"duplicate edge: {source} -[{relation}]-> {target}")
        seen_edges.add(key)

    expected_nodes = meta.get("total_nodes")
    expected_edges = meta.get("total_edges")
    count_mismatches = 0
    if expected_nodes != len(nodes):
        count_mismatches += 1
        record(f"meta.total_nodes mismatch: expected {expected_nodes!r}, actual {len(nodes)}")
    if expected_edges != len(edges):
        count_mismatches += 1
        record(f"meta.total_edges mismatch: expected {expected_edges!r}, actual {len(edges)}")

    ok = not any(
        (
            invalid_nodes,
            duplicate_node_ids,
            invalid_edges,
            dangling_edges,
            self_edges,
            duplicate_edges,
            count_mismatches,
        )
    )
    return {
        "ok": ok,
        "schema": meta.get("schema_version", "legacy-unversioned"),
        "nodes": len(nodes),
        "edges": len(edges),
        "unique_node_ids": len(node_ids),
        "invalid_nodes": invalid_nodes,
        "duplicate_node_ids": duplicate_node_ids,
        "invalid_edges": invalid_edges,
        "dangling_edges": dangling_edges,
        "self_edges": self_edges,
        "duplicate_edges": duplicate_edges,
        "count_mismatches": count_mismatches,
        "errors": errors,
        "errors_truncated": len(errors) >= max_errors,
        "authority": "ARTIFACT_INTEGRITY_ONLY",
    }


def load_and_validate(path: Path = DEFAULT_GRAPH_PATH, *, max_errors: int = 100) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeGraphValidationError(f"cannot read {path}: {exc}") from exc
    report = validate_graph(data, max_errors=max_errors)
    report["path"] = path.as_posix()
    report["bytes"] = path.stat().st_size
    report["sha256"] = sha256_file(path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_GRAPH_PATH)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument("--max-errors", type=int, default=100)
    args = parser.parse_args()

    if args.max_errors < 1:
        parser.error("--max-errors must be at least 1")

    try:
        report = load_and_validate(args.path, max_errors=args.max_errors)
    except KnowledgeGraphValidationError as exc:
        report = {"ok": False, "errors": [str(exc)]}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(
            "OK: portable KB graph integrity validated; "
            f"nodes={report['nodes']} edges={report['edges']} sha256={report['sha256']}"
        )
    else:
        print("FAILED: portable KB graph integrity errors:")
        for error in report.get("errors", []):
            print(f"  - {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
