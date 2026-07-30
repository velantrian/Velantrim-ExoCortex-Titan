from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.server_middleware import register_server_middleware
from core.synaptic_shadow import build_synaptic_shadow_preview


def _fact(
    fact_id: str,
    claim: str,
    *,
    score: float = 0.9,
    metadata: dict | None = None,
) -> dict:
    return {
        "fact_id": fact_id,
        "claim": claim,
        "source": "test",
        "confidence": 0.8,
        "retrieval_score": score,
        "epistemic_state": "Validated",
        "metadata": metadata or {},
    }


def test_preview_is_deterministic_and_non_authoritative() -> None:
    facts = [
        _fact("f1", "Alpha is documented.", score=0.8),
        _fact("f2", "Beta remains uncertain.", score=0.7),
    ]
    first = build_synaptic_shadow_preview(facts)
    second = build_synaptic_shadow_preview(reversed(facts))

    assert first == second
    assert first["status"] == "ok"
    assert first["mode"] == "shadow_only"
    assert first["legacy_answer_authoritative"] is True
    assert first["source_mode"] == "legacy_fact_projection"
    assert first["metrics"]["input_facts"] == 2
    assert first["metrics"]["projected_capsules"] == 2
    assert first["metrics"]["selected_claims"] == 2
    assert all(
        claim["truth_confidence"] is None
        for claim in first["context_pack_preview"]["claims"]
    )


def test_projection_preserves_known_claim_modality() -> None:
    fact = _fact("hyp", "This may be true.")
    fact["claim_type"] = "HYPOTHESIS"
    preview = build_synaptic_shadow_preview([fact])

    claim = preview["context_pack_preview"]["claims"][0]
    assert claim["modality"] == "hypothesis"
    assert claim["truth_confidence"] is None


def test_user_report_origin_maps_to_user_report() -> None:
    fact = _fact("reported", "My preferred language is Russian.")
    fact["origin_type"] = "USER_REPORTED"
    fact["reported_only"] = True
    preview = build_synaptic_shadow_preview([fact])

    claim = preview["context_pack_preview"]["claims"][0]
    assert claim["modality"] == "user_report"
    assert claim["truth_confidence"] is None


def test_projection_preserves_exact_legacy_claim_whitespace() -> None:
    claim = "  exact legacy claim  "
    preview = build_synaptic_shadow_preview([_fact("spaced", claim)])

    packed = preview["context_pack_preview"]["claims"]
    assert packed[0]["text"] == claim
    assert packed[0]["evidence"][0]["start_offset"] == 0
    assert packed[0]["evidence"][0]["end_offset"] == len(claim)


def test_malformed_explicit_policy_marker_fails_closed() -> None:
    preview = build_synaptic_shadow_preview(
        [_fact("bad-policy", "must stay out", metadata={"restricted": "false"})]
    )

    assert preview["metrics"]["dispositions"]["exclude"] == 1
    assert preview["context_pack_preview"]["claims"] == []


def test_restricted_projection_never_enters_context_pack() -> None:
    secret = "restricted shadow text"
    preview = build_synaptic_shadow_preview(
        [
            _fact("public", "public text"),
            _fact("secret", secret, metadata={"restricted": True}),
        ]
    )
    serialized_pack = json.dumps(
        preview["context_pack_preview"], ensure_ascii=False, sort_keys=True
    )

    assert secret not in serialized_pack
    assert "legacy-fact:secret" not in serialized_pack
    assert preview["metrics"]["dispositions"]["exclude"] == 1
    assert preview["context_pack_preview"]["meta"]["excluded_count"] == 1


def test_recall_policy_erasure_status_fails_closed() -> None:
    fact = _fact("erased", "erased content must stay out")
    fact["erasure_status"] = "erased"
    preview = build_synaptic_shadow_preview([fact])

    assert preview["metrics"]["dispositions"]["exclude"] == 1
    assert preview["context_pack_preview"]["claims"] == []


def test_recall_policy_collapsed_state_fails_closed() -> None:
    fact = _fact("collapsed", "collapsed content must stay out")
    fact["epistemic_state"] = "Collapsed"
    preview = build_synaptic_shadow_preview([fact])

    assert preview["metrics"]["dispositions"]["exclude"] == 1
    assert preview["context_pack_preview"]["claims"] == []


