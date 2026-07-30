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
_READER_VERSION = "1.1"
_SOURCE_REVISION = "legacy-fact-projection-v1"
_EVIDENCE_REQUIRED_WORLD_FACT_ORIGINS = frozenset(
    {
        "EXTERNAL",
        "EXTERNAL_SOURCE",
        "IMPORT",
        "LLM",
        "LLM_DERIVED",
        "LLM_OUTPUT",
        "MODEL_DERIVED",
        "MODEL_GENERATED",
        "REMOTE_PROVIDER",
        "WEB",
    }
)
_GENERIC_PROVENANCE_VALUES = frozenset(
    {"", "external", "legacy-memory", "llm", "model", "remote", "unknown"}
)


@dataclass(frozen=True, slots=True)
class SynapticShadowConfig:
    """Hard, deterministic bounds for one shadow preview."""

    max_input_facts: int = 64
    max_input_chars: int = 64_000
    max_items: int = 12
    max_chars: int = 4_000
    max_tokens: int = 16_384
    max_deferred_pointers: int = 32

    def __post_init__(self) -> None:
        for name in (
            "max_input_facts",
            "max_input_chars",
            "max_items",
            "max_chars",
            "max_tokens",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            isinstance(self.max_deferred_pointers, bool)
            or not isinstance(self.max_deferred_pointers, int)
            or self.max_deferred_pointers < 0
        ):
            raise ValueError("max_deferred_pointers must be a non-negative integer")


