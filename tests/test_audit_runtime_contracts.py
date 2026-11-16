"""Producer/consumer and failure-path regressions from the repository audit."""
import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest


@pytest.mark.parametrize("backend", ["sqlite", "ladybug"])
def test_edge_upsert_preserves_existing_node_payload(tmp_path, monkeypatch, backend):
    if backend == "sqlite":
        from core.backends.sqlite_graph import SQLiteGraphStore
        store = SQLiteGraphStore(tmp_path / "graph.db")
    else:
        pytest.importorskip("ladybug")
        from core.backends.ladybug_graph import LadybugGraphStore
        monkeypatch.setenv("LADYBUG_BUFFER_POOL_MB", "64")
        store = LadybugGraphStore(tmp_path / "graph.lbug")
    try:
        store.upsert_node("a", label="Fact", claim="preserve me", confidence=.91)
        store.upsert_edge("a", "new")
        store.upsert_edge("a", "new", weight=.5)
        if backend == "sqlite":
            with sqlite3.connect(store._path) as conn:
                label, props = conn.execute("SELECT label, props_json FROM gs_nodes WHERE node_id='a'").fetchone()
            props = json.loads(props)
        else:
            from core.backends.cypher_graph_base import _decode_json
            row = store._query("MATCH (n:GsNode {node_id: $id}) RETURN n.label AS label, n.props_json AS props", {"id": "a"})[0]
            label, props = row["label"], _decode_json(row["props"])
        assert label == "Fact"
        assert props == {"claim": "preserve me", "confidence": .91}
        assert "new" in store.get_neighbors("a")
    finally:
        if hasattr(store, "close"):
            store.close()


def test_embedding_commit_failure_reports_zero_and_closes(tmp_path, monkeypatch):
    from core.embedding_store import EmbeddingStore
    import core.embedding_store as module
    path = str(tmp_path / "vectors.db")
    store = EmbeddingStore(path)
    store.ensure_table()
    real_connect = sqlite3.connect
    connections = []
    class FailingCommit(sqlite3.Connection):
        closed = False
        def commit(self):
            raise sqlite3.OperationalError("synthetic commit failure")
        def close(self):
            self.closed = True
            super().close()
    def connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs, factory=FailingCommit)
        connections.append(conn)
        return conn
    monkeypatch.setattr(module.sqlite3, "connect", connect)
    assert store.store_batch([("a", np.array([1., 2.])), ("b", np.array([3., 4.]))]) == 0
    assert connections and all(c.closed for c in connections)
    with real_connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM gs_vectors").fetchone()[0] == 0


def test_blocks_read_committed_values_across_instances(tmp_path):
    from core.sleep_time_worker import CoreMemoryBlocks
    a = CoreMemoryBlocks(str(tmp_path / "blocks.db"))
    b = CoreMemoryBlocks(a.db_path)
    a.update("current_goals", "first")
    assert b.get("current_goals") == "first"
    b.update("current_goals", "second")
    assert a.get("current_goals") == "second"
    assert "second" in a.get_system_context()
    assert a.all_as_dict()["current_goals"] == "second"


async def test_worker_start_is_idempotent_and_stop_awaits_episode_tasks(tmp_path, monkeypatch):
    from core.sleep_time_worker import NotebookStore, SleepTimeWorker
    worker = SleepTimeWorker("audit", notebook_store=NotebookStore(str(tmp_path / "notebook.db")))
    entered, cancelled = asyncio.Event(), asyncio.Event()
    async def blocked_think():
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
    monkeypatch.setattr(worker, "think", blocked_think)
    await worker.start()
    task = worker._task
    await worker.start()
    assert worker._task is task
    await worker.update_from_episode({"content": "A sufficiently long episode for the background worker"})
    await entered.wait()
    await worker.update_from_episode({"content": "Another episode while the previous think is still running"})
    assert len(worker._bg_tasks) == 1
    await worker.stop()
    assert cancelled.is_set() and task.done() and not worker._bg_tasks
    await worker.start()
    assert worker._task is not task
    await worker.stop()


