from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import textwrap
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core.memory import SQLiteGraphStore


ROOT = Path(__file__).resolve().parents[1]


def _fact(fact_id: str, *, confidence: float = 0.8) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "claim": f"SQLite resilience characterization fact {fact_id}",
        "source": "sqlite_resilience_test",
        "confidence": confidence,
        "metadata": {"resilience_test": True},
    }


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=30.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def _run_child(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(ROOT)
        if not current_pythonpath
        else os.pathsep.join((str(ROOT), current_pythonpath))
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=45.0,
        check=False,
    )


def test_same_instance_serializes_100_threaded_writes(tmp_path) -> None:
    db_path = tmp_path / "same-instance.db"
    store = SQLiteGraphStore(str(db_path))
    start = threading.Event()

    def write_one(index: int) -> str | None:
        start.wait()
        try:
            store.store_fact(_fact(f"same-{index}"))
        except Exception as exc:  # noqa: BLE001 - test reports every failure
            return f"{type(exc).__name__}: {exc}"
        return None

    try:
        with ThreadPoolExecutor(max_workers=32) as pool:
            futures = [pool.submit(write_one, index) for index in range(100)]
            start.set()
            errors = [
                error
                for future in futures
                if (error := future.result(timeout=45.0)) is not None
            ]

        assert errors == []
        facts = store.get_all_facts()
        assert len(facts) == 100
        assert {fact["fact_id"] for fact in facts} == {
            f"same-{index}" for index in range(100)
        }
    finally:
        store.close()

    assert _integrity_check(db_path) == "ok"


def test_25_independent_store_instances_commit_without_missing_facts(tmp_path) -> None:
    db_path = tmp_path / "multi-instance.db"
    bootstrap = SQLiteGraphStore(str(db_path))
    bootstrap.ensure_schema()
    bootstrap.close()

    stores = [SQLiteGraphStore(str(db_path)) for _ in range(25)]
    for store in stores:
        store.ensure_schema()
    start = threading.Event()

    def write_one(index: int) -> str | None:
        start.wait()
        try:
            stores[index].store_fact(_fact(f"multi-{index}"))
        except Exception as exc:  # noqa: BLE001 - test reports every failure
            return f"{type(exc).__name__}: {exc}"
        return None

    try:
        with ThreadPoolExecutor(max_workers=25) as pool:
            futures = [pool.submit(write_one, index) for index in range(25)]
            start.set()
            errors = [
                error
                for future in futures
                if (error := future.result(timeout=45.0)) is not None
            ]
    finally:
        for store in stores:
            store.close()

    assert errors == []

    verifier = SQLiteGraphStore(str(db_path))
    try:
        facts = verifier.get_all_facts()
        assert len(facts) == 25
        assert {fact["fact_id"] for fact in facts} == {
            f"multi-{index}" for index in range(25)
        }
    finally:
        verifier.close()

    assert _integrity_check(db_path) == "ok"


def test_mixed_multi_instance_readers_and_writers_observe_complete_rows(tmp_path) -> None:
    db_path = tmp_path / "mixed.db"
    seed = SQLiteGraphStore(str(db_path))
    for index in range(10):
        seed.store_fact(_fact(f"seed-{index}"))
    seed.close()

    stores = [SQLiteGraphStore(str(db_path)) for _ in range(20)]
    for store in stores:
        store.ensure_schema()
    start = threading.Event()

    def writer(index: int) -> str | None:
        start.wait()
        try:
            stores[index].store_fact(_fact(f"mixed-write-{index}"))
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"
        return None

    def reader(index: int) -> str | None:
        start.wait()
        store = stores[10 + index]
        try:
            for read_index in range(40):
                fact = store.get_fact(f"seed-{read_index % 10}")
                if fact is None or not fact.get("claim"):
                    return f"incomplete seed row at iteration {read_index}"
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"
        return None

    try:
        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(writer, index) for index in range(10)]
            futures.extend(pool.submit(reader, index) for index in range(10))
            start.set()
            errors = [
                error
                for future in futures
                if (error := future.result(timeout=45.0)) is not None
            ]
    finally:
        for store in stores:
            store.close()

    assert errors == []

    verifier = SQLiteGraphStore(str(db_path))
    try:
        assert len(verifier.get_all_facts()) == 20
    finally:
        verifier.close()
    assert _integrity_check(db_path) == "ok"


def test_committed_store_fact_survives_abrupt_process_exit(tmp_path) -> None:
    db_path = tmp_path / "committed-crash.db"
    code = textwrap.dedent(
        f"""
        import os
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore({str(db_path)!r})
        store.store_fact({{
            "fact_id": "committed-before-exit",
            "claim": "Committed write must survive abrupt process exit",
            "source": "crash-test",
            "confidence": 0.8,
        }})
        os._exit(17)
        """
    )

    child = _run_child(code)
    assert child.returncode == 17, child.stderr

    verifier = SQLiteGraphStore(str(db_path))
    try:
        fact = verifier.get_fact("committed-before-exit")
        assert fact is not None
        assert fact["claim"] == "Committed write must survive abrupt process exit"
    finally:
        verifier.close()
    assert _integrity_check(db_path) == "ok"


def test_uncommitted_update_rolls_back_after_abrupt_process_exit(tmp_path) -> None:
    db_path = tmp_path / "uncommitted-crash.db"
    seed = SQLiteGraphStore(str(db_path))
    seed.store_fact(_fact("rollback-target", confidence=0.8))
    seed.close()

    code = textwrap.dedent(
        f"""
        import os
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore({str(db_path)!r})
        context = store._db()
        conn = context.__enter__()
        conn.execute(
            "UPDATE facts SET confidence = ? WHERE fact_id = ?",
            (0.1, "rollback-target"),
        )
        os._exit(18)
        """
    )

    child = _run_child(code)
    assert child.returncode == 18, child.stderr

    verifier = SQLiteGraphStore(str(db_path))
    try:
        fact = verifier.get_fact("rollback-target")
        assert fact is not None
        assert float(fact["confidence"]) == 0.8
    finally:
        verifier.close()
    assert _integrity_check(db_path) == "ok"
