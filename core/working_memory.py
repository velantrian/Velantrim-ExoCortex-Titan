"""
🧠 core/working_memory.py — Working Memory LRU Cache (V8.8)
============================================================

Биологический аналог: working memory — ограниченный буфер (~7±2 элемента),
который хранит недавно активированные элементы для мгновенного доступа.

Проблема: каждый retrieval идёт в SQLite. Для часто используемых фактов
это избыточно — они уже загружены, но каждый раз перечитываются.

Решение: LRU-кэш на 128 последних использованных фактов.
  - O(1) доступ к недавним фактам (без SQL)
  - Автоматическое вытеснение старых при превышении размера
  - Подключается к HybridRetriever как pre-fetch

Использование:
    wm = get_working_memory()             # синглтон
    wm.touch("fact_abc", fact_dict)       # факт использован → в кэш
    recent = wm.get_recent(10)            # последние 10
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.working_memory")

DEFAULT_CAP = 128


class WorkingMemory:
    """
    LRU-кэш недавно использованных фактов.

    Принцип: последний использованный — последний вытесненный.
    O(1) вставка, O(1) чтение, O(1) вытеснение.
    """

    def __init__(self, max_size: int = DEFAULT_CAP):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max = max_size
        self._hit_count = 0
        self._miss_count = 0

    def touch(self, fact_id: str, fact: Dict[str, Any]) -> None:
        """
        Отметить факт как использованный (переместить в конец LRU).

        Если факта нет в кэше — добавить. Если кэш полон — вытеснить старейший.
        """
        if not fact_id:
            return
        self._cache[fact_id] = fact
        self._cache.move_to_end(fact_id)
        if len(self._cache) > self._max:
            self._cache.popitem(last=False)

    def touch_batch(self, facts: list[Dict[str, Any]]) -> None:
        """Пакетное обновление (все факты из ответа)."""
        for f in facts:
            fid = str(f.get("fact_id", ""))
            if fid:
                self.touch(fid, f)

    def get(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить факт из кэша (O(1)).

        При попадании обновляет LRU-позицию.
        """
        if fact_id in self._cache:
            self._cache.move_to_end(fact_id)
            self._hit_count += 1
            return self._cache[fact_id]
        self._miss_count += 1
        return None

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Последние N использованных фактов (самые свежие)."""
        items = list(self._cache.values())
        return items[-n:][::-1]  # самые свежие первыми

    def contains(self, fact_id: str) -> bool:
        """Есть ли факт в кэше?"""
        return fact_id in self._cache

    def preload(self, facts: list[Dict[str, Any]]) -> None:
        """
        Предзагрузить факты в кэш (при старте, без вытеснения).
        Используется для «горячих» фактов (Ring Zero, часто используемые).
        """
        for f in facts:
            fid = str(f.get("fact_id", ""))
            if fid and fid not in self._cache:
                self._cache[fid] = f
                if len(self._cache) > self._max:
                    self._cache.popitem(last=False)

    def clear(self) -> None:
        """Очистить кэш."""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0

    def invalidate(self, fact_id: str) -> bool:
        """Удалить факт из кэша (при изменении в БД)."""
        if fact_id in self._cache:
            del self._cache[fact_id]
            return True
        return False

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def max_size(self) -> int:
        return self._max

    @property
    def hit_rate(self) -> float:
        total = self._hit_count + self._miss_count
        return self._hit_count / total if total > 0 else 0.0

    def stats(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "max_size": self._max,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": round(self.hit_rate, 4),
            "recent_ids": [fid for fid in list(self._cache.keys())[-5:][::-1]],
        }


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_memory: Optional[WorkingMemory] = None


def get_working_memory() -> WorkingMemory:
    global _memory
    if _memory is None:
        _memory = WorkingMemory()
    return _memory


def reset_working_memory() -> None:
    global _memory
    _memory = None


__all__ = [
    "WorkingMemory",
    "get_working_memory",
    "reset_working_memory",
]
