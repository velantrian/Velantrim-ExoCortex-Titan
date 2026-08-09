from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_project_state import ProjectStateError, validate_project_state


STATE_PATH = Path("docs/state/project_state.json")
AUDIT_MERGE = "90e221be2bed8177f4648787d713058df0f29e1f"
RESOLVER_MERGE = "dc30817f2c4abb1afcaab2f127e679d5f9b884d7"
LIFECYCLE_MERGE = "064845579c520e7464678cd0c41d9b650368dfa8"
RUNTIME_WIRING_MERGE = "802e833fa251a8831add8a6b802a5ebb57533549"
CONTROLLED_ENABLEMENT_MERGE = "66318e6883590cb29a4565157e0a3a25b3716d81"


def _current_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _historical_v5_state() -> dict:
    state = copy.deepcopy(_current_state())
    state["schema_version"] = 5
    repository = state["repository"]
    repository["repository_head_sha_at_verification"] = RUNTIME_WIRING_MERGE
    repository["implementation_baseline_sha"] = RUNTIME_WIRING_MERGE
    repository["documentation_checkpoint_sha"] = RUNTIME_WIRING_MERGE
    state["continuity"] = {
        "completed_capabilities": 10,
        "total_capabilities": 12,
        "readiness_percent": 83.3,
        "remaining_capabilities": 2,
        "remaining_percent": 16.7,
        "implemented": True,
        "tested": True,
        "wired": True,
        "enabled": False,
        "observed": False,
        "runtime_authority": False,
        "next_bounded_slice": (
            "Controlled enablement remains the next unresolved capability."
        ),
    }
    state.pop("continuity_controlled_enablement", None)
    notion = state["notion"]
    notion["latest_synchronization_kind"] = (
        "CONTINUITY_BOUNDED_RUNTIME_COMPOSITION"
    )
    notion["latest_implementation_merge_sha"] = RUNTIME_WIRING_MERGE
    return state


def _historical_v4_state() -> dict:
    state = _historical_v5_state()
    state["schema_version"] = 4
    repository = state["repository"]
    repository["repository_head_sha_at_verification"] = LIFECYCLE_MERGE
    repository["implementation_baseline_sha"] = LIFECYCLE_MERGE
    repository["documentation_checkpoint_sha"] = LIFECYCLE_MERGE
    state["continuity"].update(
        {
            "completed_capabilities": 9,
            "readiness_percent": 75.0,
            "remaining_capabilities": 3,
            "remaining_percent": 25.0,
            "wired": False,
            "next_bounded_slice": (
                "Runtime wiring with one explicitly selected lifecycle owner."
            ),
        }
    )
    state.pop("continuity_bounded_runtime_composition", None)
    notion = state["notion"]
    notion["latest_synchronization_kind"] = (
        "CONTINUITY_ADMISSION_ARTIFACT_LIFECYCLE"
    )
    notion["latest_implementation_merge_sha"] = LIFECYCLE_MERGE
    return state


def _historical_v3_state() -> dict:
    state = _historical_v4_state()
    state["schema_version"] = 3
    repository = state["repository"]
    repository["repository_head_sha_at_verification"] = RESOLVER_MERGE
    repository["implementation_baseline_sha"] = RESOLVER_MERGE
    repository["documentation_checkpoint_sha"] = RESOLVER_MERGE
    state["continuity"].update(
        {
            "completed_capabilities": 8,
            "readiness_percent": 66.7,
            "remaining_capabilities": 4,
            "remaining_percent": 33.3,
            "next_bounded_slice": (
                "Durable retention, replay, cleanup and erasure lifecycle."
            ),
        }
    )
    state.pop("continuity_admission_artifact_lifecycle", None)
    notion = state["notion"]
    notion["latest_synchronization_kind"] = (
        "CONTINUITY_CURRENT_DECISION_RESOLVER"
    )
    notion["latest_implementation_merge_sha"] = RESOLVER_MERGE
    return state


def _historical_v2_state() -> dict:
    state = _historical_v3_state()
    state["schema_version"] = 2
    repository = state["repository"]
    repository["repository_head_sha_at_verification"] = AUDIT_MERGE
    repository["implementation_baseline_sha"] = "9f07db6de8d32683d00bfe4f1673e84493607553"
    repository["documentation_checkpoint_sha"] = AUDIT_MERGE
    state["continuity"].update(
        {
            "completed_capabilities": 7,
            "readiness_percent": 58.3,
            "remaining_capabilities": 5,
            "remaining_percent": 41.7,
        }
    )
    state.pop("continuity_current_decision_resolver", None)
    notion = state["notion"]
    for field in (
        "latest_status_target",
        "latest_status_page_id",
        "latest_synchronization_kind",
        "latest_implementation_merge_sha",
        "latest_synchronization_finalized",
    ):
        notion.pop(field, None)
    return state


def _legacy_v1_state() -> dict:
    state = _historical_v2_state()
    state["schema_version"] = 1
    state["governance"] = {
        "aggregate_merge_evidence_present": True,
        "codeowners_present": True,
        "branch_ruleset_enforced": True,
    }
    state.pop("notion", None)
    return state


