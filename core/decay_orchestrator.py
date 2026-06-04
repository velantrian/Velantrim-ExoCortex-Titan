"""
DecayOrchestrator — единая цепочка затухания (V9 Contract #22).

Приоритет: ESM → DAAD → FSRS → Vintage → Salience.
Разрешает интерференцию FSRS + ACT-R + Hebbian + DAAD + Salience
в одном детерминированном пайплайне (0 LLM).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from core.daad import DomainResolver
from core.esm import EpistemicState
from core.fsrs import FSRSParams, decay_edge_weight
from core.salience_fsrs import effective_decay_weight, should_protect_from_decay
from core.vintage_decay import VintageDecayCalculator

logger = logging.getLogger(__name__)

PRIORITY_CHAIN = ("ESM", "DAAD", "FSRS", "Vintage", "Salience")


@dataclass
class DecayTarget:
    """Цель decay (Velum synapse, Entity importance, …)."""

    weight: float
    t_days: float
    stability_days: float = 7.0
    salience_weight: float = 1.0
    epistemic_state: str | None = None
    domain_vector: dict[str, float] | None = None
    content_domain: str | None = None
    source_year: int | None = None
    decay_lambda: float | None = None
    min_weight: float = 0.0
    max_weight: float = 1.0
    # Heterogeneous decay: "stable" ages slowly, "volatile" fast, "medium" = unchanged.
    volatility_class: str = "medium"


@dataclass
class DecayOutcome:
    """Результат одного прохода orchestrator."""

    new_weight: float
    skipped: bool = False
    skip_reason: str | None = None
    stages_applied: list[str] = field(default_factory=list)
    stability_effective: float = 7.0
    floor_eff: float = 0.0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecayBatchStats:
    """Агрегат batch decay."""

    processed: int = 0
    decayed: int = 0
    unchanged: int = 0
    skipped_esm: int = 0
    skipped_salience: int = 0
    daad_fallback: int = 0
    floor_applied: int = 0
    avg_weight_before: float = 0.0
    avg_weight_after: float = 0.0


class DecayOrchestrator:
    """
    V9 priority chain для synapse / importance decay.

    ESM: ImmutableCore → полный skip.
    DAAD: S_eff = S / λ_daad.
    Vintage: дополнительный λ по домену/возрасту.
    FSRS: power-law retention × weight.
    Salience: защита высокого salience (I26).
    """

    def __init__(self, fsrs: FSRSParams | None = None) -> None:
        self.fsrs = fsrs or FSRSParams()

    def compute(
        self,
        target: DecayTarget,
        *,
        prune_below: float | None = None,
    ) -> DecayOutcome:
        old_w = float(target.weight)
        stages: list[str] = []
        detail: dict[str, Any] = {}

        if target.t_days <= 0.0:
            return DecayOutcome(
                new_weight=old_w,
                skipped=True,
                skip_reason="t_zero",
                stages_applied=["ESM"],
                detail={"t_days": target.t_days},
            )

        # ── 1. ESM ──
        state = (target.epistemic_state or "").strip()
        if state == EpistemicState.IMMUTABLE_CORE.value:
            return DecayOutcome(
                new_weight=old_w,
                skipped=True,
                skip_reason="esm_immutable",
                stages_applied=["ESM"],
            )
        stages.append("ESM")
        detail["epistemic_state"] = state or None

        # ── 5. Salience (ранний skip = полная защита) ──
        if should_protect_from_decay(target.salience_weight):
            return DecayOutcome(
                new_weight=old_w,
                skipped=True,
                skip_reason="salience_protected",
                stages_applied=stages + ["Salience"],
                detail={"salience_weight": target.salience_weight},
            )

        # ── 2. DAAD ──
        daad = DomainResolver.resolve(target.domain_vector)
        stages.append("DAAD")
        if daad.used_fallback:
            detail["daad_fallback"] = True

        stability = float(target.stability_days or 7.0)
        stability_eff = stability / max(0.01, daad.lambda_eff)
        floor_eff = daad.floor_eff
        detail["lambda_daad"] = daad.lambda_eff

        # ── 4. Vintage (перед FSRS — масштабирует S) ──
        vintage = VintageDecayCalculator.resolve(
            content_domain=target.content_domain,
            source_year=target.source_year,
            decay_lambda=target.decay_lambda,
            epistemic_state=state or None,
        )
        stages.append("Vintage")
        stability_eff = stability_eff / max(0.01, vintage.lambda_eff)
        detail["lambda_vintage"] = vintage.lambda_eff
        detail["vintage_domain"] = vintage.domain

        # ── Heterogeneous volatility (default "medium" ⇒ ×1.0, no change) ──
        vclass = getattr(target, "volatility_class", "medium") or "medium"
        if vclass != "medium":
            from core.fsrs import volatility_stability

            stability_eff = volatility_stability(stability_eff, vclass)
            detail["volatility_class"] = vclass

        # ── 3. FSRS ──
        stages.append("FSRS")
        raw_new = decay_edge_weight(
            old_w,
            t_days=target.t_days,
            stability=stability_eff,
            params=self.fsrs,
        )
        new_w = max(floor_eff, raw_new)
        if new_w < floor_eff + 1e-12 and raw_new < floor_eff:
            detail["floor_applied"] = True

        new_w = max(target.min_weight, min(target.max_weight, new_w))

        # ── Salience (финальная коррекция) ──
        stages.append("Salience")
        final_w = effective_decay_weight(old_w, new_w, target.salience_weight)

        if prune_below is not None and final_w < prune_below:
            detail["below_prune"] = True

        return DecayOutcome(
            new_weight=final_w,
            skipped=False,
            stages_applied=stages,
            stability_effective=stability_eff,
            floor_eff=floor_eff,
            detail=detail,
        )

    def apply_batch(
        self,
        targets: list[DecayTarget],
        *,
        prune_below: float | None = None,
    ) -> tuple[list[DecayOutcome], DecayBatchStats]:
        if not targets:
            return [], DecayBatchStats()

        weights_before = [t.weight for t in targets]
        outcomes: list[DecayOutcome] = []
        stats = DecayBatchStats(processed=len(targets))

        for target in targets:
            out = self.compute(target, prune_below=prune_below)
            outcomes.append(out)

            if out.skipped:
                if out.skip_reason == "esm_immutable":
                    stats.skipped_esm += 1
                elif out.skip_reason == "salience_protected":
                    stats.skipped_salience += 1
                else:
                    stats.unchanged += 1
                continue

            if abs(out.new_weight - target.weight) > 1e-12:
                stats.decayed += 1
            else:
                stats.unchanged += 1

            if out.detail.get("daad_fallback"):
                stats.daad_fallback += 1
            if out.detail.get("floor_applied"):
                stats.floor_applied += 1

        weights_after = [o.new_weight for o in outcomes if not o.skipped]
        stats.avg_weight_before = sum(weights_before) / len(weights_before)
        stats.avg_weight_after = (
            sum(weights_after) / len(weights_after) if weights_after else 0.0
        )
        return outcomes, stats


_default_orchestrator: DecayOrchestrator | None = None


def get_decay_orchestrator() -> DecayOrchestrator:
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = DecayOrchestrator()
    return _default_orchestrator


def is_decay_orchestrator_enabled() -> bool:
    from core.feature_config import get_config

    return bool(get_config().app.enable_decay_orchestrator)


__all__ = [
    "DecayBatchStats",
    "DecayOrchestrator",
    "DecayOutcome",
    "DecayTarget",
    "PRIORITY_CHAIN",
    "get_decay_orchestrator",
    "is_decay_orchestrator_enabled",
]
