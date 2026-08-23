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
from .security import (
    DEFAULT_RUNTIME_SECURITY_PROFILE,
    RUNTIME_SECURITY_PROFILE_VERSION,
    RuntimeSecurityProfile,
    SandboxAdmissionError,
)
from .workspace import (
    DEFAULT_MAX_WORKSPACE_BYTES,
    DEFAULT_MAX_WORKSPACE_FILES,
    WORKSPACE_MANIFEST_SCHEMA_VERSION,
    WorkspaceFile,
    WorkspaceManifest,
    WorkspaceManifestError,
)

__all__ = [
    "ArtifactRef",
    "DEFAULT_MAX_WORKSPACE_BYTES",
    "DEFAULT_MAX_WORKSPACE_FILES",
    "DEFAULT_RUNTIME_SECURITY_PROFILE",
    "ExecutionReceipt",
    "NetworkPolicy",
    "NullBackend",
    "RUNTIME_SECURITY_PROFILE_VERSION",
    "ResourceLimits",
    "RuntimeSecurityProfile",
    "SandboxAdmissionError",
    "SandboxBackend",
    "SandboxBackendError",
    "SandboxBackendStateError",
    "SandboxBackendUnavailableError",
    "SandboxRun",
    "SandboxSpec",
    "SandboxStatus",
    "WORKSPACE_MANIFEST_SCHEMA_VERSION",
    "WorkspaceFile",
    "WorkspaceManifest",
    "WorkspaceManifestError",
]
