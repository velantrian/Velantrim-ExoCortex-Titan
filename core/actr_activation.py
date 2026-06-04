"""
ACT-R Activation — бонус retrieval по истории обращений (Titan HYPERIA-3).

B = ln(Σ tᵢ^(-decay_exponent))
"""

from __future__ import annotations

import math
import threading
from datetime import UTC, datetime

from core.feature_config import get_config

_access_lock = threading.Lock()
_access_times: dict[str, list[datetime]] = {}


def is_actr_enabled() -> bool:
    return get_config().app.enable_actr_activation


def record_fact_access(fact_id: str, when: datetime | None = None) -> None:
    """Зафиксировать обращение к факту (retrieval / query)."""
    if not fact_id:
        return
    ts = when or datetime.now(UTC)
    with _access_lock:
        hist = _access_times.setdefault(fact_id, [])
        hist.append(ts)
        if len(hist) > 200:
            _access_times[fact_id] = hist[-200:]


def get_access_times(fact_id: str) -> list[datetime]:
    with _access_lock:
        return list(_access_times.get(fact_id, []))


def reset_actr_store() -> None:
    with _access_lock:
        _access_times.clear()


def actr_stats() -> dict[str, int]:
    """Сводка in-memory истории обращений."""
    with _access_lock:
        if not _access_times:
            return {"tracked_facts": 0, "total_accesses": 0}
        total = sum(len(v) for v in _access_times.values())
        return {"tracked_facts": len(_access_times), "total_accesses": total}


def compute_actr_activation(
    access_times: list[datetime],
    now: datetime | None = None,
    decay_exponent: float | None = None,
) -> float:
    if not access_times:
        return 0.0
    cfg = get_config().app
    exp = decay_exponent if decay_exponent is not None else cfg.actr_decay_exponent
    now = now or datetime.now(UTC)
    total = 0.0
    for t in access_times:
        if t.tzinfo is None:
            t = t.replace(tzinfo=UTC)
        delta_sec = max((now - t).total_seconds(), 0.001)
        total += delta_sec ** (-exp)
    if total <= 0:
        return 0.0
    return math.log(total)


def actr_score_boost(
    base_score: float,
    activation: float,
    weight: float | None = None,
) -> float:
    w = weight if weight is not None else get_config().app.actr_retrieval_weight
    return base_score + w * max(0.0, activation)


def boost_retrieval_score(fact_id: str, base_score: float) -> float:
    if not is_actr_enabled():
        return base_score
    activation = compute_actr_activation(get_access_times(fact_id))
    return actr_score_boost(base_score, activation)


__all__ = [
    "actr_score_boost",
    "actr_stats",
    "boost_retrieval_score",
    "compute_actr_activation",
    "get_access_times",
    "is_actr_enabled",
    "record_fact_access",
    "reset_actr_store",
]