@pytest.mark.parametrize(
    ("factory", "schema", "continuity", "readiness"),
    [
        (_legacy_v1_state, 1, "7/12", 58.3),
        (_historical_v2_state, 2, "7/12", 58.3),
        (_historical_v3_state, 3, "8/12", 66.7),
        (_historical_v4_state, 4, "9/12", 75.0),
        (_historical_v5_state, 5, "10/12", 83.3),
        (_current_state, 6, "11/12", 91.7),
    ],
)
def test_all_historical_and_current_schemas_remain_readable(
    factory,
    schema: int,
    continuity: str,
    readiness: float,
) -> None:
    report = validate_project_state(factory())

    assert report["ok"] is True
    assert report["schema_version"] == schema
    assert report["continuity"] == continuity
    assert report["readiness_percent"] == readiness
    assert report["kb_policy"] == "KEEP_VERSIONED_KNOWLEDGE_ASSET"


def test_schema_v6_sha_roles_pin_controlled_enablement_merge() -> None:
    state = _current_state()
    repository = state["repository"]
    enablement = state["continuity_controlled_enablement"]

    assert (
        repository["repository_head_sha_at_verification"]
        == repository["implementation_baseline_sha"]
        == repository["documentation_checkpoint_sha"]
        == enablement["merge_sha"]
        == CONTROLLED_ENABLEMENT_MERGE
    )


@pytest.mark.parametrize("schema_version", [7, 6.0, True, "6", [], {}])
def test_unknown_or_non_integer_schema_versions_fail_closed(
    schema_version: object,
) -> None:
    state = _current_state()
    state["schema_version"] = schema_version

    with pytest.raises(ProjectStateError, match="schema_version must be one of"):
        validate_project_state(state)


def test_schema_v6_requires_exact_eleven_of_twelve() -> None:
    state = _current_state()
    state["continuity"].update(
        {
            "completed_capabilities": 10,
            "remaining_capabilities": 2,
            "readiness_percent": 83.3,
            "remaining_percent": 16.7,
        }
    )

    with pytest.raises(ProjectStateError, match="exactly 11/12"):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "enabled",
        "operator_authorization_present",
        "operator_go",
        "observed",
        "runtime_authority",
        "user_visible_behavior_changed",
        "side_effects_enabled",
    ],
)
def test_schema_v6_does_not_conflate_mechanism_with_runtime_authority(
    field: str,
) -> None:
    state = _current_state()
    state["continuity"][field] = True

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


def test_schema_v6_requires_enablement_mechanism() -> None:
    state = _current_state()
    state["continuity"]["enablement_mechanism_implemented"] = False

    with pytest.raises(
        ProjectStateError,
        match="enablement_mechanism_implemented",
    ):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "persisted_evidence_is_permission",
        "runtime_currently_enabled",
        "operator_authorization_present",
        "operator_go",
        "observed",
        "runtime_authority",
        "caller_selected_database_path",
        "caller_selected_owner",
        "caller_selected_tenant",
        "producer_side_effects_present",
        "canon_writes_present",
        "esm_writes_present",
        "truth_gate_writes_present",
        "goal_stack_writes_present",
        "reminder_created",
        "notification_created",
        "action_created",
        "tool_call_created",
        "scheduler_enabled",
        "independent_review_claimed",
    ],
)
def test_controlled_enablement_non_authority_flags_fail_closed(field: str) -> None:
    state = _current_state()
    state["continuity_controlled_enablement"][field] = True

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "same_database_activation_evidence",
        "enablement_mechanism_implemented",
    ],
)
def test_controlled_enablement_proof_flags_are_required(field: str) -> None:
    state = _current_state()
    state["continuity_controlled_enablement"][field] = False

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


def test_controlled_enablement_identity_is_exact() -> None:
    state = _current_state()
    state["continuity_controlled_enablement"]["implementation_pr"] = 999

    with pytest.raises(ProjectStateError, match="implementation_pr"):
        validate_project_state(state)


def test_controlled_enablement_run_evidence_must_be_positive() -> None:
    state = _current_state()
    state["continuity_controlled_enablement"]["post_merge_full_ci_run"] = 0

    with pytest.raises(ProjectStateError, match="post_merge_full_ci_run"):
        validate_project_state(state)


def test_notion_target_and_kind_cannot_be_substituted() -> None:
    state = _current_state()
    state["notion"]["latest_status_page_id"] = (
        "00000000-0000-0000-0000-000000000000"
    )

    with pytest.raises(ProjectStateError, match="latest_status_page_id"):
        validate_project_state(state)

    state = _current_state()
    state["notion"]["latest_synchronization_kind"] = "PRODUCTION_OBSERVED"

    with pytest.raises(ProjectStateError, match="latest_synchronization_kind"):
        validate_project_state(state)


def test_historical_v5_does_not_acquire_controlled_enablement() -> None:
    state = _historical_v5_state()
    state["continuity"]["enablement_mechanism_implemented"] = True
    state["continuity_controlled_enablement"] = copy.deepcopy(
        _current_state()["continuity_controlled_enablement"]
    )

    with pytest.raises(
        ProjectStateError,
        match="schema v5 must remain Continuity 10/12",
    ):
        validate_project_state(state)


def test_readiness_arithmetic_fails_closed() -> None:
    state = _current_state()
    state["continuity"]["readiness_percent"] = 90.0

    with pytest.raises(ProjectStateError, match="readiness_percent"):
        validate_project_state(state)


def test_sha_roles_require_full_commit_ids() -> None:
    state = _current_state()
    state["repository"]["repository_head_sha_at_verification"] = "66318e6"

    with pytest.raises(ProjectStateError, match="40-character SHA"):
        validate_project_state(state)
