"""Adversarial tests for bounded Continuity runtime composition."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Any
from unittest.mock import Mock

import pytest

import core.continuity.runtime_composition as runtime
from core.continuity.admission_artifact_lifecycle import (
    ContinuityAdmissionArtifact,
    ContinuityArtifactLifecycleError,
    ContinuityArtifactScope,
    ContinuityRetentionPolicy,
)
from core.continuity.admission_evaluator import (
    ContinuityAdmissionRegistry,
    ContinuityCurrentDecisionEvidence,
)
from core.continuity.admission_facade import (
    ContinuityAdmissionFacadePolicy,
    ContinuityAdmissionFacadeResult,
)
from core.continuity.current_decision_resolver import (
    ContinuityCurrentDecisionOwnerSnapshot,
)
from core.continuity.runtime_composition import (
    ENV_RUNTIME_OWNER_ID,
    ENV_RUNTIME_OWNER_VERSION,
    ENV_RUNTIME_STORAGE_ROOT,
    ENV_RUNTIME_TENANT_REF,
    SUPPORTED_LIFECYCLE_OWNER_ID,
    SUPPORTED_LIFECYCLE_OWNER_VERSION,
    ContinuityAcceptedAdmissionGraph,
    ContinuityRuntimeCompositionError,
    ContinuityRuntimeCompositionOwner,
    ContinuityRuntimeConfiguration,
    ContinuityRuntimeConfigurationError,
    ContinuityRuntimeState,
    ContinuityRuntimeStateError,
    compose_continuity_runtime_from_environment,
    load_continuity_runtime_configuration,
)
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceBindingReceipt,
)
from core.continuity.source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

_NOW = datetime(2026, 8, 9, 22, 0, tzinfo=UTC)


def _environment(root: Path, *, tenant: str = "tenant:one") -> dict[str, str]:
    return {
        ENV_RUNTIME_OWNER_ID: SUPPORTED_LIFECYCLE_OWNER_ID,
        ENV_RUNTIME_OWNER_VERSION: SUPPORTED_LIFECYCLE_OWNER_VERSION,
        ENV_RUNTIME_STORAGE_ROOT: str(root),
        ENV_RUNTIME_TENANT_REF: tenant,
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


def _typed_mock(kind: type[Any], **attributes: object) -> Mock:
    value = Mock(spec=kind)
    for name, item in attributes.items():
        setattr(value, name, item)
    return value


def _accepted_graph(*, tenant: str = "tenant:one") -> ContinuityAcceptedAdmissionGraph:
    evaluation = Mock()
    evaluation.admitted_draft_ids = ("draft:accepted",)
    facade_result = _typed_mock(
        ContinuityAdmissionFacadeResult,
        no_runtime_authority=True,
        evaluation=evaluation,
    )
    return ContinuityAcceptedAdmissionGraph(
        principal_context=_typed_mock(ContinuityPrincipalContext),
        authorization_context=_typed_mock(
            ContinuityAuthorizationContext,
            tenant_ref=tenant,
        ),
        source_envelope=_typed_mock(ContinuitySourceEnvelope),
        binding_receipt=_typed_mock(ContinuitySourceBindingReceipt),
        drafts=(_typed_mock(ContinuityObservationDraft),),
        owner_snapshots=(_typed_mock(ContinuityCurrentDecisionOwnerSnapshot),),
        current_decision_evidence=_typed_mock(ContinuityCurrentDecisionEvidence),
        registry=_typed_mock(ContinuityAdmissionRegistry),
        facade_policy=_typed_mock(ContinuityAdmissionFacadePolicy),
        facade_result=facade_result,
        retention_policy=_typed_mock(ContinuityRetentionPolicy),
        recorded_at=_NOW,
    )


class _FakeStore:
    created_paths: list[Path] = []
    ensure_calls = 0
    append_calls = 0
    replay_calls = 0
    fail_ensure = False
    fail_append = False
    fail_replay = False
    artifact: ContinuityAdmissionArtifact | Mock | None = None

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        type(self).created_paths.append(self.path)

    @classmethod
    def reset(cls) -> None:
        cls.created_paths = []
        cls.ensure_calls = 0
        cls.append_calls = 0
        cls.replay_calls = 0
        cls.fail_ensure = False
        cls.fail_append = False
        cls.fail_replay = False
        cls.artifact = None

    def ensure_schema(self) -> None:
        type(self).ensure_calls += 1
        if type(self).fail_ensure:
            raise ContinuityArtifactLifecycleError("schema failure")
        self.path.touch(exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            for table, columns in runtime._EXPECTED_SCHEMA_COLUMNS.items():
                definitions = ", ".join(f"{column} TEXT" for column in columns)
                connection.execute(f"CREATE TABLE IF NOT EXISTS {table}({definitions})")

    def append(
        self,
        artifact: ContinuityAdmissionArtifact,
        *,
        appended_at: datetime,
    ) -> str:
        del appended_at
        type(self).append_calls += 1
        if type(self).fail_append:
            raise ContinuityArtifactLifecycleError("append failure")
        type(self).artifact = artifact
        return "a" * 64

    def replay(
        self,
        artifact_id: str,
        *,
        scope: ContinuityArtifactScope,
        replayed_at: datetime,
    ) -> ContinuityAdmissionArtifact:
        del artifact_id, scope, replayed_at
        type(self).replay_calls += 1
        if type(self).fail_replay:
            raise ContinuityArtifactLifecycleError("replay failure")
        assert type(self).artifact is not None
        return type(self).artifact  # type: ignore[return-value]


@pytest.fixture(autouse=True)
def _reset_fake_store() -> None:
    _FakeStore.reset()


def _patch_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "ContinuityArtifactStore", _FakeStore)


def _patch_artifact(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tenant: str = "tenant:one",
) -> Mock:
    artifact = _typed_mock(
        ContinuityAdmissionArtifact,
        artifact_id="b" * 64,
        tenant_ref=tenant,
        no_runtime_authority=True,
    )
    monkeypatch.setattr(
        runtime.ContinuityAdmissionArtifact,
        "create",
        classmethod(lambda cls, **kwargs: artifact),
    )
    return artifact


def _scope(*, tenant: str = "tenant:one") -> Mock:
    return _typed_mock(ContinuityArtifactScope, tenant_ref=tenant)


def test_no_configuration_means_no_owner_and_no_sqlite(tmp_path: Path) -> None:
    assert load_continuity_runtime_configuration({}) is None
    assert compose_continuity_runtime_from_environment({}) is None
    assert tuple(tmp_path.iterdir()) == ()


@pytest.mark.parametrize(
    "missing",
    [
        ENV_RUNTIME_OWNER_ID,
        ENV_RUNTIME_OWNER_VERSION,
        ENV_RUNTIME_STORAGE_ROOT,
        ENV_RUNTIME_TENANT_REF,
    ],
)
def test_partial_configuration_fails_closed(tmp_path: Path, missing: str) -> None:
    environment = _environment(tmp_path)
    environment.pop(missing)

    with pytest.raises(
        ContinuityRuntimeConfigurationError,
        match="partial Continuity runtime configuration",
    ):
        load_continuity_runtime_configuration(environment)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (ENV_RUNTIME_OWNER_ID, "continuity.unknown", "owner ID"),
        (ENV_RUNTIME_OWNER_VERSION, "999", "owner version"),
    ],
)
def test_unknown_owner_selection_fails_closed(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    environment = _environment(tmp_path)
    environment[field] = value

    with pytest.raises(ContinuityRuntimeConfigurationError, match=message):
        load_continuity_runtime_configuration(environment)


def test_relative_and_missing_storage_roots_fail_closed(tmp_path: Path) -> None:
    relative = _environment(tmp_path)
    relative[ENV_RUNTIME_STORAGE_ROOT] = "relative/data"
    with pytest.raises(ContinuityRuntimeConfigurationError, match="absolute"):
        load_continuity_runtime_configuration(relative)

    missing = _environment(tmp_path / "missing")
    with pytest.raises(ContinuityRuntimeConfigurationError, match="already exist"):
        load_continuity_runtime_configuration(missing)


def test_symlink_storage_root_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")

    with pytest.raises(ContinuityRuntimeConfigurationError, match="symlink"):
        load_continuity_runtime_configuration(_environment(link))


def test_configuration_identity_and_database_derivation_are_deterministic(
    tmp_path: Path,
) -> None:
    first = _configuration(tmp_path)
    second = _configuration(tmp_path)

    assert first == second
    assert first.configuration_id == second.configuration_id
    assert first.database_path() == second.database_path()
    assert first.database_path().parent == tmp_path
    assert first.database_path().name.startswith("continuity-admission-")
    assert "db_path" not in first.__dataclass_fields__


def test_real_startup_validates_schema_and_restart(tmp_path: Path) -> None:
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))

    first = owner.startup()
    second = owner.startup()
    assert first.state is ContinuityRuntimeState.STARTED
    assert second == first
    assert owner.state is ContinuityRuntimeState.STARTED
    assert _configuration(tmp_path).database_path().exists()

    assert owner.shutdown().state is ContinuityRuntimeState.STOPPED
    assert owner.shutdown().state is ContinuityRuntimeState.STOPPED
    assert owner.startup().state is ContinuityRuntimeState.STARTED


def test_shutdown_before_startup_is_deterministic(tmp_path: Path) -> None:
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))

    assert owner.shutdown().state is ContinuityRuntimeState.STOPPED
    assert owner.startup().state is ContinuityRuntimeState.STARTED


def test_concurrent_startup_creates_one_logical_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_store(monkeypatch)
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))

    with ThreadPoolExecutor(max_workers=12) as pool:
        diagnostics = tuple(pool.map(lambda _: owner.startup(), range(24)))

    assert {item.state for item in diagnostics} == {ContinuityRuntimeState.STARTED}
    assert _FakeStore.ensure_calls == 1
    assert len(_FakeStore.created_paths) == 1


def test_startup_failure_keeps_owner_unstarted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_store(monkeypatch)
    _FakeStore.fail_ensure = True
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))

    with pytest.raises(ContinuityArtifactLifecycleError, match="schema failure"):
        owner.startup()
    assert owner.state is ContinuityRuntimeState.NEW
    with pytest.raises(ContinuityRuntimeStateError, match="not started"):
        owner.replay("a" * 64, scope=_scope(), replayed_at=_NOW)


def test_incompatible_existing_schema_fails_closed(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    with sqlite3.connect(configuration.database_path()) as connection:
        connection.execute(
            "CREATE TABLE continuity_admission_artifacts(artifact_id TEXT)"
        )

    owner = ContinuityRuntimeCompositionOwner(configuration)
    with pytest.raises(ContinuityRuntimeCompositionError, match="incompatible"):
        owner.startup()
    assert owner.state is ContinuityRuntimeState.NEW


def test_configuration_and_owner_substitution_fail_closed(tmp_path: Path) -> None:
    configuration = _configuration(tmp_path)
    owner = ContinuityRuntimeCompositionOwner(configuration)
    object.__setattr__(configuration, "tenant_ref", "tenant:substituted")

    with pytest.raises(ContinuityRuntimeConfigurationError, match="substituted"):
        owner.startup()

    configuration = _configuration(tmp_path)
    owner = ContinuityRuntimeCompositionOwner(configuration)
    object.__setattr__(configuration, "lifecycle_owner_id", "continuity.substituted")
    with pytest.raises(ContinuityRuntimeConfigurationError, match="substituted"):
        owner.startup()


def test_bare_inputs_and_unaccepted_facade_result_are_rejected(
    tmp_path: Path,
) -> None:
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))
    with pytest.raises(
        ContinuityRuntimeCompositionError,
        match="complete facade-bound",
    ):
        owner.persist_accepted_admission(  # type: ignore[arg-type]
            object(),
            appended_at=_NOW,
        )

    evaluation = Mock()
    evaluation.admitted_draft_ids = ()
    facade_result = _typed_mock(
        ContinuityAdmissionFacadeResult,
        no_runtime_authority=True,
        evaluation=evaluation,
    )
    with pytest.raises(ContinuityRuntimeCompositionError, match="accepted Draft"):
        ContinuityAcceptedAdmissionGraph(
            principal_context=_typed_mock(ContinuityPrincipalContext),
            authorization_context=_typed_mock(
                ContinuityAuthorizationContext,
                tenant_ref="tenant:one",
            ),
            source_envelope=_typed_mock(ContinuitySourceEnvelope),
            binding_receipt=_typed_mock(ContinuitySourceBindingReceipt),
            drafts=(_typed_mock(ContinuityObservationDraft),),
            owner_snapshots=(
                _typed_mock(ContinuityCurrentDecisionOwnerSnapshot),
            ),
            current_decision_evidence=_typed_mock(
                ContinuityCurrentDecisionEvidence
            ),
            registry=_typed_mock(ContinuityAdmissionRegistry),
            facade_policy=_typed_mock(ContinuityAdmissionFacadePolicy),
            facade_result=facade_result,
            retention_policy=_typed_mock(ContinuityRetentionPolicy),
            recorded_at=_NOW,
        )


def test_append_and_replay_use_only_selected_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_store(monkeypatch)
    artifact = _patch_artifact(monkeypatch)
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))
    owner.startup()

    evidence = owner.persist_accepted_admission(
        _accepted_graph(),
        appended_at=_NOW,
    )
    replayed = owner.replay(
        artifact.artifact_id,
        scope=_scope(),
        replayed_at=_NOW,
    )

    assert evidence.artifact_id == artifact.artifact_id
    assert evidence.append_receipt_id == "a" * 64
    assert evidence.no_runtime_authority is True
    assert replayed is artifact
    assert _FakeStore.append_calls == 1
    assert _FakeStore.replay_calls == 1


def test_cross_tenant_append_and_replay_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_store(monkeypatch)
    _patch_artifact(monkeypatch)
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))
    owner.startup()

    with pytest.raises(ContinuityRuntimeCompositionError, match="tenant"):
        owner.persist_accepted_admission(
            _accepted_graph(tenant="tenant:two"),
            appended_at=_NOW,
        )
    with pytest.raises(ContinuityRuntimeCompositionError, match="tenant"):
        owner.replay("a" * 64, scope=_scope(tenant="tenant:two"), replayed_at=_NOW)


def test_append_and_replay_failures_propagate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_store(monkeypatch)
    artifact = _patch_artifact(monkeypatch)
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))
    owner.startup()

    _FakeStore.fail_append = True
    with pytest.raises(ContinuityArtifactLifecycleError, match="append failure"):
        owner.persist_accepted_admission(_accepted_graph(), appended_at=_NOW)

    _FakeStore.fail_append = False
    owner.persist_accepted_admission(_accepted_graph(), appended_at=_NOW)
    _FakeStore.fail_replay = True
    with pytest.raises(ContinuityArtifactLifecycleError, match="replay failure"):
        owner.replay(artifact.artifact_id, scope=_scope(), replayed_at=_NOW)


def test_concurrent_append_is_serialized_through_one_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_store(monkeypatch)
    _patch_artifact(monkeypatch)
    owner = ContinuityRuntimeCompositionOwner(_configuration(tmp_path))
    owner.startup()
    graph = _accepted_graph()

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = tuple(
            pool.map(
                lambda _: owner.persist_accepted_admission(
                    graph,
                    appended_at=_NOW,
                ),
                range(24),
            )
        )

    assert {item.append_receipt_id for item in results} == {"a" * 64}
    assert _FakeStore.append_calls == 24
    assert len(_FakeStore.created_paths) == 1


def test_runtime_module_has_no_forbidden_side_effect_imports() -> None:
    path = Path("core/continuity/runtime_composition.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
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
    }
    assert imported.isdisjoint(forbidden)


def test_there_is_no_second_non_test_artifact_store_path() -> None:
    allowed = {
        Path("core/continuity/admission_artifact_lifecycle.py"),
        Path("core/continuity/runtime_composition.py"),
    }
    offenders: list[str] = []
    for root in (Path("core"), Path("api")):
        for path in root.rglob("*.py"):
            if path in allowed:
                continue
            if "ContinuityArtifactStore" in path.read_text(encoding="utf-8"):
                offenders.append(str(path))
    assert offenders == []


def test_public_query_path_is_not_wired_to_continuity_runtime() -> None:
    server_source = Path("server.py").read_text(encoding="utf-8")
    assert "continuity_runtime_owner" not in server_source
    assert "persist_accepted_admission" not in server_source


def test_server_registration_installs_exactly_one_lifespan_wrapper() -> None:
    source = Path("api/server_middleware.py").read_text(encoding="utf-8")
    assert source.count("_install_continuity_runtime_lifespan(app)") == 1
    assert "app.state.continuity_runtime_owner" in source
    assert "persist_accepted_admission" not in source
