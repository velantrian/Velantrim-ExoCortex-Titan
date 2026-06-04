"""
📓 core/working_notebook.py — Exocortex Mirror / Working Notebook (RFC-0081 P0)
==============================================================================

«Думай, как я»: молчаливый рабочий блокнот, который в реальном времени держит
МОДЕЛЬ ТЕКУЩЕГО МЫШЛЕНИЯ пользователя — маленькими блоками сути (цель, ограничения,
приоритеты, материалы, открытые вопросы) — ДО retrieval и ответа.

Канон (RFC-0081):
  • Раздел 8 Decay: «затухание влияет на ВНИМАНИЕ, не на истину» — turn-based, по типу блока.
  • Раздел 9 Reactivation: повторное касание темы возвращает блок в фокус (mention boost).
  • Инварианты: `truth_status = USER_STATED` (мысль ≠ факт мира); НЕ пишет в L3; не меняет truth.

Дисциплина: аддитивно, за флагом `ENABLE_WORKING_NOTEBOOK` (по умолчанию ВЫКЛ), без LLM,
без мутаций L3. Это «тёплый» слой понимания пользователя НАД холодной памятью-истиной.

P0: детерминированная эвристическая экстракция + decay/reactivation/состояния/директива.
Семантическая экстракция и concept-match реактивация (по эмбеддингам) — P1.
"""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Раздел 8: λ затухания по типу блока (turn-based) ──
_LAMBDA = {
    "protected": 0.00, "constraint": 0.03, "priority": 0.05, "goal": 0.06,
    "open_question": 0.10, "material": 0.12, "topic": 0.12, "detail": 0.20,
}
_BASE_PRIORITY = {
    "goal": 0.92, "constraint": 0.90, "priority": 0.85, "material": 0.72,
    "open_question": 0.70, "topic": 0.60, "detail": 0.50,
}
# Пороги состояний (Раздел 8.3)
_ACTIVE, _WARM, _COLD = 0.70, 0.40, 0.15


def is_working_notebook_enabled() -> bool:
    return os.getenv("ENABLE_WORKING_NOTEBOOK", "false").strip().lower() in {"1", "true", "yes", "on"}


class BlockType(str, Enum):
    GOAL = "goal"
    CONSTRAINT = "constraint"
    PRIORITY = "priority"
    MATERIAL = "material"
    OPEN_QUESTION = "open_question"
    TOPIC = "topic"
    DETAIL = "detail"


def _state_of(score: float) -> str:
    if score >= _ACTIVE:
        return "ACTIVE"
    if score >= _WARM:
        return "WARM"
    if score >= _COLD:
        return "COLD"
    return "DORMANT"


def _slug(text: str) -> str:
    return re.sub(r"\s+", "_", re.sub(r"[^\w\s]", " ", (text or "").lower()).strip())[:48]


@dataclass
class MentalBlock:
    id: str
    type: str
    text: str
    base_priority: float
    current_score: float
    state: str = "ACTIVE"
    missed_turns: int = 0
    last_touched_turn: int = 0
    access_count: int = 1
    protected: bool = False
    truth_status: str = "USER_STATED"   # мысль пользователя, НЕ факт мира

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "text": self.text,
            "score": round(self.current_score, 3), "state": self.state,
            "missed_turns": self.missed_turns, "access_count": self.access_count,
            "protected": self.protected, "truth_status": self.truth_status,
        }


# ── эвристическая классификация сегмента речи ──
_CUES = [
    (BlockType.CONSTRAINT, r"бюджет|млн|тыс|руб|\$|budget|cost|не более|не дороже|максимум|"
                           r"нельзя|без |не хочу|avoid|must|обязательн|только |no more than"),
    (BlockType.PRIORITY,   r"важн|приоритет|главн|в первую очередь|important|priority|critical"),
    (BlockType.OPEN_QUESTION, r"\?|почему|зачем|как |какой|какая|сколько|where|why|how|what|which|when"),
    (BlockType.MATERIAL,   r"дерев|брус|бревн|кирпич|бетон|металл|сталь|камень|wood|brick|concrete|steel|материал"),
    (BlockType.GOAL,       r"хочу|хотел бы|нужно|надо|постро|сделать|спроект|want|need|build|design|create|план"),
]


def _classify(segment: str) -> BlockType:
    low = segment.lower()
    for btype, pat in _CUES:
        if re.search(pat, low):
            return btype
    return BlockType.TOPIC


def _segments(text: str) -> list[str]:
    raw = re.split(r"[,.;!?\n]+|\bи\b|\bа\b|\bно\b", text or "")
    return [s.strip() for s in raw if len(s.strip().split()) >= 2]


