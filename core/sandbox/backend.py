"""Backend protocol boundary for Titan sandbox execution.

This module defines orchestration-facing interfaces only. It does not execute
commands, access a container runtime, open network connections, mount filesystems,
read host secrets, or grant authority.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contracts import ArtifactRef, ExecutionReceipt, SandboxRun, SandboxSpec


class SandboxBackendError(RuntimeError):
    """Base error for bounded sandbox backend adapters."""


class SandboxBackendUnavailableError(SandboxBackendError):
    """Raised when a backend intentionally has no execution capability."""


class SandboxBackendStateError(SandboxBackendError):
    """Raised when a caller violates a backend lifecycle boundary."""


@runtime_checkable
class SandboxBackend(Protocol):
    """Minimal backend-neutral lifecycle contract.

    Implementations must enforce SandboxSpec constraints themselves. The
    protocol is deliberately silent about Docker, Podman, gVisor, Firecracker,
    Kubernetes, or any other concrete execution technology.
    """

    @property
    def name(self) -> str:
        """Stable backend identifier used in SandboxRun provenance."""
        ...

    def prepare(self, spec: SandboxSpec, *, attempt_id: str) -> SandboxRun:
        """Prepare one execution attempt without changing trust or authority."""
        ...

    def execute(self, run: SandboxRun) -> ExecutionReceipt:
        """Execute one previously prepared attempt and return an untrusted receipt."""
        ...

    def collect(self, receipt: ExecutionReceipt) -> tuple[ArtifactRef, ...]:
        """Return artifact references already represented by the receipt."""
        ...

    def teardown(self, run: SandboxRun) -> None:
        """Release backend-owned ephemeral state for one run."""
        ...


class NullBackend:
    """Fail-closed backend with deliberately zero execution capability.

    This is suitable as a safe default wiring target: callers can prepare a run
    identity, but any attempt to execute fails explicitly. It does not allocate
    workspaces or touch the host.
    """

    name = "null"

    def prepare(self, spec: SandboxSpec, *, attempt_id: str) -> SandboxRun:
        return SandboxRun(
            spec_id=spec.spec_id,
            backend=self.name,
            attempt_id=attempt_id,
        )

    def execute(self, run: SandboxRun) -> ExecutionReceipt:
        self._require_owned_run(run)
        raise SandboxBackendUnavailableError(
            "NullBackend has no execution capability"
        )

    def collect(self, receipt: ExecutionReceipt) -> tuple[ArtifactRef, ...]:
        raise SandboxBackendUnavailableError(
            "NullBackend cannot collect artifacts because it never executes"
        )

    def teardown(self, run: SandboxRun) -> None:
        self._require_owned_run(run)

    def _require_owned_run(self, run: SandboxRun) -> None:
        if run.backend != self.name:
            raise SandboxBackendStateError(
                "run backend does not match NullBackend"
            )


__all__ = [
    "NullBackend",
    "SandboxBackend",
    "SandboxBackendError",
    "SandboxBackendStateError",
    "SandboxBackendUnavailableError",
]
