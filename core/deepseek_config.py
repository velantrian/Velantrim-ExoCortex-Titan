"""Pure validation for the narrowly allowlisted DeepSeek thinking modes."""

from __future__ import annotations


_ALLOWED_PILOT0_THINKING_MODES = frozenset({"off", "high", "max"})


def validate_deepseek_thinking_mode(mode: object) -> str:
    """Reject aliases, case changes, whitespace and unknown thinking values."""

    if not isinstance(mode, str) or mode not in _ALLOWED_PILOT0_THINKING_MODES:
        raise ValueError("Pilot-0 deepseek_thinking must be exactly off, high, or max")
    return mode


__all__ = ["validate_deepseek_thinking_mode"]
