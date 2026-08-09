from __future__ import annotations

from pathlib import Path

from scripts.check_pr_merge_evidence import (
    ARM03_WORKFLOW,
    CI_WORKFLOW,
    CONTINUITY_WORKFLOW,
    DOCKER_WORKFLOW,
    ActorIdentity,
    classify_required_workflows,
    evaluate_documentation_metadata,
    evaluate_required_runs,
    is_trusted_dependabot,
    resolve_documentation_impact,
    _is_dependabot_inferred_none_path,
)

HANDOFF_PATH = Path("docs/operations/branch-ruleset-admin-handoff.md")


def _run(
    name: str,
    *,
    status: str = "completed",
    conclusion: str | None = "success",
    run_number: int = 1,
    run_attempt: int = 1,
    run_id: int = 1,
) -> dict[str, object]:
    return {
        "id": run_id,
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "run_number": run_number,
        "run_attempt": run_attempt,
        "created_at": f"2026-08-07T00:00:{run_id:02d}Z",
    }


def test_docs_only_change_requires_only_primary_ci() -> None:
    required = classify_required_workflows(("docs/ai/CURRENT_STATE.md",))

    assert required == {
        CI_WORKFLOW: True,
        CONTINUITY_WORKFLOW: False,
        DOCKER_WORKFLOW: False,
        ARM03_WORKFLOW: False,
    }


def test_continuity_change_requires_continuity_and_docker() -> None:
    required = classify_required_workflows(
        ("core/continuity/goal_source_adapter.py",)
    )

    assert required[CI_WORKFLOW] is True
    assert required[CONTINUITY_WORKFLOW] is True
    assert required[DOCKER_WORKFLOW] is True
    assert required[ARM03_WORKFLOW] is False


def test_arm_change_requires_arm_and_docker() -> None:
    required = classify_required_workflows(
        ("core/selective_memory_candidates.py",)
    )

    assert required[CI_WORKFLOW] is True
    assert required[CONTINUITY_WORKFLOW] is False
    assert required[DOCKER_WORKFLOW] is True
    assert required[ARM03_WORKFLOW] is True


def test_missing_applicable_workflow_is_pending() -> None:
    required = {
        CI_WORKFLOW: True,
        CONTINUITY_WORKFLOW: True,
        DOCKER_WORKFLOW: False,
        ARM03_WORKFLOW: False,
    }

    evaluation = evaluate_required_runs(required, (_run(CI_WORKFLOW),))

    assert evaluation.state == "pending"
    assert "Continuity contracts: missing" in evaluation.description


def test_cancelled_applicable_workflow_fails_closed() -> None:
    required = {
        CI_WORKFLOW: True,
        CONTINUITY_WORKFLOW: True,
        DOCKER_WORKFLOW: False,
        ARM03_WORKFLOW: False,
    }

    evaluation = evaluate_required_runs(
        required,
        (
            _run(CI_WORKFLOW),
            _run(CONTINUITY_WORKFLOW, conclusion="cancelled", run_id=2),
        ),
    )

    assert evaluation.state == "failure"
    assert "Continuity contracts: cancelled" in evaluation.description


def test_latest_rerun_replaces_older_failure() -> None:
    required = {
        CI_WORKFLOW: True,
        CONTINUITY_WORKFLOW: False,
        DOCKER_WORKFLOW: False,
        ARM03_WORKFLOW: False,
    }

    evaluation = evaluate_required_runs(
        required,
        (
            _run(CI_WORKFLOW, conclusion="failure", run_number=10, run_id=1),
            _run(
                CI_WORKFLOW,
                conclusion="success",
                run_number=10,
                run_attempt=2,
                run_id=2,
            ),
        ),
    )

    assert evaluation.state == "success"


def test_documentation_impact_is_mandatory() -> None:
    evaluation = evaluate_documentation_metadata("No classification")

    assert evaluation.state == "failure"


def test_duplicate_documentation_impact_is_rejected() -> None:
    body = """
Documentation impact: NONE
Documentation impact: GITHUB_AND_NOTION
Notion access: AVAILABLE
Notion synchronization: SYNCED
"""

    evaluation = evaluate_documentation_metadata(body)

    assert evaluation.state == "failure"
    assert "exactly one" in evaluation.description


