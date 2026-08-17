from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(".github/workflows/codeql.yml")
ACTION_SHA = "5595ccaf912efad79be6eef63a5619ff05969be3"


def test_codeql_candidate_is_python_only_and_low_noise() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "languages: python" in text
    assert "build-mode: none" in text
    assert "autobuild" not in text
    assert "security-extended" not in text
    assert "security-and-quality" not in text
    assert 'cron: "17 4 * * 2"' in text


def test_codeql_actions_are_pinned_and_permissions_are_bounded() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert f"github/codeql-action/init@{ACTION_SHA}" in text
    assert f"github/codeql-action/analyze@{ACTION_SHA}" in text
    assert "security-events: write" in text
    assert "contents: read" in text
    assert "actions: read" in text
    assert "packages: read" in text
    assert "contents: write" not in text
    assert "pull-requests: write" not in text
