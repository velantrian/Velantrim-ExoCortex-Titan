from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_project_state import ProjectStateError, validate_project_state


STATE_PATH = Path("docs/state/project_state.json")
AUDIT_MERGE = "90e221be2bed8177f4648787d713058df0f29e1f"
AUDIT_IMPLEMENTATION = "9f07db6de8d32683d00bfe4f1673e84493607553"
RESOLVER_MERGE = "dc30817f2c4abb1afcaab2f127e679d5f9b884d7"
LIFECYCLE_MERGE = "064845579c520e7464678cd0c41d9b650368dfa8"
RUNTIME_WIRING_MERGE = "802e833fa251a8831add8a6b802a5ebb57533549"


def _current_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _historical_v4_state() -> dict:
    state = copy.deepcopy(_current_state())
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
            "enabled": False,
            "observed": False,
            "runtime_authority": False,
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


def _state() -> dict:
    return _historical_v4_state()


def _historical_v3_state() -> dict:
    state = copy.deepcopy(_state())
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
                "Durable retention, replay, cleanup and erasure lifecycle for "
                "admission artifacts."
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
    state["repository"]["repository_head_sha_at_verification"] = AUDIT_MERGE
    state["repository"]["implementation_baseline_sha"] = AUDIT_IMPLEMENTATION
    state["repository"]["documentation_checkpoint_sha"] = AUDIT_MERGE
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


def test_repository_project_state_v4_is_valid() -> None:
    report = validate_project_state(_state())

    assert report["ok"] is True
    assert report["schema_version"] == 4
    assert report["continuity"] == "9/12"
    assert report["readiness_percent"] == 75.0
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED"
    assert report["kb_policy"] == "KEEP_VERSIONED_KNOWLEDGE_ASSET"


def test_schema_v4_sha_roles_pin_the_lifecycle_merge() -> None:
    state = _state()
    repository = state["repository"]
    lifecycle = state["continuity_admission_artifact_lifecycle"]

    assert (
        repository["repository_head_sha_at_verification"]
        == repository["implementation_baseline_sha"]
        == repository["documentation_checkpoint_sha"]
        == lifecycle["merge_sha"]
        == LIFECYCLE_MERGE
    )


def test_historical_v3_snapshot_remains_readable() -> None:
    report = validate_project_state(_historical_v3_state())

    assert report["ok"] is True
    assert report["schema_version"] == 3
    assert report["continuity"] == "8/12"
    assert report["readiness_percent"] == 66.7
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED"


def test_historical_v2_snapshot_remains_readable() -> None:
    report = validate_project_state(_historical_v2_state())

    assert report["ok"] is True
    assert report["schema_version"] == 2
    assert report["continuity"] == "7/12"
    assert report["readiness_percent"] == 58.3
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED"


def test_historical_v1_snapshot_remains_readable() -> None:
    report = validate_project_state(_legacy_v1_state())

    assert report["ok"] is True
    assert report["schema_version"] == 1
    assert report["audit_status"] == "LEGACY_OR_UNDECLARED"
    assert report["notion_status"] == "LEGACY_OR_UNDECLARED"


def test_historical_v1_ignores_fields_the_original_validator_ignored() -> None:
    state = _legacy_v1_state()
    state["governance"]["tracking_issue"] = "not validated by v1"
    state["notion"] = "not validated by v1"

    report = validate_project_state(state)

    assert report["ok"] is True
    assert report["schema_version"] == 1


def test_unknown_schema_version_fails_closed() -> None:
    state = copy.deepcopy(_state())
    state["schema_version"] = 6

    with pytest.raises(ProjectStateError, match="schema_version must be one of"): 
        validate_project_state(state)


@pytest.mark.parametrize("schema_version", [5.0, True, "5", [], {}])
def test_non_integer_schema_versions_fail_closed(schema_version: object) -> None:
    state = copy.deepcopy(_state())
    state["schema_version"] = schema_version

    with pytest.raises(ProjectStateError, match="schema_version must be one of"):
        validate_project_state(state)


