"""Regression: TruthGate pass must not report promote success when persist fails.

Default flags remain off. force=True exercises the contract without enabling
ENABLE_CONCEPT_PROMOTE / ENABLE_TRUTH_GATE / ENABLE_CONCEPT_EMERGENCE.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.concept_emergence import (
    ProtoConcept,
    get_concept_detector,
    reset_concept_detector,
)
from core.concept_promote import promote_proto_to_l3
from core.epistemic_pipeline import EpistemicResult
from core.esm import EpistemicState


@pytest.fixture(autouse=True)
def _isolated_detector():
    reset_concept_detector()
    yield
    reset_concept_detector()


def _seed_proto() -> ProtoConcept:
    detector = get_concept_detector()
    proto = ProtoConcept(
        proto_id="proto:persist-fail",
        entities=frozenset({"alpha", "beta", "gamma"}),
        co_occur_count=20,
        cross_sessions=10,
        name="persist_fail_concept",
        confidence=0.95,
    )
    detector._protos[proto.proto_id] = proto
    return proto


def _passed_epistemic(proto: ProtoConcept) -> EpistemicResult:
    return EpistemicResult(
        fact_id=proto.proto_id,
        passed=True,
        epistemic_state=EpistemicState.VALIDATED.value,
        reason="passed",
        justification="unit-test TruthGate stub",
        mode="BALANCED",
        confidence=proto.confidence,
        evidence_count=3,
    )


@pytest.mark.asyncio
async def test_promote_proto_persist_none_is_not_passed(monkeypatch):
    """persist_promoted_concept returning None must yield passed=False."""
    proto = _seed_proto()

    monkeypatch.setattr(
        "core.concept_naming.resolve_proto_name",
        AsyncMock(return_value=proto.name),
    )
    monkeypatch.setattr(
        "core.concept_promote.evaluate_proto_for_promote",
        lambda p: _passed_epistemic(p),
    )
    monkeypatch.setattr(
        "core.concept_promote.persist_promoted_concept",
        AsyncMock(return_value=None),
    )

    result = await promote_proto_to_l3(object(), proto.proto_id, force=True)

    assert result.passed is False
    assert result.skipped is False
    assert result.reason == "persist_failed"
    assert result.entity_uuid is None
    assert proto.promoted is False


@pytest.mark.asyncio
async def test_promote_proto_persist_uuid_still_passes(monkeypatch):
    """Successful persist continues to report passed=True with the uuid."""
    proto = _seed_proto()
    stored = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    monkeypatch.setattr(
        "core.concept_naming.resolve_proto_name",
        AsyncMock(return_value=proto.name),
    )
    monkeypatch.setattr(
        "core.concept_promote.evaluate_proto_for_promote",
        lambda p: _passed_epistemic(p),
    )
    monkeypatch.setattr(
        "core.concept_promote.persist_promoted_concept",
        AsyncMock(return_value=stored),
    )

    result = await promote_proto_to_l3(object(), proto.proto_id, force=True)

    assert result.passed is True
    assert result.reason == "passed"
    assert result.entity_uuid == stored
