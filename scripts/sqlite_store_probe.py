from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from core.memory import SQLiteGraphStore


@dataclass(frozen=True, slots=True)
class WriterLevelResult:
    writers: int
    successes: int
    observed_count: int
    duration_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    integrity_check: str
    errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return (
            self.successes == self.writers
            and self.observed_count == self.writers
            and self.integrity_check == "ok"
            and not self.errors
        )


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * percentile))))
    return round(ordered[index], 3)


def _fact(fact_id: str) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "claim": f"Concurrent SQLite characterization fact {fact_id}",
        "source": "sqlite_resilience_probe",
        "confidence": 0.8,
        "metadata": {"probe": True},
    }


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=30.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def run_writer_level(db_path: Path, writers: int) -> WriterLevelResult:
    if writers < 1:
        raise ValueError("writers must be >= 1")

    bootstrap = SQLiteGraphStore(str(db_path))
    bootstrap.ensure_schema()
    bootstrap.close()

    stores = [SQLiteGraphStore(str(db_path)) for _ in range(writers)]
    for store in stores:
        store.ensure_schema()

    start = threading.Event()

    def write_one(index: int) -> tuple[float, str | None]:
        start.wait()
        began = time.perf_counter()
        try:
            stores[index].store_fact(_fact(f"probe-{writers}-{index}"))
        except Exception as exc:  # noqa: BLE001 - probe records exact failure class
            elapsed_ms = (time.perf_counter() - began) * 1000.0
            return elapsed_ms, f"{type(exc).__name__}: {exc}"
        elapsed_ms = (time.perf_counter() - began) * 1000.0
        return elapsed_ms, None

    began_level = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=writers) as pool:
            futures = [pool.submit(write_one, index) for index in range(writers)]
            start.set()
            outcomes = [future.result(timeout=45.0) for future in futures]
    finally:
        for store in stores:
            store.close()
    duration_ms = (time.perf_counter() - began_level) * 1000.0

    latencies = [elapsed for elapsed, error in outcomes if error is None]
    errors = tuple(error for _, error in outcomes if error is not None)

    verifier = SQLiteGraphStore(str(db_path))
    try:
        observed_count = len(verifier.get_all_facts())
    finally:
        verifier.close()

    return WriterLevelResult(
        writers=writers,
        successes=len(latencies),
        observed_count=observed_count,
        duration_ms=round(duration_ms, 3),
        p50_ms=_percentile(latencies, 0.50),
        p95_ms=_percentile(latencies, 0.95),
        p99_ms=_percentile(latencies, 0.99),
        integrity_check=_integrity_check(db_path),
        errors=errors,
    )


def run_probe(writer_levels: Sequence[int], db_dir: Path) -> dict[str, object]:
    results = [
        run_writer_level(db_dir / f"writers-{writers}.db", writers)
        for writers in writer_levels
    ]
    return {
        "schema_version": 1,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "sqlite_version": sqlite3.sqlite_version,
        "sqlite_threadsafe": sqlite3.threadsafety,
        "writer_levels": list(writer_levels),
        "passed": all(result.passed for result in results),
        "results": [asdict(result) | {"passed": result.passed} for result in results],
    }


def _parse_levels(raw: str) -> tuple[int, ...]:
    levels = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    if not levels or any(level < 1 for level in levels):
        raise argparse.ArgumentTypeError("writer levels must be positive integers")
    return levels


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Characterize SQLiteGraphStore multi-instance writer behavior."
    )
    parser.add_argument(
        "--writers",
        type=_parse_levels,
        default=(1, 10, 25, 50, 100),
        help="Comma-separated writer levels (default: 1,10,25,50,100).",
    )
    parser.add_argument(
        "--db-dir",
        type=Path,
        default=None,
        help="Directory for probe databases; defaults to a temporary directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )
    args = parser.parse_args()

    if args.db_dir is None:
        with tempfile.TemporaryDirectory(prefix="titan-sqlite-probe-") as temp_dir:
            report = run_probe(args.writers, Path(temp_dir))
    else:
        args.db_dir.mkdir(parents=True, exist_ok=True)
        report = run_probe(args.writers, args.db_dir)

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if bool(report["passed"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
