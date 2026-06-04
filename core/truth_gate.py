"""
core/truth_gate.py — Velantrim v8.4.0
======================================
Реальный Truth Gate вместо MVP-заглушки (confidence >= 0.5).

Закрывает инвариант I68: TruthGateGateway.
Закрывает критику 6/9 ИИ из аудита май 2026.

Архитектура:
    TruthGate НЕ зависит от Neo4j.
    Работает поверх GraphStore ABC (SQLite сейчас, Neo4j в Sprint 2c).

Cognitive Modes (из V9 §12.1):
    PRECISION   — evidence ≥ 5, confidence ≥ 0.9  (медицина, право)
    BALANCED    — evidence ≥ 2, confidence ≥ 0.7  (стандарт, 90% задач)
    EXPLORATION — evidence ≥ 1, confidence ≥ 0.4  (brainstorm)
    CREATIVE    — evidence ≥ 2, confidence ≥ 0.7  (аналогии, только Validated)

AUDIT-FIX v8.4.0: contradiction detection теперь явный параметр со значениями
    "none" (default) | "naive" | "nli" (Sprint 2c через ATLAS-OS).
    До v8.4.0 _find_contradictions использовала word-overlap-XOR-negation
    эвристику, которая давала ложные срабатывания на парах вроде:
        "вода кипит при 100°C" / "вода не кипит при 0°C"
    Эти факты не противоречат — оба истинны при разных температурах.
    Naive детектор отключён по умолчанию; включать только явно.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.storage import GraphStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cognitive Modes
# ---------------------------------------------------------------------------

class CognitiveMode(str, Enum):
    PRECISION   = "PRECISION"
    BALANCED    = "BALANCED"
    EXPLORATION = "EXPLORATION"
    CREATIVE    = "CREATIVE"


# Пороги по V9 §12.1
_MODE_CONFIG: dict[CognitiveMode, dict] = {
    CognitiveMode.PRECISION:   {"min_confidence": 0.9, "min_evidence": 5},
    CognitiveMode.BALANCED:    {"min_confidence": 0.7, "min_evidence": 2},
    CognitiveMode.EXPLORATION: {"min_confidence": 0.4, "min_evidence": 1},
    CognitiveMode.CREATIVE:    {"min_confidence": 0.7, "min_evidence": 2},
}


# ---------------------------------------------------------------------------
# Результат Truth Gate
# ---------------------------------------------------------------------------

@dataclass
class TruthGateVerdict:
    """Вердикт Truth Gate — полный audit trail."""
    passed:         bool
    fact_id:        str
    reason:         str                  # машиночитаемый код причины
    justification:  str                  # человекочитаемое объяснение
    by:             str = "truth_gate"
    mode:           CognitiveMode = CognitiveMode.BALANCED
    confidence:     float = 0.0
    evidence_count: int = 0
    contradictions: list[str] = field(default_factory=list)
    checked_at:     str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def __bool__(self) -> bool:
        return self.passed


# ---------------------------------------------------------------------------
# Главный класс
# ---------------------------------------------------------------------------

class TruthGate:
    """
    Единственный путь перевода факта в Validated (инвариант I68).

    Проверки (в порядке):
        1. source присутствует и непустой
        2. confidence >= порог для текущего mode
        3. evidence_count >= порог для текущего mode
        4. Отсутствие активных contradictions в L1 (опционально — см. contradiction_detector)

    Usage:
        gate = TruthGate(store)                              # default: contradiction-stage отключена
        gate = TruthGate(store, contradiction_detector="naive")  # включить naive (development!)
        verdict = gate.evaluate(fact, mode=CognitiveMode.BALANCED)
        if verdict:
            transition_esm(fact_id, "Validated", by="truth_gate")
    """

    # AUDIT-FIX v8.4.0: возможные значения contradiction_detector.
    # "none"  — стадия 4 пропускается. Используется по умолчанию до подключения NLI.
    # "naive" — word-overlap-XOR-negation эвристика. Известно даёт false positives.
    #           Включать ТОЛЬКО для development/debug, не в production.
    # "nli"   — TODO Sprint 2c: cross-encoder через ATLAS-OS (NLI-1 invariant).
    _ALLOWED_DETECTORS = {"none", "naive", "nli"}

    def __init__(
        self,
        store: GraphStore | None,
        contradiction_detector: str = "none",
    ) -> None:
        if contradiction_detector not in self._ALLOWED_DETECTORS:
            raise ValueError(
                f"contradiction_detector='{contradiction_detector}' не поддерживается. "
                f"Допустимые: {sorted(self._ALLOWED_DETECTORS)}"
            )
        if contradiction_detector == "nli":
            raise NotImplementedError(
                "NLI contradiction detection — TODO Sprint 2c (ATLAS-OS integration). "
                "Используй 'none' до подключения."
            )
        self._store = store
        self._contradiction_detector = contradiction_detector
        if contradiction_detector == "naive":
            logger.warning(
                "TruthGate: naive contradiction detector активен — "
                "известно даёт ложные срабатывания на парах с отрицанием. "
                "Только для development."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        fact: dict,
        mode: CognitiveMode = CognitiveMode.BALANCED,
        by: str = "truth_gate",
    ) -> TruthGateVerdict:
        """
        Оценить факт. Возвращает TruthGateVerdict.
        Никогда не бросает исключений — только verdict.passed = False.
        """
        fact_id = fact.get("fact_id", "<unknown>")
        cfg = _MODE_CONFIG[mode]

        # 1. Source check
        # FIX v8.5.2 (Claude audit): делегировано в validators.validate_source.
        # Поведение идентично прежнему (пустое или whitespace-only → reject),
        # но теперь правило едино с memory и pipeline.
        from core.validators import validate_confidence, validate_source
        source = fact.get("source", "")
        ok_src, err_src = validate_source(source)
        if not ok_src:
            return self._reject(fact_id, mode, fact,
                reason="no_source",
                justification=f"{err_src}. Каждый факт обязан иметь источник.")

        # 2. Confidence check
        # FIX v8.5.2 (Claude audit): раньше `not isinstance(confidence, (int, float))
        # or confidence < min_conf` пропускал NaN, потому что `NaN < anything == False`.
        # Сейчас validators.validate_confidence явно ловит NaN/Inf через isnan/isinf
        # и нечисловые типы. После проверки типа отдельно сверяемся с min_conf.
        confidence = fact.get("confidence", 0.0)
        min_conf = cfg["min_confidence"]
        ok_conf, err_conf = validate_confidence(confidence)
        if not ok_conf:
            return self._reject(fact_id, mode, fact,
                reason="invalid_confidence",
                justification=f"confidence={confidence!r}: {err_conf}")
        if confidence < min_conf:
            return self._reject(fact_id, mode, fact,
                reason="low_confidence",
                justification=f"confidence={confidence:.3f} < "
                              f"порог {min_conf} для mode={mode.value}.")

        # 3. Evidence count check
        evidence_count = self._count_evidence(fact)
        min_ev = cfg["min_evidence"]
        if evidence_count < min_ev:
            return self._reject(fact_id, mode, fact,
                reason="insufficient_evidence",
                justification=f"evidence_count={evidence_count} < "
                              f"порог {min_ev} для mode={mode.value}. "
                              "Добавьте больше подтверждающих источников.",
                evidence_count=evidence_count)

        # 4. Contradiction check (опционально — AUDIT-FIX v8.4.0)
        # Naive детектор отключён по умолчанию из-за false positives.
        # Включать через TruthGate(store, contradiction_detector="naive")
        # или ждать NLI в Sprint 2c.
        if self._contradiction_detector == "naive":
            contradictions = self._find_contradictions_naive(fact)
            if contradictions:
                return self._reject(fact_id, mode, fact,
                    reason="active_contradictions",
                    justification=f"Найдено {len(contradictions)} активных "
                                  f"противоречий в L1: {contradictions}. "
                                  "ВНИМАНИЕ: naive детектор даёт false positives — "
                                  "проверь вручную. Разрешение через "
                                  "ConflictResolutionWorker (RFC0062).",
                    evidence_count=evidence_count,
                    contradictions=contradictions)

        # ✅ Все проверки пройдены
        logger.info(
            "TruthGate PASS | fact_id=%s mode=%s confidence=%.3f evidence=%d",
            fact_id, mode.value, confidence, evidence_count,
        )
        return TruthGateVerdict(
            passed=True,
            fact_id=fact_id,
            reason="passed",
            justification=(
                f"Все проверки пройдены: source='{source}', "
                f"confidence={confidence:.3f}, evidence={evidence_count}, "
                f"contradictions=0."
            ),
            by=by,
            mode=mode,
            confidence=confidence,
            evidence_count=evidence_count,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count_evidence(self, fact: dict) -> int:
        """
        Считаем доказательства.
        Сейчас: metadata.evidence_refs + 1 (сам факт).
        Sprint 2c: граф-запрос к Neo4j/Graphiti.
        """
        metadata = fact.get("metadata") or {}
        refs = metadata.get("evidence_refs", [])
        if isinstance(refs, list):
            return max(1, len(refs))
        # Если refs — строка (legacy), считаем как 1
        return 1

    def _find_contradictions_naive(self, fact: dict) -> list[str]:
        """
        ⚠️ NAIVE детектор противоречий — даёт ЛОЖНЫЕ срабатывания.

        Алгоритм: пары фактов с пересечением ≥ 2 слов И XOR на маркерах
        отрицания ("не", "нет", "no", "not", "never") считаются
        противоречащими.

        Известные ложные срабатывания:
          - "вода кипит при 100°C" / "вода не кипит при 0°C"
            → overlap={вода, кипит}, XOR=True → false positive
          - "Apple продаёт iPhone" / "Tesla не продаёт iPhone"
            → overlap={продаёт, iPhone}, XOR=True → false positive

        TODO Sprint 2c: заменить на NLI cross-encoder через ATLAS-OS
        (NLI-1 invariant). До тех пор включать только для development/debug.
        """
        if self._store is None:
            return []
        try:
            all_facts = self._store.get_all_facts()
        except Exception as exc:
            logger.warning("TruthGate: не удалось проверить contradictions: %s", exc)
            return []

        fact_id  = fact.get("fact_id", "")
        claim    = (fact.get("claim") or "").strip().lower()
        if not claim:
            return []

        contradicting: list[str] = []
        for stored in all_facts:
            if stored.get("fact_id") == fact_id:
                continue
            if stored.get("epistemic_state") not in ("Validated", "Supported"):
                continue
            stored_claim = (stored.get("claim") or "").strip().lower()
            claim_words   = set(claim.split())
            stored_words  = set(stored_claim.split())
            negation_markers = {"не", "нет", "no", "not", "never", "никогда"}
            overlap = claim_words & stored_words
            if len(overlap) >= 2:
                xor_negation = (
                    bool(claim_words & negation_markers) ^
                    bool(stored_words & negation_markers)
                )
                if xor_negation:
                    contradicting.append(stored["fact_id"])

        return contradicting

    def _reject(
        self,
        fact_id: str,
        mode: CognitiveMode,
        fact: dict,
        reason: str,
        justification: str,
        evidence_count: int = 0,
        contradictions: list[str] | None = None,
    ) -> TruthGateVerdict:
        logger.warning(
            "TruthGate REJECT | fact_id=%s reason=%s mode=%s",
            fact_id, reason, mode.value,
        )
        return TruthGateVerdict(
            passed=False,
            fact_id=fact_id,
            reason=reason,
            justification=justification,
            mode=mode,
            confidence=fact.get("confidence", 0.0),
            evidence_count=evidence_count,
            contradictions=contradictions or [],
        )


# ---------------------------------------------------------------------------
# Backward-compatible функция для pipeline.py
# ---------------------------------------------------------------------------

def truth_gate(
    fact: dict,
    store: GraphStore,
    mode: CognitiveMode = CognitiveMode.BALANCED,
    by: str = "pipeline.run",
) -> bool:
    """
    Drop-in замена для MVP `if confidence >= 0.5`.
    Использование в pipeline.py:

        from core.truth_gate import truth_gate, CognitiveMode
        ...
        if not truth_gate(fact, store, mode=CognitiveMode.BALANCED):
            blocked.append(fact)
            continue
    """
    gate = TruthGate(store)
    verdict = gate.evaluate(fact, mode=mode, by=by)
    return verdict.passed
