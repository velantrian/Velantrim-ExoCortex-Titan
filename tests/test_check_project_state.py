from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_project_state import ProjectStateError, validate_project_state


STATE_PATH = Path("docs/state/project_state.json")


def _state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


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


def test_repository_project_state_is_valid() -> None:
    report = validate_project_state(_state())

    assert report["ok"] is True
    assert report["continuity"] == "7/12"
    assert report["readiness_percent"] == 58.3
    assert report["audit_status"] == "COMPLETE"
    assert report["notion_status"] == "SYNCED_FINAL"
    assert report["kb_policy"] == "KEEP_VERSIONED_KNOWLEDGE_ASSET"


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


def test_final_audit_requires_public_pr_number() -> None:
    state = copy.deepcopy(_state())
    del state["governance"]["retrospective_audit_pr"]

    with pytest.raises(ProjectStateError, match="retrospective_audit_pr"):
        validate_project_state(state)


def test_final_audit_requires_full_merge_sha() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_merge_sha"] = "90e221b"

    with pytest.raises(ProjectStateError, match="40-character SHA"):
        validate_project_state(state)


def test_final_audit_rejects_non_final_status() -> None:
    state = copy.deepcopy(_state())
    state["governance"]["retrospective_audit_status"] = "PENDING"

    with pytest.raises(ProjectStateError, match="retrospective_audit_status"):
        validate_project_state(state)


def test_audit_merge_must_match_repository_checkpoint() -> None:
    state = copy.deepcopy(_state())
    state["repository"]["documentation_checkpoint_sha"] = "a" * 40

    with pytest.raises(ProjectStateError, match="audit checkpoint SHAs"):
        validate_project_state(state)


def test_notion_merge_must_match_audit_merge() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["audit_merge_sha_recorded"] = "b" * 40

    with pytest.raises(ProjectStateError, match="must equal retrospective_audit_merge_sha"):
        validate_project_state(state)


def test_notion_finalization_requires_valid_page_id() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["audit_page_id"] = "not-a-page-id"

    with pytest.raises(ProjectStateError, match="lowercase dashed UUID"):
        validate_project_state(state)


def test_notion_audit_target_must_be_allowlisted() -> None:
    state = copy.deepcopy(_state())
    state["notion"]["safe_targets"].remove("Velantrim Titan 9.0")

    with pytest.raises(ProjectStateError, match="included in safe_targets"):
        validate_project_state(state)
