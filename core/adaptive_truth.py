"""
⚖️ core/adaptive_truth.py — Adaptive Truth Thresholds (V8.7 Titan)

Динамические пороги TruthGate. Вместо фиксированных CognitiveModes — пороги
меняются автоматически по контексту темы и реакции пользователя.

Зелёная зона (доверие):
    созидательные темы (экология, здоровье, образование) + пользователь доволен
    → confidence порог снижается с 0.7 до 0.5
    → Hypothesized факты допускаются

Красная зона (верификация):
    точные науки, медицина, право
    → confidence порог поднимается до 0.9
    → требуется 5+ evidence

Инварианты:
    I-AT1: Адаптация меняет ТОЛЬКО пороги TruthGate. Не truth_status фактов.
    I-AT2: Никогда не опускает порог ниже 0.3 (даже в зелёной зоне).
    I-AT3: Никогда не поднимает порог выше 0.95 (даже в красной зоне).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.adaptive_truth")

# ─── Тематические зоны ────────────────────────────────────────────────────────

GREEN_DOMAINS = {
    "ecology", "environment", "sustainability", "health", "wellness",
    "education", "art", "creativity", "music", "literature",
    "gardening", "cooking", "sports", "travel", "community",
    "экология", "здоровье", "образование", "искусство", "творчество",
}

RED_DOMAINS = {
    "medicine", "pharmacology", "surgery", "diagnosis",
    "law", "legal", "jurisdiction", "contracts",
    "physics", "chemistry", "mathematics", "formal_science",
    "finance", "accounting", "taxation",
    "медицина", "право", "физика", "химия", "математика", "финансы",
    "safety", "security", "critical_infrastructure",
}


@dataclass
class AdaptiveThreshold:
    """Динамический порог TruthGate."""
    min_confidence: float = 0.7
    min_evidence: int = 2
    allow_hypothesized: bool = False
    zone: str = "neutral"
    reason: str = ""


class AdaptiveTruthEngine:
    """
    Движок адаптивных порогов TruthGate.

    Использование:
        engine = AdaptiveTruthEngine()

        # Перед TruthGate.evaluate():
        threshold = engine.get_threshold(fact, domain="ecology")
        if fact.confidence >= threshold.min_confidence:
            ...
    """

    # Базовые пороги
    DEFAULT = AdaptiveThreshold(0.7, 2, False, "neutral")
    GREEN = AdaptiveThreshold(0.45, 1, True, "green", "созидательная тема — доверие")
    RED = AdaptiveThreshold(0.85, 4, False, "red", "точная наука/медицина/право — строгость")

    def __init__(self):
        self._domain_history: Dict[str, List[float]] = {}  # domain → user satisfaction scores
        self._adaptation_count = 0

    def get_threshold(
        self,
        *,
        domain: Optional[str] = None,
        claim_type: Optional[str] = None,
        user_satisfaction: Optional[float] = None,
    ) -> AdaptiveThreshold:
        """
        Получить порог для конкретного контекста.

        Args:
            domain: домен факта (ecology, medicine, ...).
            claim_type: тип утверждения (WORLD_FACT, USER_EXPERIENCE, ...).
            user_satisfaction: удовлетворённость пользователя (0..1), если известна.

        Returns:
            AdaptiveThreshold с min_confidence, min_evidence, allow_hypothesized.
        """
        # 1. Научные/строгие домены → красная зона
        if domain and self._is_red_domain(domain):
            th = self._clone(self.RED)
            th = self._apply_satisfaction(th, domain, user_satisfaction)
            return th

        # 2. Созидательные домены → зелёная зона
        if domain and self._is_green_domain(domain):
            th = self._clone(self.GREEN)
            th = self._apply_satisfaction(th, domain, user_satisfaction)
            return th

        # 3. USER_EXPERIENCE / EMOTION → мягче
        if claim_type in ("USER_EXPERIENCE", "EMOTION", "USER_STATED"):
            return AdaptiveThreshold(
                min_confidence=0.35,
                min_evidence=1,
                allow_hypothesized=True,
                zone="personal",
                reason="личный опыт — мягкий порог",
            )

        # 4. Default
        return self.DEFAULT

    def record_satisfaction(self, domain: str, score: float) -> None:
        """
        Записать удовлетворённость пользователя для домена.
        Используется для долгосрочной адаптации порогов.
        """
        s = max(0.0, min(1.0, score))
        self._domain_history.setdefault(domain, []).append(s)
        if len(self._domain_history[domain]) > 50:
            self._domain_history[domain] = self._domain_history[domain][-50:]
        self._adaptation_count += 1

    def get_domain_trust(self, domain: str) -> float:
        """Уровень доверия к домену (0..1) на основе истории удовлетворённости."""
        history = self._domain_history.get(domain, [])
        if not history:
            return 0.5
        return round(sum(history) / len(history), 2)

    def _is_red_domain(self, domain: str) -> bool:
        d = domain.lower().strip()
        return d in RED_DOMAINS or any(rd in d for rd in RED_DOMAINS if len(rd) > 3)

    def _is_green_domain(self, domain: str) -> bool:
        d = domain.lower().strip()
        return d in GREEN_DOMAINS or any(gd in d for gd in GREEN_DOMAINS if len(gd) > 3)

    def _apply_satisfaction(
        self, th: AdaptiveThreshold, domain: str, satisfaction: Optional[float]
    ) -> AdaptiveThreshold:
        """Скорректировать порог на основе реакции пользователя."""
        if satisfaction is None:
            return th

        trust = self.get_domain_trust(domain)
        # FIX (Claude audit 2026-07-28, Low): RED zone (medicine/law/physics/
        # finance/security) must never be softened by user satisfaction — a
        # user being happy with a wrong claim in a high-stakes domain is
        # exactly the signal this zone exists to resist. Dissatisfaction may
        # still tighten it further (branch below is unaffected).
        # Если пользователь доволен → ещё мягче (кроме red-зоны)
        if satisfaction > 0.7 and trust > 0.6 and th.zone != "red":
            th.min_confidence = max(0.35, th.min_confidence - 0.1)
            th.reason += " + пользователь доволен"
        # Если недоволен → жёстче
        elif satisfaction < 0.3:
            th.min_confidence = min(0.95, th.min_confidence + 0.1)
            th.reason += " + пользователь недоволен"

        return th

    def _clone(self, th: AdaptiveThreshold) -> AdaptiveThreshold:
        return AdaptiveThreshold(th.min_confidence, th.min_evidence, th.allow_hypothesized, th.zone, th.reason)

    def stats(self) -> Dict[str, Any]:
        return {
            "adaptation_count": self._adaptation_count,
            "tracked_domains": len(self._domain_history),
            "domain_trust": {
                d: round(sum(h) / len(h), 2)
                for d, h in list(self._domain_history.items())[:10]
            },
        }


# Глобальный экземпляр
_engine: Optional[AdaptiveTruthEngine] = None


def get_adaptive_truth_engine() -> AdaptiveTruthEngine:
    global _engine
    if _engine is None:
        _engine = AdaptiveTruthEngine()
    return _engine


__all__ = ["AdaptiveThreshold", "AdaptiveTruthEngine", "get_adaptive_truth_engine"]
