"""Deterministic low-risk Advisory Shadow for continuity projections.

The gate accepts only explicit typed relevance signals. It never infers motive,
psychology, need, or intent from raw text. Its output is shadow-only and cannot
alter the answer path, persist memory, write Canon, or authorize actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable

from .evaluation import ReplayEvaluationReport
from .goal_open_loop import (
    GoalProjection,
    GoalStatus,
    OpenLoopKind,
    OpenLoopProjection,
    OpenLoopStatus,
)
from .state_reconciler import CurrentStateProjection, ProjectionStatus

ADVISORY_SCHEMA_VERSION = "continuity.advisory_shadow.v1"
ADVISORY_POLICY_VERSION = "continuity.advisory_shadow.policy.v1"


class AdvisoryShadowError(ValueError):
    """Advisory Shadow input violates a deterministic safety boundary."""


class AdvisoryAction(str, Enum):
    ANSWER_ONLY = "answer_only"
    REMIND = "remind"
    ASK_CONFIRMATION = "ask_confirmation"
    SUGGEST = "suggest"
    WARN = "warn"
    DEFER = "defer"
    SILENCE = "silence"


class AdvisoryAudience(str, Enum):
    PRIVATE = "private"
    SHARED = "shared"
    UNKNOWN = "unknown"


class AdvisorySensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AdvisoryRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AdvisorySignalKind(str, Enum):
    PRIORITY_MAY_HAVE_CHANGED = "priority_may_have_changed"
    GOAL_RELEVANT = "goal_relevant"
    OPEN_LOOP_RELEVANT = "open_loop_relevant"
    BLOCKER_RELEVANT = "blocker_relevant"


class AdvisoryReason(str, Enum):
    SHADOW_ONLY = "shadow_only"
    HARD_GATES_FAILED = "hard_gates_failed"
    NON_PRIVATE_AUDIENCE = "non_private_audience"
    NO_RELEVANT_SIGNAL = "no_relevant_signal"
    CONFIRMATION_NOT_ALLOWED = "confirmation_not_allowed"
    REMINDER_NOT_ALLOWED = "reminder_not_allowed"
    PRIORITY_CHANGE_UNCONFIRMED = "priority_change_unconfirmed"
    CONTESTED_STATE = "contested_state"
    ACTIVE_GOAL_RELEVANT = "active_goal_relevant"
    OPEN_LOOP_RELEVANT = "open_loop_relevant"
    OPEN_LOOP_OVERDUE = "open_loop_overdue"
    BLOCKER_RELEVANT = "blocker_relevant"
    PROJECTION_NOT_ACTIONABLE = "projection_not_actionable"


class AdvisoryAssumption(str, Enum):
    GOAL_MAY_STILL_APPLY = "goal_may_still_apply"
    OPEN_LOOP_MAY_STILL_MATTER = "open_loop_may_still_matter"
    PRIORITY_MAY_HAVE_CHANGED = "priority_may_have_changed"
    BLOCKER_MAY_STILL_APPLY = "blocker_may_still_apply"


class AdvisoryUncertainty(str, Enum):
    CURRENTNESS_UNCONFIRMED = "currentness_unconfirmed"
    SHADOW_EVALUATION_ONLY = "shadow_evaluation_only"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdvisoryShadowError(f"{name} must be a non-empty string")
    return value.strip()


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise AdvisoryShadowError(f"{name} must be a bool")
    return value


def _unique_refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    refs = tuple(_text(value, name) for value in values)
    if len(refs) != len(set(refs)):
        raise AdvisoryShadowError(f"{name} cannot contain duplicates")
    return tuple(sorted(refs))


def _enum_values(values: Iterable[Enum], name: str) -> tuple[Enum, ...]:
    items = tuple(values)
    if any(not isinstance(value, Enum) for value in items):
        raise AdvisoryShadowError(f"{name} contains an invalid value")
    by_value = {str(value.value): value for value in items}
    if len(by_value) != len(items):
        raise AdvisoryShadowError(f"{name} cannot contain duplicates")
    return tuple(by_value[key] for key in sorted(by_value))


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AdvisoryShadowRequest:
    request_ref: str
    audience: AdvisoryAudience
    sensitivity: AdvisorySensitivity = AdvisorySensitivity.LOW
    allow_reminders: bool = True
    allow_confirmation_questions: bool = True
    shadow_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_ref",
            _text(self.request_ref, "request_ref"),
        )
        if not isinstance(self.audience, AdvisoryAudience):
            raise AdvisoryShadowError("audience must be an AdvisoryAudience")
        if not isinstance(self.sensitivity, AdvisorySensitivity):
            raise AdvisoryShadowError(
                "sensitivity must be an AdvisorySensitivity"
            )
        for name in (
            "allow_reminders",
            "allow_confirmation_questions",
            "shadow_only",
        ):
            object.__setattr__(
                self,
                name,
                _strict_bool(getattr(self, name), name),
            )
        if not self.shadow_only:
            raise AdvisoryShadowError(
                "Advisory Shadow cannot be activated through this contract"
            )


@dataclass(frozen=True, slots=True)
class AdvisorySignal:
    signal_id: str
    kind: AdvisorySignalKind
    projection_id: str

    @classmethod
    def create(
        cls,
        *,
        kind: AdvisorySignalKind,
        projection_id: str,
    ) -> AdvisorySignal:
        if not isinstance(kind, AdvisorySignalKind):
            raise AdvisoryShadowError("kind must be an AdvisorySignalKind")
        projection_ref = _text(projection_id, "projection_id")
        payload = {
            "kind": kind.value,
            "projection_id": projection_ref,
        }
        return cls(_digest(payload), kind, projection_ref)


@dataclass(frozen=True, slots=True)
class AdviceCandidate:
    candidate_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    action: AdvisoryAction
    proposed_text: str | None
    basis_refs: tuple[str, ...]
    assumption_codes: tuple[AdvisoryAssumption, ...]
    uncertainty_codes: tuple[AdvisoryUncertainty, ...]
    sensitivity: AdvisorySensitivity
    risk: AdvisoryRisk
    reason_codes: tuple[AdvisoryReason, ...]
    source_signal_id: str | None
    shadow_only: bool

    @classmethod
    def create(
        cls,
        *,
        request_ref: str,
        action: AdvisoryAction,
        proposed_text: str | None,
        basis_refs: Iterable[str],
        assumption_codes: Iterable[AdvisoryAssumption],
        uncertainty_codes: Iterable[AdvisoryUncertainty],
        sensitivity: AdvisorySensitivity,
        risk: AdvisoryRisk,
        reason_codes: Iterable[AdvisoryReason],
        source_signal_id: str | None,
        policy_version: str = ADVISORY_POLICY_VERSION,
    ) -> AdviceCandidate:
        request = _text(request_ref, "request_ref")
        policy = _text(policy_version, "policy_version")
        if not isinstance(action, AdvisoryAction):
            raise AdvisoryShadowError("action must be an AdvisoryAction")
        if not isinstance(sensitivity, AdvisorySensitivity):
            raise AdvisoryShadowError(
                "sensitivity must be an AdvisorySensitivity"
            )
        if not isinstance(risk, AdvisoryRisk):
            raise AdvisoryShadowError("risk must be an AdvisoryRisk")
        text = (
            _text(proposed_text, "proposed_text")
            if proposed_text is not None
            else None
        )
        refs = _unique_refs(basis_refs, "basis_refs")
        assumptions = tuple(
            value
            for value in _enum_values(
                assumption_codes,
                "assumption_codes",
            )
            if isinstance(value, AdvisoryAssumption)
        )
        uncertainties = tuple(
            value
            for value in _enum_values(
                uncertainty_codes,
                "uncertainty_codes",
            )
            if isinstance(value, AdvisoryUncertainty)
        )
        reasons = tuple(
            value
            for value in _enum_values(reason_codes, "reason_codes")
            if isinstance(value, AdvisoryReason)
        )
        signal_id = (
            _text(source_signal_id, "source_signal_id")
            if source_signal_id is not None
            else None
        )
        if action in {AdvisoryAction.SILENCE, AdvisoryAction.DEFER}:
            if text is not None:
                raise AdvisoryShadowError(
                    "SILENCE/DEFER candidates cannot contain proposed_text"
                )
        elif text is None:
            raise AdvisoryShadowError(
                "user-facing advisory actions require proposed_text"
            )
        if action in {
            AdvisoryAction.REMIND,
            AdvisoryAction.ASK_CONFIRMATION,
            AdvisoryAction.SUGGEST,
            AdvisoryAction.WARN,
        } and not refs:
            raise AdvisoryShadowError(
                "user-facing advisory actions require basis_refs"
            )
        if AdvisoryReason.SHADOW_ONLY not in reasons:
            raise AdvisoryShadowError("reason_codes must include SHADOW_ONLY")
        payload = {
            "schema_version": ADVISORY_SCHEMA_VERSION,
            "policy_version": policy,
            "request_ref": request,
            "action": action.value,
            "proposed_text": text,
            "basis_refs": list(refs),
            "assumption_codes": [value.value for value in assumptions],
            "uncertainty_codes": [value.value for value in uncertainties],
            "sensitivity": sensitivity.value,
            "risk": risk.value,
            "reason_codes": [value.value for value in reasons],
            "source_signal_id": signal_id,
            "shadow_only": True,
        }
        return cls(
            candidate_id=_digest(payload),
            schema_version=ADVISORY_SCHEMA_VERSION,
            policy_version=policy,
            request_ref=request,
            action=action,
            proposed_text=text,
            basis_refs=refs,
            assumption_codes=assumptions,
            uncertainty_codes=uncertainties,
            sensitivity=sensitivity,
            risk=risk,
            reason_codes=reasons,
            source_signal_id=signal_id,
            shadow_only=True,
        )

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "request_ref": self.request_ref,
            "action": self.action.value,
            "proposed_text": self.proposed_text,
            "basis_refs": list(self.basis_refs),
            "assumption_codes": [
                value.value for value in self.assumption_codes
            ],
            "uncertainty_codes": [
                value.value for value in self.uncertainty_codes
            ],
            "sensitivity": self.sensitivity.value,
            "risk": self.risk.value,
            "reason_codes": [value.value for value in self.reason_codes],
            "source_signal_id": self.source_signal_id,
            "shadow_only": self.shadow_only,
        }


@dataclass(frozen=True, slots=True)
class AdvisoryReceipt:
    receipt_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    candidate_id: str
    evaluated_signal_ids: tuple[str, ...]
    excluded_signal_ids: tuple[str, ...]
    reason_codes: tuple[AdvisoryReason, ...]
    shadow_only: bool

    @classmethod
    def create(
        cls,
        *,
        request_ref: str,
        candidate_id: str,
        evaluated_signal_ids: Iterable[str],
        excluded_signal_ids: Iterable[str],
        reason_codes: Iterable[AdvisoryReason],
        policy_version: str = ADVISORY_POLICY_VERSION,
    ) -> AdvisoryReceipt:
        request = _text(request_ref, "request_ref")
        candidate = _text(candidate_id, "candidate_id")
        evaluated = _unique_refs(
            evaluated_signal_ids,
            "evaluated_signal_ids",
        )
        excluded = _unique_refs(
            excluded_signal_ids,
            "excluded_signal_ids",
        )
        if set(evaluated) & set(excluded):
            raise AdvisoryShadowError(
                "a signal cannot be evaluated and excluded"
            )
        reasons = tuple(
            value
            for value in _enum_values(reason_codes, "reason_codes")
            if isinstance(value, AdvisoryReason)
        )
        if AdvisoryReason.SHADOW_ONLY not in reasons:
            raise AdvisoryShadowError("reason_codes must include SHADOW_ONLY")
        policy = _text(policy_version, "policy_version")
        payload = {
            "schema_version": ADVISORY_SCHEMA_VERSION,
            "policy_version": policy,
            "request_ref": request,
            "candidate_id": candidate,
            "evaluated_signal_ids": list(evaluated),
            "excluded_signal_ids": list(excluded),
            "reason_codes": [value.value for value in reasons],
            "shadow_only": True,
        }
        return cls(
            receipt_id=_digest(payload),
            schema_version=ADVISORY_SCHEMA_VERSION,
            policy_version=policy,
            request_ref=request,
            candidate_id=candidate,
            evaluated_signal_ids=evaluated,
            excluded_signal_ids=excluded,
            reason_codes=reasons,
            shadow_only=True,
        )


@dataclass(frozen=True, slots=True)
class AdvisoryShadowResult:
    result_id: str
    candidate: AdviceCandidate
    receipt: AdvisoryReceipt

    @classmethod
    def create(
        cls,
        candidate: AdviceCandidate,
        receipt: AdvisoryReceipt,
    ) -> AdvisoryShadowResult:
        if not isinstance(candidate, AdviceCandidate):
            raise AdvisoryShadowError("candidate must be AdviceCandidate")
        if not isinstance(receipt, AdvisoryReceipt):
            raise AdvisoryShadowError("receipt must be AdvisoryReceipt")
        if receipt.candidate_id != candidate.candidate_id:
            raise AdvisoryShadowError(
                "receipt does not reference advisory candidate"
            )
        if receipt.request_ref != candidate.request_ref:
            raise AdvisoryShadowError(
                "candidate and receipt request_ref do not match"
            )
        payload = {
            "candidate_id": candidate.candidate_id,
            "receipt_id": receipt.receipt_id,
        }
        return cls(_digest(payload), candidate, receipt)


class AdvisoryShadowGate:
    """Select at most one deterministic low-risk shadow candidate."""

    def evaluate(
        self,
        *,
        request: AdvisoryShadowRequest,
        hard_gate_report: ReplayEvaluationReport,
        signals: Iterable[AdvisorySignal] = (),
        state_projections: Iterable[CurrentStateProjection] = (),
        goal_projections: Iterable[GoalProjection] = (),
        open_loop_projections: Iterable[OpenLoopProjection] = (),
    ) -> AdvisoryShadowResult:
        if not isinstance(request, AdvisoryShadowRequest):
            raise AdvisoryShadowError(
                "request must be an AdvisoryShadowRequest"
            )
        if not isinstance(hard_gate_report, ReplayEvaluationReport):
            raise AdvisoryShadowError(
                "hard_gate_report must be ReplayEvaluationReport"
            )
        signal_map = self._signal_map(signals)
        states = self._state_map(state_projections)
        goals = self._goal_map(goal_projections)
        loops = self._loop_map(open_loop_projections)
        self._validate_signal_targets(signal_map, states, goals, loops)
        signal_ids = tuple(sorted(signal_map))

        if not hard_gate_report.passed:
            candidate = AdviceCandidate.create(
                request_ref=request.request_ref,
                action=AdvisoryAction.DEFER,
                proposed_text=None,
                basis_refs=(),
                assumption_codes=(),
                uncertainty_codes=(
                    AdvisoryUncertainty.SHADOW_EVALUATION_ONLY,
                ),
                sensitivity=request.sensitivity,
                risk=AdvisoryRisk.HIGH,
                reason_codes=(
                    AdvisoryReason.HARD_GATES_FAILED,
                    AdvisoryReason.SHADOW_ONLY,
                ),
                source_signal_id=None,
            )
            return self._result(
                request,
                candidate,
                evaluated=(),
                excluded=signal_ids,
            )

        if request.audience is not AdvisoryAudience.PRIVATE:
            candidate = self._silent_candidate(
                request,
                AdvisoryReason.NON_PRIVATE_AUDIENCE,
            )
            return self._result(
                request,
                candidate,
                evaluated=(),
                excluded=signal_ids,
            )

        ranked = tuple(
            sorted(
                signal_map.values(),
                key=lambda value: (
                    -self._priority(value.kind),
                    value.signal_id,
                ),
            )
        )
        excluded: list[str] = []
        for signal in ranked:
            candidate = self._candidate_for_signal(
                request,
                signal,
                states,
                goals,
                loops,
            )
            if candidate is None:
                excluded.append(signal.signal_id)
                continue
            return self._result(
                request,
                candidate,
                evaluated=(signal.signal_id,),
                excluded=tuple(
                    sorted(
                        {
                            *excluded,
                            *(
                                value.signal_id
                                for value in ranked
                                if value.signal_id != signal.signal_id
                            ),
                        }
                    )
                ),
            )

        candidate = self._silent_candidate(
            request,
            AdvisoryReason.NO_RELEVANT_SIGNAL,
        )
        return self._result(
            request,
            candidate,
            evaluated=(),
            excluded=signal_ids,
        )

    @staticmethod
    def _priority(kind: AdvisorySignalKind) -> int:
        priorities = {
            AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED: 400,
            AdvisorySignalKind.BLOCKER_RELEVANT: 300,
            AdvisorySignalKind.OPEN_LOOP_RELEVANT: 200,
            AdvisorySignalKind.GOAL_RELEVANT: 100,
        }
        return priorities[kind]

    @staticmethod
    def _signal_map(
        values: Iterable[AdvisorySignal],
    ) -> dict[str, AdvisorySignal]:
        result: dict[str, AdvisorySignal] = {}
        for value in values:
            if not isinstance(value, AdvisorySignal):
                raise AdvisoryShadowError("signals contain an invalid value")
            existing = result.get(value.signal_id)
            if existing is not None and existing != value:
                raise AdvisoryShadowError(
                    f"conflicting advisory signal: {value.signal_id}"
                )
            result[value.signal_id] = value
        return result

    @staticmethod
    def _state_map(
        values: Iterable[CurrentStateProjection],
    ) -> dict[str, CurrentStateProjection]:
        result: dict[str, CurrentStateProjection] = {}
        for value in values:
            if not isinstance(value, CurrentStateProjection):
                raise AdvisoryShadowError(
                    "state_projections contain an invalid value"
                )
            existing = result.get(value.projection_id)
            if existing is not None and existing != value:
                raise AdvisoryShadowError(
                    f"conflicting state projection: {value.projection_id}"
                )
            result[value.projection_id] = value
        return result

    @staticmethod
    def _goal_map(
        values: Iterable[GoalProjection],
    ) -> dict[str, GoalProjection]:
        result: dict[str, GoalProjection] = {}
        for value in values:
            if not isinstance(value, GoalProjection):
                raise AdvisoryShadowError(
                    "goal_projections contain an invalid value"
                )
            existing = result.get(value.projection_id)
            if existing is not None and existing != value:
                raise AdvisoryShadowError(
                    f"conflicting goal projection: {value.projection_id}"
                )
            result[value.projection_id] = value
        return result

    @staticmethod
    def _loop_map(
        values: Iterable[OpenLoopProjection],
    ) -> dict[str, OpenLoopProjection]:
        result: dict[str, OpenLoopProjection] = {}
        for value in values:
            if not isinstance(value, OpenLoopProjection):
                raise AdvisoryShadowError(
                    "open_loop_projections contain an invalid value"
                )
            existing = result.get(value.projection_id)
            if existing is not None and existing != value:
                raise AdvisoryShadowError(
                    f"conflicting open-loop projection: {value.projection_id}"
                )
            result[value.projection_id] = value
        return result

    @staticmethod
    def _validate_signal_targets(
        signals: dict[str, AdvisorySignal],
        states: dict[str, CurrentStateProjection],
        goals: dict[str, GoalProjection],
        loops: dict[str, OpenLoopProjection],
    ) -> None:
        for signal in signals.values():
            if signal.kind is AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED:
                if signal.projection_id not in states:
                    raise AdvisoryShadowError(
                        "priority signal references unknown state projection"
                    )
            elif signal.kind is AdvisorySignalKind.GOAL_RELEVANT:
                if signal.projection_id not in goals:
                    raise AdvisoryShadowError(
                        "goal signal references unknown goal projection"
                    )
            elif signal.kind in {
                AdvisorySignalKind.OPEN_LOOP_RELEVANT,
                AdvisorySignalKind.BLOCKER_RELEVANT,
            }:
                if signal.projection_id not in loops:
                    raise AdvisoryShadowError(
                        "open-loop signal references unknown projection"
                    )

    def _candidate_for_signal(
        self,
        request: AdvisoryShadowRequest,
        signal: AdvisorySignal,
        states: dict[str, CurrentStateProjection],
        goals: dict[str, GoalProjection],
        loops: dict[str, OpenLoopProjection],
    ) -> AdviceCandidate | None:
        if signal.kind is AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED:
            return self._priority_candidate(
                request,
                signal,
                states[signal.projection_id],
            )
        if signal.kind is AdvisorySignalKind.GOAL_RELEVANT:
            return self._goal_candidate(
                request,
                signal,
                goals[signal.projection_id],
            )
        if signal.kind is AdvisorySignalKind.OPEN_LOOP_RELEVANT:
            return self._loop_candidate(
                request,
                signal,
                loops[signal.projection_id],
                blocker=False,
            )
        return self._loop_candidate(
            request,
            signal,
            loops[signal.projection_id],
            blocker=True,
        )

    @staticmethod
    def _priority_candidate(
        request: AdvisoryShadowRequest,
        signal: AdvisorySignal,
        projection: CurrentStateProjection,
    ) -> AdviceCandidate | None:
        if not request.allow_confirmation_questions:
            return None
        refs = AdvisoryShadowGate._state_refs(projection)
        reasons = {
            AdvisoryReason.PRIORITY_CHANGE_UNCONFIRMED,
            AdvisoryReason.SHADOW_ONLY,
        }
        if projection.status is ProjectionStatus.CONTESTED:
            reasons.add(AdvisoryReason.CONTESTED_STATE)
        return AdviceCandidate.create(
            request_ref=request.request_ref,
            action=AdvisoryAction.ASK_CONFIRMATION,
            proposed_text=(
                "Ранее зафиксированный приоритет может быть неактуален. "
                "Подтвердить, изменился ли приоритет?"
            ),
            basis_refs=refs,
            assumption_codes=(
                AdvisoryAssumption.PRIORITY_MAY_HAVE_CHANGED,
            ),
            uncertainty_codes=(
                AdvisoryUncertainty.CURRENTNESS_UNCONFIRMED,
                AdvisoryUncertainty.SHADOW_EVALUATION_ONLY,
            ),
            sensitivity=request.sensitivity,
            risk=AdvisoryRisk.LOW,
            reason_codes=reasons,
            source_signal_id=signal.signal_id,
        )

    @staticmethod
    def _goal_candidate(
        request: AdvisoryShadowRequest,
        signal: AdvisorySignal,
        projection: GoalProjection,
    ) -> AdviceCandidate | None:
        if projection.status is not GoalStatus.ACTIVE:
            return None
        if request.allow_reminders:
            action = AdvisoryAction.REMIND
            text = f"Ранее была подтверждена цель: «{projection.title}»."
        elif request.allow_confirmation_questions:
            action = AdvisoryAction.ASK_CONFIRMATION
            text = f"Цель «{projection.title}» всё ещё актуальна?"
        else:
            return None
        return AdviceCandidate.create(
            request_ref=request.request_ref,
            action=action,
            proposed_text=text,
            basis_refs=projection.source_refs,
            assumption_codes=(AdvisoryAssumption.GOAL_MAY_STILL_APPLY,),
            uncertainty_codes=(
                AdvisoryUncertainty.CURRENTNESS_UNCONFIRMED,
                AdvisoryUncertainty.SHADOW_EVALUATION_ONLY,
            ),
            sensitivity=request.sensitivity,
            risk=AdvisoryRisk.LOW,
            reason_codes=(
                AdvisoryReason.ACTIVE_GOAL_RELEVANT,
                AdvisoryReason.SHADOW_ONLY,
            ),
            source_signal_id=signal.signal_id,
        )

    @staticmethod
    def _loop_candidate(
        request: AdvisoryShadowRequest,
        signal: AdvisorySignal,
        projection: OpenLoopProjection,
        *,
        blocker: bool,
    ) -> AdviceCandidate | None:
        if projection.status not in {
            OpenLoopStatus.OPEN,
            OpenLoopStatus.OVERDUE,
        }:
            return None
        if blocker and projection.kind is not OpenLoopKind.BLOCKER:
            return None

        if projection.status is OpenLoopStatus.OVERDUE and request.allow_reminders:
            action = AdvisoryAction.REMIND
            text = f"Незакрытый пункт просрочен: «{projection.summary}»."
        elif request.allow_confirmation_questions:
            action = AdvisoryAction.ASK_CONFIRMATION
            text = f"Вернуться к незакрытому пункту: «{projection.summary}»?"
        elif request.allow_reminders:
            action = AdvisoryAction.REMIND
            text = f"Остаётся незакрытый пункт: «{projection.summary}»."
        else:
            return None

        reason = (
            AdvisoryReason.BLOCKER_RELEVANT
            if blocker
            else (
                AdvisoryReason.OPEN_LOOP_OVERDUE
                if projection.status is OpenLoopStatus.OVERDUE
                else AdvisoryReason.OPEN_LOOP_RELEVANT
            )
        )
        assumption = (
            AdvisoryAssumption.BLOCKER_MAY_STILL_APPLY
            if blocker
            else AdvisoryAssumption.OPEN_LOOP_MAY_STILL_MATTER
        )
        return AdviceCandidate.create(
            request_ref=request.request_ref,
            action=action,
            proposed_text=text,
            basis_refs=projection.source_refs,
            assumption_codes=(assumption,),
            uncertainty_codes=(
                AdvisoryUncertainty.CURRENTNESS_UNCONFIRMED,
                AdvisoryUncertainty.SHADOW_EVALUATION_ONLY,
            ),
            sensitivity=request.sensitivity,
            risk=AdvisoryRisk.LOW,
            reason_codes=(reason, AdvisoryReason.SHADOW_ONLY),
            source_signal_id=signal.signal_id,
        )

    @staticmethod
    def _state_refs(projection: CurrentStateProjection) -> tuple[str, ...]:
        refs = {
            *projection.candidate_assertion_refs,
            *projection.supporting_assertion_refs,
            *projection.contradiction_assertion_refs,
            *projection.superseded_assertion_refs,
            *projection.retracted_assertion_refs,
        }
        if projection.selected_assertion_ref is not None:
            refs.add(projection.selected_assertion_ref)
        if not refs:
            refs.add(projection.projection_id)
        return tuple(sorted(refs))

    @staticmethod
    def _silent_candidate(
        request: AdvisoryShadowRequest,
        reason: AdvisoryReason,
    ) -> AdviceCandidate:
        return AdviceCandidate.create(
            request_ref=request.request_ref,
            action=AdvisoryAction.SILENCE,
            proposed_text=None,
            basis_refs=(),
            assumption_codes=(),
            uncertainty_codes=(
                AdvisoryUncertainty.SHADOW_EVALUATION_ONLY,
            ),
            sensitivity=request.sensitivity,
            risk=AdvisoryRisk.LOW,
            reason_codes=(reason, AdvisoryReason.SHADOW_ONLY),
            source_signal_id=None,
        )

    @staticmethod
    def _result(
        request: AdvisoryShadowRequest,
        candidate: AdviceCandidate,
        *,
        evaluated: Iterable[str],
        excluded: Iterable[str],
    ) -> AdvisoryShadowResult:
        receipt = AdvisoryReceipt.create(
            request_ref=request.request_ref,
            candidate_id=candidate.candidate_id,
            evaluated_signal_ids=evaluated,
            excluded_signal_ids=excluded,
            reason_codes=candidate.reason_codes,
        )
        return AdvisoryShadowResult.create(candidate, receipt)


__all__ = [
    "ADVISORY_POLICY_VERSION",
    "ADVISORY_SCHEMA_VERSION",
    "AdviceCandidate",
    "AdvisoryAction",
    "AdvisoryAssumption",
    "AdvisoryAudience",
    "AdvisoryReason",
    "AdvisoryReceipt",
    "AdvisoryRisk",
    "AdvisorySensitivity",
    "AdvisoryShadowError",
    "AdvisoryShadowGate",
    "AdvisoryShadowRequest",
    "AdvisoryShadowResult",
    "AdvisorySignal",
    "AdvisorySignalKind",
    "AdvisoryUncertainty",
]
