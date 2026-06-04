"""
ConsolidationEngine — ночная/micro-batch консолидация Observed → Validated.

Спринт 1 (system docx v2). Вызывается из SleepTimeWorker и POST /memory/consolidate.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.storage import GraphStore

logger = logging.getLogger(__name__)


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class ConsolidationReport:
    scanned: int = 0
    promoted_validated: int = 0
    promoted_hypothesized: int = 0
    skipped_low_confidence: int = 0
    skipped_short_claim: int = 0
    errors: int = 0
    fact_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "promoted_validated": self.promoted_validated,
            "promoted_hypothesized": self.promoted_hypothesized,
            "promoted_total": self.promoted_validated + self.promoted_hypothesized,
            "skipped_low_confidence": self.skipped_low_confidence,
            "skipped_short_claim": self.skipped_short_claim,
            "errors": self.errors,
            "fact_ids": self.fact_ids[:50],
        }


class ConsolidationEngine:
    """Micro-batch: Observed с высоким confidence → Validated (или Hypothesized)."""

    def __init__(
        self,
        store: GraphStore,
        *,
        min_confidence: float | None = None,
        min_claim_len: int = 8,
        max_batch: int | None = None,
        prefer_validated: bool = True,
    ) -> None:
        self._store = store
        self.min_confidence = (
            min_confidence
            if min_confidence is not None
            else _float_env("CONSOLIDATION_MIN_CONFIDENCE", 0.75)
        )
        self.min_claim_len = min_claim_len
        self.max_batch = max_batch if max_batch is not None else _int_env(
            "CONSOLIDATION_MAX_BATCH", 50
        )
        self.prefer_validated = prefer_validated

    def run(self) -> ConsolidationReport:
        report = ConsolidationReport()
        try:
            observed = self._store.get_all_facts(epistemic_state="Observed")
        except Exception as exc:  # noqa: BLE001
            logger.error("ConsolidationEngine: get_all_facts failed: %s", exc)
            report.errors += 1
            return report

        report.scanned = len(observed)
        batch = observed[: self.max_batch]

        for fact in batch:
            fact_id = fact.get("fact_id")
            if not fact_id:
                continue
            claim = (fact.get("claim") or "").strip()
            conf = float(fact.get("confidence", 0.0))

            if len(claim) < self.min_claim_len:
                report.skipped_short_claim += 1
                continue
            if conf < self.min_confidence:
                report.skipped_low_confidence += 1
                continue

            target = "Validated" if self.prefer_validated else "Hypothesized"
            try:
                ok = self._store.transition_esm(
                    fact_id, target, by="consolidation_engine"
                )
                if ok:
                    if target == "Validated":
                        report.promoted_validated += 1
                    else:
                        report.promoted_hypothesized += 1
                    report.fact_ids.append(fact_id)
                    self._refresh_checksum(fact_id)
            except ValueError:
                try:
                    ok = self._store.transition_esm(
                        fact_id, "Hypothesized", by="consolidation_engine"
                    )
                    if ok:
                        report.promoted_hypothesized += 1
                        report.fact_ids.append(fact_id)
                        self._refresh_checksum(fact_id)
                except Exception as exc2:  # noqa: BLE001
                    logger.debug("consolidation %s: %s", fact_id, exc2)
                    report.errors += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("consolidation %s: %s", fact_id, exc)
                report.errors += 1

        logger.info("ConsolidationEngine: %s", report.to_dict())
        return report

    def _refresh_checksum(self, fact_id: str) -> None:
        """Обновить content_checksum после смены epistemic_state."""
        from core.fact_integrity import attach_integrity_metadata

        fact = self._store.get_fact(fact_id)
        if not fact:
            return
        meta = attach_integrity_metadata(
            fact.get("metadata") or {},
            claim=fact.get("claim", ""),
            source=fact.get("source", "unknown"),
            confidence=float(fact.get("confidence", 0.5)),
            epistemic_state=fact.get("epistemic_state", "Observed"),
        )
        fact["metadata"] = meta
        self._store.store_fact(fact)


def run_consolidation(store: GraphStore | None = None) -> Any:
    """
    Синхронный запуск (SleepTimeWorker, API).

    Диспетчер по флагам (по убыванию приоритета, все по умолчанию ВЫКЛ):
      • ENABLE_SLEEP_CONSOLIDATION → полный цикл (corroboration→promotion→contradiction→decay);
      • ENABLE_GRADUATED_PROMOTION → только градуированный промоушен;
      • иначе → наивный ConsolidationEngine (поведение по умолчанию, fallback).

    Все пути возвращают объект с .to_dict() — вызыватели (SleepTimeWorker, API)
    используют только его, поэтому смена реализации для них прозрачна.
    """
    if store is None:
        from core.memory import _GLOBAL_STORE

        store = _GLOBAL_STORE

    from core.sleep_consolidation import is_sleep_consolidation_enabled

    if is_sleep_consolidation_enabled():
        from core.sleep_consolidation import run_sleep_consolidation

        logger.info("run_consolidation: SLEEP consolidation loop ENABLED")
        return run_sleep_consolidation(store)

    from core.promotion_policy import is_graduated_promotion_enabled

    if is_graduated_promotion_enabled():
        from core.promotion_policy import run_graduated_promotion

        logger.info("run_consolidation: graduated promotion ENABLED")
        return run_graduated_promotion(store)

    return ConsolidationEngine(store).run()


__all__ = ["ConsolidationEngine", "ConsolidationReport", "run_consolidation"]
