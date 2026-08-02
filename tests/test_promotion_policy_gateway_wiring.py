from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import core.promotion_policy as promotion_policy
from core.promotion_gateway import PromotionRequest
from core.promotion_policy import PromotionConfig, run_graduated_promotion


class SupportedCandidateStore:
    def __init__(self) -> None:
        self.direct_validation_calls = 0
        self.transition_calls: list[tuple[str, str, str]] = []

    def get_all_facts(self) -> list[dict[str, Any]]:
        return [
            {
                "fact_id": "candidate-1",
                "claim": "A sufficiently long supported candidate claim",
                "source": "domain_seed",
                "confidence": 0.9,
                "epistemic_state": "Supported",
                "t_ingestion_start": (
                    datetime.now(UTC) - timedelta(days=2)
                ).isoformat(),
            }
        ]

    def validate_and_promote(self, *_args: Any, **_kwargs: Any) -> Any:
        self.direct_validation_calls += 1
        raise AssertionError("graduated promotion bypassed PromotionGateway")

    def transition_esm(self, fact_id: str, target: str, by: str) -> bool:
        self.transition_calls.append((fact_id, target, by))
        return True


class SpyGateway:
    instances: list["SpyGateway"] = []
    passed = False

    def __init__(self, store: SupportedCandidateStore) -> None:
        self.store = store
        self.requests: list[PromotionRequest] = []
        self.__class__.instances.append(self)

    def promote(self, request: PromotionRequest) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            receipt=SimpleNamespace(passed=self.__class__.passed)
        )


def _run(monkeypatch: Any, *, passed: bool) -> tuple[SupportedCandidateStore, Any]:
    SpyGateway.instances.clear()
    SpyGateway.passed = passed
    monkeypatch.setattr(promotion_policy, "PromotionGateway", SpyGateway)
    store = SupportedCandidateStore()
    report = run_graduated_promotion(
        store,
        cfg=PromotionConfig(validate_min_age_s=0),
        corroboration_override={"candidate-1": 3},
    )
    return store, report


def test_graduated_validated_candidate_routes_once_through_gateway(
    monkeypatch: Any,
) -> None:
    store, report = _run(monkeypatch, passed=True)

    assert store.direct_validation_calls == 0
    assert store.transition_calls == []
    assert len(SpyGateway.instances) == 1
    assert SpyGateway.instances[0].requests == [
        PromotionRequest(
            fact_id="candidate-1",
            requested_by="graduated_promotion",
        )
    ]
    assert report.promoted == {"Supported->Validated": 1}
    assert report.rejected_by_truthgate == 0
    assert report.errors == 0


def test_gateway_rejection_preserves_existing_accounting(
    monkeypatch: Any,
) -> None:
    store, report = _run(monkeypatch, passed=False)

    assert store.direct_validation_calls == 0
    assert len(SpyGateway.instances[0].requests) == 1
    assert report.promoted == {}
    assert report.rejected_by_truthgate == 1
    assert report.errors == 0
    assert report.scanned == 1
