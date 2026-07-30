"""PR-ARM-02 (issue #92): rebuildable embedding projection contract.

Covers the 14 required cases from the issue's acceptance criteria, using a
fake, dependency-free encode_fn (deterministic, no network, no real model)
and an isolated on-disk EmbeddingStore per test (tmp_path).

The module under test (core/embedding_projection.py) is NOT wired into the
live retrieval path in this PR — it defines the identity/staleness/reindex/
fallback contract for a future persistent-projection ingest pipeline.
core.hybrid_retriever.DenseRetriever (PR #91/#95/#99) already recomputes
embeddings correctly on demand and is unaffected by this module.
"""
from __future__ import annotations

import numpy as np
import pytest

import core.embedding_projection as ep
import core.memory as mem
from core.embedding_store import EmbeddingStore
from core.memory import SQLiteGraphStore, get_fact_ids, promote_to_validated, store_fact


def _vec(text: str, dims: int = 4) -> np.ndarray:
    """Deterministic, dependency-free stand-in for a real embedding."""
    return np.array(
        [((hash((text, i)) % 997) / 997.0) for i in range(dims)], dtype=np.float32
    )


def _fake_encode(texts: list[str]) -> list[np.ndarray]:
    return [_vec(t) for t in texts]


@pytest.fixture
def backing(tmp_path) -> EmbeddingStore:
    store = EmbeddingStore(str(tmp_path / "emb.db"))
    store.ensure_table()
    return store


@pytest.fixture
def store(backing) -> ep.EmbeddingProjectionStore:
    return ep.EmbeddingProjectionStore(backing)


def _identity(record_id="f1", content="claim text", model="model-a", version="v1",
              projection_version="1") -> ep.EmbeddingProjectionIdentity:
    return ep.EmbeddingProjectionIdentity(
        record_id=record_id,
        content_hash=ep.compute_content_hash(content),
        model_name=model,
        model_version=version,
        projection_version=projection_version,
    )


# ─── 1: same record + same content/model/version -> fresh ─────────────────

def test_identical_identity_is_fresh(store):
    ident = _identity()
    assert store.check_state(ident) == ep.ProjectionState.MISSING
    store.store(ident, _vec("claim text"))
    assert store.check_state(ident) == ep.ProjectionState.FRESH
    # A structurally identical, independently-constructed identity must
    # also see FRESH (comparison is field-by-field dataclass equality, not
    # object identity).
    same_again = _identity()
    assert store.check_state(same_again) == ep.ProjectionState.FRESH


# ─── 2: same ID + changed content -> stale_content ─────────────────────────

def test_changed_content_same_id_is_stale_content(store):
    original = _identity(content="claim v1")
    store.store(original, _vec("claim v1"))

    edited = _identity(content="claim v2")
    assert store.check_state(edited) == ep.ProjectionState.STALE_CONTENT


# ─── 3: same ID/content + different model -> stale_model ──────────────────

def test_different_model_same_id_content_is_stale_model(store):
    original = _identity(model="model-a")
    store.store(original, _vec("claim text"))

    different_model = _identity(model="model-b")
    assert store.check_state(different_model) == ep.ProjectionState.STALE_MODEL


def test_different_model_version_same_model_name_is_stale_model(store):
    original = _identity(version="v1")
    store.store(original, _vec("claim text"))

    different_version = _identity(version="v2")
    assert store.check_state(different_version) == ep.ProjectionState.STALE_MODEL


# ─── 4: different projection schema version -> stale_projection_version ───

def test_different_projection_version_is_stale_projection_version(store):
    original = _identity(projection_version="1")
    store.store(original, _vec("claim text"))

    schema_bumped = _identity(projection_version="2")
    assert store.check_state(schema_bumped) == ep.ProjectionState.STALE_PROJECTION_VERSION


# ─── 5: incompatible models never silently share a vector/index ───────────

def test_incompatible_models_do_not_share_vectors(store):
    model_a = _identity(model="model-a")
    store.store(model_a, _vec("claim text"))

    model_b = _identity(model="model-b")
    # model-b was never stored -> must not receive model-a's vector.
    assert store.get_vector_if_fresh(model_b) is None
    assert store.check_state(model_b) == ep.ProjectionState.STALE_MODEL

    # model-a's own vector is completely unaffected by model-b's absence.
    assert store.get_vector_if_fresh(model_a) is not None


