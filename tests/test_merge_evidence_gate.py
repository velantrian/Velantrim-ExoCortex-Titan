from __future__ import annotations

from scripts.check_pr_merge_evidence import (
    ARM03_WORKFLOW,
    CI_WORKFLOW,
    CONTINUITY_WORKFLOW,
    DOCKER_WORKFLOW,
    classify_required_workflows,
    evaluate_documentation_metadata,
    evaluate_required_runs,
)


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
