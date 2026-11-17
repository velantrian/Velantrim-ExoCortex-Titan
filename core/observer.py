"""
core/observer.py — Observer P0: passive meta-monitor (Essence Layer Completion).

After the system has produced an answer, the Observer asks one question:
"did we distort the goal, the evidence, the epistemic scope, or stay ungrounded?"
It is a thin ORCHESTRATOR over checks that ALREADY exist — it composes them into a single
verdict; it does not re-implement them and adds no new infrastructure.

Hard constraints (canon / ТЗ) — Observer is PASSIVE:
  • MUST NOT write FACT / L3, MUST NOT change truth_status or the graph.
  • MUST NOT generate the user answer.
  • Only returns a verdict (allow|warn|gap_notice|reject) + flags. It may append ONE
    audit_chain event, but only if a chain is explicitly handed to it.

Increment-1 checks (each delegates to an existing module):
  unsupported_claim      → core.output_faithfulness.OutputFaithfulnessChecker
  no_admissible_evidence → core.truth_policy.decide (hard reject only)
  truth_scope_leak       → epistemic_state mix / known_false among the facts used
  goal_drift             → core.gap_detector.query_goal_alignment

A check that raises is reported as flag ``check_unavailable`` (decision at least ``warn``,
``details["unavailable_checks"]`` = check name + exception type, no exception text). It is never
folded into a clean ``allow``, and it is distinct from missing-evidence flags. The severity is a flat
``warn`` (also for the hard ``no_admissible_evidence`` check), so a consumer that gates on Observer
must key on ``check_unavailable`` in ``flags`` / ``not is_clean``, not on ``decision == reject``.

Deferred (named in the plan): query-side gist, stale_context, false_reactivation,
causal_overclaim, advanced gist_distortion, metrics dashboards, nightly review.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from core.core3_adapter import ALLOW, GAP_NOTICE, REJECT  # shared verdict vocabulary

logger = logging.getLogger(__name__)

WARN = "warn"
# Flag for a check that raised: the mechanism was unavailable (not "nothing found").
CHECK_UNAVAILABLE = "check_unavailable"

# Severity ordering for aggregation (higher = more severe).
_SEVERITY = {ALLOW: 0, WARN: 1, GAP_NOTICE: 2, REJECT: 3}

# Conservative tunables — calibrate before flipping the flag on by default.
_FAITHFULNESS_MIN = 0.30      # answer grounding below this → unsupported_claim
_GOAL_ALIGNMENT_MIN = 0.30    # query↔goal alignment below this → goal_drift
_LEAK_STATES = {"Contradicted", "Deprecated", "Collapsed"}
_TRUSTED_STATES = {"Validated", "ImmutableCore", "Supported"}


@dataclass
class ObserverVerdict:
    """Mirrors truth_policy.TruthVerdict / core3_adapter.Core3Verdict shape."""

    decision: str = ALLOW                       # allow | warn | gap_notice | reject
    flags: list[str] = field(default_factory=list)
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return self.decision == ALLOW and not self.flags

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "flags": list(self.flags),
            "reason": self.reason,
            "details": self.details,
        }


def _check_unsupported_claim(answer: str, facts: list, details: dict):
    if not answer or not facts:
        return None
    from core.output_faithfulness import OutputFaithfulnessChecker

    res = OutputFaithfulnessChecker().check(answer, facts)
    details["faithfulness"] = res.to_dict()
    if res.total_claims and res.score < _FAITHFULNESS_MIN:
        return GAP_NOTICE, "unsupported_claim"
    return None


def _check_admissible_evidence(query: str, facts: list, mode: str, details: dict):
    from core.truth_policy import decide

    verdict = decide(query, facts, mode=mode)
    details["truth_policy"] = verdict.to_dict()
    # Only the HARD signal escalates here (0 admissible facts → don't fabricate).
    # The softer "admissible but no structured evidence" (gap_notice) is recorded in
    # details without raising the Observer decision — it is the common case for
    # source-only facts and would otherwise be noise until EvidenceRef adoption grows.
    if verdict.is_reject:
        return REJECT, "no_admissible_evidence"
    return None


def _check_truth_scope_leak(facts: list, details: dict):
    states = [str((f or {}).get("epistemic_state") or "") for f in facts]
    trusted = any(s in _TRUSTED_STATES for s in states)
    leaky = [s for s in states if s in _LEAK_STATES]
    known_false = any(
        bool((f or {}).get("known_false") or (f or {}).get("contradicts")) for f in facts
    )
    details["epistemic_states"] = states
    if known_false or (trusted and leaky):
        return WARN, "truth_scope_leak"
    return None


def _check_goal_drift(query: str, user_id: str, details: dict):
    from core.gap_detector import query_goal_alignment

    align = float(query_goal_alignment(query, user_id))
    details["goal_alignment"] = round(align, 3)
    if align < _GOAL_ALIGNMENT_MIN:
        return WARN, "goal_drift"
    return None


def observe(
    query: str,
    facts: Sequence[dict],
    answer: str,
    *,
    mode: str = "BALANCED",
    user_id: str = "default",
    audit_chain: Any = None,
) -> ObserverVerdict:
    """Run the passive meta-checks and return one aggregated verdict. Never raises."""
    facts = list(facts or [])
    details: dict[str, Any] = {}
    flags: list[str] = []
    decision = ALLOW

    checks = (
        ("unsupported_claim", lambda: _check_unsupported_claim(answer, facts, details)),
        ("no_admissible_evidence", lambda: _check_admissible_evidence(query, facts, mode, details)),
        ("truth_scope_leak", lambda: _check_truth_scope_leak(facts, details)),
        ("goal_drift", lambda: _check_goal_drift(query, user_id, details)),
    )
    unavailable: list[dict[str, str]] = []
    for name, check in checks:
        try:
            res = check()
        except Exception as exc:  # noqa: BLE001 — a broken check never breaks Observer
            # A check that could not run is NOT a clean result: report it as
            # unavailable (mechanism state, distinct from missing evidence).
            # Content-free: only the check name and exception type are kept.
            logger.warning("observer check unavailable: %s (%s)", name, type(exc).__name__)
            unavailable.append({"check": name, "error_type": type(exc).__name__})
            res = (WARN, CHECK_UNAVAILABLE)
        if res:
            sev, flag = res
            if flag not in flags:
                flags.append(flag)
            if _SEVERITY[sev] > _SEVERITY[decision]:
                decision = sev
    if unavailable:
        details["unavailable_checks"] = unavailable

    verdict = ObserverVerdict(
        decision=decision,
        flags=flags,
        reason="clean" if decision == ALLOW else ", ".join(flags),
        details=details,
    )

    # Optional, best-effort audit logging — ONLY if a chain was explicitly provided.
    # Observer stays passive: it logs an observation, it does NOT write facts / change graph.
    if audit_chain is not None:
        try:
            audit_chain.log_observer_verdict(
                decision=verdict.decision,
                flags=verdict.flags,
                actor="observer",
                reason=verdict.reason,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("observer audit log skipped: %s", exc)

    return verdict


__all__ = [
    "ObserverVerdict", "observe", "ALLOW", "WARN", "GAP_NOTICE", "REJECT", "CHECK_UNAVAILABLE",
]
