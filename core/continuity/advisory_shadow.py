"""Deterministic low-risk Advisory Shadow over typed continuity projections.

Only explicit relevance signals and a passed replay report may produce a
shadow candidate. This module never reads raw request text, persists state,
writes Canon, changes an answer, sends a reminder, calls a tool, or authorizes
an action.
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

ADVISORY_SCHEMA_VERSION = "continuity.advisory_shadow.v2"
ADVISORY_POLICY_VERSION = "continuity.advisory_shadow.policy.v2"


class AdvisoryShadowError(ValueError):
    pass


class AdvisoryAction(str, Enum):
    REMIND = "remind"
    ASK_CONFIRMATION = "ask_confirmation"
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


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdvisoryShadowError(f"{name} must be a non-empty string")
    return value.strip()


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise AdvisoryShadowError(f"{name} must be a bool")
    return value


def _refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    items = tuple(_text(value, name) for value in values)
    if len(items) != len(set(items)):
        raise AdvisoryShadowError(f"{name} cannot contain duplicates")
    return tuple(sorted(items))


def _reasons(values: Iterable[AdvisoryReason]) -> tuple[AdvisoryReason, ...]:
    items = tuple(values)
    if any(not isinstance(value, AdvisoryReason) for value in items):
        raise AdvisoryShadowError("reason_codes contain an invalid value")
    by_value = {value.value: value for value in items}
    if len(by_value) != len(items):
        raise AdvisoryShadowError("reason_codes cannot contain duplicates")
    return tuple(by_value[key] for key in sorted(by_value))


def _json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(payload: object) -> str:
    return sha256(_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AdvisoryShadowRequest:
    request_ref: str
    audience: AdvisoryAudience
    sensitivity: AdvisorySensitivity = AdvisorySensitivity.LOW
    allow_reminders: bool = True
    allow_confirmation_questions: bool = True
    shadow_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_ref", _text(self.request_ref, "request_ref"))
        if not isinstance(self.audience, AdvisoryAudience):
            raise AdvisoryShadowError("audience must be an AdvisoryAudience")
        if not isinstance(self.sensitivity, AdvisorySensitivity):
            raise AdvisoryShadowError("sensitivity must be an AdvisorySensitivity")
        for name in (
            "allow_reminders",
            "allow_confirmation_questions",
            "shadow_only",
        ):
            object.__setattr__(self, name, _bool(getattr(self, name), name))
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
        cls, *, kind: AdvisorySignalKind, projection_id: str
    ) -> AdvisorySignal:
        if not isinstance(kind, AdvisorySignalKind):
            raise AdvisoryShadowError("kind must be an AdvisorySignalKind")
        target = _text(projection_id, "projection_id")
        return cls(_digest({"kind": kind.value, "projection_id": target}), kind, target)


@dataclass(frozen=True, slots=True)
class AdviceCandidate:
    candidate_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    action: AdvisoryAction
    proposed_text: str | None
    basis_refs: tuple[str, ...]
    reason_codes: tuple[AdvisoryReason, ...]
    source_signal_id: str | None
    sensitivity: AdvisorySensitivity
    risk: AdvisoryRisk
    shadow_only: bool

    @classmethod
    def create(
        cls,
        *,
        request_ref: str,
        action: AdvisoryAction,
        proposed_text: str | None,
        basis_refs: Iterable[str],
        reason_codes: Iterable[AdvisoryReason],
        source_signal_id: str | None,
        sensitivity: AdvisorySensitivity,
        risk: AdvisoryRisk,
        policy_version: str = ADVISORY_POLICY_VERSION,
    ) -> AdviceCandidate:
        request = _text(request_ref, "request_ref")
        policy = _text(policy_version, "policy_version")
        if not isinstance(action, AdvisoryAction):
            raise AdvisoryShadowError("action must be an AdvisoryAction")
        if not isinstance(sensitivity, AdvisorySensitivity):
            raise AdvisoryShadowError("sensitivity must be an AdvisorySensitivity")
        if not isinstance(risk, AdvisoryRisk):
            raise AdvisoryShadowError("risk must be an AdvisoryRisk")
        text = _text(proposed_text, "proposed_text") if proposed_text is not None else None
        basis = _refs(basis_refs, "basis_refs")
        reasons = _reasons(reason_codes)
        signal = (
            _text(source_signal_id, "source_signal_id")
            if source_signal_id is not None
            else None
        )
        if AdvisoryReason.SHADOW_ONLY not in reasons:
            raise AdvisoryShadowError("reason_codes must include SHADOW_ONLY")
        if action in {AdvisoryAction.SILENCE, AdvisoryAction.DEFER}:
            if text is not None:
                raise AdvisoryShadowError("SILENCE/DEFER cannot contain proposed_text")
        elif text is None:
            raise AdvisoryShadowError(
                "REMIND/ASK_CONFIRMATION require proposed_text"
            )
        if action in {AdvisoryAction.REMIND, AdvisoryAction.ASK_CONFIRMATION}:
            if not basis:
                raise AdvisoryShadowError(
                    "user-facing-shaped candidates require basis_refs"
                )
            if signal is None:
                raise AdvisoryShadowError(
                    "user-facing-shaped candidates require source_signal_id"
                )
        payload = {
            "schema_version": ADVISORY_SCHEMA_VERSION,
            "policy_version": policy,
            "request_ref": request,
            "action": action.value,
            "proposed_text": text,
            "basis_refs": list(basis),
            "reason_codes": [reason.value for reason in reasons],
            "source_signal_id": signal,
            "sensitivity": sensitivity.value,
            "risk": risk.value,
            "shadow_only": True,
        }
        return cls(
            _digest(payload),
            ADVISORY_SCHEMA_VERSION,
            policy,
            request,
            action,
            text,
            basis,
            reasons,
            signal,
            sensitivity,
            risk,
            True,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "request_ref": self.request_ref,
            "action": self.action.value,
            "proposed_text": self.proposed_text,
            "basis_refs": list(self.basis_refs),
            "reason_codes": [reason.value for reason in self.reason_codes],
            "source_signal_id": self.source_signal_id,
            "sensitivity": self.sensitivity.value,
            "risk": self.risk.value,
            "shadow_only": self.shadow_only,
        }


@dataclass(frozen=True, slots=True)
class AdvisoryReceipt:
    receipt_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    evaluation_report_id: str
    candidate_id: str
    evaluated_signal_ids: tuple[str, ...]
    excluded_signal_ids: tuple[str, ...]
    hard_gates_passed: bool
    shadow_only: bool

    @classmethod
    def create(
        cls,
        *,
        request_ref: str,
        evaluation_report_id: str,
        candidate_id: str,
        evaluated_signal_ids: Iterable[str],
        excluded_signal_ids: Iterable[str],
        hard_gates_passed: bool,
        policy_version: str = ADVISORY_POLICY_VERSION,
    ) -> AdvisoryReceipt:
        request = _text(request_ref, "request_ref")
        report = _text(evaluation_report_id, "evaluation_report_id")
        candidate = _text(candidate_id, "candidate_id")
        evaluated = _refs(evaluated_signal_ids, "evaluated_signal_ids")
        excluded = _refs(excluded_signal_ids, "excluded_signal_ids")
        if set(evaluated) & set(excluded):
            raise AdvisoryShadowError("evaluated and excluded signals cannot overlap")
        passed = _bool(hard_gates_passed, "hard_gates_passed")
        policy = _text(policy_version, "policy_version")
        payload = {
            "schema_version": ADVISORY_SCHEMA_VERSION,
            "policy_version": policy,
            "request_ref": request,
            "evaluation_report_id": report,
            "candidate_id": candidate,
            "evaluated_signal_ids": list(evaluated),
            "excluded_signal_ids": list(excluded),
            "hard_gates_passed": passed,
            "shadow_only": True,
        }
        return cls(
            _digest(payload),
            ADVISORY_SCHEMA_VERSION,
            policy,
            request,
            report,
            candidate,
            evaluated,
            excluded,
            passed,
            True,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "request_ref": self.request_ref,
            "evaluation_report_id": self.evaluation_report_id,
            "candidate_id": self.candidate_id,
            "evaluated_signal_ids": list(self.evaluated_signal_ids),
            "excluded_signal_ids": list(self.excluded_signal_ids),
            "hard_gates_passed": self.hard_gates_passed,
            "shadow_only": self.shadow_only,
        }


@dataclass(frozen=True, slots=True)
class AdvisoryShadowResult:
    result_id: str
    candidate: AdviceCandidate
    receipt: AdvisoryReceipt

    @classmethod
    def create(
        cls, candidate: AdviceCandidate, receipt: AdvisoryReceipt
    ) -> AdvisoryShadowResult:
        if not isinstance(candidate, AdviceCandidate):
            raise AdvisoryShadowError("candidate must be an AdviceCandidate")
        if not isinstance(receipt, AdvisoryReceipt):
            raise AdvisoryShadowError("receipt must be an AdvisoryReceipt")
        if receipt.candidate_id != candidate.candidate_id:
            raise AdvisoryShadowError("receipt does not reference candidate")
        if receipt.request_ref != candidate.request_ref:
            raise AdvisoryShadowError("receipt request_ref does not match candidate")
        return cls(
            _digest(
                {
                    "candidate_id": candidate.candidate_id,
                    "receipt_id": receipt.receipt_id,
                }
            ),
            candidate,
            receipt,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "result_id": self.result_id,
            "candidate": self.candidate.to_dict(),
            "receipt": self.receipt.to_dict(),
        }


class AdvisoryShadowGate:
    def evaluate(
        self,
        *,
        request: AdvisoryShadowRequest,
        hard_gate_report: ReplayEvaluationReport,
        signals: Iterable[AdvisorySignal],
        state_projections: Iterable[CurrentStateProjection] = (),
        goal_projections: Iterable[GoalProjection] = (),
        open_loop_projections: Iterable[OpenLoopProjection] = (),
    ) -> AdvisoryShadowResult:
        if not isinstance(request, AdvisoryShadowRequest):
            raise AdvisoryShadowError("request must be an AdvisoryShadowRequest")
        if not isinstance(hard_gate_report, ReplayEvaluationReport):
            raise AdvisoryShadowError(
                "hard_gate_report must be a ReplayEvaluationReport"
            )
        signal_map = self._signal_map(signals)
        states = self._state_map(state_projections)
        goals = self._goal_map(goal_projections)
        loops = self._loop_map(open_loop_projections)
        signal_ids = tuple(sorted(signal_map))

        if not hard_gate_report.passed:
            return self._finish(
                request,
                hard_gate_report,
                self._silent(request, AdvisoryAction.DEFER, AdvisoryReason.HARD_GATES_FAILED),
                evaluated=(),
                excluded=signal_ids,
            )
        if request.audience is not AdvisoryAudience.PRIVATE:
            return self._finish(
                request,
                hard_gate_report,
                self._silent(
                    request,
                    AdvisoryAction.SILENCE,
                    AdvisoryReason.NON_PRIVATE_AUDIENCE,
                ),
                evaluated=(),
                excluded=signal_ids,
            )

        ranked = tuple(
            sorted(
                signal_map.values(),
                key=lambda signal: (-self._priority(signal.kind), signal.signal_id),
            )
        )
        for signal in ranked:
            candidate = self._for_signal(request, signal, states, goals, loops)
            if candidate is None:
                continue
            excluded = tuple(
                value.signal_id
                for value in ranked
                if value.signal_id != signal.signal_id
            )
            return self._finish(
                request,
                hard_gate_report,
                candidate,
                evaluated=(signal.signal_id,),
                excluded=excluded,
            )

        return self._finish(
            request,
            hard_gate_report,
            self._silent(
                request,
                AdvisoryAction.SILENCE,
                AdvisoryReason.NO_RELEVANT_SIGNAL,
            ),
            evaluated=(),
            excluded=signal_ids,
        )

    @staticmethod
    def _signal_map(values: Iterable[AdvisorySignal]) -> dict[str, AdvisorySignal]:
        result: dict[str, AdvisorySignal] = {}
        for value in values:
            if not isinstance(value, AdvisorySignal):
                raise AdvisoryShadowError("signals contain an invalid value")
            previous = result.get(value.signal_id)
            if previous is not None and previous != value:
                raise AdvisoryShadowError(f"conflicting signal: {value.signal_id}")
            result[value.signal_id] = value
        return result

    @staticmethod
    def _state_map(
        values: Iterable[CurrentStateProjection],
    ) -> dict[str, CurrentStateProjection]:
        result: dict[str, CurrentStateProjection] = {}
        for value in values:
            if not isinstance(value, CurrentStateProjection):
                raise AdvisoryShadowError("state_projections contain invalid value")
            if value.projection_id in result and result[value.projection_id] != value:
                raise AdvisoryShadowError(
                    f"conflicting state projection: {value.projection_id}"
                )
            result[value.projection_id] = value
        return result

    @staticmethod
    def _goal_map(values: Iterable[GoalProjection]) -> dict[str, GoalProjection]:
        result: dict[str, GoalProjection] = {}
        for value in values:
            if not isinstance(value, GoalProjection):
                raise AdvisoryShadowError("goal_projections contain invalid value")
            if value.projection_id in result and result[value.projection_id] != value:
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
                raise AdvisoryShadowError("open_loop_projections contain invalid value")
            if value.projection_id in result and result[value.projection_id] != value:
                raise AdvisoryShadowError(
                    f"conflicting open-loop projection: {value.projection_id}"
                )
            result[value.projection_id] = value
        return result

    @staticmethod
    def _priority(kind: AdvisorySignalKind) -> int:
        return {
            AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED: 4,
            AdvisorySignalKind.BLOCKER_RELEVANT: 3,
            AdvisorySignalKind.OPEN_LOOP_RELEVANT: 2,
            AdvisorySignalKind.GOAL_RELEVANT: 1,
        }[kind]

    def _for_signal(
        self,
        request: AdvisoryShadowRequest,
        signal: AdvisorySignal,
        states: dict[str, CurrentStateProjection],
        goals: dict[str, GoalProjection],
        loops: dict[str, OpenLoopProjection],
    ) -> AdviceCandidate | None:
        if signal.kind is AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED:
            state = states.get(signal.projection_id)
            if state is None or (
                state.status is not ProjectionStatus.CONTESTED
                and not state.review_required
            ):
                return None
            if not request.allow_confirmation_questions:
                return self._silent(
                    request,
                    AdvisoryAction.SILENCE,
                    AdvisoryReason.CONFIRMATION_NOT_ALLOWED,
                    signal.signal_id,
                )
            basis = {
                state.projection_id,
                *state.candidate_assertion_refs,
                *state.supporting_assertion_refs,
                *state.contradiction_assertion_refs,
            }
            if state.selected_assertion_ref is not None:
                basis.add(state.selected_assertion_ref)
            return AdviceCandidate.create(
                request_ref=request.request_ref,
                action=AdvisoryAction.ASK_CONFIRMATION,
                proposed_text=(
                    "Уточните, пожалуйста: приоритет или текущее состояние "
                    "могли измениться?"
                ),
                basis_refs=basis,
                reason_codes=(
                    AdvisoryReason.SHADOW_ONLY,
                    AdvisoryReason.PRIORITY_CHANGE_UNCONFIRMED,
                    AdvisoryReason.CONTESTED_STATE,
                ),
                source_signal_id=signal.signal_id,
                sensitivity=request.sensitivity,
                risk=AdvisoryRisk.MEDIUM,
            )

        if signal.kind is AdvisorySignalKind.GOAL_RELEVANT:
            goal = goals.get(signal.projection_id)
            if goal is None or goal.status is not GoalStatus.ACTIVE:
                return None
            if not request.allow_reminders:
                return self._silent(
                    request,
                    AdvisoryAction.SILENCE,
                    AdvisoryReason.REMINDER_NOT_ALLOWED,
                    signal.signal_id,
                )
            return AdviceCandidate.create(
                request_ref=request.request_ref,
                action=AdvisoryAction.REMIND,
                proposed_text=f"Напоминание о цели: {goal.title}",
                basis_refs=(goal.projection_id, *goal.source_refs),
                reason_codes=(
                    AdvisoryReason.SHADOW_ONLY,
                    AdvisoryReason.ACTIVE_GOAL_RELEVANT,
                ),
                source_signal_id=signal.signal_id,
                sensitivity=request.sensitivity,
                risk=AdvisoryRisk.LOW,
            )

        loop = loops.get(signal.projection_id)
        if loop is None or loop.status not in {
            OpenLoopStatus.OPEN,
            OpenLoopStatus.OVERDUE,
        }:
            return None
        if (
            signal.kind is AdvisorySignalKind.BLOCKER_RELEVANT
            and loop.kind is not OpenLoopKind.BLOCKER
        ):
            return None
        if not request.allow_reminders:
            return self._silent(
                request,
                AdvisoryAction.SILENCE,
                AdvisoryReason.REMINDER_NOT_ALLOWED,
                signal.signal_id,
            )
        reasons = [AdvisoryReason.SHADOW_ONLY]
        risk = AdvisoryRisk.LOW
        if signal.kind is AdvisorySignalKind.BLOCKER_RELEVANT:
            reasons.append(AdvisoryReason.BLOCKER_RELEVANT)
            risk = AdvisoryRisk.MEDIUM
        else:
            reasons.append(AdvisoryReason.OPEN_LOOP_RELEVANT)
        if loop.status is OpenLoopStatus.OVERDUE:
            reasons.append(AdvisoryReason.OPEN_LOOP_OVERDUE)
            risk = AdvisoryRisk.MEDIUM
        return AdviceCandidate.create(
            request_ref=request.request_ref,
            action=AdvisoryAction.REMIND,
            proposed_text=f"Незакрытый вопрос: {loop.summary}",
            basis_refs=(loop.projection_id, *loop.source_refs),
            reason_codes=reasons,
            source_signal_id=signal.signal_id,
            sensitivity=request.sensitivity,
            risk=risk,
        )

    @staticmethod
    def _silent(
        request: AdvisoryShadowRequest,
        action: AdvisoryAction,
        reason: AdvisoryReason,
        signal_id: str | None = None,
    ) -> AdviceCandidate:
        return AdviceCandidate.create(
            request_ref=request.request_ref,
            action=action,
            proposed_text=None,
            basis_refs=(),
            reason_codes=(AdvisoryReason.SHADOW_ONLY, reason),
            source_signal_id=signal_id,
            sensitivity=request.sensitivity,
            risk=AdvisoryRisk.LOW,
        )

    @staticmethod
    def _finish(
        request: AdvisoryShadowRequest,
        report: ReplayEvaluationReport,
        candidate: AdviceCandidate,
        *,
        evaluated: Iterable[str],
        excluded: Iterable[str],
    ) -> AdvisoryShadowResult:
        receipt = AdvisoryReceipt.create(
            request_ref=request.request_ref,
            evaluation_report_id=report.report_id,
            candidate_id=candidate.candidate_id,
            evaluated_signal_ids=evaluated,
            excluded_signal_ids=excluded,
            hard_gates_passed=report.passed,
        )
        return AdvisoryShadowResult.create(candidate, receipt)


__all__ = [
    "ADVISORY_POLICY_VERSION",
    "ADVISORY_SCHEMA_VERSION",
    "AdviceCandidate",
    "AdvisoryAction",
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
]
