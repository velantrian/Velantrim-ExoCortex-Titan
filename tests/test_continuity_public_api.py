"""Smoke tests for the public continuity package API."""

from core import continuity
from core.continuity import (
    CompleteShadowRunInput,
    CompleteShadowRunResult,
    CompleteShadowRunner,
    ShadowRunnerConfig,
)


def test_complete_shadow_runner_is_exported_from_public_api() -> None:
    assert continuity.CompleteShadowRunner is CompleteShadowRunner
    assert continuity.CompleteShadowRunInput is CompleteShadowRunInput
    assert continuity.CompleteShadowRunResult is CompleteShadowRunResult
    assert continuity.ShadowRunnerConfig is ShadowRunnerConfig
    assert "CompleteShadowRunner" in continuity.__all__
    assert "ShadowRunnerConfig" in continuity.__all__
