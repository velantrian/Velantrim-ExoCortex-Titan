"""Deterministic commit/publication gates for one CoreMemoryBlocks instance.

These tests pause writer A just after a real SQLite commit and before RAM
publication. On PR #490's baseline, writer B can publish a newer committed
value first, after which A overwrites the local cache with stale content.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread

import pytest

from core.sleep_time_worker import CoreMemoryBlocks


def _pause_first_writer_after_real_commit(monkeypatch):
    committed = Event()
    resume = Event()
    real_connect = sqlite3.connect

    class PausedCommitConnection(sqlite3.Connection):
        def commit(self):
            super().commit()
            committed.set()
            assert resume.wait(10), "timed out waiting to resume writer A"

    def connect(*args, **kwargs):
        if current_thread().name == "core-blocks-paused-writer-A":
            return real_connect(*args, **kwargs, factory=PausedCommitConnection)
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    return committed, resume, real_connect


def _update_as_paused_writer(blocks, name, content):
    current_thread().name = "core-blocks-paused-writer-A"
    blocks.update(name, content)


@pytest.mark.parametrize("name", ["current_goals", "new_custom_block"])
def test_same_instance_never_publishes_older_committed_value(monkeypatch, tmp_path, name):
    path = str(tmp_path / "blocks.db")
    blocks = CoreMemoryBlocks(path)
    committed, resume, real_connect = _pause_first_writer_after_real_commit(monkeypatch)
    second_started, second_finished = Event(), Event()

    def second_writer():
        second_started.set()
        blocks.update(name, "B: newer commit")
        second_finished.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(_update_as_paused_writer, blocks, name, "A: older commit")
        try:
            assert committed.wait(5), "writer A did not reach the post-commit gate"
            second = executor.submit(second_writer)
            assert second_started.wait(5), "writer B did not start"
            # Pre-fix B completes while A is paused, publishing B before A.
            # After serialization B waits for A to publish before entering SQLite.
            second_finished_before_release = second_finished.wait(1)
        finally:
            resume.set()
        first.result(timeout=5)
        second.result(timeout=5)

    connection = real_connect(path)
    try:
        row = connection.execute(
            "SELECT content, last_updated FROM core_blocks WHERE name = ?", (name,)
        ).fetchone()
    finally:
        connection.close()
    assert not second_finished_before_release, "writer B bypassed pending publication"
    assert row is not None
    assert row[0] == "B: newer commit"
    assert blocks.get(name) == row[0]
    assert blocks.blocks[name].last_updated == row[1]
    assert blocks.all_as_dict()[name] == row[0]
    assert f"## {name}\n{row[0]}" in blocks.get_system_context()


@pytest.mark.parametrize("reader", ["get", "all_as_dict", "get_system_context"])
def test_same_instance_reader_waits_for_commit_and_publication(monkeypatch, tmp_path, reader):
    path = str(tmp_path / "blocks.db")
    blocks = CoreMemoryBlocks(path)
    committed, resume, _ = _pause_first_writer_after_real_commit(monkeypatch)
    read_started, read_finished = Event(), Event()

    def read_context():
        read_started.set()
        if reader == "get":
            result = blocks.get("current_goals")
        elif reader == "all_as_dict":
            result = blocks.all_as_dict()["current_goals"]
        else:
            result = blocks.get_system_context()
        read_finished.set()
        return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        writer = executor.submit(
            _update_as_paused_writer, blocks, "current_goals", "committed goal"
        )
        try:
            assert committed.wait(5)
            reader_future = executor.submit(read_context)
            assert read_started.wait(5)
            observed_during_publication = read_finished.wait(0.5)
        finally:
            resume.set()
        writer.result(timeout=5)
        observed = reader_future.result(timeout=5)

    assert not observed_during_publication, "reader crossed the commit/cache publication gap"
    if reader == "get_system_context":
        assert "## current_goals\ncommitted goal" in observed
    else:
        assert observed == "committed goal"


def test_distinct_instances_still_keep_independent_snapshots(tmp_path):
    """No claim of cross-instance cache coherence or compare-and-swap."""
    path = str(tmp_path / "blocks.db")
    first = CoreMemoryBlocks(path)
    second = CoreMemoryBlocks(path)
    first.update("current_goals", "from first")
    second.update("current_goals", "from second")

    assert first.get("current_goals") == "from first"
    assert second.get("current_goals") == "from second"
    assert CoreMemoryBlocks(path).get("current_goals") == "from second"
