"""Pure Docker launch-plan compilation for Titan Sandbox.

This module translates already-admitted sandbox contracts into an immutable
security plan. It never invokes Docker, starts a process, mounts a path, opens a
network, reads secrets, or mutates the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from .contracts import NetworkPolicy, SandboxSpec
from .ephemeral_workspace import EphemeralWorkspace
from .security import DEFAULT_RUNTIME_SECURITY_PROFILE, RuntimeSecurityProfile


DOCKER_LAUNCH_PLAN_SCHEMA_VERSION = "titan.sandbox-docker-plan.v0.1"
DOCKER_SANDBOX_USER = "65532:65532"


class DockerPlanError(ValueError):
    """Raised when a SandboxSpec cannot be represented by the safe Docker v0.1 plan."""


@dataclass(frozen=True, slots=True)
class DockerLaunchPlan:
    """Immutable security intent for a future Docker runtime adapter.

    The plan intentionally contains no Docker socket/host, container ID, host
    bind path, credential, or executable command for invoking the Docker CLI.
    """

    image_ref: str
    command: tuple[str, ...]
    workspace_manifest_id: str
    environment: tuple[tuple[str, str], ...]
    user: str
    read_only_root: bool
    network_mode: str
    cap_drop: tuple[str, ...]
    security_opt: tuple[str, ...]
    pids_limit: int
    memory_bytes: int
    nano_cpus: int
    timeout_seconds: int
    writable_bytes: int
    schema_version: str = DOCKER_LAUNCH_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != DOCKER_LAUNCH_PLAN_SCHEMA_VERSION:
            raise DockerPlanError("unsupported Docker launch plan schema")
        if self.user != DOCKER_SANDBOX_USER:
            raise DockerPlanError("Docker sandbox user is fixed in v0.1")
        if self.read_only_root is not True:
            raise DockerPlanError("Docker sandbox root must be read-only")
        if self.network_mode != "none":
            raise DockerPlanError("Docker v0.1 requires network_mode=none")
        if self.cap_drop != ("ALL",):
            raise DockerPlanError("Docker v0.1 requires cap_drop=ALL")
        if self.security_opt != ("no-new-privileges:true",):
            raise DockerPlanError("Docker v0.1 requires no-new-privileges")
        for name in ("pids_limit", "memory_bytes", "nano_cpus", "timeout_seconds", "writable_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise DockerPlanError(f"{name} must be a positive integer")
        if not self.workspace_manifest_id.startswith("workspace-manifest:"):
            raise DockerPlanError("workspace must be bound to a WorkspaceManifest identity")


class DockerPlanCompiler:
    """Compile a deny-only Docker v0.1 security plan without executing it."""

    def __init__(
        self,
        *,
        security_profile: RuntimeSecurityProfile = DEFAULT_RUNTIME_SECURITY_PROFILE,
    ) -> None:
        self._security_profile = security_profile

    def compile(self, spec: SandboxSpec, workspace: EphemeralWorkspace) -> DockerLaunchPlan:
        """Validate exact bindings and return immutable Docker security intent."""
        self._security_profile.admit(spec)
        if workspace.closed:
            raise DockerPlanError("cannot plan execution for a closed workspace")
        if spec.workspace_ref != workspace.manifest_id:
            raise DockerPlanError("SandboxSpec workspace_ref must equal workspace manifest_id")
        if spec.network_policy is not NetworkPolicy.DENY:
            raise DockerPlanError(
                "Docker v0.1 supports DENY networking only; ALLOWLIST requires external enforcement"
            )
        cpu_cores = float(spec.limits.cpu_cores)
        if not math.isfinite(cpu_cores) or cpu_cores <= 0:
            raise DockerPlanError("cpu_cores must be finite and positive")
        nano_cpus = int(cpu_cores * 1_000_000_000)
        if nano_cpus <= 0:
            raise DockerPlanError("cpu_cores is too small for Docker nano_cpus")

        return DockerLaunchPlan(
            image_ref=spec.image_ref,
            command=spec.command,
            workspace_manifest_id=workspace.manifest_id,
            environment=spec.environment,
            user=DOCKER_SANDBOX_USER,
            read_only_root=True,
            network_mode="none",
            cap_drop=("ALL",),
            security_opt=("no-new-privileges:true",),
            pids_limit=spec.limits.pids,
            memory_bytes=spec.limits.memory_mb * 1024 * 1024,
            nano_cpus=nano_cpus,
            timeout_seconds=spec.limits.timeout_seconds,
            writable_bytes=spec.limits.writable_mb * 1024 * 1024,
        )


__all__ = [
    "DOCKER_LAUNCH_PLAN_SCHEMA_VERSION",
    "DOCKER_SANDBOX_USER",
    "DockerLaunchPlan",
    "DockerPlanCompiler",
    "DockerPlanError",
]
