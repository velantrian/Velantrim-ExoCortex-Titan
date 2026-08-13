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

from core.policy_kernel import CapabilityLease, PolicyKernel

_LOCALITIES = frozenset({"local", "remote"})
_DATA_MODES = frozenset({"none", "redacted", "raw"})
_AUTO_PREFERENCE = "auto"


class ProviderHealthState(str, Enum):
    """Explicit availability state supplied to the registry."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ProviderDescriptor:
    """Stable provider identity and policy-relevant execution metadata.

    ``locality`` describes where the provider executes. A remote provider must declare
    ``requires_network=True`` so a descriptor cannot hide remote egress from PolicyKernel.
    ``data_mode`` is the maximum payload class the capability declaration expects to
    expose if selected; PolicyKernel remains authoritative for whether that is permitted.
    """

    provider_id: str
    locality: str
    requires_network: bool
    data_mode: str = "none"
    revision: str | None = None
    privacy_class: str = "default"

    def __post_init__(self) -> None:
        _require_token("provider_id", self.provider_id)
        _require_token("locality", self.locality)
        _require_token("data_mode", self.data_mode)
        _require_token("privacy_class", self.privacy_class)
        if self.locality not in _LOCALITIES:
            raise ValueError("locality must be local or remote")
        if self.data_mode not in _DATA_MODES:
            raise ValueError("data_mode must be none, redacted, or raw")
        if self.locality == "remote" and not self.requires_network:
            raise ValueError("remote providers must declare requires_network=True")
        if self.revision is not None:
            _require_token("revision", self.revision)


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Descriptive capability metadata with no execution authority."""

    capability_id: str
    kind: str
    provider_id: str
    model: str | None = None
    revision: str | None = None
    deterministic: bool = False
    resource_profile: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_token("capability_id", self.capability_id)
        _require_token("kind", self.kind)
        _require_token("provider_id", self.provider_id)
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
    """One explicit provider-health observation/configuration snapshot.

    The registry never probes providers. UNKNOWN is the default and is fail-closed for
    selection until a caller supplies health evidence through ``set_provider_health``.
    """

    state: ProviderHealthState
    reason_code: str

    def __post_init__(self) -> None:
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
    def unavailable(
        cls, reason_code: str = "provider_unavailable"
    ) -> ProviderHealth:
        return cls(ProviderHealthState.UNAVAILABLE, reason_code)


