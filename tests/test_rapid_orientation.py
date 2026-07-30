from __future__ import annotations

import ast
from pathlib import Path
from threading import Event

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.server_middleware as middleware_module
from api.server_middleware import register_server_middleware
from core.policy_kernel import EffectivePolicy, PolicySnapshot
from core.rapid_orientation import build_rapid_orientation_receipt
from core.synaptic_shadow import build_synaptic_shadow_preview


def _fact(
    fact_id: str,
    claim: str,
    *,
    claim_type: str = "INTERPRETATION",
) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "claim": claim,
        "source": "test",
        "confidence": 0.8,
        "retrieval_score": 0.9,
        "epistemic_state": "Validated",
        "claim_type": claim_type,
        "metadata": {},
    }


def _policy(*, healthy: bool = True) -> PolicySnapshot:
    return PolicySnapshot(
        snapshot_id="policy-snapshot-1",
        policy_version="titan-policy-v2",
        captured_at="2026-07-30T00:00:00+00:00",
        effective=EffectivePolicy(),
        supervisor_mode="normal" if healthy else "unavailable",
        writes_allowed=healthy,
        source="verified_local_runtime" if healthy else "safe_default_fail_closed",
        reason_code="ok" if healthy else "policy_dependency_unavailable",
    )


def _receipt(query: str, facts: list[dict[str, object]]) -> dict[str, object]:
    return build_rapid_orientation_receipt(
        query,
        build_synaptic_shadow_preview(facts),
        _policy(),
    )


def test_rco1_is_deterministic_for_equivalent_evidence_order() -> None:
    facts = [
        _fact("a", "Alpha is relevant."),
        _fact("b", "Beta is relevant."),
    ]

    first = _receipt("Где сервер? Коротко.", facts)
    second = _receipt("Где сервер? Коротко.", list(reversed(facts)))

    assert first == second
    assert first["status"] == "ok"
    assert first["mode"] == "shadow_only"
    assert first["legacy_answer_authoritative"] is True
    assert first["authoritative_route"] == "LEGACY_QUERY"
    assert first["action_attempted"] is False
    assert first["proposal"]["route"] == "FAST_LOCAL"
    assert first["proposal"]["fallback"] == "LEGACY_QUERY"
    assert first["proposal"]["compute_path_mapping_id"] is None
    assert first["metrics"]["model_calls"] == 0
    assert first["metrics"]["remote_calls"] == 0
    assert first["metrics"]["mutations_attempted"] == 0


def test_empty_goal_proposes_clarification_without_execution() -> None:
    receipt = _receipt("", [])

    assert receipt["proposal"]["route"] == "CLARIFY"
    assert receipt["proposal"]["route_payload"]["blocking_ambiguity_ids"] == [
        "missing_goal",
        "no_admitted_evidence",
    ]
    assert receipt["action_attempted"] is False


def test_high_risk_query_with_thin_evidence_requests_evidence() -> None:
    receipt = _receipt(
        "Проверь медицинское лечение и диагноз.",
        [_fact("one", "A single interpretation is available.")],
    )

    assert receipt["proposal"]["route"] == "REQUEST_EVIDENCE"
    assert "high_risk_evidence_insufficient" in receipt["proposal"]["critical_gaps"]
    assert receipt["proposal"]["compute_path"] == "verify_path"


def test_conflict_proposes_deliberate_local_and_surfaces_pointer() -> None:
    facts = [
        _fact("same", "One exact claim", claim_type="HYPOTHESIS"),
        _fact("same", "One exact claim", claim_type="OPINION"),
    ]
    receipt = _receipt("Сравни эти утверждения.", facts)

    assert receipt["proposal"]["route"] == "REQUEST_EVIDENCE"
    assert "material_conflict_requires_review" in receipt["proposal"]["critical_gaps"]
    assert receipt["metrics"]["contradictions"] == 1
    assert receipt["projection"]["contradictions"]


