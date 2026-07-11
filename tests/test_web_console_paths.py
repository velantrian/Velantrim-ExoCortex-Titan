"""Regression tests for api/web_console.py app-root resolution.

PR-A (Docker hardening) switched to a non-editable wheel install, which
decouples api/web_console.py's __file__ from the repo/runtime root that
holds static/console/* and the console's docs/*.md files — the console
404'd looking for them inside site-packages. See
api/web_console.py:_resolve_app_root and the VELANTRIM_APP_ROOT the
Dockerfile now sets.
"""

from pathlib import Path

import api.web_console as web_console


def test_development_checkout_path_has_no_env_override(monkeypatch):
    """Without VELANTRIM_APP_ROOT, resolution falls back to the source-tree
    root (api/web_console.py's grandparent directory) — the layout that
    holds when running from an editable/source checkout, not a wheel."""
    monkeypatch.delenv("VELANTRIM_APP_ROOT", raising=False)
    root = web_console._resolve_app_root()
    assert root == Path(web_console.__file__).resolve().parents[1]
    # Sanity: this really is the checked-out repo, not some arbitrary dir.
    assert (root / "static" / "console" / "index.html").is_file()


def test_env_override_wins_regardless_of_file_location(monkeypatch, tmp_path):
    """This is what fixes the wheel/site-packages regression: once
    VELANTRIM_APP_ROOT is set (as the Dockerfile does), it is authoritative
    regardless of where __file__ actually resolves to (site-packages)."""
    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(tmp_path))
    root = web_console._resolve_app_root()
    assert root == tmp_path.resolve()


def test_env_override_matches_docker_runtime_layout(monkeypatch, tmp_path):
    """Exercise the exact value the Dockerfile sets (VELANTRIM_APP_ROOT=/app)
    against a directory laid out like the runtime image: static/console/
    and docs/ copied in next to it, independent of __file__."""
    fake_app_root = tmp_path / "app"
    (fake_app_root / "static" / "console").mkdir(parents=True)
    (fake_app_root / "static" / "console" / "index.html").write_text("<html></html>")
    (fake_app_root / "docs").mkdir()
    (fake_app_root / "docs" / "CONSOLE_BROWSER_TEST.ru.md").write_text("# help")

    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(fake_app_root))
    root = web_console._resolve_app_root()
    assert root == fake_app_root.resolve()
    assert (root / "static" / "console" / "index.html").is_file()
    assert (root / "docs" / "CONSOLE_BROWSER_TEST.ru.md").is_file()


def test_missing_asset_root_resolves_cleanly_without_raising(monkeypatch, tmp_path):
    """A configured-but-nonexistent root must not raise — callers use
    `.is_file()`/console_available() checks, so a bad VELANTRIM_APP_ROOT
    degrades to a clean 404 instead of crashing the app at import time."""
    missing_root = tmp_path / "does-not-exist"
    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(missing_root))
    root = web_console._resolve_app_root()
    assert root == missing_root.resolve()
    assert not (root / "static" / "console" / "index.html").is_file()


def test_resolution_does_not_depend_on_cwd(monkeypatch, tmp_path):
    """Resolution must be deterministic regardless of the process's current
    working directory — it must never silently fall back to Path.cwd()."""
    monkeypatch.delenv("VELANTRIM_APP_ROOT", raising=False)
    expected = Path(web_console.__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)
    assert web_console._resolve_app_root() == expected


class TestConsoleAvailable:
    def test_true_for_the_real_checkout_index(self):
        assert web_console.console_available() is True

    def test_false_when_index_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(web_console, "_CONSOLE_INDEX", tmp_path / "nope.html")
        assert web_console.console_available() is False
