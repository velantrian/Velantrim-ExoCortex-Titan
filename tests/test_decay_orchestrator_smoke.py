"""
Smoke-тест DecayOrchestrator (умное забывание).
Страж против регресса: отсутствие config-поля salience_fsrs_protect_threshold
роняло orchestrator с AttributeError (feature был за флагом и никто не натыкался).
"""
from core.decay_orchestrator import DecayOrchestrator, DecayTarget
from core.salience_fsrs import protect_threshold, should_protect_from_decay


def test_protect_threshold_does_not_crash():
    # сам баг: protect_threshold() читал отсутствующее поле AppSettings → AttributeError
    val = protect_threshold()
    assert isinstance(val, float) and 0.0 < val <= 1.0


def test_normal_fact_decays():
    o = DecayOrchestrator().compute(
        DecayTarget(weight=1.0, t_days=365, stability_days=7, salience_weight=0.5)
    )
    assert not o.skipped
    assert o.new_weight < 1.0            # тускнеет
    assert o.new_weight > 0.0            # но не исчезает (вес, не удаление)
    assert "FSRS" in o.stages_applied


def test_immutable_core_protected():
    o = DecayOrchestrator().compute(
        DecayTarget(weight=1.0, t_days=365, epistemic_state="ImmutableCore", salience_weight=0.5)
    )
    assert o.skipped and o.skip_reason == "esm_immutable"
    assert o.new_weight == 1.0           # ценности не забываются


def test_high_salience_protected():
    assert should_protect_from_decay(0.99) is True
    o = DecayOrchestrator().compute(
        DecayTarget(weight=1.0, t_days=365, stability_days=7, salience_weight=0.99)
    )
    assert o.skipped and o.skip_reason == "salience_protected"


def test_higher_stability_decays_slower():
    orch = DecayOrchestrator()
    rare = orch.compute(DecayTarget(weight=1.0, t_days=90, stability_days=3, salience_weight=0.5))
    often = orch.compute(DecayTarget(weight=1.0, t_days=90, stability_days=30, salience_weight=0.5))
    assert often.new_weight > rare.new_weight   # частое вспоминание → медленнее тускнеет
