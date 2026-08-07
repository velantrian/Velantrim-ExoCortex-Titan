"""Explicit, unwired Goal projection to Continuity Draft adapter.

This module validates one immutable ``GoalProjectionResult`` against an
externally issued source-binding receipt, then derives a neutral source
envelope and bounded observation drafts. It does not issue identity,
authorization, admission, persistence, routing, response, reminder, tool,
action, Canon, TruthGate, GoalStack, or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .goal_open_loop import (
    GOAL_PROJECTION_SCHEMA_VERSION,
    GoalBasis,
    GoalDecisionDisposition,
    GoalDecisionReason,
    GoalProjection,
    GoalProjectionDecision,
    GoalProjectionResult,
    GoalStatus,
    _digest,
    _dt,
)
from .observations import ContinuitySignalType
from .source_admission import (
    ContinuityAuthorizationContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)
from .source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

GOAL_SOURCE_TYPE = "goal_projection_result"
GOAL_SOURCE_OWNER = "continuity.goal_projector"
GOAL_SOURCE_ADAPTER_ID = "continuity.goal_projection_to_drafts"
GOAL_SOURCE_ADAPTER_VERSION = "1"
GOAL_SOURCE_COMPONENT_VERSION = "2"

_INCLUDED_REASONS = (
    GoalDecisionReason.EXPLICIT_ATTESTATION,
    GoalDecisionReason.LEGACY_SOURCE_SNAPSHOT,
)
_EXCLUDED_REASONS = (GoalDecisionReason.MISSING_ATTESTATION,)


@dataclass(frozen=True, slots=True)
class GoalDraftAdapterOutput:
    """Evidence-only output from one explicit Goal adapter invocation."""

    source_envelope: ContinuitySourceEnvelope
    drafts: tuple[ContinuityObservationDraft, ...]
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.source_envelope, ContinuitySourceEnvelope):
            raise ContinuitySourceAdmissionError(
                "source_envelope must be a ContinuitySourceEnvelope"
            )
        if any(
            not isinstance(value, ContinuityObservationDraft)
            for value in self.drafts
        ):
            raise ContinuitySourceAdmissionError(
                "drafts must contain ContinuityObservationDraft values"
            )
        ordered = tuple(sorted(self.drafts, key=lambda value: value.draft_id))
        if len(ordered) != len({value.draft_id for value in ordered}):
            raise ContinuitySourceAdmissionError(
                "drafts cannot contain duplicate draft identities"
            )
        if any(
            value.source_envelope_id != self.source_envelope.envelope_id
            for value in ordered
        ):
            raise ContinuitySourceAdmissionError(
                "every draft must reference the output source envelope"
            )
        object.__setattr__(self, "drafts", ordered)
        if self.no_runtime_authority is not True:
            raise ContinuitySourceAdmissionError(
                "no_runtime_authority must remain True"
            )


def adapt_goal_projection_to_drafts(
    *,
    result: GoalProjectionResult,
    binding_receipt: ContinuitySourceBindingReceipt,
    authorization_context: ContinuityAuthorizationContext,
    created_at: datetime,
) -> GoalDraftAdapterOutput:
    """Validate one subject-bound Goal result and derive conservative Drafts."""
    if not isinstance(result, GoalProjectionResult):
        raise ContinuitySourceAdmissionError(
            "result must be a GoalProjectionResult"
        )
    if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
        raise ContinuitySourceAdmissionError(
            "binding_receipt must be a ContinuitySourceBindingReceipt"
        )
    if not isinstance(authorization_context, ContinuityAuthorizationContext):
        raise ContinuitySourceAdmissionError(
            "authorization_context must be a ContinuityAuthorizationContext"
        )

    included = _validate_binding(result=result, binding_receipt=binding_receipt)
    envelope = ContinuitySourceEnvelope.create(
        binding_receipt=binding_receipt,
        authorization_context=authorization_context,
        source_schema_version=GOAL_PROJECTION_SCHEMA_VERSION,
        producer_adapter_id=GOAL_SOURCE_ADAPTER_ID,
        producer_adapter_version=GOAL_SOURCE_ADAPTER_VERSION,
        created_at=created_at,
    )
    drafts = tuple(
        draft
        for projection in result.projections
        for draft in _projection_drafts(
            projection=projection,
            decision=included[(projection.user_id, projection.goal_ref)],
            envelope=envelope,
            created_at=created_at,
        )
    )
    return GoalDraftAdapterOutput(source_envelope=envelope, drafts=drafts)


def _projection_payload(projection: GoalProjection) -> dict[str, object]:
    if not isinstance(projection.basis, GoalBasis):
        raise ContinuitySourceAdmissionError(
            "Goal projection basis must be a GoalBasis"
        )
    if not isinstance(projection.status, GoalStatus):
        raise ContinuitySourceAdmissionError(
            "Goal projection status must be a GoalStatus"
        )
    return {
        "schema_version": projection.schema_version,
        "policy_version": projection.policy_version,
        "user_id": projection.user_id,
        "goal_ref": projection.goal_ref,
        "source_snapshot_id": projection.source_snapshot_id,
        "attestation_id": projection.attestation_id,
        "basis": projection.basis.value,
        "status": projection.status.value,
        "title": projection.title,
        "description": projection.description,
        "priority": projection.priority,
        "keywords": list(projection.keywords),
        "source_refs": list(projection.source_refs),
        "updated_at": _dt(projection.updated_at),
    }


def _decision_payload(decision: GoalProjectionDecision) -> dict[str, object]:
    if not isinstance(decision.disposition, GoalDecisionDisposition):
        raise ContinuitySourceAdmissionError(
            "Goal decision disposition must be a GoalDecisionDisposition"
        )
    if any(
        not isinstance(reason, GoalDecisionReason)
        for reason in decision.reason_codes
    ):
        raise ContinuitySourceAdmissionError(
            "Goal decision reasons must be GoalDecisionReason values"
        )
    return {
        "user_id": decision.user_id,
        "goal_ref": decision.goal_ref,
        "disposition": decision.disposition.value,
        "reason_codes": [reason.value for reason in decision.reason_codes],
        "source_refs": list(decision.source_refs),
    }


def _validate_result_integrity(
    result: GoalProjectionResult,
) -> tuple[str, dict[tuple[str, str], GoalProjectionDecision]]:
    if not isinstance(result.policy_version, str) or not result.policy_version.strip():
        raise ContinuitySourceAdmissionError(
            "Goal result policy_version must be a non-empty string"
        )
    if not result.subject_ids:
        raise ContinuitySourceAdmissionError(
            "Goal result subject_ids cannot be empty"
        )
    if result.subject_ids != tuple(sorted(result.subject_ids)):
        raise ContinuitySourceAdmissionError(
            "Goal result subject_ids must be sorted"
        )
    if len(result.subject_ids) != len(set(result.subject_ids)):
        raise ContinuitySourceAdmissionError(
            "Goal result subject_ids cannot contain duplicates"
        )
    if any(
        not isinstance(value, str) or not value.strip()
        for value in result.subject_ids
    ):
        raise ContinuitySourceAdmissionError(
            "Goal result subject_ids must contain non-empty strings"
        )

    ordered_projections = tuple(
        sorted(result.projections, key=lambda value: value.projection_id)
    )
    if result.projections != ordered_projections:
        raise ContinuitySourceAdmissionError(
            "Goal result projections must be sorted by projection_id"
        )
    if len(result.projections) != len(
        {value.projection_id for value in result.projections}
    ):
        raise ContinuitySourceAdmissionError(
            "Goal result projections cannot contain duplicate identities"
        )

    projection_by_key: dict[tuple[str, str], GoalProjection] = {}
    for projection in result.projections:
        if not isinstance(projection, GoalProjection):
            raise ContinuitySourceAdmissionError(
                "Goal result projections must contain GoalProjection values"
            )
        if projection.schema_version != GOAL_PROJECTION_SCHEMA_VERSION:
            raise ContinuitySourceAdmissionError(
                "Goal projection schema_version is not supported"
            )
        if projection.policy_version != result.policy_version:
            raise ContinuitySourceAdmissionError(
                "Goal projection policy_version does not match result policy"
            )
        if projection.user_id not in result.subject_ids:
            raise ContinuitySourceAdmissionError(
                "Goal projection user_id is absent from result subject_ids"
            )
        expected_projection_id = _digest(_projection_payload(projection))
        if projection.projection_id != expected_projection_id:
            raise ContinuitySourceAdmissionError(
                "Goal projection_id does not match canonical projection payload"
            )
        key = (projection.user_id, projection.goal_ref)
        if key in projection_by_key:
            raise ContinuitySourceAdmissionError(
                "Goal result cannot contain duplicate subject/goal projections"
            )
        projection_by_key[key] = projection

    ordered_decisions = tuple(
        sorted(result.decisions, key=lambda value: (value.user_id, value.goal_ref))
    )
    if result.decisions != ordered_decisions:
        raise ContinuitySourceAdmissionError(
            "Goal result decisions must be sorted by subject and goal"
        )
    decision_by_key: dict[tuple[str, str], GoalProjectionDecision] = {}
    included: dict[tuple[str, str], GoalProjectionDecision] = {}
    for decision in result.decisions:
        if not isinstance(decision, GoalProjectionDecision):
            raise ContinuitySourceAdmissionError(
                "Goal result decisions must contain GoalProjectionDecision values"
            )
        _decision_payload(decision)
        if decision.user_id not in result.subject_ids:
            raise ContinuitySourceAdmissionError(
                "Goal decision user_id is absent from result subject_ids"
            )
        key = (decision.user_id, decision.goal_ref)
        if key in decision_by_key:
            raise ContinuitySourceAdmissionError(
                "Goal result cannot contain duplicate subject/goal decisions"
            )
        decision_by_key[key] = decision
        if decision.disposition is GoalDecisionDisposition.INCLUDED:
            matched_projection = projection_by_key.get(key)
            if matched_projection is None:
                raise ContinuitySourceAdmissionError(
                    "included Goal decision must reference one projection"
                )
            if decision.reason_codes != _INCLUDED_REASONS:
                raise ContinuitySourceAdmissionError(
                    "included Goal decision reasons are not canonical"
                )
            if decision.source_refs != matched_projection.source_refs:
                raise ContinuitySourceAdmissionError(
                    "included Goal decision source_refs must match projection"
                )
            included[key] = decision
        else:
            if decision.reason_codes != _EXCLUDED_REASONS:
                raise ContinuitySourceAdmissionError(
                    "excluded Goal decision reasons are not canonical"
                )
            if key in projection_by_key:
                raise ContinuitySourceAdmissionError(
                    "excluded Goal decision cannot retain a projection"
                )
            if not decision.source_refs:
                raise ContinuitySourceAdmissionError(
                    "excluded Goal decision source_refs cannot be empty"
                )

    if set(projection_by_key) != set(included):
        raise ContinuitySourceAdmissionError(
            "every Goal projection must have exactly one included decision"
        )
    if {value.user_id for value in result.decisions} != set(result.subject_ids):
        raise ContinuitySourceAdmissionError(
            "Goal result subject_ids must exactly match decision subjects"
        )

    payload = {
        "policy_version": result.policy_version,
        "subject_ids": list(result.subject_ids),
        "projection_ids": [
            value.projection_id for value in result.projections
        ],
        "decisions": [
            _decision_payload(value) for value in result.decisions
        ],
    }
    expected_result_id = _digest(payload)
    if result.result_id != expected_result_id:
        raise ContinuitySourceAdmissionError(
            "Goal result_id does not match canonical result payload"
        )
    return expected_result_id, included


def _required_evidence(result: GoalProjectionResult) -> set[str]:
    return {
        result.result_id,
        *(projection.projection_id for projection in result.projections),
        *(projection.source_snapshot_id for projection in result.projections),
        *(projection.attestation_id for projection in result.projections),
        *(
            ref
            for projection in result.projections
            for ref in projection.source_refs
        ),
        *(ref for decision in result.decisions for ref in decision.source_refs),
    }


def _validate_binding(
    *,
    result: GoalProjectionResult,
    binding_receipt: ContinuitySourceBindingReceipt,
) -> dict[tuple[str, str], GoalProjectionDecision]:
    expected_digest, included = _validate_result_integrity(result)
    bound_ids = tuple(
        sorted(subject.subject_id for subject in binding_receipt.subject_refs)
    )
    if len(bound_ids) != len(set(bound_ids)):
        raise ContinuitySourceAdmissionError(
            "Goal binding cannot assign multiple subject kinds to one user_id"
        )

    checks = (
        (
            binding_receipt.source_type == GOAL_SOURCE_TYPE,
            "binding source_type does not identify a Goal result",
        ),
        (
            binding_receipt.source_owner == GOAL_SOURCE_OWNER,
            "binding source_owner does not identify the Goal projector",
        ),
        (
            binding_receipt.source_component_version
            == GOAL_SOURCE_COMPONENT_VERSION,
            "binding source_component_version is not supported",
        ),
        (
            binding_receipt.source_result_id == result.result_id,
            "binding source_result_id does not match the Goal result",
        ),
        (
            binding_receipt.source_digest == expected_digest,
            "binding source_digest does not match canonical Goal payload",
        ),
        (
            binding_receipt.source_policy_version == result.policy_version,
            "binding source_policy_version does not match the Goal result",
        ),
        (
            bound_ids == result.subject_ids,
            "binding subject IDs must exactly match every Goal result subject",
        ),
        (
            _required_evidence(result).issubset(
                set(binding_receipt.evidence_refs)
            ),
            "binding evidence must include result, projection, snapshot, "
            "attestation, and decision source references",
        ),
    )
    for valid, message in checks:
        if not valid:
            raise ContinuitySourceAdmissionError(message)

    if result.projections:
        latest_projection = max(
            projection.updated_at for projection in result.projections
        )
        if binding_receipt.source_as_of < latest_projection:
            raise ContinuitySourceAdmissionError(
                "binding source_as_of cannot precede Goal projection updates"
            )
    return included


def _projection_drafts(
    *,
    projection: GoalProjection,
    decision: GoalProjectionDecision,
    envelope: ContinuitySourceEnvelope,
    created_at: datetime,
) -> tuple[ContinuityObservationDraft, ...]:
    if projection.status is not GoalStatus.ACTIVE:
        return ()
    evidence = tuple(
        sorted(
            {
                projection.projection_id,
                projection.source_snapshot_id,
                projection.attestation_id,
                *projection.source_refs,
                *decision.source_refs,
            }
        )
    )
    return (
        ContinuityObservationDraft.create(
            source_envelope=envelope,
            signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            value=True,
            proposed_confidence=1.0,
            evidence_refs=evidence,
            reason_codes=(
                "goal_active_projection",
                "goal_explicit_attestation",
            ),
            derivation_rule_id="goal.active_evidence_coverage.v1",
            created_at=created_at,
            scope=f"goal_projection:{projection.projection_id}",
        ),
    )
