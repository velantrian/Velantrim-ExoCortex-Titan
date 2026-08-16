from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from unittest import mock

from core.memory import SQLiteGraphStore


@dataclass(frozen=True, slots=True)
class SqlErrorEvent:
    sequence: int
    thread: str
    phase: str
    sql: str
    error_type: str
    error: str


class TraceRecorder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sequence = 0
        self._errors: list[SqlErrorEvent] = []

    def record_error(self, *, phase: str, sql: str, exc: BaseException) -> None:
        with self._lock:
            self._sequence += 1
            self._errors.append(
                SqlErrorEvent(
                    sequence=self._sequence,
                    thread=threading.current_thread().name,
                    phase=phase,
                    sql=" ".join(str(sql).split()),
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
            )

    def snapshot(self) -> list[SqlErrorEvent]:
        with self._lock:
            return list(self._errors)


class _TracingCursor:
    def __init__(self, real: sqlite3.Cursor, recorder: TraceRecorder, sql: str) -> None:
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_recorder", recorder)
        object.__setattr__(self, "_sql", sql)

    def _call(self, phase: str, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase=phase,
                sql=object.__getattribute__(self, "_sql"),
                exc=exc,
            )
            raise

    def fetchone(self):
        return self._call("fetchone", object.__getattribute__(self, "_real").fetchone)

    def fetchall(self):
        return self._call("fetchall", object.__getattribute__(self, "_real").fetchall)

    def fetchmany(self, *args, **kwargs):
        return self._call(
            "fetchmany", object.__getattribute__(self, "_real").fetchmany, *args, **kwargs
        )

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(object.__getattribute__(self, "_real"))
        except StopIteration:
            raise
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase="cursor_next",
                sql=object.__getattribute__(self, "_sql"),
                exc=exc,
            )
            raise

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, "_real"), name)


class _TracingConnection:
    """Test-only proxy. SQL is never rewritten, retried, or swallowed."""

    def __init__(self, real: sqlite3.Connection, recorder: TraceRecorder) -> None:
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_recorder", recorder)

    def execute(self, sql, *args, **kwargs):
        try:
            cursor = object.__getattribute__(self, "_real").execute(sql, *args, **kwargs)
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase="execute", sql=str(sql), exc=exc
            )
            raise
        return _TracingCursor(cursor, object.__getattribute__(self, "_recorder"), str(sql))

    def executemany(self, sql, *args, **kwargs):
        try:
            cursor = object.__getattribute__(self, "_real").executemany(sql, *args, **kwargs)
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase="executemany", sql=str(sql), exc=exc
            )
            raise
        return _TracingCursor(cursor, object.__getattribute__(self, "_recorder"), str(sql))

    def executescript(self, sql, *args, **kwargs):
        try:
            cursor = object.__getattribute__(self, "_real").executescript(sql, *args, **kwargs)
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase="executescript", sql=str(sql), exc=exc
            )
            raise
        return _TracingCursor(cursor, object.__getattribute__(self, "_recorder"), str(sql))

    def commit(self):
        try:
            return object.__getattribute__(self, "_real").commit()
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase="commit", sql="<COMMIT>", exc=exc
            )
            raise

    def rollback(self):
        try:
            return object.__getattribute__(self, "_real").rollback()
        except sqlite3.Error as exc:
            object.__getattribute__(self, "_recorder").record_error(
                phase="rollback", sql="<ROLLBACK>", exc=exc
            )
            raise

    def __enter__(self):
        object.__getattribute__(self, "_real").__enter__()
        return self

    def __exit__(self, *args):
        return object.__getattribute__(self, "_real").__exit__(*args)

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, "_real"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_real"), name, value)


@dataclass(frozen=True, slots=True)
class IterationResult:
    mode: str
    iteration: int
    contenders: int
    worker_errors: tuple[str, ...]
    sql_errors: tuple[SqlErrorEvent, ...]
    integrity_check: str
    duration_ms: float

    @property
    def passed(self) -> bool:
        return not self.worker_errors and self.integrity_check == "ok"


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=10.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def _seed_current_schema(db_path: Path) -> None:
    seed = SQLiteGraphStore(str(db_path))
    try:
        seed.ensure_schema()
    finally:
        seed.close()


