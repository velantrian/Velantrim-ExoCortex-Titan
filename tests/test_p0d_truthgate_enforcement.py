"""P0-D (belt-and-suspenders): the final Supported -> Validated hop from
graduated promotion (core/promotion_policy.py) and consolidation
(core/consolidation_engine.py) must go through validate_and_promote()
(TruthGate + CAS), never a bare transition_esm().

Each module's own thresholds (corroboration/age/confidence, or
confidence/utility-gate) remain pre-vetting: they decide a fact is a
CANDIDATE for Validated. TruthGate decides whether it actually becomes
Validated. A candidate that clears the module's own bar but not
TruthGate's must be left at 'Supported', not silently promoted — that is
exactly the bypass this fix closes.
"""
from __future__ import annotations

import pytest

from core.consolidation_engine import ConsolidationEngine
from core.memory import SQLiteGraphStore
from core.promotion_policy import PromotionConfig, run_graduated_promotion


@pytest.fixture
def store(tmp_path):
    return SQLiteGraphStore(db_path=str(tmp_path / "p0d.db"))


def _trusted_fact(fact_id: str, *, evidence_refs=None) -> dict:
    fact = {
        "fact_id": fact_id,
        "claim": "A trusted seed axiom about the domain",
        "source": "domain_seed",
        "confidence": 0.9,
    }
    if evidence_refs is not None:
        fact["metadata"] = {"evidence_refs": evidence_refs}
    return fact


# ── core/promotion_policy.py ────────────────────────────────────────────────

def test_graduated_promotion_candidate_without_evidence_stays_supported(store):
    """Clears this module's own bar (trusted source, no age/corroboration
    requirement bypassed via source_trusted) but has zero evidence_refs —
    TruthGate's BALANCED mode requires >= 2. Must NOT reach Validated."""
    store.store_fact(_trusted_fact("t1"))  # no evidence_refs at all
    cfg = PromotionConfig(validate_min_age_s=0)

    run_graduated_promotion(store, cfg=cfg)  # Observed -> Hypothesized
    run_graduated_promotion(store, cfg=cfg)  # Hypothesized -> Supported
    report = run_graduated_promotion(store, cfg=cfg)  # attempted Supported -> Validated

    assert store.get_fact("t1")["epistemic_state"] == "Supported"
    assert "Supported->Validated" not in report.promoted
    # Review finding (Copilot): the previous assertion here
    # (`unchanged >= 1 or errors == 0`) could pass even if the rejection
    # were silently mis-accounted as an error. Assert the rejection is
    # counted explicitly, and that nothing crashed.
    assert report.errors == 0
    assert report.rejected_by_truthgate == 1


def test_graduated_promotion_rejected_candidate_is_retried_after_evidence_added(store):
    """A TruthGate rejection must not strand the fact — run_graduated_promotion
    already rescans 'Supported' facts every run (unlike the naive
    ConsolidationEngine before its own fix below), so adding evidence_refs
    later and re-running must reach Validated without any special retry API.
    """
    store.store_fact(_trusted_fact("t1b"))
    cfg = PromotionConfig(validate_min_age_s=0)
    run_graduated_promotion(store, cfg=cfg)
    run_graduated_promotion(store, cfg=cfg)
    rejected = run_graduated_promotion(store, cfg=cfg)
    assert store.get_fact("t1b")["epistemic_state"] == "Supported"
    assert rejected.rejected_by_truthgate == 1

    store.store_fact(_trusted_fact("t1b", evidence_refs=["src1", "src2"]))
    retried = run_graduated_promotion(store, cfg=cfg)

    assert store.get_fact("t1b")["epistemic_state"] == "Validated"
    assert retried.promoted.get("Supported->Validated") == 1


def test_graduated_promotion_candidate_with_evidence_reaches_validated(store):
    """Same module-level candidacy, but with enough evidence_refs to also
    clear TruthGate — the belt-and-suspenders gate is additive, not a
    second obstacle course that can never be cleared."""
    store.store_fact(_trusted_fact("t2", evidence_refs=["src1", "src2"]))
    cfg = PromotionConfig(validate_min_age_s=0)

    run_graduated_promotion(store, cfg=cfg)
    run_graduated_promotion(store, cfg=cfg)
    report = run_graduated_promotion(store, cfg=cfg)

    assert store.get_fact("t2")["epistemic_state"] == "Validated"
    assert report.promoted.get("Supported->Validated") == 1


