#!/usr/bin/env python
"""Удалить промежуточные SQLite-артефакты KB-sprint (P1 hygiene)."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

KEEP = frozenset({
    "velantrim_house.db",
    "velantrim_kb_clean_20260710_graph.db",
    "ngram_house.db",
    "velantrim_ngram.db",
    "exocortex_graph.db",
    "exocortex_graph_kuzu_fallback.db",
})

KEEP_PREFIXES = (
    "velantrim_kb_clean_20260710_graph.db.",
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Remove stale data/*.db build artifacts")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = Path(args.data_dir)
    if not data.is_dir():
        print(f"❌ not found: {data}")
        return 2

    removed = kept = 0
    for path in sorted(data.glob("*.db")):
        name = path.name
        if name in KEEP or any(name.startswith(p) for p in KEEP_PREFIXES):
            kept += 1
            continue
        removed += 1
        print(f"{'[dry-run] ' if args.dry_run else ''}remove {path}")
        if not args.dry_run:
            path.unlink(missing_ok=True)
            for suffix in ("-wal", "-shm", "-journal"):
                side = Path(str(path) + suffix)
                if side.exists():
                    side.unlink()

    print(f"kept={kept} removed={removed} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())