"""Pure contracts for a future bounded Titan sandbox executor.

No type in this module performs execution. The contracts deliberately model
sandbox output as untrusted observations/artifacts. Successful execution never
implies truth, Canon admission, promotion, deployment, or production authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Mapping


SANDBOX_SPEC_SCHEMA_VERSION = "titan.sandbox-spec.v0.1"
SANDBOX_RUN_SCHEMA_VERSION = "titan.sandbox-run.v0.1"
EXECUTION_RECEIPT_SCHEMA_VERSION = "titan.execution-receipt.v0.1"


class SandboxContractError(ValueError):
    """Raised when a sandbox contract violates a fail-closed invariant."""


class NetworkPolicy(str, Enum):
    DENY = "deny"
    ALLOWLIST = "allowlist"


class SandboxStatus(str, Enum):
    PREPARED = "prepared"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


def _stable_id(namespace: str, payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"{namespace}:{hashlib.sha256(encoded).hexdigest()}"


def _require_text(value: str, field_name: str) -> str:
    text = (value or "").strip()
    if not text:
        raise SandboxContractError(f"{field_name} must be non-empty")
    return text


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Fail-closed resource envelope for one sandbox run."""

    timeout_seconds: int = 300
    cpu_cores: float = 1.0
    memory_mb: int = 1024
    pids: int = 128
    writable_mb: int = 1024

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise SandboxContractError("timeout_seconds must be > 0")
        if self.cpu_cores <= 0:
            raise SandboxContractError("cpu_cores must be > 0")
        for name in ("memory_mb", "pids", "writable_mb"):
            if getattr(self, name) <= 0:
                raise SandboxContractError(f"{name} must be > 0")