def _run_iteration(
    *,
    root: Path,
    mode: str,
    iteration: int,
    contenders: int,
    timeout: float,
) -> IterationResult:
    db_path = root / f"{mode}-{iteration}.db"
    _seed_current_schema(db_path)

    stores = [SQLiteGraphStore(str(db_path)) for _ in range(contenders)]
    if mode == "preinitialized-read":
        for store in stores:
            store.ensure_schema()

    recorder = TraceRecorder()
    worker_errors: list[str] = []
    errors_lock = threading.Lock()
    start = threading.Barrier(contenders, timeout=timeout)
    real_connect = sqlite3.connect

    def traced_connect(path, *args, **kwargs):
        real = real_connect(path, *args, **kwargs)
        if str(path) == str(db_path):
            return _TracingConnection(real, recorder)
        return real

    def worker(index: int) -> None:
        threading.current_thread().name = f"contender_{index}"
        try:
            start.wait(timeout=timeout)
            if mode == "fresh-ensure-only":
                stores[index].ensure_schema()
            else:
                # Missing fact is deliberate: it forces the normal durable read path
                # without introducing a concurrent canonical mutation.
                assert stores[index].get_fact("__issue_347_missing__") is None
        except BaseException as exc:  # noqa: BLE001 - diagnostic records exact class
            with errors_lock:
                worker_errors.append(f"contender_{index}: {type(exc).__name__}: {exc}")

    began = time.perf_counter()
    try:
        with mock.patch("sqlite3.connect", side_effect=traced_connect):
            threads = [threading.Thread(target=worker, args=(index,)) for index in range(contenders)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=timeout + 10.0)
                if thread.is_alive():
                    with errors_lock:
                        worker_errors.append(f"{thread.name}: TIMEOUT: thread remained alive")
    finally:
        for store in stores:
            store.close()
    duration_ms = (time.perf_counter() - began) * 1000.0

    return IterationResult(
        mode=mode,
        iteration=iteration,
        contenders=contenders,
        worker_errors=tuple(sorted(worker_errors)),
        sql_errors=tuple(recorder.snapshot()),
        integrity_check=_integrity_check(db_path),
        duration_ms=round(duration_ms, 3),
    )


def run_probe(*, contenders: int, repetitions: int, root: Path) -> dict[str, object]:
    modes = ("fresh-read", "preinitialized-read", "fresh-ensure-only")
    results: list[IterationResult] = []
    for mode in modes:
        for iteration in range(1, repetitions + 1):
            result = _run_iteration(
                root=root,
                mode=mode,
                iteration=iteration,
                contenders=contenders,
                timeout=20.0,
            )
            results.append(result)
            print(
                f"{mode} {iteration}/{repetitions}: "
                f"worker_errors={len(result.worker_errors)} "
                f"sql_errors={len(result.sql_errors)} "
                f"integrity={result.integrity_check}"
            )
            for error in result.worker_errors:
                print(f"  worker: {error}")
            for event in result.sql_errors:
                print(
                    f"  sql[{event.sequence}] {event.thread} {event.phase}: "
                    f"{event.error_type}: {event.error} :: {event.sql}"
                )

    by_mode: dict[str, dict[str, object]] = {}
    for mode in modes:
        selected = [result for result in results if result.mode == mode]
        by_mode[mode] = {
            "iterations": len(selected),
            "clean_iterations": sum(result.passed for result in selected),
            "failed_iterations": sum(not result.passed for result in selected),
            "worker_error_count": sum(len(result.worker_errors) for result in selected),
            "sql_error_count": sum(len(result.sql_errors) for result in selected),
            "schema_changed_events": sum(
                1
                for result in selected
                for event in result.sql_errors
                if "database schema has changed" in event.error.lower()
            ),
        }

    # The preinitialized control is an accepted existing concurrency contract and must
    # remain clean. The two fresh modes are characterization subjects: either failure or
    # non-reproduction is evidence, so their outcome does not drive this script's exit.
    preinitialized_clean = bool(
        by_mode["preinitialized-read"]["failed_iterations"] == 0
        and by_mode["preinitialized-read"]["worker_error_count"] == 0
    )
    all_integrity_ok = all(result.integrity_check == "ok" for result in results)

    return {
        "schema_version": 1,
        "contenders": contenders,
        "repetitions": repetitions,
        "modes": by_mode,
        "preinitialized_control_clean": preinitialized_clean,
        "all_integrity_checks_ok": all_integrity_ok,
        "results": [
            {
                **asdict(result),
                "sql_errors": [asdict(event) for event in result.sql_errors],
                "passed": result.passed,
            }
            for result in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Characterize concurrent fresh-store SQLite bootstrap.")
    parser.add_argument("--contenders", type=int, default=25)
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.contenders < 2:
        raise SystemExit("--contenders must be >= 2")
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be >= 1")

    with tempfile.TemporaryDirectory(prefix="titan-issue347-") as temp_dir:
        report = run_probe(
            contenders=args.contenders,
            repetitions=args.repetitions,
            root=Path(temp_dir),
        )

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if (
        report["preinitialized_control_clean"]
        and report["all_integrity_checks_ok"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