def test_exact_duplicate_projection_is_deduplicated() -> None:
    fact = _fact("same", "One exact claim")
    preview = build_synaptic_shadow_preview([fact, dict(fact)])

    assert preview["metrics"]["input_facts"] == 2
    assert preview["metrics"]["projected_capsules"] == 1
    assert preview["metrics"]["duplicate_capsules"] == 1


def test_duplicate_policy_merge_is_fail_closed() -> None:
    public = _fact("same", "One exact claim", score=0.9)
    restricted = _fact(
        "same",
        "One exact claim",
        score=0.1,
        metadata={"restricted": True},
    )
    preview = build_synaptic_shadow_preview([public, restricted])

    assert preview["metrics"]["projected_capsules"] == 1
    assert preview["metrics"]["duplicate_capsules"] == 1
    assert preview["metrics"]["dispositions"]["exclude"] == 1
    assert preview["context_pack_preview"]["claims"] == []


def _app(monkeypatch, *, enabled: bool) -> FastAPI:
    if enabled:
        monkeypatch.setenv("ENABLE_SYNAPTIC_SHADOW", "1")
    else:
        monkeypatch.delenv("ENABLE_SYNAPTIC_SHADOW", raising=False)
    app = FastAPI()
    register_server_middleware(app)

    @app.post("/query")
    async def query() -> dict:
        return {
            "query": "q",
            "answer": "legacy answer",
            "llm_answer": None,
            "facts": [_fact("f1", "source claim")],
            "total_facts": 1,
            "mode": "BALANCED",
            "error": None,
            "latency_ms": 1.0,
        }

    @app.post("/other")
    async def other() -> dict:
        return {"answer": "unchanged"}

    return app


def test_middleware_flag_off_leaves_response_unchanged(monkeypatch) -> None:
    with TestClient(_app(monkeypatch, enabled=False)) as client:
        data = client.post("/query").json()

    assert data["answer"] == "legacy answer"
    assert "synaptic_shadow" not in data


def test_middleware_adds_shadow_without_changing_legacy_fields(monkeypatch) -> None:
    with TestClient(_app(monkeypatch, enabled=True)) as client:
        response = client.post("/query")

    data = response.json()
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert data["answer"] == "legacy answer"
    assert data["llm_answer"] is None
    assert data["facts"] == [_fact("f1", "source claim")]
    assert data["synaptic_shadow"]["status"] == "ok"
    assert data["synaptic_shadow"]["legacy_answer_authoritative"] is True


def test_shadow_failure_isolated_from_legacy_response(monkeypatch) -> None:
    import core.synaptic_shadow as shadow_module

    def fail(_facts):
        raise RuntimeError("must not escape")

    monkeypatch.setattr(shadow_module, "build_synaptic_shadow_preview", fail)
    with TestClient(_app(monkeypatch, enabled=True)) as client:
        response = client.post("/query")

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "legacy answer"
    assert data["facts"] == [_fact("f1", "source claim")]
    assert data["synaptic_shadow"]["status"] == "error"
    assert data["synaptic_shadow"]["error_code"] == "RuntimeError"
    assert "must not escape" not in response.text


def test_non_query_response_is_untouched(monkeypatch) -> None:
    with TestClient(_app(monkeypatch, enabled=True)) as client:
        data = client.post("/other").json()

    assert data == {"answer": "unchanged"}


def test_shadow_runner_has_no_remote_or_persistence_imports() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(
        Path("core/synaptic_shadow.py").read_text(encoding="utf-8")
    )
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
        "httpx",
        "requests",
        "sqlite3",
    )

    assert not any(
        module == prefix or module.startswith(prefix + ".")
        for module in imported
        for prefix in forbidden_prefixes
    )


def test_non_200_query_response_is_untouched(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_SYNAPTIC_SHADOW", "1")
    app = FastAPI()
    register_server_middleware(app)

    @app.post("/query")
    async def query_error():
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"error": "legacy"})

    with TestClient(app) as client:
        response = client.post("/query")

    assert response.status_code == 400
    assert response.json() == {"error": "legacy"}
