"""
GoalFrame - explicit goal extraction for Velantrim orchestration.

This module is intentionally small and dependency-free. It does not replace
the existing intent router. It creates a stable contract that other layers
can use before retrieval, routing, compute selection, and answer generation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GoalIntent(str, Enum):
    FACT_LOOKUP = "fact_lookup"
    EXPLAIN = "explain"
    COMPARE = "compare"
    PLAN = "plan"
    VERIFY = "verify"
    CREATE = "create"
    ANALYZE = "analyze"
    PERSONAL = "personal"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class GoalFrame:
    query: str
    intent: GoalIntent = GoalIntent.UNKNOWN
    risk_level: RiskLevel = RiskLevel.LOW
    domain_hint: str = "general"
    output_style: str = "balanced"
    constraints: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_verification(self) -> bool:
        return self.risk_level == RiskLevel.HIGH or self.intent == GoalIntent.VERIFY

    @property
    def prefers_short_answer(self) -> bool:
        return self.output_style in {"short", "summary"}

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "intent": self.intent.value,
            "risk_level": self.risk_level.value,
            "domain_hint": self.domain_hint,
            "output_style": self.output_style,
            "constraints": list(self.constraints),
            "reasons": list(self.reasons),
            "metadata": dict(self.metadata),
        }


_TOKEN_RE = re.compile(r"[\w\-]{3,}", re.UNICODE)

_HIGH_RISK_WORDS = {
    "medical", "medicine", "doctor", "legal", "law", "lawyer", "finance",
    "investment", "diagnosis", "treatment", "gdpr", "security", "password",
    "медицина", "врач", "диагноз", "лечение", "закон", "юрист", "финансы",
    "инвестиции", "безопасность", "пароль", "gdpr",
}

_DOMAIN_WORDS = {
    "science": {"science", "research", "paper", "arxiv", "biology", "physics",
                "наука", "исследование", "биология", "физика"},
    "engineering": {"architecture", "api", "server", "runtime", "code",
                    "архитектура", "код", "сервер", "модуль"},
    "personal": {"я", "мой", "моя", "мне", "память", "лично", "personal"},
}


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")}


def _has_any(tokens: set[str], words: set[str]) -> bool:
    return bool(tokens & words)


def infer_goal_frame(query: str, metadata: dict[str, Any] | None = None) -> GoalFrame:
    """Infer a conservative GoalFrame from a user query."""
    text = query or ""
    lower = text.lower()
    toks = _tokens(lower)
    reasons: list[str] = []
    constraints: list[str] = []

    intent = GoalIntent.UNKNOWN
    if any(x in lower for x in ("проверь", "верно ли", "правда ли", "verify", "audit")):
        intent = GoalIntent.VERIFY
        reasons.append("verification marker")
    elif any(x in lower for x in ("сравни", "compare", "versus", " vs ")):
        intent = GoalIntent.COMPARE
        reasons.append("comparison marker")
    elif any(
        x in lower
        for x in (
            "объясни",
            "объясните",
            "поясни",
            "поясните",
            "почему",
            "зачем",
            "как работает",
            "explain",
            "why",
            "how does",
        )
    ):
        intent = GoalIntent.EXPLAIN
        reasons.append("explanation marker")
    elif any(x in lower for x in ("сделай", "добавь", "реализуй", "план", "roadmap", "implement")):
        intent = GoalIntent.PLAN
        reasons.append("action/planning marker")
    elif any(x in lower for x in ("создай", "напиши", "generate", "create")):
        intent = GoalIntent.CREATE
        reasons.append("creation marker")
    elif any(x in lower for x in ("аудит", "анализ", "analyze", "review")):
        intent = GoalIntent.ANALYZE
        reasons.append("analysis marker")
    elif any(x in lower for x in ("что такое", "define", "кто", "где", "когда")):
        intent = GoalIntent.FACT_LOOKUP
        reasons.append("fact lookup marker")

    risk = RiskLevel.LOW
    if _has_any(toks, _HIGH_RISK_WORDS):
        risk = RiskLevel.HIGH
        reasons.append("high-risk domain marker")
        constraints.append("require evidence and trace")
    elif intent in {GoalIntent.VERIFY, GoalIntent.ANALYZE, GoalIntent.COMPARE}:
        risk = RiskLevel.MEDIUM

    domain = "general"
    for name, words in _DOMAIN_WORDS.items():
        if _has_any(toks, words):
            domain = name
            reasons.append(f"domain hint: {name}")
            break

    style = "balanced"
    if any(x in lower for x in ("коротко", "кратко", "по сути", "summary", "short")):
        style = "short"
        reasons.append("short answer requested")
    elif any(x in lower for x in ("глубоко", "подробно", "deep", "detailed")):
        style = "deep"
        reasons.append("deep answer requested")

    return GoalFrame(
        query=text,
        intent=intent,
        risk_level=risk,
        domain_hint=domain,
        output_style=style,
        constraints=constraints,
        reasons=reasons,
        metadata=metadata or {},
    )


__all__ = [
    "GoalFrame",
    "GoalIntent",
    "RiskLevel",
    "infer_goal_frame",
]
