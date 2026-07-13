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

Follow-up fix #1 (review finding on PR #6, TOCTOU race): validate_and_promote()
read a fact, evaluated TruthGate against that snapshot, and only then wrote
'Validated' — with no DB-level guard against the fact changing in between.
A concurrent POST /facts upsert that weakened confidence/evidence (while
leaving epistemic_state alone, e.g. Supported -> Supported) could slip a
fact that no longer passed TruthGate into 'Validated'. Same fix also moved
the ESM-transition-legality check (I50) to run *before* TruthGate.evaluate(),
so an illegal direct Observed -> Validated jump is always 400, never 422,
regardless of how strong or weak the fact's evidence is.

Follow-up fix #2 (independent Codex re-review of the fix above found 5 more
issues, all addressed here):
  1. The CAS token was derived via get_fact(), which prefers the L0 cache.
     store_fact()'s no-op upsert path (identical claim/source/confidence)
     publishes a fresh `updated_at` to L0 without touching the durable SQL
     row — so an idempotent re-POST could poison the CAS token and cause a
     legitimate promotion to 409 forever. Fixed: validate_and_promote() now
     reads its TruthGate snapshot and CAS token from
     SQLiteGraphStore._get_fact_durable(), which bypasses L0 entirely.
  2. transition_esm()'s `False` return (fact vanished) was silently ignored,
     so a fact deleted between the TruthGate check and the write could still
     get a `passed=True` verdict. Fixed: the guarded write's success/failure
     is checked explicitly; any failure (including deletion) is reported as
     `concurrent_modification`/409, never as a false success.
  3. The guarded write went through transition_esm(), which does its own
     fresh get_fact() + ESM-legality check — a concurrent state change could
     make the *new* state's target illegal, raising ValueError/400 for what
     was actually a race, not a bad request. Fixed: a new, dedicated
     SQLiteGraphStore._promote_to_validated_cas() performs one atomic
     conditional UPDATE (`WHERE fact_id=? AND epistemic_state=? AND
     updated_at=?`) directly against the original durable snapshot — no
     fresh read, no re-check that could raise ValueError for a race.
  4. _snapshot_before_change() (the VersionStore audit pre-image) ran before
     the CAS-guarded write, so a rejected/raced promotion still left a
     `fact_versions` record for a transition that never happened. Fixed:
     the snapshot is now written only after the guarded UPDATE commits.
  5. docs/REVIEWER_README.md claimed PATCH was the *only* public path to
     Validated; POST /query's pipeline path can also promote facts (under
     its own, uncorrelated policy). Docs corrected to state this precisely.

