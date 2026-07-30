"""Shadow-only Synaptic projection for the legacy ``/query`` read path.

The runner projects already-retrieved legacy facts into source-linked capsules,
plans Working Memory, and builds a deterministic ContextPack preview.  It never
renders an answer, calls a provider, persists state, or mutates Canon/ESM.

Projection provenance is intentionally narrow: the exact source is the legacy
fact claim returned by the existing pipeline, not the fact's original document.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Iterable, Mapping

from core.context_pack import ContextPackBudget, ContextPackBuilder
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.recall_policy import is_fact_allowed_for_recall
from core.working_memory_gate import (
    GateDisposition,
    WorkingMemoryBudget,
    WorkingMemoryCandidate,
    WorkingMemoryGate,
)

SHADOW_SCHEMA_VERSION = "synaptic.shadow-preview.v1"
SOURCE_MODE = "legacy_fact_projection"
_READER_ID = "legacy-fact-shadow-projector"
_READER_VERSION = "1.0"
_SOURCE_REVISION = "legacy-fact-projection-v1"


@dataclass(frozen=True, slots=True)
class SynapticShadowConfig:
    """Hard, deterministic bounds for one shadow preview."""

    max_items: int = 12
    max_chars: int = 4_000
    max_tokens: int = 16_384
    max_deferred_pointers: int = 32

    def __post_init__(self) -> None:
        for name in ("max_items", "max_chars", "max_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            isinstance(self.max_deferred_pointers, bool)
            or not isinstance(self.max_deferred_pointers, int)
            or self.max_deferred_pointers < 0
        ):
            raise ValueError("max_deferred_pointers must be a non-negative integer")


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _stable_id(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _fail_closed_policy_flag(mapping: Mapping[str, object], name: str) -> bool:
    """Treat malformed explicit policy markers as restrictive, never permissive."""

    if name not in mapping:
        return False
    value = mapping[name]
    return value if isinstance(value, bool) else True


def _bounded_score(*values: object) -> float:
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        score = float(value)
        if not math.isfinite(score):
            continue
        return max(0.0, min(1.0, score))
    return 0.0


def _claim_modality(fact: Mapping[str, object]) -> ClaimModality:
    raw = str(fact.get("claim_type") or "").strip().lower()
    try:
        return ClaimModality(raw)
    except ValueError:
        pass
    if fact.get("reported_only") is True or (
        str(fact.get("origin_type") or "").strip().upper() == "USER_REPORTED"
    ):
        return ClaimModality.USER_REPORT
    return ClaimModality.INTERPRETATION


def _fact_identity(fact: Mapping[str, object]) -> str:
    explicit = str(fact.get("fact_id") or fact.get("id") or "").strip()
    if explicit:
        return explicit
    return _stable_id(
        {
            "claim": str(fact.get("claim") or fact.get("text") or "").strip(),
            "source": str(fact.get("source") or "legacy-memory"),
        }
    )


def _project_fact(
    fact: Mapping[str, object],
) -> tuple[KnowledgeCapsule, WorkingMemoryCandidate] | None:
    claim_text = str(fact.get("claim") or fact.get("text") or "")
    if not claim_text.strip():
        return None

    fact_id = _fact_identity(fact)
    document_id = f"legacy-fact:{fact_id}"
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=claim_text,
        start_offset=0,
        end_offset=len(claim_text),
        source_revision=_SOURCE_REVISION,
    )
    claim = CapsuleClaim.create(
        text=claim_text,
        modality=_claim_modality(fact),
        source_spans=(span,),
        extraction_confidence=1.0,
        truth_confidence=None,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=claim_text,
        claims=(claim,),
        reader_id=_READER_ID,
        reader_version=_READER_VERSION,
        coverage_score=1.0,
        compression_ratio=1.0,
    )

    metadata = _mapping(fact.get("metadata"))
    restricted = _fail_closed_policy_flag(fact, "restricted") or (
        _fail_closed_policy_flag(metadata, "restricted")
    )
    erased = _fail_closed_policy_flag(fact, "erased") or _fail_closed_policy_flag(
        metadata, "erased"
    )
    conflict = _fail_closed_policy_flag(fact, "conflict") or (
        _fail_closed_policy_flag(metadata, "conflict")
    )
    protected = _fail_closed_policy_flag(fact, "protected") or (
        _fail_closed_policy_flag(metadata, "protected")
    )
    attention_score = _bounded_score(
        fact.get("retrieval_score"),
        fact.get("score"),
        fact.get("confidence"),
    )
    candidate = WorkingMemoryCandidate(
        capsule=capsule,
        attention_score=attention_score,
        recall_allowed=(
            is_fact_allowed_for_recall(fact) and not restricted and not erased
        ),
        eligible=True,
        restricted=restricted,
        erased=erased,
        protected=protected,
        conflict=conflict,
        metadata={
            "projection": SOURCE_MODE,
            "legacy_fact_id": fact_id,
            "legacy_source": str(fact.get("source") or "legacy-memory"),
        },
    )
    return capsule, candidate


def build_synaptic_shadow_preview(
    facts: Iterable[Mapping[str, object]],
    *,
    config: SynapticShadowConfig | None = None,
) -> dict[str, object]:
    """Build one deterministic preview from legacy retrieval output.

    Exact duplicate capsule identities are deduplicated before the Gate.  This
    function is pure and may raise typed contract errors; HTTP integration must
    isolate those errors from the legacy response.
    """

    resolved = config or SynapticShadowConfig()
    projected: dict[str, tuple[KnowledgeCapsule, WorkingMemoryCandidate]] = {}
    input_facts = 0
    skipped_empty = 0
    duplicate_capsules = 0

    for raw_fact in facts:
        input_facts += 1
        if not isinstance(raw_fact, Mapping):
            skipped_empty += 1
            continue
        item = _project_fact(raw_fact)
        if item is None:
            skipped_empty += 1
            continue
        capsule, candidate = item
        current = projected.get(capsule.capsule_id)
        if current is None:
            projected[capsule.capsule_id] = item
            continue
        duplicate_capsules += 1
        current_candidate = current[1]
        projected[capsule.capsule_id] = (
            capsule,
            WorkingMemoryCandidate(
                capsule=capsule,
                attention_score=max(
                    current_candidate.attention_score, candidate.attention_score
                ),
                recall_allowed=(
                    current_candidate.recall_allowed and candidate.recall_allowed
                ),
                eligible=current_candidate.eligible and candidate.eligible,
                restricted=current_candidate.restricted or candidate.restricted,
                erased=current_candidate.erased or candidate.erased,
                protected=current_candidate.protected or candidate.protected,
                conflict=current_candidate.conflict or candidate.conflict,
                metadata={
                    "projection": SOURCE_MODE,
                    "legacy_fact_id": _fact_identity(raw_fact),
                    "duplicate_policy_merge": True,
                },
            ),
        )

    ordered = tuple(projected[key] for key in sorted(projected))
    capsules = tuple(item[0] for item in ordered)
    candidates = tuple(item[1] for item in ordered)
    plan = WorkingMemoryGate().plan(
        candidates,
        budget=WorkingMemoryBudget(
            max_items=resolved.max_items,
            max_chars=resolved.max_chars,
        ),
    )
    pack = ContextPackBuilder().build(
        plan,
        capsules,
        budget=ContextPackBudget(
            max_tokens=resolved.max_tokens,
            max_deferred_pointers=resolved.max_deferred_pointers,
        ),
    )
    counts = {
        disposition.value: len(plan.by_disposition(disposition))
        for disposition in GateDisposition
    }
    return {
        "schema_version": SHADOW_SCHEMA_VERSION,
        "status": "ok",
        "mode": "shadow_only",
        "legacy_answer_authoritative": True,
        "source_mode": SOURCE_MODE,
        "metrics": {
            "input_facts": input_facts,
            "projected_capsules": len(capsules),
            "skipped_inputs": skipped_empty,
            "duplicate_capsules": duplicate_capsules,
            "selected_claims": len(pack.claims),
            "context_pack_token_cost": pack.token_cost,
            "context_pack_max_tokens": pack.max_tokens,
            "dispositions": counts,
        },
        "working_memory_plan": plan.to_dict(),
        "context_pack_preview": pack.to_prompt_dict(),
    }


def shadow_error_preview(code: str) -> dict[str, object]:
    """Return a safe non-authoritative error block without exception details."""

    safe_code = str(code or "shadow_failed").strip() or "shadow_failed"
    return {
        "schema_version": SHADOW_SCHEMA_VERSION,
        "status": "error",
        "mode": "shadow_only",
        "legacy_answer_authoritative": True,
        "source_mode": SOURCE_MODE,
        "error_code": safe_code,
    }


__all__ = [
    "SHADOW_SCHEMA_VERSION",
    "SOURCE_MODE",
    "SynapticShadowConfig",
    "build_synaptic_shadow_preview",
    "shadow_error_preview",
]
