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
