"""Bounded sandbox contracts and backend interfaces for Titan.

The package defines data contracts plus non-executing backend boundaries. It
does not itself start containers, shell out, access Docker/Podman, or grant
runtime authority.
"""

from .backend import (
    NullBackend,
    SandboxBackend,
    SandboxBackendError,
    SandboxBackendStateError,
    SandboxBackendUnavailableError,
)
from .contracts import (
    ArtifactRef,
    ExecutionReceipt,
    NetworkPolicy,
    ResourceLimits,
    SandboxRun,
    SandboxSpec,
    SandboxStatus,
)

__all__ = [
    "ArtifactRef",
    "ExecutionReceipt",
    "NetworkPolicy",
    "NullBackend",
    "ResourceLimits",
    "SandboxBackend",
    "SandboxBackendError",
    "SandboxBackendStateError",
    "SandboxBackendUnavailableError",
    "SandboxRun",
    "SandboxSpec",
    "SandboxStatus",
]
