"""Adversarial proof for bounded Continuity controlled enablement."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from unittest.mock import Mock

import pytest

import core.continuity.controlled_enablement as enablement
from core.continuity.controlled_enablement import (
    CONTROLLED_ENABLEMENT_SCHEMA_VERSION,
    ENV_ACTIVATION_MANIFEST,
    ENV_ACTIVATION_MANIFEST_SHA256,
    ContinuityActivationAction,
    ContinuityActivationConfigurationError,
    ContinuityActivationConflictError,
    ContinuityActivationDecision,
    ContinuityActivationStateError,
    ContinuityControlledEnablementController,
    ContinuityControlledEnablementError,
    ContinuityEnablementState,
    compose_controlled_continuity_runtime_from_environment,
    load_continuity_activation_decision,
)
from core.continuity.runtime_composition import (
    ENV_RUNTIME_OWNER_ID,
    ENV_RUNTIME_OWNER_VERSION,
    ENV_RUNTIME_STORAGE_ROOT,
    ENV_RUNTIME_TENANT_REF,
    SUPPORTED_LIFECYCLE_OWNER_ID,
    SUPPORTED_LIFECYCLE_OWNER_VERSION,
    ContinuityRuntimeCompositionOwner,
    ContinuityRuntimeConfiguration,
)

_NOW = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


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


def _runtime_environment(
    root: Path,
    *,
    tenant: str = "tenant:one",
) -> dict[str, str]:
    return {
        ENV_RUNTIME_OWNER_ID: SUPPORTED_LIFECYCLE_OWNER_ID,
        ENV_RUNTIME_OWNER_VERSION: SUPPORTED_LIFECYCLE_OWNER_VERSION,
        ENV_RUNTIME_STORAGE_ROOT: str(root),
        ENV_RUNTIME_TENANT_REF: tenant,
    }


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


def _activation_environment(
    decision: ContinuityActivationDecision,
) -> dict[str, str]:
    return {
        ENV_ACTIVATION_MANIFEST: decision.canonical_manifest(),
        ENV_ACTIVATION_MANIFEST_SHA256: decision.decision_id,
    }


def _environment_with_decision(
    root: Path,
    decision: ContinuityActivationDecision,
) -> dict[str, str]:
    return {
        **_runtime_environment(root, tenant=decision.tenant_ref),
        **_activation_environment(decision),
    }


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _controller(
    root: Path,
    *,
    decision: ContinuityActivationDecision | None = None,
) -> ContinuityControlledEnablementController:
    configuration = _configuration(root)
    return ContinuityControlledEnablementController(
        configuration=configuration,
        runtime_owner=ContinuityRuntimeCompositionOwner(configuration),
        configured_decision=decision,
    )


def test_no_runtime_or_activation_configuration_means_no_controller(
    tmp_path: Path,
) -> None:
    assert compose_controlled_continuity_runtime_from_environment({}) is None
    assert tuple(tmp_path.iterdir()) == ()


def test_activation_without_runtime_configuration_fails_closed(
    tmp_path: Path,
) -> None:
    decision = _decision(_configuration(tmp_path))

    with pytest.raises(
        ContinuityActivationConfigurationError,
        match="requires complete runtime configuration",
    ):
        compose_controlled_continuity_runtime_from_environment(
            _activation_environment(decision)
        )


@pytest.mark.parametrize(
    "missing",
    [ENV_ACTIVATION_MANIFEST, ENV_ACTIVATION_MANIFEST_SHA256],
)
def test_partial_activation_configuration_fails_closed(
    tmp_path: Path,
    missing: str,
) -> None:
    configuration = _configuration(tmp_path)
    environment = _activation_environment(_decision(configuration))
    environment.pop(missing)

    with pytest.raises(
        ContinuityActivationConfigurationError,
        match="partial Continuity activation configuration",
    ):
        load_continuity_activation_decision(configuration, environment)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.__setitem__("unknown", True), "fields are invalid"),
        (
            lambda value: value.__setitem__(
                "schema_version", "continuity.controlled_enablement.v999"
            ),
            "schema version",
        ),
        (
            lambda value: value.__setitem__("no_runtime_authority", False),
            "runtime authority",
        ),
        (
            lambda value: value.__setitem__("no_side_effect_authority", False),
            "side-effect authority",
        ),
        (
            lambda value: value.__setitem__("scope", "continuity.everything"),
            "scope",
        ),
    ],
)
def test_unknown_or_authority_escalating_manifest_fails_closed(
    tmp_path: Path,
    mutation,
    message: str,
) -> None:
    manifest = json.loads(_decision(_configuration(tmp_path)).canonical_manifest())
    mutation(manifest)
    canonical = _canonical(manifest)

    with pytest.raises(ContinuityActivationConfigurationError, match=message):
        ContinuityActivationDecision.from_manifest(canonical, _digest(canonical))


def test_noncanonical_json_and_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    decision = _decision(_configuration(tmp_path))
    noncanonical = json.dumps(json.loads(decision.canonical_manifest()), indent=2)

    with pytest.raises(ContinuityActivationConfigurationError, match="canonical JSON"):
        ContinuityActivationDecision.from_manifest(
            noncanonical,
            _digest(noncanonical),
        )
    with pytest.raises(ContinuityActivationConfigurationError, match="digest"):
        ContinuityActivationDecision.from_manifest(
            decision.canonical_manifest(),
            "0" * 64,
        )


@pytest.mark.parametrize(
    "field",
    [
        "configuration_id",
        "lifecycle_owner_id",
        "lifecycle_owner_version",
        "tenant_ref",
        "storage_location_id",
    ],
)
def test_substituted_runtime_binding_fails_closed(
    tmp_path: Path,
    field: str,
) -> None:
    configuration = _configuration(tmp_path)
    manifest = json.loads(_decision(configuration).canonical_manifest())
    manifest[field] = f"substituted:{field}"
    canonical = _canonical(manifest)

    with pytest.raises(ContinuityActivationConfigurationError):
        decision = ContinuityActivationDecision.from_manifest(
            canonical,
            _digest(canonical),
        )
        decision.validate_binding(configuration)


def test_manifest_contains_no_caller_controlled_database_path(tmp_path: Path) -> None:
    decision = _decision(_configuration(tmp_path))
    payload = json.loads(decision.canonical_manifest())

    assert set(payload) == enablement._MANIFEST_FIELDS
    assert "database_path" not in payload
    assert "storage_root" not in payload
    assert "db_path" not in decision.__dataclass_fields__


def test_runtime_configuration_without_operator_decision_starts_disabled(
    tmp_path: Path,
) -> None:
    controller = compose_controlled_continuity_runtime_from_environment(
        _runtime_environment(tmp_path)
    )
    assert controller is not None

    diagnostic = controller.startup(evaluated_at=_NOW)

    assert diagnostic.state is ContinuityEnablementState.DISABLED
    assert diagnostic.enablement_mechanism_implemented is True
    assert diagnostic.operator_enable_decision_present is False
    assert diagnostic.observed is False
    assert diagnostic.runtime_authority is False
    assert diagnostic.side_effect_authority is False
    assert len(tuple(tmp_path.glob("*.sqlite3"))) == 1


def test_valid_operator_enable_decision_enables_only_bounded_internal_scope(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    decision = _decision(configuration)
    controller = compose_controlled_continuity_runtime_from_environment(
        _environment_with_decision(tmp_path, decision)
    )
    assert controller is not None

    diagnostic = controller.startup(evaluated_at=_NOW)

    assert diagnostic.state is ContinuityEnablementState.ENABLED
    assert diagnostic.applied_decision_id == decision.decision_id
    assert diagnostic.applied_decision_sequence == 1
    assert diagnostic.operator_enable_decision_present is True
    assert diagnostic.runtime_authority is False
    assert diagnostic.side_effect_authority is False


def test_enable_before_startup_and_after_shutdown_fails_closed(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    decision = _decision(configuration)

    with pytest.raises(ContinuityActivationStateError, match="started runtime"):
        controller.apply_decision(decision, evaluated_at=_NOW)

    controller.startup(evaluated_at=_NOW)
    controller.shutdown()
    with pytest.raises(ContinuityActivationStateError, match="started runtime"):
        controller.apply_decision(decision, evaluated_at=_NOW)


def test_duplicate_enable_and_disable_are_idempotent(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    enable = _decision(configuration, sequence=1)
    disable = _decision(
        configuration,
        action=ContinuityActivationAction.DISABLE,
        sequence=2,
        expires_at=None,
    )

    assert (
        controller.apply_decision(enable, evaluated_at=_NOW).state
        is ContinuityEnablementState.ENABLED
    )
    assert (
        controller.apply_decision(enable, evaluated_at=_NOW).state
        is ContinuityEnablementState.ENABLED
    )
    assert (
        controller.apply_decision(disable, evaluated_at=_NOW).state
        is ContinuityEnablementState.DISABLED
    )
    assert (
        controller.apply_decision(disable, evaluated_at=_NOW).state
        is ContinuityEnablementState.DISABLED
    )

    with sqlite3.connect(configuration.database_path()) as connection:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {enablement._ACTIVATION_TABLE}"
        ).fetchone()[0]
    assert count == 2


def test_enable_after_disable_requires_higher_sequence(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    first_enable = _decision(configuration, sequence=1)
    disable = _decision(
        configuration,
        action=ContinuityActivationAction.DISABLE,
        sequence=2,
        expires_at=None,
    )
    second_enable = _decision(configuration, sequence=3)

    controller.apply_decision(first_enable, evaluated_at=_NOW)
    controller.apply_decision(disable, evaluated_at=_NOW)
    diagnostic = controller.apply_decision(second_enable, evaluated_at=_NOW)

    assert diagnostic.state is ContinuityEnablementState.ENABLED
    assert diagnostic.applied_decision_sequence == 3


def test_stale_and_same_sequence_conflicting_decisions_fail_closed(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    enable = _decision(configuration, sequence=2)
    stale = _decision(configuration, sequence=1)
    conflict = _decision(
        configuration,
        action=ContinuityActivationAction.DISABLE,
        sequence=2,
        expires_at=None,
    )
    controller.apply_decision(enable, evaluated_at=_NOW)

    with pytest.raises(ContinuityActivationConflictError, match="stale"):
        controller.apply_decision(stale, evaluated_at=_NOW)
    with pytest.raises(ContinuityActivationConflictError, match="conflicts"):
        controller.apply_decision(conflict, evaluated_at=_NOW)


def test_concurrent_duplicate_enable_is_one_persisted_decision(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    decision = _decision(configuration)

    with ThreadPoolExecutor(max_workers=12) as pool:
        diagnostics = tuple(
            pool.map(
                lambda _: controller.apply_decision(decision, evaluated_at=_NOW),
                range(24),
            )
        )

    assert {item.state for item in diagnostics} == {
        ContinuityEnablementState.ENABLED
    }
    with sqlite3.connect(configuration.database_path()) as connection:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {enablement._ACTIVATION_TABLE}"
        ).fetchone()[0]
    assert count == 1


def test_concurrent_enable_disable_race_converges_to_highest_sequence(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    enable = _decision(configuration, sequence=2)
    disable = _decision(
        configuration,
        action=ContinuityActivationAction.DISABLE,
        sequence=3,
        expires_at=None,
    )

    def apply(decision: ContinuityActivationDecision) -> object:
        try:
            return controller.apply_decision(decision, evaluated_at=_NOW)
        except ContinuityActivationConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(apply, (enable, disable)))

    assert any(
        getattr(result, "state", None) is ContinuityEnablementState.DISABLED
        for result in results
    )
    assert controller.state is ContinuityEnablementState.DISABLED
    assert controller.diagnostic().applied_decision_sequence == 3


def test_shutdown_revokes_in_process_enablement(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    controller.apply_decision(_decision(configuration), evaluated_at=_NOW)

    diagnostic = controller.shutdown()

    assert diagnostic.state is ContinuityEnablementState.STOPPED
    assert diagnostic.operator_enable_decision_present is False


def test_restart_without_current_manifest_remains_disabled(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    first = _controller(tmp_path)
    first.startup(evaluated_at=_NOW)
    first.apply_decision(_decision(configuration), evaluated_at=_NOW)
    first.shutdown()

    second = _controller(tmp_path)
    diagnostic = second.startup(evaluated_at=_NOW + timedelta(minutes=5))

    assert diagnostic.state is ContinuityEnablementState.DISABLED
    assert diagnostic.applied_decision_id is None
    assert diagnostic.operator_enable_decision_present is False


def test_restart_with_same_current_manifest_revalidates_and_enables(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    decision = _decision(configuration)
    first = _controller(tmp_path, decision=decision)
    first.startup(evaluated_at=_NOW)
    first.shutdown()

    second = _controller(tmp_path, decision=decision)
    diagnostic = second.startup(evaluated_at=_NOW + timedelta(minutes=5))

    assert diagnostic.state is ContinuityEnablementState.ENABLED
    assert diagnostic.applied_decision_id == decision.decision_id


def test_expired_or_future_enable_lease_fails_startup(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    expired = _decision(
        configuration,
        effective_at=_NOW - timedelta(hours=2),
        expires_at=_NOW - timedelta(hours=1),
    )
    future = _decision(
        configuration,
        sequence=2,
        effective_at=_NOW + timedelta(hours=1),
        expires_at=_NOW + timedelta(hours=2),
    )

    with pytest.raises(ContinuityActivationConfigurationError, match="expired"):
        _controller(tmp_path, decision=expired).startup(evaluated_at=_NOW)
    with pytest.raises(ContinuityActivationConfigurationError, match="not yet"):
        _controller(tmp_path, decision=future).startup(evaluated_at=_NOW)


def test_expired_persisted_enable_is_not_permission_without_manifest(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    decision = _decision(
        configuration,
        effective_at=_NOW,
        expires_at=_NOW + timedelta(minutes=1),
    )
    first = _controller(tmp_path, decision=decision)
    first.startup(evaluated_at=_NOW)
    first.shutdown()

    second = _controller(tmp_path)
    diagnostic = second.startup(evaluated_at=_NOW + timedelta(hours=1))

    assert diagnostic.state is ContinuityEnablementState.DISABLED


def test_malformed_persisted_state_fails_closed(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    first = _controller(tmp_path)
    first.startup(evaluated_at=_NOW)
    first.apply_decision(_decision(configuration), evaluated_at=_NOW)
    first.shutdown()

    with sqlite3.connect(configuration.database_path()) as connection:
        connection.execute(
            f"UPDATE {enablement._ACTIVATION_TABLE} SET manifest_json = '{{}}'"
        )

    with pytest.raises(ContinuityControlledEnablementError):
        _controller(tmp_path).startup(evaluated_at=_NOW)


def test_incompatible_activation_table_fails_closed(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    owner = ContinuityRuntimeCompositionOwner(configuration)
    owner.startup()
    owner.shutdown()
    with sqlite3.connect(configuration.database_path()) as connection:
        connection.execute(
            f"CREATE TABLE {enablement._ACTIVATION_TABLE}(decision_id TEXT)"
        )

    with pytest.raises(ContinuityControlledEnablementError, match="incompatible"):
        _controller(tmp_path).startup(evaluated_at=_NOW)


def test_persist_and_replay_are_blocked_while_disabled(
    tmp_path: Path,
) -> None:
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)

    with pytest.raises(ContinuityActivationStateError, match="not currently enabled"):
        controller.persist_accepted_admission(  # type: ignore[arg-type]
            object(),
            appended_at=_NOW,
            evaluated_at=_NOW,
        )
    with pytest.raises(ContinuityActivationStateError, match="not currently enabled"):
        controller.replay(  # type: ignore[arg-type]
            "a" * 64,
            scope=object(),
            replayed_at=_NOW,
        )


def test_enabled_controller_delegates_only_to_existing_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    controller.apply_decision(_decision(configuration), evaluated_at=_NOW)
    append_evidence = Mock()
    replayed_artifact = Mock()
    persist = Mock(return_value=append_evidence)
    replay = Mock(return_value=replayed_artifact)
    monkeypatch.setattr(controller._runtime_owner, "persist_accepted_admission", persist)
    monkeypatch.setattr(controller._runtime_owner, "replay", replay)

    assert (
        controller.persist_accepted_admission(  # type: ignore[arg-type]
            object(),
            appended_at=_NOW,
            evaluated_at=_NOW,
        )
        is append_evidence
    )
    assert (
        controller.replay(  # type: ignore[arg-type]
            "a" * 64,
            scope=object(),
            replayed_at=_NOW,
        )
        is replayed_artifact
    )
    persist.assert_called_once()
    replay.assert_called_once()


def test_lease_expiry_revokes_access_without_side_effect(
    tmp_path: Path,
) -> None:
    configuration = _configuration(tmp_path)
    controller = _controller(tmp_path)
    controller.startup(evaluated_at=_NOW)
    controller.apply_decision(
        _decision(configuration, expires_at=_NOW + timedelta(minutes=1)),
        evaluated_at=_NOW,
    )

    with pytest.raises(ContinuityActivationStateError, match="lease"):
        controller.persist_accepted_admission(  # type: ignore[arg-type]
            object(),
            appended_at=_NOW,
            evaluated_at=_NOW + timedelta(minutes=2),
        )
    assert controller.state is ContinuityEnablementState.DISABLED


def test_controlled_enablement_has_no_forbidden_side_effect_imports() -> None:
    tree = ast.parse(
        Path("core/continuity/controlled_enablement.py").read_text(encoding="utf-8")
    )
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = {
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
    assert imported.isdisjoint(forbidden)


def test_no_second_runtime_store_path_or_module_singleton() -> None:
    source = Path("core/continuity/controlled_enablement.py").read_text(
        encoding="utf-8"
    )
    assert "ContinuityArtifactStore(" not in source
    assert (
        "database_path"
        not in enablement.ContinuityActivationDecision.__dataclass_fields__
    )
    assert "= ContinuityControlledEnablementController(" not in source

    allowed = {
        Path("core/continuity/admission_artifact_lifecycle.py"),
        Path("core/continuity/runtime_composition.py"),
    }
    offenders: list[str] = []
    for root in (Path("core"), Path("api")):
        for path in root.rglob("*.py"):
            if path in allowed:
                continue
            if "ContinuityArtifactStore(" in path.read_text(encoding="utf-8"):
                offenders.append(str(path))
    assert offenders == []


def test_public_query_and_user_visible_behavior_remain_unchanged() -> None:
    server_source = Path("server.py").read_text(encoding="utf-8")
    middleware_source = Path("api/server_middleware.py").read_text(encoding="utf-8")

    assert "controlled_enablement" not in server_source
    assert "continuity_runtime_owner" not in server_source
    assert "persist_accepted_admission" not in server_source
    assert (
        "compose_controlled_continuity_runtime_from_environment"
        in middleware_source
    )
    assert "persist_accepted_admission" not in middleware_source
    assert ".replay(" not in middleware_source


def test_schema_and_state_vocabulary_are_exact() -> None:
    assert CONTROLLED_ENABLEMENT_SCHEMA_VERSION == (
        "continuity.controlled_enablement.v1"
    )
    assert {state.value for state in ContinuityEnablementState} == {
        "new",
        "disabled",
        "enabled",
        "stopped",
    }
