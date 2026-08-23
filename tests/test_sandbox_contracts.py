from __future__ import annotations

import pytest

from core.sandbox import (
    ArtifactRef,
    ExecutionReceipt,
    NetworkPolicy,
    ResourceLimits,
    SandboxRun,
    SandboxSpec,
    SandboxStatus,
)
from core.sandbox.contracts import SandboxContractError


ZERO_SHA = "0" * 64
ONE_SHA = "1" * 64


def _spec(**overrides: object) -> SandboxSpec:
    values: dict[str, object] = {
        "image_ref": "python:3.11-slim@sha256:deadbeef",
        "command": ("python", "-m", "pytest", "-q"),
        "workspace_ref": "workspace:example",
    }
    values.update(overrides)
    return SandboxSpec(**values)  # type: ignore[arg-type]


def test_defaults_are_fail_closed() -> None:
    spec = _spec()

    assert spec.ephemeral is True
    assert spec.read_only_root is True
    assert spec.inherit_host_environment is False
    assert spec.network_policy is NetworkPolicy.DENY
    assert spec.network_allowlist == ()
    assert spec.limits == ResourceLimits()


def test_spec_id_is_stable_for_equivalent_content() -> None:
    first = _spec(environment=(("B", "2"), ("A", "1")))
    second = _spec(environment=(("A", "1"), ("B", "2")))

    assert first.spec_id == second.spec_id


def test_non_ephemeral_sandbox_is_rejected() -> None:
    with pytest.raises(SandboxContractError, match="ephemeral"):
        _spec(ephemeral=False)


def test_host_environment_inheritance_is_rejected() -> None:
    with pytest.raises(SandboxContractError, match="host environment"):
        _spec(inherit_host_environment=True)


def test_network_allowlist_requires_allowlist_policy() -> None:
    with pytest.raises(SandboxContractError, match="allowlist"):
        _spec(network_allowlist=("pypi.org:443",))


def test_allowlist_policy_requires_destination() -> None:
    with pytest.raises(SandboxContractError, match="requires at least one endpoint"):
        _spec(network_policy=NetworkPolicy.ALLOWLIST)


def test_resource_limits_must_be_positive() -> None:
    with pytest.raises(SandboxContractError, match="timeout_seconds"):
        ResourceLimits(timeout_seconds=0)


def test_artifact_requires_content_digest() -> None:
    with pytest.raises(SandboxContractError, match="sha256"):
        ArtifactRef(path="dist/pkg.whl", sha256="not-a-digest", size_bytes=12)


def test_receipt_cannot_carry_authority() -> None:
    run = SandboxRun(spec_id=_spec().spec_id, backend="unimplemented")

    with pytest.raises(SandboxContractError, match="cannot carry authority"):
        ExecutionReceipt(
            run_id=run.run_id,
            status=SandboxStatus.SUCCEEDED,
            exit_code=0,
            stdout_sha256=ZERO_SHA,
            stderr_sha256=ZERO_SHA,
            trusted=True,
        )


def test_receipt_identity_is_stable_across_artifact_order() -> None:
    run = SandboxRun(spec_id=_spec().spec_id, backend="unimplemented")
    a = ArtifactRef(path="a.txt", sha256=ZERO_SHA, size_bytes=1)
    b = ArtifactRef(path="b.txt", sha256=ONE_SHA, size_bytes=2)

    first = ExecutionReceipt(
        run_id=run.run_id,
        status=SandboxStatus.SUCCEEDED,
        exit_code=0,
        stdout_sha256=ZERO_SHA,
        stderr_sha256=ONE_SHA,
        artifacts=(b, a),
    )
    second = ExecutionReceipt(
        run_id=run.run_id,
        status=SandboxStatus.SUCCEEDED,
        exit_code=0,
        stdout_sha256=ZERO_SHA,
        stderr_sha256=ONE_SHA,
        artifacts=(a, b),
    )

    assert first.receipt_id == second.receipt_id
    assert first.artifacts == (a, b)