# ─── 6: missing projection -> lexical fallback ─────────────────────────────

def test_missing_projection_falls_back_to_lexical(store):
    ident = _identity()
    mode, vectors = ep.resolve_or_fallback([ident], store, embeddings_available=True)
    assert mode == "lexical_fallback"
    assert vectors is None
    # And detecting this must not have silently reindexed anything.
    assert store.check_state(ident) == ep.ProjectionState.MISSING


# ─── 7: stale projection -> lexical fallback until reindexed ──────────────

def test_stale_projection_falls_back_until_explicit_reindex(store):
    stale_ident = _identity(content="old claim")
    store.store(stale_ident, _vec("old claim"))

    current_ident = _identity(content="new claim")
    mode, vectors = ep.resolve_or_fallback([current_ident], store, embeddings_available=True)
    assert mode == "lexical_fallback"
    assert vectors is None
    # Merely resolving/falling back must not have reindexed it.
    assert store.check_state(current_ident) == ep.ProjectionState.STALE_CONTENT

    # Only an explicit rebuild() call fixes it.
    report = store.rebuild([(current_ident, "new claim")], _fake_encode)
    assert report.rebuilt == (current_ident.record_id,)
    assert store.check_state(current_ident) == ep.ProjectionState.FRESH

    mode2, vectors2 = ep.resolve_or_fallback([current_ident], store, embeddings_available=True)
    assert mode2 == "dense"
    assert vectors2 is not None


# ─── 8: failed model load -> lexical fallback ──────────────────────────────

def test_embeddings_unavailable_falls_back_to_lexical_even_if_fresh(store):
    ident = _identity()
    store.store(ident, _vec("claim text"))
    assert store.check_state(ident) == ep.ProjectionState.FRESH  # projection itself is fine

    mode, vectors = ep.resolve_or_fallback([ident], store, embeddings_available=False)
    assert mode == "lexical_fallback"
    assert vectors is None


def test_backend_construction_failure_degrades_to_missing_not_a_crash(monkeypatch):
    """Simulates numpy/core.embedding_store genuinely being unavailable
    (an optional dependency, per core.erasure_coordinator's own comment)."""
    import core.embedding_store as es_mod

    def _boom():
        raise ImportError("numpy not installed")

    monkeypatch.setattr(es_mod, "get_embedding_store", _boom)
    projection_store = ep.EmbeddingProjectionStore()  # must not raise
    assert projection_store.available is False

    ident = _identity()
    assert projection_store.check_state(ident) == ep.ProjectionState.MISSING
    assert projection_store.store(ident, _vec("claim text")) is False
    mode, vectors = ep.resolve_or_fallback([ident], projection_store, embeddings_available=True)
    assert mode == "lexical_fallback"
    assert vectors is None


# ─── 9: erasure/revocation invalidates the derived projection ─────────────

def test_erasure_purge_node_invalidates_projection(store, backing):
    """core.erasure_coordinator._run_embeddings calls
    EmbeddingStore.purge_node(fact_id) on exactly this shared backing —
    proving that call invalidates a row written through
    EmbeddingProjectionStore is sufficient to prove erasure-compatibility,
    without needing to stand up the full coordinator/job machinery."""
    ident = _identity(record_id="erasable-1")
    store.store(ident, _vec("claim text"))
    assert store.check_state(ident) == ep.ProjectionState.FRESH

    deleted = backing.purge_node("erasable-1")
    assert deleted >= 1
    assert store.check_state(ident) == ep.ProjectionState.MISSING


def test_invalidate_record_helper_matches_erasure_purge(store):
    ident = _identity(record_id="erasable-2")
    store.store(ident, _vec("claim text"))
    n = store.invalidate_record("erasable-2")
    assert n >= 1
    assert store.check_state(ident) == ep.ProjectionState.MISSING


# ─── 10: query path (this module's read surface) remains read-only ───────

def test_read_only_operations_never_mutate_projection_or_canon(store, backing):
    ident = _identity(record_id="ro-1")
    store.store(ident, _vec("claim text"))
    before_stats = backing.stats()

    other = _identity(record_id="ro-2")
    store.check_state(ident)
    store.check_state(other)
    store.get_vector_if_fresh(ident)
    store.get_vector_if_fresh(other)
    store.list_stale_or_missing([ident, other])
    ep.resolve_or_fallback([ident, other], store, embeddings_available=True)
    ep.resolve_or_fallback([ident, other], store, embeddings_available=False)

    after_stats = backing.stats()
    assert after_stats == before_stats, "read-only calls must not change stored row counts"


