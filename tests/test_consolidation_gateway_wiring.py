from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import core.consolidation_engine as consolidation_module
from core.consolidation_engine import ConsolidationEngine, ConsolidationReport
from core.promotion_gateway import PromotionRequest


class CandidateStore:
    def __init__(self, *, support_ok: bool = True) -> None:
        self.support_ok = support_ok
        self.support_calls: list[tuple[str, str, str]] = []
        self.direct_validation_calls = 0
        self.transition_calls: list[tuple[str, str, str]] = []

    def promote_esm_to(self, fact_id: str, target: str, by: str) -> bool:
        self.support_calls.append((fact_id, target, by))
        return self.support_ok

    def validate_and_promote(self, *_args: Any, **_kwargs: Any) -> Any:
        self.direct_validation_calls += 1
        raise AssertionError("ConsolidationEngine bypassed PromotionGateway")

    def transition_esm(self, fact_id: str, target: str, by: str) -> bool:
        self.transition_calls.append((fact_id, target, by))
        return True


class SpyGateway:
    instances: list["SpyGateway"] = []
    passed = False
    error: Exception | None = None

    def __init__(self, store: CandidateStore) -> None:
        self.store = store
        self.requests: list[PromotionRequest] = []
        self.__class__.instances.append(self)

    def promote(self, request: PromotionRequest) -> Any:
        self.requests.append(request)
        if self.__class__.error is not None:
            raise self.__class__.error
        return SimpleNamespace(
            receipt=SimpleNamespace(passed=self.__class__.passed)
        )


def _engine(monkeypatch: Any, *, passed: bool) -> tuple[CandidateStore, ConsolidationEngine]:
    SpyGateway.instances.clear()
    SpyGateway.passed = passed
    SpyGateway.error = None
    monkeypatch.setattr(consolidation_module, "PromotionGateway", SpyGateway)
    store = CandidateStore()
    engine = ConsolidationEngine(store)  # type: ignore[arg-type]
    return store, engine


def test_consolidation_validated_candidate_routes_once_through_gateway(
    monkeypatch: Any,
) -> None:
    store, engine = _engine(monkeypatch, passed=True)
    report = ConsolidationReport()

    promoted_as = engine._promote_one("candidate-1", "Validated", report)

    assert store.support_calls == [
        ("candidate-1", "Supported", "consolidation_engine")
    ]
    assert store.direct_validation_calls == 0
    assert len(SpyGateway.instances) == 1
    assert SpyGateway.instances[0].requests == [
        PromotionRequest(
            fact_id="candidate-1",
            requested_by="consolidation_engine",
        )
    ]
    assert promoted_as == "Validated"
    assert report.promoted_validated == 1
    assert report.rejected_by_truthgate == 0
    assert report.errors == 0


def test_gateway_rejection_preserves_truthgate_accounting(
    monkeypatch: Any,
) -> None:
    store, engine = _engine(monkeypatch, passed=False)
    report = ConsolidationReport()

    promoted_as = engine._promote_one("candidate-1", "Validated", report)

    assert store.direct_validation_calls == 0
    assert len(SpyGateway.instances[0].requests) == 1
    assert promoted_as is None
    assert report.promoted_validated == 0
    assert report.rejected_by_truthgate == 1
    assert report.errors == 0


def test_support_ladder_failure_does_not_call_gateway(monkeypatch: Any) -> None:
    SpyGateway.instances.clear()
    SpyGateway.passed = True
    SpyGateway.error = None
    monkeypatch.setattr(consolidation_module, "PromotionGateway", SpyGateway)
    store = CandidateStore(support_ok=False)
    engine = ConsolidationEngine(store)  # type: ignore[arg-type]
    report = ConsolidationReport()

    promoted_as = engine._promote_one("candidate-1", "Validated", report)

    assert promoted_as is None
    assert SpyGateway.instances[0].requests == []
    assert report.rejected_by_truthgate == 1
    assert report.errors == 0


def test_gateway_exception_preserves_existing_error_boundary(monkeypatch: Any) -> None:
    store, engine = _engine(monkeypatch, passed=False)
    SpyGateway.error = RuntimeError("gateway unavailable")
    report = ConsolidationReport()

    promoted_as = engine._promote_one("candidate-1", "Validated", report)

    assert store.direct_validation_calls == 0
    assert promoted_as is None
    assert report.promoted_validated == 0
    assert report.rejected_by_truthgate == 0
    assert report.errors == 1
    assert store.transition_calls == []
