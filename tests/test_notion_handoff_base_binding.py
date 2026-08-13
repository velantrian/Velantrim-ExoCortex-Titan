from scripts.notion_handoff_contract import NOTION_HANDOFF_PATH, evaluate_structured_handoff


def test_wrong_base_sha_fails_closed() -> None:
    current_base = "f5921b06ebb8e6b95e4ed83db9297cccfd5ded44"
    item = f"""## handoff-pr-306
### Test
- **Status:** HANDOFF_REQUIRED
- **Documentation impact:** GITHUB_AND_NOTION
- **Repository / PR / issue:** PR #306
- **Base SHA:** {'c' * 40}
- **Head SHA:** {'b' * 40}
- **Intended Notion record:** Velantrim Titan 9.0
- **Notion access for originating actor:** UNAVAILABLE
### Problem / opportunity
x
### Material findings
x
### Decision and rationale
x
### Authority, safety, privacy, and Canon boundaries
x
### Evidence
x
### Next actions
x
### Synchronization result
x
"""
    body = (
        "Documentation impact: GITHUB_AND_NOTION\n"
        "Notion access: UNAVAILABLE\n"
        "Notion synchronization: HANDOFF_REQUIRED\n"
        f"GitHub hand-off path: {NOTION_HANDOFF_PATH}#handoff-pr-306\n"
    )
    result = evaluate_structured_handoff(
        body,
        item,
        changed_paths=(NOTION_HANDOFF_PATH,),
        pull_request_number=306,
        base_sha=current_base,
    )
    assert result.state == "failure"
    assert "Base SHA must match" in result.description
