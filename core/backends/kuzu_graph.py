"""
DEPRECATED: Kuzu заархивирован Kùzu Inc. в октябре 2025 года.

Используйте LadybugDB — поддерживаемый API-совместимый форк: STORAGE_BACKEND=ladybug.
Этот модуль оставлен как тонкий слой совместимости: KuzuGraphStore →
LadybugGraphStore (старые импорты не ломаются, но перенаправляются на LadybugDB).
"""

from __future__ import annotations

import warnings

from core.backends.ladybug_graph import LadybugGraphStore

warnings.warn(
    "core.backends.kuzu_graph устарел: Kuzu заархивирован (окт. 2025). "
    "Используйте LadybugGraphStore или STORAGE_BACKEND=ladybug.",
    DeprecationWarning,
    stacklevel=2,
)


class KuzuGraphStore(LadybugGraphStore):
    """Совместимость со старым кодом: перенаправляет на LadybugDB (форк Kuzu)."""


__all__ = ["KuzuGraphStore"]
