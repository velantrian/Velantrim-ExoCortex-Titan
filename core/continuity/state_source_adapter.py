"""Explicit, unwired State reconciliation to Continuity Draft adapter.

This module validates one immutable ``StateReconciliationResult`` against an
externally issued source-binding receipt, then derives a neutral source
envelope and deterministic observation drafts. It does not issue identity,
authorization, admission, persistence, routing, response, reminder, tool,
action, Canon, TruthGate, or runtime authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

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
from .state_reconciler import (
    STATE_PROJECTION_SCHEMA_VERSION,
    CurrentStateProjection,
    ProjectionStatus,
    StateReconciliationResult,
)

STATE_SOURCE_TYPE = "state_reconciliation_result"
STATE_SOURCE_OWNER = "continuity.state_reconciler"
STATE_SOURCE_ADAPTER_ID = "continuity.state_reconciliation_to_drafts"
STATE_SOURCE_ADAPTER_VERSION = "1"
STATE_SOURCE_COMPONENT_VERSION = "1"


@dataclass(frozen=True, slots=True)
class StateDraftAdapterOutput:
    """Evidence-only output from one explicit State adapter invocation."""

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


def adapt_state_reconciliation_to_drafts(
    *,
    result: StateReconciliationResult,
    binding_receipt: ContinuitySourceBindingReceipt,
    authorization_context: ContinuityAuthorizationContext,
    created_at: datetime,
) -> StateDraftAdapterOutput:
    """Validate one bound State result and derive conservative Draft values."""
    if not isinstance(result, StateReconciliationResult):
        raise ContinuitySourceAdmissionError(
            "result must be a StateReconciliationResult"
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
        source_schema_version=STATE_PROJECTION_SCHEMA_VERSION,
        producer_adapter_id=STATE_SOURCE_ADAPTER_ID,
        producer_adapter_version=STATE_SOURCE_ADAPTER_VERSION,
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
    return StateDraftAdapterOutput(source_envelope=envelope, drafts=drafts)


def _validate_binding(
    *,
    result: StateReconciliationResult,
    binding_receipt: ContinuitySourceBindingReceipt,
) -> None:
    expected_digest = sha256(result.canonical_bytes()).hexdigest()
    expected_subjects = frozenset(
        (projection.subject_ref.subject_id, projection.subject_ref.kind.value)
        for projection in result.projections
    )
    bound_subjects = frozenset(
        (subject.subject_id, subject.kind.value)
        for subject in binding_receipt.subject_refs
    )
    required_evidence = {
        result.result_id,
        *(projection.projection_id for projection in result.projections),
        *result.assertion_refs,
        *result.relation_refs,
    }

    checks = (
        (
            binding_receipt.source_type == STATE_SOURCE_TYPE,
            "binding source_type does not identify a State reconciliation result",
        ),
        (
            binding_receipt.source_owner == STATE_SOURCE_OWNER,
            "binding source_owner does not identify the State reconciler",
        ),
        (
            binding_receipt.source_component_version
            == STATE_SOURCE_COMPONENT_VERSION,
            "binding source_component_version is not supported",
        ),
        (
            binding_receipt.source_result_id == result.result_id,
            "binding source_result_id does not match the State result",
        ),
        (
            binding_receipt.source_digest == expected_digest,
            "binding source_digest does not match canonical State result bytes",
        ),
        (
            binding_receipt.source_policy_version == result.policy_version,
            "binding source_policy_version does not match the State result",
        ),
        (
            binding_receipt.source_as_of == result.as_of,
            "binding source_as_of does not match the State result",
        ),
        (
            bound_subjects == expected_subjects,
            "binding subject set must exactly match every State projection subject",
        ),
        (
            required_evidence.issubset(set(binding_receipt.evidence_refs)),
            "binding evidence must include result, projection, assertion, and relation references",
        ),
    )
    for valid, message in checks:
        if not valid:
            raise ContinuitySourceAdmissionError(message)


def _projection_scope(projection: CurrentStateProjection) -> str:
    subject = projection.subject_ref
    return f"{subject.kind.value}:{subject.subject_id}:{projection.predicate}"


def _projection_evidence(projection: CurrentStateProjection) -> tuple[str, ...]:
    refs = {
        projection.projection_id,
        *projection.candidate_assertion_refs,
        *projection.supporting_assertion_refs,
        *projection.contradiction_assertion_refs,
        *projection.superseded_assertion_refs,
        *projection.retracted_assertion_refs,
        *projection.expired_assertion_refs,
        *projection.future_assertion_refs,
    }
    if projection.selected_assertion_ref is not None:
        refs.add(projection.selected_assertion_ref)
    return tuple(sorted(refs))


def _projection_drafts(
    *,
    projection: CurrentStateProjection,
    envelope: ContinuitySourceEnvelope,
    created_at: datetime,
) -> tuple[ContinuityObservationDraft, ...]:
    scope = _projection_scope(projection)
    evidence = _projection_evidence(projection)
    drafts: list[ContinuityObservationDraft] = []

    degraded_reasons = {
        reason.value for reason in projection.reason_codes
    }
    if projection.status in {
        ProjectionStatus.CONTESTED,
        ProjectionStatus.UNRESOLVED,
    }:
        degraded_reasons.add(f"state_status:{projection.status.value}")
    if projection.review_required:
        degraded_reasons.add("state_review_required")
    if degraded_reasons:
        drafts.append(
            ContinuityObservationDraft.create(
                source_envelope=envelope,
                signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
                value=True,
                proposed_confidence=1.0,
                evidence_refs=evidence,
                reason_codes=tuple(sorted(degraded_reasons)),
                derivation_rule_id="state.context_degraded.v1",
                created_at=created_at,
                scope=scope,
            )
        )

    for contradiction_ref in projection.contradiction_assertion_refs:
        drafts.append(
            ContinuityObservationDraft.create(
                source_envelope=envelope,
                signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
                value=True,
                proposed_confidence=1.0,
                evidence_refs=(projection.projection_id, contradiction_ref),
                reason_codes=("state_active_contradiction",),
                derivation_rule_id="state.active_contradiction.v1",
                created_at=created_at,
                scope=f"{scope}:contradiction:{contradiction_ref}",
            )
        )

    freshness: str | None = None
    if projection.status is ProjectionStatus.STALE:
        freshness = "stale"
    elif projection.status is ProjectionStatus.EXPIRED:
        freshness = "critical_stale"
    if freshness is not None:
        drafts.append(
            ContinuityObservationDraft.create(
                source_envelope=envelope,
                signal_type=ContinuitySignalType.CONTEXT_FRESHNESS,
                value=freshness,
                proposed_confidence=1.0,
                evidence_refs=evidence,
                reason_codes=(f"state_status:{projection.status.value}",),
                derivation_rule_id="state.context_freshness.v1",
                created_at=created_at,
                scope=scope,
            )
        )

    return tuple(drafts)
