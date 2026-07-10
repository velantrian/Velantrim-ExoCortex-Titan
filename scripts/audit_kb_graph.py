#!/usr/bin/env python
"""
🔍 scripts/audit_kb_graph.py — аудит качества KB causal graph (SQLite + markdown).

    python scripts/audit_kb_graph.py --db data/velantrim_kb_clean_20260710_graph.db
    python scripts/audit_kb_graph.py --db data/velantrim_kb.db --json report.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import time

sys.path.insert(0, os.getcwd())

CURATED_EDGE_BASES = frozenset({
    "curated_explicit",
    "heuristic_ops_sequence",
    "heuristic_safety",
    "heuristic_causal_claim",
    "claim_reference",
})


def _parse_meta(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def audit_db(db_path: str, sample_size: int = 50) -> dict:
    from core.knowledge_linker import link_facts
    from core.world_skills_ingest import parse_knowledge_dir

    facts = parse_knowledge_dir()
    fact_ids = {f["fact_id"] for f in facts}
    computed = link_facts(facts)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    fact_count = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    validated = conn.execute(
        "SELECT COUNT(*) FROM facts WHERE epistemic_state='Validated'"
    ).fetchone()[0]

    rows = conn.execute(
        "SELECT from_fact_id, to_fact_id, relation_type, knowledge_status, "
        "inference_source, metadata FROM relations"
    ).fetchall()

    dangling = self_edges = duplicate_pairs = missing_basis = 0
    by_type: dict[str, int] = {}
    by_basis: dict[str, int] = {}
    curated = inferred = 0
    pair_seen: set[tuple[str, str, str]] = set()
    namespace_by_ns: dict[str, int] = {}
    sample_pool: list[dict] = []

    for row in rows:
        src, tgt, rtype = row["from_fact_id"], row["to_fact_id"], row["relation_type"]
        meta = _parse_meta(row["metadata"])
        basis = str(meta.get("edge_basis", "unknown"))
        by_type[rtype] = by_type.get(rtype, 0) + 1
        by_basis[basis] = by_basis.get(basis, 0) + 1
        if row["knowledge_status"] == "inferred":
            inferred += 1
        if basis in CURATED_EDGE_BASES:
            curated += 1
        if src == tgt:
            self_edges += 1
        if src not in fact_ids or tgt not in fact_ids:
            dangling += 1
        if basis in ("", "unknown") and meta.get("kb_build"):
            missing_basis += 1
        key = (src, tgt, rtype)
        if key in pair_seen:
            duplicate_pairs += 1
        pair_seen.add(key)
        if basis == "namespace":
            ns = src.split(".", 1)[0]
            namespace_by_ns[ns] = namespace_by_ns.get(ns, 0) + 1
        if row["knowledge_status"] == "inferred" and basis in {"semantic_similarity", "namespace"}:
            sample_pool.append({
                "source_id": src,
                "target_id": tgt,
                "relation_type": rtype,
                "edge_basis": basis,
                "confidence": meta.get("semantic_score"),
            })

    degrees: dict[str, int] = {}
    for row in rows:
        if row["from_fact_id"] in fact_ids and row["to_fact_id"] in fact_ids:
            degrees[row["from_fact_id"]] = degrees.get(row["from_fact_id"], 0) + 1
            degrees[row["to_fact_id"]] = degrees.get(row["to_fact_id"], 0) + 1
    connected = sum(1 for fid in fact_ids if degrees.get(fid, 0) > 0)
    isolated = len(fact_ids) - connected

    # RU ↔ EN ID parity
    from scripts.verify_world_skills import check_bilingual_ids
    bilingual = check_bilingual_ids()

    top_namespace = sorted(namespace_by_ns.items(), key=lambda x: -x[1])[:15]
    rng = random.Random(42)
    inferred_sample = rng.sample(sample_pool, min(sample_size, len(sample_pool)))

    computed_quality = __import__("core.knowledge_linker", fromlist=["graph_quality_report"]).graph_quality_report(
        facts, computed
    )

    report = {
        "db": db_path,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "facts_in_db": fact_count,
        "facts_validated": validated,
        "facts_in_corpus": len(fact_ids),
        "edges_in_db": len(rows),
        "edges_computed": len(computed),
        "connected_nodes": connected,
        "isolated_nodes": isolated,
        "coverage_pct": round(100.0 * connected / max(1, len(fact_ids)), 4),
        "average_degree": round(2.0 * len(rows) / max(1, len(fact_ids)), 2),
        "by_relation_type": by_type,
        "by_edge_basis": by_basis,
        "curated_edges_db": curated,
        "inferred_edges_db": inferred,
        "curated_ratio_pct": round(100.0 * curated / max(1, len(rows)), 2),
        "dangling_edges": dangling,
        "self_edges": self_edges,
        "duplicate_edge_keys": duplicate_pairs,
        "missing_edge_basis": missing_basis,
        "computed_quality": computed_quality,
        "top_namespace_domains": top_namespace,
        "inferred_edge_sample": inferred_sample,
        "bilingual": bilingual,
        "pass": (
            isolated <= max(1, int(len(fact_ids) * 0.001))
            and dangling == 0
            and self_edges == 0
            and duplicate_pairs == 0
            and missing_basis == 0
            and bilingual.get("missing_en", 0) == 0
            and bilingual.get("missing_ru", 0) == 0
            and curated >= 500
        ),
    }
    conn.close()
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit KB graph quality")
    ap.add_argument("--db", type=str, required=True, help="SQLite KB database")
    ap.add_argument("--json", type=str, default="", help="write JSON report")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print(f"❌ БД не найдена: {args.db}")
        return 2

    report = audit_db(args.db)
    out = args.json or f"{args.db}.audit.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(f"📊 Аудит KB: {args.db}")
    print(f"   facts: {report['facts_in_db']} (Validated: {report['facts_validated']})")
    print(f"   edges: {report['edges_in_db']}  curated: {report['curated_edges_db']}")
    print(f"   coverage: {report['coverage_pct']}%  isolated: {report['isolated_nodes']}")
    print(f"   dangling/self/dup: {report['dangling_edges']}/{report['self_edges']}/{report['duplicate_edge_keys']}")
    print(f"   bilingual missing EN: {report['bilingual'].get('missing_en', '?')}  missing RU: {report['bilingual'].get('missing_ru', '?')}")
    cq = report.get("computed_quality", {})
    print(
        f"   causal (Essence): {cq.get('causal_edges_essence', '?')} "
        f"({cq.get('causal_ratio_pct', '?')}%)  causes: {cq.get('causes_edges', '?')}"
    )
    print(f"   PASS: {'✅' if report['pass'] else '❌'}  → {out}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