class CapabilityLeaser(Protocol):
    """Structural subset of PolicyKernel used by the registry."""

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
    """Reason-coded evaluation for one registered capability."""

    capability_id: str
    provider_id: str
    health_state: ProviderHealthState
    eligible: bool
    reason_code: str
    policy_snapshot_id: str | None = None
    policy_version: str | None = None

    def as_trace_metadata(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "provider_id": self.provider_id,
            "health": self.health_state.value,
            "eligible": self.eligible,
            "reason_code": self.reason_code,
            "policy_snapshot_id": self.policy_snapshot_id,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class SelectionResult:
    """Deterministic, replay-friendly selection explanation."""

    kind: str
    preference: str
    selected_capability_id: str | None
    reason_code: str
    candidates: tuple[CandidateEvaluation, ...]

    @property
    def selected(self) -> bool:
        return self.selected_capability_id is not None

    def as_trace_metadata(self) -> dict[str, Any]:
        """Return bounded metadata suitable for an existing AnalysisTrace owner.

        This method does not write or persist a trace. It only returns deterministic
        selection metadata for a future authorized caller to attach to its own trace.
        """

        return {
            "capability_kind": self.kind,
            "preference": self.preference,
            "selected_capability_id": self.selected_capability_id,
            "selection_reason_code": self.reason_code,
            "candidates": [candidate.as_trace_metadata() for candidate in self.candidates],
        }


class CapabilityRegistry:
    """In-memory descriptor/health registry with fail-closed selection.

    The registry snapshots its own descriptors and health under one lock, then delegates
    permission for every health-eligible candidate to the injected PolicyKernel-compatible
    owner. If policy evaluation errors or produces inconsistent snapshots during one
    selection, no capability is selected.
    """

    def __init__(self, policy_kernel: CapabilityLeaser | None = None) -> None:
        self._policy_kernel: CapabilityLeaser = policy_kernel or PolicyKernel()
        self._providers: dict[str, ProviderDescriptor] = {}
        self._capabilities: dict[str, CapabilityDescriptor] = {}
        self._health: dict[str, ProviderHealth] = {}
        self._lock = RLock()

    def register_provider(self, descriptor: ProviderDescriptor) -> None:
        with self._lock:
            if descriptor.provider_id in self._providers:
                raise ValueError(f"provider already registered: {descriptor.provider_id}")
            self._providers[descriptor.provider_id] = descriptor

    def register_capability(self, descriptor: CapabilityDescriptor) -> None:
        with self._lock:
            if descriptor.capability_id in self._capabilities:
                raise ValueError(
                    f"capability already registered: {descriptor.capability_id}"
                )
            if descriptor.provider_id not in self._providers:
                raise ValueError(
                    f"unknown provider for capability {descriptor.capability_id}: "
                    f"{descriptor.provider_id}"
                )
            self._capabilities[descriptor.capability_id] = descriptor

    def set_provider_health(self, provider_id: str, health: ProviderHealth) -> None:
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
            values = self._capabilities.values()
            if kind is not None:
                values = (item for item in values if item.kind == kind)
            return tuple(sorted(values, key=lambda item: item.capability_id))

    def provider_health(self, provider_id: str) -> ProviderHealth:
        with self._lock:
            if provider_id not in self._providers:
                raise ValueError(f"unknown provider: {provider_id}")
            return self._health.get(provider_id, ProviderHealth.unknown())

    def resolve(self, kind: str, *, preference: str = _AUTO_PREFERENCE) -> SelectionResult:
        """Resolve one allowed capability without granting permission itself.

        Selection order is intentionally conservative:

        1. only HEALTHY/DEGRADED providers can become eligible;
        2. every such candidate must receive an allowed PolicyKernel lease;
        3. all successful policy evaluations in this selection must agree on snapshot id
           and policy version, otherwise the whole selection fails closed;
        4. HEALTHY beats DEGRADED;
        5. an explicit preference is considered only after health/policy eligibility;
        6. local beats remote when otherwise equal;
        7. deterministic capability and capability id provide stable tie-breaking.

        Thus ``preference``/``auto`` can never weaken health or policy.
        """

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
            return SelectionResult(
                kind=kind,
                preference=preference,
                selected_capability_id=None,
                reason_code="no_registered_capability",
                candidates=(),
            )

        capability_ids = {item.capability_id for item in capabilities}
        if preference != _AUTO_PREFERENCE and preference not in capability_ids:
            return SelectionResult(
                kind=kind,
                preference=preference,
                selected_capability_id=None,
                reason_code="preferred_capability_unknown",
                candidates=(),
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
                        capability_id=capability.capability_id,
                        provider_id=provider.provider_id,
                        health_state=provider_health.state,
                        eligible=False,
                        reason_code="provider_health_unknown",
                    )
                )
                continue

            if provider_health.state is ProviderHealthState.UNAVAILABLE:
                evaluations.append(
                    CandidateEvaluation(
                        capability_id=capability.capability_id,
                        provider_id=provider.provider_id,
                        health_state=provider_health.state,
                        eligible=False,
                        reason_code=provider_health.reason_code,
                    )
                )
                continue

            try:
                lease = self._policy_kernel.lease_capability(
                    capability.capability_id,
                    locality=provider.locality,
                    requires_network=provider.requires_network,
                    data_mode=provider.data_mode,
                )
            except Exception:  # noqa: BLE001 - selection boundary must fail closed
                policy_error = True
                evaluations.append(
                    CandidateEvaluation(
                        capability_id=capability.capability_id,
                        provider_id=provider.provider_id,
                        health_state=provider_health.state,
                        eligible=False,
                        reason_code="policy_lease_error",
                    )
                )
                continue

            leases_by_capability[capability.capability_id] = lease
            evaluations.append(
                CandidateEvaluation(
                    capability_id=capability.capability_id,
                    provider_id=provider.provider_id,
                    health_state=provider_health.state,
                    eligible=lease.allowed,
                    reason_code=(
                        "candidate_allowed" if lease.allowed else lease.reason_code
                    ),
                    policy_snapshot_id=lease.snapshot_id,
                    policy_version=lease.policy_version,
                )
            )

        ordered_evaluations = tuple(
            sorted(evaluations, key=lambda item: item.capability_id)
        )

        if policy_error:
            return SelectionResult(
                kind=kind,
                preference=preference,
                selected_capability_id=None,
                reason_code="policy_evaluation_incomplete",
                candidates=ordered_evaluations,
            )

        snapshots = {
            (lease.snapshot_id, lease.policy_version)
            for lease in leases_by_capability.values()
        }
        if len(snapshots) > 1:
            return SelectionResult(
                kind=kind,
                preference=preference,
                selected_capability_id=None,
                reason_code="policy_snapshot_changed_during_selection",
                candidates=ordered_evaluations,
            )

        evaluation_by_id = {
            evaluation.capability_id: evaluation for evaluation in evaluations
        }
        eligible = [
            capability
            for capability in capabilities
            if evaluation_by_id[capability.capability_id].eligible
        ]
        if not eligible:
            return SelectionResult(
                kind=kind,
                preference=preference,
                selected_capability_id=None,
                reason_code="no_allowed_healthy_capability",
                candidates=ordered_evaluations,
            )

        def selection_key(capability: CapabilityDescriptor) -> tuple[int, int, int, int, str]:
            provider = providers[capability.provider_id]
            state = health.get(provider.provider_id, ProviderHealth.unknown()).state
            health_rank = 0 if state is ProviderHealthState.HEALTHY else 1
            preference_rank = (
                0
                if preference != _AUTO_PREFERENCE
                and capability.capability_id == preference
                else 1
            )
            locality_rank = 0 if provider.locality == "local" else 1
            deterministic_rank = 0 if capability.deterministic else 1
            return (
                health_rank,
                preference_rank,
                locality_rank,
                deterministic_rank,
                capability.capability_id,
            )

        selected = min(eligible, key=selection_key)
        selected_health = health.get(
            providers[selected.provider_id].provider_id,
            ProviderHealth.unknown(),
        ).state
        reason = (
            "selected_degraded_provider"
            if selected_health is ProviderHealthState.DEGRADED
            else "selected"
        )
        return SelectionResult(
            kind=kind,
            preference=preference,
            selected_capability_id=selected.capability_id,
            reason_code=reason,
            candidates=ordered_evaluations,
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
