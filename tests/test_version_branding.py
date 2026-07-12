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
    errors = guard.check_canonical_values() + guard.check_branding()
    assert errors == [], "\n".join(errors)
