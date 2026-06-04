"""
Epistemic Pipeline — связка TruthGate + ESM + Trace для ingest.

Sprint 1 / T4. Изолированный слой над Graphiti: НЕ заменяет add_episode, а
дополняет каждое успешно созданное episode эпистемическим вердиктом.

Поток:
    chunk + source + ep_uuid
        → fact_candidate (dict)
        → TruthGate.evaluate(fact_candidate)
        → build_trace([fact_candidate])
        → если passed:  promote_trace(trace, Validated)
        → если passed:  factstate = Validated
        → если reject:  factstate = Observed (с trace reason'ом)
        → запись метаданных в episode (через Cypher) — опционально

Принципы:
  - Backend-agnostic: build_fact_candidate / evaluate_fact_candidate не требуют
    Graphiti. Это позволяет unit-тестировать без графа.
  - I2: переход в Validated происходит только если TruthGate.passed.
  - I6 учитывается через Trace.promote_trace (Ring Zero фактоr пропускается).
  - Идемпотентность: повторный прогон одного chunk даёт стабильный verdict
    (никаких side-effect, кроме записи в graph).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from core.esm import EpistemicState
from core.feature_config import get_config
from core.trace import build_trace, promote_trace, trace_summary
from core.truth_gate import (
    CognitiveMode,
    TruthGate,
    TruthGateVerdict,
)

logger = logging.getLogger(__name__)


# ─── Результат эпистемической проверки ────────────────────────────────────────


@dataclass
class EpistemicResult:
    """Что произошло с одним chunk после TruthGate + Trace."""

    fact_id: str
    passed: bool
    epistemic_state: str            # "Validated" если passed, иначе "Observed"
    reason: str                     # код причины: passed/no_source/low_confidence/...
    justification: str
    mode: str
    confidence: float
    evidence_count: int
    trace: list[dict[str, Any]] = field(default_factory=list)
    trace_summary: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        """Сериализуемая форма для записи в episode metadata."""
        return {
            "fact_id": self.fact_id,
            "passed": self.passed,
            "epistemic_state": self.epistemic_state,
            "truth_gate_reason": self.reason,
            "truth_gate_justification": self.justification,
            "truth_gate_mode": self.mode,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "trace_size": len(self.trace),
        }


# ─── Построение fact-кандидата ────────────────────────────────────────────────


def build_fact_candidate(
    *,
    chunk: str,
    source: str,
    fact_id: str,
    confidence: float | None = None,
    evidence_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    epistemic_state: str = EpistemicState.OBSERVED.value,
) -> dict[str, Any]:
    """
    Сформировать fact_candidate из chunk текста.

    `confidence` по умолчанию берётся из config.app.default_fact_confidence.
    `evidence_refs` влияет на evidence_count в TruthGate.
    """
    if confidence is None:
        confidence = get_config().app.default_fact_confidence

    md: dict[str, Any] = dict(metadata or {})
    if evidence_refs is not None:
        md["evidence_refs"] = list(evidence_refs)

    claim = (chunk or "").strip()
    return {
        "fact_id": str(fact_id),
        "claim": claim,
        "source": source or "unknown",
        "confidence": confidence,
        "epistemic_state": epistemic_state,
        "metadata": md,
    }


# ─── Главная функция ──────────────────────────────────────────────────────────


def _coerce_mode(value: Any) -> CognitiveMode:
    """Привести строку/enum к CognitiveMode; неизвестное → BALANCED (с предупреждением)."""
    if isinstance(value, CognitiveMode):
        return value
    try:
        return CognitiveMode(str(value).upper())
    except ValueError:
        logger.warning("Неизвестный truth_gate_mode=%r → BALANCED", value)
        return CognitiveMode.BALANCED


def evaluate_fact_candidate(
    fact: dict[str, Any],
    *,
    mode: Any | None = None,
) -> EpistemicResult:
    """
    Прогнать fact через TruthGate, построить trace, вернуть EpistemicResult.

    `mode`: переопределяет config.app.truth_gate_mode (для админских/тестовых
    сценариев). По умолчанию используется значение из конфига.
    """
    chosen_mode = _coerce_mode(
        mode if mode is not None else get_config().app.truth_gate_mode
    )

    # TruthGate работает поверх GraphStore, но стадия противоречий по умолчанию
    # отключена ("none") и НЕ обращается к стору — поэтому ingest-проверка остаётся
    # backend-agnostic (store=None), как и заявлено в docstring модуля.
    gate = TruthGate(store=None, contradiction_detector="none")
    verdict: TruthGateVerdict = gate.evaluate(fact, mode=chosen_mode)

    trace = build_trace([{
        "fact_id": fact.get("fact_id"),
        "source": fact.get("source"),
        "origin": "ingestion",
        "epistemic_state": fact.get("epistemic_state", EpistemicState.OBSERVED.value),
        "confidence": fact.get("confidence", 0.0),
    }])

    if verdict.passed:
        promote_trace(trace, EpistemicState.VALIDATED.value, by="truth_gate")
        state = EpistemicState.VALIDATED.value
    else:
        # Reject: оставляем Observed, но в trace элементах появится reason
        # через promote_skipped? Нет: при reject mы не делаем promote, чтобы
        # явно отделить "не валидирован" от "валидирован".
        state = EpistemicState.OBSERVED.value
        if trace:
            trace[0]["truth_gate_reason"] = verdict.reason

    summary = trace_summary(trace)

    result = EpistemicResult(
        fact_id=str(fact.get("fact_id") or "<unknown>"),
        passed=verdict.passed,
        epistemic_state=state,
        reason=verdict.reason,
        justification=verdict.justification,
        mode=verdict.mode,
        confidence=verdict.confidence,
        evidence_count=verdict.evidence_count,
        trace=trace,
        trace_summary=summary,
    )

    log_method = logger.info if verdict.passed else logger.warning
    log_method(
        "epistemic_pipeline: fact_id=%s mode=%s passed=%s reason=%s "
        "conf=%.3f evidence=%d",
        result.fact_id, result.mode, result.passed, result.reason,
        result.confidence, result.evidence_count,
    )

    return result


# ─── Опциональная persistence в Graphiti episode ──────────────────────────────


async def persist_epistemic_metadata(
    graphiti,
    *,
    episode_uuid: str,
    result: EpistemicResult,
) -> bool:
    """
    Записать эпистемические метаданные в Graphiti episode (по UUID).

    Используется из ingest pipeline (опционально). Безопасно: при любых ошибках
    Cypher возвращает False без бросания исключения.
    """
    if not episode_uuid or graphiti is None:
        return False

    try:
        driver = graphiti.driver
        meta = result.to_metadata()
        await driver.execute_query(
            """
            MATCH (e:Episodic {uuid: $uuid})
            SET e.epistemic_state = $state,
                e.truth_gate_reason = $reason,
                e.truth_gate_mode = $mode,
                e.confidence = $confidence,
                e.evidence_count = $evidence_count,
                e.truth_gate_passed = $passed
            """,
            uuid=episode_uuid,
            state=meta["epistemic_state"],
            reason=meta["truth_gate_reason"],
            mode=meta["truth_gate_mode"],
            confidence=meta["confidence"],
            evidence_count=meta["evidence_count"],
            passed=meta["passed"],
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "persist_epistemic_metadata: не удалось записать "
            "epistemic metadata для %s: %s",
            episode_uuid, exc,
        )
        return False


async def run_epistemic_pipeline(
    *,
    fact_id: str,
    content: str,
    source: str,
    mode: Any | None = None,
    graphiti=None,
) -> EpistemicResult:
    """
    TruthGate + Trace для одного chunk; опционально persist в Graphiti или SQLite.
    """
    fact_candidate = build_fact_candidate(
        chunk=content,
        source=source,
        fact_id=str(fact_id),
    )
    result = evaluate_fact_candidate(fact_candidate, mode=mode)

    if graphiti is not None:
        await persist_epistemic_metadata(
            graphiti,
            episode_uuid=str(fact_id),
            result=result,
        )
    else:
        try:
            from core.local_episode_store import get_local_episode_store

            get_local_episode_store().merge_episode_meta(
                str(fact_id),
                {"epistemic": result.to_metadata()},
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("local epistemic meta: %s", exc)

    try:
        from core.event_bridge import on_truth_gate_verdict

        await on_truth_gate_verdict(
            episode_uuid=str(fact_id),
            passed=result.passed,
            reason=result.reason,
            epistemic_state=result.epistemic_state,
        )
    except Exception:  # noqa: BLE001
        pass

    return result


__all__ = [
    "EpistemicResult",
    "build_fact_candidate",
    "evaluate_fact_candidate",
    "persist_epistemic_metadata",
    "run_epistemic_pipeline",
]
