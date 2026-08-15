from __future__ import annotations

from core.storage_facade import reset_graph_store, storage_info


def test_reset_graph_store_refreshes_storage_info_after_backend_switch(
    monkeypatch,
    tmp_path,
):
    try:
        monkeypatch.setenv("STORAGE_BACKEND", "memory")
        reset_graph_store()
        memory_info = storage_info()
        assert memory_info["backend"] == "memory"

        sqlite_path = tmp_path / "switched-graph.db"
        monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
        monkeypatch.setenv("SQLITE_GRAPH_PATH", str(sqlite_path))
        reset_graph_store()

        sqlite_info = storage_info()
        assert sqlite_info["backend"] == "sqlite"
        assert sqlite_info["sqlite_path"] == str(sqlite_path)
        assert sqlite_info is not memory_info
    finally:
        reset_graph_store()


def test_reset_graph_store_refreshes_cached_storage_paths(monkeypatch, tmp_path):
    try:
        monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
        first_path = tmp_path / "first-graph.db"
        monkeypatch.setenv("SQLITE_GRAPH_PATH", str(first_path))
        reset_graph_store()
        first_info = storage_info()
        assert first_info["sqlite_path"] == str(first_path)

        second_path = tmp_path / "second-graph.db"
        monkeypatch.setenv("SQLITE_GRAPH_PATH", str(second_path))
        reset_graph_store()
        second_info = storage_info()

        assert second_info["backend"] == "sqlite"
        assert second_info["sqlite_path"] == str(second_path)
        assert second_info is not first_info
    finally:
        reset_graph_store()
