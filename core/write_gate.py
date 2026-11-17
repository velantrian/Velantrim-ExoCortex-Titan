"""
🛡️ core/write_gate.py — mandatory canonical Write Protocol Gate.

Закрывает находку аудита: `store_fact` / server `/facts` писали факты В ПАМЯТЬ БЕЗ
truth-гейта — то есть «truth-движок построен, но не подключён к записи». Этот гейт
СУДИТ допуск факта (сам не пишет). Консервативен: блокирует только явно нелегитимное;
субъективное (EMOTION/OPINION/…) и UNKNOWN допускает (хранятся как Observed; промоушн
до Validated/ImmutableCore guard'ится `truth_policy.modality_guard` отдельно).

Правила (разделы 20-21 спеки v1.1):
  • WORLD_FACT без источника             → reject (факт о мире обязан иметь провенанс)
  • WORLD_FACT + LLM_OUTPUT без evidence  → reject (LLM сам не верифицирует мир)
  • остальное                             → allow

Since Titan's local-first P0 policy, this boundary is mandatory.  The legacy
ENABLE_WRITE_GATE setting remains readable for compatibility/diagnostics but
cannot disable canonical admission checks.
"""
from __future__ import annotations


def resolve_admission_types(
    claim: str, source: str, claim_type=None, origin_type=None,
) -> tuple[str, str, str | None]:
    """Resolve both modality axes before admission; never turn failure into UNKNOWN.

    UNKNOWN is an auto-classification sentinel. Explicit supported values remain
    overrides. The returned reason is content-free and suitable for write results.
    This helper makes no policy decision and performs no writes.
    """
    from core.validators import (
        ClaimType, OriginType, normalize_claim_type, normalize_origin_type,
    )

    values = []
    for raw, allowed, normalize in (
        (claim_type, ClaimType.ALL, normalize_claim_type),
        (origin_type, OriginType.ALL, normalize_origin_type),
    ):
        if raw is None or raw == "":
            values.append("UNKNOWN")
            continue
        if not isinstance(raw, str):
            return "UNKNOWN", "UNKNOWN", "invalid_modality_type"
        normalized = normalize(raw)
        if normalized not in allowed or (
            normalized == "UNKNOWN" and raw.strip().upper() != "UNKNOWN"
        ):
            return "UNKNOWN", "UNKNOWN", "invalid_modality_type"
        values.append(normalized)
    ct, ot = values
    if ct == "UNKNOWN" or ot == "UNKNOWN":
        try:
            from core.claim_classifier import classify_claim

            ct, ot, _ = classify_claim(
                claim, source,
                explicit_claim_type=None if ct == "UNKNOWN" else ct,
                explicit_origin_type=None if ot == "UNKNOWN" else ot,
            )
            if ct not in ClaimType.ALL or ot not in OriginType.ALL:
                return "UNKNOWN", "UNKNOWN", "claim_classification_failed"
        except Exception:
            return "UNKNOWN", "UNKNOWN", "claim_classification_failed"
    return ct, ot, None


def is_write_gate_enabled() -> bool:
    """Compatibility readout: the mandatory gate is always enabled."""
    return True


class WritesBlockedError(RuntimeError):
    """PolicyKernel denied a canonical mutation."""

    def __init__(
        self,
        reason_code: str,
        *,
        snapshot_id: str | None = None,
    ) -> None:
        self.reason_code = reason_code
        self.snapshot_id = snapshot_id
        label = "SAFE_MODE" if reason_code == "safe_mode_writes_blocked" else "PolicyKernel"
        super().__init__(f"{label}: canonical writes blocked ({reason_code})")


def check_writes_allowed() -> tuple[bool, str]:
    """Return the current canonical-write decision with a stable reason."""
    from core.policy_kernel import get_policy_kernel

    decision = get_policy_kernel().canonical_write_decision()
    return decision.allowed, decision.reason_code


def ensure_writes_allowed() -> None:
    """Raise when the immutable policy snapshot denies a canonical write."""
    from core.policy_kernel import get_policy_kernel

    decision = get_policy_kernel().canonical_write_decision()
    if not decision.allowed:
        raise WritesBlockedError(
            decision.reason_code,
            snapshot_id=decision.snapshot_id,
        )


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


__all__ = [
    "resolve_admission_types",
    "admit_fact",
    "is_write_gate_enabled",
    "check_writes_allowed",
    "ensure_writes_allowed",
    "WritesBlockedError",
]
