from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_project_state import ProjectStateError, validate_project_state


STATE_PATH = Path("docs/state/project_state.json")
AUDIT_MERGE = "90e221be2bed8177f4648787d713058df0f29e1f"
AUDIT_IMPLEMENTATION = "9f07db6de8d32683d00bfe4f1673e84493607553"


def _state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _historical_v2_state() -> dict:
    state = copy.deepcopy(_state())
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


def test_repository_project_state_v3_is_valid() -> None:
    report = validate_project_state(_state())

    assert report["ok"] is True
    assert report["schema_version"] == 3
    assert report["continuity"] == "8/12"
    assert report["readiness_percent"] == 66.7
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED"
    assert report["kb_policy"] == "KEEP_VERSIONED_KNOWLEDGE_ASSET"


def test_schema_v3_sha_roles_pin_the_resolver_merge() -> None:
    state = _state()
    repository = state["repository"]
    resolver = state["continuity_current_decision_resolver"]

    assert (
        repository["repository_head_sha_at_verification"]
        == repository["implementation_baseline_sha"]
        == repository["documentation_checkpoint_sha"]
        == resolver["merge_sha"]
    )


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
    state["schema_version"] = 4

    with pytest.raises(ProjectStateError, match="schema_version must be one of"):
        validate_project_state(state)


@pytest.mark.parametrize("schema_version", [3.0, True, "3", [], {}])
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


def test_schema_v3_requires_exact_eight_of_twelve() -> None:
    state = copy.deepcopy(_state())
    state["continuity"].update(
        {
            "completed_capabilities": 9,
            "remaining_capabilities": 3,
            "readiness_percent": 75.0,
            "remaining_percent": 25.0,
        }
    )

    with pytest.raises(ProjectStateError, match="exactly 8/12"):
        validate_project_state(state)


def test_enabled_requires_wiring() -> None:
    state = copy.deepcopy(_state())
    state["continuity"]["enabled"] = True

    with pytest.raises(ProjectStateError, match="enabled while wired=false"):
        validate_project_state(state)


def test_v3_runtime_wiring_and_authority_remain_false() -> None:
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
    state["repository"]["repository_head_sha_at_verification"] = "dc30817"

    with pytest.raises(ProjectStateError, match="40-character SHA"):
        validate_project_state(state)


def test_repository_head_must_match_documentation_checkpoint() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="must equal documentation_checkpoint_sha"):
        validate_project_state(state)


def test_v3_implementation_baseline_must_match_verified_head() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["implementation_baseline_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="implementation_baseline_sha"):
        validate_project_state(state)


def test_final_audit_requires_exact_public_pr_in_v3() -> None:
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


def test_latest_notion_merge_must_match_resolver_merge() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["latest_implementation_merge_sha"] = "b" * 40

    with pytest.raises(ProjectStateError, match="latest_implementation_merge_sha"):
        validate_project_state(state)


def test_resolver_identity_is_exact() -> None:
    state = copy.deepcopy(_state())
    state["continuity_current_decision_resolver"]["implementation_pr"] = 999

    with pytest.raises(ProjectStateError, match="implementation_pr must be 264"):
        validate_project_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "concrete_live_owner_adapters_selected",
        "persistence_present",
        "runtime_wired",
        "operator_go",
        "independent_review_claimed",
    ],
)
def test_resolver_non_authority_flags_fail_closed(field: str) -> None:
    state = copy.deepcopy(_state())
    state["continuity_current_decision_resolver"][field] = True

    with pytest.raises(ProjectStateError, match=field):
        validate_project_state(state)


def test_notion_finalization_requires_non_empty_safe_targets() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["safe_targets"] = []

    with pytest.raises(ProjectStateError, match="non-empty string list"):
        validate_project_state(state)