async def test_event_bus_background_delivery_shutdown_and_inline_fallback():
    from core.event_bus import EventBus
    bus = EventBus()
    received = asyncio.Event()
    async def handler(event):
        received.set()
    bus.subscribe("AUDIT", handler)
    assert await bus.publish({"type": "AUDIT"}, dispatch=False)
    assert received.is_set()  # no consumer must never turn success into undelivered work
    received.clear()
    await bus.start()
    first = bus._consumer
    await bus.start()
    assert bus._consumer is first
    assert await bus.publish({"type": "AUDIT"}, dispatch=False)
    await asyncio.wait_for(received.wait(), 1)
    await bus.stop()
    assert first.done()
    assert bus.get_metrics().consumed_total == 2


def test_archive_parallel_contexts_preserve_all_child_text(tmp_path):
    import zipfile
    from core.file_parsers.file_ingester import FileIngester
    ingester = FileIngester()
    paths = []
    text = "distinct child payload " * 200
    for i in range(8):
        path = tmp_path / f"archive{i}.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("child.txt", text + str(i))
        paths.append(path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda p: ingester.ingest(str(p)), paths))
    for i, result in enumerate(results):
        assert not result.error
        assert result.structured_data["depth"] == 0
        assert text + str(i) in result.extracted_text
    assert ingester.registry._initialized["archive"]._depth == 0


def test_real_mhi_report_reaches_export_spec():
    from core.mhi import MHIReport, MHIStatus
    from core.velantrim_reports.mhi_report import generate_mhi_report
    report = MHIReport(.7, MHIStatus.HEALTHY, .8, .6, .7, .7, 10, 8, 0, 1, "now", [])
    spec = generate_mhi_report(report)
    serialized = repr(spec)
    assert "MHI = 0.700" in serialized and "0.600" in serialized
    assert "Validated фактов" in serialized and "'8'" in serialized


def test_di_constructor_store_replacement_and_causal_connection_ownership(tmp_path):
    from core.app import VelantrimApp
    from core.feature_config import FeatureConfig
    from core.memory import SQLiteGraphStore
    config = FeatureConfig()
    config.db.sqlite_graph_path = str(tmp_path / "app.db")
    config.app.enable_causal_graph = True
    app = VelantrimApp(config=config)
    assert app.store.db_path == config.db.sqlite_graph_path
    replacement = SQLiteGraphStore(str(tmp_path / "replacement.db"))
    try:
        app.store = replacement
        assert app.store is replacement
        graph = app.causal_graph
        assert graph._conn.execute("PRAGMA database_list").fetchone()[2] == replacement.db_path
        app.close()
        with pytest.raises(sqlite3.ProgrammingError):
            graph._conn.execute("SELECT 1")
        assert replacement.get_all_facts() == []  # injected object was not closed
    finally:
        replacement.close()
        app.close()


def test_facade_bridges_use_real_functions_and_selected_notebook():
    from core.essence_facade.observer_bridge import get_observer_bridge
    from core.essence_facade.mirror import get_mirror_bridge
    from core.observer import observe
    from core.working_notebook import get_notebook
    assert get_observer_bridge() is observe
    assert get_mirror_bridge("audit-specific-session") is get_notebook("audit-specific-session")


def test_branch_retrieval_uses_policy_owner_not_full_store(monkeypatch):
    from core.branch_manager import BranchManager
    from core import pipeline
    monkeypatch.setattr(pipeline, "run", lambda query: {"facts": [{"fact_id": "bounded"}]})
    assert BranchManager()._retrieve_with_hints("test", {}) == [{"fact_id": "bounded"}]
    monkeypatch.setattr(pipeline, "run", lambda query: {"reason_code": "facts_pack_policy_unavailable"})
    with pytest.raises(RuntimeError, match="retrieval_policy_unavailable"):
        BranchManager()._retrieve_with_hints("test", {})


