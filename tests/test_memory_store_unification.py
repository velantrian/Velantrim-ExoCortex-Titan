"""
Confirmed issue #2: get_store(), _GLOBAL_STORE, and app.store must refer to
the same runtime DB by default. Root cause was two independent config
defaults: core.memory.SQLITE_PATH (VELANTRIM_DB_PATH) and
core.feature_config.DatabaseSettings.sqlite_graph_path (SQLITE_GRAPH_PATH),
which could silently diverge. Fixed by deriving the latter's default from
the former.

NOTE: some other tests in this suite (e.g. test_server_integration.py) purge
`core.*` entries from sys.modules and reimport them under a monkeypatched
env, which can leave a *different* core.memory module object canonical in
sys.modules for the rest of the run than the one bound at this file's
collection time. These tests re-import core.memory inside each test body
(not at module scope) so they always compare against whatever module object
is currently canonical — matching what production code (which also imports
lazily) actually sees.
"""
from __future__ import annotations

import sys
import types

from core.app import VelantrimApp
from core.feature_config import DatabaseSettings, FeatureConfig


def _memory():
    import core.memory as m
    return m


def test_from_env_default_sqlite_graph_path_matches_canonical(monkeypatch):
    monkeypatch.delenv("SQLITE_GRAPH_PATH", raising=False)
    cfg = FeatureConfig.from_env()
    assert cfg.db.sqlite_graph_path == _memory().SQLITE_PATH


def test_explicit_sqlite_graph_path_override_still_wins(monkeypatch):
    monkeypatch.setenv("SQLITE_GRAPH_PATH", "./data/some_other_graph.db")
    cfg = FeatureConfig.from_env()
    assert cfg.db.sqlite_graph_path == "./data/some_other_graph.db"


def test_get_store_falls_back_to_global_store_when_no_app_registered(monkeypatch):
    """get_store()'s `from core.app import get_app` resolves via sys.modules
    at call time — replace the sys.modules entry directly (rather than
    monkeypatching an attribute reached through a possibly-stale module
    reference) so this is immune to any other test's del-sys.modules/reimport
    dance leaving a different core.app object canonical for this run."""
    memory_api = _memory()
    fake_app_module = types.ModuleType("core.app")
    fake_app_module.get_app = lambda: (_ for _ in ()).throw(
        RuntimeError("no app in this test")
    )
    monkeypatch.setitem(sys.modules, "core.app", fake_app_module)

    assert memory_api.get_store() is memory_api._GLOBAL_STORE


def test_get_store_matches_global_store_path_when_app_uses_default_config(
    tmp_path, monkeypatch
):
    """With the fix, a VelantrimApp built from the default config resolves its
    store to the SAME path as _GLOBAL_STORE — not a silently different DB."""
    memory_api = _memory()
    db_path = str(tmp_path / "unified.db")
    monkeypatch.setattr(memory_api, "_GLOBAL_STORE", memory_api.SQLiteGraphStore(db_path))
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.delenv("SQLITE_GRAPH_PATH", raising=False)

    app = VelantrimApp(config=FeatureConfig(db=DatabaseSettings(sqlite_graph_path=db_path)))
    app._init_components()
    fake_app_module = types.ModuleType("core.app")
    fake_app_module.get_app = lambda: app
    monkeypatch.setitem(sys.modules, "core.app", fake_app_module)

    store = memory_api.get_store()
    assert store.db_path == memory_api._GLOBAL_STORE.db_path == db_path


def test_get_store_respects_explicit_per_test_isolation(tmp_path, monkeypatch):
    """An explicitly-constructed VelantrimApp with its OWN db path is a
    deliberate DI feature (test isolation), not a regression of issue #2 —
    get_store() must still surface that isolated store, not silently prefer
    _GLOBAL_STORE."""
    memory_api = _memory()
    isolated_path = str(tmp_path / "isolated.db")

    app = VelantrimApp(config=FeatureConfig(db=DatabaseSettings(sqlite_graph_path=isolated_path)))
    app._init_components()
    fake_app_module = types.ModuleType("core.app")
    fake_app_module.get_app = lambda: app
    monkeypatch.setitem(sys.modules, "core.app", fake_app_module)

    store = memory_api.get_store()
    assert store.db_path == isolated_path
    assert store.db_path != memory_api._GLOBAL_STORE.db_path