def test_available_notion_requires_synced_state() -> None:
    body = """
Documentation impact: `GITHUB_AND_NOTION`
Notion access: `AVAILABLE`
Notion synchronization: `SYNCED`
"""

    assert evaluate_documentation_metadata(body).state == "success"


def test_unavailable_notion_requires_structured_handoff() -> None:
    body = """
Documentation impact: GITHUB_AND_NOTION
Notion access: UNAVAILABLE
Notion synchronization: HANDOFF_REQUIRED
GitHub hand-off path: docs/ai/NOTION_HANDOFF.md#governance
"""

    assert evaluate_documentation_metadata(body).state == "success"


def _dependabot() -> ActorIdentity:
    return ActorIdentity(login="dependabot[bot]", type="Bot", id=49699333)


def _human() -> ActorIdentity:
    return ActorIdentity(login="velantrian", type="User", id=1)


def test_trusted_dependabot_identity_requires_bot_type() -> None:
    assert is_trusted_dependabot(_dependabot()) is True
    assert (
        is_trusted_dependabot(
            ActorIdentity(login="dependabot[bot]", type="User", id=49699333)
        )
        is False
    )
    assert (
        is_trusted_dependabot(
            ActorIdentity(login="renovate[bot]", type="Bot", id=2)
        )
        is False
    )


def test_dependabot_uv_lock_missing_metadata_infers_none() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=("uv.lock",),
        body="Bumps uv.lock.",
    )

    assert evaluation.state == "success"
    assert "inferred Documentation impact NONE" in evaluation.description


def test_human_missing_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=_human(),
        changed_paths=(".github/workflows/ci.yml",),
        body="No classification",
    )

    assert evaluation.state == "failure"
    assert "must declare Documentation impact" in evaluation.description


def test_unknown_bot_missing_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=ActorIdentity(login="some-other[bot]", type="Bot", id=99),
        changed_paths=("uv.lock",),
        body="",
    )

    assert evaluation.state == "failure"


def test_human_body_claiming_dependabot_does_not_spoof_identity() -> None:
    evaluation = resolve_documentation_impact(
        actor=_human(),
        changed_paths=(".github/workflows/ci.yml",),
        body="This PR is from dependabot[bot] / app/dependabot.",
    )

    assert evaluation.state == "failure"
    assert "must declare Documentation impact" in evaluation.description


def test_dependabot_workflow_without_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=(".github/workflows/ci.yml",),
        body="Bumps the github-actions group with 3 updates.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description


def test_dependabot_action_without_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=(".github/actions/my-action/action.yml",),
        body="Updates custom action.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description


def test_dependabot_pyproject_toml_without_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=("pyproject.toml",),
        body="Updates dependencies.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description


def test_dependabot_dependabot_yml_without_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=(".github/dependabot.yml",),
        body="Reconfigures Dependabot.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description


def test_dependabot_sensitive_path_without_metadata_fails_closed() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=(
            "uv.lock",
            "docs/operations/branch-ruleset-admin-handoff.md",
        ),
        body="Bumps dependencies.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description


def test_dependabot_explicit_metadata_uses_ordinary_contract() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=("docs/ai/CURRENT_STATE.md",),
        body="Documentation impact: `GITHUB_ONLY`",
    )

    assert evaluation.state == "success"
    assert evaluation.description == "documentation impact is GITHUB_ONLY"


def test_dependabot_explicit_notion_requirement_still_validated() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=("docs/ai/CURRENT_STATE.md",),
        body="Documentation impact: `GITHUB_AND_NOTION`\nNotion access: `AVAILABLE`",
    )

    assert evaluation.state == "failure"
    assert "GITHUB_AND_NOTION requires" in evaluation.description


