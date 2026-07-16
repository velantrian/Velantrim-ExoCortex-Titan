"""Regression tests for issue #26 (ConsolidationEngine._refresh_checksum
false error accounting) and its PR #27 fix.

Root cause: the old _refresh_checksum() called store.store_fact() with a
fact whose epistemic_state was already promoted past 'Observed'.
store_fact() unconditionally rejects any non-Observed upsert with
ValueError, and that call used to run INSIDE run()'s promotion
try/except — so a fully successful promotion could still be misread as
a failed one, incrementing report.errors and even triggering a bogus
Hypothesized fallback transition on an already-promoted fact.

The fix has three independent parts, each covered below:
  1. core/memory.py: SQLiteGraphStore.refresh_fact_integrity_metadata() —
     a narrow, atomic, CAS-guarded metadata-only write that never touches
     epistemic_state and proves existence via SELECT, never via UPDATE
     rowcount.
  2. core/consolidation_engine.py: promotion (_promote_one) and checksum
     maintenance (_refresh_checksum_after_promotion) are now two
     structurally separate steps — a checksum-refresh failure can only
     ever increment report.checksum_refresh_errors, never report.errors,
     and can never undo or re-attempt the promotion.
  3. core/consolidation_engine.py: report.scanned now always equals
     len(batch) (the actually-processed slice), with report.discovered
     tracking the pre-truncation candidate count — restoring the
     invariant scanned == sum(every mutually exclusive outcome bucket).
"""
from __future__ import annotations

import pytest

from core.consolidation_engine import ConsolidationEngine
from core.fact_integrity import compute_content_checksum
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


def _trusted_fact(fact_id: str, *, evidence_refs: list[str]) -> dict:
    return {
        "fact_id": fact_id,
        "claim": "a normal length claim entered manually",
        "source": "manual",
        "confidence": 0.9,
        "metadata": {"evidence_refs": evidence_refs},
    }


def _accounting_total(d: dict) -> int:
    return (
        d["promoted_hypothesized"]
        + d["promoted_validated"]
        + d["skipped_low_confidence"]
        + d["skipped_short_claim"]
        + d["errors"]
        + d["rejected_by_truthgate"]
    )


# ── A. Hypothesized happy path ────────────────────────────────────────────────

def test_hypothesized_happy_path(store):
    store.store_fact(_basic_fact("a1"))

    engine = ConsolidationEngine(store, min_confidence=0.7, prefer_validated=False)
    report = engine.run()

    assert report.errors == 0
    assert report.checksum_refresh_errors == 0
    assert report.promoted_hypothesized == 1
    assert report.fact_ids.count("a1") == 1

    fact = store.get_fact("a1")
    assert fact["epistemic_state"] == "Hypothesized"
    assert fact["metadata"]["content_checksum"] == compute_content_checksum(
        fact["claim"], fact["source"], fact["confidence"], "Hypothesized"
    )


# ── B. Validated happy path (real production path, no shortcuts) ─────────────

def test_validated_happy_path_via_real_truthgate(store, monkeypatch):
    store.store_fact(_trusted_fact("b1", evidence_refs=["src1", "src2"]))

    real_transition_esm = store.transition_esm

    def _guarded_transition_esm(fact_id, new_state, by="transition_esm"):
        assert new_state != "Validated", (
            "Validated must be reached only via validate_and_promote(), "
            "never a direct transition_esm() call"
        )
        return real_transition_esm(fact_id, new_state, by=by)

    monkeypatch.setattr(store, "transition_esm", _guarded_transition_esm)

    engine = ConsolidationEngine(store, min_confidence=0.7)
    report = engine.run()

    assert report.errors == 0
    assert report.checksum_refresh_errors == 0
    assert report.promoted_validated == 1
    assert report.fact_ids.count("b1") == 1

    fact = store.get_fact("b1")
    assert fact["epistemic_state"] == "Validated"
    assert fact["metadata"]["content_checksum"] == compute_content_checksum(
        fact["claim"], fact["source"], fact["confidence"], "Validated"
    )
    assert fact["metadata"]["evidence_refs"] == ["src1", "src2"]


# ── C. Genuine metadata no-op ─────────────────────────────────────────────────

