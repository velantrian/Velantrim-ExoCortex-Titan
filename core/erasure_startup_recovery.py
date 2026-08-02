"""Typed contracts for bounded GDPR erasure recovery at application startup.

This module deliberately does not execute recovery, open a database, register a
scheduler, or modify server startup. It defines the budget and receipt contract
that the later coordinator/runtime wiring must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from core.runtime_evidence import ObservationResult, ObservationState


ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION = "titan.erasure-startup-recovery.v1"


class ErasureStartupRecoveryError(ValueError):
    """Raised when a startup-recovery contract violates its invariants."""


class RecoveryDomain(str, Enum):
    SINGLE_FACT = "single_fact"
    BATCH = "batch"


def _required_text(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ErasureStartupRecoveryError(f"{name} must be non-empty")
    return normalized


def _nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ErasureStartupRecoveryError(f"{name} must be a non-negative integer")
    return value


def _positive_int(value: int, name: str) -> int:
    value = _nonnegative_int(value, name)
    if value == 0:
        raise ErasureStartupRecoveryError(f"{name} must be greater than zero")
    return value


def _canonical_codes(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({_required_text(value, "error_code") for value in values}))


def _utc(value: str, name: str) -> datetime:
    text = _required_text(value, name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ErasureStartupRecoveryError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ErasureStartupRecoveryError(f"{name} must be UTC")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class StartupRecoveryBudget:
    """Hard startup bounds; exhaustive operator recovery remains separate."""

    max_single_jobs: int = 25
    max_batches: int = 5
    time_budget_ms: int = 5_000
    schema_version: str = ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        single = _nonnegative_int(self.max_single_jobs, "max_single_jobs")
        batches = _nonnegative_int(self.max_batches, "max_batches")
        _positive_int(self.time_budget_ms, "time_budget_ms")
        if single == 0 and batches == 0:
            raise ErasureStartupRecoveryError(
                "at least one recovery domain must have a positive item budget"
            )
        if self.schema_version != ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION:
            raise ErasureStartupRecoveryError("unsupported startup recovery schema")


@dataclass(frozen=True, slots=True)
class RecoveryDomainReceipt:
    """Measured outcome for one recovery domain within one bounded run."""

    domain: RecoveryDomain
    selected: int
    attempted: int
    completed: int
    partial: int
    failed: int
    skipped: int
    remaining_backlog: int
    error_codes: tuple[str, ...] = ()
    schema_version: str = ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.domain, RecoveryDomain):
            raise ErasureStartupRecoveryError("domain must be a RecoveryDomain")
        values = {
            name: _nonnegative_int(getattr(self, name), name)
            for name in (
                "selected",
                "attempted",
                "completed",
                "partial",
                "failed",
                "skipped",
                "remaining_backlog",
            )
        }
        if values["attempted"] > values["selected"]:
            raise ErasureStartupRecoveryError("attempted cannot exceed selected")
        unattempted = values["selected"] - values["attempted"]
        if values["remaining_backlog"] < unattempted:
            raise ErasureStartupRecoveryError(
                "remaining_backlog must include every selected but unattempted item"
            )
        terminal_accounting = (
            values["completed"]
            + values["partial"]
            + values["failed"]
            + values["skipped"]
        )
        if terminal_accounting != values["attempted"]:
            raise ErasureStartupRecoveryError(
                "completed + partial + failed + skipped must equal attempted"
            )
        codes = _canonical_codes(self.error_codes)
        if values["failed"] > 0 and not codes:
            raise ErasureStartupRecoveryError(
                "failed recovery outcomes require at least one error_code"
            )
        if values["failed"] == 0 and codes:
            raise ErasureStartupRecoveryError(
                "error_codes require at least one failed recovery outcome"
            )
        if self.schema_version != ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION:
            raise ErasureStartupRecoveryError("unsupported startup recovery schema")
        object.__setattr__(self, "error_codes", codes)

    @property
    def unresolved_count(self) -> int:
        return self.partial + self.failed + self.remaining_backlog

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "domain": self.domain.value,
            "selected": self.selected,
            "attempted": self.attempted,
            "completed": self.completed,
            "partial": self.partial,
            "failed": self.failed,
            "skipped": self.skipped,
            "remaining_backlog": self.remaining_backlog,
            "error_codes": list(self.error_codes),
            "unresolved_count": self.unresolved_count,
        }


@dataclass(frozen=True, slots=True)
class StartupRecoveryReceipt:
    """Truthful aggregate receipt for one bounded startup recovery run."""

    run_id: str
    started_at_utc: str
    completed_at_utc: str
    budget: StartupRecoveryBudget
    single_fact: RecoveryDomainReceipt
    batch: RecoveryDomainReceipt
    stopped_by_time_budget: bool = False
    persisted: bool = False
    storage_ref: str | None = None
    schema_version: str = ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION
    observation: ObservationResult = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _required_text(self.run_id, "run_id"))
        started = _utc(self.started_at_utc, "started_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        if completed < started:
            raise ErasureStartupRecoveryError(
                "completed_at_utc cannot be before started_at_utc"
            )
        if not isinstance(self.budget, StartupRecoveryBudget):
            raise ErasureStartupRecoveryError("budget must be StartupRecoveryBudget")
        if self.single_fact.domain is not RecoveryDomain.SINGLE_FACT:
            raise ErasureStartupRecoveryError(
                "single_fact receipt must use SINGLE_FACT domain"
            )
        if self.batch.domain is not RecoveryDomain.BATCH:
            raise ErasureStartupRecoveryError("batch receipt must use BATCH domain")
        if not isinstance(self.stopped_by_time_budget, bool):
            raise ErasureStartupRecoveryError("stopped_by_time_budget must be bool")
        if self.single_fact.selected > self.budget.max_single_jobs:
            raise ErasureStartupRecoveryError(
                "single_fact selected count exceeds max_single_jobs"
            )
        if self.batch.selected > self.budget.max_batches:
            raise ErasureStartupRecoveryError(
                "batch selected count exceeds max_batches"
            )
        unattempted = (
            self.single_fact.selected
            - self.single_fact.attempted
            + self.batch.selected
            - self.batch.attempted
        )
        if unattempted > 0 and not self.stopped_by_time_budget:
            raise ErasureStartupRecoveryError(
                "selected but unattempted work requires stopped_by_time_budget"
            )
        if not isinstance(self.persisted, bool):
            raise ErasureStartupRecoveryError("persisted must be bool")
        if self.persisted:
            if self.storage_ref is None:
                raise ErasureStartupRecoveryError(
                    "persisted receipt requires storage_ref"
                )
            object.__setattr__(
                self, "storage_ref", _required_text(self.storage_ref, "storage_ref")
            )
        elif self.storage_ref is not None:
            raise ErasureStartupRecoveryError(
                "non-persisted receipt cannot claim storage_ref"
            )
        if self.schema_version != ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION:
            raise ErasureStartupRecoveryError("unsupported startup recovery schema")

        risk_count = self.unresolved_count
        if risk_count == 0:
            observation = ObservationResult(
                feature_name="gdpr_startup_recovery",
                metric_name="unresolved_recovery_items",
                state=ObservationState.OBSERVED_ZERO,
                observed_value=0,
                source_refs=(self.run_id,),
            )
        else:
            observation = ObservationResult(
                feature_name="gdpr_startup_recovery",
                metric_name="unresolved_recovery_items",
                state=ObservationState.OBSERVED_NONZERO,
                observed_value=risk_count,
                reason_code=(
                    "time_budget_exhausted"
                    if self.stopped_by_time_budget
                    else "recovery_work_remaining"
                ),
                source_refs=(self.run_id,),
            )
        object.__setattr__(self, "observation", observation)

    @property
    def unresolved_count(self) -> int:
        return self.single_fact.unresolved_count + self.batch.unresolved_count

    @property
    def duration_ms(self) -> int:
        started = _utc(self.started_at_utc, "started_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        return int((completed - started).total_seconds() * 1_000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "duration_ms": self.duration_ms,
            "budget": {
                "max_single_jobs": self.budget.max_single_jobs,
                "max_batches": self.budget.max_batches,
                "time_budget_ms": self.budget.time_budget_ms,
                "schema_version": self.budget.schema_version,
            },
            "single_fact": self.single_fact.to_dict(),
            "batch": self.batch.to_dict(),
            "stopped_by_time_budget": self.stopped_by_time_budget,
            "persisted": self.persisted,
            "storage_ref": self.storage_ref,
            "unresolved_count": self.unresolved_count,
            "observation": {
                "feature_name": self.observation.feature_name,
                "metric_name": self.observation.metric_name,
                "state": self.observation.state.value,
                "observed_value": self.observation.observed_value,
                "reason_code": self.observation.reason_code,
                "source_refs": list(self.observation.source_refs),
                "schema_version": self.observation.schema_version,
            },
        }


__all__ = [
    "ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION",
    "ErasureStartupRecoveryError",
    "RecoveryDomain",
    "RecoveryDomainReceipt",
    "StartupRecoveryBudget",
    "StartupRecoveryReceipt",
]
