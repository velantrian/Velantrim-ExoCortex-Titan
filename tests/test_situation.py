"""tests/test_situation.py

#26 (Claude audit 2026-07-28): build_situation()'s LivingContext enrichment
step wrapped its except in a bare `except Exception: pass` — completely
silent, no log at all — and never closed the sqlite3.Connection it opened,
leaking one connection per call regardless of success or failure.
"""
from __future__ import annotations

import logging
import sqlite3

import pytest


def _fact(fid: str) -> dict:
    return {"fact_id": fid, "claim": "x", "source": "test", "confidence": 0.9}


def test_build_situation_closes_connection_on_living_context_failure(
    tmp_path, monkeypatch, caplog,
):
    """A virgin DB (no fact_living_context table) makes LivingContextStore.get()
    raise sqlite3.OperationalError — a realistic, common failure — and the
    connection opened for it must still be closed, with the failure logged
    rather than silently absorbed."""
    from core.essence_facade.situation import build_situation

    db_path = str(tmp_path / "virgin.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)

    captured_conns: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect

    def _spy_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        captured_conns.append(conn)
        return conn

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)

    with caplog.at_level(logging.DEBUG, logger="velantrim.essence_facade.situation"):
        model = build_situation([_fact("f1")], "query", user_id="default")

    assert model is not None
    assert len(captured_conns) == 1
    with pytest.raises(sqlite3.ProgrammingError):
        captured_conns[0].execute("SELECT 1")  # closed database raises

    assert any(
        "LivingContext enrichment skipped" in r.message
        for r in caplog.records
    ), f"failure was not logged: {[r.message for r in caplog.records]}"


def test_build_situation_closes_connection_on_success(tmp_path, monkeypatch):
    """Same connection-leak fix, success path: a real fact_living_context
    table with no matching row (the common case — most facts never get a
    LivingContext entry) must still close its connection."""
    from core.essence_facade.situation import build_situation

    db_path = str(tmp_path / "with_schema.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE fact_living_context (
            fact_id TEXT PRIMARY KEY, ctx_where TEXT, ctx_who TEXT,
            ctx_how TEXT, ctx_what TEXT, ctx_feel TEXT, ctx_role TEXT,
            ctx_time TEXT, ctx_deep TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)

    captured_conns: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect

    def _spy_connect(*args, **kwargs):
        c = real_connect(*args, **kwargs)
        captured_conns.append(c)
        return c

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)

    model = build_situation([_fact("f1")], "query", user_id="default")

    assert model is not None
    assert len(captured_conns) == 1
    with pytest.raises(sqlite3.ProgrammingError):
        captured_conns[0].execute("SELECT 1")
