from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_project_state import ProjectStateError, validate_project_state


STATE_PATH = Path("docs/state/project_state.json")


def _state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def test_repository_project_state_is_valid() -> None:
    report = validate_project_state(_state())

    assert report["ok"] is True
    assert report["continuity"] == "5/12"
    assert report["readiness_percent"] == 41.7
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
    state["repository"]["repository_head_sha_at_verification"] = "9dfbfe5"

    with pytest.raises(ProjectStateError, match="40-character SHA"):
        validate_project_state(state)
