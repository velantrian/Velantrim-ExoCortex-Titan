"""Adversarial proof for bounded, content-free Continuity observation evidence."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

import pytest

from core.continuity.bounded_observation import (
    BOUNDED_OBSERVATION_SCHEMA_VERSION,
    ContinuityBoundedObservationController,
    ContinuityBoundedObservationError,
    ContinuityBoundedObservationEvidence,
    ContinuityObservationConfigurationError,
    ContinuityObservationConflictError,
    ContinuityObservationLifecycle,
    ContinuityObservationStateError,
    compose_bounded_observation,
    summarize_observation_session,
)
from core.continuity.controlled_enablement import (
    ContinuityActivationAction,
    ContinuityActivationDecision,
    ContinuityActivationStateError,
    ContinuityControlledEnablementController,
    ContinuityEnablementState,
)
from core.continuity.runtime_composition import (
    SUPPORTED_LIFECYCLE_OWNER_ID,
    SUPPORTED_LIFECYCLE_OWNER_VERSION,
    ContinuityRuntimeCompositionOwner,
    ContinuityRuntimeConfiguration,
)

_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)

_ALL_TRUE_INVARIANTS = {
    "configuration_binding_stable": True,
    "storage_location_unchanged": True,
    "single_lifecycle_owner": True,
    "decision_binding_consistent": True,
    "lease_valid_when_enabled": True,
    "runtime_authority_absent": True,
    "side_effect_authority_absent": True,
}


def _configuration(
    root: Path,
    *,
    tenant: str = "tenant:one",
) -> ContinuityRuntimeConfiguration:
    return ContinuityRuntimeConfiguration.create(
        lifecycle_owner_id=SUPPORTED_LIFECYCLE_OWNER_ID,
        lifecycle_owner_version=SUPPORTED_LIFECYCLE_OWNER_VERSION,
        storage_root=root,
        tenant_ref=tenant,
    )


def _enablement(
    configuration: ContinuityRuntimeConfiguration,
) -> ContinuityControlledEnablementController:
    return ContinuityControlledEnablementController(
        configuration=configuration,
        runtime_owner=ContinuityRuntimeCompositionOwner(configuration),
    )


def _decision(
    configuration: ContinuityRuntimeConfiguration,
    *,
    action: ContinuityActivationAction = ContinuityActivationAction.ENABLE,
    sequence: int = 1,
    effective_at: datetime = _NOW,
    expires_at: datetime | None = None,
) -> ContinuityActivationDecision:
    if action is ContinuityActivationAction.ENABLE and expires_at is None:
        expires_at = effective_at + timedelta(hours=1)
    return ContinuityActivationDecision.create(
        action=action,
        decision_sequence=sequence,
        operator_ref="operator:deployment-owner",
        configuration=configuration,
        issued_at=effective_at - timedelta(minutes=1),
        effective_at=effective_at,
        expires_at=expires_at,
    )


def _started_pair(
    root: Path,
    *,
    tenant: str = "tenant:one",
) -> tuple[ContinuityRuntimeConfiguration, ContinuityControlledEnablementController]:
    configuration = _configuration(root, tenant=tenant)
    enablement = _enablement(configuration)
    enablement.startup(evaluated_at=_NOW)
    return configuration, enablement


def _open_observer(
    configuration: ContinuityRuntimeConfiguration,
    enablement: ContinuityControlledEnablementController,
) -> ContinuityBoundedObservationController:
    observer = ContinuityBoundedObservationController(
        configuration=configuration,
        enablement_controller=enablement,
    )
    observer.open()
    return observer


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #


def test_observer_requires_typed_configuration_and_controller(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    enablement = _enablement(configuration)

    with pytest.raises(ContinuityObservationConfigurationError):
        ContinuityBoundedObservationController(
            configuration=object(),  # type: ignore[arg-type]
            enablement_controller=enablement,
        )
    with pytest.raises(ContinuityObservationConfigurationError):
        ContinuityBoundedObservationController(
            configuration=configuration,
            enablement_controller=object(),  # type: ignore[arg-type]
        )


def test_observer_rejects_binding_mismatch_at_construction(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    configuration_a = _configuration(tmp_path / "a", tenant="tenant:a")
    configuration_b = _configuration(tmp_path / "b", tenant="tenant:b")
    enablement_b = _enablement(configuration_b)

    with pytest.raises(ContinuityObservationConfigurationError, match="binding mismatch"):
        ContinuityBoundedObservationController(
            configuration=configuration_a,
            enablement_controller=enablement_b,
        )


def test_open_is_idempotent_and_rejects_reopen_after_close(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = ContinuityBoundedObservationController(
        configuration=configuration,
        enablement_controller=enablement,
    )
    observer.open()
    observer.open()  # idempotent
    assert observer.lifecycle is ContinuityObservationLifecycle.READY

    observer.close()
    assert observer.lifecycle is ContinuityObservationLifecycle.CLOSED
    with pytest.raises(ContinuityObservationStateError, match="already closed"):
        observer.open()


def test_compose_bounded_observation_helper_binds_exactly(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = compose_bounded_observation(
        configuration=configuration,
        enablement_controller=enablement,
    )
    assert isinstance(observer, ContinuityBoundedObservationController)
    assert observer.configuration_id == configuration.configuration_id


# --------------------------------------------------------------------------- #
# Lifecycle / fail-closed
# --------------------------------------------------------------------------- #


def test_observe_before_open_fails_closed(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = ContinuityBoundedObservationController(
        configuration=configuration,
        enablement_controller=enablement,
    )
    with pytest.raises(ContinuityObservationStateError, match="not open"):
        observer.observe(observation_sequence=1, observed_at=_NOW)


def test_observe_before_runtime_startup_fails_closed(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    enablement = _enablement(configuration)
    observer = ContinuityBoundedObservationController(
        configuration=configuration,
        enablement_controller=enablement,
    )
    observer.open()
    with pytest.raises(ContinuityObservationStateError, match="not started"):
        observer.observe(observation_sequence=1, observed_at=_NOW)


def test_observe_while_disabled_succeeds_and_records_disabled_state(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)

    evidence = observer.observe(observation_sequence=1, observed_at=_NOW)
    assert evidence.observed_state == ContinuityEnablementState.DISABLED.value
    assert evidence.applied_decision_id is None
    assert evidence.all_invariants_passed()


def test_valid_enable_then_observe_records_enabled_state_with_valid_lease(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)

    evidence = observer.observe(observation_sequence=1, observed_at=_NOW)
    assert evidence.observed_state == ContinuityEnablementState.ENABLED.value
    assert evidence.lease_valid is True
    assert evidence.all_invariants_passed()
    assert dict(evidence.invariants)["lease_valid_when_enabled"] is True


def test_expired_lease_is_observed_as_a_failed_invariant_without_mutating_state(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    enablement.apply_decision(
        _decision(configuration, expires_at=_NOW + timedelta(minutes=5)),
        evaluated_at=_NOW,
    )

    later = _NOW + timedelta(minutes=10)
    evidence = observer.observe(observation_sequence=1, observed_at=later)

    # Enablement itself is lazy: state stays ENABLED until a gated operation
    # re-checks the lease. Observation must report this truthfully instead of
    # silently mutating the enablement controller's state on its own.
    assert enablement.state is ContinuityEnablementState.ENABLED
    assert evidence.observed_state == ContinuityEnablementState.ENABLED.value
    assert evidence.lease_valid is False
    assert dict(evidence.invariants)["lease_valid_when_enabled"] is False
    assert evidence.all_invariants_passed() is False


def test_after_disable_observe_records_disabled_and_after_shutdown_fails_closed(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)
    observer.observe(observation_sequence=1, observed_at=_NOW)

    enablement.apply_decision(
        _decision(
            configuration,
            action=ContinuityActivationAction.DISABLE,
            sequence=2,
        ),
        evaluated_at=_NOW,
    )
    evidence = observer.observe(observation_sequence=2, observed_at=_NOW)
    assert evidence.observed_state == ContinuityEnablementState.DISABLED.value

    enablement.shutdown()
    with pytest.raises(ContinuityObservationStateError, match="shut down"):
        observer.observe(observation_sequence=3, observed_at=_NOW)


def test_shutdown_during_observation_window_fails_closed_on_next_observe(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    observer.observe(observation_sequence=1, observed_at=_NOW)

    enablement.shutdown()

    with pytest.raises(ContinuityObservationStateError):
        observer.observe(observation_sequence=2, observed_at=_NOW)


def test_restart_after_successful_observation_starts_disabled_with_no_silent_reenable(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)
    enabled_evidence = observer.observe(observation_sequence=1, observed_at=_NOW)
    assert enabled_evidence.observed_state == ContinuityEnablementState.ENABLED.value
    observer.close()
    enablement.shutdown()

    # Fresh process objects, same storage root, no configured decision supplied.
    restarted_configuration = _configuration(tmp_path)
    restarted_enablement = _enablement(restarted_configuration)
    restarted_enablement.startup(evaluated_at=_NOW)
    assert restarted_enablement.state is ContinuityEnablementState.DISABLED

    restarted_observer = _open_observer(restarted_configuration, restarted_enablement)
    evidence = restarted_observer.observe(observation_sequence=2, observed_at=_NOW)
    assert evidence.observed_state == ContinuityEnablementState.DISABLED.value

    # The earlier ENABLED evidence row remains readable; rollback did not
    # erase history, and history did not silently re-enable the restart.
    persisted = restarted_observer._read_persisted_records()  # noqa: SLF001
    assert [record.observation_sequence for record in persisted] == [1, 2]
    assert persisted[0].observed_state == ContinuityEnablementState.ENABLED.value


def test_restart_with_incompatible_schema_fails_closed(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    observer.observe(observation_sequence=1, observed_at=_NOW)
    observer.close()
    enablement.shutdown()

    with sqlite3.connect(configuration.database_path()) as connection:
        connection.execute(
            "ALTER TABLE continuity_bounded_observation_records "
            "ADD COLUMN unexpected_extra TEXT"
        )

    restarted_configuration = _configuration(tmp_path)
    restarted_enablement = _enablement(restarted_configuration)
    restarted_enablement.startup(evaluated_at=_NOW)
    restarted_observer = ContinuityBoundedObservationController(
        configuration=restarted_configuration,
        enablement_controller=restarted_enablement,
    )
    with pytest.raises(ContinuityBoundedObservationError, match="incompatible"):
        restarted_observer.open()


def test_malformed_persisted_evidence_fails_closed(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    observer.observe(observation_sequence=1, observed_at=_NOW)

    with sqlite3.connect(configuration.database_path()) as connection:
        connection.execute(
            "UPDATE continuity_bounded_observation_records "
            "SET evidence_json = '{\"tampered\": true}'"
        )

    with pytest.raises(ContinuityBoundedObservationError, match="digest mismatch"):
        observer.observe(observation_sequence=2, observed_at=_NOW)


def test_foreign_configuration_row_in_shared_storage_fails_closed(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    observer.observe(observation_sequence=1, observed_at=_NOW)

    # A self-consistent (correctly digested) evidence row for a *different*
    # configuration ends up in the same SQLite file - e.g. a storage
    # collision. Insert it directly, bypassing this controller's own write
    # path, then confirm the read path still fails closed on the mismatch.
    foreign_configuration = _configuration(tmp_path, tenant="tenant:foreign")
    foreign_diagnostic = _enablement(foreign_configuration).diagnostic()
    foreign_evidence = ContinuityBoundedObservationEvidence.create(
        observation_sequence=2,
        configuration=foreign_configuration,
        diagnostic=foreign_diagnostic,
        lease_valid=False,
        invariants=_ALL_TRUE_INVARIANTS,
        observed_at=_NOW,
    )
    observer._insert_record(foreign_evidence, recorded_at=_NOW)  # noqa: SLF001

    with pytest.raises(ContinuityBoundedObservationError, match="does not match"):
        observer.observe(observation_sequence=3, observed_at=_NOW)


# --------------------------------------------------------------------------- #
# Idempotency / monotonic sequencing
# --------------------------------------------------------------------------- #


def test_duplicate_observation_is_idempotent(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)

    first = observer.observe(observation_sequence=1, observed_at=_NOW)
    second = observer.observe(observation_sequence=1, observed_at=_NOW)
    assert first.observation_id == second.observation_id
    assert len(observer._read_persisted_records()) == 1  # noqa: SLF001


def test_stale_observation_sequence_is_rejected(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    observer.observe(observation_sequence=5, observed_at=_NOW)

    with pytest.raises(ContinuityObservationConflictError, match="stale"):
        observer.observe(observation_sequence=3, observed_at=_NOW)


def test_conflicting_same_sequence_observation_is_rejected(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    observer.observe(observation_sequence=1, observed_at=_NOW)
    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)

    with pytest.raises(ContinuityObservationConflictError, match="conflicts"):
        observer.observe(observation_sequence=1, observed_at=_NOW)


@pytest.mark.parametrize("sequence", [0, -1])
def test_non_positive_observation_sequence_fails_closed(
    tmp_path: Path,
    sequence: int,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    with pytest.raises(ContinuityObservationConfigurationError):
        observer.observe(observation_sequence=sequence, observed_at=_NOW)


# --------------------------------------------------------------------------- #
# Concurrency
# --------------------------------------------------------------------------- #


def test_concurrent_observations_converge_to_exactly_one_row_per_sequence(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)

    def _observe(
        sequence: int,
    ) -> ContinuityBoundedObservationEvidence | ContinuityObservationConflictError:
        try:
            return observer.observe(
                observation_sequence=sequence,
                observed_at=_NOW + timedelta(seconds=sequence),
            )
        except ContinuityObservationConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_observe, range(1, 21)))

    # Out-of-order concurrent arrival of a strictly monotonic sequence means
    # some submissions legitimately lose the race and are rejected as stale
    # rather than silently reordered or duplicated: no crash, no unexpected
    # exception type, and the persisted history stays strictly increasing.
    assert all(
        isinstance(item, (ContinuityBoundedObservationEvidence, ContinuityObservationConflictError))
        for item in results
    )
    persisted = observer._read_persisted_records()  # noqa: SLF001
    sequences = [record.observation_sequence for record in persisted]
    assert sequences == sorted(sequences)
    assert len(sequences) == len(set(sequences))
    assert 1 <= len(sequences) <= 20
    accepted = {item.observation_sequence for item in results if not isinstance(item, Exception)}
    assert accepted == set(sequences)


def test_concurrent_duplicate_same_sequence_never_double_inserts(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)

    def _observe(_: int) -> ContinuityBoundedObservationEvidence:
        return observer.observe(observation_sequence=1, observed_at=_NOW)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_observe, range(16)))

    ids = {result.observation_id for result in results}
    assert len(ids) == 1
    assert len(observer._read_persisted_records()) == 1  # noqa: SLF001


def test_disable_during_concurrent_observation_yields_deterministic_states(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)

    def _observe(sequence: int) -> str:
        return observer.observe(
            observation_sequence=sequence, observed_at=_NOW
        ).observed_state

    def _disable() -> None:
        enablement.apply_decision(
            _decision(
                configuration,
                action=ContinuityActivationAction.DISABLE,
                sequence=2,
            ),
            evaluated_at=_NOW,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        observe_future = pool.submit(_observe, 1)
        disable_future = pool.submit(_disable)
        observed_state = observe_future.result()
        disable_future.result()

    assert observed_state in {
        ContinuityEnablementState.ENABLED.value,
        ContinuityEnablementState.DISABLED.value,
    }
    assert enablement.state is ContinuityEnablementState.DISABLED


# --------------------------------------------------------------------------- #
# Authority absence / no escalation
# --------------------------------------------------------------------------- #


def test_bounded_observation_has_no_forbidden_side_effect_imports_or_calls() -> None:
    source = Path("core/continuity/bounded_observation.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden_modules = {
        "core.memory",
        "core.truth_gate",
        "core.goal_stack",
        "core.pipeline",
        "core.llm_router",
        "core.sleep_time_worker",
        "core.scheduler",
        "core.actions",
        "core.tools",
        "core.notifications",
        "core.reminders",
    }
    assert imported.isdisjoint(forbidden_modules)
    # Checked as call syntax, not bare substring: the module's own docstring
    # legitimately *names* these methods in prose to explain it never calls
    # them.
    assert ".persist_accepted_admission(" not in source
    assert ".replay(" not in source
    assert "ContinuityArtifactStore(" not in source


def test_bounded_observation_controller_exposes_no_gated_business_operations() -> None:
    public_methods = {
        name
        for name in dir(ContinuityBoundedObservationController)
        if not name.startswith("_")
    }
    assert public_methods == {
        "open",
        "close",
        "observe",
        "lifecycle",
        "configuration_id",
    }


def test_evidence_cannot_be_constructed_with_a_false_authority_marker() -> None:
    configuration = _configuration(Path.cwd())
    diagnostic = _enablement(configuration).diagnostic()
    evidence = ContinuityBoundedObservationEvidence.create(
        observation_sequence=1,
        configuration=configuration,
        diagnostic=diagnostic,
        lease_valid=False,
        invariants=_ALL_TRUE_INVARIANTS,
        observed_at=_NOW,
    )
    with pytest.raises(ContinuityObservationConfigurationError, match="new authority"):
        replace(evidence, no_new_authority_granted=False)
    with pytest.raises(ContinuityObservationConfigurationError, match="permission"):
        replace(evidence, evidence_is_not_permission=False)


def test_evidence_rejects_incomplete_or_unknown_invariant_checklist() -> None:
    configuration = _configuration(Path.cwd())
    diagnostic = _enablement(configuration).diagnostic()
    base_invariants = dict(_ALL_TRUE_INVARIANTS)
    incomplete = dict(base_invariants)
    incomplete.pop("lease_valid_when_enabled")
    with pytest.raises(ContinuityObservationConfigurationError, match="checklist"):
        ContinuityBoundedObservationEvidence.create(
            observation_sequence=1,
            configuration=configuration,
            diagnostic=diagnostic,
            lease_valid=False,
            invariants=incomplete,
            observed_at=_NOW,
        )

    unknown = dict(base_invariants)
    unknown["unexpected_invariant"] = True
    with pytest.raises(ContinuityObservationConfigurationError, match="unknown"):
        ContinuityBoundedObservationEvidence.create(
            observation_sequence=1,
            configuration=configuration,
            diagnostic=diagnostic,
            lease_valid=False,
            invariants=unknown,
            observed_at=_NOW,
        )


def test_public_query_and_user_visible_behavior_remain_unchanged() -> None:
    server_source = Path("server.py").read_text(encoding="utf-8")
    middleware_source = Path("api/server_middleware.py").read_text(encoding="utf-8")

    assert "bounded_observation" not in server_source
    assert "continuity_observation_controller" not in server_source
    assert "ContinuityBoundedObservationController" in middleware_source
    assert "persist_accepted_admission" not in middleware_source
    assert ".replay(" not in middleware_source
    assert ".observe(" not in middleware_source


def test_no_second_runtime_or_storage_path_is_introduced(tmp_path: Path) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)
    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)
    observer.observe(observation_sequence=1, observed_at=_NOW)

    databases = list(tmp_path.glob("*.sqlite3"))
    assert len(databases) == 1
    assert databases[0] == configuration.database_path()

    source = Path("core/continuity/bounded_observation.py").read_text(
        encoding="utf-8"
    )
    assert "= ContinuityRuntimeCompositionOwner(" not in source
    assert "= ContinuityControlledEnablementController(" not in source


# --------------------------------------------------------------------------- #
# Rollback proof / deterministic session result
# --------------------------------------------------------------------------- #


def test_full_bounded_canary_session_proves_rollback_deterministically(
    tmp_path: Path,
) -> None:
    configuration, enablement = _started_pair(tmp_path)
    observer = _open_observer(configuration, enablement)

    before = observer.observe(observation_sequence=1, observed_at=_NOW)

    enablement.apply_decision(_decision(configuration), evaluated_at=_NOW)
    during = observer.observe(observation_sequence=2, observed_at=_NOW)

    enablement.apply_decision(
        _decision(
            configuration,
            action=ContinuityActivationAction.DISABLE,
            sequence=2,
        ),
        evaluated_at=_NOW,
    )
    after = observer.observe(observation_sequence=3, observed_at=_NOW)

    summary = summarize_observation_session([before, during, after])
    assert summary.rollback_verified is True
    assert summary.all_invariants_passed is True
    assert summary.no_configuration_drift is True
    assert summary.observation_count == 3

    # Access remains rejected post-disable/post-rollback through the existing
    # enablement gate; observation never grants that access itself.
    with pytest.raises(ContinuityActivationStateError):
        enablement.persist_accepted_admission(
            object(),  # type: ignore[arg-type]
            appended_at=_NOW,
            evaluated_at=_NOW,
        )


def test_summary_requires_at_least_one_evidence_record() -> None:
    with pytest.raises(ContinuityObservationConfigurationError):
        summarize_observation_session([])


def test_summary_detects_configuration_drift_across_evidence(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    configuration_a = _configuration(tmp_path / "a", tenant="tenant:a")
    configuration_b = _configuration(tmp_path / "b", tenant="tenant:b")
    evidence_a = ContinuityBoundedObservationEvidence.create(
        observation_sequence=1,
        configuration=configuration_a,
        diagnostic=_enablement(configuration_a).diagnostic(),
        lease_valid=False,
        invariants=_ALL_TRUE_INVARIANTS,
        observed_at=_NOW,
    )
    evidence_b = ContinuityBoundedObservationEvidence.create(
        observation_sequence=2,
        configuration=configuration_b,
        diagnostic=_enablement(configuration_b).diagnostic(),
        lease_valid=False,
        invariants=_ALL_TRUE_INVARIANTS,
        observed_at=_NOW,
    )
    assert evidence_a.configuration_id != evidence_b.configuration_id

    summary = summarize_observation_session([evidence_a, evidence_b])
    assert summary.no_configuration_drift is False
    assert summary.rollback_verified is False


# --------------------------------------------------------------------------- #
# Schema / vocabulary
# --------------------------------------------------------------------------- #


def test_schema_version_is_exact() -> None:
    assert BOUNDED_OBSERVATION_SCHEMA_VERSION == "continuity.bounded_observation.v1"


def test_evidence_schema_version_is_enforced() -> None:
    configuration = _configuration(Path.cwd())
    diagnostic = _enablement(configuration).diagnostic()
    evidence = ContinuityBoundedObservationEvidence.create(
        observation_sequence=1,
        configuration=configuration,
        diagnostic=diagnostic,
        lease_valid=False,
        invariants=_ALL_TRUE_INVARIANTS,
        observed_at=_NOW,
    )
    with pytest.raises(ContinuityObservationConfigurationError, match="schema version"):
        replace(evidence, schema_version="continuity.bounded_observation.v999")
