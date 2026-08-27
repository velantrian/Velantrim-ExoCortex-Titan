from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from core.conversation_consolidation import ConversationNotebook
from core.continuity.ticc import (
    ConversationSourceTurn,
    TICCCaptureCandidate,
    TICCSemanticAnnotation,
    TICCSourceSpan,
)
from core.continuity.ticc_relations import TICCRelationRequest


LEGACY_NOTEBOOK_FIELDS = {field.name for field in fields(ConversationNotebook)}
SOURCE_TURN_FIELDS = {field.name for field in fields(ConversationSourceTurn)}
ANNOTATION_FIELDS = {field.name for field in fields(TICCSemanticAnnotation)}
SPAN_FIELDS = {field.name for field in fields(TICCSourceSpan)}
CANDIDATE_FIELDS = {field.name for field in fields(TICCCaptureCandidate)}
RELATION_REQUEST_FIELDS = {field.name for field in fields(TICCRelationRequest)}


def test_legacy_notebook_does_not_structurally_preserve_ticc_source_distinctions() -> None:
    absent_from_legacy = {
        "actor_ref",
        "origin_type",
        "semantic_modality",
        "source_span",
        "raw_text_sha256",
        "slice_sha256",
        "declared_loss_codes",
        "uncertainty_codes",
        "source_assertion",
        "target_assertion",
        "relation_type",
    }
    assert LEGACY_NOTEBOOK_FIELDS.isdisjoint(absent_from_legacy)


def test_ticc_structurally_preserves_source_actor_origin_modality_and_loss_axes() -> None:
    assert {"actor_ref", "raw_text_sha256", "turn_ref", "session_ref"} <= SOURCE_TURN_FIELDS
    assert {"origin_type", "modality", "source_span", "declared_loss_codes", "uncertainty_codes"} <= ANNOTATION_FIELDS
    assert {"source_turn_ref", "start_offset", "end_offset", "slice_sha256"} <= SPAN_FIELDS
    assert {"semantic_modality", "actor_ref", "origin_type", "declared_loss_codes"} <= CANDIDATE_FIELDS


def test_ticc_relation_request_requires_exact_assertion_endpoints() -> None:
    assert {"source_assertion", "target_assertion", "relation_type", "evidence_refs"} <= RELATION_REQUEST_FIELDS
    assert "query" not in RELATION_REQUEST_FIELDS
    assert "search" not in RELATION_REQUEST_FIELDS
    assert "similarity" not in RELATION_REQUEST_FIELDS


def test_ticc_modules_are_not_imported_by_non_test_runtime_modules() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    core_root = repo_root / "core"
    allowed = {
        core_root / "continuity" / "ticc.py",
        core_root / "continuity" / "ticc_relations.py",
    }

    offenders: list[str] = []
    needles = (
        "from core.continuity.ticc import",
        "import core.continuity.ticc",
        "from .ticc import",
        "from core.continuity.ticc_relations import",
        "import core.continuity.ticc_relations",
        "from .ticc_relations import",
    )
    for path in core_root.rglob("*.py"):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if any(needle in text for needle in needles):
            offenders.append(str(path.relative_to(repo_root)))

    assert offenders == []


def test_ticc_core_has_no_direct_persistence_network_or_notebook_dependency() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    paths = [
        repo_root / "core" / "continuity" / "ticc.py",
        repo_root / "core" / "continuity" / "ticc_relations.py",
    ]
    forbidden_tokens = (
        "sqlite3",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "ConversationConsolidator",
        "ConversationNotebook",
        "LocalShadowLedger",
        "TruthGate",
        "Canon",
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"forbidden dependency token {token!r} in {path.name}"


def test_structural_comparison_does_not_claim_behavioral_superiority() -> None:
    # This suite proves representational capability/isolation only.
    # It does not prove better answer quality, lower hallucination rate,
    # production readiness, or action-authority safety.
    unsupported_claims = {
        "better_answers",
        "production_ready",
        "runtime_authorized",
        "truth_authority",
        "identity_authority",
    }
    observed_capabilities = {
        "source_binding",
        "actor_origin_separation",
        "semantic_modality",
        "declared_loss",
        "exact_relation_endpoints",
    }
    assert unsupported_claims.isdisjoint(observed_capabilities)
