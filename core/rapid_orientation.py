"""Deterministic RCO-1 shadow projection.

RCO-1 reads an already-authorised query, the passive Synaptic shadow preview,
and one immutable PolicySnapshot.  It emits a read-only OrientationProjection,
a proposal conforming to the D16 research vocabulary, and an auditable receipt.
It never executes the proposal, calls a provider, retrieves more data, persists
state, or mutates Canon/ESM/task state.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Mapping

from core.compute_controller import ComputePath, decide_compute_path
from core.goal_frame import GoalFrame, GoalIntent, RiskLevel, infer_goal_frame
from core.policy_kernel import PolicySnapshot

PROJECTION_VERSION = "rco.orientation-projection.v1"
RECEIPT_VERSION = "rco.understanding-receipt.v1"
D16_CONTRACT_ID = "titan.d16.executive-control"
D16_CONTRACT_VERSION = "d16-research-v1"
AUTHORITATIVE_ROUTE = "LEGACY_QUERY"
CONFIDENCE_BASIS = "rco1-deterministic-heuristic-not-calibrated-v1"


class CognitiveRoute(str, Enum):
    FAST_LOCAL = "FAST_LOCAL"
    DELIBERATE_LOCAL = "DELIBERATE_LOCAL"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    CLARIFY = "CLARIFY"
    DEFER = "DEFER"


@dataclass(frozen=True, slots=True)
class OrientationProjection:
    projection_id: str
    request_id: str
    policy_snapshot_id: str
    policy_version: str
    goal_frame_digest: str
    evidence_refs: tuple[dict[str, object], ...]
    evidence_snapshot_digest: str
    apparent_subject: str
    task_shape: tuple[str, ...]
    knowledge_lenses: tuple[str, ...]
    critical_gaps: tuple[str, ...]
    contradictions: tuple[dict[str, object], ...]
    risk_flags: tuple[str, ...]
    expected_information_gain: float
    estimated_cognitive_cost: int
    confidence: float
    generated_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "projection_version": PROJECTION_VERSION,
            "projection_id": self.projection_id,
            "request_id": self.request_id,
            "policy_snapshot_id": self.policy_snapshot_id,
            "policy_version": self.policy_version,
            "capability_lease_refs": [],
            "goal_frame_digest": self.goal_frame_digest,
            "evidence_refs": [dict(item) for item in self.evidence_refs],
            "evidence_snapshot_digest": self.evidence_snapshot_digest,
            "apparent_subject": self.apparent_subject,
            "task_shape": list(self.task_shape),
            "knowledge_lenses": list(self.knowledge_lenses),
            "critical_gaps": list(self.critical_gaps),
            "contradictions": [dict(item) for item in self.contradictions],
            "risk_flags": list(self.risk_flags),
            "expected_information_gain": self.expected_information_gain,
            "estimated_cognitive_cost": self.estimated_cognitive_cost,
            "confidence": self.confidence,
            "confidence_basis": CONFIDENCE_BASIS,
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True, slots=True)
class CognitiveRouteProposal:
    proposal_id: str
    request_id: str
    projection_id: str
    route: CognitiveRoute
    route_payload: dict[str, object]
    compute_path: ComputePath
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[dict[str, object], ...]
    critical_gaps: tuple[str, ...]
    confidence: float
    estimated_cost: int
    policy_snapshot_id: str
    policy_version: str
    generated_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": D16_CONTRACT_ID,
            "contract_version": D16_CONTRACT_VERSION,
            "proposal_id": self.proposal_id,
            "request_id": self.request_id,
            "projection_id": self.projection_id,
            "route": self.route.value,
            "route_payload": dict(self.route_payload),
            "compute_path": self.compute_path.value,
            "compute_path_mapping_id": None,
            "reason_codes": list(self.reason_codes),
            "evidence_refs": [dict(item) for item in self.evidence_refs],
            "critical_gaps": list(self.critical_gaps),
            "confidence": self.confidence,
            "confidence_basis": CONFIDENCE_BASIS,
            "estimated_cost": self.estimated_cost,
            "policy_snapshot_id": self.policy_snapshot_id,
            "policy_version": self.policy_version,
            "capability_lease_refs": [],
            "fallback": AUTHORITATIVE_ROUTE,
            "generated_at": self.generated_at,
        }


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _objects(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _healthy_policy(snapshot: PolicySnapshot) -> bool:
    return (
        snapshot.reason_code != "policy_dependency_unavailable"
        and snapshot.supervisor_mode != "unavailable"
        and snapshot.source == "verified_local_runtime"
    )


def _request_id(query: str, shadow_preview: Mapping[str, object]) -> str:
    metrics = _mapping(shadow_preview.get("metrics"))
    return _digest(
        {
            "query": query,
            "shadow_schema_version": shadow_preview.get("schema_version"),
            "source_mode": shadow_preview.get("source_mode"),
            "input_facts": metrics.get("input_facts", 0),
            "input_chars": metrics.get("input_chars", 0),
        }
    )[:24]


def _evidence_refs(context_pack: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    refs: dict[str, dict[str, object]] = {}
    for raw_claim in _objects(context_pack.get("claims")):
        claim = _mapping(raw_claim)
        for raw_evidence in _objects(claim.get("evidence")):
            evidence = _mapping(raw_evidence)
            span_id = evidence.get("span_id")
            document_id = evidence.get("document_id")
            if not isinstance(span_id, str) or not span_id.strip():
                continue
            if not isinstance(document_id, str) or not document_id.strip():
                continue
            item: dict[str, object] = {
                "span_id": span_id,
                "document_id": document_id,
                "source_revision": evidence.get("source_revision"),
                "start_offset": evidence.get("start_offset"),
                "end_offset": evidence.get("end_offset"),
                "content_hash": evidence.get("content_hash"),
            }
            refs[_canonical_json(item)] = item
    return tuple(refs[key] for key in sorted(refs))


def _contradictions(
    context_pack: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    result: dict[str, dict[str, object]] = {}
    for raw_conflict in _objects(context_pack.get("conflicts")):
        conflict = _mapping(raw_conflict)
        capsule_id = conflict.get("capsule_id")
        source_document_id = conflict.get("source_document_id")
        if not isinstance(capsule_id, str) or not capsule_id.strip():
            continue
        if not isinstance(source_document_id, str) or not source_document_id.strip():
            continue
        reasons = sorted(
            str(reason)
            for reason in _objects(conflict.get("reasons"))
            if isinstance(reason, str) and reason.strip()
        )
        item: dict[str, object] = {
            "capsule_id": capsule_id,
            "source_document_id": source_document_id,
            "reasons": reasons,
        }
        result[_canonical_json(item)] = item
    return tuple(result[key] for key in sorted(result))


def _knowledge_lenses(context_pack: Mapping[str, object]) -> tuple[str, ...]:
    lenses: set[str] = set()
    for raw_claim in _objects(context_pack.get("claims")):
        modality = str(_mapping(raw_claim).get("modality") or "").strip().lower()
        if modality in {"observation", "world_fact"}:
            lenses.add("invariant_candidate")
        elif modality == "user_report":
            lenses.add("context_variant")
        elif modality in {"instruction", "goal"}:
            lenses.add("practical_procedure")
        elif modality in {"opinion", "hypothesis", "interpretation"}:
            lenses.add("hypothesis_or_unknown")
    if not lenses:
        lenses.add("hypothesis_or_unknown")
    return tuple(sorted(lenses))


def _critical_gaps(
    query: str,
    goal: GoalFrame,
    *,
    selected_claims: int,
    contradictions: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    gaps: set[str] = set()
    if not query.strip():
        gaps.add("missing_goal")
    if selected_claims == 0 and goal.intent not in {GoalIntent.CREATE}:
        gaps.add("no_admitted_evidence")
    if goal.risk_level is RiskLevel.HIGH and selected_claims < 2:
        gaps.add("high_risk_evidence_insufficient")
    if contradictions:
        gaps.add("material_conflict_requires_review")
    return tuple(sorted(gaps))


def _risk_flags(
    goal: GoalFrame,
    *,
    selected_claims: int,
    contradictions: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    flags: set[str] = set()
    if goal.risk_level is RiskLevel.HIGH:
        flags.add("high_risk_domain")
    elif goal.risk_level is RiskLevel.MEDIUM:
        flags.add("elevated_reasoning_risk")
    if selected_claims == 0:
        flags.add("no_active_evidence")
    if contradictions:
        flags.add("contradictory_evidence")
    return tuple(sorted(flags))


def _information_gain(
    gaps: tuple[str, ...], contradictions: tuple[dict[str, object], ...]
) -> float:
    if "missing_goal" in gaps:
        return 0.95
    if "high_risk_evidence_insufficient" in gaps:
        return 0.9
    if "no_admitted_evidence" in gaps:
        return 0.85
    if contradictions:
        return 0.75
    return 0.25


def _cost_for_path(path: ComputePath) -> int:
    return {
        ComputePath.FAST_PATH: 1,
        ComputePath.NORMAL_PATH: 2,
        ComputePath.CREATIVE_PATH: 2,
        ComputePath.DEEP_PATH: 3,
        ComputePath.VERIFY_PATH: 4,
    }[path]


def _confidence(
    *,
    selected_claims: int,
    gaps: tuple[str, ...],
    contradictions: tuple[dict[str, object], ...],
) -> float:
    value = 0.45 + min(selected_claims, 4) * 0.1
    value -= len(gaps) * 0.14
    value -= len(contradictions) * 0.08
    return round(max(0.05, min(0.9, value)), 3)


def _select_route(
    goal: GoalFrame,
    *,
    gaps: tuple[str, ...],
    contradictions: tuple[dict[str, object], ...],
    selected_claims: int,
) -> tuple[CognitiveRoute, tuple[str, ...]]:
    reasons: list[str] = []
    if "missing_goal" in gaps:
        return CognitiveRoute.CLARIFY, ("goal_missing",)
    if (
        "no_admitted_evidence" in gaps
        or "high_risk_evidence_insufficient" in gaps
    ):
        return CognitiveRoute.REQUEST_EVIDENCE, tuple(gaps)
    if contradictions:
        reasons.append("material_conflict")
    if goal.risk_level is not RiskLevel.LOW:
        reasons.append("risk_requires_deliberation")
    if goal.intent in {
        GoalIntent.VERIFY,
        GoalIntent.ANALYZE,
        GoalIntent.COMPARE,
        GoalIntent.EXPLAIN,
        GoalIntent.PLAN,
    }:
        reasons.append("intent_requires_deliberation")
    if reasons:
        return CognitiveRoute.DELIBERATE_LOCAL, tuple(sorted(set(reasons)))
    if goal.intent is GoalIntent.UNKNOWN and selected_claims == 0:
        return CognitiveRoute.CLARIFY, ("intent_unknown",)
    return CognitiveRoute.FAST_LOCAL, ("low_risk_local_sufficiency",)


def _route_payload(
    route: CognitiveRoute,
    *,
    gaps: tuple[str, ...],
    max_reasoning_steps: int,
) -> dict[str, object]:
    if route is CognitiveRoute.FAST_LOCAL:
        return {}
    if route is CognitiveRoute.DELIBERATE_LOCAL:
        return {
            "budget": {"max_reasoning_steps": max_reasoning_steps},
            "stop_conditions": [
                "critical_gaps_resolved_or_exposed",
                "budget_exhausted",
                "policy_denied",
            ],
        }
    if route is CognitiveRoute.REQUEST_EVIDENCE:
        return {
            "gap_ids": list(gaps),
            "acceptable_evidence_types": ["source_linked_local_evidence"],
            "completion_condition": "all_critical_gaps_resolved_or_explicitly_bounded",
        }
    if route is CognitiveRoute.CLARIFY:
        return {
            "question": "Clarify the goal, constraints, or expected outcome.",
            "blocking_ambiguity_ids": list(gaps or ("intent_unknown",)),
        }
    return {
        "reason_codes": ["research_defer_not_selected_by_rco1"],
        "review_trigger": "operator_review",
        "expires_at": None,
        "operator_override": True,
    }


def build_rapid_orientation_receipt(
    query: str,
    shadow_preview: Mapping[str, object],
    policy_snapshot: PolicySnapshot,
    *,
    request_id: str | None = None,
) -> dict[str, object]:
    """Build one deterministic, zero-model RCO-1 receipt.

    Policy failure rejects the proposal.  It never converts a degraded snapshot
    into permission and never changes the authoritative LEGACY_QUERY result.
    """

    resolved_query = query if isinstance(query, str) else ""
    resolved_request_id = request_id or _request_id(resolved_query, shadow_preview)
    if not _healthy_policy(policy_snapshot):
        return {
            "schema_version": RECEIPT_VERSION,
            "status": "rejected",
            "mode": "shadow_only",
            "rco_phase": "RCO-1",
            "legacy_answer_authoritative": True,
            "authoritative_route": AUTHORITATIVE_ROUTE,
            "action_attempted": False,
            "failure_code": "policy_snapshot_unhealthy",
            "policy_snapshot_id": policy_snapshot.snapshot_id,
            "policy_version": policy_snapshot.policy_version,
            "proposal": None,
            "metrics": {
                "model_calls": 0,
                "remote_calls": 0,
                "retrievals": 0,
                "mutations_attempted": 0,
                "policy_non_interference": True,
            },
        }

    if shadow_preview.get("status") != "ok":
        return {
            "schema_version": RECEIPT_VERSION,
            "status": "rejected",
            "mode": "shadow_only",
            "rco_phase": "RCO-1",
            "legacy_answer_authoritative": True,
            "authoritative_route": AUTHORITATIVE_ROUTE,
            "action_attempted": False,
            "failure_code": "shadow_preview_unavailable",
            "policy_snapshot_id": policy_snapshot.snapshot_id,
            "policy_version": policy_snapshot.policy_version,
            "proposal": None,
            "metrics": {
                "model_calls": 0,
                "remote_calls": 0,
                "retrievals": 0,
                "mutations_attempted": 0,
                "policy_non_interference": True,
            },
        }

    context_pack = _mapping(shadow_preview.get("context_pack_preview"))
    evidence_refs = _evidence_refs(context_pack)
    contradictions = _contradictions(context_pack)
    selected_claims = len(_objects(context_pack.get("claims")))
    goal = infer_goal_frame(resolved_query)
    gaps = _critical_gaps(
        resolved_query,
        goal,
        selected_claims=selected_claims,
        contradictions=contradictions,
    )
    risk_flags = _risk_flags(
        goal,
        selected_claims=selected_claims,
        contradictions=contradictions,
    )
    uncertainty = min(1.0, 0.15 * len(gaps) + 0.2 * len(contradictions))
    compute = decide_compute_path(
        resolved_query,
        goal=goal,
        candidate_count=selected_claims,
        uncertainty=uncertainty,
    )
    confidence = _confidence(
        selected_claims=selected_claims,
        gaps=gaps,
        contradictions=contradictions,
    )
    goal_digest = _digest(goal.to_dict())
    evidence_digest = _digest(context_pack)
    identity_payload = {
        "projection_version": PROJECTION_VERSION,
        "request_id": resolved_request_id,
        "policy_snapshot_id": policy_snapshot.snapshot_id,
        "policy_version": policy_snapshot.policy_version,
        "capability_lease_refs": [],
        "goal_frame_digest": goal_digest,
        "evidence_refs": list(evidence_refs),
        "evidence_snapshot_digest": evidence_digest,
    }
    projection_id = _digest(identity_payload)
    projection = OrientationProjection(
        projection_id=projection_id,
        request_id=resolved_request_id,
        policy_snapshot_id=policy_snapshot.snapshot_id,
        policy_version=policy_snapshot.policy_version,
        goal_frame_digest=goal_digest,
        evidence_refs=evidence_refs,
        evidence_snapshot_digest=evidence_digest,
        apparent_subject=goal.domain_hint,
        task_shape=(goal.intent.value, goal.risk_level.value, goal.output_style),
        knowledge_lenses=_knowledge_lenses(context_pack),
        critical_gaps=gaps,
        contradictions=contradictions,
        risk_flags=risk_flags,
        expected_information_gain=_information_gain(gaps, contradictions),
        estimated_cognitive_cost=_cost_for_path(compute.path),
        confidence=confidence,
        generated_at=policy_snapshot.captured_at,
    )
    route, reasons = _select_route(
        goal,
        gaps=gaps,
        contradictions=contradictions,
        selected_claims=selected_claims,
    )
    proposal_payload = {
        "contract_id": D16_CONTRACT_ID,
        "contract_version": D16_CONTRACT_VERSION,
        "request_id": resolved_request_id,
        "projection_id": projection_id,
        "route": route.value,
        "route_payload": _route_payload(
            route,
            gaps=gaps,
            max_reasoning_steps=compute.max_reasoning_steps,
        ),
        "compute_path": compute.path.value,
        "compute_path_mapping_id": None,
        "reason_codes": list(reasons),
        "evidence_refs": list(evidence_refs),
        "critical_gaps": list(gaps),
        "confidence": confidence,
        "estimated_cost": _cost_for_path(compute.path),
        "policy_snapshot_id": policy_snapshot.snapshot_id,
        "policy_version": policy_snapshot.policy_version,
        "capability_lease_refs": [],
        "fallback": AUTHORITATIVE_ROUTE,
    }
    proposal = CognitiveRouteProposal(
        proposal_id=_digest(proposal_payload),
        request_id=resolved_request_id,
        projection_id=projection_id,
        route=route,
        route_payload=_route_payload(
            route,
            gaps=gaps,
            max_reasoning_steps=compute.max_reasoning_steps,
        ),
        compute_path=compute.path,
        reason_codes=reasons,
        evidence_refs=evidence_refs,
        critical_gaps=gaps,
        confidence=confidence,
        estimated_cost=_cost_for_path(compute.path),
        policy_snapshot_id=policy_snapshot.snapshot_id,
        policy_version=policy_snapshot.policy_version,
        generated_at=policy_snapshot.captured_at,
    )
    return {
        "schema_version": RECEIPT_VERSION,
        "status": "ok",
        "mode": "shadow_only",
        "rco_phase": "RCO-1",
        "legacy_answer_authoritative": True,
        "authoritative_route": AUTHORITATIVE_ROUTE,
        "action_attempted": False,
        "projection": projection.to_dict(),
        "proposal": proposal.to_dict(),
        "policy_snapshot_id": policy_snapshot.snapshot_id,
        "policy_version": policy_snapshot.policy_version,
        "metrics": {
            "selected_claims": selected_claims,
            "evidence_refs": len(evidence_refs),
            "critical_gaps": len(gaps),
            "contradictions": len(contradictions),
            "proposed_route": route.value,
            "compute_path": compute.path.value,
            "model_calls": 0,
            "remote_calls": 0,
            "retrievals": 0,
            "mutations_attempted": 0,
            "policy_non_interference": True,
            "stability_key": projection_id,
        },
    }


__all__ = [
    "AUTHORITATIVE_ROUTE",
    "CognitiveRoute",
    "CognitiveRouteProposal",
    "D16_CONTRACT_ID",
    "D16_CONTRACT_VERSION",
    "OrientationProjection",
    "PROJECTION_VERSION",
    "RECEIPT_VERSION",
    "build_rapid_orientation_receipt",
]
