"""Phase 3A — strict embedding-space identity and dimension safety.

These tests prove contract convergence only. They do not invoke a real model,
network provider, live pipeline wiring, Canon mutation, or background indexing.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pytest

from core.embedding_projection import (
    EmbeddingProjectionIdentity,
    EmbeddingProjectionStore,
    ProjectionState,
    compute_content_hash,
    resolve_or_fallback,
)
from core.embedding_registry import (
    DimMismatchError,
    EmbeddingRegistry,
    EmbeddingSpaceDescriptor,
    EmbeddingSpaceMismatchError,
)
from core.embedding_store import EmbeddingStore
from core.hybrid_retriever import DenseRetriever


def _space(**overrides: Any) -> EmbeddingSpaceDescriptor:
    values: dict[str, Any] = {
        "provider_id": "local-sentence-transformers",
        "model": "all-MiniLM-L6-v2",
        "model_revision": "fixture-r1",
        "dimension": 4,
        "normalization": "l2",
        "pooling": "mean",
        "distance_metric": "cosine",
        "chunker_version": "chunker-v1",
        "preprocessing_version": "prep-v1",
    }
    values.update(overrides)
    return EmbeddingSpaceDescriptor(**values)


def _identity(
    space: EmbeddingSpaceDescriptor,
    *,
    record_id: str = "f1",
    content: str = "claim text",
) -> EmbeddingProjectionIdentity:
    return EmbeddingProjectionIdentity(
        record_id=record_id,
        content_hash=compute_content_hash(content),
        model_name=space.projection_model_name,
        model_version=space.projection_model_version,
        projection_version="1",
    )


def test_embedding_space_id_is_stable_sha256_of_canonical_payload() -> None:
    first = _space()
    second = _space()

    expected_digest = hashlib.sha256(first.canonical_json().encode("utf-8")).hexdigest()
    expected_id = f"embedding-space-v1:{expected_digest}"

    assert first.embedding_space_id == expected_id
    assert second.embedding_space_id == expected_id
    assert first.canonical_json() == second.canonical_json()


@pytest.mark.parametrize(
    ("field_name", "changed_value"),
    [
        ("provider_id", "other-provider"),
        ("model", "all-MiniLM-L12-v2"),
        ("model_revision", "fixture-r2"),
        ("dimension", 8),
        ("normalization", "none"),
        ("pooling", "cls"),
        ("distance_metric", "dot_product"),
        ("chunker_version", "chunker-v2"),
        ("preprocessing_version", "prep-v2"),
    ],
)
def test_every_identity_axis_changes_embedding_space_id(
    field_name: str,
    changed_value: str | int,
) -> None:
    baseline = _space()
    changed = _space(**{field_name: changed_value})

    assert baseline.dimension == changed.dimension or field_name == "dimension"
    assert baseline.embedding_space_id != changed.embedding_space_id
    assert not baseline.compatible_with(changed)

    with pytest.raises(EmbeddingSpaceMismatchError):
        EmbeddingRegistry.require_compatible_spaces(baseline, changed)


def test_same_dimension_does_not_make_different_spaces_compatible() -> None:
    local = _space(provider_id="provider-a", model="model-a")
    other = _space(provider_id="provider-b", model="model-b")

    assert local.dimension == other.dimension == 4
    assert local.embedding_space_id != other.embedding_space_id
    with pytest.raises(EmbeddingSpaceMismatchError):
        EmbeddingRegistry.require_compatible_spaces(local, other)


def test_typed_space_reuses_existing_projection_store_without_schema_change(tmp_path) -> None:
    backing = EmbeddingStore(str(tmp_path / "emb.db"))
    backing.ensure_table()
    projection = EmbeddingProjectionStore(backing)

    space = _space()
    identity = _identity(space)
    vector = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

    assert projection.store(identity, vector) is True
    assert projection.check_state(identity) is ProjectionState.FRESH
    assert projection.get_vector_if_fresh(identity) is not None

    axes = backing.list_stored_axes("f1")
    assert len(axes) == 1
    storage_axis = axes[0][0]
    assert space.embedding_space_id in storage_axis

    # Existing erasure semantics remain axis-agnostic: purge by record id
    # removes every derived embedding row regardless of its full space id.
    assert backing.purge_node("f1") == 1
    assert projection.check_state(identity) is ProjectionState.MISSING


def test_same_dimension_different_space_cannot_reuse_persistent_vector(tmp_path) -> None:
    backing = EmbeddingStore(str(tmp_path / "emb.db"))
    backing.ensure_table()
    projection = EmbeddingProjectionStore(backing)

    original_space = _space(provider_id="provider-a")
    incompatible_space = _space(provider_id="provider-b")
    original = _identity(original_space)
    incompatible = _identity(incompatible_space)

    projection.store(original, np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32))

    assert projection.check_state(incompatible) is ProjectionState.STALE_MODEL
    assert projection.get_vector_if_fresh(incompatible) is None
    mode, vectors = resolve_or_fallback(
        [incompatible], projection, embeddings_available=True
    )
    assert mode == "lexical_fallback"
    assert vectors is None


def test_legacy_projection_axis_is_unknown_not_auto_compatible(tmp_path) -> None:
    backing = EmbeddingStore(str(tmp_path / "emb.db"))
    backing.ensure_table()
    projection = EmbeddingProjectionStore(backing)

    legacy = EmbeddingProjectionIdentity(
        record_id="f1",
        content_hash=compute_content_hash("claim text"),
        model_name="all-MiniLM-L6-v2",
        model_version="legacy-r1",
        projection_version="1",
    )
    projection.store(legacy, np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32))

    typed_expected = _identity(_space())
    assert projection.check_state(typed_expected) is ProjectionState.STALE_MODEL
    assert projection.get_vector_if_fresh(typed_expected) is None

    mode, vectors = resolve_or_fallback(
        [typed_expected], projection, embeddings_available=True
    )
    assert mode == "lexical_fallback"
    assert vectors is None


def test_vector_dimension_mismatch_fails_closed() -> None:
    descriptor = _space(dimension=4)

    with pytest.raises(DimMismatchError):
        EmbeddingRegistry.validate_space_vector([0.1, 0.2], descriptor)

    with pytest.raises(DimMismatchError):
        EmbeddingRegistry.validate_pair_dimensions([0.1, 0.2], [0.1])

    with pytest.raises(DimMismatchError):
        EmbeddingRegistry.validate_pair_dimensions(
            [0.1, 0.2], [0.3, 0.4], expected_dimension=4
        )


def test_dense_retriever_dimension_mismatch_happens_before_any_scoring() -> None:
    class _NoMultiply(float):
        calls = 0

        def __mul__(self, other):  # type: ignore[override]
            type(self).calls += 1
            raise AssertionError("similarity scoring must not run after dimension mismatch")

    class _FakeModel:
        def encode(self, texts, normalize_embeddings=True):
            assert texts == ["query"]
            assert normalize_embeddings is True
            return [[1.0]]

    retriever = object.__new__(DenseRetriever)
    retriever._model = _FakeModel()
    retriever._embeddings = [[_NoMultiply(1.0), _NoMultiply(2.0)]]

    previous_available = DenseRetriever._AVAILABLE
    DenseRetriever._AVAILABLE = True
    try:
        assert retriever.retrieve("query") == []
        assert _NoMultiply.calls == 0
    finally:
        DenseRetriever._AVAILABLE = previous_available


def test_dense_retriever_equal_dimensions_still_score_normally() -> None:
    class _FakeModel:
        def encode(self, texts, normalize_embeddings=True):
            assert texts == ["query"]
            assert normalize_embeddings is True
            return [[0.5, 0.5]]

    retriever = object.__new__(DenseRetriever)
    retriever._model = _FakeModel()
    retriever._embeddings = [[1.0, 0.0], [0.0, 1.0]]

    previous_available = DenseRetriever._AVAILABLE
    DenseRetriever._AVAILABLE = True
    try:
        assert retriever.retrieve("query", top_k=2) == [(0, 0.5), (1, 0.5)]
    finally:
        DenseRetriever._AVAILABLE = previous_available