def extract_blocks(text: str, turn: int) -> list[MentalBlock]:
    """Грубая детерминированная экстракция блоков сути из сообщения (P0, без LLM)."""
    blocks: list[MentalBlock] = []
    seen = set()
    for seg in _segments(text):
        btype = _classify(seg)
        bid = f"{btype.value}:{_slug(seg)}"
        if bid in seen:
            continue
        seen.add(bid)
        bp = _BASE_PRIORITY[btype.value]
        blocks.append(MentalBlock(
            id=bid, type=btype.value, text=seg, base_priority=bp,
            current_score=bp, state=_state_of(bp), last_touched_turn=turn,
        ))
    return blocks


def _content_words(text: str) -> set:
    return {w for w in re.sub(r"[^\w\s]", " ", (text or "").lower()).split() if len(w) >= 3}


@dataclass
class WorkingNotebook:
    """Рабочий блокнот одной сессии. Не пишет в L3; держит мысль пользователя."""
    session_id: str = "session"
    turn: int = 0
    blocks: dict[str, MentalBlock] = field(default_factory=dict)
    core_goal: str = ""

    def update_from_message(self, text: str) -> None:
        self.turn += 1
        new_blocks = extract_blocks(text, self.turn)
        touched_ids = set()

        for nb in new_blocks:
            existing = self._match(nb)
            if existing is not None:
                # Раздел 9: реактивация (mention boost) — вернуть в фокус
                existing.current_score = min(1.0, max(existing.current_score, existing.base_priority))
                existing.missed_turns = 0
                existing.last_touched_turn = self.turn
                existing.access_count += 1
                existing.state = _state_of(existing.current_score)
                touched_ids.add(existing.id)
            else:
                nb.last_touched_turn = self.turn
                self.blocks[nb.id] = nb
                touched_ids.add(nb.id)

        # Раздел 8: затухание нетронутых блоков
        for bid, b in self.blocks.items():
            if bid in touched_ids or b.protected:
                continue
            b.missed_turns += 1
            lam = _LAMBDA.get(b.type, 0.12)
            b.current_score = b.base_priority * math.exp(-lam * b.missed_turns)
            b.state = _state_of(b.current_score)

        self._refresh_core_goal()

    def _match(self, nb: MentalBlock) -> MentalBlock | None:
        """Совпадение с существующим блоком: тот же id ИЛИ высокий лексический overlap (P0)."""
        if nb.id in self.blocks:
            return self.blocks[nb.id]
        nw = _content_words(nb.text)
        if not nw:
            return None
        best, bb = 0.0, None
        for b in self.blocks.values():
            if b.type != nb.type:
                continue
            ow = _content_words(b.text)
            if not ow:
                continue
            jac = len(nw & ow) / len(nw | ow)
            if jac > best:
                best, bb = jac, b
        return bb if best >= 0.5 else None

    def _refresh_core_goal(self) -> None:
        goals = [b for b in self.blocks.values()
                 if b.type in ("goal", "priority") and b.state in ("ACTIVE", "WARM")]
        if goals:
            self.core_goal = max(goals, key=lambda b: b.current_score).text

    def active_blocks(self) -> list[MentalBlock]:
        order = {"ACTIVE": 0, "WARM": 1}
        return sorted(
            (b for b in self.blocks.values() if b.state in ("ACTIVE", "WARM")),
            key=lambda b: (order[b.state], -b.current_score),
        )

    def directive(self) -> str:
        """Короткая инструкция для основной LLM (только активные/тёплые блоки)."""
        act = self.active_blocks()
        if not act and not self.core_goal:
            return ""
        lines = [f"Текущая суть (USER_STATED): {self.core_goal or '—'}"]
        cons = [b.text for b in act if b.type == "constraint"]
        if cons:
            lines.append("Ограничения: " + "; ".join(cons))
        foc = [b.text for b in act if b.type not in ("constraint",)]
        if foc:
            lines.append("В фокусе: " + "; ".join(foc[:5]))
        lines.append("Отвечай в рамках этой модели; не нарушай ограничения. Это мысль пользователя, не факт мира.")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn": self.turn,
            "core_goal": self.core_goal,
            "blocks": [b.to_dict() for b in self.blocks.values()],
        }


# ── Реестр блокнотов по сессиям (для wiring в /query) ──
_SESSIONS: dict[str, WorkingNotebook] = {}


def get_notebook(session_id: str) -> WorkingNotebook:
    nb = _SESSIONS.get(session_id)
    if nb is None:
        nb = WorkingNotebook(session_id=session_id)
        _SESSIONS[session_id] = nb
    return nb


def notebook_directive_for(session_id: str, message: str) -> str:
    """Обновить блокнот сессии новым сообщением и вернуть директиву для LLM («думай, как я»)."""
    nb = get_notebook(session_id)
    nb.update_from_message(message)
    return nb.directive()


def reset_notebooks() -> None:
    """Очистить все сессионные блокноты (для тестов / нового запуска)."""
    _SESSIONS.clear()


__all__ = [
    "BlockType",
    "MentalBlock",
    "WorkingNotebook",
    "extract_blocks",
    "get_notebook",
    "is_working_notebook_enabled",
    "notebook_directive_for",
    "reset_notebooks",
]
