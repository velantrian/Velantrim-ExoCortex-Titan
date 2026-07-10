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


def main() -> int:
    ap = argparse.ArgumentParser(description="Build production KB graph (facts + edges).")
    ap.add_argument("--db", type=str, default="", help="путь к KB SQLite (VELANTRIM_DB_PATH)")
    ap.add_argument("--limit", type=int, default=0, help="ограничить число фактов (0 = все)")
    ap.add_argument("--batch-size", type=int, default=500, help="batch для facts ingest")
    ap.add_argument("--fast-fresh", action="store_true", help="быстрый insert в пустую БД")
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
    from core.knowledge_linker import graph_quality_report, link_facts
    from core.memory import _GLOBAL_STORE, _now, store_facts_batch
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"🔗 KB → {db}  (synchronous={os.environ['VELANTRIM_SQLITE_SYNCHRONOUS']})")
    t0 = time.time()

    facts = parse_knowledge_dir()
    if args.limit:
        facts = facts[: args.limit]
    print(f"  распарсено фактов: {len(facts)}")

    # ── Факты ────────────────────────────────────────────────────────────────
    if not args.edges_only:
        payload = [{
            "fact_id": f["fact_id"],
            "claim": f["claim"],
            "source": f["source"],
            "confidence": 0.85,
            "metadata": {"domain": f["metadata"]["domain"], "kb_type": f.get("type", "")},
        } for f in facts]

        batch_size = max(1, args.batch_size)
        if args.fast_fresh:
            from core.fact_integrity import compute_claim_dedup_key

            records = []
            for fact in payload:
                metadata = dict(fact["metadata"])
                metadata["claim_dedup_key"] = compute_claim_dedup_key(fact["claim"])
                records.append({
                    **fact,
                    "epistemic_state": "Observed",
                    "created_at": _now(),
                    "updated_at": _now(),
                    "metadata": json.dumps(metadata, ensure_ascii=False),
                    "history": "[]",
                    "t_event_valid_start": _now(),
                    "t_event_valid_end": None,
                    "t_ingestion_start": _now(),
                    "t_ingestion_end": None,
                    "claim_type": "UNKNOWN",
                    "origin_type": "UNKNOWN",
                    "memory_type": "semantic",
                })
            with _GLOBAL_STORE._db() as conn:
                existing = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                if existing:
                    raise RuntimeError("--fast-fresh requires an empty KB database")
                conn.executemany("""
                    INSERT INTO facts (
                        fact_id, claim, source, confidence, epistemic_state,
                        created_at, updated_at, metadata, history,
                        t_event_valid_start, t_event_valid_end,
                        t_ingestion_start, t_ingestion_end,
                        claim_type, origin_type, memory_type
                    ) VALUES (
                        :fact_id, :claim, :source, :confidence, :epistemic_state,
                        :created_at, :updated_at, :metadata, :history,
                        :t_event_valid_start, :t_event_valid_end,
                        :t_ingestion_start, :t_ingestion_end,
                        :claim_type, :origin_type, :memory_type
                    )
                """, records)
            print(f"  факты в store: stored={len(records)} errors=0 (fast-fresh)")
        else:
            totals = {"stored": 0, "updated": 0, "errors": 0}
            for start in range(0, len(payload), batch_size):
                st = store_facts_batch(payload[start:start + batch_size])
                for key in totals:
                    totals[key] += int(st.get(key, 0))
                print(f"  facts batch {min(start + batch_size, len(payload))}/{len(payload)}", flush=True)
            print(
                f"  факты в store: stored={totals['stored']} updated={totals['updated']} "
                f"errors={totals['errors']} (batch_size={batch_size})"
            )

        fact_ids = [f["fact_id"] for f in facts]
        now = _now()
        with _GLOBAL_STORE._db() as conn:
            has_version = any(
                r[1] == "fact_version" for r in conn.execute("PRAGMA table_info(facts)")
            )
            bump = ", fact_version = fact_version + 1" if has_version else ""
            conn.execute("CREATE TEMP TABLE IF NOT EXISTS _kb_ids (fact_id TEXT PRIMARY KEY)")
            conn.execute("DELETE FROM _kb_ids")
            conn.executemany("INSERT OR IGNORE INTO _kb_ids VALUES (?)", [(i,) for i in fact_ids])
            conn.execute(
                "UPDATE facts SET claim_type='WORLD_FACT', origin_type='EXTERNAL' "
                "WHERE fact_id IN (SELECT fact_id FROM _kb_ids) "
                "  AND epistemic_state NOT IN ('ImmutableCore', 'Collapsed') "
                "  AND (claim_type IS NULL OR claim_type != 'WORLD_FACT')"
            )
            val = 0
            for frm, to in (
                ("Observed", "Hypothesized"),
                ("Hypothesized", "Supported"),
                ("Supported", "Validated"),
            ):
                cur = conn.execute(
                    f"UPDATE facts SET epistemic_state=?, updated_at=?{bump} "
                    "WHERE epistemic_state=? AND fact_id IN (SELECT fact_id FROM _kb_ids)",
                    (to, now, frm),
                )
                val = cur.rowcount
            conn.execute("DROP TABLE IF EXISTS _kb_ids")
        print(f"  валидировано → Validated (ESM 3 ступени): {val}")

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
        print(f"  ⚠️  не все рёбра записаны; перезапустите с --resume")
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
