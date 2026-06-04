"""
core/rate_limit.py — tiny in-process per-IP token-bucket rate limiter (stdlib only).

Zero dependencies (matches Velantrim's zero-dep core ethos). Used by an opt-in middleware
in server.py, gated by ENABLE_RATE_LIMIT (default off) → no behavior change when disabled.

Not distributed/persistent (single-process only) — adequate for the local single-node MVP;
swap for slowapi/Redis if multi-tenant/public deployment is ever needed.
"""
from __future__ import annotations

import threading
import time

from core.feature_config import get_config

# Defaults; overridable via env through feature_config if desired later.
_DEFAULT_CAPACITY = 60      # burst tokens
_DEFAULT_REFILL_PER_SEC = 1.0  # ~60 req/min steady state

_lock = threading.Lock()
# ip -> (tokens, last_refill_ts)
_buckets: dict[str, tuple[float, float]] = {}


def _params() -> tuple[float, float]:
    app = get_config().app
    cap = float(getattr(app, "rate_limit_capacity", _DEFAULT_CAPACITY) or _DEFAULT_CAPACITY)
    refill = float(getattr(app, "rate_limit_refill_per_sec", _DEFAULT_REFILL_PER_SEC)
                   or _DEFAULT_REFILL_PER_SEC)
    return cap, refill


def check_rate_limit(ip: str, *, now: float | None = None) -> tuple[bool, int]:
    """Consume one token for `ip`. Returns (allowed, retry_after_seconds).

    Token bucket: refill `refill`/sec up to `capacity`; each request costs 1 token.
    Thread-safe. retry_after is 0 when allowed.
    """
    cap, refill = _params()
    t = now if now is not None else time.monotonic()
    with _lock:
        tokens, last = _buckets.get(ip, (cap, t))
        tokens = min(cap, tokens + (t - last) * refill)
        if tokens >= 1.0:
            _buckets[ip] = (tokens - 1.0, t)
            return True, 0
        _buckets[ip] = (tokens, t)
        deficit = 1.0 - tokens
        retry_after = int(deficit / refill) + 1 if refill > 0 else 1
        return False, retry_after


def reset() -> None:
    """Clear all buckets (tests)."""
    with _lock:
        _buckets.clear()


__all__ = ["check_rate_limit", "reset"]
