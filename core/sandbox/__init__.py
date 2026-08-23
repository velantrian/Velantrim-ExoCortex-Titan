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
    SandboxBackendUnavailable,
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
    "SandboxBackendUnavailable",
    "SandboxRun",
    "SandboxSpec",
    "SandboxStatus",
]