Follow-up fix #3 (second independent Codex re-review of fix #2 found 3 more
issues, all addressed here):
  1. store_fact()'s no-op check (fix #2 item 1) didn't compare metadata, so
     a re-POST with the same claim/source/confidence but NEW evidence_refs
     still took the no-op branch — which performs no SQL write at all. Since
     validate_and_promote() now reads L1 directly (fix #2 item 1), it never
     saw that freshly supplied evidence, and a legitimate promotion was
     wrongly rejected as insufficient_evidence. Fixed: metadata is now part
     of the no-op comparison — a metadata difference falls through to the
     real upsert, which persists it and bumps updated_at like any other
     real change.
  2. _get_fact_durable() published its snapshot to L0 before the CAS-guarded
     write ran. If that write then lost the race, L0 was left caching a
     now-stale pre-race row for every other reader in the process until the
     next real write or eviction. Fixed: _get_fact_durable() no longer
     publishes to L0 at all — its only caller always re-reads durably on
     every call and gets no benefit from populating the cache.
  3. The use_json_insert=False fallback branch of _promote_to_validated_cas()
     judged success from the preceding SELECT, not the guarded UPDATE's own
     rowcount — a race between those two statements could report a false
     success. Fixed: success is now judged from the UPDATE's rowcount, same
     as the use_json_insert=True branch already did correctly.

This file is the adversarial regression suite for all of the above:
  - a fact that does not satisfy TruthGate cannot reach Validated via the API;
  - a fact that DOES satisfy TruthGate can reach Validated via the API;
  - ordinary non-validation ESM transitions remain functional;
  - Ring Zero / ImmutableCore protections are unchanged;
  - authenticated access is still required;
  - a rejected validation is atomic (no state mutation, no partial history);
  - an illegal ESM jump is 400 regardless of evidence strength (strong AND weak);
  - a fact concurrently weakened between the TruthGate check and the write
    (threading.Barrier-pinned) cannot be promoted, and leaves no partial
    mutation and no stray fact_versions snapshot;
  - an idempotent re-POST (no durable change) never causes a false 409;
  - a fact deleted between the check and the write never reports a false
    200/passed=True — it's concurrent_modification/409;
  - a concurrent state change (to a state where Validated would be illegal)
    is reported as concurrent_modification/409, never a misleading 400.
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

    def test_illegal_esm_jump_still_rejected_with_weak_evidence(self, test_client):
        """Same illegal direct Observed -> Validated jump, but with evidence
        that would ALSO fail TruthGate on its own. Must still be 400
        (illegal ESM transition), never 422 (truth_gate_rejected) — ESM
        legality is checked before TruthGate runs, so a weak fact doesn't
        get a different status code than a strong one for the same illegal
        jump."""
        client, _ = test_client
        _create_fact(client, fact_id="weak_jump_fact", confidence=0.2)
        r = _patch_transition(client, "weak_jump_fact", "Validated")
        assert r.status_code == 400, r.text
        r = client.get("/facts/weak_jump_fact")
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

    def test_idempotent_repost_does_not_cause_permanent_409(self, test_client, monkeypatch):
        """
        API-level companion to
        test_idempotent_store_fact_call_does_not_poison_cas_token: a
        harmless repeated POST /facts followed by PATCH .../transition to
        Validated must succeed through the real endpoint, not just at the
        store level. Note this does NOT reliably exercise the L0-poisoning
        mechanism itself (review finding #1, PR #6) end-to-end: this
        endpoint also calls link_raw_to_fact() after store_fact(), which
        invalidates the L0 cache entry as an (incidental, not guaranteed —
        it's skipped if store_raw_text() fails) side effect, independently
        of this fix. The store-level test is the precise regression check
        for the actual CAS-poisoning bug; this one guards the
        endpoint-level outcome regardless of mechanism.

        ENABLE_EPISODE_DEDUP is disabled here: by default POST /facts
        short-circuits on a claim/source match (_find_duplicate_fact)
        before ever reaching store_fact() at all.
        """
        monkeypatch.setenv("ENABLE_EPISODE_DEDUP", "0")
        client, _ = test_client
        _create_fact(
            client, fact_id="idempotent_fact", confidence=0.85,
            evidence_refs=["a", "b"],
        )
        assert _patch_transition(client, "idempotent_fact", "Hypothesized").status_code == 200
        assert _patch_transition(client, "idempotent_fact", "Supported").status_code == 200

        # Idempotent re-POST: identical claim/source/confidence triggers
        # store_fact()'s no-op branch (the durable SQL row is untouched).
        r = client.post("/facts", json={
            "fact_id":    "idempotent_fact",
            "claim":      "claim for idempotent_fact",
            "source":     "integration-test",
            "confidence": 0.85,
            "metadata":   {"evidence_refs": ["a", "b"]},
        })
        assert r.status_code in (200, 201), r.text
        assert not r.json().get("deduplicated"), (
            "setup: request was deduplicated instead of reaching "
            "store_fact()'s no-op branch — test doesn't exercise the "
            "intended code path"
        )

        r = _patch_transition(client, "idempotent_fact", "Validated")
        assert r.status_code == 200, (
            f"Legitimate promotion falsely rejected after a harmless "
            f"idempotent re-POST: {r.status_code} {r.text}"
        )
        assert r.json()["epistemic_state"] == "Validated"

    def test_idempotent_store_fact_call_does_not_poison_cas_token(self, tmp_path):
        """
        Store-level version of the same regression, independent of the
        HTTP-layer dedup feature flag: two identical store_fact() calls
        (the second a pure no-op — same claim/source/confidence) followed
        by validate_and_promote() must succeed. This is the precise
        scenario review finding #1 (PR #6) describes.
        """
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore(str(tmp_path / "idempotent_store_level.db"))
        fact = {
            "fact_id":    "idempotent_fact",
            "claim":      "idempotent claim",
            "source":     "integration-test",
            "confidence": 0.85,
            "metadata":   {"evidence_refs": ["a", "b"]},
        }
        store.store_fact(fact)
        store.transition_esm("idempotent_fact", "Hypothesized")
        store.transition_esm("idempotent_fact", "Supported")

        is_new = store.store_fact(dict(fact))
        assert is_new is False, "setup: expected a no-op upsert (not a new insert)"

        verdict = store.validate_and_promote("idempotent_fact", by="test")
        assert verdict.passed is True, (
            f"Legitimate promotion falsely rejected after a harmless "
            f"idempotent store_fact() call: reason={verdict.reason!r} "
            f"justification={verdict.justification!r}"
        )
        assert store.get_fact("idempotent_fact")["epistemic_state"] == "Validated"


def _run_cas_race(store, fact_id, racer_action, *, mode=None):
    """
    Shared harness for the store-level concurrency regressions below.

    Instruments SQLiteGraphStore._promote_to_validated_cas() — the single
    atomic guarded write validate_and_promote() performs — to rendezvous
    with a concurrent "racer" thread right after TruthGate.evaluate() has
    passed the original snapshot, but before the guarded UPDATE runs. This
    is the exact window review finding #3 (PR #6) was about: the guarded
    write must be evaluated against the ORIGINAL snapshot, not a fresh
    re-read, so racer_action() runs and completes before the real guarded
    write ever executes.

    Returns (verdict, errors) — errors is a list of any exceptions raised
    in either thread (should be empty; assert on it before trusting verdict).
    """
    import threading

    from core.truth_gate import CognitiveMode

    if mode is None:
        mode = CognitiveMode.BALANCED

    rendezvous = threading.Barrier(2, timeout=5)
    racer_done = threading.Event()
    results: dict = {}
    errors: list = []

    original_cas = store._promote_to_validated_cas

    def instrumented_cas(fid, expected_state, expected_updated_at, durable_snapshot, by):
        rendezvous.wait(timeout=5)
        racer_done.wait(timeout=5)
        return original_cas(fid, expected_state, expected_updated_at, durable_snapshot, by)

    store._promote_to_validated_cas = instrumented_cas

    def run_validator():
        try:
            results["verdict"] = store.validate_and_promote(
                fact_id, by="validator-thread", mode=mode,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    def run_racer():
        try:
            rendezvous.wait(timeout=5)
            racer_action()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            racer_done.set()

    t_validator = threading.Thread(target=run_validator)
    t_racer = threading.Thread(target=run_racer)
    t_validator.start()
    t_racer.start()
    t_validator.join(timeout=10)
    t_racer.join(timeout=10)

    return results.get("verdict"), errors


class TestValidateAndPromoteConcurrencyGuard:
    """
    TOCTOU regressions (review findings on PR #6): validate_and_promote()
    reads a fact durably, evaluates TruthGate against that snapshot, then
    writes 'Validated' via a single atomic guarded UPDATE against that same
    snapshot. These are plain store-level tests (not API-level) so each
    race can be pinned deterministically with threading.Barrier/Event
    around the exact evaluate -> write window, independent of
    TestClient/event-loop threading behavior.
    """

    def _make_strong_supported_fact(self, tmp_path, db_name, fact_id="race_fact"):
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore(str(tmp_path / db_name))
        store.store_fact({
            "fact_id":    fact_id,
            "claim":      "race claim",
            "source":     "integration-test",
            "confidence": 0.85,
            "metadata":   {"evidence_refs": ["src1", "src2"]},
        })
        store.transition_esm(fact_id, "Hypothesized")
        store.transition_esm(fact_id, "Supported")
        # Sanity: the snapshot the validator will read genuinely passes
        # BALANCED (confidence=0.85 >= 0.7, evidence=2 >= 2).
        assert store.get_fact(fact_id)["epistemic_state"] == "Supported"
        return store

    def test_concurrent_weakening_blocks_promotion(self, tmp_path):
        """Content-only race (state unchanged): a concurrent POST /facts
        upsert weakens confidence/evidence while leaving epistemic_state at
        'Supported' — the exact race an epistemic_state-only CAS guard
        would miss."""
        from core.version_store import VersionStore

        store = self._make_strong_supported_fact(tmp_path, "toctou_weaken.db")

        def weaken():
            store.store_fact({
                "fact_id":    "race_fact",
                "claim":      "race claim",
                "source":     "integration-test",
                "confidence": 0.1,
                "metadata":   {"evidence_refs": []},
            })

        versions_before = VersionStore(store.db_path).count_versions("race_fact")
        verdict, errors = _run_cas_race(store, "race_fact", weaken)

        assert not errors, f"unexpected thread errors: {errors!r}"
        assert verdict is not None, "validator thread did not produce a verdict"
        assert verdict.passed is False, (
            "BYPASS: promotion succeeded despite the fact being weakened "
            "concurrently between the TruthGate check and the write."
        )
        assert verdict.reason == "concurrent_modification", verdict.reason

        # Atomicity: the fact must be exactly what the racer left it as —
        # not Validated, and no misleading 'Validated' history entry.
        final = store.get_fact("race_fact")
        assert final["epistemic_state"] == "Supported"
        assert final["confidence"] == 0.1
        assert not any(h.get("state") == "Validated" for h in final.get("history", [])), (
            "History contains a 'Validated' entry despite the concurrent-"
            "modification rejection — not atomic."
        )
        # Review finding #4 (PR #6): a rejected CAS attempt must not create
        # a VersionStore audit snapshot for a transition that never happened.
        # The racer's own store_fact() weakening IS a real, successful
        # mutation and legitimately creates exactly one snapshot of its own
        # (the pre-image before it weakened the fact) — the invariant under
        # test is that the *rejected* validate_and_promote() attempt adds
        # nothing on top of that, not that the count stays flat.
        versions_after = VersionStore(store.db_path).count_versions("race_fact")
        assert versions_after == versions_before + 1, (
            f"fact_versions changed by {versions_after - versions_before} "
            f"(expected exactly +1, for the racer's own legitimate "
            f"weakening snapshot) — the rejected CAS attempt appears to "
            f"have created its own misleading audit record on top."
        )

    def test_get_fact_durable_does_not_populate_l0(self, tmp_path):
        """Regression for the 2nd independent Codex re-review, finding #2:
        _get_fact_durable() must not cache its result. In a multi-worker
        deployment, each worker has its own in-process L0 — populating it
        from a pre-CAS snapshot that then loses its guarded-write race
        would leave THIS worker's cache holding a now-stale row for every
        other reader until an unrelated write or eviction touches it. The
        fix removes the cache-publish entirely, so this checks that
        directly: an uncached fact_id stays uncached in L0 after a durable
        read, regardless of what the guarded write that follows does."""
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore(str(tmp_path / "l0_no_populate.db"))
        store.store_fact({
            "fact_id": "durable_fact", "claim": "durable claim",
            "source": "integration-test", "confidence": 0.9, "metadata": {},
        })
        # store_fact() itself populates L0 on write (expected, unrelated
        # behavior) — evict it explicitly to isolate _get_fact_durable()'s
        # own caching behavior from that.
        store._l0_del("durable_fact")
        assert store._l0_get("durable_fact") is None, "setup: expected uncached"

        result = store._get_fact_durable("durable_fact")

        assert result is not None
        assert result["confidence"] == 0.9
        assert store._l0_get("durable_fact") is None, (
            "_get_fact_durable() populated L0 — a pre-CAS snapshot that "
            "later loses its guarded-write race would leave this cached "
            "indefinitely for every other reader in this process."
        )

    def test_concurrent_deletion_reports_409_not_false_success(self, tmp_path):
        """Review finding #2 (PR #6): if the fact is deleted between the
        TruthGate pass and the guarded write, the API must never report
        success against a fact that no longer exists."""
        from core.version_store import VersionStore

        store = self._make_strong_supported_fact(tmp_path, "toctou_delete.db")

        def delete_it():
            store.delete_fact_l1("race_fact")

        versions_before = VersionStore(store.db_path).count_versions("race_fact")
        verdict, errors = _run_cas_race(store, "race_fact", delete_it)

        assert not errors, f"unexpected thread errors: {errors!r}"
        assert verdict is not None, "validator thread did not produce a verdict"
        assert verdict.passed is False, (
            "BYPASS: promotion reported success for a fact deleted "
            "concurrently between the TruthGate check and the write."
        )
        assert verdict.reason == "concurrent_modification", verdict.reason
        assert store.get_fact("race_fact") is None, (
            "Fact should remain deleted, not resurrected by the guarded write."
        )
        # Review finding #4 (PR #6) still holds — the rejected CAS attempt
        # itself creates no VersionStore snapshot of its own. But P0-B
        # (GDPR Art. 17) extended delete_fact_l1() to ALSO purge the fact's
        # existing fact_versions rows as part of complete erasure (leaving
        # version history behind for a "deleted" fact would itself be an
        # incomplete erasure) — so the racer's own delete_it() now drops the
        # count to 0, not "unchanged". versions_before > 0 here (from the
        # setup's Hypothesized/Supported transitions) is exactly what proves
        # delete_fact_l1() did the purging, not the rejected CAS attempt.
        assert versions_before > 0
        versions_after = VersionStore(store.db_path).count_versions("race_fact")
        assert versions_after == 0, (
            f"fact_versions not fully purged by delete_fact_l1() "
            f"({versions_before} -> {versions_after}) — the rejected CAS "
            "attempt must not be the one adding or leaving behind version "
            "rows for a fact that no longer exists."
        )

    def test_concurrent_state_change_to_hypothesized_reports_409_not_400(self, tmp_path):
        """Review finding #3 (PR #6): a concurrent, independently-legal
        transition (Supported -> Hypothesized) makes a direct jump to
        Validated newly illegal from the *new* state. The old design
        (fresh re-read + re-check inside transition_esm()) would raise
        ValueError/400 here — misreporting a race as a bad request. The new
        guarded write evaluates only against the original snapshot, so this
        must be concurrent_modification/409."""
        store = self._make_strong_supported_fact(tmp_path, "toctou_state_change.db")

        def demote():
            ok = store.transition_esm("race_fact", "Hypothesized", by="racer-thread")
            assert ok, "setup: racer's own transition must succeed"

        verdict, errors = _run_cas_race(store, "race_fact", demote)

        assert not errors, f"unexpected thread errors: {errors!r}"
        assert verdict is not None, "validator thread did not produce a verdict"
        assert verdict.passed is False
        assert verdict.reason == "concurrent_modification", (
            f"expected concurrent_modification, got {verdict.reason!r} — a "
            "race must never surface as an illegal-transition rejection"
        )
        final = store.get_fact("race_fact")
        assert final["epistemic_state"] == "Hypothesized", (
            "Racer's legitimate transition should stand, untouched by the "
            "rejected promotion attempt."
        )

    def test_concurrent_state_change_to_validated_reports_409_not_400(self, tmp_path):
        """Review finding #3 (PR #6), second case: a concurrent transition
        that itself reaches Validated first (e.g. another actor's own
        legitimate promotion). Documented behavior: this is reported as
        concurrent_modification/409 (the guarded write's snapshot no longer
        matches), not treated as a special idempotent success — but it must
        never be misreported as a 400 illegal-transition error."""
        store = self._make_strong_supported_fact(tmp_path, "toctou_state_change_v.db")

        def other_actor_validates_first():
            ok = store.transition_esm("race_fact", "Validated", by="other-actor")
            assert ok, "setup: racer's own transition must succeed"

        verdict, errors = _run_cas_race(store, "race_fact", other_actor_validates_first)

        assert not errors, f"unexpected thread errors: {errors!r}"
        assert verdict is not None, "validator thread did not produce a verdict"
        assert verdict.passed is False
        assert verdict.reason == "concurrent_modification", (
            f"expected concurrent_modification, got {verdict.reason!r} — a "
            "race must never surface as an illegal-transition rejection"
        )
        # The other actor's legitimate promotion must stand.
        final = store.get_fact("race_fact")
        assert final["epistemic_state"] == "Validated"


class TestStoreFactMetadataNoOpFix:
    """Regression for the 2nd independent Codex re-review, finding #1: a
    metadata-only re-post (same claim/source/confidence, new evidence_refs)
    used to take store_fact()'s no-op branch, which performs no SQL write —
    so the fresh evidence never reached the durable row validate_and_promote()
    reads via _get_fact_durable()."""

    def test_metadata_only_repost_persists_new_evidence_before_validation(self, tmp_path):
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore(str(tmp_path / "metadata_repost.db"))
        fact = {
            "fact_id":    "meta_fact",
            "claim":      "meta claim",
            "source":     "integration-test",
            "confidence": 0.8,
            "metadata":   {"evidence_refs": ["a"]},  # 1 ref: fails BALANCED (min_evidence=2)
        }
        store.store_fact(fact)
        store.transition_esm("meta_fact", "Hypothesized")
        store.transition_esm("meta_fact", "Supported")

        # Sanity: not enough evidence yet.
        verdict_before = store.validate_and_promote("meta_fact", by="test")
        assert verdict_before.passed is False
        assert verdict_before.reason == "insufficient_evidence"

        # Metadata-only re-post: identical claim/source/confidence, but a
        # second evidence_ref — must NOT be treated as a no-op.
        is_new = store.store_fact({**fact, "metadata": {"evidence_refs": ["a", "b"]}})
        assert is_new is False, "setup: expected an upsert of an existing fact"

        verdict_after = store.validate_and_promote("meta_fact", by="test")
        assert verdict_after.passed is True, (
            f"Freshly supplied evidence via a metadata-only re-post was not "
            f"persisted/visible to validation: reason={verdict_after.reason!r} "
            f"justification={verdict_after.justification!r}"
        )
        assert store.get_fact("meta_fact")["epistemic_state"] == "Validated"

    def test_true_noop_repost_still_skips_sql_write(self, tmp_path):
        """Guardrail: an actually-identical re-post (same claim/source/
        confidence/metadata) must still take the no-op fast path — the fix
        must not regress TASK-04/05's no-op optimization for genuine no-ops."""
        from core.memory import SQLiteGraphStore

        store = SQLiteGraphStore(str(tmp_path / "true_noop.db"))
        fact = {
            "fact_id":    "noop_fact",
            "claim":      "noop claim",
            "source":     "integration-test",
            "confidence": 0.8,
            "metadata":   {"evidence_refs": ["a", "b"]},
        }
        store.store_fact(fact)
        before = store.get_fact("noop_fact")

        is_new = store.store_fact(dict(fact))
        assert is_new is False

        after = store.get_fact("noop_fact")
        assert after["updated_at"] == before["updated_at"], (
            "A truly identical re-post bumped updated_at — the no-op fast "
            "path should not have fallen through to a real write."
        )


class TestPromoteToValidatedCasFallbackPath:
    """Regression for the 2nd independent Codex re-review, finding #3: the
    use_json_insert=False fallback branch of _promote_to_validated_cas()
    judged success from the preceding SELECT instead of the guarded UPDATE's
    own rowcount."""

    def test_fallback_cas_checks_final_update_rowcount_not_select(self, tmp_path):
        import sqlite3

        from core.memory import SQLiteGraphStore

        db_path = str(tmp_path / "fallback_cas.db")
        store = SQLiteGraphStore(db_path)
        store.use_json_insert = False  # force the fallback branch under test

        store.store_fact({
            "fact_id":    "fallback_fact",
            "claim":      "fallback claim",
            "source":     "integration-test",
            "confidence": 0.85,
            "metadata":   {"evidence_refs": ["a", "b"]},
        })
        store.transition_esm("fallback_fact", "Hypothesized")
        store.transition_esm("fallback_fact", "Supported")

        fact = store.get_fact("fallback_fact")
        expected_updated_at = fact["updated_at"]

        # sqlite3.Connection is an immutable C type — its methods can't be
        # patched on an instance or the class directly. Subclass it instead,
        # and force the store to open a *fresh* connection (through a
        # patched sqlite3.connect) so it picks up our subclass as its
        # factory. The store's existing connection (opened by the setup
        # calls above) is discarded first.
        triggered = {"done": False}

        class _RacyConnection(sqlite3.Connection):
            def execute(self, sql, params=()):
                result = super().execute(sql, params)
                if not triggered["done"] and isinstance(sql, str) and sql.strip().startswith(
                    "SELECT history FROM facts"
                ):
                    triggered["done"] = True
                    # Simulate a concurrent writer (a separate connection)
                    # racing in right after our SELECT reads the row, but
                    # before our own guarded UPDATE runs against the same
                    # WHERE clause.
                    side_conn = sqlite3.connect(db_path)
                    side_conn.execute(
                        "UPDATE facts SET confidence = ?, updated_at = ? WHERE fact_id = ?",
                        (0.1, "raced-away-timestamp", "fallback_fact"),
                    )
                    side_conn.commit()
                    side_conn.close()
                return result

        if store._sqlite_conn is not None:
            store._sqlite_conn.close()
            store._sqlite_conn = None

        original_connect = sqlite3.connect

        def patched_connect(*args, **kwargs):
            kwargs.setdefault("factory", _RacyConnection)
            return original_connect(*args, **kwargs)

        sqlite3.connect = patched_connect
        try:
            committed = store._promote_to_validated_cas(
                "fallback_fact",
                expected_state="Supported",
                expected_updated_at=expected_updated_at,
                durable_snapshot=fact,
                by="test",
            )
        finally:
            sqlite3.connect = original_connect

        assert triggered["done"], "setup: race injection point was never hit"
        assert committed is False, (
            "BYPASS: fallback CAS reported success even though the row "
            "changed between the SELECT and the guarded UPDATE."
        )
        # Read durably (bypass L0): the side connection wrote straight to
        # SQL and never touched this store's in-process cache, so a plain
        # get_fact() here would just show the stale pre-race L0 entry.
        final = store._get_fact_durable("fallback_fact")
        assert final["epistemic_state"] == "Supported"
        assert final["confidence"] == 0.1
