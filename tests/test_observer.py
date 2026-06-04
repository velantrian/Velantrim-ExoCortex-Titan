"""Unit tests for core/observer.py (Observer P0, passive meta-monitor)."""
from __future__ import annotations

import copy
import sqlite3

import pytest

from core.observer import ALLOW, GAP_NOTICE, REJECT, WARN, ObserverVerdict, observe


@pytest.fixture(autouse=True)
def _no_goal_drift(monkeypatch):
    """Neutralize goal alignment by default so only the test under scrutiny drives it.

    Belt-and-suspenders: besides patching query_goal_alignment, archive any active
    goals leaked into the shared goal-stack DB by an earlier test. In the full suite
    a leaked active goal for user 'default' makes the REAL query_goal_alignment return
    0.25 (<0.30) → spurious goal_drift, if the monkeypatch is bypassed (observed: the
    clean-answer test failed with goal_alignment=0.25 only in full-suite order). With
    no active goals the real function returns 0.5, so the test is robust either way.
    Tests that need drift (test_observe_goal_drift) re-patch the fn explicitly.
    """
    monkeypatch.setattr("core.gap_detector.query_goal_alignment", lambda q, u="default": 0.5)
    try:
        import sqlite3

        from core.goal_stack import get_goal_stack
        gs = get_goal_stack()
        with sqlite3.connect(gs.db_path) as _c:
            _c.execute("UPDATE user_goals SET status = 'archived' WHERE status = 'active'")
    except Exception:
        pass  # table may not exist yet / DB unavailable — harmless


def _fact(fid, conf, claim, state="Validated", evidence=None, **extra):
    f = {
        "fact_id": fid,
        "claim": claim,
        "confidence": conf,
        "source": "src:test",
        "epistemic_state": state,
    }
    if evidence is not None:
        f["metadata"] = {"evidence_refs": evidence}
    f.update(extra)
    return f


# ── clean / grounded ────────────────────────────────────────────────────────────

def test_observe_clean_grounded_answer():
    claim = "Вода кипит при 100 градусах Цельсия при атмосферном давлении"
    facts = [_fact("a", 0.95, claim, evidence=[{"source_id": "phys", "span": "1-9"}])]
    v = observe("при какой температуре кипит вода", facts, claim)
    assert isinstance(v, ObserverVerdict)
    assert v.decision == ALLOW and v.flags == []


# ── unsupported_claim (answer not grounded in facts) ─────────────────────────────

def test_observe_unsupported_claim():
    facts = [_fact("a", 0.9, "Вода кипит при 100 градусах Цельсия")]
    answer = "Слоны являются крупнейшими сухопутными млекопитающими планеты."
    v = observe("вопрос про воду", facts, answer)
    assert "unsupported_claim" in v.flags
    assert v.decision == GAP_NOTICE


# ── no_admissible_evidence (reject) ──────────────────────────────────────────────

def test_observe_reject_no_admissible_facts():
    facts = [_fact("a", 0.1, "что-то"), _fact("b", 0.2, "ещё что-то")]
    v = observe("q", facts, "ответ")
    assert v.decision == REJECT and "no_admissible_evidence" in v.flags


def test_observe_reject_on_empty_facts():
    v = observe("q", [], "")
    assert v.decision == REJECT and "no_admissible_evidence" in v.flags


# ── truth_scope_leak (mixing trusted with contradicted / known_false) ────────────

def test_observe_truth_scope_leak_known_false():
    claim = "Вода кипит при 100 градусах"
    facts = [
        _fact("v", 0.95, claim),
        _fact("c", 0.0, "Вода кипит при 0 градусах", state="Contradicted",
              contradicts="v"),
    ]
    v = observe("q", facts, claim)
    assert "truth_scope_leak" in v.flags


# ── goal_drift (low alignment) ───────────────────────────────────────────────────

def test_observe_goal_drift(monkeypatch):
    monkeypatch.setattr("core.gap_detector.query_goal_alignment", lambda q, u="default": 0.1)
    claim = "Питон — язык программирования"
    facts = [_fact("a", 0.95, claim, evidence=[{"source_id": "psf", "span": "1-5"}])]
    v = observe("вопрос не по цели", facts, claim)
    assert "goal_drift" in v.flags and v.decision in (WARN, GAP_NOTICE, REJECT)


# ── severity aggregation (reject dominates warn) ─────────────────────────────────

def test_observe_severity_reject_dominates():
    # low-confidence facts → reject; also mark a leak → warn; reject must win
    facts = [_fact("a", 0.1, "x", state="Contradicted", contradicts="y")]
    v = observe("q", facts, "ответ")
    assert v.decision == REJECT


# ── passivity: observe() mutates nothing ─────────────────────────────────────────

def test_observe_is_passive():
    facts = [_fact("a", 0.95, "Вода кипит при 100 градусах")]
    snapshot = copy.deepcopy(facts)
    observe("q", facts, "Вода кипит при 100 градусах")
    assert facts == snapshot  # no mutation of the input facts


# ── audit_chain helper (capability tested with an in-memory chain) ───────────────

def test_log_observer_verdict_writes_event():
    from core.audit_chain import AuditChain, EventType

    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE memory_events (
            event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, fact_id TEXT,
            from_state TEXT, to_state TEXT, actor TEXT NOT NULL, reason TEXT,
            payload TEXT, confidence REAL, event_hash TEXT NOT NULL UNIQUE,
            prev_event_hash TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    chain = AuditChain(conn)
    evt = chain.log_observer_verdict(decision="reject", flags=["no_admissible_evidence"])
    assert evt.event_type == EventType.OBSERVER_VERDICT
    row = conn.execute(
        "SELECT event_type, payload FROM memory_events WHERE event_id=?", (evt.event_id,)
    ).fetchone()
    assert row is not None and row[0] == "observer_verdict"
    assert "no_admissible_evidence" in row[1]


def test_observe_logs_when_chain_provided():
    from core.audit_chain import AuditChain

    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE memory_events (
            event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, fact_id TEXT,
            from_state TEXT, to_state TEXT, actor TEXT NOT NULL, reason TEXT,
            payload TEXT, confidence REAL, event_hash TEXT NOT NULL UNIQUE,
            prev_event_hash TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    chain = AuditChain(conn)
    observe("q", [_fact("a", 0.1, "x")], "ответ", audit_chain=chain)
    n = conn.execute(
        "SELECT COUNT(*) FROM memory_events WHERE event_type='observer_verdict'"
    ).fetchone()[0]
    assert n == 1
