#!/usr/bin/env python
"""
📤 scripts/export_kb_graph.py — экспортировать связный граф знаний в JSON (nodes + edges).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

os.environ.setdefault("VELANTRIM_DB_PATH", "data/velantrim_kb.db")
os.environ.setdefault("VELANTRIM_SQLITE_SYNCHRONOUS", "NORMAL")
os.environ.setdefault("ENABLE_CAUSAL_GRAPH", "true")

sys.path.insert(0, os.getcwd())


def export_graph_json(
    out_path: str,
    facts: list[dict],
    edges: list[dict],
) -> dict:
    from core.knowledge_linker import graph_quality_report

    nodes = [{
        "id": f.get("fact_id", ""),
        "knowledge_unit": f.get("knowledge_unit", ""),
        "type": f.get("type", ""),
        "claim": f.get("claim", ""),
        "conditions": f.get("conditions", ""),
        "practical": f.get("practical", ""),
        "source": f.get("source", ""),
    } for f in facts]
    quality = graph_quality_report(facts, edges)
    graph = {
        "meta": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "language": "ru",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "quality": quality,
        },
        "nodes": nodes,
        "edges": edges,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, ensure_ascii=False, indent=2)
    return graph


def main() -> int:
    ap = argparse.ArgumentParser(description="Export connected KB graph as JSON")
    ap.add_argument("--out", type=str, default="kb_graph.json", help="output file")
    args = ap.parse_args()

    from core.knowledge_linker import link_facts
    from core.world_skills_ingest import parse_knowledge_dir

    print("📚 Парсинг фактов из KB...")
    facts = parse_knowledge_dir()
    print(f"   фактов: {len(facts)}")

    print("🔗 Вычисление рёбер (curated + tags + semantic + namespace)...")
    edges = link_facts(facts)
    print(f"   рёбер вычислено: {len(edges)}")

    export_graph_json(args.out, facts, edges)
    size_mb = os.path.getsize(args.out) / (1024 * 1024)
    print(f"\n✅ Экспортировано: {args.out}  ({size_mb:.1f} MB)")
    print(f"   nodes: {len(facts)}, edges: {len(edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
