"""End-to-end tests for the disabled-by-default R5B shadow runner."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

from core.compute_controller import (
    ComputePath,
    ContextFreshness,
    ContinuityComputeSignals,
)
from core.context_pack import ContextPackBudget
from core.continuity.advisory_shadow import (
    AdvisoryAction,
    AdvisoryAudience,
    AdvisoryShadowRequest,
    AdvisorySignalKind,
)
from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.conversation_bridge import ConversationEpisode
from core.continuity.evaluation import ShadowSafetyObservation
from core.continuity.goal_open_loop import (
    GoalAttestation,
    GoalBasis,
    GoalRecordSnapshot,
    OpenLoopKind,
    OpenLoopSignal,
)
from core.continuity.shadow_runner import (
    AdvisoryIntent,
    CompleteShadowRunInput,
    CompleteShadowRunner,
    CompleteShadowRunnerError,
    ShadowRunnerConfig,
    ShadowRunnerReason,
    ShadowRunnerStatus,
)
from core.continuity.thread_weaver import ThreadWeaver
from core.conversation_consolidation import ConversationNotebook
from core.goal_stack import Goal
from core.working_memory_gate import WorkingMemoryBudget

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
USER = ActorRef("actor:user", ActorKind.HUMAN)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)


def _episode(
    chat_id: str,
    *,
    goal: str,
    created_at: str,
    related: list[str] | None = None,
) -> ConversationEpisode:
    return ConversationEpisode.from_notebook(
        ConversationNotebook(
            chat_id=chat_id,
            main_topic="Titan continuity",
            user_goal=goal,
            key_insights=["Preserve provenance"],
            conclusion="Keep the milestone deterministic",
            related_chats=related or [],
            facts_count=2,
            messages_count=5,
            produced_gist=True,
            created_at=created_at,
            finalized_at=created_at,
        )
    )


def _assertion(value: str, *, source: str, hour: int) -> AssertionRecord:
    timestamp = datetime(2026, 8, 5, hour, 0, tzinfo=UTC)
    return AssertionRecord.create(
        subject_ref=PROJECT,
        predicate="priority",
        value=value,
        origin_type=OriginType.USER_STATED,
        source_refs=(source,),
        asserted_by=USER,
        valid_from=timestamp,
        recorded_at=timestamp,
    )


def _input(
    *,
    audience: AdvisoryAudience = AdvisoryAudience.PRIVATE,
    observation: ShadowSafetyObservation | None = None,
    advisory_target: str | None = None,
) -> CompleteShadowRunInput:
    older = _episode(
        "chat:older",
        goal="Finish the MVP first",
        created_at="2026-08-04T10:00:00+00:00",
    )
    current = _episode(
        "chat:current",
        goal="Add another architecture layer",
        created_at="2026-08-05T10:00:00+00:00",
        related=["chat:older"],
    )
    finish_mvp = _assertion(
        "finish-mvp",
        source="conversation:priority-old",
        hour=9,
    )
    add_layer = _assertion(
        "add-layer",
        source="conversation:priority-new",
        hour=10,
    )
    goal_snapshot = GoalRecordSnapshot.from_goal(
        Goal(
            goal_id="goal:mvp",
            user_id="user:owner",
            title="Finish the MVP",
            description="Complete the milestone before adding layers",
            status="active",
            priority=10,
            keywords=["mvp", "titan"],
            created_at="2026-08-04T09:00:00+00:00",
            updated_at="2026-08-05T10:00:00+00:00",
        )
    )
    goal_attestation = GoalAttestation.create(
        user_id=goal_snapshot.user_id,
        goal_ref=goal_snapshot.goal_ref,
        basis=GoalBasis.ACCEPTED_DECISION,
        source_refs=("conversation:goal-decision",),
        confirmed_at=datetime(2026, 8, 5, 10, 0, tzinfo=UTC),
    )
    loop_signal = OpenLoopSignal.create(
        loop_key="loop:new-layer",
        kind=OpenLoopKind.DEFERRED_DECISION,
        summary="Decide whether to add another architecture layer",
        source_refs=("conversation:open-loop",),
        opened_at=datetime(2026, 8, 4, 10, 0, tzinfo=UTC),
        related_goal_ref=goal_snapshot.goal_ref,
    )
    request_ref = "request:complete-shadow"
    return CompleteShadowRunInput(
        request_ref=request_ref,
        query="Explain the current Titan priority",
        current_episode=current,
        episodes=(older, current),
        as_of=NOW,
        advisory_request=AdvisoryShadowRequest(
            request_ref=request_ref,
            audience=audience,
        ),
        state_assertions=(finish_mvp, add_layer),
        goal_snapshots=(goal_snapshot,),
        goal_attestations=(goal_attestation,),
        open_loop_signals=(loop_signal,),
        advisory_intents=(
            AdvisoryIntent(
                AdvisorySignalKind.GOAL_RELEVANT,
                advisory_target or goal_snapshot.goal_ref,
            ),
        ),
        working_memory_budget=WorkingMemoryBudget(
            max_items=20,
            max_chars=20_000,
        ),
        context_pack_budget=ContextPackBudget(max_tokens=100_000),
        compute_signals=ContinuityComputeSignals(
            context_freshness=ContextFreshness.FRESH,
            evidence_coverage=1.0,
            active_contradictions=1,
            continuity_available=True,
            important_claim=True,
            requires_current_state=True,
        ),
        observation=observation or ShadowSafetyObservation(),
    )


def _enabled_config() -> ShadowRunnerConfig:
    return ShadowRunnerConfig(
        enabled=True,
        scenario_id="continuity-r5b-complete-shadow",
    )


def test_disabled_runner_returns_before_pipeline_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("pipeline must not run while disabled")

    monkeypatch.setattr(ThreadWeaver, "weave", fail_if_called)

    result = CompleteShadowRunner().run()

    assert result.status is ShadowRunnerStatus.DISABLED
    assert result.baseline is None
    assert result.replay is None
    assert result.evaluation is None
    assert result.advisory is None
    assert ShadowRunnerReason.FEATURE_DISABLED in result.receipt.reason_codes
    assert ShadowRunnerReason.NO_RUNTIME_AUTHORITY in result.receipt.reason_codes


def test_complete_pipeline_replays_and_emits_shadow_reminder() -> None:
    result = CompleteShadowRunner().run(_enabled_config(), _input())

    assert result.status is ShadowRunnerStatus.COMPLETED
    assert result.baseline is not None
    assert result.replay is not None
    assert result.evaluation is not None
    assert result.advisory is not None
    assert result.baseline.snapshot.snapshot_id == result.replay.snapshot.snapshot_id
    assert result.evaluation.replay_equal is True
    assert result.evaluation.passed is True
    assert result.baseline.compute_assessment.changed_legacy_decision is True
    assert result.baseline.compute_decision.path is ComputePath.VERIFY_PATH
    assert result.advisory.candidate.action is AdvisoryAction.REMIND
    assert result.advisory.candidate.shadow_only is True
    assert ShadowRunnerReason.MAIN_ANSWER_UNTOUCHED in result.receipt.reason_codes
    assert ShadowRunnerReason.CANON_UNCHANGED in result.receipt.reason_codes
    assert ShadowRunnerReason.NO_RUNTIME_AUTHORITY in result.receipt.reason_codes


def test_hard_gate_failure_defers_advisory_without_text() -> None:
    result = CompleteShadowRunner().run(
        _enabled_config(),
        _input(observation=ShadowSafetyObservation(privacy_leakage=1)),
    )

    assert result.evaluation is not None
    assert result.advisory is not None
    assert result.evaluation.passed is False
    assert result.advisory.candidate.action is AdvisoryAction.DEFER
    assert result.advisory.candidate.proposed_text is None


def test_shared_audience_silences_personal_continuity() -> None:
    result = CompleteShadowRunner().run(
        _enabled_config(),
        _input(audience=AdvisoryAudience.SHARED),
    )

    assert result.advisory is not None
    assert result.advisory.candidate.action is AdvisoryAction.SILENCE
    assert result.advisory.candidate.proposed_text is None


def test_unknown_advisory_target_fails_closed() -> None:
    with pytest.raises(
        CompleteShadowRunnerError,
        match="exactly one projection",
    ):
        CompleteShadowRunner().run(
            _enabled_config(),
            _input(advisory_target="goal:unknown"),
        )


def test_external_input_order_does_not_change_result_identity() -> None:
    inputs = _input()
    reordered = replace(
        inputs,
        episodes=tuple(reversed(inputs.episodes)),
        state_assertions=tuple(reversed(inputs.state_assertions)),
    )

    first = CompleteShadowRunner().run(_enabled_config(), inputs)
    second = CompleteShadowRunner().run(_enabled_config(), reordered)

    assert first.result_id == second.result_id
    assert first.receipt.receipt_id == second.receipt.receipt_id


def test_disabled_result_is_deterministic() -> None:
    first = CompleteShadowRunner().run()
    second = CompleteShadowRunner().run()

    assert first == second
    assert first.result_id == second.result_id
    assert first.receipt.receipt_id == second.receipt.receipt_id


def test_enabled_runner_requires_typed_input() -> None:
    with pytest.raises(
        CompleteShadowRunnerError,
        match="requires CompleteShadowRunInput",
    ):
        CompleteShadowRunner().run(_enabled_config())


def test_advisory_request_must_match_runner_request() -> None:
    inputs = _input()
    with pytest.raises(
        CompleteShadowRunnerError,
        match="must match request_ref",
    ):
        replace(
            inputs,
            advisory_request=AdvisoryShadowRequest(
                request_ref="request:other",
                audience=AdvisoryAudience.PRIVATE,
            ),
        )


def test_config_rejects_ambiguous_enable_values() -> None:
    with pytest.raises(CompleteShadowRunnerError, match="enabled"):
        ShadowRunnerConfig(enabled=1)  # type: ignore[arg-type]


def test_result_is_immutable_and_has_no_runtime_authority() -> None:
    result = CompleteShadowRunner().run(_enabled_config(), _input())

    with pytest.raises(FrozenInstanceError):
        result.status = ShadowRunnerStatus.DISABLED  # type: ignore[misc]

    for value in (CompleteShadowRunner(), result, result.receipt):
        for forbidden in (
            "answer",
            "send",
            "persist",
            "canon_write",
            "execute",
            "apply",
            "tool_call",
            "start",
            "schedule",
            "register",
        ):
            assert not hasattr(value, forbidden)
