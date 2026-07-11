"""Regression tests for core/app_paths.resolve_app_root.

Shared by api/web_console.py, core/deployment_profiles.py, and
core/umwelt_store.py — all three used to compute their runtime asset root
as Path(__file__).resolve().parents[1], which breaks once the package is
installed as a non-editable wheel (PR-A): __file__ then resolves into
site-packages, not /app.
"""

from pathlib import Path

from core.app_paths import resolve_app_root

_FAKE_CALLER_FILE = "/somewhere/site-packages/core/whatever.py"


def test_falls_back_to_file_parent_without_env(monkeypatch):
    monkeypatch.delenv("VELANTRIM_APP_ROOT", raising=False)
    root = resolve_app_root(__file__)
    assert root == Path(__file__).resolve().parents[1]


def test_env_override_wins_regardless_of_caller_file(monkeypatch, tmp_path):
    """This is the actual fix: VELANTRIM_APP_ROOT (set by the Dockerfile)
    is authoritative no matter where the calling module's __file__ points —
    including a path that looks like site-packages."""
    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(tmp_path))
    root = resolve_app_root(_FAKE_CALLER_FILE)
    assert root == tmp_path.resolve()


def test_missing_env_root_resolves_cleanly_without_raising(monkeypatch, tmp_path):
    missing = tmp_path / "does-not-exist"
    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(missing))
    root = resolve_app_root(_FAKE_CALLER_FILE)
    assert root == missing.resolve()
    assert not root.is_dir()


def test_does_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.delenv("VELANTRIM_APP_ROOT", raising=False)
    expected = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)
    assert resolve_app_root(__file__) == expected
