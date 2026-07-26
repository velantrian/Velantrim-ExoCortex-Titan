"""PolicyKernel invariants for local-first capability authority."""
from __future__ import annotations


def test_default_snapshot_is_local_first_and_replayable():
    from core.policy_kernel import NetworkMode, PolicyKernel, RemoteDataMode

    kernel = PolicyKernel()
    first = kernel.capture_snapshot()
    second = kernel.capture_snapshot()

    assert first.effective.network is NetworkMode.DENY
    assert first.effective.remote_data is RemoteDataMode.NEVER
    assert first.effective.canonical_write_provider == "local"
    assert first.effective.remote_canonical_write_allowed is False
    assert first.effective.write_gate_required is True
    assert first.snapshot_id == second.snapshot_id


def test_network_deny_dominates_remote_capability():
    from core.policy_kernel import PolicyKernel

    lease = PolicyKernel().lease_capability(
        "embeddings",
        locality="remote",
        requires_network=True,
    )

    assert lease.allowed is False
    assert lease.reason_code == "network_denied"


def test_local_read_capability_is_allowed():
    from core.policy_kernel import PolicyKernel

    lease = PolicyKernel().lease_capability(
        "lexical_retrieval",
        locality="local",
        requires_network=False,
    )

    assert lease.allowed is True
    assert lease.reason_code == "ok"


def test_remote_canonical_write_is_never_leased():
    from core.policy_kernel import PolicyKernel

    lease = PolicyKernel().lease_capability(
        "canonical_write",
        locality="remote",
        requires_network=False,
    )

    assert lease.allowed is False
    assert lease.reason_code == "remote_canonical_write_forbidden"


def test_dependency_failure_uses_safe_default_and_denies(monkeypatch):
    from core.policy_kernel import PolicyKernel

    kernel = PolicyKernel()

    def _unavailable() -> str:
        raise RuntimeError("down")

    monkeypatch.setattr(kernel, "_supervisor_mode", _unavailable)
    snapshot = kernel.capture_snapshot()
    decision = kernel.canonical_write_decision()

    assert snapshot.source == "safe_default_fail_closed"
    assert snapshot.writes_allowed is False
    assert snapshot.reason_code == "policy_dependency_unavailable"
    assert decision.allowed is False
    assert decision.reason_code == "policy_dependency_unavailable"
