"""
core/graph_lab.py — NetworkX Graph-Analysis Lab (read-only analytics over the causal graph).

The causal store (core/causal_graph.py, SQLite `relations` table) does traversals
(chains, contradictions, counterfactual) but NOT structural analytics. This lab loads a
*subgraph* of `relations` into a networkx.DiGraph and computes centrality / communities /
cycles / PageRank — the things NetworkX is built for.

Hard constraints (canon — analysis ≠ truth):
  • PASSIVE: reads `relations` with SELECT only; never writes facts/relations, never
    changes truth_status, never promotes anything.
  • Gracefully disabled when networkx is absent (mirrors DenseRetriever._AVAILABLE):
    every entry point returns {"available": False, ...} and NEVER raises.
  • In-RAM: a max_nodes guard bounds memory; truncation is reported, never silent.

Increment 1 algorithms: centrality (degree+betweenness), communities
(greedy_modularity), cycles (simple_cycles), PageRank. Deferred: articulation points,
prereq DAG ordering, contradiction-spread, wiring into cross_domain/salience.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MAX_NODES = 2000
_DEFAULT_MAX_CYCLE_LEN = 6


class _NX:
    """Lazy networkx import guard (graceful degradation pattern)."""

    _available: bool | None = None
    _mod = None

    @classmethod
    def get(cls):
        if cls._available is None:
            try:
                import networkx as nx  # noqa: WPS433
                cls._mod = nx
                cls._available = True
            except Exception as exc:  # noqa: BLE001
                cls._available = False
                logger.info("graph_lab: networkx unavailable (%s) — lab disabled", exc)
        return cls._mod if cls._available else None


def is_available() -> bool:
    return _NX.get() is not None


# ── subgraph loader (read-only over the `relations` table) ──────────────────────

def _store_conn() -> sqlite3.Connection | None:
    """Open an owned read-only connection; analytics never initializes a writer."""
    try:
        import core.memory as memory
        path = getattr(memory._GLOBAL_STORE, "db_path", None)
        if path:
            return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    except Exception as exc:
        logger.debug("graph_lab: read connection unavailable (%s)", type(exc).__name__)
    return None


def build_subgraph(
    seed_fact_ids: Sequence[str] | None = None,
    *,
    max_nodes: int = _DEFAULT_MAX_NODES,
    conn: sqlite3.Connection | None = None,
):
    """Build a networkx.DiGraph from the `relations` table. Returns (graph, truncated).

    Edges carry `type`, `confidence`, `knowledge_status`. When seed_fact_ids is given,
    only relations touching a seed node are loaded (1-hop). Read-only; never raises on
    a missing table — returns an empty graph instead.
    """
    nx = _NX.get()
    if nx is None:
        return None, False
    c = conn or _store_conn()
    if c is None:
        g = nx.DiGraph()
        g.graph["read_error"] = "store_read_unavailable"
        return g, False

    g = nx.DiGraph()
    truncated = False
    if not isinstance(max_nodes, int) or not 1 <= max_nodes <= _DEFAULT_MAX_NODES:
        if conn is None:
            c.close()
        g.graph["read_error"] = "invalid_graph_budget"
        return g, False
    seeds = list(dict.fromkeys(seed_fact_ids or []))
    if len(seeds) > max_nodes:
        seeds = seeds[:max_nodes]
        truncated = True
    edge_budget = max_nodes * 10
    params: list[Any] = []
    where = ""
    if seeds:
        marks = ",".join("?" for _ in seeds)
        where = f" WHERE from_fact_id IN ({marks}) OR to_fact_id IN ({marks})"
        params.extend(seeds + seeds)
    try:
        cursor = c.execute(
            "SELECT from_fact_id, to_fact_id, relation_type, confidence, knowledge_status "
            "FROM relations" + where + " LIMIT ?", (*params, edge_budget + 1),
        )
        for index, (src, dst, rtype, conf, kstatus) in enumerate(cursor):
            if index >= edge_budget:
                truncated = True
                break
            if g.number_of_nodes() + sum(node not in g for node in {src, dst}) > max_nodes:
                truncated = True
                continue
            g.add_edge(src, dst, type=rtype,
                       confidence=float(conf if conf is not None else 0.0),
                       knowledge_status=kstatus)
    except Exception as exc:
        logger.debug("graph_lab: relations read unavailable (%s)", type(exc).__name__)
        g.graph["read_error"] = "relations_read_unavailable"
    finally:
        if conn is None:
            c.close()
    return g, truncated


# ── analyses (each returns plain JSON-ready data) ───────────────────────────────

def centrality(g, top_k: int = 20) -> list[dict[str, Any]]:
    nx = _NX.get()
    if nx is None or g is None or g.number_of_nodes() == 0:
        return []
    deg = nx.degree_centrality(g)
    try:
        btw = nx.betweenness_centrality(g)
    except Exception:  # noqa: BLE001
        btw = {n: 0.0 for n in g.nodes}
    ranked = sorted(g.nodes, key=lambda n: (deg.get(n, 0.0), btw.get(n, 0.0)), reverse=True)
    return [
        {"fact_id": n, "degree": round(deg.get(n, 0.0), 4), "betweenness": round(btw.get(n, 0.0), 4)}
        for n in ranked[:top_k]
    ]


def communities(g) -> list[list[str]]:
    nx = _NX.get()
    if nx is None or g is None or g.number_of_nodes() == 0:
        return []
    try:
        from networkx.algorithms.community import greedy_modularity_communities

        comms = greedy_modularity_communities(g.to_undirected())
        return [sorted(map(str, c)) for c in comms]
    except Exception as exc:  # noqa: BLE001
        logger.debug("graph_lab: communities failed (%s)", exc)
        return []


def cycles(g, max_len: int = _DEFAULT_MAX_CYCLE_LEN, limit: int = 50) -> list[list[str]]:
    """Enumerate short directed cycles under a node-expansion and time budget.

    Canonical start ordering avoids rotated copies. Budget exhaustion is explicit
    in graph metadata; an empty bounded result is not proof of acyclicity.
    """
    if g is None or not g or max_len < 1 or limit < 1:
        return []
    out: list[list[str]] = []
    order = {node: index for index, node in enumerate(g.nodes)}
    steps = 0
    deadline = time.monotonic() + .25
    g.graph["cycle_budget_exhausted"] = False
    for start in g.nodes:
        path = [start]
        seen = {start}
        stack = [iter(g.successors(start))]
        while stack:
            steps += 1
            if steps > 10000 or time.monotonic() >= deadline:
                g.graph["cycle_budget_exhausted"] = True
                return out
            neighbor = next(stack[-1], None)
            if neighbor is None:
                stack.pop()
                seen.remove(path.pop())
            elif neighbor == start:
                out.append([str(node) for node in path])
                if len(out) >= limit:
                    g.graph["cycle_budget_exhausted"] = True
                    return out
            elif len(path) < min(max_len, _DEFAULT_MAX_CYCLE_LEN) and neighbor not in seen and order[neighbor] >= order[start]:
                path.append(neighbor)
                seen.add(neighbor)
                stack.append(iter(g.successors(neighbor)))
    return out


def pagerank(g, top_k: int = 20) -> list[dict[str, Any]]:
    nx = _NX.get()
    if nx is None or g is None or g.number_of_nodes() == 0:
        return []
    try:
        pr = nx.pagerank(g, weight="confidence")
    except Exception as exc:  # noqa: BLE001 — numpy/scipy may be absent
        logger.debug("graph_lab: pagerank failed (%s), fallback degree_centrality", exc)
        try:
            pr = nx.degree_centrality(g)
            total = sum(pr.values()) or 1.0
            pr = {k: v / total for k, v in pr.items()}
        except Exception as exc2:  # noqa: BLE001
            logger.debug("graph_lab: degree_centrality failed (%s)", exc2)
            return []
    ranked = sorted(pr.items(), key=lambda kv: kv[1], reverse=True)
    return [{"fact_id": n, "pagerank": round(s, 5)} for n, s in ranked[:top_k]]


# ── path-finding (increment 2: causal "why-path" between facts) ─────────────────
# Read-only routes over the same DiGraph. Distinct from similarity search: these answer
# "how does A lead to B" and "what reaches / flows from this fact". Path queries need the
# broader graph (multi-hop), so they build with seed_fact_ids=None, bounded by max_nodes.

def _edges_for_path(g, path: list[str]) -> list[dict[str, Any]]:
    """Annotate consecutive path nodes with their edge metadata."""
    edges: list[dict[str, Any]] = []
    for a, b in zip(path, path[1:]):
        data = g.get_edge_data(a, b) or {}
        edges.append({
            "from": a, "to": b,
            "type": data.get("type"),
            "confidence": data.get("confidence"),
        })
    return edges


def shortest_why_path(
    src: str,
    dst: str,
    *,
    max_nodes: int = _DEFAULT_MAX_NODES,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Shortest causal route src→dst. Returns {found, path, edges, length}. Never raises."""
    nx = _NX.get()
    if nx is None:
        return {"found": False, "reason": "networkx_not_installed"}
    g, truncated = build_subgraph(None, max_nodes=max_nodes, conn=conn)
    if g is None or not g.has_node(src) or not g.has_node(dst):
        return {"found": False, "reason": "node_not_in_graph", "truncated": truncated}
    try:
        path = nx.shortest_path(g, src, dst)
    except Exception as exc:  # noqa: BLE001 — NetworkXNoPath / NodeNotFound
        return {"found": False, "reason": "no_path", "detail": str(exc), "truncated": truncated}
    return {
        "found": True,
        "path": [str(n) for n in path],
        "edges": _edges_for_path(g, path),
        "length": len(path) - 1,
        "truncated": truncated,
    }


