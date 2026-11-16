"""Session-scoped WorkingNotebook bridge."""
from __future__ import annotations


def get_mirror_bridge(session_id: str = "session"):
    """Return the existing notebook for the explicitly selected session."""
    from core.working_notebook import get_notebook
    return get_notebook(session_id)
