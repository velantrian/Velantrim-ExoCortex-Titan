"""
ConsolidationEngine — ночная/micro-batch консолидация Observed → Validated.

Спринт 1 (system docx v2). Вызывается из SleepTimeWorker и POST /memory/consolidate.

P0-D (belt-and-suspenders): confidence/claim-length/utility-gate ниже — это
pre-vetting этого движка, они решают, что факт СТАЛ КАНДИДАТОМ на Validated.
Финальный переход Supported → Validated идёт ТОЛЬКО через
store.validate_and_promote() (TruthGate + CAS) — см.
_promote_to_validated_via_truthgate(). Кандидат, прошедший локальные пороги,
но не TruthGate (например, недостаточно evidence_refs для своего
CognitiveMode), остаётся Supported, а не молча становится Validated.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.memory import SQLiteGraphStore

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
    # P0-D: a candidate that cleared this engine's own confidence/utility
    # gate but was rejected by validate_and_promote()'s TruthGate (e.g. too
    # few evidence_refs) — counted separately so scanned == promoted_total +
    # skipped_* + errors + rejected_by_truthgate always holds. The fact is
    # left at 'Supported' (see run()'s Supported rescan) and re-attempted
    # on the next run, not stranded.
    rejected_by_truthgate: int = 0
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
            "rejected_by_truthgate": self.rejected_by_truthgate,
            "fact_ids": self.fact_ids[:50],
        }


class ConsolidationEngine:
    """Micro-batch: Observed с высоким confidence → Validated (или Hypothesized)."""

    def __init__(
        self,
        store: SQLiteGraphStore,
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
        """
        Micro-batch консолидация с utility-gating (V8.8).

        Фазы:
          1. Scan – найти Observed факты
          2. Pre-check – confidence, длина claim
          3. Utility gate (NEW) – использовался ли? связан ли с другими?
          4. Promote – Validated или Hypothesized

        Utility gate из CraniMem (март 2026): не все high-confidence факты
        должны становиться Validated — только те что реально пригодились.
        """
        report = ConsolidationReport()
        try:
            observed = self._store.get_all_facts(epistemic_state="Observed")
        except Exception as exc:  # noqa: BLE001
            logger.error("ConsolidationEngine: get_all_facts failed: %s", exc)
            report.errors += 1
            return report

        candidates = observed
        if self.prefer_validated:
            # P0-D (review finding): _promote_to_validated_via_truthgate()
            # durably advances a fact to 'Supported' via promote_esm_to()
            # BEFORE validate_and_promote() runs — if TruthGate then rejects
            # it (e.g. no evidence_refs yet), the fact is no longer Observed
            # and this scan would never see it again even after evidence is
            # added later. Rescanning Supported facts every run gives those
            # candidates a retry path instead of stranding them.
            try:
                stuck_supported = self._store.get_all_facts(epistemic_state="Supported")
            except Exception as exc:  # noqa: BLE001
                logger.error("ConsolidationEngine: Supported rescan failed: %s", exc)
                stuck_supported = []
            candidates = observed + stuck_supported

        report.scanned = len(candidates)
        batch = candidates[: self.max_batch]

        # V8.8: corroboration boost — несколько независимых наблюдений
        # одного и того же → взаимное усиление confidence
        batch = self._apply_corroboration(batch)

        for fact in batch:
            fact_id = fact.get("fact_id")
            if not fact_id:
                continue
            claim = (fact.get("claim") or "").strip()
            conf = float(fact.get("confidence", 0.0))

            # Pre-checks (существующие)
            if len(claim) < self.min_claim_len:
                report.skipped_short_claim += 1
                continue
            if conf < self.min_confidence:
                report.skipped_low_confidence += 1
                continue

            # Utility gate (NEW V8.8): факт должен быть полезен
            if not self._passes_utility_gate(fact):
                report.skipped_low_confidence += 1  # reuse counter for now
                continue

            target = "Validated" if self.prefer_validated else "Hypothesized"
            try:
                if target == "Validated":
                    ok = self._promote_to_validated_via_truthgate(fact_id)
                else:
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
                elif target == "Validated":
                    report.rejected_by_truthgate += 1
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

    def _promote_to_validated_via_truthgate(self, fact_id: str) -> bool:
        """P0-D: reach 'Validated' with the final hop enforced by TruthGate
        + CAS, not a bare ESM-legality transition.

        promote_esm_to(..., "Supported") walks Observed -> Hypothesized ->
        Supported exactly as before (pre-vetting only — this engine's own
        confidence/utility gate already decided the fact is a candidate).
        The last, security-sensitive hop into 'Validated' goes through
        store.validate_and_promote() instead of store.promote_to_validated()
        — a candidate that fails TruthGate (e.g. too little evidence for
        its CognitiveMode) is left at 'Supported', not silently promoted.
        Raises ValueError exactly like the old path did on an illegal jump
        (e.g. a concurrent transition moved the fact somewhere the ladder
        can't reach Supported from) — callers already handle that.
        """
        if not self._store.promote_esm_to(fact_id, "Supported", by="consolidation_engine"):
            return False
        return self._store.validate_and_promote(fact_id, by="consolidation_engine").passed

    def _passes_utility_gate(self, fact: dict) -> bool:
        """
        V8.8 Utility gate: факт должен быть полезен чтобы стать Validated.

        Критерии (CraniMem-inspired):
          1. Использовался в ответах (usage_count > 0) ИЛИ
          2. Ручной ввод (source=manual) ИЛИ
          3. Связан с другими фактами (has relations)
          4. НЕ противоречит существующим
        """
        fact_id = fact.get("fact_id", "")
        source = str(fact.get("source", "")).lower()
        usage = int(fact.get("usage_count", 0))

        # Ручной ввод всегда проходит
        if source == "manual":
            return True

        # Использовался → полезен
        if usage > 0:
            return True

        # Связан с другими фактами? (проверяем relations)
        if self._count_relations(fact_id) > 0:
            return True

        # Ни разу не использован и изолирован → не продвигаем
        logger.debug("Consolidation: %s skipped (unused, isolated)", fact_id)
        return False

    def _count_relations(self, fact_id: str) -> int:
        """Число рёбер для факта."""
        try:
            from core.memory import SQLiteGraphStore
            if not isinstance(self._store, SQLiteGraphStore):
                return 0
            with self._store._db() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM relations WHERE from_fact_id = ? OR to_fact_id = ?",
                    (fact_id, fact_id),
                ).fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0

    def _apply_corroboration(self, facts: list[dict]) -> list[dict]:
        """
        V8.8: Corroboration engine — semantic clustering observed facts.

        Если 3+ факта утверждают ОДНО и ТО ЖЕ (Jaccard > 0.8),
        каждый получает +0.1 confidence boost.
        Меньше 3 — без изменений.
        """
        if len(facts) < 3:
            return facts

        # Кластеризация по Jaccard-сходству claims
        result: list[dict] = list(facts)
        tokens = [frozenset((f.get("claim", "") or "").lower().split()) for f in facts]
        cluster: list[set[int]] = []

        for i in range(len(facts)):
            merged = False
            for c in cluster:
                for j in c:
                    if tokens[i] and tokens[j]:
                        overlap = len(tokens[i] & tokens[j]) / max(min(len(tokens[i]), len(tokens[j])), 1)
                        if overlap > 0.8:
                            c.add(i)
                            merged = True
                            break
                if merged:
                    break
            if not merged:
                cluster.append({i})

        # Boost: кластеры размером >=3 → +0.1 confidence
        for c in cluster:
            if len(c) >= 3:
                for idx in c:
                    old_conf = float(result[idx].get("confidence", 0.5))
                    result[idx]["confidence"] = min(1.0, old_conf + 0.1)

        return result

    def _refresh_checksum(self, fact_id: str) -> None:
        """Обновить content_checksum после смены epistemic_state.

        Использует store.update_fact_metadata() вместо store.store_fact(),
        чтобы обновить только поле metadata, не затрагивая epistemic_state.
        store_fact() отклоняет любой факт не в состоянии 'Observed' (кроме
        Ring Zero), что приводило к ложным report.errors после каждого
        успешного перевода.
        """
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
        self._store.update_fact_metadata(fact_id, meta)


def run_consolidation(store: SQLiteGraphStore | None = None) -> Any:
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
