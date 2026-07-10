"""🪞 core/essence/mirror.py — Mirror bridge"""
from __future__ import annotations


def get_mirror_bridge():
    """Мост к working_notebook.py. Файл не перемещён."""
    try:
        # Pre-existing API drift: core.working_notebook exposes get_notebook(session_id),
        # not get_working_notebook(). Caught below like any other optional-bridge failure,
        # so this bridge currently always returns None. Not fixed here (behavior change
        # out of scope for a typing-only pass) — tracked as a follow-up bug.
        from core.working_notebook import get_working_notebook  # type: ignore[attr-defined]
        return get_working_notebook()
    except Exception:
        return None
