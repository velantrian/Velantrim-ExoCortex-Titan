from __future__ import annotations

from unittest.mock import patch

import pytest

from core.capability_registry import (
    CapabilityDescriptor,
    CapabilityRegistry,
    ProviderDescriptor,
    ProviderHealth,
)
from core.policy_kernel import CapabilityLease


class FakeLeaser:
    def __init__(self, *, deny_remote=False, fail=False, changing=False):
        self.deny_remote = deny_remote
        self.fail = fail
        self.changing = changing
        self.calls: list[dict[str, object]] = []

    def lease_capability(
        self,
        capability: str,
        *,
        locality: str = "local",
        requires_network: bool = False,
        data_mode: str = "none",
    ) -> CapabilityLease:
        self.calls.append({"capability": capability, "network": requires_network, "data_mode": data_mode})
        if self.fail:
            raise RuntimeError("policy unavailable")
        allowed = not (self.deny_remote and requires_network)
        return CapabilityLease(
            capability=capability,
            locality=locality,
            allowed=allowed,
            reason_code="ok" if allowed else "network_denied",
            snapshot_id=f"s{len(self.calls)}" if self.changing else "stable",
            policy_version="test-v1",
            data_mode=data_mode,
        )


def registry(leaser: FakeLeaser | None = None) -> CapabilityRegistry:
    with patch("core.capability_registry.get_policy_kernel", return_value=leaser or FakeLeaser()):
        return CapabilityRegistry()


def local(provider_id="local") -> ProviderDescriptor:
    return ProviderDescriptor(provider_id, "local", False)


def remote(provider_id="remote") -> ProviderDescriptor:
    return ProviderDescriptor(provider_id, "remote", True)


def cap(capability_id, provider_id="local", *, data_mode="none") -> CapabilityDescriptor:
    return CapabilityDescriptor(capability_id, "analysis", provider_id, data_mode=data_mode, deterministic=True)


def test_policy_owner_is_not_constructor_injectable() -> None:
    with pytest.raises(TypeError):
        CapabilityRegistry(FakeLeaser())  # type: ignore[call-arg]


def test_descriptor_validation_and_unknown_health_fail_closed() -> None:
    with pytest.raises(ValueError, match="requires_network=True"):
        ProviderDescriptor("r", "remote", False)
    with pytest.raises(ValueError, match="data_mode"):
        cap("bad", data_mode="secret")
    r = registry()
    r.register_provider(local())
    r.register_capability(cap("local-cap"))
    result = r.resolve("analysis")
    assert not result.selected
    assert result.candidates[0].health_reason_code == "provider_health_unknown"


def test_healthy_selection_preserves_policy_and_health_evidence() -> None:
    fake = FakeLeaser()
    r = registry(fake)
    r.register_provider(local())
    r.register_capability(cap("local-cap"))
    r.set_provider_health("local", ProviderHealth.healthy())
    result = r.resolve("analysis")
    metadata = result.as_trace_metadata()
    assert result.selected_capability_id == "local-cap"
    assert metadata["candidates"][0]["health_reason_code"] == "provider_healthy"
    assert metadata["candidates"][0]["policy_snapshot_id"] == "stable"


def test_capability_data_mode_reaches_existing_policy_owner() -> None:
    fake = FakeLeaser()
    r = registry(fake)
    r.register_provider(remote())
    r.register_capability(cap("remote-cap", "remote", data_mode="redacted"))
    r.set_provider_health("remote", ProviderHealth.healthy())
    assert r.resolve("analysis").selected_capability_id == "remote-cap"
    assert fake.calls == [{"capability": "remote-cap", "network": True, "data_mode": "redacted"}]


def test_remote_preference_cannot_override_policy_denial() -> None:
    fake = FakeLeaser(deny_remote=True)
    r = registry(fake)
    r.register_provider(local())
    r.register_provider(remote())
    r.register_capability(cap("local-cap"))
    r.register_capability(cap("remote-cap", "remote", data_mode="redacted"))
    r.set_provider_health("local", ProviderHealth.healthy())
    r.set_provider_health("remote", ProviderHealth.healthy())
    result = r.resolve("analysis", preference="remote-cap")
    by_id = {item.capability_id: item for item in result.candidates}
    assert result.selected_capability_id == "local-cap"
    assert by_id["remote-cap"].reason_code == "network_denied"


def test_unavailable_and_degraded_health_are_bounded() -> None:
    r = registry()
    r.register_provider(local("healthy"))
    r.register_provider(local("degraded"))
    r.register_capability(cap("healthy-cap", "healthy"))
    r.register_capability(cap("degraded-cap", "degraded"))
    r.set_provider_health("healthy", ProviderHealth.healthy())
    r.set_provider_health("degraded", ProviderHealth.degraded("provider_slow"))
    result = r.resolve("analysis", preference="degraded-cap")
    assert result.selected_capability_id == "healthy-cap"
    degraded = next(item for item in result.candidates if item.capability_id == "degraded-cap")
    assert degraded.health_reason_code == "provider_slow"


def test_policy_exception_fails_whole_selection_closed() -> None:
    r = registry(FakeLeaser(fail=True))
    r.register_provider(local())
    r.register_capability(cap("local-cap"))
    r.set_provider_health("local", ProviderHealth.healthy())
    result = r.resolve("analysis")
    assert not result.selected
    assert result.reason_code == "policy_evaluation_incomplete"


def test_mixed_policy_snapshots_fail_closed() -> None:
    r = registry(FakeLeaser(changing=True))
    r.register_provider(local("a"))
    r.register_provider(local("b"))
    r.register_capability(cap("a-cap", "a"))
    r.register_capability(cap("b-cap", "b"))
    r.set_provider_health("a", ProviderHealth.healthy())
    r.set_provider_health("b", ProviderHealth.healthy())
    result = r.resolve("analysis")
    assert not result.selected
    assert result.reason_code == "policy_snapshot_changed_during_selection"
