"""In-memory sandbox test doubles.

Nothing in this module executes commands or accesses external resources. The
FakeBackend only replays a predeclared outcome so lifecycle behavior can be
tested without creating an execution surface.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .backend import SandboxBackendStateError
from .contracts import (
    ArtifactRef,
    ExecutionReceipt,
    SandboxRun,
    SandboxSpec,
    SandboxStatus,
)


_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


@dataclass(frozen=True, slots=True)
class FakeOutcome:
    """Predeclared terminal result returned by FakeBackend."""

    status: SandboxStatus = SandboxStatus.SUCCEEDED
    exit_code: int | None = 0
    stdout_sha256: str = _EMPTY_SHA256
    stderr_sha256: str = _EMPTY_SHA256
    artifacts: tuple[ArtifactRef, ...] = ()
    duration_ms: int = 0


class FakeBackend:
    """Deterministic in-memory backend for contract and orchestration tests only."""

    name = "fake"

    def __init__(self, outcome: FakeOutcome | None = None) -> None:
        self._outcome = outcome or FakeOutcome()
        self._prepared: dict[str, SandboxRun] = {}
        self._attempt_ids: set[str] = set()
        self._receipts: dict[str, str] = {}
        self._torn_down: set[str] = set()

    def prepare(self, spec: SandboxSpec, *, attempt_id: str) -> SandboxRun:
        normalized_attempt_id = attempt_id.strip()
        if normalized_attempt_id in self._attempt_ids:
            raise SandboxBackendStateError("attempt_id was already used")
        run = SandboxRun(
            spec_id=spec.spec_id,
            backend=self.name,
            attempt_id=normalized_attempt_id,
        )
        if run.run_id in self._prepared:
            raise SandboxBackendStateError("run was already prepared")
        self._attempt_ids.add(normalized_attempt_id)
        self._prepared[run.run_id] = run
        return run

    def execute(self, run: SandboxRun) -> ExecutionReceipt:
        self._require_prepared(run)
        if run.run_id in self._torn_down:
            raise SandboxBackendStateError("run was already torn down")
        if run.run_id in self._receipts:
            raise SandboxBackendStateError("run was already executed")

        receipt = ExecutionReceipt(
            run_id=run.run_id,
            status=self._outcome.status,
            exit_code=self._outcome.exit_code,
            stdout_sha256=self._outcome.stdout_sha256,
            stderr_sha256=self._outcome.stderr_sha256,
            artifacts=self._outcome.artifacts,
            duration_ms=self._outcome.duration_ms,
        )
        self._receipts[run.run_id] = receipt.receipt_id
        return receipt

    def collect(self, receipt: ExecutionReceipt) -> tuple[ArtifactRef, ...]:
        expected_receipt_id = self._receipts.get(receipt.run_id)
        if expected_receipt_id is None:
            raise SandboxBackendStateError(
                "receipt does not belong to an executed FakeBackend run"
            )
        if receipt.receipt_id != expected_receipt_id:
            raise SandboxBackendStateError(
                "receipt identity does not match FakeBackend execution"
            )
        if receipt.run_id in self._torn_down:
            raise SandboxBackendStateError("run was already torn down")
        return receipt.artifacts

    def teardown(self, run: SandboxRun) -> None:
        self._require_prepared(run)
        if run.run_id in self._torn_down:
            raise SandboxBackendStateError("run was already torn down")
        self._torn_down.add(run.run_id)
        self._prepared.pop(run.run_id, None)

    def _require_prepared(self, run: SandboxRun) -> None:
        if run.backend != self.name:
            raise SandboxBackendStateError(
                "run backend does not match FakeBackend"
            )
        prepared = self._prepared.get(run.run_id)
        if prepared is None or prepared != run:
            raise SandboxBackendStateError(
                "run was not prepared by this FakeBackend instance"
            )


__all__ = ["FakeBackend", "FakeOutcome"]
