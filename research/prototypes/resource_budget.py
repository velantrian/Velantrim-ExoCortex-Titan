"""Deterministic multi-component resource budget prototype.

Research-only.  This module is intentionally not imported by Titan startup, query
routing, ComputeController or any write path.  It explores whether a simple explicit
budget can replace the historical single-component "memory node count" intuition when
planning a local runtime profile.

The prototype has no hardware probing and no activation authority.  Callers provide a
capacity snapshot and component reservations, making replay deterministic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HostCapacity:
    ram_mb: int
    cpu_cores: float
    os_reserve_mb: int = 1024
    cpu_reserve_cores: float = 0.5

    def __post_init__(self) -> None:
        if self.ram_mb <= 0:
            raise ValueError("ram_mb must be > 0")
        if self.cpu_cores <= 0:
            raise ValueError("cpu_cores must be > 0")
        if self.os_reserve_mb < 0 or self.os_reserve_mb >= self.ram_mb:
            raise ValueError("os_reserve_mb must be >= 0 and < ram_mb")
        if self.cpu_reserve_cores < 0 or self.cpu_reserve_cores >= self.cpu_cores:
            raise ValueError("cpu_reserve_cores must be >= 0 and < cpu_cores")

    @property
    def usable_ram_mb(self) -> int:
        return self.ram_mb - self.os_reserve_mb

    @property
    def usable_cpu_cores(self) -> float:
        return self.cpu_cores - self.cpu_reserve_cores


@dataclass(frozen=True)
class ComponentReservation:
    name: str
    ram_mb: int = 0
    cpu_cores: float = 0.0
    optional: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("component name is required")
        if self.ram_mb < 0:
            raise ValueError("component ram_mb must be >= 0")
        if self.cpu_cores < 0:
            raise ValueError("component cpu_cores must be >= 0")


@dataclass(frozen=True)
class BudgetEvaluation:
    decision: str
    ram_required_mb: int
    cpu_required_cores: float
    ram_utilization: float
    cpu_utilization: float
    mandatory_fit: bool
    full_profile_fit: bool
    suggested_disable: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def _fits(capacity: HostCapacity, components: list[ComponentReservation]) -> bool:
    return (
        sum(item.ram_mb for item in components) <= capacity.usable_ram_mb
        and sum(item.cpu_cores for item in components) <= capacity.usable_cpu_cores
    )


def evaluate_resource_budget(
    capacity: HostCapacity,
    components: list[ComponentReservation] | tuple[ComponentReservation, ...],
    *,
    pressure_ratio: float = 0.85,
) -> BudgetEvaluation:
    """Evaluate a supplied local runtime profile without changing runtime state.

    Decisions:
    - ``fit``: the full requested profile fits below the pressure threshold;
    - ``pressure``: it fits, but RAM or CPU reservation is near capacity;
    - ``downshift``: mandatory components fit but optional components do not;
    - ``refuse``: mandatory components alone exceed supplied capacity.

    The function never disables anything itself; ``suggested_disable`` is advisory.
    """

    if not 0.0 < pressure_ratio <= 1.0:
        raise ValueError("pressure_ratio must be in (0, 1]")

    items = list(components)
    mandatory = [item for item in items if not item.optional]
    optional = [item for item in items if item.optional]

    ram_required = sum(item.ram_mb for item in items)
    cpu_required = sum(item.cpu_cores for item in items)
    ram_util = ram_required / capacity.usable_ram_mb
    cpu_util = cpu_required / capacity.usable_cpu_cores

    mandatory_fit = _fits(capacity, mandatory)
    full_fit = _fits(capacity, items)

    if not mandatory_fit:
        return BudgetEvaluation(
            decision="refuse",
            ram_required_mb=ram_required,
            cpu_required_cores=round(cpu_required, 4),
            ram_utilization=round(ram_util, 4),
            cpu_utilization=round(cpu_util, 4),
            mandatory_fit=False,
            full_profile_fit=False,
            suggested_disable=(),
            reason="mandatory_profile_exceeds_capacity",
        )

    if not full_fit:
        # Largest optional reservations first gives the operator the shortest likely
        # path to a fitting profile.  This is a suggestion, not an automatic action.
        disabled: list[str] = []
        remaining = list(items)
        for candidate in sorted(
            optional,
            key=lambda item: (item.ram_mb, item.cpu_cores, item.name),
            reverse=True,
        ):
            disabled.append(candidate.name)
            remaining = [item for item in remaining if item.name != candidate.name]
            if _fits(capacity, remaining):
                break
        return BudgetEvaluation(
            decision="downshift",
            ram_required_mb=ram_required,
            cpu_required_cores=round(cpu_required, 4),
            ram_utilization=round(ram_util, 4),
            cpu_utilization=round(cpu_util, 4),
            mandatory_fit=True,
            full_profile_fit=False,
            suggested_disable=tuple(disabled),
            reason="optional_components_exceed_capacity",
        )

    pressure = max(ram_util, cpu_util) >= pressure_ratio
    return BudgetEvaluation(
        decision="pressure" if pressure else "fit",
        ram_required_mb=ram_required,
        cpu_required_cores=round(cpu_required, 4),
        ram_utilization=round(ram_util, 4),
        cpu_utilization=round(cpu_util, 4),
        mandatory_fit=True,
        full_profile_fit=True,
        suggested_disable=(),
        reason="near_capacity" if pressure else "profile_fits",
    )


__all__ = [
    "BudgetEvaluation",
    "ComponentReservation",
    "HostCapacity",
    "evaluate_resource_budget",
]
