#!/usr/bin/env python3
"""
scripts/ingest_world_skills_run.py — integration run of the dedup/resolver pipeline
on the REAL collected world_skills_core knowledge (~6K units).

Parses every batch → ingests into a SCRATCH store (never the canonical velantrim.db)
→ runs the living-memory organs and reports what they find:
  • ingest stats (parsed / stored / validated)
  • semantic dedup (D4): merge-candidate clusters (same-meaning facts to review),
    domain-blocked + deterministic — with a few examples
  • contradiction detection (D5): opposite-polarity same-subject pairs (likely
    naive-heuristic false positives in factual text — useful to see)

Usage:
    python scripts/ingest_world_skills_run.py [--db data/world_skills_scratch.db] [--no-embed]

--no-embed uses the lexical fallback (fast, no model load). Default loads the local
sentence-transformers model for true semantic dedup. Pure read-only to markdown.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ingest world_skills_core + run dedup/contradiction.")
    ap.add_argument("--db", default="data/world_skills_scratch.db",
                    help="scratch DB path (NOT the canonical velantrim.db)")
    ap.add_argument("--no-embed", action="store_true", help="lexical fallback (no model load)")
    ap.add_argument("--examples", type=int, default=5, help="how many examples to print")
    args = ap.parse_args(argv)

    from core.contradiction_resolver import detect_contradictions
    from core.memory import SQLiteGraphStore
    from core.semantic_dedup import default_embedder, plan_dedup
    from core.world_skills_ingest import ingest_facts, parse_knowledge_dir

    # fresh scratch store (delete old so the run is reproducible)
    if os.path.exists(args.db):
        os.remove(args.db)
    store = SQLiteGraphStore(db_path=args.db)

    print("📂 Parsing world_skills_core …")
    facts = parse_knowledge_dir()
    print(f"   parsed: {len(facts)} units")
    # sanity: claims must be sentences, not type tokens (header-aware parser)
    type_tokens = {"invariant", "variant"}
    bad = [f for f in facts if f["claim"].strip().lower() in type_tokens]
    print(f"   claims mis-parsed as type token: {len(bad)} (must be 0)")

    print(f"💾 Ingesting into scratch store {args.db} …")
    t0 = time.time()
    rep = ingest_facts(store, facts, validate=False)   # keep Observed → let organs work
    print(f"   {rep} in {time.time()-t0:.1f}s")

    all_facts = store.get_all_facts()
    print(f"   store now holds: {len(all_facts)} facts")

    embed_fn = None if args.no_embed else default_embedder()
    mode = "lexical" if embed_fn is None else "semantic (sentence-transformers)"
    print(f"\n🧬 Semantic dedup (D4), mode = {mode}, domain-blocked …")
    t0 = time.time()
    plans = plan_dedup(all_facts, embed_fn=embed_fn)
    print(f"   merge-candidate clusters (size≥2): {len(plans)}  in {time.time()-t0:.1f}s")
    for p in sorted(plans, key=lambda x: -x.size)[:args.examples]:
        print(f"     • canon={p.canonical_id} absorbs {p.absorbed_ids[:3]}"
              f"{'…' if len(p.absorbed_ids) > 3 else ''} (size {p.size}, sources {p.sources_after[:3]})")

    print("\n⚖️  Contradiction detection (D5) …")
    t0 = time.time()
    contras = detect_contradictions(all_facts)
    print(f"   detected opposite-polarity pairs: {len(contras)}  in {time.time()-t0:.1f}s")
    for c in contras[:args.examples]:
        print(f"     • {c.older_id}  ⟂  {c.newer_id}  | subject «{c.subject[:50]}»")

    print(f"\n✅ Integration run complete. Scratch DB: {args.db} (gitignored).")
    print("   Flags for production wiring: ENABLE_SEMANTIC_DEDUP, ENABLE_GRADUATED_PROMOTION,")
    print("   ENABLE_CONTRADICTION_RESOLVER, ENABLE_SLEEP_CONSOLIDATION.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
