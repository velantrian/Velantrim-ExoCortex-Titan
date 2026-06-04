#!/usr/bin/env python3
"""
scripts/calibrate_semantic_dedup.py — calibrate the D4 semantic-dedup threshold
on the REAL Russian world_skills_core corpus.

The default 0.78 (calibrated for English paraphrases) caused massive over-merging on
short Russian claims. This script embeds the corpus ONCE with the chosen model and:
  1. measures the within-domain DIFFERENT-pair cosine distribution (negatives — pairs
     that must NOT merge) → percentiles;
  2. sweeps thresholds and reports cluster count / max size / mean size (guard OFF, to
     see raw behaviour), so you can pick a threshold that keeps clusters small.

Pick a threshold safely above the negatives' p99. Pure measurement — no DB writes.

Usage:
    python scripts/calibrate_semantic_dedup.py [--model NAME] [--sample N] [--pairs N]
"""
from __future__ import annotations

import argparse
import os
import random
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2")
    ap.add_argument("--sample", type=int, default=2500, help="max facts to embed (speed)")
    ap.add_argument("--pairs", type=int, default=6000, help="random within-domain pairs for negatives")
    args = ap.parse_args(argv)
    random.seed(0)

    import numpy as np
    from sentence_transformers import SentenceTransformer

    import core.semantic_dedup as sd
    from core.world_skills_ingest import parse_knowledge_dir

    facts = parse_knowledge_dir()
    if len(facts) > args.sample:
        facts = random.sample(facts, args.sample)
    claims = [f["claim"] for f in facts]
    print(f"📂 {len(facts)} facts | model = {args.model}")

    t0 = time.time()
    model = SentenceTransformer(args.model)
    vecs = model.encode(claims, normalize_embeddings=True, show_progress_bar=False)
    V = np.asarray(vecs, dtype=float)
    print(f"   embedded in {time.time()-t0:.1f}s")
    cache = {c: V[i] for i, c in enumerate(claims)}

    def embed_fn(cl):
        return [cache[c] for c in cl]

    # ── negatives: within-domain DIFFERENT-pair similarity ───────────────────
    by_dom: dict = {}
    for i, f in enumerate(facts):
        by_dom.setdefault(f["metadata"]["domain"], []).append(i)
    sims = []
    doms = [d for d, idx in by_dom.items() if len(idx) >= 2]
    for _ in range(args.pairs):
        d = random.choice(doms)
        a, b = random.sample(by_dom[d], 2)
        sims.append(float(V[a] @ V[b]))
    sims.sort()

    def pct(p):
        return sims[min(len(sims) - 1, int(len(sims) * p))]

    print("\n📊 within-domain DIFFERENT-pair cosine (negatives — must NOT merge):")
    print(f"   p50={pct(.5):.3f}  p90={pct(.9):.3f}  p95={pct(.95):.3f}  "
          f"p99={pct(.99):.3f}  max={sims[-1]:.3f}  mean={statistics.mean(sims):.3f}")

    # ── threshold sweep (guard disabled to see RAW component sizes) ──────────
    sd._MAX_CLUSTER_SIZE = 10**9
    print("\n📈 threshold sweep (guard OFF — raw connected-component sizes):")
    print(f"   {'thr':>5} {'clusters≥2':>11} {'merged_facts':>12} {'max_size':>8} {'mean_size':>9}")
    for thr in (0.80, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94):
        cl = [c for c in sd.cluster_by_meaning(facts, threshold=thr, embed_fn=embed_fn) if len(c) >= 2]
        if cl:
            sizes = [len(c) for c in cl]
            print(f"   {thr:>5.2f} {len(cl):>11} {sum(sizes):>12} {max(sizes):>8} {statistics.mean(sizes):>9.1f}")
        else:
            print(f"   {thr:>5.2f} {0:>11} {0:>12} {0:>8} {0:>9.1f}")

    print("\n✅ Recommend: threshold a bit ABOVE negatives p99, where max_size stays small (≈2–5).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
