"""Fail-closed admission policy for future runtime-capable sandbox backends.

This module performs validation only. It does not start processes, access a
container runtime, inspect the host, pull images, mount paths, or open networks.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from .contracts import NetworkPolicy, SandboxSpec


RUNTIME_SECURITY_PROFILE_VERSION = "titan.sandbox-runtime-security.v0.1"
_SHA256_IMAGE_RE = re.compile(r"^[^\s@]+@sha256:[0-9a-fA-F]{64}$")


class SandboxAdmissionError(ValueError):
    """Raised when a spec cannot enter a runtime-capable backend."""


@dataclass(frozen=True, slots=True)
class RuntimeSecurityProfile:
    """Backend-independent minimum controls for bounded local execution.

    The booleans are intentionally fixed to their safe v0.1 values. They make
    backend conformance review explicit without creating knobs that callers can
    weaken per run.
    """

    profile_version: str = RUNTIME_SECURITY_PROFILE_VERSION
    require_digest_image: bool = True
    require_read_only_root: bool = True
    require_non_root: bool = True
    forbid_privileged: bool = True
    drop_all_capabilities: bool = True
    forbid_host_namespaces: bool = True
    forbid_host_mounts: bool = True
    forbid_runtime_sockets: bool = True
    forbid_host_devices: bool = True
    forbid_host_environment: bool = True
    forbid_secret_injection: bool = True
    require_ephemeral_workspace: bool = True
    require_verified_teardown: bool = True
    require_external_network_enforcement: bool = True

    def __post_init__(self) -> None:
        if self.profile_version != RUNTIME_SECURITY_PROFILE_VERSION:
            raise SandboxAdmissionError("unsupported runtime security profile")
        required_true = (
            "require_digest_image",
            "require_read_only_root",
            "require_non_root",
            "forbid_privileged",
            "drop_all_capabilities",
            "forbid_host_namespaces",
            "forbid_host_mounts",
            "forbid_runtime_sockets",
            "forbid_host_devices",
            "forbid_host_environment",
            "forbid_secret_injection",
            "require_ephemeral_workspace",
            "require_verified_teardown",
            "require_external_network_enforcement",
        )
        weakened = [name for name in required_true if getattr(self, name) is not True]
        if weakened:
            raise SandboxAdmissionError(
                "runtime security profile cannot weaken v0.1 controls: "
                + ", ".join(weakened)
            )

    def admit(self, spec: SandboxSpec) -> None:
        """Validate the contract-level requirements known before runtime setup."""
        if not _SHA256_IMAGE_RE.fullmatch(spec.image_ref):
            raise SandboxAdmissionError(
                "runtime backend requires image_ref pinned as name@sha256:<64 hex>"
            )
        if not spec.read_only_root:
            raise SandboxAdmissionError("runtime backend requires read_only_root=True")
        if not spec.ephemeral:
            raise SandboxAdmissionError("runtime backend requires ephemeral=True")
        if spec.inherit_host_environment:
            raise SandboxAdmissionError("host environment inheritance is forbidden")
        if spec.network_policy not in (NetworkPolicy.DENY, NetworkPolicy.ALLOWLIST):
            raise SandboxAdmissionError("unsupported network policy")


DEFAULT_RUNTIME_SECURITY_PROFILE = RuntimeSecurityProfile()


__all__ = [
    "DEFAULT_RUNTIME_SECURITY_PROFILE",
    "RUNTIME_SECURITY_PROFILE_VERSION",
    "RuntimeSecurityProfile",
    "SandboxAdmissionError",
]
