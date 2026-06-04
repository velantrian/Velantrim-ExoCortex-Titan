"""LocalMind: local language layer for Velantrim console."""

from .answer_composer import build_offline_reply
from .intent_router import intent_for

__all__ = ["build_offline_reply", "intent_for"]

