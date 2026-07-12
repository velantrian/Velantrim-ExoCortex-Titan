"""
📊 core/metrics.py — Prometheus Metrics (V8.7 Titan)

Экспортирует метрики Velantrim в Prometheus-формате через /metrics эндпоинт.

Без внешних зависимостей: ручной экспорт text/plain (OpenMetrics).
Если prometheus_client установлен — использует официальную библиотеку.

Метрики:
  - velantrim_facts_total{state}            — фактов по ESM-состояниям
  - velantrim_pipeline_duration_seconds     — гистограмма времени pipeline
  - velantrim_store_operations_total{op}    — счётчик операций с БД
  - velantrim_eventbus_queue_size           — размер очереди EventBus
  - velantrim_hybrid_retriever_build_seconds — время пересборки индекса
  - velantrim_mhi                          — Memory Health Index
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core import __version__

logger = logging.getLogger("velantrim.metrics")

# ─── Проверка prometheus_client ──────────────────────────────────────────────

_PROMETHEUS_AVAILABLE: Optional[bool] = None


def _check_prometheus() -> bool:
    global _PROMETHEUS_AVAILABLE
    if _PROMETHEUS_AVAILABLE is None:
        try:
            import prometheus_client  # noqa: F401
            _PROMETHEUS_AVAILABLE = True
        except ImportError:
            _PROMETHEUS_AVAILABLE = False
    return _PROMETHEUS_AVAILABLE


# ─── Ручные счётчики (stdlib only) ───────────────────────────────────────────

_lock = threading.Lock()


@dataclass
class _Counter:
    name: str
    help: str
    labels: Dict[str, int] = field(default_factory=dict)
    _total: int = 0

    def inc(self, labels: Optional[Dict[str, str]] = None) -> None:
        with _lock:
            self._total += 1
            if labels:
                key = _labels_key(labels)
                self.labels[key] = self.labels.get(key, 0) + 1

    def set(self, value: float) -> None:
        with _lock:
            self._total = int(value)


@dataclass
class _Gauge:
    name: str
    help: str
    value: float = 0.0

    def set(self, v: float) -> None:
        with _lock:
            self.value = v

    def inc(self, delta: float = 1.0) -> None:
        with _lock:
            self.value += delta


@dataclass
class _Histogram:
    name: str
    help: str
    buckets: List[float]
    _count: int = 0
    _sum: float = 0.0
    _bucket_counts: Dict[float, int] = field(default_factory=dict)

    def observe(self, value: float) -> None:
        with _lock:
            self._count += 1
            self._sum += value
            for b in sorted(self.buckets):
                if value <= b:
                    self._bucket_counts[b] = self._bucket_counts.get(b, 0) + 1


def _labels_key(labels: Dict[str, str]) -> str:
    return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))


# ─── Реестр метрик ───────────────────────────────────────────────────────────


class MetricsRegistry:
    """Реестр метрик Velantrim."""

    def __init__(self):
        self._counters: Dict[str, _Counter] = {}
        self._gauges: Dict[str, _Gauge] = {}
        self._histograms: Dict[str, _Histogram] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        # Counters
        self._counters["store_ops"] = _Counter(
            "velantrim_store_operations_total",
            "Store operations (store_fact, get_fact, batch)",
        )

        # Gauges
        self._gauges["facts_observed"] = _Gauge(
            "velantrim_facts_total", "Facts by ESM state (Observed)"
        )
        self._gauges["facts_validated"] = _Gauge(
            "velantrim_facts_total", "Facts by ESM state (Validated)"
        )
        self._gauges["eventbus_queue"] = _Gauge(
            "velantrim_eventbus_queue_size", "EventBus queue size"
        )
        self._gauges["mhi"] = _Gauge(
            "velantrim_mhi", "Memory Health Index"
        )

        # Histograms
        self._histograms["pipeline"] = _Histogram(
            "velantrim_pipeline_duration_seconds",
            "Pipeline duration",
            [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
        self._histograms["retrieval"] = _Histogram(
            "velantrim_retrieval_duration_seconds",
            "Retrieval step duration",
            [0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
        )
        self._histograms["hybrid_build"] = _Histogram(
            "velantrim_hybrid_retriever_build_seconds",
            "Hybrid retriever build time",
            [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
        )

    # ── Counters ──────────────────────────────────────────────────────────

    def store_op(self, op: str) -> None:
        c = self._counters.get("store_ops")
        if c:
            c.inc({"op": op})

    # ── Gauges ────────────────────────────────────────────────────────────

    def set_facts_by_state(self, state: str, count: int) -> None:
        if state == "Observed":
            self._gauges.get("facts_observed", _Gauge("", "")).set(count)
        elif state == "Validated":
            self._gauges.get("facts_validated", _Gauge("", "")).set(count)

    def set_eventbus_queue(self, size: int) -> None:
        self._gauges.get("eventbus_queue", _Gauge("", "")).set(size)

    def set_mhi(self, value: float) -> None:
        self._gauges.get("mhi", _Gauge("", "")).set(value)

    # ── Histograms ────────────────────────────────────────────────────────

    def pipeline_duration(self, seconds: float) -> None:
        self._histograms.get("pipeline", _Histogram("", "", [])).observe(seconds)

    def retrieval_duration(self, seconds: float) -> None:
        self._histograms.get("retrieval", _Histogram("", "", [])).observe(seconds)

    def hybrid_build_duration(self, seconds: float) -> None:
        self._histograms.get("hybrid_build", _Histogram("", "", [])).observe(seconds)

    # ── Экспорт ──────────────────────────────────────────────────────────

    def export(self) -> str:
        """Экспортировать все метрики в формате Prometheus text/plain."""
        lines: List[str] = []

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        for c in self._counters.values():
            lines.append(f"# HELP {c.name} {c.help}")
            lines.append(f"# TYPE {c.name} counter")
            lines.append(f"{c.name}_total {c._total} {now_ms}")
            for lk, lv in c.labels.items():
                lines.append(f"{c.name}_total{{{lk}}} {lv} {now_ms}")

        for g in self._gauges.values():
            lines.append(f"# HELP {g.name} {g.help}")
            lines.append(f"# TYPE {g.name} gauge")
            lines.append(f"{g.name} {g.value} {now_ms}")

        for h in self._histograms.values():
            lines.append(f"# HELP {h.name} {h.help}")
            lines.append(f"# TYPE {h.name} histogram")
            lines.append(f"{h.name}_count {h._count} {now_ms}")
            lines.append(f"{h.name}_sum {h._sum} {now_ms}")
            for b in sorted(h._bucket_counts):
                lines.append(
                    f'{h.name}_bucket{{le="{b}"}} {h._bucket_counts[b]} {now_ms}'
                )
            lines.append(f'{h.name}_bucket{{le="+Inf"}} {h._count} {now_ms}')

        return "\n".join(lines) + "\n"


# ─── Глобальный реестр ───────────────────────────────────────────────────────

_registry: Optional[MetricsRegistry] = None


def get_metrics() -> MetricsRegistry:
    global _registry
    if _registry is None:
        _registry = MetricsRegistry()
    return _registry


def reset_metrics() -> None:
    global _registry
    _registry = None


# ─── Healthcheck ─────────────────────────────────────────────────────────────

def healthcheck(store=None) -> Dict[str, Any]:
    """Быстрый healthcheck — состояние всех компонентов."""
    status: Dict[str, Any] = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": os.getenv("VELANTRIM_VERSION", __version__),
    }

    # Проверить store
    if store is not None:
        try:
            facts = store.get_all_facts()
            status["store"] = {
                "connected": True,
                "facts_count": len(facts) if facts else 0,
            }
        except Exception as e:
            status["store"] = {"connected": False, "error": str(e)}
            status["status"] = "degraded"

    # Проверить EventBus
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        status["eventbus"] = {"queue_size": len(bus._queue)}
    except Exception:
        status["eventbus"] = {"available": False}

    # Memory metrics
    import sys
    status["memory"] = {
        "python_heap_mb": round(sys.getsizeof(None) * 0, 1),  # placeholder
    }

    return status


__all__ = [
    "MetricsRegistry",
    "get_metrics",
    "reset_metrics",
    "healthcheck",
]
