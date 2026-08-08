#!/usr/bin/env python3
"""Bounded local diagnostic for CAS contention harness stability.

This script is intentionally outside ordinary PR CI. Use it to stress the
parameterized [25] contender case after harness changes.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_promotion_projection_outbox_caller import (  # noqa: E402
    _migrate,
    _run_cas_contention_race,
    _seed_promotable_fact,
)
from core.memory import SQLiteGraphStore  # noqa: E402


def run_once(tmp_dir: Path, contenders: int) -> None:
    db_path = tmp_dir / f"cas-contention-{contenders}.db"
    _migrate(db_path)
    bootstrap = SQLiteGraphStore(str(db_path))
    _seed_promotable_fact(bootstrap, "f_cas_contention")
    bootstrap.close()
    verdicts = _run_cas_contention_race(db_path, contenders=contenders)
    winners = [verdict for verdict in verdicts if verdict.passed]
    if len(winners) != 1:
        raise RuntimeError(f"expected one winner, got {len(winners)}: {verdicts}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contenders", type=int, default=25)
    parser.add_argument("--repetitions", type=int, default=100)
    args = parser.parse_args()

    for attempt in range(1, args.repetitions + 1):
        with tempfile.TemporaryDirectory(prefix="cas-harness-") as tmp:
            run_once(Path(tmp), args.contenders)
        print(f"attempt {attempt}/{args.repetitions}: PASS")

    print(
        f"OK: {args.repetitions}/{args.repetitions} passes for "
        f"contenders={args.contenders}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
