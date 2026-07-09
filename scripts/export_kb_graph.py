#!/usr/bin/env python
"""
📤 scripts/export_kb_graph.py — экспортировать связный граф знаний в JSON (nodes + edges).

Запуск из корня репозитория:
    python scripts/export_kb_graph.py
    python scripts/export_kb_graph.py --out kb_graph.json

Создаёт kb_graph.json со структурой:
    {
      "nodes": [ { "id": "physics.mechanics.force", "type": "INVARIANT", "claim": "..." }, ... ],
      "edges": [ { "source": "...", "target": "...", "relation": "enables", "confidence": 0.6 }, ... ]
    }
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Export connected KB graph as JSON")
    ap.add_argument("--out", type=str, default="kb_graph.json", help="output file")
    args = ap.parse_args()

    from core.knowledge_linker import link_facts
    from core.world_skills_ingest import parse_knowledge_dir

    print("📚 Парсинг фактов из KB...")
    facts = parse_knowledge_dir()
    print(f"   фактов: {len(facts)}")

    print("🔗 Вычисление рёбер (тег-матч + namespace-структура)...")
    edges = link_facts(facts)
    print(f"   рёбер вычислено: {len(edges)}")

    # --- Сборка графа ---
    nodes: list[dict] = []
    for f in facts:
        nodes.append({
            "id":    f.get("fact_id", ""),
            "type":  f.get("type", ""),
            "claim": f.get("claim", ""),
            "source": f.get("source", ""),
        })

    graph = {
        "meta": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "language": "ru",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "nodes": nodes,
        "edges": edges,
    }

    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"\n✅ Экспортировано: {out_path}  ({size_mb:.1f} MB)")
    print(f"   nodes: {len(nodes)}, edges: {len(edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