def test_readiness_arithmetic_fails_closed() -> None:
    state = copy.deepcopy(_state())
    state["continuity"]["readiness_percent"] = 50.0

    with pytest.raises(ProjectStateError, match="readiness_percent"):
        validate_project_state(state)


def test_schema_v4_requires_exact_nine_of_twelve() -> None:
    state = copy.deepcopy(_state())
    state["continuity"].update(
        {
            "completed_capabilities": 8,
            "remaining_capabilities": 4,
            "readiness_percent": 66.7,
            "remaining_percent": 33.3,
        }
    )

    with pytest.raises(ProjectStateError, match="exactly 9/12"):
        validate_project_state(state)


def test_enabled_requires_wiring() -> None:
    state = copy.deepcopy(_state())
    state["continuity"]["enabled"] = True

    with pytest.raises(ProjectStateError, match="enabled while wired=false"):
        validate_project_state(state)


def test_v4_runtime_wiring_and_authority_remain_false() -> None:
    state = copy.deepcopy(_state())
    state["continuity"]["wired"] = True
    state["continuity"]["runtime_authority"] = True

    with pytest.raises(ProjectStateError, match="wired must be False"):
        validate_project_state(state)


def test_kb_preservation_policy_cannot_silently_change() -> None:
    state = copy.deepcopy(_state())
    state["knowledge_base"]["preservation_policy"] = "DELETE_ARTIFACT"

    with pytest.raises(ProjectStateError, match="preservation policy"):
        validate_project_state(state)


def test_sha_roles_require_full_commit_ids() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["repository_head_sha_at_verification"] = "0648455"

    with pytest.raises(ProjectStateError, match="40-character SHA"):
        validate_project_state(state)


def test_repository_head_must_match_documentation_checkpoint() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="must equal documentation_checkpoint_sha"):
        validate_project_state(state)


def test_v4_implementation_baseline_must_match_verified_head() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["implementation_baseline_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="implementation_baseline_sha"):
        validate_project_state(state)


def test_v4_checkpoint_must_match_lifecycle_merge() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["repository_head_sha_at_verification"] = "a" * 40
    state["repository"]["implementation_baseline_sha"] = "a" * 40
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="lifecycle merge SHA"):
        validate_project_state(state)


def test_final_audit_requires_exact_public_pr_in_v4() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_pr"] = 999

    with pytest.raises(ProjectStateError, match="retrospective_audit_pr must be 261"):
        validate_project_state(state)


def test_historical_v2_still_requires_audit_checkpoint_equality() -> None:
    state = _historical_v2_state()
    state["repository"]["repository_head_sha_at_verification"] = "a" * 40
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="audit checkpoint SHAs"):
        validate_project_state(state)


def test_notion_status_uses_canonical_synced_value() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["status"] = "SYNCED_FINAL"

    with pytest.raises(ProjectStateError, match="status must be 'SYNCED'"):
        validate_project_state(state)


def test_notion_audit_merge_remains_immutable() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["audit_merge_sha_recorded"] = "b" * 40

    with pytest.raises(ProjectStateError, match="retrospective_audit_merge_sha"):
        validate_project_state(state)


def test_notion_page_id_cannot_be_substituted() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["latest_status_page_id"] = (
        "00000000-0000-0000-0000-000000000000"
    )

    with pytest.raises(ProjectStateError, match="latest_status_page_id"):
        validate_project_state(state)


def test_latest_notion_merge_must_match_lifecycle_merge() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["latest_implementation_merge_sha"] = "b" * 40

    with pytest.raises(ProjectStateError, match="latest_implementation_merge_sha"):
        validate_project_state(state)