class SynapticShadowInputLimitError(ValueError):
    """A stable, non-sensitive failure for bounded shadow input."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _snapshot_with_size(
    facts: Iterable[object],
    *,
    config: SynapticShadowConfig,
) -> tuple[tuple[object, ...], int]:
    snapshot: list[object] = []
    input_chars = 0
    for raw_fact in facts:
        if len(snapshot) >= config.max_input_facts:
            raise SynapticShadowInputLimitError("shadow_input_facts_exceeded")
        input_chars += len(_canonical_json(raw_fact))
        if input_chars > config.max_input_chars:
            raise SynapticShadowInputLimitError("shadow_input_chars_exceeded")
        snapshot.append(dict(raw_fact) if isinstance(raw_fact, Mapping) else raw_fact)
    return tuple(snapshot), input_chars


def snapshot_synaptic_shadow_input(
    facts: Iterable[object],
    *,
    config: SynapticShadowConfig | None = None,
) -> tuple[object, ...]:
    """Create an immutable, bounded snapshot before background dispatch."""

    snapshot, _ = _snapshot_with_size(
        facts,
        config=config or SynapticShadowConfig(),
    )
    return snapshot


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


def _privilege_policy_flag(mapping: Mapping[str, object], name: str) -> bool:
    """Only a literal true grants an admission privilege."""

    return mapping.get(name) is True


def _malformed_policy_flag(mapping: Mapping[str, object], name: str) -> bool:
    return name in mapping and not isinstance(mapping[name], bool)


def _attributable_reference_present(value: object) -> bool:
    """Accept concrete references, never generic provenance labels."""

    if isinstance(value, str):
        normalized = value.strip().casefold()
        return bool(normalized) and normalized not in _GENERIC_PROVENANCE_VALUES
    if isinstance(value, Mapping):
        return any(_attributable_reference_present(item) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_attributable_reference_present(item) for item in value)
    return False


def _has_structural_evidence_refs(metadata: Mapping[str, object]) -> bool:
    """Mirror truth_policy: evidence is a list of mappings with a source reference."""

    refs = metadata.get("evidence_refs")
    if not isinstance(refs, list):
        return False
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        source_ref = ref.get("source_id") or ref.get("source")
        if isinstance(source_ref, str) and source_ref.strip():
            return True
    return False


def _has_attributable_provenance(
    fact: Mapping[str, object], metadata: Mapping[str, object]
) -> bool:
    explicit_keys = (
        "source_document_id",
        "source_ref",
        "source_revision",
        "source_uri",
        "source_url",
        "provenance",
        "provenance_ref",
    )
    if any(
        _attributable_reference_present(container.get(key))
        for container in (fact, metadata)
        for key in explicit_keys
    ):
        return True
    return _attributable_reference_present(
        fact.get("source") or metadata.get("source") or ""
    )


def _world_fact_evidence_allowed(
    fact: Mapping[str, object],
    metadata: Mapping[str, object],
    modality: ClaimModality,
) -> bool:
    """Fail closed for unknown origins; require evidence for external/model facts."""

    if modality is not ClaimModality.WORLD_FACT:
        return True
    origin = str(
        fact.get("origin_type") or metadata.get("origin_type") or ""
    ).strip().upper()
    if not origin or origin == "UNKNOWN":
        return False
    if origin not in _EVIDENCE_REQUIRED_WORLD_FACT_ORIGINS:
        return True
    return _has_attributable_provenance(
        fact, metadata
    ) and _has_structural_evidence_refs(metadata)


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
    modality = _claim_modality(fact)
    claim = CapsuleClaim.create(
        text=claim_text,
        modality=modality,
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
    malformed_protected = _malformed_policy_flag(
        fact, "protected"
    ) or _malformed_policy_flag(metadata, "protected")
    protected = _privilege_policy_flag(fact, "protected") or (
        _privilege_policy_flag(metadata, "protected")
    )
    world_fact_evidence_allowed = _world_fact_evidence_allowed(
        fact, metadata, modality
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
            is_fact_allowed_for_recall(fact)
            and not restricted
            and not erased
            and not malformed_protected
            and world_fact_evidence_allowed
        ),
        eligible=not malformed_protected and world_fact_evidence_allowed,
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


def _projection_key(capsule: KnowledgeCapsule) -> tuple[str, int, int, str]:
    claim = capsule.claims[0]
    span = claim.source_spans[0]
    return (
        capsule.source_document_id,
        span.start_offset,
        span.end_offset,
        span.content_hash,
    )


def build_synaptic_shadow_preview(
    facts: Iterable[object],
    *,
    config: SynapticShadowConfig | None = None,
) -> dict[str, object]:
    """Build one deterministic preview from legacy retrieval output.

    Exact projection identities are deduplicated before the Gate.  This
    function is pure and may raise typed contract errors; HTTP integration must
    isolate those errors from the legacy response.
    """

    resolved = config or SynapticShadowConfig()
    snapshot, input_chars = _snapshot_with_size(facts, config=resolved)
    projected: dict[
        tuple[str, int, int, str],
        tuple[KnowledgeCapsule, WorkingMemoryCandidate],
    ] = {}
    input_facts = 0
    skipped_empty = 0
    duplicate_capsules = 0

    for raw_fact in snapshot:
        input_facts += 1
        if not isinstance(raw_fact, Mapping):
            skipped_empty += 1
            continue
        item = _project_fact(raw_fact)
        if item is None:
            skipped_empty += 1
            continue
        capsule, candidate = item
        projection_key = _projection_key(capsule)
        current = projected.get(projection_key)
        if current is None:
            projected[projection_key] = item
            continue
        duplicate_capsules += 1
        current_capsule, current_candidate = current
        semantic_conflict = current_capsule.capsule_id != capsule.capsule_id
        chosen_capsule = min(
            (current_capsule, capsule), key=lambda value: value.capsule_id
        )
        projected[projection_key] = (
            chosen_capsule,
            WorkingMemoryCandidate(
                capsule=chosen_capsule,
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
                conflict=(
                    current_candidate.conflict
                    or candidate.conflict
                    or semantic_conflict
                ),
                metadata={
                    "projection": SOURCE_MODE,
                    "legacy_fact_id": _fact_identity(raw_fact),
                    "duplicate_policy_merge": True,
                    "semantic_conflict": semantic_conflict,
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
            "input_chars": input_chars,
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


def shadow_queue_preview(
    *,
    status: str,
    input_facts: int,
    error_code: str | None = None,
) -> dict[str, object]:
    """Return the immediate receipt for non-blocking shadow dispatch."""

    receipt: dict[str, object] = {
        "schema_version": SHADOW_SCHEMA_VERSION,
        "status": status,
        "mode": "shadow_only",
        "legacy_answer_authoritative": True,
        "source_mode": SOURCE_MODE,
        "metrics": {"input_facts": input_facts},
    }
    if error_code is not None:
        receipt["error_code"] = error_code
    return receipt


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
    "SynapticShadowInputLimitError",
    "SynapticShadowConfig",
    "build_synaptic_shadow_preview",
    "shadow_queue_preview",
    "shadow_error_preview",
    "snapshot_synaptic_shadow_input",
]
