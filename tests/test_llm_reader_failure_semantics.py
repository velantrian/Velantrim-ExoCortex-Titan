from __future__ import annotations

import asyncio
import json

import pytest

from core.readers.llm_adapter import LlmReaderAdapter, LlmReaderLimits
from core.semantic_reader import RawSource, ReaderStatus

_TEXT = "Кошка спит на окне."


def _adapter(*, attempts: int = 3) -> LlmReaderAdapter:
    return LlmReaderAdapter(
        provider="openai",
        model="gpt-test",
        limits=LlmReaderLimits(
            max_attempts_per_chunk=attempts,
            max_chunks=1,
        ),
    )


def _run(adapter: LlmReaderAdapter):
    return asyncio.run(
        adapter.extract_with_receipt(
            RawSource(document_id="failure-semantics", text=_TEXT)
        )
    )


def _payload() -> str:
    return json.dumps(
        {
            "claims": [
                {
                    "text": _TEXT,
                    "modality": "observation",
                }
            ]
        },
        ensure_ascii=False,
    )


def test_transient_value_error_is_retried_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import core.llm_router as router

    calls = {"count": 0}

    async def transient_then_success(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("empty provider response")
        return _payload()

    monkeypatch.setattr(router, "chat_complete", transient_then_success)
    outcome = _run(_adapter())

    assert calls["count"] == 2
    assert outcome.result.accepted
    assert "PROVIDER_RESPONSE_ERROR" in outcome.receipt.failure_codes


def test_http_503_is_not_reported_as_rate_limit_and_remains_retryable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import core.llm_router as router

    calls = {"count": 0}

    async def unavailable(*args, **kwargs):
        calls["count"] += 1
        raise router.LlmProviderRequestError(
            provider="openai",
            status_code=503,
            detail="unavailable",
            message="openai: HTTP 503",
        )

    monkeypatch.setattr(router, "chat_complete", unavailable)
    outcome = _run(_adapter(attempts=2))

    assert calls["count"] == 2
    assert outcome.result.status is ReaderStatus.PROVIDER_ERROR
    assert outcome.result.failure is not None
    assert outcome.result.failure.code == "PROVIDER_SERVER_ERROR"
    assert outcome.result.failure.retryable is True
    assert "PROVIDER_RATE_LIMITED" not in outcome.receipt.failure_codes


def test_http_408_has_its_own_retryable_failure_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import core.llm_router as router

    async def request_timeout(*args, **kwargs):
        raise router.LlmProviderRequestError(
            provider="openai",
            status_code=408,
            detail="request timeout",
            message="openai: HTTP 408",
        )

    monkeypatch.setattr(router, "chat_complete", request_timeout)
    outcome = _run(_adapter(attempts=1))

    assert outcome.result.status is ReaderStatus.PROVIDER_ERROR
    assert outcome.result.failure is not None
    assert outcome.result.failure.code == "PROVIDER_REQUEST_TIMEOUT"
    assert outcome.result.failure.retryable is True


def test_exhausted_rate_limit_propagates_retryable_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import core.llm_router as router

    async def rate_limited(*args, **kwargs):
        raise router.LlmProviderRequestError(
            provider="openai",
            status_code=429,
            detail="slow down",
            message="openai: HTTP 429",
        )

    monkeypatch.setattr(router, "chat_complete", rate_limited)
    outcome = _run(_adapter(attempts=2))

    assert outcome.result.status is ReaderStatus.PROVIDER_ERROR
    assert outcome.result.failure is not None
    assert outcome.result.failure.code == "PROVIDER_RATE_LIMITED"
    assert outcome.result.failure.retryable is True


def test_permanent_configuration_value_error_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import core.llm_router as router

    calls = {"count": 0}

    async def invalid_key(*args, **kwargs):
        calls["count"] += 1
        raise ValueError("invalid API key")

    monkeypatch.setattr(router, "chat_complete", invalid_key)
    outcome = _run(_adapter(attempts=3))

    assert calls["count"] == 1
    assert outcome.result.status is ReaderStatus.PROVIDER_ERROR
    assert outcome.result.failure is not None
    assert outcome.result.failure.code == "PROVIDER_REQUEST_REJECTED"
    assert outcome.result.failure.retryable is False
