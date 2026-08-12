#!/usr/bin/env python
"""
🔗 scripts/build_kb_graph.py — собрать production-quality KB causal graph.

Фазы (можно комбинировать с --resume):
    python scripts/build_kb_graph.py --db data/velantrim_kb_clean_20260710_graph.db
    python scripts/build_kb_graph.py --facts-only --fast-fresh
    python scripts/build_kb_graph.py --edges-only --edge-batch-size 1000
    python scripts/build_kb_graph.py --edges-only --edge-offset 5000 --edge-limit 5000
    python scripts/build_kb_graph.py --export kb_graph.json

ENV: VELANTRIM_DB_PATH (или --db), VELANTRIM_SQLITE_SYNCHRONOUS=NORMAL
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


def _write_quality_report(
    path: str,
    facts: list[dict],
    edges: list[dict],
    extra: dict | None = None,
) -> dict:
    from core.knowledge_linker import graph_quality_report

    report = graph_quality_report(facts, edges)
    report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if extra:
        report.update(extra)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return report



def ingest_kb_facts(
    store,
    facts: list[dict],
    *,
    batch_size: int = 500,
    require_empty: bool = False,
) -> dict[str, int]:
    """Ingest curated KB facts only through canonical fact/ESM owners.

    ``require_empty`` preserves the historical ``--fast-fresh`` safety
    precondition, but never grants a raw-SQL bootstrap bypass. A partial or
    evidence-failed batch is an unsuccessful build so the launcher cannot
    treat that DB as an accepted smart-KB Canon.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if require_empty:
        with store._db() as conn:
            existing = int(conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0])
        if existing:
            raise RuntimeError("--fast-fresh requires an empty KB database")

    from core.world_skills_ingest import ingest_facts

    totals = {"parsed": len(facts), "ingested": 0, "validated": 0, "errors": 0}
    for start in range(0, len(facts), batch_size):
        chunk = facts[start:start + batch_size]
        rep = ingest_facts(store, chunk, validate=True)
        for key in ("ingested", "validated", "errors"):
            totals[key] += int(rep.get(key, 0))
        if (
            int(rep.get("errors", 0)) != 0
            or int(rep.get("ingested", 0)) != len(chunk)
            or int(rep.get("validated", 0)) != len(chunk)
        ):
            raise RuntimeError(
                "canonical smart-KB ingest incomplete: "
                f"chunk={start}:{start + len(chunk)} "
                f"ingested={rep.get('ingested', 0)} "
                f"validated={rep.get('validated', 0)} "
                f"errors={rep.get('errors', 0)}"
            )
    return totals

