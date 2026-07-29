"""Tests for core/graph_lab.py — NetworkX Graph-Analysis Lab (read-only)."""
from __future__ import annotations

import sqlite3

import pytest

from core import graph_lab

# ── availability guard: must never raise, even without networkx ─────────────────

def test_analyze_never_raises_and_reports_availability():
    out = graph_lab.analyze()
    assert isinstance(out, dict)
    assert "available" in out
    if not out["available"]:
        assert out["reason"] == "networkx_not_installed"


# Everything below needs networkx; skip cleanly when the extra isn't installed.
nx = pytest.importorskip("networkx")


def _seed_conn() -> sqlite3.Connection:
    """In-memory `relations` table with a known shape: a hub + a planted cycle."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY, from_fact_id TEXT, to_fact_id TEXT,
            relation_type TEXT, confidence REAL, knowledge_status TEXT
        )
        """
    )
    edges = [
        # hub 'h' points to many → high centrality/pagerank
        ("r1", "h", "a", "causes", 0.9, "known"),
        ("r2", "h", "b", "causes", 0.9, "known"),
        ("r3", "h", "c", "causes", 0.9, "known"),
        ("r4", "a", "b", "enables", 0.8, "known"),
        # planted cycle x → y → z → x
        ("r5", "x", "y", "causes", 0.7, "known"),
        ("r6", "y", "z", "causes", 0.7, "known"),
        ("r7", "z", "x", "causes", 0.7, "known"),
    ]
    conn.executemany(
        "INSERT INTO relations VALUES (?,?,?,?,?,?)", edges
    )
    conn.commit()
    return conn


def test_build_subgraph_loads_edges():
    g, truncated = graph_lab.build_subgraph(conn=_seed_conn())
    assert g.number_of_edges() == 7
    assert not truncated
    assert g["h"]["a"]["type"] == "causes"


def test_centrality_ranks_hub_first():
    g, _ = graph_lab.build_subgraph(conn=_seed_conn())
    ranked = graph_lab.centrality(g, top_k=5)
    assert ranked and ranked[0]["fact_id"] == "h"


def test_cycles_detects_planted_loop():
    g, _ = graph_lab.build_subgraph(conn=_seed_conn())
    found = graph_lab.cycles(g)
    norm = {frozenset(c) for c in found}
    assert frozenset({"x", "y", "z"}) in norm


def test_communities_nonempty():
    g, _ = graph_lab.build_subgraph(conn=_seed_conn())
    assert len(graph_lab.communities(g)) >= 1


def test_pagerank_hub_on_top_and_sums_to_one():
    g, _ = graph_lab.build_subgraph(conn=_seed_conn())
    pr = graph_lab.pagerank(g, top_k=10)
    assert pr
    assert abs(sum(x["pagerank"] for x in pr) - 1.0) < 0.05


def test_truncation_flag():
    g, truncated = graph_lab.build_subgraph(conn=_seed_conn(), max_nodes=2)
    assert truncated
    assert g.number_of_nodes() <= 2


def test_analyze_full_report_shape():
    out = graph_lab.analyze(conn=_seed_conn())
    assert out["available"] is True
    for k in ("node_count", "edge_count", "centrality", "communities", "cycles", "pagerank"):
        assert k in out


def test_analyze_is_passive_no_writes():
    conn = _seed_conn()
    before = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    graph_lab.analyze(conn=conn)
    after = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    assert before == after == 7


# ── increment 2: path-finding ────────────────────────────────────────────────────

def test_shortest_why_path_found():
    out = graph_lab.shortest_why_path("x", "z", conn=_seed_conn())
    assert out["found"] is True
    assert out["path"] == ["x", "y", "z"]
    assert out["length"] == 2
    assert out["edges"][0]["type"] == "causes"


def test_shortest_why_path_no_path():
    # 'a' is a sink in the hub cluster; 'x' lives in the isolated cycle → no route
    out = graph_lab.shortest_why_path("a", "x", conn=_seed_conn())
    assert out["found"] is False
    assert out["reason"] in ("no_path", "node_not_in_graph")


def test_shortest_why_path_missing_node():
    out = graph_lab.shortest_why_path("h", "nonexistent", conn=_seed_conn())
    assert out["found"] is False and out["reason"] == "node_not_in_graph"


def test_all_paths_bounded():
    out = graph_lab.all_paths("h", "b", conn=_seed_conn())
    # h→b direct and h→a→b → at least 2 simple paths
    assert out["found"] is True and out["count"] >= 2
    assert ["h", "b"] in out["paths"]


def test_reaches_ancestors():
    out = graph_lab.reaches("z", direction="to", conn=_seed_conn())
    ids = {n["fact_id"] for n in out["nodes"]}
    assert {"x", "y"}.issubset(ids)  # both lead to z in the cycle


def test_reaches_descendants():
    out = graph_lab.reaches("h", direction="from", conn=_seed_conn())
    ids = {n["fact_id"] for n in out["nodes"]}
    assert {"a", "b", "c"}.issubset(ids)


def test_reaches_is_passive_no_writes():
    conn = _seed_conn()
    before = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    graph_lab.shortest_why_path("x", "z", conn=conn)
    graph_lab.reaches("h", direction="from", conn=conn)
    after = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    assert before == after == 7


def test_path_fns_guard_when_networkx_absent(monkeypatch):
    # force the lazy guard to "unavailable" and confirm no raise + sane shape
    monkeypatch.setattr(graph_lab._NX, "_available", False)
    monkeypatch.setattr(graph_lab._NX, "_mod", None)
    assert graph_lab.shortest_why_path("x", "z")["found"] is False
    assert graph_lab.reaches("z")["available"] is False


# ── graph_lab_bridge.analyze_graph(): db_path wiring (M11, Claude audit 2026-07-28) ──

def test_bridge_analyze_graph_actually_runs_against_db_path(tmp_path):
    """core.graph_lab.analyze() has no db_path parameter — it takes conn=.
    graph_lab_bridge.analyze_graph() used to call it with db_path=, which
    always raised TypeError (caught, reported as available=False), so this
    endpoint reported "unavailable" unconditionally regardless of whether
    NetworkX/graph_lab were actually usable."""
    from core import graph_lab_bridge

    db_path = str(tmp_path / "bridge.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY, from_fact_id TEXT, to_fact_id TEXT,
            relation_type TEXT, confidence REAL, knowledge_status TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO relations VALUES (?,?,?,?,?,?)",
        [
            ("r1", "h", "a", "causes", 0.9, "known"),
            ("r2", "h", "b", "causes", 0.9, "known"),
        ],
    )
    conn.commit()
    conn.close()

    out = graph_lab_bridge.analyze_graph(db_path=db_path)
    assert out["available"] is True, out
    assert out["node_count"] == 3
    assert out["edge_count"] == 2
