"""
VintageDecayCalculator — адаптивный decay_lambda по домену/возрасту (I65, RFC0063).

Упрощённый MVP для DecayOrchestrator: λ по типу контента и ESM-модификатор.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC

from core.esm import EpistemicState

# Базовые λ по «винтажу» источника (книга/статья/чат)
DOMAIN_LAMBDA: dict[str, float] = {
    "physics": 0.001,
    "mathematics": 0.002,
    "programming": 0.15,
    "medicine": 0.05,
    "general": 0.08,
    "chat": 0.20,
}

DEFAULT_LAMBDA = 0.08

ESM_DECAY_MULTIPLIER: dict[str, float] = {
    EpistemicState.VALIDATED.value: 0.5,
    EpistemicState.HYPOTHESIZED.value: 2.0,
    EpistemicState.SUPPORTED.value: 1.0,
    EpistemicState.DEPRECATED.value: 2.5,
}


@dataclass(frozen=True)
class VintageDecayResult:
    lambda_eff: float
    domain: str
    esm_multiplier: float


class VintageDecayCalculator:
    """Вычисляет λ для затухания с учётом домена и ESM."""

    @staticmethod
    def base_lambda(
        *,
        content_domain: str | None = None,
        source_year: int | None = None,
        decay_lambda: float | None = None,
    ) -> float:
        if decay_lambda is not None and decay_lambda > 0:
            return float(decay_lambda)
        if content_domain:
            key = content_domain.strip().lower()
            if key in DOMAIN_LAMBDA:
                return DOMAIN_LAMBDA[key]
        if source_year is not None:
            from datetime import datetime

            age = max(0, datetime.now(UTC).year - int(source_year))
            if age >= 10:
                return min(0.25, DEFAULT_LAMBDA + age * 0.01)
        return DEFAULT_LAMBDA

    @classmethod
    def resolve(
        cls,
        *,
        content_domain: str | None = None,
        source_year: int | None = None,
        decay_lambda: float | None = None,
        epistemic_state: str | None = None,
    ) -> VintageDecayResult:
        base = cls.base_lambda(
            content_domain=content_domain,
            source_year=source_year,
            decay_lambda=decay_lambda,
        )
        esm_mult = 1.0
        if epistemic_state:
            esm_mult = ESM_DECAY_MULTIPLIER.get(epistemic_state, 1.0)
        lambda_eff = max(0.001, base * esm_mult)
        domain = (content_domain or "general").strip().lower()
        return VintageDecayResult(
            lambda_eff=lambda_eff,
            domain=domain,
            esm_multiplier=esm_mult,
        )


__all__ = [
    "DOMAIN_LAMBDA",
    "VintageDecayCalculator",
    "VintageDecayResult",
]
