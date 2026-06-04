"""
Epistemic State Machine — константы ESM (V8.6).

Согласовано с core.memory.ESM_STATES / ESM_TRANSITIONS.
"""

from __future__ import annotations

from enum import Enum


class EpistemicState(str, Enum):
    OBSERVED = "Observed"
    HYPOTHESIZED = "Hypothesized"
    SUPPORTED = "Supported"
    VALIDATED = "Validated"
    CONTRADICTED = "Contradicted"
    DEPRECATED = "Deprecated"
    COLLAPSED = "Collapsed"
    IMMUTABLE_CORE = "ImmutableCore"


__all__ = ["EpistemicState"]
