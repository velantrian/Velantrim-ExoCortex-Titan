"""Observer must not report a clean verdict when one of its checks could not run.

Regression: ``observe()`` swallowed a check exception as ``res = None``, which is
indistinguishable from "check ran and found nothing". With the other checks
quiet, the verdict stayed ``allow`` / ``clean``.

``check_unavailable`` describes the checking mechanism, not the evidence: it is
reported separately from ``unsupported_claim`` / ``no_admissible_evidence`` and
carries only the check name and exception type (no exception text).
"""
from __future__ import annotations

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
