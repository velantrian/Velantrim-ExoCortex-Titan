"""
DAAD — Domain-Aware Attention & Decay (HYPERIA-1, RFC0017).

Меняет только λ_eff и floor_eff по domain_vector узла (I66).
Не трогает ESM / truth_status.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DOMAIN_CONFIG: dict[str, dict[str, float]] = {
    "active_project": {"lambda": 0.001, "floor": 0.85},
    "personal_pref": {"lambda": 0.004, "floor": 0.60},
    "domain_knowledge": {"lambda": 0.006, "floor": 0.50},
    "completed_project": {"lambda": 0.008, "floor": 0.40},
    "casual_chat": {"lambda": 0.150, "floor": 0.00},
    "general_question": {"lambda": 0.200, "floor": 0.00},
}

FALLBACK_LAMBDA = 0.05
FALLBACK_FLOOR = 0.00


@dataclass(frozen=True)
class DecayParams:
    """Эффективные параметры затухания для узла."""

    lambda_eff: float
    floor_eff: float
    used_fallback: bool = False


class DomainResolver:
    """
    λ_eff = Σ(dᵢ × λᵢ), floor_eff = max(dᵢ × floorᵢ).
    domain_vector=None → fallback (I66).
    """

    @staticmethod
    def resolve(domain_vector: dict[str, float] | None) -> DecayParams:
        if not domain_vector:
            return DecayParams(
                lambda_eff=FALLBACK_LAMBDA,
                floor_eff=FALLBACK_FLOOR,
                used_fallback=True,
            )

        lambda_eff = 0.0
        floor_eff = 0.0
        total_weight = sum(
            w for w in domain_vector.values() if w and w > 0
        )

        if total_weight <= 0:
            return DecayParams(
                lambda_eff=FALLBACK_LAMBDA,
                floor_eff=FALLBACK_FLOOR,
                used_fallback=True,
            )

        for domain, weight in domain_vector.items():
            if weight <= 0:
                continue
            norm_weight = weight / total_weight
            cfg = DOMAIN_CONFIG.get(domain)
            if cfg is None:
                logger.warning("DomainResolver: неизвестный домен %r", domain)
                continue
            lambda_eff += norm_weight * cfg["lambda"]
            floor_eff = max(floor_eff, norm_weight * cfg["floor"])

        if lambda_eff == 0.0:
            return DecayParams(
                lambda_eff=FALLBACK_LAMBDA,
                floor_eff=FALLBACK_FLOOR,
                used_fallback=True,
            )

        return DecayParams(lambda_eff=lambda_eff, floor_eff=floor_eff)


__all__ = [
    "DOMAIN_CONFIG",
    "DecayParams",
    "DomainResolver",
    "FALLBACK_FLOOR",
    "FALLBACK_LAMBDA",
]
