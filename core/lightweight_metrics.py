"""
📊 core/lightweight_metrics.py — Lightweight Eval Metrics (V8.7 Titan)

ChatGPT совет: «не подключай тяжёлую observability-систему, пока нет простого логирования».
Без метрик нельзя говорить «система стала умнее», можно только «мне кажется».

Метрики (append-only JSONL + in-memory counters):
    trace_completeness       — есть ли путь доказательства для каждого ответа
    grounding_score          — насколько ответ опирается на FactsPack
    unsupported_claim_count  — сколько утверждений без источника
    latency_by_step          — какой модуль тормозит
    retrieval_precision      — достаёт ли поиск нужное (sampled)

Инварианты:
    I-LM1: Метрики не блокируют pipeline. Fire-and-forget.
    I-LM2: metrics.jsonl — append-only. Не перезаписывается.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.lightweight_metrics")

METRICS_PATH = os.getenv("VELANTRIM_METRICS_PATH", "./data/metrics.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvalReport:
    """Лёгкий оценочный отчёт для одного запроса."""
    query: str
    timestamp: str = field(default_factory=_now)

    # Trace
    trace_completeness: float = 0.0      # 0..1 — насколько полный trace

    # Grounding
    grounding_score: float = 0.0          # 0..1 — overlap ответа с FactsPack
    unsupported_claim_count: int = 0
    total_claims: int = 0

    # Latency (ms)
    latency_total_ms: float = 0.0
    latency_retrieval_ms: float = 0.0
    latency_llm_ms: float = 0.0

    # Retrieval
    retrieval_precision: float = 0.0     # 0..1 — sampled: сколько retrieved фактов релевантны
    facts_retrieved: int = 0
    facts_used: int = 0

    # Meta
    intent: str = ""
    roles_used: str = ""                 # comma-separated role IDs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:200],
            "timestamp": self.timestamp,
            "trace_completeness": round(self.trace_completeness, 3),
            "grounding_score": round(self.grounding_score, 3),
            "unsupported_claim_count": self.unsupported_claim_count,
            "total_claims": self.total_claims,
            "latency_total_ms": round(self.latency_total_ms, 1),
            "latency_retrieval_ms": round(self.latency_retrieval_ms, 1),
            "latency_llm_ms": round(self.latency_llm_ms, 1),
            "retrieval_precision": round(self.retrieval_precision, 3),
            "facts_retrieved": self.facts_retrieved,
            "facts_used": self.facts_used,
            "intent": self.intent,
            "roles_used": self.roles_used,
        }


# In-memory counters (для быстрого доступа)
_counters: Dict[str, int] = {
    "total_queries": 0,
    "total_unsupported_claims": 0,
    "total_gcr_blocks": 0,
}


class LightweightMetrics:
    """
    Лёгкая система метрик.

    Использование:
        metrics = LightweightMetrics()

        # После каждого ответа:
        report = EvalReport(query="...", grounding_score=0.85, ...)
        metrics.record(report)

        # Сводка:
        print(metrics.summary())
    """

    def __init__(self, metrics_path: str = METRICS_PATH):
        self._path = metrics_path
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        d = os.path.dirname(self._path)
        if d:
            os.makedirs(d, exist_ok=True)

    def record(self, report: EvalReport) -> None:
        """Записать отчёт в metrics.jsonl (append-only)."""
        global _counters
        try:
            _counters["total_queries"] += 1
            _counters["total_unsupported_claims"] += report.unsupported_claim_count
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(report.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("metrics record: %s", exc)

    def record_gcr_block(self) -> None:
        global _counters
        _counters["total_gcr_blocks"] += 1

    def summary(self) -> Dict[str, Any]:
        """Быстрая сводка (in-memory counters)."""
        global _counters
        return {
            "total_queries": _counters["total_queries"],
            "total_unsupported_claims": _counters["total_unsupported_claims"],
            "total_gcr_blocks": _counters["total_gcr_blocks"],
            "metrics_file": self._path,
        }

    def read_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Прочитать последние N записей из metrics.jsonl."""
        try:
            if not os.path.exists(self._path):
                return []
            with open(self._path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            recent = lines[-limit:]
            return [json.loads(line) for line in recent if line.strip()]
        except Exception:
            return []

    def aggregate(self) -> Dict[str, Any]:
        """Агрегированные метрики по всем записям."""
        reports = self.read_recent(limit=1000)
        if not reports:
            return {"count": 0}

        n = len(reports)
        avg_grounding = sum(r.get("grounding_score", 0) for r in reports) / n
        avg_trace = sum(r.get("trace_completeness", 0) for r in reports) / n
        avg_latency = sum(r.get("latency_total_ms", 0) for r in reports) / n
        avg_retrieval = sum(r.get("retrieval_precision", 0) for r in reports) / n
        total_unsupported = sum(r.get("unsupported_claim_count", 0) for r in reports)

        return {
            "count": n,
            "avg_grounding_score": round(avg_grounding, 3),
            "avg_trace_completeness": round(avg_trace, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "avg_retrieval_precision": round(avg_retrieval, 3),
            "total_unsupported_claims": total_unsupported,
        }


# Глобальный экземпляр
_metrics: Optional[LightweightMetrics] = None


def get_lightweight_metrics() -> LightweightMetrics:
    global _metrics
    if _metrics is None:
        _metrics = LightweightMetrics()
    return _metrics


__all__ = ["EvalReport", "LightweightMetrics", "get_lightweight_metrics"]
