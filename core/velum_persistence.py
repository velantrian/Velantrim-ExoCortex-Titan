"""
Velum Persistence + FSRS Batch Decay (Sprint 2 / T5).

Опционально сохраняет synapse в Neo4j (:VelumSynapse) для переживания
рестартов процесса. Batch job применяет FSRS decay к узлам графа.

Инвариант Velum.I4: in-memory остаётся primary; Neo4j — опциональный snapshot.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from core.decay_orchestrator import (
    DecayTarget,
    is_decay_orchestrator_enabled,
)
from core.feature_config import get_config
from core.fsrs import FSRSParams, decay_edge_weight
from core.salience_fsrs import effective_decay_weight, should_protect_from_decay
from core.velum import VelumDecayBatchResult
from core.velum_bridge import get_velum

logger = logging.getLogger(__name__)


@dataclass
class GraphVelumDecayResult:
    """Результат decay по Neo4j VelumSynapse."""

    rows_fetched: int
    rows_updated: int
    rows_deleted: int
    dry_run: bool
    avg_weight_before: float
    avg_weight_after: float


def _driver(graphiti):
    return getattr(graphiti, "driver", None) or getattr(graphiti, "_driver", None)


def is_velum_persist_enabled() -> bool:
    return bool(get_config().app.velum_persist)


async def fetch_synapse_rows(graphiti) -> list[dict[str, Any]]:
    driver = _driver(graphiti)
    if not driver:
        return []

    res = await driver.execute_query(
        """
        MATCH (s:VelumSynapse)
        RETURN s.edge_key AS edge_key,
               s.entity_a AS entity_a,
               s.entity_b AS entity_b,
               s.weight AS weight,
               s.stability_days AS stability_days,
               s.co_occur_count AS co_occur_count,
               s.last_touch AS last_touch,
               s.last_episode_id AS last_episode_id,
               s.retrieval_hits AS retrieval_hits,
               s.salience_weight AS salience_weight
        """
    )
    rows: list[dict[str, Any]] = []
    for rec in res.records or []:
        last_touch = rec.get("last_touch")
        if hasattr(last_touch, "to_native"):
            last_touch = last_touch.to_native()
        if hasattr(last_touch, "isoformat"):
            last_touch = last_touch.isoformat()
        rows.append(
            {
                "edge_key": rec.get("edge_key"),
                "entity_a": rec.get("entity_a"),
                "entity_b": rec.get("entity_b"),
                "weight": float(rec.get("weight") or 0.0),
                "stability_days": float(rec.get("stability_days") or 7.0),
                "co_occur_count": int(rec.get("co_occur_count") or 0),
                "last_touch": last_touch,
                "last_episode_id": rec.get("last_episode_id"),
                "retrieval_hits": int(rec.get("retrieval_hits") or 0),
                "salience_weight": float(rec.get("salience_weight") or 1.0),
            }
        )
    return rows


async def import_graph_to_velum(graphiti) -> int:
    """Загрузить VelumSynapse из Neo4j в process singleton."""
    rows = await fetch_synapse_rows(graphiti)
    if not rows:
        return 0
    return await get_velum().import_snapshots(rows, merge=True)


async def export_velum_to_graph(graphiti) -> int:
    """Сохранить in-memory Velum → Neo4j (MERGE по edge_key)."""
    driver = _driver(graphiti)
    if not driver:
        return 0

    snapshots = await get_velum().export_snapshots()
    if not snapshots:
        return 0

    written = 0
    for row in snapshots:
        await driver.execute_query(
            """
            MERGE (s:VelumSynapse {edge_key: $edge_key})
            SET s.entity_a = $entity_a,
                s.entity_b = $entity_b,
                s.weight = $weight,
                s.stability_days = $stability_days,
                s.co_occur_count = $co_occur_count,
                s.last_touch = $last_touch,
                s.last_episode_id = $last_episode_id,
                s.retrieval_hits = $retrieval_hits,
                s.salience_weight = $salience_weight,
                s.salience_fsrs_protected = $protected,
                s.updated_at = datetime()
            """,
            edge_key=row["edge_key"],
            entity_a=row["entity_a"],
            entity_b=row["entity_b"],
            weight=row["weight"],
            stability_days=row["stability_days"],
            co_occur_count=row["co_occur_count"],
            last_touch=row["last_touch"],
            last_episode_id=row.get("last_episode_id"),
            retrieval_hits=row.get("retrieval_hits", 0),
            salience_weight=row.get("salience_weight", 1.0),
            protected=should_protect_from_decay(
                float(row.get("salience_weight", 1.0))
            ),
        )
        written += 1
    logger.info("velum_persist: exported %d synapses to Neo4j", written)
    return written


async def run_graph_fsrs_decay(
    graphiti,
    *,
    dry_run: bool = False,
    prune_below: float | None = None,
    fsrs: FSRSParams | None = None,
) -> GraphVelumDecayResult:
    """
    FSRS decay для :VelumSynapse в Neo4j (RFC0017 batch, T5).
    """
    if fsrs is None:
        fsrs = FSRSParams()
    if prune_below is None:
        prune_below = get_config().app.velum_decay_prune_below

    now = datetime.now(UTC)
    rows = await fetch_synapse_rows(graphiti)
    if not rows:
        return GraphVelumDecayResult(
            rows_fetched=0,
            rows_updated=0,
            rows_deleted=0,
            dry_run=dry_run,
            avg_weight_before=0.0,
            avg_weight_after=0.0,
        )

    weights_before = [float(r["weight"]) for r in rows]
    updates: list[dict[str, Any]] = []
    deletes: list[str] = []
    skipped_protected = 0
    skipped_orchestrator = 0

    orchestrator = None
    if is_decay_orchestrator_enabled():
        from core.decay_orchestrator import get_decay_orchestrator

        orchestrator = get_decay_orchestrator()

    for row in rows:
        touch_raw = row.get("last_touch")
        if isinstance(touch_raw, str) and touch_raw:
            try:
                touch = datetime.fromisoformat(touch_raw.replace("Z", "+00:00"))
            except ValueError:
                touch = now
        else:
            touch = now
        if touch.tzinfo is None:
            touch = touch.replace(tzinfo=UTC)

        salience_w = float(row.get("salience_weight") or 1.0)
        t_days = max(0.0, (now - touch).total_seconds() / 86_400.0)
        old_w = float(row["weight"])
        stability = float(row.get("stability_days") or 7.0)

        if orchestrator is not None:
            outcome = orchestrator.compute(
                DecayTarget(
                    weight=old_w,
                    t_days=t_days,
                    stability_days=stability,
                    salience_weight=salience_w,
                    domain_vector=row.get("domain_vector"),
                    content_domain=row.get("content_domain"),
                    source_year=row.get("source_year"),
                    decay_lambda=row.get("decay_lambda"),
                    min_weight=0.0,
                    max_weight=1.0,
                ),
                prune_below=prune_below,
            )
            if outcome.skipped:
                skipped_orchestrator += 1
                if outcome.skip_reason == "salience_protected":
                    skipped_protected += 1
                continue
            new_w = outcome.new_weight
        else:
            if should_protect_from_decay(salience_w):
                skipped_protected += 1
                continue
            raw_new = decay_edge_weight(old_w, t_days, stability, fsrs)
            new_w = effective_decay_weight(old_w, raw_new, salience_w)
            new_w = max(0.0, min(1.0, new_w))

        edge_key = row.get("edge_key")
        if not edge_key:
            continue
        if new_w < prune_below:
            deletes.append(edge_key)
        else:
            updates.append({"edge_key": edge_key, "weight": new_w})

    weights_after = [u["weight"] for u in updates]
    avg_before = sum(weights_before) / len(weights_before)
    avg_after = (
        sum(weights_after) / len(weights_after) if weights_after else 0.0
    )

    if dry_run:
        return GraphVelumDecayResult(
            rows_fetched=len(rows),
            rows_updated=len(updates),
            rows_deleted=len(deletes),
            dry_run=True,
            avg_weight_before=avg_before,
            avg_weight_after=avg_after,
        )

    driver = _driver(graphiti)
    if not driver:
        return GraphVelumDecayResult(
            rows_fetched=len(rows),
            rows_updated=0,
            rows_deleted=0,
            dry_run=False,
            avg_weight_before=avg_before,
            avg_weight_after=avg_after,
        )

    for item in updates:
        await driver.execute_query(
            """
            MATCH (s:VelumSynapse {edge_key: $edge_key})
            SET s.weight = $weight, s.decayed_at = datetime()
            """,
            edge_key=item["edge_key"],
            weight=item["weight"],
        )

    for edge_key in deletes:
        await driver.execute_query(
            """
            MATCH (s:VelumSynapse {edge_key: $edge_key})
            DELETE s
            """,
            edge_key=edge_key,
        )

    logger.info(
        "velum graph FSRS decay: fetched=%d updated=%d deleted=%d "
        "skipped_orchestrator=%d skipped_salience=%d",
        len(rows),
        len(updates),
        len(deletes),
        skipped_orchestrator,
        skipped_protected,
    )

    return GraphVelumDecayResult(
        rows_fetched=len(rows),
        rows_updated=len(updates),
        rows_deleted=len(deletes),
        dry_run=False,
        avg_weight_before=avg_before,
        avg_weight_after=avg_after,
    )


async def run_memory_fsrs_decay(
    *,
    prune_below: float | None = None,
    run_gc: bool = True,
) -> VelumDecayBatchResult:
    """FSRS decay in-memory singleton."""
    return await get_velum().apply_fsrs_decay_all(
        prune_below=prune_below,
        run_gc=run_gc,
    )


async def run_full_decay_job(
    graphiti=None,
    *,
    memory_only: bool = False,
    dry_run: bool = False,
    sync_from_graph: bool = False,
    sync_to_graph: bool = False,
) -> dict[str, Any]:
    """
    Полный цикл T5:
      - опционально import/export Neo4j
      - decay memory и/или graph
    """
    report: dict[str, Any] = {"dry_run": dry_run, "memory_only": memory_only}

    if graphiti and sync_from_graph and not memory_only:
        report["imported"] = await import_graph_to_velum(graphiti)

    if dry_run:
        report["memory"] = {"skipped": True, "reason": "dry_run"}
    else:
        mem_result = await run_memory_fsrs_decay(
            prune_below=get_config().app.velum_decay_prune_below,
        )
        report["memory"] = {
            "edges_processed": mem_result.edges_processed,
            "edges_decayed": mem_result.edges_decayed,
            "edges_pruned": mem_result.edges_pruned,
            "gc_removed": mem_result.gc_removed,
            "avg_weight_before": mem_result.avg_weight_before,
            "avg_weight_after": mem_result.avg_weight_after,
        }

    if graphiti and not memory_only:
        graph_result = await run_graph_fsrs_decay(
            graphiti, dry_run=dry_run
        )
        report["graph"] = {
            "rows_fetched": graph_result.rows_fetched,
            "rows_updated": graph_result.rows_updated,
            "rows_deleted": graph_result.rows_deleted,
            "avg_weight_before": graph_result.avg_weight_before,
            "avg_weight_after": graph_result.avg_weight_after,
        }

    if graphiti and sync_to_graph and not dry_run and not memory_only:
        report["exported"] = await export_velum_to_graph(graphiti)

    return report


__all__ = [
    "GraphVelumDecayResult",
    "export_velum_to_graph",
    "fetch_synapse_rows",
    "import_graph_to_velum",
    "is_velum_persist_enabled",
    "run_full_decay_job",
    "run_graph_fsrs_decay",
    "run_memory_fsrs_decay",
]
