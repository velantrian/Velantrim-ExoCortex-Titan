"""Core-block failures and initialization must preserve committed values."""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread

import pytest
from core.sleep_time_worker import CoreMemoryBlocks


@pytest.mark.parametrize('name', ['current_goals', 'new_custom_block'])
def test_rejected_write_preserves_disk_cache_context_and_retry(tmp_path, name):
    path = str(tmp_path / 'blocks.db')
    blocks = CoreMemoryBlocks(path)
    if name == 'current_goals':
        blocks.update(name, 'previous accepted goal')
    before = blocks.all_as_dict()
    timestamps = {k: v.last_updated for k, v in blocks.blocks.items()}
    context = blocks.get_system_context()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TRIGGER deny_write BEFORE INSERT ON core_blocks BEGIN SELECT RAISE(ABORT, 'synthetic write refusal'); END")
    with pytest.raises(sqlite3.IntegrityError, match='synthetic write refusal'):
        blocks.update(name, 'uncommitted candidate')
    assert blocks.all_as_dict() == before
    assert {k: v.last_updated for k, v in blocks.blocks.items()} == timestamps
    assert blocks.get_system_context() == context
    assert CoreMemoryBlocks(path).all_as_dict() == before
    with sqlite3.connect(path) as db:
        db.execute('DROP TRIGGER deny_write')
    blocks.update(name, 'accepted retry')
    expected = dict(before, **{name: 'accepted retry'})
    assert blocks.all_as_dict() == expected
    assert CoreMemoryBlocks(path).all_as_dict() == expected


def test_connection_failure_keeps_original_value(monkeypatch, tmp_path):
    path = str(tmp_path / 'blocks.db')
    blocks = CoreMemoryBlocks(path)
    old, context = blocks.all_as_dict(), blocks.get_system_context()
    with monkeypatch.context() as m:
        def fail_connect(*args, **kwargs):
            raise sqlite3.OperationalError('synthetic connection failure')
        m.setattr(sqlite3, 'connect', fail_connect)
        with pytest.raises(sqlite3.OperationalError, match='synthetic connection failure'):
            blocks.update('current_goals', 'not durable')
    assert blocks.all_as_dict() == old
    assert blocks.get_system_context() == context
    assert CoreMemoryBlocks(path).all_as_dict() == old


def test_commit_failure_keeps_original_value(monkeypatch, tmp_path):
    path = str(tmp_path / 'blocks.db')
    blocks = CoreMemoryBlocks(path)
    old, context = blocks.all_as_dict(), blocks.get_system_context()
    connect = sqlite3.connect
    class FailCommit(sqlite3.Connection):
        def commit(self):
            raise sqlite3.OperationalError('synthetic commit failure')
    with monkeypatch.context() as m:
        m.setattr(sqlite3, 'connect', lambda *a, **kw: connect(*a, **kw, factory=FailCommit))
        with pytest.raises(sqlite3.OperationalError, match='synthetic commit failure'):
            blocks.update('current_goals', 'not durable')
    assert blocks.all_as_dict() == old
    assert blocks.get_system_context() == context
    assert CoreMemoryBlocks(path).all_as_dict() == old


def test_concurrent_default_initialization_preserves_committed_value(monkeypatch, tmp_path):
    path = str(tmp_path / 'blocks.db')
    snapshot_loaded, resume = Event(), Event()
    owner_thread = current_thread()
    connect = sqlite3.connect

    class PausedSnapshotCursor(sqlite3.Cursor):
        def fetchall(self):
            rows = super().fetchall()
            if not snapshot_loaded.is_set():
                snapshot_loaded.set()
                assert resume.wait(5), 'default initialization was not resumed'
            return rows

    class PausedSnapshotConnection(sqlite3.Connection):
        def execute(self, *args, **kwargs):
            return self.cursor(factory=PausedSnapshotCursor).execute(*args, **kwargs)

    def connect_with_paused_reader(*args, **kwargs):
        if current_thread() is not owner_thread:
            kwargs['factory'] = PausedSnapshotConnection
        return connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, 'connect', connect_with_paused_reader)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(CoreMemoryBlocks, path)
        try:
            assert snapshot_loaded.wait(5), 'initial database snapshot was not read'
            writer = CoreMemoryBlocks(path)
            writer.update('current_goals', 'explicitly accepted goal')
            expected = writer.all_as_dict()
            timestamps = {k: v.last_updated for k, v in writer.blocks.items()}
            context = writer.get_system_context()
        finally:
            resume.set()
        delayed = pending.result(timeout=5)

    assert delayed.get('current_goals') == 'explicitly accepted goal'
    assert delayed.all_as_dict() == expected
    assert {k: v.last_updated for k, v in delayed.blocks.items()} == timestamps
    assert delayed.get_system_context() == context
    restored = CoreMemoryBlocks(path)
    assert restored.all_as_dict() == expected
    assert {k: v.last_updated for k, v in restored.blocks.items()} == timestamps
