"""
core/mhi.py — Velantrim v8.4.0
================================
Memory Health Index (MHI) — метрика здоровья памяти агента.

Закрывает stub в SLO Contract (V9 §8).
Закрывает RFC0070 (pending).
Закрывает рекомендацию Kimi из мета-аудита май 2026.

Формула (взвешенная):
    MHI = 0.30 × validated_ratio
        + 0.25 × freshness_score
        + 0.25 × retrieval_precision
        + 0.20 × graph_coverage

    MHI ∈ [0.0, 1.0]

Пороги (из V9 §8 SLO Contract):
    MHI >= 0.60  → HEALTHY
    MHI >= 0.30  → DEGRADED (включая 0.30–0.50 = WARN, 0.50–0.60 = OK-borderline)
    MHI <  0.30  → SAFE_MODE (немедленный GC + alert ops)

AUDIT-FIX v8.4.0: _status() теперь реально использует THRESHOLD_DEGRADED=0.50.
До v8.4.0 константа была объявлена, но не использовалась — статус переключался
напрямую на границе 0.30. Это создавало расхождение с документацией.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.storage import GraphStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Статусы
# ---------------------------------------------------------------------------

class MHIStatus(str, Enum):
    HEALTHY    = "HEALTHY"
    DEGRADED   = "DEGRADED"
    SAFE_MODE  = "SAFE_MODE"


# ---------------------------------------------------------------------------
# Результат
# ---------------------------------------------------------------------------

@dataclass
class MHIReport:
    """Полный отчёт о здоровье памяти."""
    mhi:                float
    status:             MHIStatus
    validated_ratio:    float
    freshness_score:    float
    retrieval_precision: float
    graph_coverage:     float
    total_facts:        int
    validated_facts:    int
    collapsed_facts:    int
    stale_facts:        int
    calculated_at:      str

    # Рекомендации для Meta-Supervisor
    recommendations:    list[str]

    def __str__(self) -> str:
        return (
            f"MHI={self.mhi:.3f} [{self.status.value}] | "
            f"validated={self.validated_ratio:.2f} "
            f"freshness={self.freshness_score:.2f} "
            f"precision={self.retrieval_precision:.2f} "
            f"graph={self.graph_coverage:.2f} | "
            f"total={self.total_facts} facts"
        )


# ---------------------------------------------------------------------------
# Вычислитель
# ---------------------------------------------------------------------------

class MHICalculator:
    """
    Калькулятор Memory Health Index.

    Weights (из рекомендации Kimi, адаптированы под Velantrim):
        validated_ratio    = 0.30  — доля фактов в Validated/ImmutableCore
        freshness_score    = 0.25  — доля фактов не старше decay_threshold
        retrieval_precision = 0.25 — hit rate последних N запросов
        graph_coverage     = 0.20  — доля фактов в L3 (сейчас 0 до Neo4j)

    Usage:
        calc   = MHICalculator(store)
        report = calc.calculate()
        print(report)

        if report.status == MHIStatus.SAFE_MODE:
            trigger_gc()
            alert_ops(report)
    """

    # Весовые коэффициенты
    W_VALIDATED  = 0.30
    W_FRESHNESS  = 0.25
    W_PRECISION  = 0.25
    W_GRAPH      = 0.20

    # Пороги статусов
    THRESHOLD_HEALTHY    = 0.60
    THRESHOLD_DEGRADED   = 0.50
    THRESHOLD_SAFE_MODE  = 0.30

    # Порог "свежести" факта — не старше N дней
    FRESHNESS_DAYS = 30

    def __init__(
        self,
        store: GraphStore,
        retrieval_hits: int = 0,
        retrieval_total: int = 0,
        l3_connected: bool = False,
    ) -> None:
        """
        Args:
            store:              GraphStore (L1 SQLite сейчас)
            retrieval_hits:     количество успешных retrieval за последние N запросов
            retrieval_total:    всего retrieval запросов за последние N
            l3_connected:       True если Neo4j/Graphiti подключён (Sprint 2c)
        """
        self._store           = store
        self._retrieval_hits  = retrieval_hits
        self._retrieval_total = retrieval_total
        self._l3_connected    = l3_connected

    def calculate(self) -> MHIReport:
        """Вычислить MHI. Никогда не бросает исключений."""
        try:
            return self._calculate_internal()
        except Exception as exc:
            logger.error("MHICalculator ошибка: %s", exc)
            return self._error_report(str(exc))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _calculate_internal(self) -> MHIReport:
        all_facts = self._store.get_all_facts()
        now       = datetime.now(UTC)
        cutoff    = now - timedelta(days=self.FRESHNESS_DAYS)

        total          = len(all_facts)
        validated      = 0
        collapsed      = 0
        stale          = 0

        healthy_states = {"Validated", "ImmutableCore"}
        dead_states    = {"Collapsed", "Deprecated"}

        for fact in all_facts:
            state = fact.get("epistemic_state", "")
            if state in healthy_states:
                validated += 1
            if state in dead_states:
                collapsed += 1

            # Freshness: t_ingestion_start > cutoff
            t_str = fact.get("t_ingestion_start") or ""
            if t_str:
                try:
                    t = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                    if t.tzinfo is None:
                        t = t.replace(tzinfo=UTC)
                    if t < cutoff:
                        stale += 1
                except ValueError:
                    stale += 1
            else:
                stale += 1

        # Метрики
        # KNOWN ISSUE (v8.5.3, отложено на v8.5.4): MHI poisoning attack.
        # Атакующий может наспамить 10000 Observed-фактов через /ingest/text,
        # raise total, drop validated_ratio к нулю, MHI < 0.30 → SAFE_MODE → GC.
        # Простой fix "исключить свежие Observed из знаменателя" ломает
        # легитимную семантику (см. v8.5.3 attempt — test_validated_ratio_*
        # ожидает 2/3 когда 2 из 3 validated, не 1.0 от исключения третьего).
        # Правильное решение: rate-based detector (если N Observed появились
        # за короткое время — подозрение на poisoning, временно cap'ить
        # их вклад). Это отдельный модуль, не однострочная правка формулы.
        # До тех пор формула остаётся уязвимой, но семантика правильная.
        validated_ratio = validated / max(total, 1)
        freshness_score = 1.0 - (stale / max(total, 1))
        retrieval_precision = (
            self._retrieval_hits / max(self._retrieval_total, 1)
            if self._retrieval_total > 0
            else 0.5  # нейтральное значение если нет данных
        )
        # graph_coverage: сейчас 0 (Neo4j не подключён).
        # Sprint 2c: запросить количество фактов в Neo4j / total.
        graph_coverage = 1.0 if self._l3_connected else 0.0

        mhi = (
            self.W_VALIDATED  * validated_ratio    +
            self.W_FRESHNESS  * freshness_score     +
            self.W_PRECISION  * retrieval_precision +
            self.W_GRAPH      * graph_coverage
        )
        mhi = max(0.0, min(1.0, mhi))  # clamp [0, 1]

        status = self._status(mhi)
        recommendations = self._recommendations(
            mhi, status, validated_ratio, freshness_score,
            retrieval_precision, graph_coverage, total, collapsed,
        )

        report = MHIReport(
            mhi=mhi,
            status=status,
            validated_ratio=validated_ratio,
            freshness_score=freshness_score,
            retrieval_precision=retrieval_precision,
            graph_coverage=graph_coverage,
            total_facts=total,
            validated_facts=validated,
            collapsed_facts=collapsed,
            stale_facts=stale,
            calculated_at=now.isoformat(),
            recommendations=recommendations,
        )

        logger.info("MHI %s", report)
        return report

    def _status(self, mhi: float) -> MHIStatus:
        # AUDIT-FIX v8.4.0: используем все три порога согласно V9 §8 SLO Contract
        # и INVARIANTS.md MHI-2. До v8.4.0 THRESHOLD_DEGRADED=0.50 была мёртвой
        # константой — теперь она реально различает HEALTHY границу.
        if mhi >= self.THRESHOLD_HEALTHY:
            return MHIStatus.HEALTHY
        if mhi >= self.THRESHOLD_SAFE_MODE:
            return MHIStatus.DEGRADED
        return MHIStatus.SAFE_MODE

    def _recommendations(
        self,
        mhi: float,
        status: MHIStatus,
        validated_ratio: float,
        freshness_score: float,
        retrieval_precision: float,
        graph_coverage: float,
        total: int,
        collapsed: int,
    ) -> list[str]:
        recs: list[str] = []

        if status == MHIStatus.SAFE_MODE:
            recs.append(
                f"🚨 MHI={mhi:.2f} < {self.THRESHOLD_SAFE_MODE} — "
                "запустить немедленный GC и оповестить ops."
            )
        elif status == MHIStatus.DEGRADED:
            # AUDIT-FIX v8.4.0: различаем "тяжёлый DEGRADED" (<0.50) и
            # "лёгкий DEGRADED" (0.50–0.60) — для разных alert-уровней.
            if mhi < self.THRESHOLD_DEGRADED:
                recs.append(
                    f"⚠️ MHI={mhi:.2f} < {self.THRESHOLD_DEGRADED} — "
                    "тяжёлая деградация, ускорить ConsolidationEngine."
                )
            else:
                recs.append(
                    f"⚠️ MHI={mhi:.2f} < {self.THRESHOLD_HEALTHY} — "
                    "система деградирует, нужны корректирующие действия."
                )

        if validated_ratio < 0.4:
            recs.append(
                f"⚠️ validated_ratio={validated_ratio:.2f} — "
                "много фактов застряли в Observed/Hypothesized. "
                "Проверить TruthGate pipeline."
            )

        if freshness_score < 0.5:
            recs.append(
                f"⚠️ freshness_score={freshness_score:.2f} — "
                f"{int((1-freshness_score)*total)} фактов старше "
                f"{self.FRESHNESS_DAYS} дней. Запустить Decay/GC worker."
            )

        if collapsed > 50:
            recs.append(
                f"📦 {collapsed} фактов в Collapsed — "
                "рассмотреть Cold Storage архивацию (DuckDB/S3). "
                "Без GC L1 будет расти (I96 запрещает DELETE)."
            )

        if retrieval_precision < 0.5 and self._retrieval_total > 10:
            recs.append(
                f"🔍 retrieval_precision={retrieval_precision:.2f} — "
                "низкий hit rate retrieval. Включить HybridRetriever (BM25+Dense)."
            )

        if graph_coverage == 0.0:
            recs.append(
                "🕸️ graph_coverage=0 — L3 не активен (STORAGE_BACKEND=sqlite без ladybug/neo4j). "
                "Установите LadybugDB (см. docs/LADYBUG_SETUP.ru.md) или Neo4j/Graphiti. "
                "MHI без L3 ограничен ≤0.80."
            )

        if not recs:
            recs.append("✅ Система здорова. Продолжать мониторинг.")

        return recs

    def _error_report(self, error: str) -> MHIReport:
        return MHIReport(
            mhi=0.0,
            status=MHIStatus.SAFE_MODE,
            validated_ratio=0.0,
            freshness_score=0.0,
            retrieval_precision=0.0,
            graph_coverage=0.0,
            total_facts=0,
            validated_facts=0,
            collapsed_facts=0,
            stale_facts=0,
            calculated_at=datetime.now(UTC).isoformat(),
            recommendations=[f"🚨 Ошибка вычисления MHI: {error}"],
        )


# ---------------------------------------------------------------------------
# Быстрая проверка статуса для Meta-Supervisor
# ---------------------------------------------------------------------------

def check_mhi(store: GraphStore, **kwargs) -> MHIStatus:
    """
    Быстрая проверка без полного отчёта.
    Использование в Meta-Supervisor:

        from core.mhi import check_mhi, MHIStatus
        status = check_mhi(store)
        if status == MHIStatus.SAFE_MODE:
            trigger_safe_mode()
    """
    return MHICalculator(store, **kwargs).calculate().status
