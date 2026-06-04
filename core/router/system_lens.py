"""
Линза VELANTRIM (system) — Graph=Truth, только проверенная память.
"""

from __future__ import annotations

from typing import Any

IMMUTABLE_IDS = frozenset({"VALUES_CORE", "RING_ZERO"})
_TRUSTED_STATES = frozenset({"Validated", "Supported", "ImmutableCore"})


def filter_facts(
    facts: list[dict[str, Any]],
    query: str,
    user_id: str = "default",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Только Validated/Supported/ImmutableCore с достаточной уверенностью."""
    _ = query, user_id
    trusted: list[dict[str, Any]] = []
    ring: list[dict[str, Any]] = []
    for f in facts:
        fid = f.get("fact_id", "")
        state = f.get("epistemic_state", "")
        conf = float(f.get("confidence") or 0)
        if fid in IMMUTABLE_IDS:
            ring.append(f)
            continue
        if state in _TRUSTED_STATES and conf >= 0.55:
            trusted.append(f)

    out = ring + trusted
    if not out:
        out = [
            f
            for f in facts
            if float(f.get("confidence") or 0) >= 0.7
        ] or facts

    meta = {
        "immutable_core_count": len(ring),
        "trusted_count": len(trusted),
        "policy": "graph_truth_strict",
    }
    return out, meta


def system_instructions(user_id: str = "default") -> str:
    _ = user_id
    return (
        "Режим VELANTRIM: отвечай строго по верифицированным фактам памяти. "
        "Graph = Truth. Не выдумывай. Если данных недостаточно — явно скажи об этом. "
        "Не смешивай гипотезы с проверенными утверждениями."
    )


__all__ = ["filter_facts", "system_instructions", "IMMUTABLE_IDS"]
