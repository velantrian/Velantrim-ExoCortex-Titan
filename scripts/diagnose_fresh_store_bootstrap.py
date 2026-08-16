from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from unittest import mock

from core.memory import SQLiteGraphStore

_ROOT = Path(__file__).resolve().parents[1]
_APPLY_MIGRATIONS = _ROOT / "scripts" / "apply_migrations.py"


@dataclass(frozen=True, slots=True)
class SqlErrorEvent:
    sequence: int
    thread: str
    phase: str
    sql: str
    error_type: str
    error: str
    sqlite_errorcode: int | None
    sqlite_errorname: str | None


class TraceRecorder:
    """Remember each worker's last real SQLite statement without proxying connections."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sequence = 0
        self._last_sql: dict[str, str] = {}
        self._errors: list[SqlErrorEvent] = []

    @staticmethod
    def _normalize(sql: str) -> str:
        return " ".join(str(sql).split())

    def trace(self, sql: str) -> None:
        thread = threading.current_thread().name
        with self._lock:
            self._last_sql[thread] = self._normalize(sql)

    def record_sqlite_error(self, *, phase: str, exc: sqlite3.Error) -> None:
        thread = threading.current_thread().name
        with self._lock:
            self._sequence += 1
            self._errors.append(
                SqlErrorEvent(
                    sequence=self._sequence,
                    thread=thread,
                    phase=phase,
                    sql=self._last_sql.get(thread, "<no traced statement>"),
                    error_type=type(exc).__name__,
                    error=str(exc),
                    sqlite_errorcode=getattr(exc, "sqlite_errorcode", None),
                    sqlite_errorname=getattr(exc, "sqlite_errorname", None),
                )
            )

    def snapshot(self) -> list[SqlErrorEvent]:
        with self._lock:
            return list(self._errors)


@dataclass(frozen=True, slots=True)
class IterationResult:
    mode: str
    iteration: int
    contenders: int
    worker_errors: tuple[str, ...]
    sql_errors: tuple[SqlErrorEvent, ...]
    integrity_check: str
    duration_ms: float
    pre_cas_reached: int = 0
    promotion_verdicts: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.worker_errors and self.integrity_check == "ok"


class _PeerPreCasAbort(RuntimeError):
    """Diagnostic-only abort so no real CAS runs after a peer failed pre-CAS."""


class _PromotionGate:
    def __init__(self, contenders: int) -> None:
        self.contenders = contenders
        self._condition = threading.Condition()
        self._reached = 0
        self._pre_cas_failed = False
        self._released = False

    def mark_pre_cas_failure(self) -> None:
        with self._condition:
            self._pre_cas_failed = True
            self._released = True
            self._condition.notify_all()

    def wait_before_real_cas(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        with self._condition:
            self._reached += 1
            if self._reached == self.contenders:
                self._released = True
                self._condition.notify_all()
            while not self._released:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._pre_cas_failed = True
                    self._released = True
                    self._condition.notify_all()
                    raise TimeoutError(
                        f"promotion pre-CAS gate timed out at {self._reached}/{self.contenders}"
                    )
                self._condition.wait(timeout=remaining)
            if self._pre_cas_failed:
                raise _PeerPreCasAbort("peer failed before all contenders reached real CAS")

    @property
    def reached(self) -> int:
        with self._condition:
            return self._reached


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


def _migrate_and_seed_promotable_fact(db_path: Path, fact_id: str) -> None:
    subprocess.run(
        [sys.executable, str(_APPLY_MIGRATIONS), "--db", str(db_path), "--no-backup"],
        check=True,
        capture_output=True,
        env={**os.environ},
    )
    seed = SQLiteGraphStore(str(db_path))
    try:
        assert seed.store_fact(
            {
                "fact_id": fact_id,
                "claim": "A well-evidenced fact for issue 347 pre-CAS characterization",
                "source": "manual",
                "confidence": 0.95,
                "metadata": {"evidence_refs": ["source-a", "source-b"]},
            }
        ) is True
        assert seed.promote_esm_to(fact_id, "Supported", by="issue_347_setup") is True
    finally:
        seed.close()


def _patch_real_connections(db_path: Path, recorder: TraceRecorder):
    """Patch connect only to install trace callbacks; return native connections unchanged."""

    real_connect = sqlite3.connect

    def traced_connect(path, *args, **kwargs):
        conn = real_connect(path, *args, **kwargs)
        if str(path) == str(db_path):
            conn.set_trace_callback(recorder.trace)
        return conn

    return mock.patch("sqlite3.connect", side_effect=traced_connect)


def _record_worker_exception(recorder: TraceRecorder, exc: BaseException) -> None:
    if isinstance(exc, sqlite3.Error):
        recorder.record_sqlite_error(phase="worker_exception_after_last_trace", exc=exc)


def _run_read_or_ensure_iteration(
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

    def worker(index: int) -> None:
        threading.current_thread().name = f"contender_{index}"
        try:
            start.wait(timeout=timeout)
            if mode == "fresh-ensure-only":
                stores[index].ensure_schema()
            else:
                assert stores[index].get_fact("__issue_347_missing__") is None
        except BaseException as exc:  # noqa: BLE001 - diagnostic records exact class
            _record_worker_exception(recorder, exc)
            with errors_lock:
                worker_errors.append(f"contender_{index}: {type(exc).__name__}: {exc}")

    began = time.perf_counter()
    try:
        with _patch_real_connections(db_path, recorder):
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


def _run_promotion_iteration(
    *,
    root: Path,
    mode: str,
    iteration: int,
    contenders: int,
    timeout: float,
) -> IterationResult:
    db_path = root / f"{mode}-{iteration}.db"
    fact_id = "f_issue_347"
    _migrate_and_seed_promotable_fact(db_path, fact_id)
    stores = [SQLiteGraphStore(str(db_path)) for _ in range(contenders)]
    if mode == "preinitialized-promotion":
        for store in stores:
            store.ensure_schema()

    recorder = TraceRecorder()
    gate = _PromotionGate(contenders)
    worker_errors: list[str] = []
    verdicts: list[str] = []
    lock = threading.Lock()
    start = threading.Barrier(contenders, timeout=timeout)

    for store in stores:
        original = store._promote_to_validated_cas

        def gated(*args, _original=original, **kwargs):
            gate.wait_before_real_cas(timeout)
            return _original(*args, **kwargs)

        store._promote_to_validated_cas = gated  # type: ignore[method-assign]

    def worker(index: int) -> None:
        threading.current_thread().name = f"contender_{index}"
        try:
            start.wait(timeout=timeout)
            verdict = stores[index].validate_and_promote(fact_id, by=f"issue347_{index}")
            with lock:
                verdicts.append(f"{index}:{bool(verdict.passed)}:{verdict.reason}")
        except _PeerPreCasAbort as exc:
            with lock:
                worker_errors.append(f"contender_{index}: diagnostic_abort: {exc}")
        except BaseException as exc:  # noqa: BLE001 - diagnostic records exact class
            _record_worker_exception(recorder, exc)
            gate.mark_pre_cas_failure()
            with lock:
                worker_errors.append(f"contender_{index}: {type(exc).__name__}: {exc}")

    began = time.perf_counter()
    try:
        with _patch_real_connections(db_path, recorder):
            threads = [threading.Thread(target=worker, args=(index,)) for index in range(contenders)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=timeout + 10.0)
                if thread.is_alive():
                    gate.mark_pre_cas_failure()
                    with lock:
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
        pre_cas_reached=gate.reached,
        promotion_verdicts=tuple(sorted(verdicts)),
    )


def _run_iteration(
    *,
    root: Path,
    mode: str,
    iteration: int,
    contenders: int,
    timeout: float,
) -> IterationResult:
    if mode in {"fresh-promotion", "preinitialized-promotion"}:
        return _run_promotion_iteration(
            root=root,
            mode=mode,
            iteration=iteration,
            contenders=contenders,
            timeout=timeout,
        )
    return _run_read_or_ensure_iteration(
        root=root,
        mode=mode,
        iteration=iteration,
        contenders=contenders,
        timeout=timeout,
    )


def run_probe(*, contenders: int, repetitions: int, root: Path) -> dict[str, object]:
    modes = (
        "fresh-read",
        "preinitialized-read",
        "fresh-ensure-only",
        "fresh-promotion",
        "preinitialized-promotion",
    )
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
                f"pre_cas={result.pre_cas_reached}/{contenders} "
                f"integrity={result.integrity_check}"
            )
            for error in result.worker_errors:
                print(f"  worker: {error}")
            for event in result.sql_errors:
                print(
                    f"  sql[{event.sequence}] {event.thread} {event.phase}: "
                    f"{event.error_type}: {event.error} "
                    f"({event.sqlite_errorname}/{event.sqlite_errorcode}) :: {event.sql}"
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
            "min_pre_cas_reached": min((result.pre_cas_reached for result in selected), default=0),
        }

    preinitialized_read_clean = bool(
        by_mode["preinitialized-read"]["failed_iterations"] == 0
        and by_mode["preinitialized-read"]["worker_error_count"] == 0
    )
    preinitialized_promotion_clean = bool(
        by_mode["preinitialized-promotion"]["failed_iterations"] == 0
        and by_mode["preinitialized-promotion"]["worker_error_count"] == 0
    )
    all_integrity_ok = all(result.integrity_check == "ok" for result in results)

    return {
        "schema_version": 3,
        "contenders": contenders,
        "repetitions": repetitions,
        "modes": by_mode,
        "preinitialized_read_control_clean": preinitialized_read_clean,
        "preinitialized_promotion_control_clean": preinitialized_promotion_clean,
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
        report["preinitialized_read_control_clean"]
        and report["preinitialized_promotion_control_clean"]
        and report["all_integrity_checks_ok"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
