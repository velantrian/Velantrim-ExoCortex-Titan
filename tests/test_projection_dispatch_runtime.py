"""Projection delivery through the real FastAPI lifespan on disposable SQLite stores."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from collections.abc import Callable
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic, sleep

import pytest

_FLAG = "VELANTRIM_PROJECTION_DISPATCH_ENABLED"
_HEALTH = "/health/projection"
_HEADERS = {"X-Api-Key": "projection-integration"}
_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("scenario", ["default_off", "delivery", "restart", "path_mismatch"])
def test_projection_dispatch_fastapi_lifespan(tmp_path: Path, scenario: str) -> None:
    # server and its stores load configuration once on import. A child process
    # gives this test a fresh import without disturbing other tests' globals.
    env = {name: os.environ[name] for name in ("PATH", "SYSTEMROOT") if name in os.environ}
    env.update(
        PYTHONPATH=str(_ROOT),
        PYTHON_DOTENV_DISABLED="1",
        VELANTRIM_API_KEY=_HEADERS["X-Api-Key"],
        VELANTRIM_DB_PATH=str(tmp_path / "memory.db"),
        VELANTRIM_NGRAM_DB=str(tmp_path / "ngram.db"),
        SQLITE_GRAPH_PATH=str(tmp_path / "graph.db"),
        VELANTRIM_NETWORK_MODE="deny",
        VELANTRIM_REMOTE_DATA_MODE="never",
        LLM_PROVIDER="none",
        SLEEP_WORKER_ENABLED="false",
        ENABLE_CAUSAL_GRAPH="0",
        ENABLE_UMWELT_STORE="0",
        ENABLE_COGNITIVE_STORE="0",
        ENABLE_COGNITIVE_RUNTIME="0",
        VELANTRIM_MULTILINGUAL="false",
    )
    if scenario != "default_off":
        env[_FLAG] = "true"
    if scenario == "path_mismatch":
        del env["VELANTRIM_DB_PATH"]
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), scenario],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"


def _await(predicate: Callable[[], bool]) -> None:
    deadline = monotonic() + 5
    while not predicate():
        assert monotonic() < deadline, "projection dispatcher did not converge in 5 s"
        sleep(0.02)


def _queue_promotion(store, fact_id: str) -> str:
    assert store.store_fact({
        "fact_id": fact_id,
        "claim": f"{fact_id} is a verified observation",
        "source": "manual",
        "confidence": 0.95,
        "metadata": {"evidence_refs": ["source-a", "source-b"]},
    })
    assert store.promote_esm_to(fact_id, "Supported", by="dispatch_test_setup")
    # Model an index row missing from a prior failure. The actual promotion
    # is the Canon operation that appends the durable refresh intent.
    with closing(sqlite3.connect(store.db_path)) as conn, conn:
        conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
    assert store.search(fact_id) == []
    assert store.validate_and_promote(fact_id, by="dispatch_test").passed
    with closing(sqlite3.connect(store.db_path)) as conn:
        [(outbox_id,)] = conn.execute(
            "SELECT outbox_id FROM projection_outbox "
            "WHERE aggregate_id = ? AND projection_kind = 'all'", (fact_id,)
        ).fetchall()
    return outbox_id


def _dispatch_state(db_path: str, outbox_id: str) -> tuple | None:
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute(
            "SELECT lifecycle_state, attempt_count, last_error_code "
            "FROM projection_dispatch_state WHERE outbox_id = ?", (outbox_id,)
        ).fetchone()


def _assert_search_projection(store, fact_id: str) -> None:
    assert [row["fact_id"] for row in store.search(fact_id, epistemic_state="Validated")] == [
        fact_id
    ]
    with closing(sqlite3.connect(store.db_path)) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM facts_fts WHERE fact_id = ?", (fact_id,)
        ).fetchone() == (1,)
        versions = conn.execute(
            "SELECT pc.applied_canonical_version, f.fact_version "
            "FROM projection_checkpoints pc JOIN facts f ON f.fact_id = pc.aggregate_id "
            "WHERE pc.projection_kind = 'fts' AND pc.aggregate_id = ?", (fact_id,)
        ).fetchall()
    [(applied, canonical)] = versions
    assert applied == canonical


def _default_off() -> None:
    from fastapi.testclient import TestClient

    import server

    with TestClient(server.app) as client:
        assert client.get(_HEALTH).status_code == 401
        outbox_id = _queue_promotion(server._store, "dormantprojection")
        response = client.get(_HEALTH, headers=_HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "disabled"
        assert _dispatch_state(server.DB_PATH, outbox_id) is None
        assert server._store.search("dormantprojection") == []


def _delivery() -> None:
    from fastapi.testclient import TestClient

    import server
    from core.projection_outbox import LOCAL_PROJECTION_SCOPE_REF, PROJECTION_OUTBOX_POLICY_VERSION

    with TestClient(server.app) as client:
        with closing(sqlite3.connect(server.DB_PATH)) as conn, conn:
            # Simulate invalid data left by an external SQLite import. INTEGER
            # affinity and the existing CHECK still admit this storage class.
            conn.execute(
                "INSERT INTO projection_outbox VALUES "
                "('invalid-version', 'fact', 'typedversionprojection', ?, 'fts', "
                " 'refresh', 'invalid', ?, '2000-01-01T00:00:00+00:00')",
                (LOCAL_PROJECTION_SCOPE_REF, PROJECTION_OUTBOX_POLICY_VERSION),
            )
        outbox_id = _queue_promotion(server._store, "typedversionprojection")
        _await(lambda: _dispatch_state(server.DB_PATH, outbox_id) == ("acknowledged", 1, None))
        assert _dispatch_state(server.DB_PATH, "invalid-version") == ("parked", 1, "INTERNAL_CONTRACT")
        _assert_search_projection(server._store, "typedversionprojection")
        _await(lambda: client.get(_HEALTH, headers=_HEADERS).json().get("pending") == 0)
        health = client.get(_HEALTH, headers=_HEADERS).json()
        assert health["status"] == "running"
        assert health["parked"] == 1
        assert health["last_success_at"]
        assert health["consecutive_errors"] == 0
        assert health["oldest_pending_age_seconds"] is None
        assert "invalid-version" not in str(health)

        with closing(sqlite3.connect(server.DB_PATH)) as blocker:
            blocker.execute("BEGIN IMMEDIATE")
            _await(lambda: client.get(_HEALTH, headers=_HEADERS).json()["status"] == "degraded")
            assert client.get(_HEALTH, headers=_HEADERS).json()["consecutive_errors"] >= 1
        _await(lambda: client.get(_HEALTH, headers=_HEADERS).json()["status"] == "running")
    assert server.app.state.projection_dispatch_runtime.diagnostics()["status"] == "stopped"


def _restart() -> None:
    from fastapi.testclient import TestClient

    import server
    from core.projection_dispatcher import (
        AckOutcome,
        DispatchAction,
        DispatchErrorCode,
        RetryOutcome,
        ack_claim,
        apply_claimed_work,
        claim_batch,
        retry_claim,
    )
    from scripts.apply_migrations import apply_migrations

    db_path = server.DB_PATH
    apply_migrations(Path(db_path), skip_backup=True)
    applied_id = _queue_promotion(server._store, "replayedprojection")
    retried_id = _queue_promotion(server._store, "retriedprojection")
    previously = datetime.now(UTC) - timedelta(minutes=5)
    with closing(sqlite3.connect(db_path)) as conn:
        leases = {
            work.outbox_id: work for work in claim_batch(
                conn, batch_size=2, lease_duration_seconds=30, now=previously,
            )
        }
        applied = leases[applied_id]
        retried = leases[retried_id]
        assert apply_claimed_work(conn, applied, now=previously).action is DispatchAction.ACKNOWLEDGE
        assert retry_claim(
            conn, retried_id, retried.lease_token, error_code=DispatchErrorCode.SQLITE_BUSY,
            now=previously,
        ) is RetryOutcome.RETRY_SCHEDULED
    assert _dispatch_state(db_path, applied_id) == ("leased", 1, None)
    assert _dispatch_state(db_path, retried_id) == ("retry", 1, "SQLITE_BUSY")

    with TestClient(server.app):
        for outbox_id in (applied_id, retried_id):
            _await(lambda: _dispatch_state(db_path, outbox_id) == ("acknowledged", 2, None))
        with closing(sqlite3.connect(db_path)) as conn:
            assert ack_claim(conn, applied_id, applied.lease_token, now=datetime.now(UTC)) is (
                AckOutcome.ACK_REJECTED
            )
        _assert_search_projection(server._store, "replayedprojection")
        _assert_search_projection(server._store, "retriedprojection")
    first_runtime = server.app.state.projection_dispatch_runtime
    assert first_runtime.diagnostics()["status"] == "stopped"

    queued_between_starts = _queue_promotion(server._store, "restartprojection")
    assert _dispatch_state(db_path, queued_between_starts) is None
    with TestClient(server.app):
        assert server.app.state.projection_dispatch_runtime is not first_runtime
        _await(lambda: _dispatch_state(db_path, queued_between_starts) == ("acknowledged", 1, None))
        _assert_search_projection(server._store, "restartprojection")
    assert server.app.state.projection_dispatch_runtime.diagnostics()["status"] == "stopped"


def _path_mismatch() -> None:
    from fastapi.testclient import TestClient

    import server

    assert Path(server.DB_PATH).resolve() != Path(server._store.db_path).resolve()
    with pytest.raises(RuntimeError, match="Set VELANTRIM_DB_PATH to the Canon database"):
        with TestClient(server.app):
            pytest.fail("mismatched database paths should prevent startup")
    assert not Path(server.DB_PATH).exists()


if __name__ == "__main__":
    scenarios = {
        "default_off": _default_off,
        "delivery": _delivery,
        "restart": _restart,
        "path_mismatch": _path_mismatch,
    }
    scenarios[sys.argv[1]]()
