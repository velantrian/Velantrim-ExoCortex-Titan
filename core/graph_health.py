"""Bounded read-only topology diagnostics for Titan's canonical causal graph.

This module extends, but does not replace, ``CausalGraph.integrity_report()``.
It deliberately owns no graph mutation, repair, truth, evidence, Canon, policy or
admission authority.  The existing integrity report remains the base structural
health signal; this module adds topology observations that were missing from it:

- high total-degree hubs;
- high outgoing fan-out;
- disconnected non-trivial components;
- small structural islands (a conservative proxy for topology dead zones).

The report never changes relation weights or epistemic state and never auto-repairs
anything.  Thresholds are explicit inputs so a future benchmark can calibrate them
without silently changing truth or retrieval semantics.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.causal_graph import CausalGraph


@dataclass(frozen=True)
class GraphHealthThresholds:
    """Operator-visible topology thresholds; diagnostic only."""

    hub_total_degree: int = 64
    fan_out_degree: int = 32
    small_component_max_nodes: int = 3

    def __post_init__(self) -> None:
        if self.hub_total_degree < 1:
            raise ValueError("hub_total_degree must be >= 1")
        if self.fan_out_degree < 1:
            raise ValueError("fan_out_degree must be >= 1")
        if self.small_component_max_nodes < 1:
            raise ValueError("small_component_max_nodes must be >= 1")


DEFAULT_THRESHOLDS = GraphHealthThresholds()


def _active_fact_ids(graph: "CausalGraph") -> list[str]:
    rows = graph._conn.execute(  # noqa: SLF001 - bounded diagnostic over canonical owner
        """
        SELECT fact_id
        FROM facts
        WHERE epistemic_state != 'Collapsed'
        ORDER BY fact_id
        """
    ).fetchall()
    return [str(row[0]) for row in rows]


def _relation_pairs(
    graph: "CausalGraph",
    *,
    only_approved: bool,
) -> list[tuple[str, str]]:
    sql = "SELECT from_fact_id, to_fact_id FROM relations"
    if only_approved:
        sql += " WHERE review_state = 'approved'"
    sql += " ORDER BY from_fact_id, to_fact_id"
    rows = graph._conn.execute(sql).fetchall()  # noqa: SLF001
    return [(str(row[0]), str(row[1])) for row in rows]


def _components(
    fact_ids: list[str],
    adjacency: dict[str, set[str]],
) -> list[list[str]]:
    remaining = set(fact_ids)
    components: list[list[str]] = []
    while remaining:
        start = min(remaining)
        queue: deque[str] = deque([start])
        remaining.remove(start)
        component: list[str] = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(adjacency.get(current, set())):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda item: (-len(item), item))


def topology_report(
    graph: "CausalGraph",
    *,
    thresholds: GraphHealthThresholds = DEFAULT_THRESHOLDS,
    only_approved: bool = True,
    sample_limit: int = 20,
) -> dict:
    """Return deterministic read-only topology diagnostics.

    ``only_approved=True`` is the conservative default: pending/hypothetical
    relations are not allowed to make the canonical topology look healthier.
    The result is diagnostic metadata only; it is not evidence and does not
    alter ``CausalGraph.integrity_report().integrity_score``.
    """

    sample_limit = max(1, int(sample_limit))
    fact_ids = _active_fact_ids(graph)
    fact_set = set(fact_ids)
    pairs = _relation_pairs(graph, only_approved=only_approved)

    adjacency: dict[str, set[str]] = defaultdict(set)
    out_neighbors: dict[str, set[str]] = defaultdict(set)
    for source, target in pairs:
        if source not in fact_set or target not in fact_set:
            continue
        adjacency[source].add(target)
        adjacency[target].add(source)
        out_neighbors[source].add(target)

    total_degree = {fact_id: len(adjacency.get(fact_id, set())) for fact_id in fact_ids}
    fan_out = {fact_id: len(out_neighbors.get(fact_id, set())) for fact_id in fact_ids}

    hubs = sorted(
        (
            {"fact_id": fact_id, "degree": degree}
            for fact_id, degree in total_degree.items()
            if degree > thresholds.hub_total_degree
        ),
        key=lambda row: (-row["degree"], row["fact_id"]),
    )
    fan_out_anomalies = sorted(
        (
            {"fact_id": fact_id, "fan_out": degree}
            for fact_id, degree in fan_out.items()
            if degree > thresholds.fan_out_degree
        ),
        key=lambda row: (-row["fan_out"], row["fact_id"]),
    )

    components = _components(fact_ids, adjacency)
    nontrivial = [component for component in components if len(component) > 1]
    disconnected_nontrivial = max(0, len(nontrivial) - 1)
    small_islands = [
        component
        for component in nontrivial
        if len(component) <= thresholds.small_component_max_nodes
    ]

    largest_component_size = len(components[0]) if components else 0
    connected_fraction = (
        largest_component_size / len(fact_ids)
        if fact_ids
        else 1.0
    )

    attention_reasons: list[str] = []
    if hubs:
        attention_reasons.append("hub_degree_threshold_exceeded")
    if fan_out_anomalies:
        attention_reasons.append("fan_out_threshold_exceeded")
    if disconnected_nontrivial > 0:
        attention_reasons.append("disconnected_nontrivial_components")
    if small_islands:
        attention_reasons.append("small_structural_islands")

    return {
        "version": "graph-health-v1",
        "diagnostic_only": True,
        "only_approved_relations": bool(only_approved),
        "thresholds": asdict(thresholds),
        "active_fact_count": len(fact_ids),
        "approved_relation_rows": len(pairs),
        "hub_count": len(hubs),
        "fan_out_anomaly_count": len(fan_out_anomalies),
        "component_count": len(components),
        "nontrivial_component_count": len(nontrivial),
        "disconnected_nontrivial_components": disconnected_nontrivial,
        "largest_component_size": largest_component_size,
        "largest_component_fraction": round(connected_fraction, 4),
        "small_structural_island_count": len(small_islands),
        "hub_samples": hubs[:sample_limit],
        "fan_out_samples": fan_out_anomalies[:sample_limit],
        "small_island_samples": small_islands[:sample_limit],
        "attention_required": bool(attention_reasons),
        "attention_reasons": attention_reasons,
        "note": (
            "Topology observations are diagnostic only. Small structural islands are "
            "not proof of retrieval dead zones, and degree is not evidence/truth."
        ),
    }


def extended_integrity_report(
    graph: "CausalGraph",
    *,
    thresholds: GraphHealthThresholds = DEFAULT_THRESHOLDS,
    only_approved: bool = True,
    sample_limit: int = 20,
) -> dict:
    """Compose the existing integrity report with additive topology diagnostics."""

    base = dict(graph.integrity_report())
    base["topology"] = topology_report(
        graph,
        thresholds=thresholds,
        only_approved=only_approved,
        sample_limit=sample_limit,
    )
    return base


__all__ = [
    "DEFAULT_THRESHOLDS",
    "GraphHealthThresholds",
    "extended_integrity_report",
    "topology_report",
]
