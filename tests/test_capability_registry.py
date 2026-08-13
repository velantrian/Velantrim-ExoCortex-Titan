from __future__ import annotations

from dataclasses import replace

import pytest

from core.capability_registry import (
    CapabilityDescriptor,
    CapabilityRegistry,
    ProviderDescriptor,
    ProviderHealth,
    ProviderHealthState,
)
from core.policy_kernel import CapabilityLease


class FakeLeaser:
    def __init__(
        self,
        *,
        deny_remote: bool = False,
        raise_error: bool = False,
        changing_snapshot: bool = False,
    ) -> None:
        self.deny_remote = deny_remote
        self.raise_error = raise_error
        self.changing_snapshot = changing_snapshot
        self.calls: list[dict[str, object]] = []

    def lease_capability(
        self,
        capability: str,
        *,
        locality: str = "local",
        requires_network: bool = False,
        data_mode: str = "none",
    ) -> CapabilityLease:
        self.calls.append(
            {
                "capability": capability,
                "locality": locality,
                "requires_network": requires_network,
                "data_mode": data_mode,
            }
        )
        if self.raise_error:
            raise RuntimeError("policy unavailable")

        allowed = not (self.deny_remote and requires_network)
        reason = "ok" if allowed else "network_denied"
        snapshot_id = (
            f"snapshot-{len(self.calls)}"
            if self.changing_snapshot
            else "snapshot-stable"
        )
        return CapabilityLease(
            capability=capability,
            locality=locality,
            allowed=allowed,
            reason_code=reason,
            snapshot_id=snapshot_id,
            policy_version="test-policy-v1",
            data_mode=data_mode,
        )


def _local_provider(provider_id: str = "local-core") -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=provider_id,
        locality="local",
        requires_network=False,
    )


def _remote_provider(provider_id: str = "remote-provider") -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=provider_id,
        locality="remote",
        requires_network=True,
    )


def _capability(
    capability_id: str,
    *,
    kind: str = "analysis",
    provider_id: str = "local-core",
    data_mode: str = "none",
    deterministic: bool = True,
) -> CapabilityDescriptor:
    return CapabilityDescriptor(
        capability_id=capability_id,
        kind=kind,
        provider_id=provider_id,
        data_mode=data_mode,
        deterministic=deterministic,
    )


def test_remote_provider_cannot_hide_network_requirement() -> None:
    with pytest.raises(ValueError, match="requires_network=True"):
        ProviderDescriptor(
            provider_id="remote",
            locality="remote",
            requires_network=False,
        )


def test_descriptors_reject_ambiguous_or_duplicate_metadata() -> None:
    with pytest.raises(ValueError, match="trimmed"):
        _capability(" bad-id")

    with pytest.raises(ValueError, match="data_mode"):
        _capability("cap-invalid-data", data_mode="secret")

    with pytest.raises(ValueError, match="duplicate resource_profile key"):
        replace(
            _capability("cap-a"),
            resource_profile=(("ram", "small"), ("ram", "large")),
        )


def test_registry_rejects_duplicate_and_unknown_owners() -> None:
    registry = CapabilityRegistry(FakeLeaser())
    provider = _local_provider()
    registry.register_provider(provider)

    with pytest.raises(ValueError, match="provider already registered"):
        registry.register_provider(provider)

    with pytest.raises(ValueError, match="unknown provider"):
        registry.register_capability(
            _capability("cap-a", provider_id="missing-provider")
        )

    capability = _capability("cap-a")
    registry.register_capability(capability)
    with pytest.raises(ValueError, match="capability already registered"):
        registry.register_capability(capability)


def test_unknown_health_is_fail_closed_and_does_not_request_policy_lease() -> None:
    leaser = FakeLeaser()
    registry = CapabilityRegistry(leaser)
    registry.register_provider(_local_provider())
    registry.register_capability(_capability("local-analysis"))

    result = registry.resolve("analysis")

    assert result.selected is False
    assert result.reason_code == "no_allowed_healthy_capability"
    assert result.candidates[0].reason_code == "provider_health_unknown"
    assert result.candidates[0].health_reason_code == "provider_health_unknown"
    assert result.candidates[0].health_state is ProviderHealthState.UNKNOWN
    assert leaser.calls == []


def test_healthy_local_capability_is_selected_with_trace_ready_explanation() -> None:
    leaser = FakeLeaser()
    registry = CapabilityRegistry(leaser)
    registry.register_provider(_local_provider())
    registry.register_capability(_capability("local-analysis"))
    registry.set_provider_health("local-core", ProviderHealth.healthy())

    result = registry.resolve("analysis")
    metadata = result.as_trace_metadata()

    assert result.selected_capability_id == "local-analysis"
    assert result.reason_code == "selected"
    assert metadata["selection_reason_code"] == "selected"
    assert metadata["selected_capability_id"] == "local-analysis"
    assert metadata["candidates"][0]["health_reason_code"] == "provider_healthy"
    assert metadata["candidates"][0]["policy_snapshot_id"] == "snapshot-stable"
    assert leaser.calls == [
        {
            "capability": "local-analysis",
            "locality": "local",
            "requires_network": False,
            "data_mode": "none",
        }
    ]


