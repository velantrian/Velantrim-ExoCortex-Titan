"""Regression tests for ConsolidationEngine._refresh_checksum bug.

Before the fix, _refresh_checksum() called store.store_fact() with the
promoted fact (whose epistemic_state is no longer 'Observed'). store_fact()
unconditionally rejects non-Observed upserts with ValueError, which was caught
by the surrounding except-ValueError handler in run(), triggering an illegal
fallback demotion and ultimately incrementing report.errors — even though the
promotion itself had fully succeeded.

After the fix, _refresh_checksum() calls store.update_fact_metadata() instead,
which updates only the metadata column and leaves epistemic_state untouched.

Invariant asserted here:
  report.errors == 0   after a successful promotion (Hypothesized or Validated)
"""
from __future__ import annotations

import pytest

from core.consolidation_engine import ConsolidationEngine
from core.memory import SQLiteGraphStore


@pytest.fixture
def store(tmp_path):
    return SQLiteGraphStore(db_path=str(tmp_path / "checksum.db"))


def _basic_fact(fact_id: str, *, confidence: float = 0.9) -> dict:
    return {
        "fact_id": fact_id,
        "claim": "a normal length claim entered manually",
        "source": "manual",
        "confidence": confidence,
    }


# ── Hypothesized path (prefer_validated=False) ────────────────────────────────

def test_no_errors_after_successful_hypothesized_promotion(store):
    """report.errors must be 0 when a fact is successfully promoted to Hypothesized."""
    store.store_fact(_basic_fact("z1"))

    engine = ConsolidationEngine(store, min_confidence=0.7, prefer_validated=False)
    report = engine.run()

    assert report.errors == 0, (
        f"Expected 0 errors after successful Hypothesized promotion, got {report.errors}. "
        f"Full report: {report.to_dict()}"
    )
    assert report.promoted_hypothesized == 1
    assert store.get_fact("z1")["epistemic_state"] == "Hypothesized"


def test_checksum_metadata_updated_after_hypothesized_promotion(store):
    """After promotion, metadata must contain a content_checksum that reflects
    the new (Hypothesized) epistemic_state — not just the old Observed one."""
    store.store_fact(_basic_fact("z2"))

    engine = ConsolidationEngine(store, min_confidence=0.7, prefer_validated=False)
    engine.run()

    fact = store.get_fact("z2")
    assert fact["epistemic_state"] == "Hypothesized"
    # attach_integrity_metadata always sets content_checksum
    assert "content_checksum" in fact.get("metadata", {}), (
        "content_checksum missing from metadata after _refresh_checksum"
    )


# ── Accounting invariant ──────────────────────────────────────────────────────

def test_accounting_invariant_hypothesized(store):
    """scanned == promoted_hypothesized + skipped + errors (no truthgate path)."""
    store.store_fact(_basic_fact("a1"))
    store.store_fact(_basic_fact("a2", confidence=0.3))  # below min_confidence → skipped

    engine = ConsolidationEngine(store, min_confidence=0.7, prefer_validated=False)
    report = engine.run()

    d = report.to_dict()
    total = (
        d["promoted_hypothesized"]
        + d["promoted_validated"]
        + d["skipped_low_confidence"]
        + d["skipped_short_claim"]
        + d["errors"]
        + d.get("rejected_by_truthgate", 0)
    )
    assert total == d["scanned"], (
        f"Accounting mismatch: scanned={d['scanned']}, sum of buckets={total}. "
        f"Full report: {d}"
    )
    assert d["errors"] == 0


# ── update_fact_metadata unit test ────────────────────────────────────────────

def test_update_fact_metadata_does_not_change_epistemic_state(store):
    """SQLiteGraphStore.update_fact_metadata() must leave epistemic_state intact."""
    store.store_fact(_basic_fact("m1"))
    store.transition_esm("m1", "Hypothesized", by="test")

    fact_before = store.get_fact("m1")
    assert fact_before["epistemic_state"] == "Hypothesized"

    new_meta = {**fact_before.get("metadata", {}), "test_key": "test_value"}
    updated = store.update_fact_metadata("m1", new_meta)

    assert updated is True
    fact_after = store.get_fact("m1")
    assert fact_after["epistemic_state"] == "Hypothesized", (
        "update_fact_metadata must not change epistemic_state"
    )
    assert fact_after["metadata"]["test_key"] == "test_value"


def test_update_fact_metadata_returns_false_for_missing_fact(store):
    """update_fact_metadata on a non-existent fact_id must return False."""
    result = store.update_fact_metadata("nonexistent", {"foo": "bar"})
    assert result is False