def test_lifecycle_identity_is_exact() -> None:
    state = copy.deepcopy(_state())
    state["continuity_admission_artifact_lifecycle"]["implementation_pr"] = 999

    with pytest.raises(ProjectStateError, match="implementation_pr must be 267"):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "concrete_live_owner_adapters_selected",
        "runtime_wired",
        "enabled",
        "observed",
        "operator_go",
        "producer_side_effects_present",
        "independent_review_claimed",
    ],
)
def test_lifecycle_non_authority_flags_fail_closed(field: str) -> None:
    state = copy.deepcopy(_state())
    state["continuity_admission_artifact_lifecycle"][field] = True

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "persistence_present",
        "deterministic_replay_present",
        "retention_cleanup_present",
        "erasure_addressability_present",
        "integrity_verification_present",
        "crash_safe_transactions_present",
    ],
)
def test_lifecycle_proof_flags_are_required(field: str) -> None:
    state = copy.deepcopy(_state())
    state["continuity_admission_artifact_lifecycle"][field] = False

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


def test_lifecycle_run_evidence_must_be_positive_integer() -> None:
    state = copy.deepcopy(_state())
    state["continuity_admission_artifact_lifecycle"][
        "post_merge_full_ci_run"
    ] = 0

    with pytest.raises(ProjectStateError, match="post_merge_full_ci_run"):
        validate_project_state(state)


def test_resolver_historical_identity_remains_exact_in_v4() -> None:
    state = copy.deepcopy(_state())
    state["continuity_current_decision_resolver"]["implementation_pr"] = 999

    with pytest.raises(ProjectStateError, match="implementation_pr must be 264"):
        validate_project_state(state)


def test_notion_finalization_requires_non_empty_safe_targets() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["safe_targets"] = []

    with pytest.raises(ProjectStateError, match="non-empty string list"):
        validate_project_state(state)



def test_repository_project_state_v5_is_valid() -> None:
    report = validate_project_state(_current_state())

    assert report["ok"] is True
    assert report["schema_version"] == 5
    assert report["continuity"] == "10/12"
    assert report["readiness_percent"] == 83.3
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED"
    assert report["kb_policy"] == "KEEP_VERSIONED_KNOWLEDGE_ASSET"


def test_schema_v5_sha_roles_pin_runtime_wiring_merge() -> None:
    state = _current_state()
    repository = state["repository"]
    composition = state["continuity_bounded_runtime_composition"]

    assert (
        repository["repository_head_sha_at_verification"]
        == repository["implementation_baseline_sha"]
        == repository["documentation_checkpoint_sha"]
        == composition["merge_sha"]
        == RUNTIME_WIRING_MERGE
    )


def test_historical_schema_v4_snapshot_remains_readable() -> None:
    report = validate_project_state(_historical_v4_state())

    assert report["ok"] is True
    assert report["schema_version"] == 4
    assert report["continuity"] == "9/12"
    assert report["readiness_percent"] == 75.0


def test_schema_v5_requires_exact_ten_of_twelve() -> None:
    state = _current_state()
    state["continuity"].update(
        {
  "completed_capabilities": 9,
  "remaining_capabilities": 3,
  "readiness_percent": 75.0,
  "remaining_percent": 25.0,
        }
    )

    with pytest.raises(ProjectStateError, match="exactly 10/12"):
        validate_project_state(state)


@pytest.mark.parametrize("field", ["enabled", "observed", "runtime_authority"])
def test_schema_v5_does_not_conflate_wiring_with_authority(field: str) -> None:
    state = _current_state()
    state["continuity"][field] = True

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
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
        "independent_review_claimed",
    ],
)
def test_schema_v5_runtime_composition_non_authority_flags_fail_closed(
    field: str,
) -> None:
    state = _current_state()
    state["continuity_bounded_runtime_composition"][field] = True

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


def test_schema_v5_runtime_composition_owner_is_exact() -> None:
    state = _current_state()
    state["continuity_bounded_runtime_composition"]["lifecycle_owner_id"] = (
        "continuity.substituted"
    )

    with pytest.raises(ProjectStateError, match="lifecycle_owner_id"):
        validate_project_state(state)


def test_schema_v5_runtime_composition_evidence_is_positive() -> None:
    state = _current_state()
    state["continuity_bounded_runtime_composition"]["post_merge_full_ci_run"] = 0

    with pytest.raises(ProjectStateError, match="post_merge_full_ci_run"):
        validate_project_state(state)
