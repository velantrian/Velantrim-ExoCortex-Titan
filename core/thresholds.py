"""
core/thresholds.py — Single source for Velantrim's truth/confidence thresholds (T1.6).

Before this module the threshold ladder was duplicated and DIVERGENT across:
  • core/truth_gate.py        _MODE_CONFIG          (gate:  PRECISION 0.9 / BALANCED 0.7 …)
  • core/facts_pack.py        require_min_confidence (pack:  PRECISION 0.75 / BALANCED 0.55 …)
  • core/promotion_policy.py  validate_min_conf = 0.75

This module is the canonical home for those numbers. Increment 1 (the P2 truth_policy
spine) only has core/truth_policy.py read from here; de-duplicating the *existing* call
sites onto these constants is task T1.2 (deferred). Keep the numbers here authoritative.
"""
from __future__ import annotations

# ── Canonical confidence ladder (canon §C12) ───────────────────────────────────
CONF_FLOOR = 0.50      # absolute minimum to even consider a claim (legacy MVP floor)
CONF_VALIDATE = 0.75   # promote/validate threshold (promotion_policy)
CONF_STRONG = 0.85     # high-trust band

# ── Per-mode GATE thresholds (admissibility for answering) ──────────────────────
# (min_confidence, min_evidence) — mirrors truth_gate._MODE_CONFIG; canonical here.
_MODE_THRESHOLDS: dict[str, dict] = {
    "PRECISION":   {"min_confidence": 0.90, "min_evidence": 5},
    "BALANCED":    {"min_confidence": 0.70, "min_evidence": 2},
    "EXPLORATION": {"min_confidence": 0.40, "min_evidence": 1},
    "CREATIVE":    {"min_confidence": 0.70, "min_evidence": 2},
}

DEFAULT_MODE = "BALANCED"


def mode_thresholds(mode: str | None) -> dict:
    """Return {min_confidence, min_evidence} for a cognitive mode (case-insensitive).

    Unknown/None mode falls back to BALANCED. Never raises.
    """
    key = (mode or DEFAULT_MODE).strip().upper()
    return dict(_MODE_THRESHOLDS.get(key, _MODE_THRESHOLDS[DEFAULT_MODE]))


__all__ = [
    "CONF_FLOOR",
    "CONF_VALIDATE",
    "CONF_STRONG",
    "DEFAULT_MODE",
    "mode_thresholds",
]
