"""👁️ core/essence/observer_bridge.py — Observer bridge"""
from __future__ import annotations
from typing import Any, Dict, Optional


def get_observer_bridge():
    """Мост к observer.py. Файл не перемещён."""
    try:
        from core.observer import get_observer
        return get_observer()
    except Exception:
        return None
