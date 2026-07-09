"""🪞 core/essence/mirror.py — Mirror bridge"""
from __future__ import annotations


def get_mirror_bridge():
    """Мост к working_notebook.py. Файл не перемещён."""
    try:
        from core.working_notebook import get_working_notebook
        return get_working_notebook()
    except Exception:
        return None