def test_read_only_operations_write_nothing_to_canon(store):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        real_store = mem.make_store(f"{d}/canon.db")
        old_global = mem._GLOBAL_STORE
        mem._GLOBAL_STORE = real_store
        try:
            store_fact({"fact_id": "canon-1", "claim": "untouched by projection reads",
                        "source": "s", "confidence": 0.9})
            before = sorted(get_fact_ids(limit=1000))

            ident = _identity(record_id="canon-1", content="untouched by projection reads")
            store.check_state(ident)
            store.get_vector_if_fresh(ident)
            store.list_stale_or_missing([ident])
            ep.resolve_or_fallback([ident], store, embeddings_available=True)

            after = sorted(get_fact_ids(limit=1000))
            assert after == before, "projection reads must never write to Canon"
        finally:
            mem._GLOBAL_STORE = old_global
            real_store.close()


# ─── 11: TruthGate bypass count stays zero regardless of projection state ─

def test_pipeline_still_reaches_truth_gate_regardless_of_projection_state(monkeypatch, tmp_path):
    """This module is not wired into pipeline.run() in this PR — proving
    that explicitly is the point: whatever this module's projection state
    says has zero bearing on whether TruthGate runs. truth_gate_bypass_count
    (per issue #92 / PR #96 acceptance language) is 0 either way."""
    import core.pipeline as pipeline

    real_store = SQLiteGraphStore(str(tmp_path / "t.db"))
    monkeypatch.setattr(mem, "_GLOBAL_STORE", real_store)
    store_fact({"fact_id": "tg-1", "claim": "вода кипит при ста градусах",
                "source": "physics", "confidence": 0.95})
    promote_to_validated("tg-1")

    # Deterministic NGram stand-in — pipeline._NGRAM_INDEX is a process-wide
    # singleton shared across the whole test session (see tests/conftest.py);
    # relying on its real, cross-test-polluted content is exactly what made
    # this test flaky when run inside the full suite. Same technique as
    # tests/test_retrieval_routing.py / tests/test_retrieval_d3.py.
    class _StubNGram:
        available = True

        def query(self, _text, limit=50):
            return ["tg-1"]

    monkeypatch.setattr(pipeline, "_NGRAM_INDEX", _StubNGram())
    # Same reasoning for the HybridRetriever singleton (also process-wide).
    monkeypatch.setattr(pipeline, "_HYBRID_RETRIEVER", None)
    monkeypatch.setattr(pipeline, "_HYBRID_DIRTY", True)
    monkeypatch.setattr(pipeline, "_HYBRID_FACTS_COUNT", 0)
    monkeypatch.setattr(pipeline, "_HYBRID_FACT_IDS", frozenset())

    embedding_backing = EmbeddingStore(str(tmp_path / "emb.db"))
    embedding_backing.ensure_table()
    projection_store = ep.EmbeddingProjectionStore(embedding_backing)
    stale_ident = _identity(record_id="tg-1", content="a completely different old claim")
    projection_store.store(stale_ident, _vec("a completely different old claim"))
    # Confirm it is indeed stale for the fact's real, current claim.
    current_ident = _identity(record_id="tg-1", content="вода кипит при ста градусах")
    assert projection_store.check_state(current_ident) == ep.ProjectionState.STALE_CONTENT

    calls = {"truth_gate": 0}
    original_truth_gate = pipeline.truth_gate

    def _spy(*a, **kw):
        calls["truth_gate"] += 1
        return original_truth_gate(*a, **kw)

    monkeypatch.setattr(pipeline, "truth_gate", _spy)

    result = pipeline.run("вода")
    assert result.get("error") is None
    truth_gate_bypass_count = 0 if calls["truth_gate"] >= 1 else 1
    assert truth_gate_bypass_count == 0
    real_store.close()


# ─── 12: rebuild is repeatable and deterministic by identity ──────────────

def test_rebuild_is_idempotent_and_deterministic(store):
    ident = _identity(record_id="rb-1", content="rebuild me")
    report1 = store.rebuild([(ident, "rebuild me")], _fake_encode)
    assert report1.rebuilt == ("rb-1",)
    vector_1 = store.get_vector_if_fresh(ident)

    report2 = store.rebuild([(ident, "rebuild me")], _fake_encode)
    assert report2.skipped_fresh == ("rb-1",)
    assert report2.rebuilt == ()
    vector_2 = store.get_vector_if_fresh(ident)

    assert np.array_equal(vector_1, vector_2)