def test_graph_lab_bridge_reads_real_db_and_closes_owned_connection(tmp_path, monkeypatch):
    from core import graph_lab, graph_lab_bridge
    path = str(tmp_path / "lab.db")
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE relations (from_fact_id TEXT, to_fact_id TEXT, relation_type TEXT, confidence REAL, knowledge_status TEXT)")
        conn.executemany("INSERT INTO relations VALUES (?, ?, 'causes', .8, 'known')", [("a", "b"), ("b", "c"), ("c", "a")])
    seen = []
    original = graph_lab.analyze
    def analyze(*args, **kwargs):
        seen.append(kwargs["conn"])
        return original(*args, **kwargs)
    monkeypatch.setattr(graph_lab, "analyze", analyze)
    result = graph_lab_bridge.analyze_graph(db_path=path, max_cycle_len=2)
    assert result["available"] and result["node_count"] == 3
    assert result["cycles"] == []
    with pytest.raises(sqlite3.ProgrammingError):
        seen[0].execute("SELECT 1")
    assert graph_lab_bridge.get_bridge_concepts(domain_a="physics")["reason"] == "domain_filter_not_supported"


def test_graph_lab_node_budget_and_cycle_enumeration_are_bounded(monkeypatch):
    import networkx as nx
    from core import graph_lab
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE relations (from_fact_id TEXT, to_fact_id TEXT, relation_type TEXT, confidence REAL, knowledge_status TEXT)")
        conn.executemany("INSERT INTO relations VALUES (?, ?, 'causes', .8, 'known')", [(str(i), str(i+1)) for i in range(100)])
        statements = []
        conn.set_trace_callback(statements.append)
        graph, truncated = graph_lab.build_subgraph(max_nodes=2, conn=conn)
        assert len(graph) <= 2 and truncated
        assert any("LIMIT 21" in statement for statement in statements)
    finally:
        conn.close()
    # An acyclic graph with many candidate walks must not be searched to completion.
    dag = nx.DiGraph((a, b) for a in range(100) for b in range(a+1, min(100, a+15)))
    monkeypatch.setattr(graph_lab.time, "monotonic", lambda: 0.)
    assert graph_lab.cycles(dag) == []
    assert dag.graph["cycle_budget_exhausted"] is True


async def test_roles_route_applies_domain_and_mode_before_branching(monkeypatch):
    import server
    from core import pipeline
    from core.branch_manager import SynthesisResult
    seen = {}
    def run(query, **kwargs):
        seen.update(kwargs)
        return {"facts": [{"fact_id": "policy-eligible"}]}
    class Manager:
        async def reason(self, **kwargs):
            assert kwargs["facts"] == [{"fact_id": "policy-eligible"}]
            return SynthesisResult("answer", [], [], [], .5)
    monkeypatch.setattr(pipeline, "run", run)
    monkeypatch.setattr("core.branch_manager.get_branch_manager", Manager)
    monkeypatch.setattr(server, "_env_llm_config", lambda: None)
    result = await server.query_with_roles(server._QueryRolesRequest(query="biology", domain="biology", cognitive_mode="PRECISION"))
    assert seen == {"domain": "biology", "cognitive_mode": "PRECISION"}
    assert result.effective_params["domain"] == "biology"


def test_bounded_cycles_match_independent_networkx_oracle_on_small_graphs():
    import random
    import networkx as nx
    from core import graph_lab
    rng = random.Random(17)
    def normalize(cycle):
        return min(tuple(cycle[offset:] + cycle[:offset]) for offset in range(len(cycle)))
    for _ in range(10):
        graph = nx.DiGraph((str(a), str(b)) for a in range(4) for b in range(4) if rng.random() < .3)
        actual = {normalize(c) for c in graph_lab.cycles(graph, max_len=3, limit=100)}
        expected = {normalize(c) for c in nx.simple_cycles(graph) if len(c) <= 3}
        assert actual == expected
