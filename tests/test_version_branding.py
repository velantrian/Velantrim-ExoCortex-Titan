"""
tests/test_version_branding.py — Version/branding unification regression guard

Confirms the Titan 9.0 unification did not regress:
    - core.__version__ / pyproject.toml stay canonical and in sync,
    - healthcheck() reports core.__version__ (no stale hardcoded fallback),
    - active public/runtime entrypoints carry no legacy V8.7 current-brand string.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import core
from core.metrics import healthcheck
from scripts import check_version_branding as guard


def test_core_version_is_canonical() -> None:
    assert core.__version__ == guard.CANONICAL_VERSION


def test_healthcheck_reports_core_version_without_override() -> None:
    os.environ.pop("VELANTRIM_VERSION", None)
    result = healthcheck()
    assert result["version"] == core.__version__
    assert result["version"] != "8.7.0"


def test_healthcheck_respects_explicit_override() -> None:
    os.environ["VELANTRIM_VERSION"] = "9.9.9-test-override"
    try:
        importlib.reload(__import__("core.metrics", fromlist=["healthcheck"]))
        from core.metrics import healthcheck as healthcheck_reloaded

        assert healthcheck_reloaded()["version"] == "9.9.9-test-override"
    finally:
        os.environ.pop("VELANTRIM_VERSION", None)


def test_no_canonical_or_branding_drift() -> None:
    errors = guard.check_canonical_values() + guard.check_branding() + guard.check_public_docs()
    assert errors == [], "\n".join(errors)


def test_public_doc_guard_detects_missing_version_and_section_drift(tmp_path: Path) -> None:
    for files, _anchors in guard.DOC_SECTION_PAIRS:
        for rel in files:
            (tmp_path / rel).write_text(
                (guard.ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8"
            )
    assert guard.check_public_docs(tmp_path) == []
    ru = tmp_path / "README.ru.md"
    original = ru.read_text(encoding="utf-8")
    ru.write_text(
        original.replace(f"v{guard.CANONICAL_VERSION}<!-- /SYNC:VERSION -->",
                         "v0.0.0<!-- /SYNC:VERSION -->"),
        encoding="utf-8",
    )
    assert any("version marker" in error for error in guard.check_public_docs(tmp_path))
    ru.write_text(original.replace('<a id="quick-start"></a>', ""), encoding="utf-8")
    assert any("section anchors" in error for error in guard.check_public_docs(tmp_path))
    ru.unlink()
    assert any("document missing" in error for error in guard.check_public_docs(tmp_path))
