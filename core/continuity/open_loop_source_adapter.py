"""Explicit, unwired OpenLoop projection to Continuity Draft adapter.

This module validates one immutable ``OpenLoopProjectionResult`` against an
externally issued source-binding receipt, then derives a neutral source
envelope and bounded evidence-only observation drafts. It does not issue
identity, authorization, admission, persistence, routing, response, reminder,
tool, action, Canon, TruthGate, GoalStack, or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .goal_open_loop import (
    GOAL_OPEN_LOOP_POLICY_VERSION,
    OPEN_LOOP_SCHEMA_VERSION,
    OpenLoopKind,
    OpenLoopProjection,
    OpenLoopProjectionResult,
    OpenLoopReason,
    OpenLoopStatus,
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

OPEN_LOOP_SOURCE_TYPE = "open_loop_projection_result"
OPEN_LOOP_SOURCE_OWNER = "continuity.open_loop_projector"
OPEN_LOOP_SOURCE_ADAPTER_ID = "continuity.open_loop_projection_to_drafts"
OPEN_LOOP_SOURCE_ADAPTER_VERSION = "1"
OPEN_LOOP_SOURCE_COMPONENT_VERSION = "2"

_ACTIVE_STATUSES = frozenset({OpenLoopStatus.OPEN, OpenLoopStatus.OVERDUE})


def _expected_reasons(status: OpenLoopStatus) -> tuple[OpenLoopReason, ...]:
    status_reason = {
        OpenLoopStatus.NOT_YET_OPEN: OpenLoopReason.FUTURE_OPEN_TIME,
        OpenLoopStatus.OPEN: OpenLoopReason.OPENED_AS_OF_REQUEST,
        OpenLoopStatus.OVERDUE: OpenLoopReason.DEADLINE_PASSED,
        OpenLoopStatus.RESOLVED: OpenLoopReason.RESOLUTION_EVIDENCE_PRESENT,
    }[status]
    return tuple(
        sorted(
            (OpenLoopReason.TYPED_SOURCE_SIGNAL, status_reason),
            key=lambda value: value.value,
        )
    )


@dataclass(frozen=True, slots=True)
class OpenLoopDraftAdapterOutput:
    """Evidence-only output from one explicit OpenLoop adapter invocation."""

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


def adapt_open_loop_projection_to_drafts(
    *,
    result: OpenLoopProjectionResult,
    binding_receipt: ContinuitySourceBindingReceipt,
    authorization_context: ContinuityAuthorizationContext,
    created_at: datetime,
) -> OpenLoopDraftAdapterOutput:
    """Validate one subject-bound OpenLoop result and derive bounded Drafts."""
    if not isinstance(result, OpenLoopProjectionResult):
        raise ContinuitySourceAdmissionError(
            "result must be an OpenLoopProjectionResult"
        )
    if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
        raise ContinuitySourceAdmissionError(
            "binding_receipt must be a ContinuitySourceBindingReceipt"
        )
    if not isinstance(authorization_context, ContinuityAuthorizationContext):
        raise ContinuitySourceAdmissionError(
            "authorization_context must be a ContinuityAuthorizationContext"
        )

    _validate_binding(result=result, binding_receipt=binding_receipt)
    envelope = ContinuitySourceEnvelope.create(
        binding_receipt=binding_receipt,
        authorization_context=authorization_context,
        source_schema_version=OPEN_LOOP_SCHEMA_VERSION,
        producer_adapter_id=OPEN_LOOP_SOURCE_ADAPTER_ID,
        producer_adapter_version=OPEN_LOOP_SOURCE_ADAPTER_VERSION,
        created_at=created_at,
    )
    drafts = tuple(
        draft
        for projection in result.projections
        for draft in _projection_drafts(
            projection=projection,
            envelope=envelope,
            created_at=created_at,
        )
    )
    return OpenLoopDraftAdapterOutput(source_envelope=envelope, drafts=drafts)


def _projection_payload(projection: OpenLoopProjection) -> dict[str, object]:
    if not isinstance(projection.kind, OpenLoopKind):
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection kind must be an OpenLoopKind"
        )
    if not isinstance(projection.status, OpenLoopStatus):
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection status must be an OpenLoopStatus"
        )
    if any(
        not isinstance(reason, OpenLoopReason)
        for reason in projection.reason_codes
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop reasons must be OpenLoopReason values"
        )
    return {
        "schema_version": projection.schema_version,
        "policy_version": projection.policy_version,
        "user_id": projection.user_id,
        "loop_key": projection.loop_key,
        "signal_id": projection.signal_id,
        "kind": projection.kind.value,
        "summary": projection.summary,
        "related_goal_ref": projection.related_goal_ref,
        "status": projection.status.value,
        "reason_codes": [value.value for value in projection.reason_codes],
        "source_refs": list(projection.source_refs),
        "opened_at": _dt(projection.opened_at),
        "due_at": _dt(projection.due_at) if projection.due_at else None,
        "resolution_ids": list(projection.resolution_ids),
        "as_of": _dt(projection.as_of),
        "review_required": projection.review_required,
    }


def _validate_projection_semantics(
    projection: OpenLoopProjection,
    *,
    result: OpenLoopProjectionResult,
) -> None:
    text_fields = {
        "user_id": projection.user_id,
        "loop_key": projection.loop_key,
        "signal_id": projection.signal_id,
        "summary": projection.summary,
    }
    for name, value in text_fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ContinuitySourceAdmissionError(
                f"OpenLoop projection {name} must be a non-empty string"
            )
    if (
        projection.related_goal_ref is not None
        and (
            not isinstance(projection.related_goal_ref, str)
            or not projection.related_goal_ref.strip()
        )
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop related_goal_ref must be None or a non-empty string"
        )
    if projection.schema_version != OPEN_LOOP_SCHEMA_VERSION:
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection schema_version is not supported"
        )
    if projection.policy_version != result.policy_version:
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection policy_version does not match result policy"
        )
    if projection.as_of != result.as_of:
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection as_of does not match result as_of"
        )
    if projection.user_id not in result.subject_ids:
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection user_id is absent from result subject_ids"
        )
    if projection.opened_at.tzinfo is None or projection.opened_at.utcoffset() is None:
        raise ContinuitySourceAdmissionError(
            "OpenLoop opened_at must be timezone-aware"
        )
    if projection.due_at is not None:
        if projection.due_at.tzinfo is None or projection.due_at.utcoffset() is None:
            raise ContinuitySourceAdmissionError(
                "OpenLoop due_at must be timezone-aware"
            )
        if projection.due_at < projection.opened_at:
            raise ContinuitySourceAdmissionError(
                "OpenLoop due_at cannot precede opened_at"
            )
    if projection.reason_codes != _expected_reasons(projection.status):
        raise ContinuitySourceAdmissionError(
            "OpenLoop reason_codes are not canonical for status"
        )
    if projection.source_refs != tuple(sorted(projection.source_refs)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop source_refs must be sorted"
        )
    if len(projection.source_refs) != len(set(projection.source_refs)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop source_refs cannot contain duplicates"
        )
    if not projection.source_refs or any(
        not isinstance(value, str) or not value.strip()
        for value in projection.source_refs
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop source_refs must contain non-empty strings"
        )
    if projection.resolution_ids != tuple(sorted(projection.resolution_ids)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop resolution_ids must be sorted"
        )
    if len(projection.resolution_ids) != len(set(projection.resolution_ids)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop resolution_ids cannot contain duplicates"
        )
    if any(
        not isinstance(value, str) or not value.strip()
        for value in projection.resolution_ids
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop resolution_ids must contain non-empty strings"
        )

    if projection.status is OpenLoopStatus.NOT_YET_OPEN:
        if projection.opened_at <= result.as_of:
            raise ContinuitySourceAdmissionError(
                "not-yet-open projection must open after result as_of"
            )
        if projection.resolution_ids or projection.review_required:
            raise ContinuitySourceAdmissionError(
                "not-yet-open projection cannot be resolved or require review"
            )
    elif projection.status is OpenLoopStatus.RESOLVED:
        if not projection.resolution_ids:
            raise ContinuitySourceAdmissionError(
                "resolved projection requires resolution evidence"
            )
        if projection.review_required:
            raise ContinuitySourceAdmissionError(
                "resolved projection cannot require review"
            )
    elif projection.status is OpenLoopStatus.OVERDUE:
        if projection.opened_at > result.as_of:
            raise ContinuitySourceAdmissionError(
                "overdue projection cannot open after result as_of"
            )
        if projection.due_at is None or projection.due_at >= result.as_of:
            raise ContinuitySourceAdmissionError(
                "overdue projection requires a passed due_at"
            )
        if projection.resolution_ids or not projection.review_required:
            raise ContinuitySourceAdmissionError(
                "overdue projection must be unresolved and require review"
            )
    else:
        if projection.opened_at > result.as_of:
            raise ContinuitySourceAdmissionError(
                "open projection cannot open after result as_of"
            )
        if projection.due_at is not None and projection.due_at < result.as_of:
            raise ContinuitySourceAdmissionError(
                "open projection cannot have a passed due_at"
            )
        if projection.resolution_ids or not projection.review_required:
            raise ContinuitySourceAdmissionError(
                "open projection must be unresolved and require review"
            )


def _validate_result_integrity(result: OpenLoopProjectionResult) -> str:
    if not isinstance(result.policy_version, str) or not result.policy_version.strip():
        raise ContinuitySourceAdmissionError(
            "OpenLoop result policy_version must be a non-empty string"
        )
    if result.policy_version != GOAL_OPEN_LOOP_POLICY_VERSION:
        raise ContinuitySourceAdmissionError(
            "OpenLoop result policy_version is not supported"
        )
    if result.as_of.tzinfo is None or result.as_of.utcoffset() is None:
        raise ContinuitySourceAdmissionError(
            "OpenLoop result as_of must be timezone-aware"
        )
    if not result.subject_ids:
        raise ContinuitySourceAdmissionError(
            "OpenLoop result subject_ids cannot be empty"
        )
    if result.subject_ids != tuple(sorted(result.subject_ids)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop result subject_ids must be sorted"
        )
    if len(result.subject_ids) != len(set(result.subject_ids)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop result subject_ids cannot contain duplicates"
        )
    if any(
        not isinstance(value, str) or not value.strip()
        for value in result.subject_ids
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop result subject_ids must contain non-empty strings"
        )

    ordered = tuple(sorted(result.projections, key=lambda value: value.loop_key))
    if result.projections != ordered:
        raise ContinuitySourceAdmissionError(
            "OpenLoop projections must be sorted by loop_key"
        )
    if len(result.projections) != len(
        {value.projection_id for value in result.projections}
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop projections cannot contain duplicate identities"
        )
    if len(result.projections) != len(
        {value.loop_key for value in result.projections}
    ):
        raise ContinuitySourceAdmissionError(
            "OpenLoop projections cannot contain duplicate loop keys"
        )

    for projection in result.projections:
        if not isinstance(projection, OpenLoopProjection):
            raise ContinuitySourceAdmissionError(
                "OpenLoop result must contain OpenLoopProjection values"
            )
        _validate_projection_semantics(projection, result=result)
        expected_projection_id = _digest(_projection_payload(projection))
        if projection.projection_id != expected_projection_id:
            raise ContinuitySourceAdmissionError(
                "OpenLoop projection_id does not match canonical payload"
            )

    expected_subjects = tuple(
        sorted({projection.user_id for projection in result.projections})
    )
    if result.subject_ids != expected_subjects:
        raise ContinuitySourceAdmissionError(
            "OpenLoop result subject_ids must exactly match projection subjects"
        )

    payload = {
        "policy_version": result.policy_version,
        "as_of": _dt(result.as_of),
        "subject_ids": list(result.subject_ids),
        "projection_ids": [
            projection.projection_id for projection in result.projections
        ],
    }
    expected_result_id = _digest(payload)
    if result.result_id != expected_result_id:
        raise ContinuitySourceAdmissionError(
            "OpenLoop result_id does not match canonical payload"
        )
    return expected_result_id


def _required_evidence(result: OpenLoopProjectionResult) -> set[str]:
    return {
        result.result_id,
        *(projection.projection_id for projection in result.projections),
        *(projection.signal_id for projection in result.projections),
        *(
            resolution_id
            for projection in result.projections
            for resolution_id in projection.resolution_ids
        ),
        *(
            source_ref
            for projection in result.projections
            for source_ref in projection.source_refs
        ),
    }


def _validate_binding(
    *,
    result: OpenLoopProjectionResult,
    binding_receipt: ContinuitySourceBindingReceipt,
) -> None:
    expected_digest = _validate_result_integrity(result)
    bound_ids = tuple(
        sorted(subject.subject_id for subject in binding_receipt.subject_refs)
    )
    if len(bound_ids) != len(set(bound_ids)):
        raise ContinuitySourceAdmissionError(
            "OpenLoop binding cannot assign multiple subject kinds to one user_id"
        )

    checks = (
        (
            binding_receipt.source_type == OPEN_LOOP_SOURCE_TYPE,
            "binding source_type does not identify an OpenLoop result",
        ),
        (
            binding_receipt.source_owner == OPEN_LOOP_SOURCE_OWNER,
            "binding source_owner does not identify the OpenLoop projector",
        ),
        (
            binding_receipt.source_component_version
            == OPEN_LOOP_SOURCE_COMPONENT_VERSION,
            "binding source_component_version is not supported",
        ),
        (
            binding_receipt.source_result_id == result.result_id,
            "binding source_result_id does not match the OpenLoop result",
        ),
        (
            binding_receipt.source_digest == expected_digest,
            "binding source_digest does not match canonical OpenLoop payload",
        ),
        (
            binding_receipt.source_policy_version == result.policy_version,
            "binding source_policy_version does not match the OpenLoop result",
        ),
        (
            binding_receipt.source_as_of == result.as_of,
            "binding source_as_of does not match the OpenLoop result",
        ),
        (
            bound_ids == result.subject_ids,
            "binding subject IDs must exactly match every OpenLoop result subject",
        ),
        (
            _required_evidence(result).issubset(
                set(binding_receipt.evidence_refs)
            ),
            "binding evidence must include result, projection, signal, "
            "resolution, and source references",
        ),
    )
    for valid, message in checks:
        if not valid:
            raise ContinuitySourceAdmissionError(message)


def _projection_drafts(
    *,
    projection: OpenLoopProjection,
    envelope: ContinuitySourceEnvelope,
    created_at: datetime,
) -> tuple[ContinuityObservationDraft, ...]:
    if projection.status not in _ACTIVE_STATUSES:
        return ()
    evidence = tuple(
        sorted(
            {
                projection.projection_id,
                projection.signal_id,
                *projection.resolution_ids,
                *projection.source_refs,
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
            reason_codes=tuple(
                sorted(
                    {
                        "open_loop_active_projection",
                        "open_loop_typed_source_signal",
                        f"open_loop_status:{projection.status.value}",
                    }
                )
            ),
            derivation_rule_id="open_loop.active_evidence_coverage.v1",
            created_at=created_at,
            scope=f"open_loop_projection:{projection.projection_id}",
        ),
    )