@dataclass(frozen=True, slots=True)
class SandboxSpec:
    """Declarative request for a future sandbox backend.

    `image_ref` is intentionally an opaque backend reference. The contract does
    not require Docker and can later be implemented by Docker, Podman,
    Firecracker, gVisor, or another bounded executor.
    """

    image_ref: str
    command: tuple[str, ...]
    workspace_ref: str
    network_policy: NetworkPolicy = NetworkPolicy.DENY
    network_allowlist: tuple[str, ...] = ()
    environment: tuple[tuple[str, str], ...] = ()
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    ephemeral: bool = True
    read_only_root: bool = True
    inherit_host_environment: bool = False
    schema_version: str = SANDBOX_SPEC_SCHEMA_VERSION
    spec_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != SANDBOX_SPEC_SCHEMA_VERSION:
            raise SandboxContractError("unsupported sandbox spec schema")
        object.__setattr__(self, "image_ref", _require_text(self.image_ref, "image_ref"))
        object.__setattr__(self, "workspace_ref", _require_text(self.workspace_ref, "workspace_ref"))
        if not self.command or any(not str(part).strip() for part in self.command):
            raise SandboxContractError("command must contain non-empty argv entries")
        if not self.ephemeral:
            raise SandboxContractError("sandbox v0.1 requires ephemeral=True")
        if self.inherit_host_environment:
            raise SandboxContractError("host environment inheritance is forbidden")
        allowlist = tuple(sorted(set(item.strip() for item in self.network_allowlist if item.strip())))
        if self.network_policy is NetworkPolicy.DENY and allowlist:
            raise SandboxContractError("network allowlist requires ALLOWLIST policy")
        if self.network_policy is NetworkPolicy.ALLOWLIST and not allowlist:
            raise SandboxContractError("ALLOWLIST policy requires at least one endpoint")
        object.__setattr__(self, "network_allowlist", allowlist)
        env = tuple(sorted((str(k).strip(), str(v)) for k, v in self.environment if str(k).strip()))
        object.__setattr__(self, "environment", env)
        expected = _stable_id("sandbox-spec", self.identity_payload(include_id=False))
        if self.spec_id and self.spec_id != expected:
            raise SandboxContractError("spec_id does not match sandbox spec content")
        object.__setattr__(self, "spec_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "image_ref": self.image_ref,
            "command": list(self.command),
            "workspace_ref": self.workspace_ref,
            "network_policy": self.network_policy.value,
            "network_allowlist": list(self.network_allowlist),
            "environment": [[k, v] for k, v in self.environment],
            "limits": {
                "timeout_seconds": self.limits.timeout_seconds,
                "cpu_cores": self.limits.cpu_cores,
                "memory_mb": self.limits.memory_mb,
                "pids": self.limits.pids,
                "writable_mb": self.limits.writable_mb,
            },
            "ephemeral": self.ephemeral,
            "read_only_root": self.read_only_root,
            "inherit_host_environment": self.inherit_host_environment,
        }
        if include_id:
            payload["spec_id"] = self.spec_id
        return payload


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Reference to an untrusted artifact emitted by a sandbox run."""

    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _require_text(self.path, "artifact path"))
        digest = self.sha256.lower().strip()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise SandboxContractError("artifact sha256 must be a 64-character hex digest")
        object.__setattr__(self, "sha256", digest)
        if self.size_bytes < 0:
            raise SandboxContractError("artifact size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class SandboxRun:
    """Lifecycle snapshot for one backend execution attempt."""

    spec_id: str
    backend: str
    status: SandboxStatus = SandboxStatus.PREPARED
    run_id: str = ""
    schema_version: str = SANDBOX_RUN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SANDBOX_RUN_SCHEMA_VERSION:
            raise SandboxContractError("unsupported sandbox run schema")
        object.__setattr__(self, "spec_id", _require_text(self.spec_id, "spec_id"))
        object.__setattr__(self, "backend", _require_text(self.backend, "backend"))
        payload = {
            "schema_version": self.schema_version,
            "spec_id": self.spec_id,
            "backend": self.backend,
            "status": self.status.value,
        }
        expected = _stable_id("sandbox-run", payload)
        if self.run_id and self.run_id != expected:
            raise SandboxContractError("run_id does not match sandbox run content")
        object.__setattr__(self, "run_id", expected)


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    """Untrusted execution observation; never an authorization or truth claim."""

    run_id: str
    status: SandboxStatus
    exit_code: int | None
    stdout_sha256: str
    stderr_sha256: str
    artifacts: tuple[ArtifactRef, ...] = ()
    duration_ms: int = 0
    trusted: bool = False
    canon_admitted: bool = False
    production_authorized: bool = False
    schema_version: str = EXECUTION_RECEIPT_SCHEMA_VERSION
    receipt_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != EXECUTION_RECEIPT_SCHEMA_VERSION:
            raise SandboxContractError("unsupported execution receipt schema")
        object.__setattr__(self, "run_id", _require_text(self.run_id, "run_id"))
        for name in ("stdout_sha256", "stderr_sha256"):
            digest = getattr(self, name).lower().strip()
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise SandboxContractError(f"{name} must be a 64-character hex digest")
            object.__setattr__(self, name, digest)
        if self.duration_ms < 0:
            raise SandboxContractError("duration_ms must be >= 0")
        if self.trusted or self.canon_admitted or self.production_authorized:
            raise SandboxContractError(
                "sandbox receipts are untrusted observations and cannot carry authority"
            )
        artifacts = tuple(sorted(self.artifacts, key=lambda item: (item.path, item.sha256)))
        object.__setattr__(self, "artifacts", artifacts)
        payload = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "artifacts": [
                {"path": a.path, "sha256": a.sha256, "size_bytes": a.size_bytes}
                for a in artifacts
            ],
            "duration_ms": self.duration_ms,
            "trusted": self.trusted,
            "canon_admitted": self.canon_admitted,
            "production_authorized": self.production_authorized,
        }
        expected = _stable_id("execution-receipt", payload)
        if self.receipt_id and self.receipt_id != expected:
            raise SandboxContractError("receipt_id does not match receipt content")
        object.__setattr__(self, "receipt_id", expected)
