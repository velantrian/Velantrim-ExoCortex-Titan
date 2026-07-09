"""
🛡️ core/meta_supervisor.py — MetaSupervisor Apex Controller (V8.7 Titan, из Crystal)

Назначение: автономная иммунная система. Читает MHI, SLO-метрики и ПРИНИМАЕТ РЕШЕНИЯ.
Не спрашивает человека. Защищает граф от деградации.

Переходы:
    HEALTHY  → NORMAL      (всё ок)
    HEALTHY  → DEGRADED    (MHI<0.50 или budget>0.85 или DLQ>10)
    DEGRADED → SAFE_MODE   (MHI<0.30 или DLQ>50)
    SAFE_MODE → DEGRADED   (MHI≥0.50 и DLQ<10)
    DEGRADED → HEALTHY     (MHI≥0.60 и DLQ<5)

Действия:
    DEGRADED: ускорить ConsolidationEngine ×2, бюджет -10%, WARN-лог
    SAFE_MODE: L3 read-only, блокировка ВСЕХ пишущих операций, CRITICAL-алерт

Инвариант:
    I-META1: MetaSupervisor NE пишет в граф. Только читает и управляет режимом.
    I-META2: Переход в SAFE_MODE необратим без ручного подтверждения (вручную или через API).

Heartbeat: каждые 10 секунд.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("velantrim.meta_supervisor")

# ─── Режимы ───────────────────────────────────────────────────────────────────

class SystemMode(str, Enum):
    HEALTHY  = "healthy"
    DEGRADED = "degraded"
    SAFE_MODE = "safe_mode"


@dataclass
class SupervisorSnapshot:
    """Снимок состояния MetaSupervisor."""
    mode: SystemMode
    mhi: float
    mhi_status: str
    dlq_size: int
    budget_pressure: float
    uptime_seconds: float
    transition_count: int
    last_action: str
    recommendations: List[str] = field(default_factory=list)
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "mhi": round(self.mhi, 3),
            "mhi_status": self.mhi_status,
            "dlq_size": self.dlq_size,
            "budget_pressure": round(self.budget_pressure, 3),
            "uptime_seconds": round(self.uptime_seconds, 1),
            "transition_count": self.transition_count,
            "last_action": self.last_action,
            "recommendations": self.recommendations,
            "checked_at": self.checked_at,
        }


# ─── Конфигурация ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SupervisorConfig:
    """Пороги из Crystal SLO Contract."""
    # MHI пороги
    mhi_healthy:   float = 0.60
    mhi_degraded:  float = 0.50
    mhi_safe_mode: float = 0.30

    # DLQ пороги
    dlq_warn:      int = 10
    dlq_safe_mode: int = 50

    # Budget пороги
    budget_warn:   float = 0.85
    budget_block:  float = 0.90

    # Интервалы
    heartbeat_sec: float = 10.0
    mhi_check_sec: float = 30.0
    gc_interval_sec: float = 3600.0  # раз в час в HEALTHY

    # Безопасность
    safe_mode_require_manual_confirm: bool = True


# ─── MetaSupervisor ────────────────────────────────────────────────────────────

class MetaSupervisor:
    """
    Апекс-контроллер иммунной системы Velantrim.

    Читает MHI, EventBus DLQ, бюджет — и ПЕРЕВОДИТ систему между режимами.
    Не пишет в граф. Не генерирует ответы. Только защищает.

    Использование:
        supervisor = MetaSupervisor()
        await supervisor.start()
        # ... система работает ...
        await supervisor.stop()
    """

    def __init__(
        self,
        *,
        config: Optional[SupervisorConfig] = None,
        on_degraded: Optional[Callable[[], None]] = None,
        on_safe_mode: Optional[Callable[[], None]] = None,
        on_recovery: Optional[Callable[[], None]] = None,
    ):
        self._config = config or SupervisorConfig()
        self._mode: SystemMode = SystemMode.HEALTHY
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._started_at = datetime.now(timezone.utc)
        self._transition_count = 0
        self._last_action = "init"
        self._mhi_cache: float = 1.0
        self._mhi_status_cache: str = "HEALTHY"
        self._dlq_cache: int = 0
        self._budget_cache: float = 0.0

        # Callback-и для внешних реакций
        self._on_degraded = on_degraded
        self._on_safe_mode = on_safe_mode
        self._on_recovery = on_recovery

        # Флаг ручного выхода из SAFE_MODE
        self._manual_confirm: bool = False

        logger.info("MetaSupervisor created (mode=HEALTHY)")

    # ── Свойства ──────────────────────────────────────────────────────────

    @property
    def mode(self) -> SystemMode:
        return self._mode

    @property
    def is_healthy(self) -> bool:
        return self._mode == SystemMode.HEALTHY

    @property
    def is_degraded(self) -> bool:
        return self._mode == SystemMode.DEGRADED

    @property
    def is_safe_mode(self) -> bool:
        return self._mode == SystemMode.SAFE_MODE

    @property
    def writes_blocked(self) -> bool:
        """В SAFE_MODE все записи в L3 заблокированы."""
        return self._mode == SystemMode.SAFE_MODE

    # ── Управление ─────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Запустить heartbeat-цикл."""
        if self._running:
            return
        self._running = True
        self._started_at = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("MetaSupervisor started (heartbeat=%.0fs)", self._config.heartbeat_sec)

    async def stop(self) -> None:
        """Остановить heartbeat-цикл."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MetaSupervisor stopped")

    def confirm_safe_mode_exit(self) -> None:
        """Разрешить выход из SAFE_MODE (ручное подтверждение)."""
        self._manual_confirm = True
        logger.warning("SAFE_MODE exit confirmed manually")

    # ── Heartbeat ──────────────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        last_gc = 0.0

        while self._running:
            try:
                now = datetime.now(timezone.utc)
                elapsed = (now - self._started_at).total_seconds()

                # Сбор метрик
                self._collect_mhi()

                # Оценка → возможный переход
                await self._evaluate(elapsed)

                # Действия по режиму
                if self._mode == SystemMode.DEGRADED:
                    if elapsed - last_gc > self._config.gc_interval_sec / 2:
                        self._action_gc_accelerated()
                        last_gc = elapsed

                elif self._mode == SystemMode.SAFE_MODE:
                    # В SAFE_MODE: GC раз в 10 минут (очень агрессивно)
                    if elapsed - last_gc > 600:
                        self._action_gc_emergency()
                        last_gc = elapsed

                elif self._mode == SystemMode.HEALTHY:
                    # Нормальный GC раз в час
                    if elapsed - last_gc > self._config.gc_interval_sec:
                        self._action_gc_normal()
                        last_gc = elapsed

                await asyncio.sleep(self._config.heartbeat_sec)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("MetaSupervisor heartbeat error: %s", exc, exc_info=True)
                await asyncio.sleep(self._config.heartbeat_sec)

    # ── Сбор метрик ────────────────────────────────────────────────────────

    def _collect_mhi(self) -> None:
        """Собрать MHI и SLO-метрики из живых компонентов."""
        try:
            from core.event_bus import get_event_bus

            # MHI
            store = None
            try:
                from core.memory import _GLOBAL_STORE
                store = _GLOBAL_STORE
            except Exception:
                pass

            if store is not None:
                # FIX #1 (Claude audit): compute_mhi — устаревшая функция.
                # Заменена на MHICalculator(store).calculate().
                # Сбор MHI/DLQ/budget разнесён по отдельным try-блокам —
                # сбой одного канала не теряет остальные.
                mhi_ok = False
                try:
                    from core.mhi import MHICalculator
                    calc = MHICalculator(store)
                    report = calc.calculate()
                    self._mhi_cache = report.mhi
                    self._mhi_status_cache = report.status.value
                    mhi_ok = True
                except Exception as exc:
                    logger.warning("MetaSupervisor: MHI collection failed: %s", exc)

                if not mhi_ok:
                    # Fallback: сохранить предыдущее значение, не перезаписывать
                    if self._mhi_cache == 1.0:  # ещё ни разу не собирали
                        self._mhi_cache = 0.75
                        self._mhi_status_cache = "DEGRADED"
            else:
                self._mhi_cache = 1.0
                self._mhi_status_cache = "HEALTHY"

            # DLQ
            try:
                bus = get_event_bus()
                self._dlq_cache = len(bus._dlq)
            except Exception:
                self._dlq_cache = 0

            # Budget pressure (упрощённо: факты / capacity)
            try:
                from core.memory_budget import get_budget_planner
                planner = get_budget_planner()
                self._budget_cache = planner.fill_ratio
            except Exception:
                self._budget_cache = 0.0

        except Exception as exc:
            logger.debug("MHI collection skipped: %s", exc)

    # ── Оценка и переходы ──────────────────────────────────────────────────

    async def _evaluate(self, elapsed: float) -> None:
        """Оценить состояние и выполнить переход если нужно."""
        cfg = self._config

        # Чтение текущих метрик
        mhi = self._mhi_cache
        dlq = self._dlq_cache
        budget = self._budget_cache

        # ── Переходы ──────────────────────────────────────────────────

        if self._mode == SystemMode.SAFE_MODE:
            # Выход из SAFE_MODE — только ручное подтверждение
            if self._manual_confirm and mhi >= cfg.mhi_healthy and dlq < cfg.dlq_warn:
                self._mode = SystemMode.HEALTHY
                self._manual_confirm = False
                self._last_action = f"SAFE_MODE→HEALTHY (manual confirm, MHI={mhi:.2f})"
                self._transition_count += 1
                logger.warning("☑️  SAFE_MODE → HEALTHY (manual)")
                self._fire_recovery()
            # Иначе — остаёмся в SAFE_MODE
            return

        if self._mode == SystemMode.DEGRADED:
            # Восстановление
            if mhi >= cfg.mhi_healthy and dlq < cfg.dlq_warn:
                self._mode = SystemMode.HEALTHY
                self._last_action = f"DEGRADED→HEALTHY (MHI={mhi:.2f})"
                self._transition_count += 1
                logger.info("✅ DEGRADED → HEALTHY")
                self._fire_recovery()
                return

            # Ухудшение → SAFE_MODE
            if mhi < cfg.mhi_safe_mode or dlq > cfg.dlq_safe_mode or budget > cfg.budget_block:
                self._mode = SystemMode.SAFE_MODE
                self._last_action = (
                    f"DEGRADED→SAFE_MODE (MHI={mhi:.2f}, DLQ={dlq}, budget={budget:.2f})"
                )
                self._transition_count += 1
                logger.critical(
                    "🔴 SAFE_MODE: MHI=%.3f DLQ=%d budget=%.2f — L3 READ-ONLY",
                    mhi, dlq, budget,
                )
                self._fire_safe_mode()
                return

        if self._mode == SystemMode.HEALTHY:
            # HEALTHY → SAFE_MODE (прямой переход при критической деградации)
            if mhi < cfg.mhi_safe_mode or dlq > cfg.dlq_safe_mode:
                self._mode = SystemMode.SAFE_MODE
                self._last_action = f"HEALTHY→SAFE_MODE (MHI={mhi:.2f}, DLQ={dlq})"
                self._transition_count += 1
                logger.critical("🔴 SAFE_MODE: критическая деградация")
                self._fire_safe_mode()
                return

            # HEALTHY → DEGRADED
            if mhi < cfg.mhi_degraded or dlq > cfg.dlq_warn or budget > cfg.budget_warn:
                self._mode = SystemMode.DEGRADED
                self._last_action = f"HEALTHY→DEGRADED (MHI={mhi:.2f}, DLQ={dlq}, budget={budget:.2f})"
                self._transition_count += 1
                logger.warning("⚠️  DEGRADED: MHI=%.3f — ускорение консолидации", mhi)
                self._fire_degraded()

    # ── Действия ───────────────────────────────────────────────────────────

    def _action_gc_normal(self) -> None:
        """Нормальный GC (HEALTHY)."""
        logger.debug("MetaSupervisor: normal GC pulse")

    def _action_gc_accelerated(self) -> None:
        """Ускоренный GC (DEGRADED) — чистим агрессивнее."""
        logger.debug("MetaSupervisor: accelerated GC (DEGRADED)")
        # Сигнал ConsolidationEngine — ускориться
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            asyncio.create_task(bus.publish({
                "type": "supervisor_gc_accelerate",
                "reason": "degraded_mode",
            }, dispatch=False))
        except Exception:
            pass

    def _action_gc_emergency(self) -> None:
        """Экстренный GC (SAFE_MODE)."""
        logger.warning("MetaSupervisor: EMERGENCY GC (SAFE_MODE)")
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            asyncio.create_task(bus.publish({
                "type": "supervisor_gc_emergency",
                "reason": "safe_mode",
            }, dispatch=False))
        except Exception:
            pass

    # ── Callback-и ────────────────────────────────────────────────────────

    def _fire_degraded(self) -> None:
        if self._on_degraded:
            try:
                self._on_degraded()
            except Exception as exc:
                logger.error("on_degraded callback: %s", exc)

    def _fire_safe_mode(self) -> None:
        if self._on_safe_mode:
            try:
                self._on_safe_mode()
            except Exception as exc:
                logger.error("on_safe_mode callback: %s", exc)

    def _fire_recovery(self) -> None:
        if self._on_recovery:
            try:
                self._on_recovery()
            except Exception as exc:
                logger.error("on_recovery callback: %s", exc)

    # ── Публичный API ─────────────────────────────────────────────────────

    def snapshot(self) -> SupervisorSnapshot:
        """Текущий снимок MetaSupervisor."""
        elapsed = (datetime.now(timezone.utc) - self._started_at).total_seconds()
        return SupervisorSnapshot(
            mode=self._mode,
            mhi=self._mhi_cache,
            mhi_status=self._mhi_status_cache,
            dlq_size=self._dlq_cache,
            budget_pressure=self._budget_cache,
            uptime_seconds=elapsed,
            transition_count=self._transition_count,
            last_action=self._last_action,
            recommendations=self._get_recommendations(),
        )

    def _get_recommendations(self) -> List[str]:
        recs: List[str] = []
        if self._mode == SystemMode.SAFE_MODE:
            recs.append("SAFE_MODE: L3 read-only. Проверить MHI, DLQ, бюджет.")
            recs.append("Выход из SAFE_MODE — ручное подтверждение.")
        elif self._mode == SystemMode.DEGRADED:
            recs.append("DEGRADED: ускорить ConsolidationEngine, проверить DLQ.")
        return recs


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_supervisor: Optional[MetaSupervisor] = None


def get_meta_supervisor() -> MetaSupervisor:
    global _supervisor
    if _supervisor is None:
        _supervisor = MetaSupervisor()
    return _supervisor


def reset_meta_supervisor() -> None:
    global _supervisor
    _supervisor = None


__all__ = [
    "MetaSupervisor",
    "SupervisorConfig",
    "SupervisorSnapshot",
    "SystemMode",
    "get_meta_supervisor",
    "reset_meta_supervisor",
]