def test_refresh_is_idempotent_true_noop(store):
    store.store_fact(_basic_fact("c1"))
    store.transition_esm("c1", "Hypothesized", by="test")

    first = store.refresh_fact_integrity_metadata("c1")
    assert first == "success"
    fact_after_first = store.get_fact("c1")

    second = store.refresh_fact_integrity_metadata("c1")
    assert second == "success", "a true no-op must still be 'success', never 'not_found'"

    fact_after_second = store.get_fact("c1")
    assert fact_after_second["metadata"] == fact_after_first["metadata"]
    assert fact_after_second["epistemic_state"] == "Hypothesized"
    assert fact_after_second["history"] == fact_after_first["history"]


# ── D. Missing fact ───────────────────────────────────────────────────────────

def test_refresh_missing_fact_returns_not_found_without_creating_it(store):
    result = store.refresh_fact_integrity_metadata("does-not-exist")
    assert result == "not_found"
    assert store.get_fact("does-not-exist") is None
    assert store.get_fact_ids() == [] or "does-not-exist" not in store.get_fact_ids()


def test_refresh_not_found_invalidates_stale_l0_entry(store):
    """Codex review finding on refresh_fact_integrity_metadata's not_found
    branch: if a fact was L0-cached by this instance and then durably
    deleted (e.g. by another SQLiteGraphStore instance, or an erasure
    path) before this call's SELECT, the SELECT proves the row absent —
    that proof must evict the stale L0 entry too, or get_fact() keeps
    serving a fact this call just proved gone."""
    store2 = SQLiteGraphStore(db_path=store.db_path)
    store.store_fact(_basic_fact("d2"))
    store.get_fact("d2")  # pre-warm L0 on `store`
    assert "d2" in store._l0

    with store2._db() as conn:
        conn.execute("DELETE FROM facts WHERE fact_id = ?", ("d2",))

    result = store.refresh_fact_integrity_metadata("d2")
    assert result == "not_found"
    assert "d2" not in store._l0
    assert store.get_fact("d2") is None


# ── E. Post-promotion refresh failure must not undo / misclassify promotion ──

def test_checksum_refresh_error_after_promotion_does_not_undo_it(store, monkeypatch):
    store.store_fact(_basic_fact("e1"))

    def _boom(fact_id, **kwargs):
        raise RuntimeError("simulated metadata-persistence failure")

    monkeypatch.setattr(store, "refresh_fact_integrity_metadata", _boom)

    engine = ConsolidationEngine(store, min_confidence=0.7, prefer_validated=False)
    report = engine.run()

    assert report.promoted_hypothesized == 1
    assert report.errors == 0
    assert report.checksum_refresh_errors == 1
    assert report.fact_ids.count("e1") == 1

    fact = store.get_fact("e1")
    assert fact["epistemic_state"] == "Hypothesized", (
        "a checksum-refresh error must never trigger a fallback ESM transition"
    )


def test_checksum_refresh_not_found_after_promotion_counts_as_diagnostic_only(store, monkeypatch):
    store.store_fact(_basic_fact("e2"))

    real_refresh = store.refresh_fact_integrity_metadata

    def _pretend_not_found(fact_id, **kwargs):
        real_refresh(fact_id)  # exercise the real path too
        return "not_found"

    monkeypatch.setattr(store, "refresh_fact_integrity_metadata", _pretend_not_found)

    engine = ConsolidationEngine(store, min_confidence=0.7, prefer_validated=False)
    report = engine.run()

    assert report.promoted_hypothesized == 1
    assert report.errors == 0
    assert report.checksum_refresh_errors == 1
    assert store.get_fact("e2")["epistemic_state"] == "Hypothesized"


# ── F. State / history preservation across a metadata-only refresh ───────────

def test_refresh_touches_only_metadata(store):
    store.store_fact(_basic_fact("f1"))
    store.transition_esm("f1", "Hypothesized", by="test")
    before = store.get_fact("f1")

    result = store.refresh_fact_integrity_metadata("f1")
    assert result == "success"

    after = store.get_fact("f1")
    assert after["epistemic_state"] == before["epistemic_state"]
    assert after["claim"] == before["claim"]
    assert after["source"] == before["source"]
    assert after["confidence"] == before["confidence"]
    assert after["history"] == before["history"]
    # Only the integrity fields inside metadata may differ (they didn't
    # change here either, since the promotion's own update_state() call
    # had already attached fresh ones — but nothing OUTSIDE metadata may
    # ever differ).
    for key in before:
        if key in ("metadata",):
            continue
        assert after[key] == before[key], f"field {key!r} changed by a metadata-only refresh"


# ── G. Cache consistency ──────────────────────────────────────────────────────

