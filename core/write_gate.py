"""
🛡️ core/write_gate.py — Write Protocol Gate (P0.5): единый эпистемический контроль
на write-пути в каноническую память.

Закрывает находку аудита: `store_fact` / server `/facts` писали факты В ПАМЯТЬ БЕЗ
truth-гейта — то есть «truth-движок построен, но не подключён к записи». Этот гейт
СУДИТ допуск факта (сам не пишет). Консервативен: блокирует только явно нелегитимное;
субъективное (EMOTION/OPINION/…) и UNKNOWN допускает (хранятся как Observed; промоушн
до Validated/ImmutableCore guard'ится `truth_policy.modality_guard` отдельно).

Правила (разделы 20-21 спеки v1.1):
  • WORLD_FACT без источника             → reject (факт о мире обязан иметь провенанс)
  • WORLD_FACT + LLM_OUTPUT без evidence  → reject (LLM сам не верифицирует мир)
  • остальное                             → allow

За флагом ENABLE_WRITE_GATE (default OFF) → по умолчанию поведение прежнее.
"""
from __future__ import annotations


def is_write_gate_enabled() -> bool:
    """ENABLE_WRITE_GATE (default OFF)."""
    try:
        from core.feature_config import get_config
        return bool(getattr(get_config().app, "enable_write_gate", False))
    except Exception:  # noqa: BLE001
        return False


def admit_fact(
    *,
    claim_type,
    origin_type=None,
    source: str = "",
    has_evidence: bool = False,
) -> tuple[bool, str]:
    """
    Допустить ли факт к записи в каноническую память. Возвращает (ok, reason); не бросает.

    Блокирует:
      • WORLD_FACT без непустого источника (или source=='unknown');
      • WORLD_FACT с origin_type=LLM_OUTPUT без evidence_refs.
    Всё остальное (субъективные типы, UNKNOWN, system_note) — допускается.
    """
    from core.validators import (
        ClaimType,
        OriginType,
        normalize_claim_type,
        normalize_origin_type,
    )
    ct = normalize_claim_type(claim_type)
    ot = normalize_origin_type(origin_type)
    if ct == ClaimType.WORLD_FACT:
        src = (source or "").strip()
        if not src or src.lower() == "unknown":
            return False, "world_fact_requires_source"
        if ot == OriginType.LLM_OUTPUT and not has_evidence:
            return False, "world_fact_from_llm_requires_evidence"
    return True, "ok"


__all__ = ["admit_fact", "is_write_gate_enabled"]
