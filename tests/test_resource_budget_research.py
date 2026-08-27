"""Deterministic tests for the research-only resource budget prototype."""
from __future__ import annotations

from research.prototypes.resource_budget import (
    ComponentReservation,
    HostCapacity,
    evaluate_resource_budget,
)


def test_full_profile_fits() -> None:
    capacity = HostCapacity(ram_mb=16_384, cpu_cores=8, os_reserve_mb=2_048, cpu_reserve_cores=1)
    result = evaluate_resource_budget(
        capacity,
        [
            ComponentReservation("llm", ram_mb=6_000, cpu_cores=2.0),
            ComponentReservation("sqlite+indexes", ram_mb=1_000, cpu_cores=0.5),
            ComponentReservation("reader", ram_mb=1_000, cpu_cores=0.5, optional=True),
        ],
    )
    assert result.decision == "fit"
    assert result.mandatory_fit is True
    assert result.full_profile_fit is True
    assert result.suggested_disable == ()


def test_pressure_is_reported_without_disabling_components() -> None:
    capacity = HostCapacity(ram_mb=8_192, cpu_cores=4, os_reserve_mb=1_024, cpu_reserve_cores=0.5)
    result = evaluate_resource_budget(
        capacity,
        [
            ComponentReservation("llm", ram_mb=5_500, cpu_cores=2.0),
            ComponentReservation("indexes", ram_mb=800, cpu_cores=0.5),
        ],
        pressure_ratio=0.85,
    )
    assert result.decision == "pressure"
    assert result.full_profile_fit is True
    assert result.suggested_disable == ()


def test_exact_capacity_boundary_still_fits() -> None:
    capacity = HostCapacity(ram_mb=4_096, cpu_cores=4, os_reserve_mb=1_024, cpu_reserve_cores=1)
    result = evaluate_resource_budget(
        capacity,
        [ComponentReservation("core", ram_mb=3_072, cpu_cores=3.0)],
        pressure_ratio=1.0,
    )
    assert result.full_profile_fit is True
    assert result.mandatory_fit is True
    assert result.decision == "pressure"
    assert result.ram_utilization == 1.0
    assert result.cpu_utilization == 1.0


def test_optional_components_produce_advisory_downshift() -> None:
    capacity = HostCapacity(ram_mb=8_192, cpu_cores=4, os_reserve_mb=1_024, cpu_reserve_cores=0.5)
    result = evaluate_resource_budget(
        capacity,
        [
            ComponentReservation("core", ram_mb=3_500, cpu_cores=1.0),
            ComponentReservation("large-local-llm", ram_mb=4_500, cpu_cores=1.5, optional=True),
            ComponentReservation("shadow-analytics", ram_mb=800, cpu_cores=0.5, optional=True),
        ],
    )
    assert result.decision == "downshift"
    assert result.mandatory_fit is True
    assert result.full_profile_fit is False
    assert result.suggested_disable[0] == "large-local-llm"


def test_mandatory_profile_can_fail_closed() -> None:
    capacity = HostCapacity(ram_mb=4_096, cpu_cores=2, os_reserve_mb=1_024, cpu_reserve_cores=0.5)
    result = evaluate_resource_budget(
        capacity,
        [
            ComponentReservation("mandatory-core", ram_mb=3_500, cpu_cores=1.0),
            ComponentReservation("mandatory-provider", ram_mb=500, cpu_cores=1.0),
        ],
    )
    assert result.decision == "refuse"
    assert result.mandatory_fit is False
    assert result.full_profile_fit is False
    assert result.reason == "mandatory_profile_exceeds_capacity"


def test_zero_reservation_is_explicitly_allowed() -> None:
    capacity = HostCapacity(ram_mb=4_096, cpu_cores=2, os_reserve_mb=1_024, cpu_reserve_cores=0.5)
    result = evaluate_resource_budget(
        capacity,
        [ComponentReservation("marker", ram_mb=0, cpu_cores=0.0)],
    )
    assert result.decision == "fit"
    assert result.ram_required_mb == 0
    assert result.cpu_required_cores == 0.0


def test_evaluation_is_replay_deterministic() -> None:
    capacity = HostCapacity(ram_mb=8_192, cpu_cores=4, os_reserve_mb=1_024, cpu_reserve_cores=0.5)
    components = (
        ComponentReservation("core", ram_mb=3_000, cpu_cores=1.0),
        ComponentReservation("reader", ram_mb=1_000, cpu_cores=0.5, optional=True),
    )
    first = evaluate_resource_budget(capacity, components).to_dict()
    second = evaluate_resource_budget(capacity, components).to_dict()
    assert first == second


def test_invalid_capacity_component_and_ratio_are_rejected() -> None:
    invalid_factories = (
        lambda: HostCapacity(ram_mb=0, cpu_cores=1),
        lambda: HostCapacity(ram_mb=1024, cpu_cores=1, os_reserve_mb=1024),
        lambda: ComponentReservation("bad-ram", ram_mb=-1),
        lambda: ComponentReservation("bad-cpu", cpu_cores=-0.1),
        lambda: ComponentReservation("   "),
    )
    for factory in invalid_factories:
        try:
            factory()
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected invalid resource-budget input to raise")

    for ratio in (0, -0.1, 1.1):
        try:
            evaluate_resource_budget(
                HostCapacity(ram_mb=4096, cpu_cores=2),
                [],
                pressure_ratio=ratio,
            )
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError(f"expected invalid pressure_ratio={ratio} to raise")
