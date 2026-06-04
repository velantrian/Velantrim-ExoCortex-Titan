"""🧬 core/essence/causal.py — CausalGraph bridge"""
from __future__ import annotations
from typing import Any, Dict, Optional


def get_causal_bridge():
    """Мост к causal_graph.py. Файл не перемещён."""
    try:
        from core.causal_graph import get_causal_graph
        return get_causal_graph()
    except Exception:
        return None
