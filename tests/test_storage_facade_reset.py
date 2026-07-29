"""
Regression test for the storage_facade reset/cache fix (Claude audit
2026-07-28, Low).

storage_info() is @lru_cache(maxsize=1) and internally calls
get_graph_store(), which reads the module-level backend singleton.
reset_graph_store() cleared that singleton but never called
storage_info.cache_clear() — so a reset immediately followed by a backend
switch (e.g. STORAGE_BACKEND changing) still returned the pre-reset
backend/capabilities forever, since lru_cache has no idea the underlying
state changed.
"""
from __future__ import annotations

import core.storage_facade as sf


def test_reset_graph_store_clears_the_storage_info_cache(monkeypatch, tmp_path):
    saved_singleton = sf._backend_singleton
    sf.storage_info.cache_clear()
    try:
        monkeypatch.setenv("STORAGE_BACKEND", "memory")
        sf.reset_graph_store()

        info_before = sf.storage_info()
        assert info_before["backend"] == "memory"

        monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
        monkeypatch.setenv("SQLITE_GRAPH_PATH", str(tmp_path / "reset_test.db"))
        sf.reset_graph_store()

        info_after = sf.storage_info()
        assert info_after["backend"] == "sqlite", (
            "reset_graph_store() must invalidate storage_info()'s cache — "
            f"got stale {info_after!r} after switching STORAGE_BACKEND"
        )
    finally:
        sf._backend_singleton = saved_singleton
        sf.storage_info.cache_clear()
