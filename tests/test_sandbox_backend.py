from __future__ import annotations

import pytest

from core.sandbox import (
    ArtifactRef,
    ExecutionReceipt,
    NullBackend,
    SandboxBackend,
    SandboxBackendStateError,
    SandboxBackendUnavailableError,
    SandboxSpec,
    SandboxStatus,
)
from core.sandbox.testing import FakeBackend, FakeOutcome


ZERO_SHA = "0" * 64
ONE_SHA = "1" * 64


def _spec() -> SandboxSpec:
    return SandboxSpec(
        image_ref="python:3.11-slim@sha256:deadbeef",
        command=("python", "-m", "pytest", "-q"),
        workspace_ref="workspace:test",
    )


def test_null_backend_satisfies_protocol_and_fails_closed() -> None:
    backend = NullBackend()
    assert isinstance(backend, SandboxBackend)

    run = backend.prepare(_spec(), attempt_id="attempt-1")
    assert run.backend == "null"
    assert run.status is SandboxStatus.PREPARED

    with pytest.raises(
        SandboxBackendUnavailableError,
        match="no execution capability",
    ):
        backend.execute(run)

    backend.teardown(run)


def test_null_backend_rejects_foreign_run() -> None:
    fake_run = FakeBackend().prepare(_spec(), attempt_id="foreign")
    with pytest.raises(SandboxBackendStateError, match="does not match"):
        NullBackend().teardown(fake_run)


def test_fake_backend_replays_predeclared_outcome_without_execution() -> None:
    artifact = ArtifactRef(path="dist/result.txt", sha256=ZERO_SHA, size_bytes=7)
    backend = FakeBackend(
        FakeOutcome(
            status=SandboxStatus.SUCCEEDED,
            exit_code=0,
            stdout_sha256=ZERO_SHA,
            stderr_sha256=ZERO_SHA,
            artifacts=(artifact,),
            duration_ms=12,
        )
    )
    assert isinstance(backend, SandboxBackend)

    run = backend.prepare(_spec(), attempt_id="attempt-2")
    receipt = backend.execute(run)

    assert receipt.run_id == run.run_id
    assert receipt.status is SandboxStatus.SUCCEEDED
    assert receipt.trusted is False
    assert receipt.canon_admitted is False
    assert receipt.production_authorized is False
    assert backend.collect(receipt) == (artifact,)

    backend.teardown(run)


def test_fake_backend_rejects_duplicate_execution() -> None:
    backend = FakeBackend()
    run = backend.prepare(_spec(), attempt_id="attempt-3")
    backend.execute(run)

    with pytest.raises(SandboxBackendStateError, match="already executed"):
        backend.execute(run)


def test_fake_backend_rejects_duplicate_attempt_identity() -> None:
    backend = FakeBackend()
    backend.prepare(_spec(), attempt_id="attempt-4")

    with pytest.raises(
        SandboxBackendStateError,
        match="attempt_id was already used",
    ):
        backend.prepare(_spec(), attempt_id="attempt-4")


def test_fake_backend_rejects_collection_after_teardown() -> None:
    backend = FakeBackend()
    run = backend.prepare(_spec(), attempt_id="attempt-5")
    receipt = backend.execute(run)
    backend.teardown(run)

    with pytest.raises(SandboxBackendStateError, match="already torn down"):
        backend.collect(receipt)


def test_fake_backend_rejects_foreign_receipt() -> None:
    first = FakeBackend()
    second = FakeBackend()
    run = first.prepare(_spec(), attempt_id="attempt-6")
    receipt = first.execute(run)

    with pytest.raises(SandboxBackendStateError, match="does not belong"):
        second.collect(receipt)


def test_fake_backend_rejects_forged_receipt_for_known_run() -> None:
    backend = FakeBackend()
    run = backend.prepare(_spec(), attempt_id="attempt-7")
    backend.execute(run)
    forged = ExecutionReceipt(
        run_id=run.run_id,
        status=SandboxStatus.SUCCEEDED,
        exit_code=0,
        stdout_sha256=ONE_SHA,
        stderr_sha256=ZERO_SHA,
    )

    with pytest.raises(SandboxBackendStateError, match="identity does not match"):
        backend.collect(forged)