def test_graduated_promotion_never_calls_transition_esm_for_validated(store, monkeypatch):
    """Direct proof the bypass is closed: transition_esm(..., 'Validated')
    must never be reachable from run_graduated_promotion — only
    validate_and_promote()."""
    store.store_fact(_trusted_fact("t3", evidence_refs=["src1", "src2"]))
    cfg = PromotionConfig(validate_min_age_s=0)
    run_graduated_promotion(store, cfg=cfg)
    run_graduated_promotion(store, cfg=cfg)  # now Supported

    real_transition_esm = store.transition_esm

    def _guarded_transition_esm(fact_id, new_state, by="transition_esm"):
        assert new_state != "Validated", (
            "run_graduated_promotion must reach 'Validated' only via "
            "validate_and_promote(), never a direct transition_esm() call"
        )
        return real_transition_esm(fact_id, new_state, by=by)

    monkeypatch.setattr(store, "transition_esm", _guarded_transition_esm)
    report = run_graduated_promotion(store, cfg=cfg)

    assert store.get_fact("t3")["epistemic_state"] == "Validated"
    assert report.promoted.get("Supported->Validated") == 1


# ── core/consolidation_engine.py ────────────────────────────────────────────

def test_consolidation_candidate_without_evidence_stays_supported(store):
    """Manual source always clears the utility gate and this engine's own
    confidence gate, but with no evidence_refs TruthGate's BALANCED mode
    still rejects the final hop."""
    store.store_fact({
        "fact_id": "c1",
        "claim": "Some claim entered by hand",
        "source": "manual",
        "confidence": 0.9,
    })
    engine = ConsolidationEngine(store, min_confidence=0.7)
    report = engine.run()

    assert store.get_fact("c1")["epistemic_state"] == "Supported"
    assert report.promoted_validated == 0
    assert report.errors == 0
    assert report.rejected_by_truthgate == 1


def test_consolidation_rejected_candidate_is_retried_after_evidence_added(store):
    """Review finding (chatgpt-codex-connector): _promote_to_validated_via_truthgate()
    durably advances the fact to 'Supported' before validate_and_promote()
    runs. Since ConsolidationEngine.run() used to scan Observed only, a
    TruthGate rejection stranded the fact at 'Supported' forever, even
    after evidence was added later. run() now also rescans 'Supported'
    facts (when prefer_validated=True), so this must reach Validated
    without needing a special retry API.
    """
    store.store_fact({
        "fact_id": "c1b",
        "claim": "Some claim entered by hand",
        "source": "manual",
        "confidence": 0.9,
    })
    engine = ConsolidationEngine(store, min_confidence=0.7)
    rejected = engine.run()
    assert store.get_fact("c1b")["epistemic_state"] == "Supported"
    assert rejected.rejected_by_truthgate == 1

    store.store_fact({
        "fact_id": "c1b",
        "claim": "Some claim entered by hand",
        "source": "manual",
        "confidence": 0.9,
        "metadata": {"evidence_refs": ["src1", "src2"]},
    })
    retried = engine.run()

    assert store.get_fact("c1b")["epistemic_state"] == "Validated"
    assert retried.promoted_validated == 1


def test_consolidation_candidate_with_evidence_reaches_validated(store):
    store.store_fact({
        "fact_id": "c2",
        "claim": "Some claim entered by hand",
        "source": "manual",
        "confidence": 0.9,
        "metadata": {"evidence_refs": ["src1", "src2"]},
    })
    engine = ConsolidationEngine(store, min_confidence=0.7)
    report = engine.run()

    assert store.get_fact("c2")["epistemic_state"] == "Validated"
    assert report.promoted_validated == 1


def test_consolidation_never_calls_transition_esm_for_validated(store, monkeypatch):
    store.store_fact({
        "fact_id": "c3",
        "claim": "Some claim entered by hand",
        "source": "manual",
        "confidence": 0.9,
        "metadata": {"evidence_refs": ["src1", "src2"]},
    })
    real_transition_esm = store.transition_esm

    def _guarded_transition_esm(fact_id, new_state, by="transition_esm"):
        assert new_state != "Validated", (
            "ConsolidationEngine must reach 'Validated' only via "
            "validate_and_promote(), never a direct transition_esm() call"
        )
        return real_transition_esm(fact_id, new_state, by=by)

    monkeypatch.setattr(store, "transition_esm", _guarded_transition_esm)
    engine = ConsolidationEngine(store, min_confidence=0.7)
    report = engine.run()

    assert store.get_fact("c3")["epistemic_state"] == "Validated"
    assert report.promoted_validated == 1