def test_capability_data_mode_is_forwarded_to_existing_policy_owner() -> None:
    leaser = FakeLeaser()
    registry = CapabilityRegistry(leaser)
    registry.register_provider(_remote_provider())
    registry.register_capability(
        _capability(
            "remote-redacted-analysis",
            provider_id="remote-provider",
            data_mode="redacted",
        )
    )
    registry.set_provider_health("remote-provider", ProviderHealth.healthy())

    result = registry.resolve("analysis")

    assert result.selected_capability_id == "remote-redacted-analysis"
    assert leaser.calls == [
        {
            "capability": "remote-redacted-analysis",
            "locality": "remote",
            "requires_network": True,
            "data_mode": "redacted",
        }
    ]


def test_explicit_remote_preference_cannot_override_policy_denial() -> None:
    leaser = FakeLeaser(deny_remote=True)
    registry = CapabilityRegistry(leaser)
    registry.register_provider(_local_provider())
    registry.register_provider(_remote_provider())
    registry.register_capability(_capability("local-analysis"))
    registry.register_capability(
        _capability(
            "remote-analysis",
            provider_id="remote-provider",
            data_mode="redacted",
            deterministic=False,
        )
    )
    registry.set_provider_health("local-core", ProviderHealth.healthy())
    registry.set_provider_health("remote-provider", ProviderHealth.healthy())

    result = registry.resolve("analysis", preference="remote-analysis")

    assert result.selected_capability_id == "local-analysis"
    assert result.reason_code == "selected"
    by_id = {item.capability_id: item for item in result.candidates}
    assert by_id["remote-analysis"].eligible is False
    assert by_id["remote-analysis"].reason_code == "network_denied"
    assert by_id["local-analysis"].eligible is True


def test_unavailable_preferred_provider_downgrades_to_healthy_local() -> None:
    registry = CapabilityRegistry(FakeLeaser())
    registry.register_provider(_local_provider())
    registry.register_provider(_remote_provider())
    registry.register_capability(_capability("local-analysis"))
    registry.register_capability(
        _capability("remote-analysis", provider_id="remote-provider")
    )
    registry.set_provider_health("local-core", ProviderHealth.healthy())
    registry.set_provider_health(
        "remote-provider",
        ProviderHealth.unavailable("provider_circuit_open"),
    )

    result = registry.resolve("analysis", preference="remote-analysis")

    assert result.selected_capability_id == "local-analysis"
    by_id = {item.capability_id: item for item in result.candidates}
    assert by_id["remote-analysis"].reason_code == "provider_circuit_open"
    assert by_id["remote-analysis"].health_reason_code == "provider_circuit_open"


def test_healthy_candidate_beats_degraded_preference() -> None:
    registry = CapabilityRegistry(FakeLeaser())
    registry.register_provider(_local_provider("healthy-provider"))
    registry.register_provider(_local_provider("degraded-provider"))
    registry.register_capability(
        _capability("healthy-cap", provider_id="healthy-provider")
    )
    registry.register_capability(
        _capability("degraded-cap", provider_id="degraded-provider")
    )
    registry.set_provider_health("healthy-provider", ProviderHealth.healthy())
    registry.set_provider_health(
        "degraded-provider",
        ProviderHealth.degraded("provider_slow"),
    )

    result = registry.resolve("analysis", preference="degraded-cap")

    assert result.selected_capability_id == "healthy-cap"
    assert result.reason_code == "selected"
    degraded = next(
        item for item in result.candidates if item.capability_id == "degraded-cap"
    )
    assert degraded.health_reason_code == "provider_slow"


def test_degraded_candidate_can_be_selected_when_it_is_the_only_allowed_option() -> None:
    registry = CapabilityRegistry(FakeLeaser())
    registry.register_provider(_local_provider())
    registry.register_capability(_capability("local-analysis"))
    registry.set_provider_health("local-core", ProviderHealth.degraded("provider_slow"))

    result = registry.resolve("analysis")

    assert result.selected_capability_id == "local-analysis"
    assert result.reason_code == "selected_degraded_provider"
    assert result.candidates[0].health_reason_code == "provider_slow"


def test_policy_exception_fails_whole_selection_closed() -> None:
    registry = CapabilityRegistry(FakeLeaser(raise_error=True))
    registry.register_provider(_local_provider())
    registry.register_capability(_capability("local-analysis"))
    registry.set_provider_health("local-core", ProviderHealth.healthy())

    result = registry.resolve("analysis")

    assert result.selected is False
    assert result.reason_code == "policy_evaluation_incomplete"
    assert result.candidates[0].reason_code == "policy_lease_error"


def test_policy_snapshot_change_during_selection_fails_closed() -> None:
    registry = CapabilityRegistry(FakeLeaser(changing_snapshot=True))
    registry.register_provider(_local_provider("provider-a"))
    registry.register_provider(_local_provider("provider-b"))
    registry.register_capability(_capability("cap-a", provider_id="provider-a"))
    registry.register_capability(_capability("cap-b", provider_id="provider-b"))
    registry.set_provider_health("provider-a", ProviderHealth.healthy())
    registry.set_provider_health("provider-b", ProviderHealth.healthy())

    result = registry.resolve("analysis")

    assert result.selected is False
    assert result.reason_code == "policy_snapshot_changed_during_selection"


def test_unknown_explicit_preference_is_not_silently_ignored() -> None:
    leaser = FakeLeaser()
    registry = CapabilityRegistry(leaser)
    registry.register_provider(_local_provider())
    registry.register_capability(_capability("local-analysis"))
    registry.set_provider_health("local-core", ProviderHealth.healthy())

    result = registry.resolve("analysis", preference="missing-capability")

    assert result.selected is False
    assert result.reason_code == "preferred_capability_unknown"
    assert result.candidates == ()
    assert leaser.calls == []
