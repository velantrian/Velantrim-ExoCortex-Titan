from __future__ import annotations

import hashlib

import pytest

from core.sandbox import (
    DockerLaunchPlan,
    DockerPlanCompiler,
    DockerPlanError,
    EphemeralWorkspaceWriter,
    NetworkPolicy,
    ResourceLimits,
    SandboxAdmissionError,
    SandboxSpec,
    VerifiedWorkspace,
    VerifiedWorkspaceBlob,
    WorkspaceFile,
    WorkspaceManifest,
)


IMAGE = "registry.example/sandbox@sha256:" + "a" * 64


def _verified_workspace() -> VerifiedWorkspace:
    payload = b"input\n"
    file = WorkspaceFile(
        path="input.txt",
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )
    manifest = WorkspaceManifest(files=(file,))
    return VerifiedWorkspace(
        manifest=manifest,
        files=(VerifiedWorkspaceBlob(file=file, payload=payload),),
    )


def _spec(workspace_ref: str, **overrides: object) -> SandboxSpec:
    values: dict[str, object] = {
        "image_ref": IMAGE,
        "command": ("python", "-m", "pytest"),
        "workspace_ref": workspace_ref,
        "environment": (("PYTHONHASHSEED", "0"),),
        "limits": ResourceLimits(
            timeout_seconds=30,
            cpu_cores=1.5,
            memory_mb=256,
            pids=64,
            writable_mb=32,
        ),
    }
    values.update(overrides)
    return SandboxSpec(**values)  # type: ignore[arg-type]


def test_compiler_maps_fail_closed_security_controls_without_runtime_call() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    try:
        plan = DockerPlanCompiler().compile(_spec(workspace.manifest_id), workspace)

        assert plan.image_ref == IMAGE
        assert plan.workspace_manifest_id == workspace.manifest_id
        assert plan.user == "65532:65532"
        assert plan.read_only_root is True
        assert plan.network_mode == "none"
        assert plan.cap_drop == ("ALL",)
        assert plan.security_opt == ("no-new-privileges:true",)
        assert plan.pids_limit == 64
        assert plan.memory_bytes == 256 * 1024 * 1024
        assert plan.nano_cpus == 1_500_000_000
        assert plan.timeout_seconds == 30
        assert plan.writable_bytes == 32 * 1024 * 1024
        assert plan.environment == (("PYTHONHASHSEED", "0"),)
    finally:
        workspace.close()


def test_compiler_rejects_workspace_binding_mismatch() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    try:
        with pytest.raises(DockerPlanError, match="workspace_ref"):
            DockerPlanCompiler().compile(_spec("workspace-manifest:" + "f" * 64), workspace)
    finally:
        workspace.close()


def test_compiler_rejects_closed_workspace() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    spec = _spec(workspace.manifest_id)
    workspace.close()

    with pytest.raises(DockerPlanError, match="closed workspace"):
        DockerPlanCompiler().compile(spec, workspace)


def test_docker_v01_rejects_allowlist_until_external_enforcement_exists() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    try:
        spec = _spec(
            workspace.manifest_id,
            network_policy=NetworkPolicy.ALLOWLIST,
            network_allowlist=("pypi.org:443",),
        )
        with pytest.raises(DockerPlanError, match="DENY networking only"):
            DockerPlanCompiler().compile(spec, workspace)
    finally:
        workspace.close()


def test_compiler_rejects_mutable_image_before_plan_creation() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    try:
        spec = _spec(workspace.manifest_id, image_ref="python:latest")
        with pytest.raises(SandboxAdmissionError, match="pinned"):
            DockerPlanCompiler().compile(spec, workspace)
    finally:
        workspace.close()


def test_compiler_rejects_non_finite_cpu_limit() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    try:
        spec = _spec(
            workspace.manifest_id,
            limits=ResourceLimits(cpu_cores=float("nan")),
        )
        with pytest.raises(DockerPlanError, match="finite"):
            DockerPlanCompiler().compile(spec, workspace)
    finally:
        workspace.close()


def test_launch_plan_cannot_weaken_network_or_privilege_defaults() -> None:
    with pytest.raises(DockerPlanError, match="network_mode"):
        DockerLaunchPlan(
            image_ref=IMAGE,
            command=("true",),
            workspace_manifest_id="workspace-manifest:" + "a" * 64,
            environment=(),
            user="65532:65532",
            read_only_root=True,
            network_mode="bridge",
            cap_drop=("ALL",),
            security_opt=("no-new-privileges:true",),
            pids_limit=1,
            memory_bytes=1,
            nano_cpus=1,
            timeout_seconds=1,
            writable_bytes=1,
        )
