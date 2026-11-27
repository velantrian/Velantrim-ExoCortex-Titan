"""Passive Observer callable bridge; no additional Observer instance/authority."""
from __future__ import annotations


def get_observer_bridge():
    """Return the existing observe function; dependency failures remain visible."""
    from core.observer import observe
    return observe
