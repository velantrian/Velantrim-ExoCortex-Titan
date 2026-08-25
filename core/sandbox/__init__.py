"""Bounded sandbox contracts and backend interfaces for Titan.

The package defines data contracts plus bounded non-executing sandbox layers. It
does not itself start containers, shell out, access Docker/Podman, open networks,
or grant runtime authority.
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
from .docker_plan import (
    DOCKER_LAUNCH_PLAN_SCHEMA_VERSION,
    DOCKER_SANDBOX_USER,
    DockerLaunchPlan,
    DockerPlanCompiler,
    DockerPlanError,
)
from .ephemeral_workspace import (
    EphemeralWorkspace,
    EphemeralWorkspaceError,
    EphemeralWorkspaceWriter,
)
from .materializer import (
    BlobResolutionError,
    BlobResolver,
    VerifiedWorkspace,
    VerifiedWorkspaceBlob,
    WorkspaceMaterializationError,
    WorkspaceMaterializer,
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
    "BlobResolutionError",
    "BlobResolver",
    "DEFAULT_MAX_WORKSPACE_BYTES",
    "DEFAULT_MAX_WORKSPACE_FILES",
    "DEFAULT_RUNTIME_SECURITY_PROFILE",
    "DOCKER_LAUNCH_PLAN_SCHEMA_VERSION",
    "DOCKER_SANDBOX_USER",
    "DockerLaunchPlan",
    "DockerPlanCompiler",
    "DockerPlanError",
    "EphemeralWorkspace",
    "EphemeralWorkspaceError",
    "EphemeralWorkspaceWriter",
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
    "VerifiedWorkspace",
    "VerifiedWorkspaceBlob",
    "WORKSPACE_MANIFEST_SCHEMA_VERSION",
    "WorkspaceFile",
    "WorkspaceManifest",
    "WorkspaceManifestError",
    "WorkspaceMaterializationError",
    "WorkspaceMaterializer",
]
