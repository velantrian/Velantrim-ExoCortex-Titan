from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
CONSOLE = REPO_ROOT / "static/console/index.html"
DE_SOURCE = REPO_ROOT / "scripts/_inject_de.js"


def _display_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"(\d+)\.(\d+)\.[^"]+"', text, re.MULTILINE)
    assert match is not None, "project version must remain declared in pyproject.toml"
    return f"V{match.group(1)}.{match.group(2)}"


def test_active_console_subtitles_use_current_project_version() -> None:
    display_version = _display_version()
    console = CONSOLE.read_text(encoding="utf-8")
    de_source = DE_SOURCE.read_text(encoding="utf-8")

    assert "V8.7 · память + LLM" not in console
    assert "V8.7 · memory + LLM" not in console
    assert "V8.7 · Speicher + LLM" not in de_source

    assert f"{display_version} · память + LLM" in console
    assert f"{display_version} · memory + LLM" in console
    assert f"{display_version} · Speicher + LLM" in de_source
