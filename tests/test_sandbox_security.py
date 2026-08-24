from __future__ import annotations

import pytest

from core.sandbox import (
    DEFAULT_RUNTIME_SECURITY_PROFILE,
    NetworkPolicy,
    RuntimeSecurityProfile,
    SandboxAdmissionError,
    SandboxSpec,
)


DIGEST_IMAGE = "registry.example/titan-sandbox@sha256:" + "a" * 64


def _spec(**overrides: object) -> SandboxSpec:
    values: dict[str, object] = {
        "image_ref": DIGEST_IMAGE,
        "command": ("python", "-m", "pytest"),
        "workspace_ref": "workspace:fixture",
    }
    values.update(overrides)
    return SandboxSpec(**values)  # type: ignore[arg-type]


def test_default_profile_admits_digest_pinned_fail_closed_spec() -> None:
    DEFAULT_RUNTIME_SECURITY_PROFILE.admit(_spec())


@pytest.mark.parametrize(
    "image_ref",
    [
        "python:3.11",
        "python:latest",
        "python@sha256:not-a-digest",
        "sha256:" + "a" * 64,
    ],
)
def test_profile_rejects_non_pinned_image_identity(image_ref: str) -> None:
    with pytest.raises(SandboxAdmissionError, match="pinned"):
        DEFAULT_RUNTIME_SECURITY_PROFILE.admit(_spec(image_ref=image_ref))


def test_profile_rejects_writable_root() -> None:
    with pytest.raises(SandboxAdmissionError, match="read_only_root"):
        DEFAULT_RUNTIME_SECURITY_PROFILE.admit(_spec(read_only_root=False))


def test_allowlisted_network_remains_admissible_only_as_contract() -> None:
    spec = _spec(
        network_policy=NetworkPolicy.ALLOWLIST,
        network_allowlist=("pypi.org:443",),
    )
    DEFAULT_RUNTIME_SECURITY_PROFILE.admit(spec)


def test_profile_cannot_be_weakened_by_caller() -> None:
    with pytest.raises(SandboxAdmissionError, match="cannot weaken"):
        RuntimeSecurityProfile(forbid_host_mounts=False)


def test_profile_keeps_secret_injection_forbidden() -> None:
    assert DEFAULT_RUNTIME_SECURITY_PROFILE.forbid_secret_injection is True
    assert DEFAULT_RUNTIME_SECURITY_PROFILE.forbid_host_environment is True
    assert DEFAULT_RUNTIME_SECURITY_PROFILE.require_verified_teardown is True
