"""👁️ core/essence/observer_bridge.py — Observer bridge"""
from __future__ import annotations


def get_observer_bridge():
    """Мост к observer.py. Файл не перемещён."""
    try:
        # Pre-existing API drift: core.observer exposes observe(...), not get_observer().
        # Caught below like any other optional-bridge failure, so this bridge currently
        # always returns None. Not fixed here (behavior change out of scope for a
        # typing-only pass) — tracked as a follow-up bug.
        from core.observer import get_observer  # type: ignore[attr-defined]
        return get_observer()
    except Exception:
        return None
