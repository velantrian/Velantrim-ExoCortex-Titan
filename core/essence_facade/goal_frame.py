"""🎯 core/essence/goal_frame.py — GoalFrame bridge"""
from __future__ import annotations


def get_goal_frame_bridge():
    """Мост к goal_stack.py + goal_frame.py. Файлы не перемещены."""
    try:
        from core.goal_stack import get_goal_stack
        return get_goal_stack()
    except Exception:
        return None