def test_refresh_cache_consistency_and_reopen(store, tmp_path):
    store.store_fact(_basic_fact("g1"))
    store.transition_esm("g1", "Hypothesized", by="test")

    # Pre-warm L0.
    warm = store.get_fact("g1")
    assert warm is not None

    result = store.refresh_fact_integrity_metadata("g1")
    assert result == "success"

    fresh = store.get_fact("g1")
    expected_checksum = compute_content_checksum(
        fresh["claim"], fresh["source"], fresh["confidence"], fresh["epistemic_state"]
    )
    assert fresh["metadata"]["content_checksum"] == expected_checksum

    # Simulate a reopen — a brand new store instance over the same file
    # must see the same durable metadata (L0 is per-instance).
    reopened = SQLiteGraphStore(db_path=store.db_path)
    from_disk = reopened.get_fact("g1")
    assert from_disk["metadata"]["content_checksum"] == expected_checksum
    assert from_disk["epistemic_state"] == "Hypothesized"


# ── H. Concurrency / CAS ──────────────────────────────────────────────────────

def test_refresh_cas_retries_on_concurrent_state_change(store, monkeypatch):
    """A concurrent transition landing between this method's read and its
    guarded write must cause a CAS miss and a retry against a fresh
    snapshot — never a stale-checksum overwrite, never a false success
    that clobbers the concurrent change."""
    store2 = SQLiteGraphStore(db_path=store.db_path)

    store.store_fact(_basic_fact("h1"))
    store.transition_esm("h1", "Hypothesized", by="test")

    import core.fact_integrity as fi

    real_attach = fi.attach_integrity_metadata
    calls = {"n": 0}

    def _racy_attach(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            # Land a real concurrent transition between this attempt's
            # SELECT (which already happened) and its guarded UPDATE
            # (which hasn't happened yet).
            assert store2.transition_esm("h1", "Supported", by="concurrent_writer")
        return real_attach(*args, **kwargs)

    monkeypatch.setattr(fi, "attach_integrity_metadata", _racy_attach)

    result = store.refresh_fact_integrity_metadata("h1")

    assert result == "success"
    assert calls["n"] >= 2, "expected at least one retry after the CAS miss"

    fact = store.get_fact("h1")
    assert fact["epistemic_state"] == "Supported", (
        "the concurrent transition must survive — a stale-snapshot write "
        "must never overwrite a newer epistemic_state"
    )
    assert fact["metadata"]["content_checksum"] == compute_content_checksum(
        fact["claim"], fact["source"], fact["confidence"], "Supported"
    ), "checksum must be recomputed from the FRESH snapshot, not the stale one"


def test_refresh_missing_fact_race_returns_not_found_not_success(store, monkeypatch):
    """If the fact is deleted between this method's read and its write,
    the next retry's read must see it as gone and report 'not_found' —
    never a false 'success'."""
    store2 = SQLiteGraphStore(db_path=store.db_path)
    store.store_fact(_basic_fact("h2"))
    # Force the write path (not the no-op short-circuit): hand-corrupt the
    # stored metadata so refresh's freshly recomputed metadata differs.
    with store._db() as conn:
        conn.execute(
            "UPDATE facts SET metadata = '{}' WHERE fact_id = ?", ("h2",)
        )

    import core.fact_integrity as fi

    real_attach = fi.attach_integrity_metadata
    calls = {"n": 0}

    def _delete_then_attach(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            with store2._db() as conn:
                conn.execute("DELETE FROM facts WHERE fact_id = ?", ("h2",))
        return real_attach(*args, **kwargs)

    monkeypatch.setattr(fi, "attach_integrity_metadata", _delete_then_attach)

    result = store.refresh_fact_integrity_metadata("h2")
    assert result == "not_found"


# ── I. max_batch accounting ───────────────────────────────────────────────────

def test_max_batch_accounting_invariant_holds_when_truncated(store):
    for i in range(5):
        store.store_fact(_basic_fact(f"i{i}"))

    engine = ConsolidationEngine(
        store, min_confidence=0.7, prefer_validated=False, max_batch=2
    )
    report = engine.run()
    d = report.to_dict()

    assert d["discovered"] == 5
    assert d["scanned"] == 2
    assert _accounting_total(d) == d["scanned"], (
        f"scanned must equal the sum of outcome buckets even when "
        f"discovered ({d['discovered']}) exceeds max_batch: {d}"
    )
    assert d["errors"] == 0
    assert d["checksum_refresh_errors"] == 0
    assert len(d["fact_ids"]) == 2

    # The 3 untouched candidates must be neither promoted, nor skipped,
    # nor counted as errors this run.
    untouched = 5 - d["scanned"]
    assert untouched == 3
