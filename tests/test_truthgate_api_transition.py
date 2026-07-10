"""
tests/test_truthgate_api_transition.py — TruthGate API validation-bypass regression
====================================================================================

Confirmed bypass (pre-fix): PATCH /facts/{fact_id}/transition called
transition_esm() directly, which only validates ESM-transition legality
(I50) and never calls TruthGate. An authenticated API client could walk a
fact Observed -> Hypothesized -> Supported -> Validated (three legal PATCH
calls) without ever satisfying evidence/confidence thresholds — silently
bypassing the evidence gate documented as the project's core trust
boundary (invariant I68).

Fix: PATCH /facts/{fact_id}/transition now routes any transition targeting
'Validated' through core.memory.validate_and_promote(), the single
canonical function that runs TruthGate.evaluate() and only mutates state
on a passing verdict. All other targets are unaffected.

This file is the adversarial regression suite for that fix:
  - a fact that does not satisfy TruthGate cannot reach Validated via the API;
  - a fact that DOES satisfy TruthGate can reach Validated via the API;
  - ordinary non-validation ESM transitions remain functional;
  - Ring Zero / ImmutableCore protections are unchanged;
  - authenticated access is still required;
  - a rejected validation is atomic (no state mutation, no partial history).
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """Isolated FastAPI TestClient, mirroring tests/test_server_integration.py."""
    db_path = str(tmp_path / "truthgate_api.db")
    ngram_db_path = str(tmp_path / "truthgate_api_ngram.db")

    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", ngram_db_path)
    monkeypatch.setenv("CORE_BLOCKS_DB", str(tmp_path / "blocks.db"))
    monkeypatch.setenv("NOTEBOOK_DB", str(tmp_path / "notebook.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
    monkeypatch.setenv("ENABLE_VELUM", "0")

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.")):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        import server as srv
        from core.feature_config import clear_config_cache
    except ImportError as exc:
        pytest.skip(f"Сервер недоступен ({exc})")

    clear_config_cache()

    with TestClient(srv.app) as client:
        client.headers.update({"X-Api-Key": "test-key"})
        yield client, srv


def _create_fact(client, *, fact_id, confidence, evidence_refs=None):
    metadata = {}
    if evidence_refs is not None:
        metadata["evidence_refs"] = evidence_refs
    r = client.post("/facts", json={
        "fact_id":    fact_id,
        "claim":      f"claim for {fact_id}",
        "source":     "integration-test",
        "confidence": confidence,
        "metadata":   metadata,
    })
    assert r.status_code in (200, 201), f"POST /facts failed: {r.status_code} {r.text}"
    return r.json()


def _patch_transition(client, fact_id, new_state):
    return client.patch(f"/facts/{fact_id}/transition", json={"new_state": new_state})


class TestTruthGateApiBypassClosed:
    """The core reproduction + regression coverage for the closed bypass."""

    def test_weak_fact_cannot_reach_validated_via_api(self, test_client):
        """
        THE BYPASS REPRODUCTION.

        Pre-fix, this exact sequence (three legal ESM hops via the public
        PATCH endpoint) reached 'Validated' with zero evidence gating:
        confidence=0.3, no evidence_refs — fails BALANCED (min_confidence=0.7,
        min_evidence=2) by a wide margin on both axes.
        """
        client, _ = test_client
        _create_fact(client, fact_id="weak_fact", confidence=0.3)

        r = _patch_transition(client, "weak_fact", "Hypothesized")
        assert r.status_code == 200, r.text
        r = _patch_transition(client, "weak_fact", "Supported")
        assert r.status_code == 200, r.text

        # The exploit step: Supported -> Validated with no evidence.
        r = _patch_transition(client, "weak_fact", "Validated")
        assert r.status_code == 422, (
            f"BYPASS STILL OPEN: expected 422 (TruthGate rejection), got "
            f"{r.status_code} {r.text}"
        )
        body = r.json()["detail"]
        assert body["error"] == "truth_gate_rejected"
        assert body["reason"] in ("low_confidence", "insufficient_evidence")

        # Atomicity: state must remain exactly where it was (Supported).
        r = client.get("/facts/weak_fact")
        assert r.status_code == 200
        fact = r.json()
        assert fact["epistemic_state"] == "Supported", (
            "State mutated despite TruthGate rejection — not atomic."
        )
        # No misleading audit entry: last history record must not claim Validated.
        history = fact.get("history", [])
        assert not any(h.get("state") == "Validated" for h in history), (
            "History contains a 'Validated' entry despite rejected verdict."
        )

    def test_strong_fact_can_reach_validated_via_api(self, test_client):
        """Positive control: a fact that genuinely satisfies TruthGate (BALANCED:
        confidence>=0.7, evidence>=2) IS allowed through the same endpoint."""
        client, _ = test_client
        _create_fact(
            client, fact_id="strong_fact", confidence=0.85,
            evidence_refs=["src1", "src2"],
        )

        assert _patch_transition(client, "strong_fact", "Hypothesized").status_code == 200
        assert _patch_transition(client, "strong_fact", "Supported").status_code == 200

        r = _patch_transition(client, "strong_fact", "Validated")
        assert r.status_code == 200, r.text
        assert r.json()["epistemic_state"] == "Validated"

        r = client.get("/facts/strong_fact")
        assert r.json()["epistemic_state"] == "Validated"

    def test_ordinary_non_validation_transitions_still_work(self, test_client):
        """Observed->Hypothesized, Hypothesized->Supported, Validated->Contradicted,
        Contradicted->Deprecated must all remain unaffected by the gate."""
        client, _ = test_client
        _create_fact(
            client, fact_id="lifecycle_fact", confidence=0.9,
            evidence_refs=["a", "b", "c"],
        )

        r = _patch_transition(client, "lifecycle_fact", "Hypothesized")
        assert r.status_code == 200, r.text
        assert r.json()["epistemic_state"] == "Hypothesized"

        r = _patch_transition(client, "lifecycle_fact", "Supported")
        assert r.status_code == 200, r.text
        assert r.json()["epistemic_state"] == "Supported"

        r = _patch_transition(client, "lifecycle_fact", "Validated")
        assert r.status_code == 200, r.text
        assert r.json()["epistemic_state"] == "Validated"

        r = _patch_transition(client, "lifecycle_fact", "Contradicted")
        assert r.status_code == 200, r.text
        assert r.json()["epistemic_state"] == "Contradicted"

        r = _patch_transition(client, "lifecycle_fact", "Deprecated")
        assert r.status_code == 200, r.text
        assert r.json()["epistemic_state"] == "Deprecated"

    def test_ring_zero_protection_unchanged_for_validated_target(self, test_client):
        """Ring Zero IDs must be rejected (403) even when the target is
        'Validated' and even if the ID doesn't exist yet in the store —
        matching transition_esm()'s existing fact_id-based check order."""
        client, _ = test_client

        r = _patch_transition(client, "VALUES_CORE", "Validated")
        assert r.status_code == 403, r.text

        r = _patch_transition(client, "RING_ZERO", "Contradicted")
        assert r.status_code == 403, r.text

    def test_immutable_core_target_still_rejected(self, test_client):
        """'ImmutableCore' as a target remains reserved for Ring Zero seeding,
        unaffected by the new Validated-specific gate."""
        client, _ = test_client
        _create_fact(client, fact_id="attempt_immutable", confidence=0.9,
                      evidence_refs=["a", "b"])
        r = _patch_transition(client, "attempt_immutable", "ImmutableCore")
        assert r.status_code == 403, r.text

    def test_illegal_esm_jump_still_rejected_even_with_strong_evidence(self, test_client):
        """A direct Observed -> Validated jump is illegal per ESM_TRANSITIONS
        regardless of evidence quality — TruthGate is an additional gate on
        top of ESM legality, not a replacement for it."""
        client, _ = test_client
        _create_fact(
            client, fact_id="jump_fact", confidence=0.95,
            evidence_refs=["a", "b", "c"],
        )
        r = _patch_transition(client, "jump_fact", "Validated")
        assert r.status_code == 400, r.text
        r = client.get("/facts/jump_fact")
        assert r.json()["epistemic_state"] == "Observed"

    def test_authentication_still_required(self, test_client):
        """The endpoint must still require a valid API key — the fix must not
        weaken or bypass the pre-existing auth dependency."""
        client, _ = test_client
        _create_fact(client, fact_id="auth_check_fact", confidence=0.9,
                      evidence_refs=["a", "b"])

        no_key_client = client
        headers_backup = dict(no_key_client.headers)
        try:
            del no_key_client.headers["X-Api-Key"]
            r = no_key_client.patch(
                "/facts/auth_check_fact/transition",
                json={"new_state": "Validated"},
            )
            assert r.status_code in (401, 403), r.text

            no_key_client.headers["X-Api-Key"] = "wrong-key"
            r = no_key_client.patch(
                "/facts/auth_check_fact/transition",
                json={"new_state": "Hypothesized"},
            )
            assert r.status_code in (401, 403), r.text
        finally:
            no_key_client.headers.clear()
            no_key_client.headers.update(headers_backup)

    def test_not_found_fact_returns_404_not_422(self, test_client):
        """A nonexistent fact_id targeting Validated must 404, not be
        misreported as a TruthGate rejection."""
        client, _ = test_client
        r = _patch_transition(client, "does_not_exist_at_all", "Validated")
        assert r.status_code == 404, r.text
