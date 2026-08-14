from __future__ import annotations

from pathlib import Path

import yaml

from scripts.check_pr_merge_evidence import paths_allow_dependabot_inferred_none


CONFIG = Path(".github/dependabot.yml")


def _updates() -> list[dict[str, object]]:
    payload = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert payload["version"] == 2
    updates = payload["updates"]
    assert isinstance(updates, list)
    return updates


def _ecosystem(name: str) -> dict[str, object]:
    matches = [entry for entry in _updates() if entry.get("package-ecosystem") == name]
    assert len(matches) == 1
    return matches[0]


def test_existing_github_actions_dependabot_owner_is_preserved() -> None:
    actions = _ecosystem("github-actions")
    assert actions["directory"] == "/"
    assert actions["schedule"] == {"interval": "weekly"}


def test_uv_dependabot_is_bounded_to_lockfile_only_weekly_refreshes() -> None:
    uv = _ecosystem("uv")

    assert uv["directory"] == "/"
    assert uv["schedule"] == {"interval": "weekly"}
    assert uv["versioning-strategy"] == "lockfile-only"
    assert uv["open-pull-requests-limit"] == 2
    assert uv["groups"] == {"uv-lock-refresh": {"patterns": ["*"]}}


def test_trusted_dependabot_lock_refresh_matches_existing_merge_evidence_boundary() -> None:
    assert paths_allow_dependabot_inferred_none(("uv.lock",)) is True
    assert paths_allow_dependabot_inferred_none(("pyproject.toml", "uv.lock")) is False
