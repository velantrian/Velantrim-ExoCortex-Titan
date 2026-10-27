"""filelock 4.x compatibility on the real lock paths Titan depends on.

Titan does not import filelock directly; it arrives via huggingface-hub
(model cache downloads, WeakFileLock) and torch. These tests exercise those
lock paths locally: no network, temp dirs only.
"""
import asyncio
import multiprocessing as mp
import time

import pytest

filelock = pytest.importorskip("filelock")
hf_fixes = pytest.importorskip("huggingface_hub.utils._fixes")


def _hold(path, ready, release):
    lock = filelock.FileLock(path)
    with lock:
        ready.set()
        release.wait(10)


def test_major_version_is_4():
    assert int(filelock.__version__.split(".")[0]) == 4


def test_weak_filelock_acquire_release(tmp_path):
    p = tmp_path / "m.lock"
    with hf_fixes.WeakFileLock(p) as lock:
        assert lock.is_locked
    assert not lock.is_locked


def test_released_after_exception(tmp_path):
    p = tmp_path / "e.lock"
    with pytest.raises(RuntimeError):
        with hf_fixes.WeakFileLock(p):
            raise RuntimeError("download failed")
    with filelock.FileLock(p, timeout=0.5):
        pass


def test_timeout_while_held_by_other_process_then_acquire(tmp_path):
    p = str(tmp_path / "x.lock")
    ctx = mp.get_context("spawn")
    ready, release = ctx.Event(), ctx.Event()
    proc = ctx.Process(target=_hold, args=(p, ready, release))
    proc.start()
    try:
        assert ready.wait(10)
        t0 = time.monotonic()
        with pytest.raises(filelock.Timeout):
            with hf_fixes.WeakFileLock(p, timeout=0.3):
                pass
        assert time.monotonic() - t0 < 5
    finally:
        release.set()
        proc.join(10)
    with hf_fixes.WeakFileLock(p, timeout=2):
        pass


def test_released_when_holder_process_killed(tmp_path):
    p = str(tmp_path / "k.lock")
    ctx = mp.get_context("spawn")
    ready, release = ctx.Event(), ctx.Event()
    proc = ctx.Process(target=_hold, args=(p, ready, release))
    proc.start()
    assert ready.wait(10)
    proc.kill()
    proc.join(10)
    with filelock.FileLock(p, timeout=2):
        pass


def test_released_after_asyncio_cancellation(tmp_path):
    p = tmp_path / "c.lock"

    async def scenario():
        entered = asyncio.Event()

        async def worker():
            with hf_fixes.WeakFileLock(p):
                entered.set()
                await asyncio.sleep(30)

        task = asyncio.create_task(worker())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    with filelock.FileLock(p, timeout=0.5):
        pass
