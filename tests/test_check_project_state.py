from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_project_state import ProjectStateError, validate_project_state


STATE_PATH = Path("docs/state/project_state.json")


def _state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _legacy_v1_state() -> dict:
    """Build the minimal shape accepted by the validator before schema v2."""

    state = copy.deepcopy(_state())
    state["schema_version"] = 1
    state["governance"] = {
        "aggregate_merge_evidence_present": True,
        "codeowners_present": True,
        "branch_ruleset_enforced": True,
    }
    state.pop("notion", None)
    return state


def test_sha_roles_are_distinct_when_docs_checkpoint_is_newer() -> None:
    state = _state()
    repository = state["repository"]
    assert (
        repository["repository_head_sha_at_verification"]
        == repository["documentation_checkpoint_sha"]
    )
    assert (
        repository["implementation_baseline_sha"]
        != repository["repository_head_sha_at_verification"]
    )


def test_repository_project_state_v2_is_valid() -> None:
    report = validate_project_state(_state())

    assert report["ok"] is True
    assert report["schema_version"] == 2
    assert report["continuity"] == "7/12"
    assert report["readiness_percent"] == 58.3
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED"
    assert report["kb_policy"] == "KEEP_VERSIONED_KNOWLEDGE_ASSET"


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
    state["schema_version"] = 3

    with pytest.raises(ProjectStateError, match="schema_version must be one of"):
        validate_project_state(state)


@pytest.mark.parametrize("schema_version", [2.0, True, "2", [], {}])
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


def test_enabled_requires_wiring() -> None:
    state = copy.deepcopy(_state())
    state["continuity"]["enabled"] = True

    with pytest.raises(ProjectStateError, match="enabled while wired=false"):
        validate_project_state(state)


def test_kb_preservation_policy_cannot_silently_change() -> None:
    state = copy.deepcopy(_state())
    state["knowledge_base"]["preservation_policy"] = "DELETE_ARTIFACT"

    with pytest.raises(ProjectStateError, match="preservation policy"):
        validate_project_state(state)


def test_sha_roles_require_full_commit_ids() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["repository_head_sha_at_verification"] = "9f07db6"

    with pytest.raises(ProjectStateError, match="40-character SHA"):
        validate_project_state(state)


def test_repository_head_must_match_documentation_checkpoint() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="must equal documentation_checkpoint_sha"):
        validate_project_state(state)


def test_final_audit_requires_exact_public_pr() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_pr"] = 999

    with pytest.raises(ProjectStateError, match="retrospective_audit_pr must be 261"):
        validate_project_state(state)


def test_final_audit_requires_exact_head_sha() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_head_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="retrospective_audit_head_sha"):
        validate_project_state(state)


def test_final_audit_requires_exact_merge_sha() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_merge_sha"] = "b" * 40

    with pytest.raises(ProjectStateError, match="retrospective_audit_merge_sha"):
        validate_project_state(state)


def test_final_audit_rejects_non_final_status() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_status"] = "PENDING"

    with pytest.raises(ProjectStateError, match="retrospective_audit_status"):
        validate_project_state(state)


def test_repository_checkpoint_must_match_audit_merge() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["repository_head_sha_at_verification"] = "a" * 40
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="audit checkpoint SHAs"):
        validate_project_state(state)


def test_notion_status_uses_canonical_synced_value() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["status"] = "SYNCED_FINAL"

    with pytest.raises(ProjectStateError, match="status must be 'SYNCED'"):
        validate_project_state(state)


def test_notion_finalization_marker_must_be_true() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["audit_synchronization_finalized"] = False

    with pytest.raises(ProjectStateError, match="must be true"):
        validate_project_state(state)


def test_notion_merge_must_match_audit_merge() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["audit_merge_sha_recorded"] = "b" * 40

    with pytest.raises(ProjectStateError, match="must equal retrospective_audit_merge_sha"):
        validate_project_state(state)


def test_notion_page_id_cannot_be_substituted() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["audit_page_id"] = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(ProjectStateError, match="audit_page_id"):
        validate_project_state(state)


def test_notion_finalization_requires_non_empty_safe_targets() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["safe_targets"] = []

    with pytest.raises(ProjectStateError, match="non-empty string list"):
        validate_project_state(state)


def test_notion_audit_target_must_be_allowlisted() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["safe_targets"].remove("Velantrim Titan 9.0")

    with pytest.raises(ProjectStateError, match="included in safe_targets"):
        validate_project_state(state)
