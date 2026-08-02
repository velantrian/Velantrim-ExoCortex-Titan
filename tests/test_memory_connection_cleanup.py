"""Regression coverage for SQLiteGraphStore connection cleanup races."""

from __future__ import annotations

import sqlite3
import threading

from core.memory import SQLiteGraphStore


def test_release_stray_locks_clears_a_stale_closed_cached_handle(tmp_path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "closed-handle.db"))
    stale = sqlite3.connect(store.db_path, check_same_thread=False)
    stale.close()
    store._sqlite_conn = stale

    store._release_stray_locks()

    assert store._sqlite_conn is None


def test_release_stray_locks_holds_connection_owner_lock(tmp_path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "serialized-cleanup.db"))
    entered = threading.Event()
    allow_property_return = threading.Event()
    closer_finished = threading.Event()
    errors: list[BaseException] = []

    class BlockingConnection:
        closed = False
        committed = False

        @property
        def in_transaction(self) -> bool:
            entered.set()
            assert allow_property_return.wait(timeout=5)
            if self.closed:
                raise sqlite3.ProgrammingError("Cannot operate on a closed database.")
            return True

        def commit(self) -> None:
            if self.closed:
                raise sqlite3.ProgrammingError("Cannot operate on a closed database.")
            self.committed = True

    connection = BlockingConnection()
    store._sqlite_conn = connection  # type: ignore[assignment]

    def release() -> None:
        try:
            store._release_stray_locks()
        except BaseException as exc:  # pragma: no cover - assertion reports it
            errors.append(exc)

    def close_under_owner_lock() -> None:
        assert entered.wait(timeout=5)
        with store._db_lock:
            connection.closed = True
            if store._sqlite_conn is connection:
                store._sqlite_conn = None
        closer_finished.set()

    releaser = threading.Thread(target=release)
    closer = threading.Thread(target=close_under_owner_lock)
    releaser.start()
    closer.start()

    assert entered.wait(timeout=5)
    assert closer_finished.wait(timeout=0.05) is False
    allow_property_return.set()

    releaser.join(timeout=5)
    closer.join(timeout=5)

    assert errors == []
    assert connection.committed is True
    assert closer_finished.is_set()
    assert store._sqlite_conn is None