def test_rebuild_all_is_bounded_to_given_records(store):
    records = [("bulk-1", "claim one"), ("bulk-2", "claim two")]
    report = store.rebuild_all(
        records, model_name="model-a", model_version="v1", projection_version="1",
        encode_fn=_fake_encode,
    )
    assert set(report.rebuilt) == {"bulk-1", "bulk-2"}
    assert report.failed == ()

    # A second identical call must be fully idempotent (all skipped_fresh).
    report2 = store.rebuild_all(
        records, model_name="model-a", model_version="v1", projection_version="1",
        encode_fn=_fake_encode,
    )
    assert set(report2.skipped_fresh) == {"bulk-1", "bulk-2"}
    assert report2.rebuilt == ()


# ─── 13: corrupted metadata is handled as invalid, never a crash ──────────

def test_corrupted_storage_key_is_invalid_not_a_crash(store, backing):
    # Bypass EmbeddingProjectionStore.store() to write a malformed
    # storage key directly, simulating on-disk corruption / a foreign
    # writer that didn't follow the storage_key() contract.
    backing.store("corrupt-1", _vec("whatever"), model_name="not-a-valid-key-shape",
                  content_hash="deadbeef")

    ident = _identity(record_id="corrupt-1")
    assert store.check_state(ident) == ep.ProjectionState.INVALID  # never raises


def test_missing_content_hash_is_invalid_not_a_crash(store, backing):
    # A row with the correct key shape but no content_hash (e.g. written by
    # an older EmbeddingStore.store_batch() call, which never sets one).
    key = ep.EmbeddingProjectionIdentity("x", "", "model-a", "v1", "1").storage_key()
    backing.store("corrupt-2", _vec("whatever"), model_name=key)  # content_hash defaults to None

    ident = _identity(record_id="corrupt-2")
    assert store.check_state(ident) == ep.ProjectionState.INVALID


# ─── 14: feature flag OFF preserves prior behavior (nothing to change yet) ─

def test_feature_flag_defaults_off():
    from core.runtime_flags import is_embedding_projection_contract_enabled
    assert is_embedding_projection_contract_enabled() is False


def test_contract_behavior_is_unaffected_by_the_flag(store, monkeypatch):
    """This PR does not wire the contract into any live pipeline path, so
    there is nothing for the flag to gate yet — behavior must be identical
    whether the flag is on or off, proving the flag is a safe no-op
    placeholder for the future integration, not a behavior change."""
    ident = _identity(record_id="flag-1")
    store.store(ident, _vec("claim text"))

    monkeypatch.setattr("core.runtime_flags.is_embedding_projection_contract_enabled",
                         lambda: False)
    state_off = store.check_state(ident)
    mode_off, _ = ep.resolve_or_fallback([ident], store, embeddings_available=True)

    monkeypatch.setattr("core.runtime_flags.is_embedding_projection_contract_enabled",
                         lambda: True)
    state_on = store.check_state(ident)
    mode_on, _ = ep.resolve_or_fallback([ident], store, embeddings_available=True)

    assert state_off == state_on == ep.ProjectionState.FRESH
    assert mode_off == mode_on == "dense"


# ─── PR #96 replay protocol linkage ────────────────────────────────────────

def test_embedding_projection_replay_fixture_is_review_required_with_no_gate_violations():
    """Links this PR to the fixed-corpus replay protocol from PR #96:
    fresh-projection baseline vs stale-content-projection candidate (falls
    back to lexical) must be classified REVIEW_REQUIRED (a route change is
    never silently auto-approved) with zero critical-gate violations on
    either side."""
    from core.evaluation_replay import evaluate_fixture

    report = evaluate_fixture("tests/fixtures/evaluation_replay/embedding_projection.json")
    diff = report["diff"]

    assert diff.stability.value == "REVIEW_REQUIRED"
    assert diff.critical_regressions == ()
    for case_diff in diff.case_diffs:
        assert case_diff.critical_regressions == ()
    assert diff.case_diffs[0].route_before == "hybrid"
    assert diff.case_diffs[0].route_after == "lexical"