# ── accounting invariant: no candidate is ever silently lost ────────────────

def test_graduated_promotion_report_accounting_has_no_lost_candidates(store):
    """scanned must equal the sum of every outcome bucket — a candidate
    rejected by TruthGate is exactly as accounted-for as one that's
    promoted, unchanged, or errored. (`demoted` is a subset annotation of
    `promoted` for target=="Contradicted", not an independent bucket, so it
    is deliberately excluded from this sum.)
    """
    store.store_fact({
        "fact_id": "m1", "claim": "tiny", "source": "x", "confidence": 0.9,
    })  # too short -> unchanged
    store.store_fact({
        "fact_id": "m2", "claim": "a normal length claim about something",
        "source": "x", "confidence": 0.9,
    })  # Observed -> Hypothesized (promoted)
    store.store_fact(_trusted_fact("m3"))  # will reach Supported, no evidence -> rejected
    store.transition_esm("m3", "Hypothesized")
    store.transition_esm("m3", "Supported")
    store.store_fact(_trusted_fact("m4", evidence_refs=["src1", "src2"]))  # -> promoted
    store.transition_esm("m4", "Hypothesized")
    store.transition_esm("m4", "Supported")

    cfg = PromotionConfig(validate_min_age_s=0)
    report = run_graduated_promotion(store, cfg=cfg)

    assert report.scanned == 4
    accounted = sum(report.promoted.values()) + report.unchanged + report.errors + report.rejected_by_truthgate
    assert accounted == report.scanned
    assert store.get_fact("m1")["epistemic_state"] == "Observed"
    assert store.get_fact("m2")["epistemic_state"] == "Hypothesized"
    assert store.get_fact("m3")["epistemic_state"] == "Supported"
    assert store.get_fact("m4")["epistemic_state"] == "Validated"


def test_consolidation_report_accounting_has_no_lost_candidates(store):
    """scanned must equal the sum of every ConsolidationReport bucket, for
    the paths P0-D touches: skipped (pre-existing gates) and
    rejected_by_truthgate (new).

    NOTE: deliberately does NOT include a fact that reaches a *successful*
    promotion (Hypothesized or Validated) in this sum-invariant check.
    ConsolidationEngine._refresh_checksum() — pre-existing, unrelated to
    P0-D, not touched by this PR — re-fetches the fact (now in its new,
    non-Observed state) and calls store_fact() on it; store_fact() rejects
    any non-Observed epistemic_state on a upsert unconditionally (except
    the Ring Zero Validated seed), so _refresh_checksum() always raises
    ValueError after every successful promotion. That's caught by the
    surrounding `except ValueError` fallback (which then also fails, since
    the fact is no longer eligible to demote to 'Hypothesized'), landing in
    `except Exception: report.errors += 1` — spuriously incrementing
    `errors` by 1 for every successful promotion, on top of the correct
    promoted_validated/promoted_hypothesized increment. This makes `errors`
    unreliable as a health signal for ConsolidationEngine today, on `main`
    as well as on this branch — confirmed present with a plain
    Hypothesized-only promotion on `main` with no TruthGate involved at
    all. Reported as a separate, pre-existing, out-of-scope issue; not
    fixed here (see PR #25 review notes).
    """
    store.store_fact({
        "fact_id": "n1", "claim": "tiny", "source": "manual", "confidence": 0.9,
    })  # too short -> skipped_short_claim
    store.store_fact({
        "fact_id": "n2", "claim": "a normal length claim about something",
        "source": "manual", "confidence": 0.1,
    })  # low confidence -> skipped_low_confidence
    store.store_fact({
        "fact_id": "n3", "claim": "a normal length claim about something else",
        "source": "some_untrusted_source", "confidence": 0.9,
    })  # clears confidence, fails utility gate (unused, isolated, not manual) -> skipped_low_confidence
    store.store_fact({
        "fact_id": "n4", "claim": "a normal length claim needing evidence",
        "source": "manual", "confidence": 0.9,
    })  # clears all gates, no evidence_refs -> rejected_by_truthgate

    engine = ConsolidationEngine(store, min_confidence=0.7)
    report = engine.run()

    assert report.scanned == 4
    assert report.errors == 0
    accounted = (
        report.promoted_validated + report.promoted_hypothesized
        + report.skipped_low_confidence + report.skipped_short_claim
        + report.errors + report.rejected_by_truthgate
    )
    assert accounted == report.scanned
    assert store.get_fact("n4")["epistemic_state"] == "Supported"
