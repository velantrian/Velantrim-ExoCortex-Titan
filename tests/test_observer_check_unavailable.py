"""Observer must not report a clean verdict when one of its checks could not run.

Regression: ``observe()`` swallowed a check exception as ``res = None``, which is
indistinguishable from "check ran and found nothing". With the other checks
quiet, the verdict stayed ``allow`` / ``clean``.

``check_unavailable`` describes the checking mechanism, not the evidence: it is
reported separately from ``unsupported_claim`` / ``no_admissible_evidence`` and
carries only the check name and exception type (no exception text).
"""
from __future__ import annotations

import importlib

import pytest

from core.observer import ALLOW, REJECT, WARN, observe

SECRET = "SECRET-EXCEPTION-DETAIL"


@pytest.fixture(autouse=True)
def _neutral_goal_alignment(monkeypatch):
    monkeypatch.setattr("core.gap_detector.query_goal_alignment", lambda q, u="default": 0.5)


def _facts():
    return [{
        "fact_id": "f1",
        "claim": "SQLite serializes writes through explicit transactions.",
        "confidence": 0.9,
        "source": "src:test",
        "epistemic_state": "Validated",
        "metadata": {"evidence_refs": [{"source_id": "doc:1"}]},
    }]


def _boom(*args, **kwargs):
    raise RuntimeError(SECRET)


def test_clean_baseline_is_allow():
    v = observe(
        "How does SQLite serialize writes?",
        _facts(),
        "SQLite serializes writes through explicit transactions.",
    )
    assert v.decision == ALLOW
    assert v.is_clean


@pytest.mark.parametrize(
    ("target", "check_name"),
    [
        ("core.truth_policy.decide", "no_admissible_evidence"),
        ("core.output_faithfulness.OutputFaithfulnessChecker.check", "unsupported_claim"),
        ("core.gap_detector.query_goal_alignment", "goal_drift"),
    ],
)
def test_failed_check_is_reported_and_not_clean(monkeypatch, target, check_name):
    monkeypatch.setattr(target, _boom)

    v = observe(
        "How does SQLite serialize writes?",
        _facts(),
        "SQLite serializes writes through explicit transactions.",
    )

    assert not v.is_clean
    assert v.decision == WARN
    assert "check_unavailable" in v.flags
    assert v.details["unavailable_checks"] == [
        {"check": check_name, "error_type": "RuntimeError"},
    ]
    assert v.reason != "clean"
    # Content-free: the exception message never leaves the Observer.
    assert SECRET not in repr(v.to_dict())


def test_unavailable_check_does_not_mask_a_stronger_verdict(monkeypatch):
    monkeypatch.setattr("core.gap_detector.query_goal_alignment", _boom)

    v = observe("anything", [], "an answer with no admissible evidence")

    assert v.decision == REJECT
    assert "no_admissible_evidence" in v.flags
    assert "check_unavailable" in v.flags


ALL_CHECKS = [
    ("core.output_faithfulness.OutputFaithfulnessChecker.check", "unsupported_claim"),
    ("core.truth_policy.decide", "no_admissible_evidence"),
    ("core.observer._check_truth_scope_leak", "truth_scope_leak"),
    ("core.gap_detector.query_goal_alignment", "goal_drift"),
]
ANSWER = "SQLite serializes writes through explicit transactions."


def _live_observer():
    """The core.observer module that is live in sys.modules.

    Earlier tests reload core.* modules, so a name imported at the top of this file
    can point at a stale module object. Patching a module attribute by dotted path and
    then calling a stale ``observe`` would silently miss the patch (order-dependent).
    """
    return importlib.import_module("core.observer")


def test_truth_scope_leak_check_failure_is_reported(monkeypatch):
    obs = _live_observer()
    monkeypatch.setattr(obs, "_check_truth_scope_leak", _boom)

    v = obs.observe("How does SQLite serialize writes?", _facts(), ANSWER)

    assert v.flags == ["check_unavailable"]
    assert v.decision == WARN
    assert v.details["unavailable_checks"] == [
        {"check": "truth_scope_leak", "error_type": "RuntimeError"},
    ]


def test_every_check_failing_reports_each_check_and_one_flag(monkeypatch):
    for target, _name in ALL_CHECKS:
        monkeypatch.setattr(target, _boom)

    v = _live_observer().observe("How does SQLite serialize writes?", _facts(), ANSWER)

    assert v.flags == ["check_unavailable"]
    assert v.decision == WARN
    assert not v.is_clean
    assert v.reason == "check_unavailable"
    assert v.details["unavailable_checks"] == [
        {"check": name, "error_type": "RuntimeError"} for _target, name in ALL_CHECKS
    ]
    assert SECRET not in repr(v.to_dict())


def test_clean_verdict_carries_no_unavailable_checks_key():
    v = observe("How does SQLite serialize writes?", _facts(), ANSWER)

    assert v.is_clean
    assert "unavailable_checks" not in v.details


def test_audit_chain_receives_the_check_unavailable_flag(monkeypatch):
    class _Chain:
        def __init__(self):
            self.calls = []

        def log_observer_verdict(self, **kwargs):
            self.calls.append(kwargs)

    monkeypatch.setattr("core.truth_policy.decide", _boom)
    chain = _Chain()

    observe("How does SQLite serialize writes?", _facts(), ANSWER, audit_chain=chain)

    assert chain.calls == [{
        "decision": WARN,
        "flags": ["check_unavailable"],
        "actor": "observer",
        "reason": "check_unavailable",
    }]
