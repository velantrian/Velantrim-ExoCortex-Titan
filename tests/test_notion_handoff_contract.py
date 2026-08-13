from scripts.notion_handoff_contract import NOTION_HANDOFF_PATH, evaluate_structured_handoff

PR_NUMBER = 306
BASE_SHA = "f5921b06ebb8e6b95e4ed83db9297cccfd5ded44"


def _body(path: str) -> str:
    return f"Documentation impact: GITHUB_AND_NOTION\nNotion access: UNAVAILABLE\nNotion synchronization: HANDOFF_REQUIRED\nGitHub hand-off path: {path}\n"


def _item() -> str:
    return f"""## handoff-pr-306
### Test item
- **Status:** HANDOFF_REQUIRED
- **Documentation impact:** GITHUB_AND_NOTION
- **Repository / PR / issue:** PR #306 · issue #305
- **Base SHA:** {BASE_SHA}
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


def test_valid_structured_handoff_passes() -> None:
    result = evaluate_structured_handoff(
        _body(f"{NOTION_HANDOFF_PATH}#handoff-pr-306"),
        _item(),
        changed_paths=(NOTION_HANDOFF_PATH,),
        pull_request_number=PR_NUMBER,
        base_sha=BASE_SHA,
    )
    assert result.state == "success"


def test_arbitrary_path_fails() -> None:
    result = evaluate_structured_handoff(
        _body("docs/ai/KNOWN_RISKS.md#anything"),
        _item(),
        changed_paths=(NOTION_HANDOFF_PATH,),
        pull_request_number=PR_NUMBER,
        base_sha=BASE_SHA,
    )
    assert result.state == "failure"


def test_missing_structured_item_fails() -> None:
    result = evaluate_structured_handoff(
        _body(f"{NOTION_HANDOFF_PATH}#handoff-pr-306"),
        "# empty queue\n",
        changed_paths=(NOTION_HANDOFF_PATH,),
        pull_request_number=PR_NUMBER,
        base_sha=BASE_SHA,
    )
    assert result.state == "failure"
    assert "handoff-pr-306 is missing" in result.description


def test_handoff_file_must_be_in_current_pr_diff() -> None:
    result = evaluate_structured_handoff(
        _body(f"{NOTION_HANDOFF_PATH}#handoff-pr-306"),
        _item(),
        changed_paths=(),
        pull_request_number=PR_NUMBER,
        base_sha=BASE_SHA,
    )
    assert result.state == "failure"
    assert "NOTION_HANDOFF.md in the PR diff" in result.description
