"""
🫀 core/promotion_policy.py — Градуированная петля обучения (P0, детерминированная)
================================================================================

Цель (задумка автора): «память умнеет от общения». Факты поднимаются по лестнице
ESM НЕ по одному числу `confidence`, а по реальным сигналам доказательности:

    • корроборация   — сколько РАЗНЫХ источников утверждают то же самое
    • доверие         — источник из доверенного списка (ring_zero/domain_seed/...)
    • выдержка        — факт «дожил» без противоречий (стабильность во времени)
    • противоречия    — есть ли конфликт (тогда демоушен, а не повышение)

Один шаг за прогон. За несколько сессий факт «дозревает» Observed→…→Validated,
как у человека: сначала гипотеза, потом подтверждение, потом знание.

Дисциплина (как Essence):
  • аддитивно, за флагом `ENABLE_GRADUATED_PROMOTION` (по умолчанию ВЫКЛ);
  • без LLM, stdlib-only; не трогает stable `/query` и существующий ConsolidationEngine;
  • все переходы — ТОЛЬКО через матрицу ESM (`transition_esm`) → нелегальных скачков нет.

Контраст с наивным ConsolidationEngine: тот делает Observed→Validated при
`confidence>=0.75` — одиночный непроверенный факт «random_blog» мгновенно становится
«истиной». Здесь такой факт дойдёт лишь до `Hypothesized`, пока его не подтвердят
другие источники или время.
"""
from __future__ import annotations

import os
import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Доверенные источники (I98): им можно верить быстрее.
DEFAULT_TRUSTED_SOURCES = frozenset({"ring_zero", "domain_seed", "system_axiom"})


