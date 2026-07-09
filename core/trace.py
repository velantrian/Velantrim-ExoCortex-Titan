# core/trace.py
# Velantrim ExoCortex — Trace / Provenance Layer
# v8.0.4 (audit-fix: `by` param in promote_trace, confidence semantics clarified)
#
# Назначение: строит цепочку провенанса для каждого факта.
# Принцип: Trace → Validation → Answer (не наоборот).
# Каждый trace-элемент содержит epistemic_state из ESM.
#
# История изменений:
#   v8.0.2-sprint1: promote_trace без проверки ESM-матрицы.
#   v8.0.3-p0:     promote_trace проверяет ESM_TRANSITIONS.
#   v8.0.3-p0-FIX: promote_trace идемпотентен.
#   v8.0.4:        promote_trace получил параметр `by` (audit trail).
#                  build_trace: поле `confidence` переименовано в `retrieval_score`
#                  внутри trace-элемента — разделение с source confidence.

from datetime import UTC, datetime
from typing import Any

from core.memory import ESM_STATES, ESM_TRANSITIONS

_ESM_LADDER = ("Observed", "Hypothesized", "Supported", "Validated")


def _can_reach_esm(current: str, target: str) -> bool:
    """Проверка достижимости target из current (лестница или один шаг)."""
    if current == target:
        return True
    if target in _ESM_LADDER and current in _ESM_LADDER:
        return _ESM_LADDER.index(current) < _ESM_LADDER.index(target)
    return target in ESM_TRANSITIONS.get(current, set())

# ─── TRACE BUILDER ────────────────────────────────────────────────────────────

def build_trace(retrieved: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Построить trace-цепочку из списка извлечённых фактов.

    Каждый элемент содержит:
      - fact_id:          идентификатор факта
      - source:           источник (откуда пришёл факт)
      - origin:           способ получения (retrieval / ingestion / volition)
      - epistemic_state:  текущее ESM-состояние факта
      - retrieval_score:  BM25-балл (query-зависимый, НЕ персистируется в L1)
      - source_confidence: confidence источника (стабильная, из L3)
      - retrieved_at:     временная метка извлечения

    Семантика confidence (v8.0.4 clarification):
      retrieval_score  — BM25-балл, меняется от запроса к запросу.
      source_confidence — confidence из источника, стабильная и персистируемая.
      Они различны. Audit Layer должен логировать оба.
    """
    trace: list[dict[str, Any]] = []
    now = datetime.now(UTC).isoformat()

    for item in retrieved:
        fact_id = item.get("id") or item.get("fact_id")
        if not fact_id:
            continue

        trace.append({
            "fact_id":          fact_id,
            "source":           item.get("source", "unknown"),
            "origin":           item.get("origin", "retrieval"),
            "epistemic_state":  item.get("epistemic_state", "Observed"),
            # v8.0.4: разделены retrieval_score (BM25) и source_confidence (L3)
            "retrieval_score":  round(float(item.get("retrieval_score", 0.5)), 4),
            "source_confidence": round(float(item.get("confidence", 0.5)), 4),
            "retrieved_at":     now,
        })

    return trace


# ─── PROMOTE TRACE ────────────────────────────────────────────────────────────

def promote_trace(
    trace: list[dict[str, Any]],
    new_state: str,
    by: str = "pipeline.promote_trace",
) -> None:
    """
    Обновить epistemic_state всех элементов trace после прохождения TruthGate.
    Вызывается из pipeline после truth_gate() → True.

    TASK-05: two-pass — сначала полная валидация без мутации,
    затем мутация. Гарантирует атомарность.

    AUDIT-FIX v8.0.4: параметр `by` — кто инициировал promote.
    Записывается в `promoted_by` каждого элемента trace для audit trail.

    Raises:
        ValueError: если new_state не в ESM_STATES или переход недопустим.
    """
    if new_state not in ESM_STATES:
        raise ValueError(f"promote_trace: недопустимое ESM-состояние '{new_state}'")

    # Pass 1: полная валидация без единой мутации
    for element in trace:
        current = element.get("epistemic_state", "Observed")
        if current == new_state:
            continue  # идемпотентный случай
        if not _can_reach_esm(current, new_state):
            raise ValueError(
                f"promote_trace: переход '{current}' → '{new_state}' недопустим "
                f"(fact_id={element.get('fact_id', '?')})"
            )

    # Pass 2: мутация — только если Pass 1 прошёл без исключений
    now = datetime.now(UTC).isoformat()
    for element in trace:
        element["epistemic_state"] = new_state
        element["promoted_at"]     = now
        element["promoted_by"]     = by  # v8.0.4: audit trail


# ─── FORMAT TRACE ─────────────────────────────────────────────────────────────

def format_trace(trace: list[dict[str, Any]]) -> str:
    """Человекочитаемый вывод trace-цепочки для логов и ответа."""
    if not trace:
        return "TRACE: empty"
    lines = ["TRACE:"]
    for i, el in enumerate(trace, 1):
        lines.append(
            f"  [{i}] {el.get('fact_id', '?')} | "
            f"source={el.get('source', '?')} | "
            f"state={el.get('epistemic_state', '?')} | "
            f"bm25={el.get('retrieval_score', '?')} | "
            f"conf={el.get('source_confidence', '?')}"
        )
    return "\n".join(lines)


# ─── TRACE SUMMARY ────────────────────────────────────────────────────────────

def trace_summary(trace: list[dict[str, Any]]) -> dict[str, Any]:
    """Компактная сводка по trace-цепочке для audit-снимка (без всей цепочки).

    Возвращает счётчики ESM-состояний, список источников и средние баллы.
    Используется epistemic_pipeline.EpistemicResult.trace_summary.
    """
    if not trace:
        return {
            "count": 0,
            "sources": [],
            "states": {},
            "avg_retrieval_score": 0.0,
            "avg_source_confidence": 0.0,
            "promoted": 0,
        }

    states: dict[str, int] = {}
    sources: list[str] = []
    rs_sum = 0.0
    sc_sum = 0.0
    promoted = 0

    for el in trace:
        st = el.get("epistemic_state", "Observed")
        states[st] = states.get(st, 0) + 1
        src = el.get("source")
        if src and src not in sources:
            sources.append(src)
        try:
            rs_sum += float(el.get("retrieval_score", 0.0) or 0.0)
        except (TypeError, ValueError):
            pass
        try:
            sc_sum += float(el.get("source_confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            pass
        if el.get("promoted_at"):
            promoted += 1

    n = len(trace)
    return {
        "count": n,
        "sources": sources,
        "states": states,
        "avg_retrieval_score": round(rs_sum / n, 4),
        "avg_source_confidence": round(sc_sum / n, 4),
        "promoted": promoted,
    }
