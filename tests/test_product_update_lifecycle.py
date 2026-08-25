from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_titan.py"
spec = importlib.util.spec_from_file_location("update_titan_stage8", SCRIPT)
assert spec and spec.loader
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def test_non_git_checkout_fails_with_fresh_checkout_guidance(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "bootstrap_titan.py").write_text("# placeholder\n", encoding="utf-8")

    with pytest.raises(updater.UpdateError) as exc:
        updater.validate_checkout(tmp_path)

    message = str(exc.value)
    assert "not a Git checkout" in message
    assert "fresh Titan checkout" in message


def test_modified_worktree_is_never_overwritten(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        updater,
        "git",
        lambda _root, *args, **kwargs: SimpleNamespace(stdout=" M server.py\n", returncode=0),
    )

    with pytest.raises(updater.UpdateError, match="Local changes are present"):
        updater.require_clean_tree(tmp_path)


def test_diverged_history_refuses_automatic_update(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        updater,
        "git",
        lambda _root, *args, **kwargs: SimpleNamespace(stdout="", returncode=1),
    )

    with pytest.raises(updater.UpdateError, match="have diverged"):
        updater.require_fast_forward(tmp_path, "old", "new")


def _patch_update_plan(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(updater, "project_root", lambda: tmp_path)
    monkeypatch.setattr(updater, "validate_checkout", lambda _root: None)
    monkeypatch.setattr(updater, "current_branch", lambda _root: "main")
    monkeypatch.setattr(updater, "require_clean_tree", lambda _root: None)
    monkeypatch.setattr(updater, "current_sha", lambda _root: "old-sha")
    monkeypatch.setattr(updater, "fetch_main", lambda _root: None)
    monkeypatch.setattr(updater, "remote_sha", lambda _root: "new-sha")
    monkeypatch.setattr(updater, "require_fast_forward", lambda _root, _old, _new: None)


def test_default_mode_only_reports_update(tmp_path: Path, monkeypatch, capsys) -> None:
    _patch_update_plan(monkeypatch, tmp_path)
    merge_calls: list[tuple[str, ...]] = []

    def fake_git(_root, *args, **kwargs):
        merge_calls.append(tuple(args))
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(updater, "git", fake_git)

    assert updater.run([]) == 0
    assert merge_calls == []
    output = capsys.readouterr().out
    assert "Update available" in output
    assert "--apply" in output


def test_apply_uses_fast_forward_only_and_refreshes_runtime(tmp_path: Path, monkeypatch, capsys) -> None:
    _patch_update_plan(monkeypatch, tmp_path)
    git_calls: list[tuple[str, ...]] = []

    def fake_git(_root, *args, **kwargs):
        git_calls.append(tuple(args))
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(updater, "git", fake_git)
    monkeypatch.setattr(updater, "refresh_runtime", lambda _root: True)

    assert updater.run(["--apply"]) == 0
    assert git_calls == [("merge", "--ff-only", "origin/main")]
    output = capsys.readouterr().out
    assert "old-sha -> new-sha" in output
    assert "dependencies refreshed" in output
    assert "Rollback reference" in output


def test_non_main_branch_is_rejected_before_update(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(updater, "project_root", lambda: tmp_path)
    monkeypatch.setattr(updater, "validate_checkout", lambda _root: None)
    monkeypatch.setattr(updater, "current_branch", lambda _root: "feature/work")

    with pytest.raises(updater.UpdateError) as exc:
        updater.run([])

    assert "not main" in str(exc.value)
    assert "clean main checkout" in str(exc.value)
