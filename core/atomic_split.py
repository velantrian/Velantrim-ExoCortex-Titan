"""
🔬 core/atomic_split.py — AtomicSplit (V8.7 Titan, из Crystal I91)

Один смысл = один факт. Multi-proposition content разбивается на атомарные утверждения
ПЕРЕД TruthGate. Это предотвращает «двойные» факты, где одно утверждение истинно,
а второе — нет, но они хранятся в одном факте.

I91 (AtomicSplit): каждый элемент содержит ровно одну пропозицию.

Использование:
    splitter = AtomicSplitter()
    atoms = splitter.split("Вода кипит при 100°C. Лёд плавится при 0°C.")
    # → ["Вода кипит при 100°C.", "Лёд плавится при 0°C."]
"""

from __future__ import annotations

import re
from typing import List

# Разделители предложений (RU + EN)
_SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?…])\s+(?=[А-ЯЁA-Z])",
    re.UNICODE,
)

# Сложные союзы, которые могут объединять утверждения в одном предложении
_COMPLEX_CONJUNCTIONS = re.compile(
    r"\s+(?:и|а|но|однако|или|либо|при этом|в то время как|"
    r"and|but|or|however|while|whereas)\s+",
    re.UNICODE | re.IGNORECASE,
)

_MIN_ATOM_LENGTH = 10  # минимальная длина атомарного факта
_MAX_ATOMS = 50  # защита от бесконечного разбиения


class AtomicSplitter:
    """
    Разбивает текст на атомарные утверждения.

    Одно утверждение = одна пропозиция. Если в одном предложении
    два утверждения (через «и», «но», «а») — разбиваем.
    """

    def split(self, text: str, *, min_length: int = _MIN_ATOM_LENGTH) -> List[str]:
        """
        Разбить текст на атомарные факты.

        Args:
            text: исходный текст (может содержать несколько предложений).
            min_length: минимальная длина атома (короче — отбрасывается).

        Returns:
            Список атомарных утверждений.
        """
        if not text or not text.strip():
            return []

        # Шаг 1: разбить по границам предложений
        sentences: List[str] = []
        parts = _SENTENCE_BOUNDARY.split(text.strip())
        for part in parts:
            part = part.strip().rstrip(".").strip()
            if len(part) >= min_length:
                sentences.append(part)

        # Шаг 2: разбить сложные предложения по союзам
        atoms: List[str] = []
        for sentence in sentences:
            sub_parts = _COMPLEX_CONJUNCTIONS.split(sentence)
            if len(sub_parts) > 1:
                # Есть союзы — разбиваем
                for sub in sub_parts:
                    sub = sub.strip().rstrip(",;").strip()
                    if len(sub) >= min_length:
                        atoms.append(sub)
            else:
                atoms.append(sentence)

        # Защита от слишком большого количества
        return atoms[:_MAX_ATOMS]

    def split_and_validate(self, text: str) -> List[str]:
        """
        Разбить и проверить. Если разбиение не дало атомов —
        вернуть исходный текст как один атом (graceful fallback).
        """
        atoms = self.split(text)
        if not atoms and text and text.strip():
            return [text.strip()]
        return atoms


def atomic_split(text: str) -> List[str]:
    """Удобная функция: разбить текст на атомарные факты."""
    return AtomicSplitter().split_and_validate(text)


def is_atomic(text: str) -> bool:
    """Проверить, является ли текст атомарным (одна пропозиция)."""
    splitter = AtomicSplitter()
    atoms = splitter.split(text)
    return len(atoms) <= 1


__all__ = [
    "AtomicSplitter",
    "atomic_split",
    "is_atomic",
]
