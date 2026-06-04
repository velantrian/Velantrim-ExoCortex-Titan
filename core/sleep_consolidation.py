"""
🌙 core/sleep_consolidation.py — Sleep Consolidation Loop (RFC-0082, P0.3)
=========================================================================

«Мозг во сне»: единый цикл, связывающий уже готовые органы памяти в ОДИН ритм —
так система сама себя приводит в порядок в простое («чем дольше живёт, тем лучше
организует себя»).

Порядок (по зависимостям, M4-fix):
    corroboration → contradiction DETECTION → promotion (знает о противоречиях)
    → contradiction RESOLUTION → decay → consolidation_report

  1. Corroboration — семантическая (если включён ENABLE_SEMANTIC_DEDUP и есть embedder),
     иначе лексическая. Считает, сколько РАЗНЫХ источников подтверждают каждый факт.
  2. Promotion — градуированный промоушен с этой корроборацией (Observed→…→Validated по доказательствам).
  3. Contradiction resolution — «новое противоречит старому» → старое Validated → Contradicted.
  4. Decay — затухание (см. примечание: цель decay — Velum-синапсы/important-веса, не ESM фактов).

Дисциплина: аддитивно, за флагом `ENABLE_SLEEP_CONSOLIDATION` (по умолчанию ВЫКЛ);
всё matrix-safe, no-DELETE, Truth Gate не обходится; возвращает отчёт с `.to_dict()`
(совместимо с `run_consolidation` → SleepTimeWorker и `POST /memory/consolidate`).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def is_sleep_consolidation_enabled() -> bool:
    return os.getenv("ENABLE_SLEEP_CONSOLIDATION", "false").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class SleepReport:
    run_id: str = "sleep"
    facts_examined: int = 0
    corroboration_mode: str = "lexical"          # lexical | semantic
    promotion: dict[str, Any] = field(default_factory=dict)
    contradictions: dict[str, Any] = field(default_factory=dict)
    decay: dict[str, Any] = field(default_factory=dict)
    errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "facts_examined": self.facts_examined,
            "corroboration_mode": self.corroboration_mode,
            "promotion": dict(self.promotion),
            "contradictions": dict(self.contradictions),
            "decay": dict(self.decay),
            "errors": self.errors,
        }


def run_sleep_consolidation(
    store: Any,
    *,
    embed_fn: Any | None = None,
    run_id: str = "sleep",
) -> SleepReport:
    """
    Запустить полный цикл консолидации над стором. Каждый шаг изолирован try/except,
    чтобы сбой одного органа не валил весь цикл (degraded, как и положено Slow Path).
    """
    from core.contradiction_resolver import detect_contradictions, resolve_contradictions
    from core.promotion_policy import compute_corroboration, run_graduated_promotion
    from core.semantic_dedup import (
        compute_semantic_corroboration,
        default_embedder,
        is_semantic_dedup_enabled,
    )

    rep = SleepReport(run_id=run_id)
    try:
        facts = store.get_all_facts()
    except Exception:  # noqa: BLE001
        facts = []
    rep.facts_examined = len(facts)

    # ── 1. Corroboration (семантическая или лексическая) ──
    try:
        if embed_fn is None and is_semantic_dedup_enabled():
            embed_fn = default_embedder()
        if embed_fn is not None:
            corro = compute_semantic_corroboration(facts, embed_fn=embed_fn)
            rep.corroboration_mode = "semantic"
        else:
            corro = compute_corroboration(facts)
            rep.corroboration_mode = "lexical"
    except Exception as exc:  # noqa: BLE001
        logger.warning("sleep: corroboration failed: %s", exc)
        corro = {}
        rep.errors += 1

    # ── M4 fix: сначала ВЫЯВЛЯЕМ противоречия (чистая функция, без мутаций), чтобы
    # промоушен не повышал контрадикт-факты до Validated в том же цикле (раньше
    # promotion шёл ДО contradiction → факт мог стать Validated и тут же Contradicted).
    try:
        contradicted_ids = {c.older_id for c in detect_contradictions(facts)}
    except Exception as exc:  # noqa: BLE001
        logger.warning("sleep: contradiction pre-detection failed: %s", exc)
        contradicted_ids = set()

    # ── 2. Promotion (с корроборацией И знанием о противоречиях) ──
    try:
        promo = run_graduated_promotion(
            store, corroboration_override=corro, contradicted_ids=contradicted_ids
        )
        rep.promotion = promo.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.warning("sleep: promotion failed: %s", exc)
        rep.errors += 1

    # ── 3. Contradiction resolution ──
    try:
        contra = resolve_contradictions(store)
        rep.contradictions = contra.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.warning("sleep: contradiction resolution failed: %s", exc)
        rep.errors += 1

    # ── 4. Decay ──
    # Примечание (честно): DecayOrchestrator затухает Velum-синапсы / important-веса сущностей,
    # а не ESM-состояния фактов. Fact-level decay не подключён в P0 — это P1 (по Velum-стору).
    rep.decay = {
        "status": "skipped_p0",
        "reason": "decay targets Velum synapse / entity weights (separate store); "
                  "fact-level decay wiring is P1",
    }

    logger.info("SleepConsolidation[%s]: %s", run_id, rep.to_dict())
    return rep


__all__ = ["SleepReport", "is_sleep_consolidation_enabled", "run_sleep_consolidation"]