def test_healthy_snapshot_identity_is_copied_to_projection_and_proposal() -> None:
    receipt = _receipt(
        "Объясни архитектуру подробно.",
        [_fact("architecture", "The module has a bounded interface.")],
    )

    assert receipt["policy_snapshot_id"] == "policy-snapshot-1"
    assert receipt["projection"]["policy_snapshot_id"] == "policy-snapshot-1"
    assert receipt["proposal"]["policy_snapshot_id"] == "policy-snapshot-1"
    assert receipt["projection"]["policy_version"] == "titan-policy-v2"
    assert receipt["proposal"]["policy_version"] == "titan-policy-v2"
    assert receipt["proposal"]["route"] == "DELIBERATE_LOCAL"


def test_unhealthy_policy_snapshot_rejects_proposal_fail_closed() -> None:
    receipt = build_rapid_orientation_receipt(
        "Где сервер?",
        build_synaptic_shadow_preview([_fact("a", "Alpha")]),
        _policy(healthy=False),
    )

    assert receipt["status"] == "rejected"
    assert receipt["failure_code"] == "policy_snapshot_unhealthy"
    assert receipt["proposal"] is None
    assert receipt["authoritative_route"] == "LEGACY_QUERY"
    assert receipt["metrics"]["policy_non_interference"] is True


def test_failed_synaptic_preview_is_not_promoted_to_route() -> None:
    receipt = build_rapid_orientation_receipt(
        "Где сервер?",
        {
            "schema_version": "synaptic.shadow-preview.v1",
            "status": "error",
        },
        _policy(),
    )

    assert receipt["status"] == "rejected"
    assert receipt["failure_code"] == "shadow_preview_unavailable"
    assert receipt["proposal"] is None
    assert receipt["legacy_answer_authoritative"] is True


def test_rco1_has_no_remote_persistence_or_write_imports() -> None:
    tree = ast.parse(Path("core/rapid_orientation.py").read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    forbidden_prefixes = (
        "core.llm_router",
        "core.remote_egress",
        "core.memory",
        "core.truth_gate",
        "core.canonical_write",
        "httpx",
        "requests",
        "sqlite3",
    )

    assert not any(
        module == prefix or module.startswith(prefix + ".")
        for module in imported
        for prefix in forbidden_prefixes
    )


def test_worker_receives_query_but_preserves_legacy_response(monkeypatch) -> None:
    import core.policy_kernel as policy_module
    import core.rapid_orientation as orientation_module

    captured: dict[str, str] = {}
    completed = Event()

    class _Kernel:
        def capture_snapshot(self) -> PolicySnapshot:
            return _policy()

    def capture_receipt(query, preview, policy_snapshot):
        captured["query"] = query
        completed.set()
        return {
            "status": "ok",
            "metrics": {
                "model_calls": 0,
                "remote_calls": 0,
                "mutations_attempted": 0,
            },
        }

    monkeypatch.setattr(policy_module, "get_policy_kernel", lambda: _Kernel())
    monkeypatch.setattr(
        orientation_module,
        "build_rapid_orientation_receipt",
        capture_receipt,
    )
    monkeypatch.setattr(
        middleware_module,
        "_SHADOW_DISPATCHER",
        middleware_module._SynapticShadowDispatcher(),
    )
    monkeypatch.setenv("ENABLE_SYNAPTIC_SHADOW", "1")
    monkeypatch.setenv("ENABLE_RCO_SHADOW", "1")

    app = FastAPI()
    register_server_middleware(app)

    @app.post("/query")
    async def query() -> dict[str, object]:
        return {
            "query": "Проверь архитектуру",
            "answer": "legacy answer",
            "facts": [_fact("a", "Alpha")],
        }

    with TestClient(app) as client:
        response = client.post("/query")
        assert completed.wait(timeout=2)

    assert response.status_code == 200
    assert response.json()["answer"] == "legacy answer"
    assert response.json()["synaptic_shadow"]["status"] == "queued"
    assert captured["query"] == "Проверь архитектуру"