def test_stage1_ruleset_contract_is_documented_without_claiming_enforcement() -> None:
    text = HANDOFF_PATH.read_text(encoding="utf-8")

    assert "Stage 1" in text
    assert "Stage 2" in text
    assert "Required approvals" in text
    assert "Titan aggregate merge evidence" in text
    assert "Require branches to be up to date" in text or "up to date" in text.lower()
    assert "force push" in text.lower() or "Force push" in text
    assert "deletion" in text.lower() or "Restrict deletions" in text
    assert "Code Owner review" in text
    assert "DO NOT ENABLE" in text or "not enabled" in text.lower() or "deferred" in text.lower()
    assert "branch_ruleset_enforced = false" in text or "branch_ruleset_enforced` remains" in text
    assert "sole" in text.lower() or "single-owner" in text.lower()
    # Contract documentation must not claim the ruleset already exists as active.
    assert "ruleset already active" not in text.lower()
    assert "Ruleset ID:" not in text or "Ruleset ID: *(pending" in text


# ============================================================================
# Strict path validation tests for Dependabot allowlist (issue #4 fix)
# ============================================================================


def test_dependabot_path_validator_accepts_uv_lock() -> None:
    assert _is_dependabot_inferred_none_path("uv.lock") is True


def test_dependabot_path_validator_accepts_requirements_txt() -> None:
    assert _is_dependabot_inferred_none_path("requirements.txt") is True


def test_dependabot_path_validator_accepts_requirements_dev_txt() -> None:
    assert _is_dependabot_inferred_none_path("requirements-dev.txt") is True


def test_dependabot_path_validator_accepts_requirements_nested_txt() -> None:
    assert _is_dependabot_inferred_none_path("requirements/dev.txt") is True


def test_dependabot_path_validator_accepts_requirements_prod_txt() -> None:
    assert _is_dependabot_inferred_none_path("requirements/prod.txt") is True


def test_dependabot_path_validator_rejects_requirements_nested_with_subdirs() -> None:
    assert _is_dependabot_inferred_none_path("requirements/nested/policy.txt") is False


def test_dependabot_path_validator_rejects_requirements_wildcard_traversal() -> None:
    assert _is_dependabot_inferred_none_path("requirements-foo/docs/architecture.txt") is False


def test_dependabot_path_validator_rejects_deeply_nested_requirements() -> None:
    assert _is_dependabot_inferred_none_path("requirements/a/b.txt") is False


def test_dependabot_path_validator_rejects_requirements_in_nested_dir() -> None:
    assert _is_dependabot_inferred_none_path("nested/requirements.txt") is False


def test_dependabot_path_validator_rejects_requirements_in_docs() -> None:
    assert _is_dependabot_inferred_none_path("docs/requirements.txt") is False


def test_dependabot_path_validator_rejects_empty_requirements_file() -> None:
    assert _is_dependabot_inferred_none_path("requirements/.txt") is False


def test_dependabot_path_validator_rejects_dot_traversal() -> None:
    assert _is_dependabot_inferred_none_path("requirements/../policy.txt") is False


def test_dependabot_path_validator_rejects_backslash_paths() -> None:
    assert _is_dependabot_inferred_none_path("requirements\\test.txt") is False


def test_dependabot_path_validator_rejects_absolute_paths() -> None:
    assert _is_dependabot_inferred_none_path("/requirements.txt") is False


def test_dependabot_path_validator_rejects_empty_string() -> None:
    assert _is_dependabot_inferred_none_path("") is False


def test_dependabot_path_validator_rejects_dot_segment() -> None:
    assert _is_dependabot_inferred_none_path("./requirements.txt") is False


def test_dependabot_path_validator_rejects_dotdot_segment() -> None:
    assert _is_dependabot_inferred_none_path("../requirements.txt") is False


def test_dependabot_infer_multiple_valid_paths() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=(
            "uv.lock",
            "requirements.txt",
            "requirements/dev.txt",
            "requirements-prod.txt",
        ),
        body="Updates multiple dependency files.",
    )

    assert evaluation.state == "success"
    assert "inferred Documentation impact NONE" in evaluation.description


def test_dependabot_fail_closed_on_mixed_valid_invalid_paths() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=(
            "uv.lock",
            "docs/architecture.md",  # Invalid path
        ),
        body="Mixed dependencies and docs.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description


def test_dependabot_fail_closed_on_nested_requirements_traversal() -> None:
    evaluation = resolve_documentation_impact(
        actor=_dependabot(),
        changed_paths=("requirements/nested/policy.txt",),
        body="Updates nested file.",
    )

    assert evaluation.state == "failure"
    assert "documentation-sensitive paths" in evaluation.description
