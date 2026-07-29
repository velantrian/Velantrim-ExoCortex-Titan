"""
Regression test for the core/app.py _create_causal_graph() dead-DI-factory
fix (Claude audit 2026-07-28, Low).

_create_causal_graph() used to call `_GLOBAL_STORE._conn()` — a method that
doesn't exist on SQLiteGraphStore (the real one is `_db()`, a @contextmanager
whose connection closes on exit anyway, unsuitable for a long-lived
CausalGraph). Every access to `VelantrimApp().causal_graph` with
enable_causal_graph=True (the default) raised AttributeError. Fixed by
opening the factory's own persistent connection to the store's db_path
instead of trying to borrow the store's internal one.
"""
from __future__ import annotations

from core.app import VelantrimApp
from core.causal_graph import CausalGraph
from core.feature_config import DatabaseSettings, FeatureConfig


def test_causal_graph_property_does_not_raise_with_a_live_store(tmp_path):
    db_path = str(tmp_path / "app_causal.db")
    cfg = FeatureConfig(db=DatabaseSettings(sqlite_graph_path=db_path))
    app = VelantrimApp(config=cfg)
    app._init_components()

    # Touch .store first so _GLOBAL_STORE is populated (the branch this bug
    # was in) before accessing .causal_graph.
    assert app.store is not None

    graph = app.causal_graph
    assert isinstance(graph, CausalGraph)


def test_causal_graph_property_works_without_a_live_store(tmp_path):
    """The `_GLOBAL_STORE is None` fallback branch — must keep working too."""
    import core.memory as memory_mod

    db_path = str(tmp_path / "app_causal_no_store.db")
    cfg = FeatureConfig(db=DatabaseSettings(sqlite_graph_path=db_path))
    app = VelantrimApp(config=cfg)
    app._init_components()

    saved = memory_mod._GLOBAL_STORE
    memory_mod._GLOBAL_STORE = None
    try:
        graph = app.causal_graph
        assert isinstance(graph, CausalGraph)
    finally:
        memory_mod._GLOBAL_STORE = saved
