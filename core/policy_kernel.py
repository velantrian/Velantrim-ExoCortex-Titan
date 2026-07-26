"""
Local-first policy kernel for Titan.

This module is the small, deterministic authority boundary between runtime
health/policy state and components that want to use a capability.  It does
not route work, call providers, or mutate memory.  ADAO will eventually
consume its immutable snapshots and leases; it must never reinterpret or
weaken them.

P0 guarantees implemented here:

* canonical writes are local-only;
* the write-protocol gate is mandatory;
* network access is denied unless a later, reviewed policy source explicitly
  grants it;
* a missing policy dependency is a denial, not an implicit permission;
* a previously verified local policy may supply restrictions during a
  dependency failure, but cannot authorize a high-risk canonical write while
  the current supervisor state is unknown;
* decisions use stable reason codes and carry a replayable snapshot id.

The current kernel intentionally has no remote-policy dependency.  Future
configuration sources can be added behind ``PolicyKernel.capture_snapshot``
without granting them canonical write authority.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger("velantrim.policy_kernel")

POLICY_VERSION = "titan-policy-v1"


class NetworkMode(str, Enum):
    """Whether a capability may contact the network."""

    DENY = "deny"
    ASK = "ask"
    ALLOW = "allow"


class RemoteDataMode(str, Enum):
    """Maximum data exposure permitted to a remote capability."""

    NEVER = "never"
    REDACTED = "redacted"
    ALLOWED = "allowed"


@dataclass(frozen=True)
class EffectivePolicy:
    """Resolved hard policy.  Optimization preferences do not belong here."""

    network: NetworkMode = NetworkMode.DENY
    remote_data: RemoteDataMode = RemoteDataMode.NEVER
    canonical_write_provider: str = "local"
    remote_canonical_write_allowed: bool = False
    write_gate_required: bool = True
    fail_closed: bool = True


@dataclass(frozen=True)
class PolicySnapshot:
    """Immutable policy/health view used for one decision or analysis plan."""

    snapshot_id: str
    policy_version: str
    captured_at: str
    effective: EffectivePolicy
    supervisor_mode: str
    writes_allowed: bool
    source: str
    reason_code: str


@dataclass(frozen=True)
class PolicyDecision:
    """One explainable allow/deny result."""

    allowed: bool
    reason_code: str
    snapshot_id: str
    policy_version: str


@dataclass(frozen=True)
class CapabilityLease:
    """A bounded permission token for an execution plan.

    A lease is descriptive in this P0 slice; it does not perform I/O and does
    not outlive the snapshot that produced it.  Execution engines must reject
    a lease whose ``snapshot_id`` does not match the active plan.
    """

    capability: str
    locality: str
    allowed: bool
    reason_code: str
    snapshot_id: str
    policy_version: str


def _snapshot_id(
    effective: EffectivePolicy,
    *,
    supervisor_mode: str,
    writes_allowed: bool,
    source: str,
    reason_code: str,
) -> str:
    payload = {
        "policy_version": POLICY_VERSION,
        "effective": {
            **asdict(effective),
            "network": effective.network.value,
            "remote_data": effective.remote_data.value,
        },
        "supervisor_mode": supervisor_mode,
        "writes_allowed": writes_allowed,
        "source": source,
        "reason_code": reason_code,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


class PolicyKernel:
    """Resolve strict local policy and issue deterministic decisions."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_verified_effective: EffectivePolicy | None = None
        self._warned_legacy_disable = False

    def _effective_from_local_config(self) -> EffectivePolicy:
        """Read local configuration without allowing it to weaken P0 rules."""
        from core.feature_config import get_config

        configured_gate = bool(
            getattr(get_config().app, "enable_write_gate", True)
        )
        # ENABLE_WRITE_GATE is retained as a compatibility/readout field, but
        # a false value can no longer switch off a canonical safety boundary.
        if not configured_gate and not self._warned_legacy_disable:
            logger.warning(
                "ENABLE_WRITE_GATE=0 is ignored: the canonical write gate is "
                "mandatory under %s",
                POLICY_VERSION,
            )
            self._warned_legacy_disable = True
        return EffectivePolicy()

    @staticmethod
    def _supervisor_mode() -> str:
        from core.meta_supervisor import get_meta_supervisor

        supervisor = get_meta_supervisor()
        mode = getattr(supervisor, "mode", None)
        value = getattr(mode, "value", mode)
        if not isinstance(value, str) or not value:
            raise RuntimeError("MetaSupervisor returned no valid mode")
        return value

    def _make_snapshot(
        self,
        effective: EffectivePolicy,
        *,
        supervisor_mode: str,
        writes_allowed: bool,
        source: str,
        reason_code: str,
    ) -> PolicySnapshot:
        return PolicySnapshot(
            snapshot_id=_snapshot_id(
                effective,
                supervisor_mode=supervisor_mode,
                writes_allowed=writes_allowed,
                source=source,
                reason_code=reason_code,
            ),
            policy_version=POLICY_VERSION,
            captured_at=datetime.now(UTC).isoformat(),
            effective=effective,
            supervisor_mode=supervisor_mode,
            writes_allowed=writes_allowed,
            source=source,
            reason_code=reason_code,
        )

    def capture_snapshot(self) -> PolicySnapshot:
        """Capture current policy; dependency failure is always fail-closed."""
        with self._lock:
            try:
                effective = self._effective_from_local_config()
                supervisor_mode = self._supervisor_mode()
            except Exception as exc:  # noqa: BLE001 - boundary must fail closed
                effective = self._last_verified_effective or EffectivePolicy()
                source = (
                    "last_verified_fail_closed"
                    if self._last_verified_effective is not None
                    else "safe_default_fail_closed"
                )
                logger.error(
                    "PolicyKernel dependency unavailable; canonical writes "
                    "blocked (%s)",
                    type(exc).__name__,
                )
                return self._make_snapshot(
                    effective,
                    supervisor_mode="unavailable",
                    writes_allowed=False,
                    source=source,
                    reason_code="policy_dependency_unavailable",
                )

            self._last_verified_effective = effective
            safe_mode = supervisor_mode == "safe_mode"
            return self._make_snapshot(
                effective,
                supervisor_mode=supervisor_mode,
                writes_allowed=not safe_mode,
                source="verified_local_runtime",
                reason_code=(
                    "safe_mode_writes_blocked" if safe_mode else "ok"
                ),
            )

    def canonical_write_decision(self) -> PolicyDecision:
        snapshot = self.capture_snapshot()
        allowed = (
            snapshot.writes_allowed
            and snapshot.effective.canonical_write_provider == "local"
            and not snapshot.effective.remote_canonical_write_allowed
            and snapshot.effective.write_gate_required
        )
        reason = snapshot.reason_code
        if snapshot.writes_allowed and not allowed:
            reason = "canonical_write_policy_invalid"
        return PolicyDecision(
            allowed=allowed,
            reason_code=reason,
            snapshot_id=snapshot.snapshot_id,
            policy_version=snapshot.policy_version,
        )

    def lease_capability(
        self,
        capability: str,
        *,
        locality: str = "local",
        requires_network: bool = False,
    ) -> CapabilityLease:
        """Issue a least-authority lease from one immutable snapshot."""
        snapshot = self.capture_snapshot()
        allowed = True
        reason = "ok"

        if capability == "canonical_write":
            if locality != "local":
                allowed = False
                reason = "remote_canonical_write_forbidden"
            else:
                allowed = (
                    snapshot.writes_allowed
                    and snapshot.effective.canonical_write_provider == "local"
                    and not snapshot.effective.remote_canonical_write_allowed
                    and snapshot.effective.write_gate_required
                )
                reason = snapshot.reason_code
                if snapshot.writes_allowed and not allowed:
                    reason = "canonical_write_policy_invalid"
            return CapabilityLease(
                capability=capability,
                locality=locality,
                allowed=allowed,
                reason_code=reason,
                snapshot_id=snapshot.snapshot_id,
                policy_version=snapshot.policy_version,
            )
        if requires_network and snapshot.effective.network is NetworkMode.DENY:
            allowed = False
            reason = "network_denied"
        elif locality == "remote" and snapshot.effective.remote_data is RemoteDataMode.NEVER:
            allowed = False
            reason = "remote_data_forbidden"

        return CapabilityLease(
            capability=capability,
            locality=locality,
            allowed=allowed,
            reason_code=reason,
            snapshot_id=snapshot.snapshot_id,
            policy_version=snapshot.policy_version,
        )


_POLICY_KERNEL = PolicyKernel()


def get_policy_kernel() -> PolicyKernel:
    return _POLICY_KERNEL


def reset_policy_kernel() -> None:
    """Reset in-memory last-known policy state (primarily for isolated tests)."""
    global _POLICY_KERNEL
    _POLICY_KERNEL = PolicyKernel()


__all__ = [
    "CapabilityLease",
    "EffectivePolicy",
    "NetworkMode",
    "POLICY_VERSION",
    "PolicyDecision",
    "PolicyKernel",
    "PolicySnapshot",
    "RemoteDataMode",
    "get_policy_kernel",
    "reset_policy_kernel",
]