def is_graduated_promotion_enabled() -> bool:
    """Флаг подключения к runtime (по умолчанию ВЫКЛ). Модуль аддитивен."""
    return os.getenv("ENABLE_GRADUATED_PROMOTION", "false").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class PromotionConfig:
    """Пороги лестницы. Всё настраивается через ENV или аргументы."""
    min_claim_len: int = 8
    support_corroboration: int = 2      # источников, чтобы дойти до Supported (answer-eligible!)
    validate_corroboration: int = 3     # источников, чтобы дойти до Validated
    validate_min_age_s: float = 86_400  # выдержка перед Validated (по умолч. 1 день)
    validate_min_conf: float = 0.75

    @classmethod
    def from_env(cls) -> PromotionConfig:
        def _f(name: str, default: float) -> float:
            try:
                return float(os.getenv(name, str(default)))
            except ValueError:
                return default

        def _i(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except ValueError:
                return default

        return cls(
            min_claim_len=_i("PROMOTION_MIN_CLAIM_LEN", 8),
            support_corroboration=_i("PROMOTION_SUPPORT_CORROBORATION", 2),
            validate_corroboration=_i("PROMOTION_VALIDATE_CORROBORATION", 3),
            validate_min_age_s=_f("PROMOTION_VALIDATE_MIN_AGE_S", 86_400),
            validate_min_conf=_f("PROMOTION_VALIDATE_MIN_CONF", 0.75),
        )


@dataclass
class Evidence:
    """Сигналы доказательности для одного факта."""
    corroboration: int = 1          # число РАЗНЫХ источников с тем же claim (включая свой)
    source_trusted: bool = False
    age_seconds: float = 0.0
    confidence: float = 0.0
    has_contradiction: bool = False


def recommend_transition(
    state: str,
    claim: str,
    ev: Evidence,
    cfg: PromotionConfig | None = None,
) -> str | None:
    """
    Вернуть СЛЕДУЮЩИЙ рекомендованный ESM-переход (ровно один шаг) или None.

    Лестница: Observed → Hypothesized → Supported → Validated.
    Supported/Validated дают право отвечать → требуют реальных доказательств.
    """
    cfg = cfg or PromotionConfig()
    claim = (claim or "").strip()

    # Противоречие → демоушен из доказательных состояний; иначе НЕ повышаем
    # контрадикт-факт (держим, пока резолвер не разрешит — фикс M4: не давать
    # факту стать Validated в том же цикле, где его признают противоречивым).
    if ev.has_contradiction:
        if state in {"Supported", "Validated"}:
            return "Contradicted"
        return None

    if len(claim) < cfg.min_claim_len:
        return None

    has_evidence = ev.source_trusted or ev.corroboration >= cfg.support_corroboration

    if state == "Observed":
        # V8.8 ESM: из Observed только в Hypothesized (один шаг за цикл).
        return "Hypothesized"

    if state == "Hypothesized":
        return "Supported" if has_evidence else None

    if state == "Supported":
        ready = ev.source_trusted or ev.corroboration >= cfg.validate_corroboration
        if (ready
                and ev.age_seconds >= cfg.validate_min_age_s
                and ev.confidence >= cfg.validate_min_conf
                and not ev.has_contradiction):
            return "Validated"
        return None

    return None


# ── helpers ──────────────────────────────────────────────────────────────────


def _normalize_claim(claim: str) -> str:
    """Нормализация для сопоставления одинаковых утверждений из разных источников."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (claim or "").lower())).strip()


def compute_corroboration(facts: Sequence[dict[str, Any]]) -> dict[str, int]:
    """
    fact_id → число РАЗНЫХ источников, утверждающих тот же (нормализованный) claim.
    Одинокий факт = 1; два факта с тем же claim из двух источников = 2.
    """
    sources_by_claim: dict[str, set] = {}
    for f in facts:
        key = _normalize_claim(f.get("claim", ""))
        if not key:
            continue
        src = str(f.get("source", "")).strip().lower()
        sources_by_claim.setdefault(key, set()).add(src)

    out: dict[str, int] = {}
    for f in facts:
        fid = f.get("fact_id")
        if not fid:
            continue
        key = _normalize_claim(f.get("claim", ""))
        out[str(fid)] = len(sources_by_claim.get(key, set())) or 1
    return out


def _age_seconds(fact: dict[str, Any], now: datetime | None = None) -> float:
    ts = fact.get("t_ingestion_start")
    if not ts:
        return 0.0
    try:
        start = datetime.fromisoformat(ts)
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        now = now or datetime.now(UTC)
        return max(0.0, (now - start).total_seconds())
    except (ValueError, TypeError):
        return 0.0


@dataclass
class PromotionReport:
    scanned: int = 0
    promoted: dict[str, int] = field(default_factory=dict)  # "Observed->Supported": n
    demoted: int = 0
    unchanged: int = 0
    errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "promoted": dict(self.promoted),
            "promoted_total": sum(self.promoted.values()),
            "demoted": self.demoted,
            "unchanged": self.unchanged,
            "errors": self.errors,
        }


def run_graduated_promotion(
    store: Any,
    cfg: PromotionConfig | None = None,
    trusted_sources: Collection[str] = DEFAULT_TRUSTED_SOURCES,
    now: datetime | None = None,
    corroboration_override: dict[str, int] | None = None,
    contradicted_ids: set | None = None,
) -> PromotionReport:
    """
    Прогнать петлю по всем непроверенным фактам стора. Один шаг лестницы на факт.
    Переходы выполняются через store.transition_esm (матрица ESM соблюдается).

    Примечание: семантическое определение противоречий — future work; здесь
    `has_contradiction=False` (демоушен через противоречия делает drift-protection
    в memory.py). Политика правило поддерживает и протестирована отдельно.
    """
    cfg = cfg or PromotionConfig.from_env()
    trusted = {s.strip().lower() for s in trusted_sources}
    report = PromotionReport()

    try:
        all_facts = store.get_all_facts()
    except Exception:  # noqa: BLE001
        all_facts = []
    # Корроборация: переданная (напр. СЕМАНТИЧЕСКАЯ из sleep-loop) или лексическая по умолчанию.
    corro = corroboration_override if corroboration_override is not None else compute_corroboration(all_facts)
    now = now or datetime.now(UTC)

    for f in all_facts:
        state = f.get("epistemic_state")
        if state not in {"Observed", "Hypothesized", "Supported"}:
            continue
        report.scanned += 1
        fid = f.get("fact_id")
        ev = Evidence(
            corroboration=corro.get(str(fid), 1),
            source_trusted=str(f.get("source", "")).strip().lower() in trusted,
            age_seconds=_age_seconds(f, now),
            confidence=float(f.get("confidence", 0.0) or 0.0),
            # M4: факт, помеченный как сторона противоречия, не повышается в этом цикле.
            has_contradiction=bool(contradicted_ids and str(fid) in contradicted_ids),
        )
        target = recommend_transition(state, f.get("claim", ""), ev, cfg)
        if not target:
            report.unchanged += 1
            continue
        try:
            ok = store.transition_esm(fid, target, by="graduated_promotion")
            if ok:
                key = f"{state}->{target}"
                report.promoted[key] = report.promoted.get(key, 0) + 1
                if target == "Contradicted":
                    report.demoted += 1
        except Exception:  # noqa: BLE001
            report.errors += 1

    return report


__all__ = [
    "PromotionConfig",
    "Evidence",
    "PromotionReport",
    "recommend_transition",
    "compute_corroboration",
    "run_graduated_promotion",
    "is_graduated_promotion_enabled",
    "DEFAULT_TRUSTED_SOURCES",
]