def main() -> int:
    ap = argparse.ArgumentParser(description="Build production KB graph (facts + edges).")
    ap.add_argument("--db", type=str, default="", help="путь к KB SQLite (VELANTRIM_DB_PATH)")
    ap.add_argument("--limit", type=int, default=0, help="ограничить число фактов (0 = все)")
    ap.add_argument("--batch-size", type=int, default=500, help="batch для facts ingest")
    ap.add_argument("--fast-fresh", action="store_true", help="требовать пустую KB-БД; запись остаётся canonical")
    ap.add_argument("--facts-only", action="store_true", help="только факты, без рёбер")
    ap.add_argument("--edges-only", action="store_true", help="только рёбра (факты уже в БД)")
    ap.add_argument("--edge-offset", type=int, default=0, help="смещение в списке рёбер")
    ap.add_argument("--edge-limit", type=int, default=0, help="лимит рёбер (0 = все)")
    ap.add_argument("--edge-batch-size", type=int, default=500, help="SQLite batch для рёбер")
    ap.add_argument("--resume", action="store_true", help="продолжить с checkpoint (edges)")
    ap.add_argument("--checkpoint", type=str, default="", help="путь к checkpoint JSON")
    ap.add_argument("--export", type=str, default="", help="экспорт kb_graph.json после сборки")
    ap.add_argument("--wipe-all-edges", action="store_true",
                    help="удалить ВСЕ рёбра перед записью (только KB-БД)")
    ap.add_argument("--quality-out", type=str, default="", help="путь quality report JSON")
    args = ap.parse_args()

    if args.facts_only and args.edges_only:
        ap.error("--facts-only и --edges-only несовместимы")

    if args.db:
        os.environ["VELANTRIM_DB_PATH"] = args.db
    db = os.environ["VELANTRIM_DB_PATH"]
    ckpt_path = args.checkpoint or f"{db}.build_checkpoint.json"
    quality_path = args.quality_out or f"{db}.quality.json"

    from core.kb_graph_build import (
        batch_insert_edges,
        delete_kb_generated_edges,
        load_checkpoint,
        save_checkpoint,
    )
    from core.knowledge_linker import link_facts
    from core.memory import _GLOBAL_STORE
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"🔗 KB → {db}  (synchronous={os.environ['VELANTRIM_SQLITE_SYNCHRONOUS']})")
    t0 = time.time()

    facts = parse_knowledge_dir()
    if args.limit:
        facts = facts[: args.limit]
    print(f"  распарсено фактов: {len(facts)}")

    # ── Факты ────────────────────────────────────────────────────────────────
    if not args.edges_only:
        fact_stats = ingest_kb_facts(
            _GLOBAL_STORE,
            facts,
            batch_size=max(1, args.batch_size),
            require_empty=args.fast_fresh,
        )
        print(
            f"  факты в store: ingested={fact_stats['ingested']} "
            f"validated={fact_stats['validated']} errors={fact_stats['errors']} "
            f"(canonical batch_size={max(1, args.batch_size)})"
        )

    if args.facts_only:
        print(f"\n✅ Факты KB готовы в {db}.")
        return 0

    # ── Рёбра ────────────────────────────────────────────────────────────────
    ckpt = load_checkpoint(ckpt_path) if args.resume else {}
    edges_cache = f"{db}.edges_cache.json"
    edge_offset = args.edge_offset or int(ckpt.get("next_offset", 0))
    edge_limit = args.edge_limit or None

    if args.resume and os.path.isfile(edges_cache) and not args.edge_offset:
        with open(edges_cache, encoding="utf-8") as fh:
            edges = json.load(fh)
        print(f"  resume: загружено {len(edges)} рёбер из cache", flush=True)
    else:
        print("  вычисление рёбер (детерминированно)…", flush=True)
        edges = link_facts(facts)
        with open(edges_cache, "w", encoding="utf-8") as fh:
            json.dump(edges, fh, ensure_ascii=False)
        ckpt = {
            "total_edges": len(edges),
            "next_offset": 0,
            "db": db,
            "facts": len(facts),
            "edges_cache": edges_cache,
        }
        save_checkpoint(ckpt_path, ckpt)
        print(f"  рёбер вычислено: {len(edges)}  (cache → {edges_cache})")

    total_edges = len(edges)
    if edge_limit:
        slice_end = edge_offset + edge_limit
    else:
        slice_end = total_edges

    with _GLOBAL_STORE._db() as conn:
        if edge_offset == 0:
            deleted = delete_kb_generated_edges(conn, wipe_all=args.wipe_all_edges)
            print(f"  удалено старых KB-рёбер: {deleted}", flush=True)
        stats = batch_insert_edges(
            conn,
            edges,
            batch_size=max(1, args.edge_batch_size),
            offset=edge_offset,
            limit=edge_limit or None,
        )
    next_offset = edge_offset + stats["attempted"]
    ckpt["next_offset"] = next_offset
    ckpt["last_inserted"] = stats["inserted"]
    ckpt["last_skipped"] = stats["skipped"]
    save_checkpoint(ckpt_path, ckpt)

    print(
        f"  рёбра [{edge_offset}:{slice_end}] inserted={stats['inserted']} "
        f"skipped={stats['skipped']} total_progress={next_offset}/{total_edges}",
        flush=True,
    )

    if next_offset < total_edges and not args.edge_limit:
        print("  ⚠️  не все рёбра записаны; перезапустите с --resume")
    elif next_offset >= total_edges:
        ckpt["completed"] = True
        save_checkpoint(ckpt_path, ckpt)
        report = _write_quality_report(
            quality_path,
            facts,
            edges,
            extra={"db": db, "edge_insert_stats": stats, "deleted_and_rebuilt": True},
        )
        print(f"  quality report → {quality_path}")
        print(f"  curated={report.get('curated_edges')}  coverage={report.get('coverage_pct')}%")

        if args.export:
            from scripts.export_kb_graph import export_graph_json
            export_graph_json(args.export, facts, edges)
            print(f"  экспорт → {args.export}")

    print(f"  ⏱ {time.time() - t0:.1f} c")
    print(f"\n✅ Готово. KB graph в {db}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
