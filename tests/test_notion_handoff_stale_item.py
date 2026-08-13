from scripts.notion_handoff_contract import NOTION_HANDOFF_PATH, evaluate_structured_handoff


def test_stale_other_pr_item_fails_closed() -> None:
    base_sha = "f5921b06ebb8e6b95e4ed83db9297cccfd5ded44"
    body = (
        "Documentation impact: GITHUB_AND_NOTION\n"
        "Notion access: UNAVAILABLE\n"
        "Notion synchronization: HANDOFF_REQUIRED\n"
        f"GitHub hand-off path: {NOTION_HANDOFF_PATH}#handoff-pr-306\n"
    )
    result = evaluate_structured_handoff(
        body,
        "## handoff-pr-297\n",
        changed_paths=(NOTION_HANDOFF_PATH,),
        pull_request_number=306,
        base_sha=base_sha,
    )
    assert result.state == "failure"
    assert "handoff-pr-306 is missing" in result.description
