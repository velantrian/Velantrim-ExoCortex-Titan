"""
core/truth_policy.py — Single law of truth admissibility + read-path verdict (T1.1).

This is the IN-PROCESS port of the contract that core/core3_adapter.py speaks to the
external Core-3 verifier: the same verdict vocabulary (allow | gap_notice | reject) and
the same question — "can an answer over these facts be trusted?". It is the single place
that decides what counts as an admissible fact and whether the read-path may answer.

Increment 1 (the P2 spine) is ADDITIVE and flag-gated (ENABLE_TRUTH_POLICY, default off):
nothing calls it on the hot path yet except the /query verdict block. Wiring the existing
write/read gates onto it (T1.2), hardening evidence everywhere (T1.3-full) and
reject-on-contradiction (T1.5) are deferred increments.

Verdict semantics (increment 1):
    REJECT       — no admissible facts at all (empty pack, or all below threshold /
                   invalid source / invalid confidence). Never fabricate an answer.
    GAP_NOTICE   — there ARE admissible facts, but none carry a structural EvidenceRef
                   (only a source tag) — honest "supported, but not citation-grade".
    ALLOW        — at least one admissible fact with a structural EvidenceRef.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field

from core.core3_adapter import ALLOW, GAP_NOTICE, REJECT  # canonical verdict vocabulary
from core.evidence import EvidenceItem
from core.thresholds import mode_thresholds
from core.validators import validate_confidence, validate_source

logger = logging.getLogger(__name__)


@dataclass
class TruthVerdict:
    """In-process truth verdict. Mirrors core3_adapter.Core3Verdict so the embedded
    policy and the subprocess verifier speak the same language."""

    decision: str                       # allow | gap_notice | reject
    truth_status: str = "unknown"
    reason: str = ""
    admissible_count: int = 0
    evidence_ids: list = field(default_factory=list)
    trace_note: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision == ALLOW

    @property
    def is_gap(self) -> bool:
        return self.decision == GAP_NOTICE

    @property
    def is_reject(self) -> bool:
        return self.decision == REJECT

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "truth_status": self.truth_status,
            "reason": self.reason,
            "admissible_count": self.admissible_count,
            "evidence_ids": self.evidence_ids,
            "trace_note": self.trace_note,
        }


def fact_admissible(
    fact: dict,
    *,
    min_conf: float | None = None,
    require_evidence: bool = False,
) -> tuple[bool, str]:
    """Single admissibility law for one fact. Returns (ok, reason); never raises.

    Admissible iff: valid non-empty source AND valid confidence in [0,1] AND
    confidence >= min_conf (default: BALANCED threshold). With require_evidence=True it
    must additionally carry a structural EvidenceRef.
    """
    if not isinstance(fact, dict):
        return False, "not_a_dict"

    ok_src, _ = validate_source(fact.get("source"))
    if not ok_src:
        return False, "no_source"

    conf = fact.get("confidence", 0.0)
    ok_conf, _ = validate_confidence(conf)
    if not ok_conf:
        return False, "invalid_confidence"

    threshold = mode_thresholds(None)["min_confidence"] if min_conf is None else float(min_conf)
    if float(conf) < threshold:
        return False, "below_confidence_threshold"

    if require_evidence and fact_evidence_ref(fact) is None:
        return False, "no_structured_evidence"

    return True, "admissible"


def fact_evidence_ref(fact: dict) -> EvidenceItem | None:
    """Extract a STRUCTURAL evidence reference from a fact, or None.

    Valid evidence lives in metadata.evidence_refs as a list of dicts carrying at least a
    source_id (optionally chunk_id/span/quote). Per canon T1.3 a plain string is NOT valid
    evidence — that is only a 'source' tag, not a citation.
    """
    if not isinstance(fact, dict):
        return None
    metadata = fact.get("metadata") or {}
    refs = metadata.get("evidence_refs")
    if not isinstance(refs, list):
        return None
    for ref in refs:
        if isinstance(ref, dict) and (ref.get("source_id") or ref.get("source")):
            return EvidenceItem(
                source_id=str(ref.get("source_id") or ref.get("source")),
                source_type=str(ref.get("source_type", "unknown")),
                source_domain=str(ref.get("source_domain", "unknown")),
                published_at=ref.get("published_at"),
                directness=float(ref.get("directness", 0.5) or 0.5),
                content_hash=ref.get("content_hash"),
                chunk_id=ref.get("chunk_id"),
                span=ref.get("span"),
                quote=ref.get("quote"),
            )
    return None


def modality_guard(
    fact: dict,
    target_epistemic_state: str,
) -> tuple[bool, str]:
    """
    Инвариант модальности (v8.7, P0): блокирует недопустимые переходы.

    Правила:
      · WORLD_FACT → может стать ImmutableCore/Validated при наличии evidence.
      · SUBJECTIVE_TYPES (EMOTION/OPINION/INTERPRETATION/PREFERENCE) → могут
        быть VALIDATED как есть, но НИКОГДА не могут стать ImmutableCore.
      · LLM_OUTPUT как origin_type → НИКОГДА не является доказательством для
        WORLD_FACT promotion.

    Возвращает (allowed: bool, reason: str).

    Использование:
        ok, reason = modality_guard(fact, "ImmutableCore")
        if not ok:
            raise ValueError(f"Modality violation: {reason}")
    """
    from core.validators import ClaimType, OriginType, normalize_claim_type, normalize_origin_type

    ct = normalize_claim_type(fact.get("claim_type"))
    ot = normalize_origin_type(fact.get("origin_type"))

    # Блокировка ImmutableCore для субъективных типов
    # Канон: чувство/мнение/интерпретация/предпочтение не могут стать
    # неизменяемым ядром знания о мире — даже если пользователь «уверен».
    if (target_epistemic_state == "ImmutableCore"
            and ct in ClaimType.SUBJECTIVE_TYPES):
        return False, (
            f"claim_type={ct!r} не может стать ImmutableCore: "
            f"субъективная модальность не является фактом о мире. "
            f"Допустимо только для WORLD_FACT."
        )

    # Блокировка: LLM_OUTPUT как единственный источник не может быть WORLD_FACT+evidence
    # (LLM генерирует текст, но не верифицирует мир сам по себе)
    if (ct == ClaimType.WORLD_FACT
            and ot == OriginType.LLM_OUTPUT
            and target_epistemic_state in ("Validated", "ImmutableCore")):
        # Не блокируем полностью — позволяем Supported (промежуточное)
        # но Validated требует независимого доказательства
        # FIX M13 (Claude audit 2026-07-28): bare list-truthiness accepted
        # ANY non-empty list here, including a list of plain strings
        # (`["i said so"]`) — canon T1.3 requires a structural EvidenceRef
        # (dict with source_id/source), which fact_evidence_ref() already
        # enforces and fact_admissible() above already uses for the same
        # purpose.
        if fact_evidence_ref(fact) is None:
            return False, (
                f"WORLD_FACT с origin_type=LLM_OUTPUT не может стать {target_epistemic_state!r} "
                f"без независимых evidence_refs. LLM-вывод не является верификацией."
            )

    # v8.7 P0.5 (поправка ChatGPT v1.1 #1): UNKNOWN-модальность (старые/неклассифи-
    # цированные записи) не может стать world-fact-grade (Validated/ImmutableCore)
    # без явной реклассификации/доказательств. Неклассифицированное идёт в cautious
    # retrieval/review, а НЕ трактуется как факт о мире. Согласовано с матрицей
    # recommend_target_state(UNKNOWN) → "Observed".
    if (ct == ClaimType.UNKNOWN
            and target_epistemic_state in ("Validated", "ImmutableCore")):
        # FIX M13 (Claude audit 2026-07-28): see the LLM_OUTPUT check above.
        if fact_evidence_ref(fact) is None:
            return False, (
                f"claim_type=UNKNOWN не может стать {target_epistemic_state!r} без "
                f"реклассификации или evidence_refs: неклассифицированная запись не "
                f"трактуется как факт о мире (→ cautious retrieval/review)."
            )

    return True, "ok"


def recommend_target_state(fact: dict) -> tuple[str, str]:
    """
    Матрица валидации (v8.7, Уточнение Qwen): по (claim_type × origin_type)
    рекомендует ЦЕЛЕВОЕ ESM-состояние. ADVISORY — не форсирует переход.

    Это дополняет modality_guard (который БЛОКИРУЕТ недопустимое): здесь — что
    РЕКОМЕНДУЕТСЯ как потолок валидации. Промоушен по-прежнему идёт только через
    transition_esm() (матрица ESM) + modality_guard. Новые факты всегда стартуют
    в Observed (инвариант I50); эта функция — подсказка для consolidation/promotion.

    Матрица (Qwen RFC + сверка с каноном):
        WORLD_FACT + EXTERNAL+evidence → Validated   (внешний источник + цитата)
        WORLD_FACT + EXTERNAL          → Supported    (внешний, но без структурной цитаты)
        WORLD_FACT + USER_REPORTED     → Hypothesized (со слов — требует подтверждения)
        WORLD_FACT + LLM_OUTPUT        → Observed      (LLM сам не верифицирует мир)
        EMOTION/OPINION/INTERPRETATION/PREFERENCE/GOAL/USER_EXPERIENCE
                   + USER_REPORTED     → Validated     (истинно как модальность)
        (любой субъективный) + LLM_OUTPUT → Hypothesized (LLM-сгенерированное — слабее)
        SYSTEM_NOTE                    → Supported
        UNKNOWN / прочее               → Observed       (консервативно)

    Возвращает (recommended_state, reason).
    """
    from core.validators import (
        ClaimType,
        OriginType,
        normalize_claim_type,
        normalize_origin_type,
    )

    ct = normalize_claim_type(fact.get("claim_type"))
    ot = normalize_origin_type(fact.get("origin_type"))

    # WORLD_FACT — зависит от происхождения
    if ct == ClaimType.WORLD_FACT:
        if ot == OriginType.EXTERNAL:
            if fact_evidence_ref(fact) is not None:
                return "Validated", "world_fact_external_with_evidence"
            return "Supported", "world_fact_external_no_structural_evidence"
        if ot == OriginType.DERIVED:
            return "Hypothesized", "world_fact_derived_needs_review"
        if ot == OriginType.USER_REPORTED:
            return "Hypothesized", "world_fact_user_reported_needs_confirmation"
        if ot == OriginType.LLM_OUTPUT:
            return "Observed", "world_fact_llm_output_not_self_verifying"
        return "Observed", "world_fact_unknown_origin"

    # Служебная заметка — отдельно (раньше SELF_VALIDATING, в которое тоже входит)
    if ct == ClaimType.SYSTEM_NOTE:
        return "Supported", "system_note"

    # Субъективные/самовалидируемые типы
    if ct in ClaimType.SELF_VALIDATING:
        if ot == OriginType.LLM_OUTPUT:
            return "Hypothesized", "subjective_llm_generated_weaker"
        # USER_REPORTED или любой человеческий источник → валидно как модальность
        return "Validated", f"{ct.lower()}_valid_as_modality"

    return "Observed", "unknown_claim_type_conservative"


def decide(query: str, facts: Iterable[dict], mode: str = "BALANCED") -> TruthVerdict:
    """Compute an explicit read-path verdict over a fact pack. Never raises."""
    facts = list(facts or [])
    min_conf = mode_thresholds(mode)["min_confidence"]

    admissible = [f for f in facts if fact_admissible(f, min_conf=min_conf)[0]]
    if not admissible:
        return TruthVerdict(
            decision=REJECT,
            truth_status="no_admissible_facts",
            reason="no_facts" if not facts else "all_below_threshold",
            admissible_count=0,
            trace_note=f"0/{len(facts)} facts admissible at min_conf={min_conf}",
        )

    evidence_ids: list = []
    auth_scores: list = []
    for f in admissible:
        ref = fact_evidence_ref(f)
        if ref is not None:
            evidence_ids.append(ref.source_id)
            try:
                from core.evidence import compute_source_authenticity

                meta_refs = (f.get("metadata") or {}).get("evidence_refs") or []
                first = meta_refs[0] if isinstance(meta_refs, list) and meta_refs else {}
                auth_scores.append(compute_source_authenticity(
                    getattr(ref, "source_type", "unknown") or "unknown",
                    verification_count=int(first.get("verification_count", 0) or 0),
                    contradiction_rate=float(first.get("contradiction_rate", 0.0) or 0.0),
                ))
            except Exception:  # noqa: BLE001 — authenticity is advisory, never blocks
                pass

    if not evidence_ids:
        # v8.7 P0: для субъективных типов отсутствие evidence_refs — не gap_notice,
        # они валидны «как есть» (EMOTION/OPINION/etc. не требуют внешней цитаты).
        from core.validators import ClaimType, normalize_claim_type
        all_subjective = all(
            normalize_claim_type(f.get("claim_type")) in ClaimType.SELF_VALIDATING
            for f in admissible
        )
        if all_subjective:
            return TruthVerdict(
                decision=ALLOW,
                truth_status="subjective_validated",
                reason="subjective_types_self_valid",
                admissible_count=len(admissible),
                evidence_ids=[],
                trace_note=(
                    f"{len(admissible)} subjective fact(s) — "
                    f"valid as experience/opinion/emotion without citation"
                ),
            )
        return TruthVerdict(
            decision=GAP_NOTICE,
            truth_status="supported_no_evidence",
            reason="no_structured_evidence",
            admissible_count=len(admissible),
            trace_note=(
                f"{len(admissible)} admissible fact(s), but none carry a structural EvidenceRef"
            ),
        )

    auth_note = ""
    if auth_scores:
        avg_auth = round(sum(auth_scores) / len(auth_scores), 4)
        auth_note = f", avg_authenticity={avg_auth}"
    return TruthVerdict(
        decision=ALLOW,
        truth_status="evidenced",
        reason="ok",
        admissible_count=len(admissible),
        evidence_ids=evidence_ids,
        trace_note=f"{len(admissible)} admissible, {len(evidence_ids)} with evidence{auth_note}",
    )


__all__ = [
    "TruthVerdict",
    "fact_admissible",
    "fact_evidence_ref",
    "modality_guard",
    "recommend_target_state",
    "decide",
    "ALLOW",
    "GAP_NOTICE",
    "REJECT",
]