def all_paths(
    src: str,
    dst: str,
    *,
    cutoff: int = 5,
    limit: int = 20,
    max_nodes: int = _DEFAULT_MAX_NODES,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Up to `limit` simple paths src→dst with length ≤ cutoff. Bounded; never raises."""
    nx = _NX.get()
    if nx is None:
        return {"found": False, "reason": "networkx_not_installed"}
    g, truncated = build_subgraph(None, max_nodes=max_nodes, conn=conn)
    if g is None or not g.has_node(src) or not g.has_node(dst):
        return {"found": False, "reason": "node_not_in_graph", "paths": [], "truncated": truncated}
    paths: list[list[str]] = []
    capped = False
    try:
        for p in nx.all_simple_paths(g, src, dst, cutoff=cutoff):
            paths.append([str(n) for n in p])
            if len(paths) >= limit:
                capped = True
                break
    except Exception as exc:  # noqa: BLE001
        logger.debug("graph_lab: all_paths failed (%s)", exc)
    return {
        "found": bool(paths),
        "paths": paths,
        "count": len(paths),
        "capped": capped,
        "truncated": truncated,
    }


def reaches(
    fact_id: str,
    *,
    direction: str = "to",
    limit: int = 50,
    max_nodes: int = _DEFAULT_MAX_NODES,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Facts that lead to (direction='to' → ancestors) or flow from (direction='from' →
    descendants) the given fact, each with hop-distance. Never raises."""
    nx = _NX.get()
    if nx is None:
        return {"available": False, "reason": "networkx_not_installed", "nodes": []}
    g, truncated = build_subgraph(None, max_nodes=max_nodes, conn=conn)
    if g is None or not g.has_node(fact_id):
        return {"available": True, "found": False, "reason": "node_not_in_graph",
                "nodes": [], "truncated": truncated}
    try:
        if direction == "from":
            reachable = nx.descendants(g, fact_id)
            dist = nx.single_source_shortest_path_length(g, fact_id)
        else:
            reachable = nx.ancestors(g, fact_id)
            dist = nx.single_source_shortest_path_length(g.reverse(copy=False), fact_id)
    except Exception as exc:  # noqa: BLE001
        logger.debug("graph_lab: reaches failed (%s)", exc)
        return {"available": True, "found": False, "reason": "error", "nodes": []}
    nodes = sorted(
        ({"fact_id": str(n), "hops": dist.get(n)} for n in reachable),
        key=lambda d: (d["hops"] if d["hops"] is not None else 1 << 30, d["fact_id"]),
    )
    return {
        "available": True,
        "found": bool(nodes),
        "direction": direction,
        "nodes": nodes[:limit],
        "count": len(nodes),
        "truncated": truncated,
    }


def analyze(
    seed_fact_ids: Sequence[str] | None = None,
    *,
    top_k: int = 20,
    max_nodes: int = _DEFAULT_MAX_NODES,
    conn: sqlite3.Connection | None = None,
    max_cycle_len: int = _DEFAULT_MAX_CYCLE_LEN,
) -> dict[str, Any]:
    """One-shot structural report over the causal subgraph. Never raises."""
    if not is_available():
        return {"available": False, "reason": "networkx_not_installed"}
    g, truncated = build_subgraph(seed_fact_ids, max_nodes=max_nodes, conn=conn)
    if g is None:
        return {"available": False, "reason": "networkx_not_installed"}
    if g.graph.get("read_error"):
        return {"available": False, "reason": g.graph["read_error"]}
    cycle_list = cycles(g, max_len=max_cycle_len)
    return {
        "available": True,
        "node_count": g.number_of_nodes(),
        "edge_count": g.number_of_edges(),
        "truncated": truncated,
        "centrality": centrality(g, top_k=top_k),
        "communities": communities(g),
        "cycles": cycle_list,
        "cycle_budget_exhausted": g.graph.get("cycle_budget_exhausted", False),
        "pagerank": pagerank(g, top_k=top_k),
    }


__all__ = [
    "is_available",
    "build_subgraph",
    "centrality",
    "communities",
    "cycles",
    "pagerank",
    "shortest_why_path",
    "all_paths",
    "reaches",
    "analyze",
]
