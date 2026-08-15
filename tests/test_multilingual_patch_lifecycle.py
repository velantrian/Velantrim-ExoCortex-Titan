from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from core import multilingual_router, pipeline


@pytest.fixture(autouse=True)
def _restore_pipeline_retrieve():
    multilingual_router.unpatch_pipeline_retrieval()
    original = pipeline.retrieve
    try:
        yield
    finally:
        multilingual_router.unpatch_pipeline_retrieval()
        pipeline.retrieve = original


def test_patch_is_idempotent_and_restores_exact_original(monkeypatch):
    original = pipeline.retrieve
    monkeypatch.setattr(
        multilingual_router,
        "retrieve_multilingual",
        lambda query, *, top_k=5, use_ngram=True: [
            {"claim": query, "top_k": top_k, "use_ngram": use_ngram}
        ],
    )

    assert multilingual_router.patch_pipeline_retrieval() is True
    installed = pipeline.retrieve
    assert installed is not original
    assert pipeline.retrieve("привет", 4) == [
        {"claim": "привет", "top_k": 4, "use_ngram": True}
    ]

    assert multilingual_router.patch_pipeline_retrieval() is False
    assert pipeline.retrieve is installed

    assert multilingual_router.unpatch_pipeline_retrieval() is True
    assert pipeline.retrieve is original
    assert multilingual_router.unpatch_pipeline_retrieval() is False


def test_database_delegation_uses_exact_captured_original():
    calls: list[tuple[Any, ...]] = []

    def original(query, k=3, database=None, domain=None):
        calls.append((query, k, database, domain))
        return ["delegated"]

    pipeline.retrieve = original
    assert multilingual_router.patch_pipeline_retrieval() is True

    database = [{"fact_id": "f-1"}]
    assert pipeline.retrieve("hello", 7, database, "test-domain") == ["delegated"]
    assert calls == [("hello", 7, database, "test-domain")]

    assert multilingual_router.unpatch_pipeline_retrieval() is True
    assert pipeline.retrieve is original


def test_unpatch_does_not_clobber_external_replacement():
    original = pipeline.retrieve
    assert multilingual_router.patch_pipeline_retrieval() is True

    def external_retrieve(query, k=3, database=None, domain=None):
        return [query, k, database, domain]

    pipeline.retrieve = external_retrieve

    assert multilingual_router.unpatch_pipeline_retrieval() is False
    assert pipeline.retrieve is external_retrieve

    pipeline.retrieve = original


def test_lost_ownership_can_be_reinstalled_without_wrapper_stacking():
    original = pipeline.retrieve
    assert multilingual_router.patch_pipeline_retrieval() is True
    first_wrapper = pipeline.retrieve

    def external_retrieve(query, k=3, database=None, domain=None):
        return ["external", query]

    pipeline.retrieve = external_retrieve

    assert multilingual_router.patch_pipeline_retrieval() is True
    second_wrapper: Callable[..., Any] = pipeline.retrieve
    assert second_wrapper is not first_wrapper
    assert second_wrapper is not external_retrieve

    assert multilingual_router.unpatch_pipeline_retrieval() is True
    assert pipeline.retrieve is external_retrieve

    pipeline.retrieve = original
