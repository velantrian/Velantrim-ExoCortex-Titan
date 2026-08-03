from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from core.memory import SQLiteGraphStore


def _promotion_evidence(db_path: Path, fact_id: str) -> tuple[int, int]:
    """Return fact-version and Validated-transition audit counts."""
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        conn.row_factory = sqlite3.Row
        version_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )
        subject_row = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()
        assert subject_row is not None
        audit_subject_id = subject_row[0]
        assert audit_subject_id
        chain_id = f"fact-transition:{audit_subject_id}"
        validated_event_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM memory_events "
                "WHERE chain_id = ? AND to_state = 'Validated'",
                (chain_id,),
            ).fetchone()[0]
        )
    return version_count, validated_event_count


def _gate_cas_at_shared_snapshot(
    store: SQLiteGraphStore,
    barrier: threading.Barrier,
) -> None:
    """Hold both writers immediately before their real conditional UPDATE."""
    original = store._promote_to_validated_cas

    def gated(*args: Any, **kwargs: Any) -> bool:
        barrier.wait(timeout=10)
        return original(*args, **kwargs)

    store._promote_to_validated_cas = gated  # type: ignore[method-assign]


def test_two_valid_promotions_have_one_cas_winner_and_one_explicit_loser(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "promotion-cas-contention.db"
    fact_id = "cas-contention-fact"

    bootstrap = SQLiteGraphStore(str(db_path))
    try:
        created = bootstrap.store_fact(
            {
                "fact_id": fact_id,
                "claim": "A well-evidenced fact for deterministic CAS contention",
                "source": "manual",
                "confidence": 0.95,
                "metadata": {"evidence_refs": ["source-a", "source-b"]},
            }
        )
        assert created is True
        assert bootstrap.promote_esm_to(
            fact_id,
            "Supported",
            by="cas_test_setup",
        )
    finally:
        bootstrap.close()

    versions_before, validated_events_before = _promotion_evidence(db_path, fact_id)
    assert validated_events_before == 0

    writer_a = SQLiteGraphStore(str(db_path))
    writer_b = SQLiteGraphStore(str(db_path))
    observer = SQLiteGraphStore(str(db_path))
    barrier = threading.Barrier(2, timeout=10)
    _gate_cas_at_shared_snapshot(writer_a, barrier)
    _gate_cas_at_shared_snapshot(writer_b, barrier)

    def promote(store: SQLiteGraphStore, actor: str):
        return store.validate_and_promote(fact_id, by=actor)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(promote, writer_a, "cas_writer_a"),
                executor.submit(promote, writer_b, "cas_writer_b"),
            ]
            verdicts = [future.result(timeout=15) for future in futures]

        winners = [verdict for verdict in verdicts if verdict.passed]
        losers = [verdict for verdict in verdicts if not verdict.passed]
        assert len(winners) == 1, [(v.passed, v.reason, v.by) for v in verdicts]
        assert len(losers) == 1, [(v.passed, v.reason, v.by) for v in verdicts]
        assert winners[0].reason == "passed"
        assert losers[0].reason == "concurrent_modification"

        final_fact = observer.get_fact(fact_id)
        assert final_fact is not None
        assert final_fact["epistemic_state"] == "Validated"
        validated_history = [
            entry
            for entry in final_fact.get("history", [])
            if entry.get("state") == "Validated"
        ]
        assert len(validated_history) == 1
    finally:
        writer_a.close()
        writer_b.close()
        observer.close()

    versions_after, validated_events_after = _promotion_evidence(db_path, fact_id)
    assert versions_after == versions_before + 1
    assert validated_events_after == validated_events_before + 1

    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert int(
            conn.execute(
                "SELECT COUNT(*) FROM facts WHERE fact_id = ? "
                "AND epistemic_state = 'Validated'",
                (fact_id,),
            ).fetchone()[0]
        ) == 1
