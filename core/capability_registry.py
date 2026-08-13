"""Bounded capability/provider registry for Titan Phase 2A.

This module is deliberately *not* a policy engine, runtime router, provider client,
or activation surface. It owns only descriptive metadata, explicit provider-health
snapshots, and deterministic selection explanations.

Permission remains owned by :mod:`core.policy_kernel`. Every candidate that is healthy
enough to be considered must receive a ``CapabilityLease`` from that existing owner.
A preference such as ``auto`` or a preferred capability id can change ordering only; it
can never turn a denied lease into permission.

The registry is currently unwired. Callers must instantiate it explicitly. It performs
no network I/O, no model/provider invocation, no Canon mutation, and no background work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Protocol

from core.policy_kernel import CapabilityLease, get_policy_kernel

_LOCALITIES = frozenset({"local", "remote"})
_DATA_MODES = frozenset({"none", "redacted", "raw"})
_AUTO_PREFERENCE = "auto"


class ProviderHealthState(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    locality: str
    requires_network: bool
    revision: str | None = None
    privacy_class: str = "default"

    def __post_init__(self) -> None:
        _require_token("provider_id", self.provider_id)
        _require_token("locality", self.locality)
        _require_token("privacy_class", self.privacy_class)
        if not isinstance(self.requires_network, bool):
            raise ValueError("requires_network must be bool")
        if self.locality not in _LOCALITIES:
            raise ValueError("locality must be local or remote")
        if self.locality == "remote" and not self.requires_network:
            raise ValueError("remote providers must declare requires_network=True")
        if self.revision is not None:
            _require_token("revision", self.revision)


@dataclass(frozen=True)
class CapabilityDescriptor:
    capability_id: str
    kind: str
    provider_id: str
    model: str | None = None
    revision: str | None = None
    data_mode: str = "none"
    deterministic: bool = False
    resource_profile: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_token("capability_id", self.capability_id)
        _require_token("kind", self.kind)
        _require_token("provider_id", self.provider_id)
        _require_token("data_mode", self.data_mode)
        if self.data_mode not in _DATA_MODES:
            raise ValueError("data_mode must be none, redacted, or raw")
        if not isinstance(self.deterministic, bool):
            raise ValueError("deterministic must be bool")
        if self.model is not None:
            _require_token("model", self.model)
        if self.revision is not None:
            _require_token("revision", self.revision)
        keys: set[str] = set()
        for key, value in self.resource_profile:
            _require_token("resource_profile key", key)
            _require_token("resource_profile value", value)
            if key in keys:
                raise ValueError(f"duplicate resource_profile key: {key}")
            keys.add(key)


@dataclass(frozen=True)
class ProviderHealth:
    state: ProviderHealthState
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, ProviderHealthState):
            raise ValueError("state must be ProviderHealthState")
        _require_token("reason_code", self.reason_code)

    @classmethod
    def unknown(cls) -> ProviderHealth:
        return cls(ProviderHealthState.UNKNOWN, "provider_health_unknown")

    @classmethod
    def healthy(cls) -> ProviderHealth:
        return cls(ProviderHealthState.HEALTHY, "provider_healthy")

    @classmethod
    def degraded(cls, reason_code: str = "provider_degraded") -> ProviderHealth:
        return cls(ProviderHealthState.DEGRADED, reason_code)

    @classmethod
    def unavailable(cls, reason_code: str = "provider_unavailable") -> ProviderHealth:
        return cls(ProviderHealthState.UNAVAILABLE, reason_code)


class CapabilityLeaser(Protocol):
    def lease_capability(
        self,
        capability: str,
        *,
        locality: str = "local",
        requires_network: bool = False,
        data_mode: str = "none",
    ) -> CapabilityLease: ...


@dataclass(frozen=True)
class CandidateEvaluation:
    capability_id: str
    provider_id: str
    health_state: ProviderHealthState
    health_reason_code: str
    eligible: bool
    reason_code: str
    policy_snapshot_id: str | None = None
    policy_version: str | None = None

    def as_trace_metadata(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "provider_id": self.provider_id,
            "health": self.health_state.value,
            "health_reason_code": self.health_reason_code,
            "eligible": self.eligible,
            "reason_code": self.reason_code,
            "policy_snapshot_id": self.policy_snapshot_id,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class SelectionResult:
    kind: str
    preference: str
    selected_capability_id: str | None
    reason_code: str
    candidates: tuple[CandidateEvaluation, ...]

    @property
    def selected(self) -> bool:
        return self.selected_capability_id is not None

    def as_trace_metadata(self) -> dict[str, Any]:
        return {
            "capability_kind": self.kind,
            "preference": self.preference,
            "selected_capability_id": self.selected_capability_id,
            "selection_reason_code": self.reason_code,
            "candidates": [candidate.as_trace_metadata() for candidate in self.candidates],
        }


class CapabilityRegistry:
    """Unwired descriptor/health registry that delegates all permission to PolicyKernel."""

    def __init__(self, policy_kernel: CapabilityLeaser | None = None) -> None:
        self._policy_kernel: CapabilityLeaser = (
            policy_kernel if policy_kernel is not None else get_policy_kernel()
        )
        self._providers: dict[str, ProviderDescriptor] = {}
        self._capabilities: dict[str, CapabilityDescriptor] = {}
        self._health: dict[str, ProviderHealth] = {}
        self._lock = RLock()

    def register_provider(self, descriptor: ProviderDescriptor) -> None:
        if not isinstance(descriptor, ProviderDescriptor):
            raise ValueError("descriptor must be ProviderDescriptor")
        with self._lock:
            if descriptor.provider_id in self._providers:
                raise ValueError(f"provider already registered: {descriptor.provider_id}")
            self._providers[descriptor.provider_id] = descriptor

    def register_capability(self, descriptor: CapabilityDescriptor) -> None:
        if not isinstance(descriptor, CapabilityDescriptor):
            raise ValueError("descriptor must be CapabilityDescriptor")
        with self._lock:
            if descriptor.capability_id in self._capabilities:
                raise ValueError(f"capability already registered: {descriptor.capability_id}")
            if descriptor.provider_id not in self._providers:
                raise ValueError(
                    f"unknown provider for capability {descriptor.capability_id}: "
                    f"{descriptor.provider_id}"
                )
            self._capabilities[descriptor.capability_id] = descriptor

    def set_provider_health(self, provider_id: str, health: ProviderHealth) -> None:
        _require_token("provider_id", provider_id)
        if not isinstance(health, ProviderHealth):
            raise ValueError("health must be ProviderHealth")
        with self._lock:
            if provider_id not in self._providers:
                raise ValueError(f"unknown provider: {provider_id}")
            self._health[provider_id] = health

    def list_providers(self) -> tuple[ProviderDescriptor, ...]:
        with self._lock:
            return tuple(self._providers[key] for key in sorted(self._providers))

    def list_capabilities(
        self, *, kind: str | None = None
    ) -> tuple[CapabilityDescriptor, ...]:
        if kind is not None:
            _require_token("kind", kind)
        with self._lock:
            items = tuple(self._capabilities.values())
        if kind is not None:
            items = tuple(item for item in items if item.kind == kind)
        return tuple(sorted(items, key=lambda item: item.capability_id))

    def provider_health(self, provider_id: str) -> ProviderHealth:
        _require_token("provider_id", provider_id)
        with self._lock:
            if provider_id not in self._providers:
                raise ValueError(f"unknown provider: {provider_id}")
            return self._health.get(provider_id, ProviderHealth.unknown())

    def resolve(self, kind: str, *, preference: str = _AUTO_PREFERENCE) -> SelectionResult:
        _require_token("kind", kind)
        _require_token("preference", preference)

        with self._lock:
            providers = dict(self._providers)
            health = dict(self._health)
            capabilities = tuple(
                sorted(
                    (item for item in self._capabilities.values() if item.kind == kind),
                    key=lambda item: item.capability_id,
                )
            )

        if not capabilities:
            return SelectionResult(kind, preference, None, "no_registered_capability", ())

        capability_ids = {item.capability_id for item in capabilities}
        if preference != _AUTO_PREFERENCE and preference not in capability_ids:
            return SelectionResult(
                kind, preference, None, "preferred_capability_unknown", ()
            )

        evaluations: list[CandidateEvaluation] = []
        leases_by_capability: dict[str, CapabilityLease] = {}
        policy_error = False

        for capability in capabilities:
            provider = providers[capability.provider_id]
            provider_health = health.get(provider.provider_id, ProviderHealth.unknown())

            if provider_health.state is ProviderHealthState.UNKNOWN:
                evaluations.append(
                    CandidateEvaluation(
                        capability.capability_id,
                        provider.provider_id,
                        provider_health.state,
                        provider_health.reason_code,
                        False,
                        "provider_health_unknown",
                    )
                )
                continue

            if provider_health.state is ProviderHealthState.UNAVAILABLE:
                evaluations.append(
                    CandidateEvaluation(
                        capability.capability_id,
                        provider.provider_id,
                        provider_health.state,
                        provider_health.reason_code,
                        False,
                        provider_health.reason_code,
                    )
                )
                continue

            try:
                lease = self._policy_kernel.lease_capability(
                    capability.capability_id,
                    locality=provider.locality,
                    requires_network=provider.requires_network,
                    data_mode=capability.data_mode,
                )
            except Exception:  # noqa: BLE001 - boundary must fail closed
                policy_error = True
                evaluations.append(
                    CandidateEvaluation(
                        capability.capability_id,
                        provider.provider_id,
                        provider_health.state,
                        provider_health.reason_code,
                        False,
                        "policy_lease_error",
                    )
                )
                continue

            leases_by_capability[capability.capability_id] = lease
            evaluations.append(
                CandidateEvaluation(
                    capability.capability_id,
                    provider.provider_id,
                    provider_health.state,
                    provider_health.reason_code,
                    lease.allowed,
                    "candidate_allowed" if lease.allowed else lease.reason_code,
                    lease.snapshot_id,
                    lease.policy_version,
                )
            )

        ordered_evaluations = tuple(sorted(evaluations, key=lambda item: item.capability_id))
        if policy_error:
            return SelectionResult(
                kind,
                preference,
                None,
                "policy_evaluation_incomplete",
                ordered_evaluations,
            )

        snapshots = {
            (lease.snapshot_id, lease.policy_version)
            for lease in leases_by_capability.values()
        }
        if len(snapshots) > 1:
            return SelectionResult(
                kind,
                preference,
                None,
                "policy_snapshot_changed_during_selection",
                ordered_evaluations,
            )

        evaluation_by_id = {item.capability_id: item for item in evaluations}
        eligible = [
            capability
            for capability in capabilities
            if evaluation_by_id[capability.capability_id].eligible
        ]
        if not eligible:
            return SelectionResult(
                kind,
                preference,
                None,
                "no_allowed_healthy_capability",
                ordered_evaluations,
            )

        def selection_key(
            capability: CapabilityDescriptor,
        ) -> tuple[int, int, int, int, str]:
            provider = providers[capability.provider_id]
            state = health.get(provider.provider_id, ProviderHealth.unknown()).state
            return (
                0 if state is ProviderHealthState.HEALTHY else 1,
                0
                if preference != _AUTO_PREFERENCE
                and capability.capability_id == preference
                else 1,
                0 if provider.locality == "local" else 1,
                0 if capability.deterministic else 1,
                capability.capability_id,
            )

        selected = min(eligible, key=selection_key)
        selected_health = health.get(
            providers[selected.provider_id].provider_id, ProviderHealth.unknown()
        ).state
        reason = (
            "selected_degraded_provider"
            if selected_health is ProviderHealthState.DEGRADED
            else "selected"
        )
        return SelectionResult(
            kind,
            preference,
            selected.capability_id,
            reason,
            ordered_evaluations,
        )


def _require_token(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty trimmed string")


__all__ = [
    "CandidateEvaluation",
    "CapabilityDescriptor",
    "CapabilityLeaser",
    "CapabilityRegistry",
    "ProviderDescriptor",
    "ProviderHealth",
    "ProviderHealthState",
    "SelectionResult",
]
