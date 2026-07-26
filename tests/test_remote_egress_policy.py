"""P0 remote egress and epistemic-boundary regressions."""
from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(autouse=True)
def _reset_remote_policy(monkeypatch):
    monkeypatch.delenv("VELANTRIM_NETWORK_MODE", raising=False)
    monkeypatch.delenv("VELANTRIM_REMOTE_DATA_MODE", raising=False)
    from core.policy_kernel import reset_policy_kernel

    reset_policy_kernel()
    yield
    reset_policy_kernel()


def test_remote_egress_is_denied_by_default():
    from core.remote_egress import (
        RemoteEgressDenied,
        ensure_remote_egress_allowed,
    )

    with pytest.raises(RemoteEgressDenied) as exc:
        ensure_remote_egress_allowed(
            "remote_llm",
            provider="openai",
            data_mode="raw",
        )

    assert exc.value.reason_code == "network_denied"


def test_explicit_network_and_data_policy_allows_raw_remote_call(monkeypatch):
    from core.policy_kernel import reset_policy_kernel
    from core.remote_egress import ensure_remote_egress_allowed

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    reset_policy_kernel()

    receipt = ensure_remote_egress_allowed(
        "remote_llm",
        provider="openai",
        data_mode="raw",
    )

    assert receipt.capability == "remote_llm"
    assert receipt.provider == "openai"
    assert receipt.data_mode == "raw"
    assert receipt.snapshot_id


def test_network_allow_does_not_override_remote_data_never(monkeypatch):
    from core.policy_kernel import reset_policy_kernel
    from core.remote_egress import (
        RemoteEgressDenied,
        ensure_remote_egress_allowed,
    )

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "never")
    reset_policy_kernel()

    with pytest.raises(RemoteEgressDenied) as exc:
        ensure_remote_egress_allowed(
            "remote_llm",
            provider="gemini",
            data_mode="raw",
        )

    assert exc.value.reason_code == "remote_data_forbidden"


def test_redacted_policy_rejects_raw_but_accepts_redacted(monkeypatch):
    from core.policy_kernel import reset_policy_kernel
    from core.remote_egress import (
        RemoteEgressDenied,
        ensure_remote_egress_allowed,
    )

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "redacted")
    reset_policy_kernel()

    with pytest.raises(RemoteEgressDenied) as exc:
        ensure_remote_egress_allowed(
            "remote_llm",
            provider="deepseek",
            data_mode="raw",
        )
    assert exc.value.reason_code == "remote_data_requires_redaction"

    receipt = ensure_remote_egress_allowed(
        "remote_embeddings",
        provider="local-redaction-proxy",
        data_mode="redacted",
    )
    assert receipt.data_mode == "redacted"


def test_ask_mode_fails_closed_without_consent_broker(monkeypatch):
    from core.policy_kernel import reset_policy_kernel
    from core.remote_egress import (
        RemoteEgressDenied,
        ensure_remote_egress_allowed,
    )

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "ask")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    reset_policy_kernel()

    with pytest.raises(RemoteEgressDenied) as exc:
        ensure_remote_egress_allowed(
            "remote_llm",
            provider="anthropic",
            data_mode="raw",
        )

    assert exc.value.reason_code == "network_consent_required"


def test_no_payload_provider_test_can_run_without_remote_data_permission(monkeypatch):
    from core.policy_kernel import reset_policy_kernel
    from core.remote_egress import ensure_remote_egress_allowed

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "never")
    reset_policy_kernel()

    receipt = ensure_remote_egress_allowed(
        "remote_llm_test",
        provider="openai",
        data_mode="none",
    )

    assert receipt.data_mode == "none"


def test_invalid_policy_value_fails_closed(monkeypatch):
    from core.policy_kernel import reset_policy_kernel
    from core.remote_egress import (
        RemoteEgressDenied,
        ensure_remote_egress_allowed,
    )

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "sometimes")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    reset_policy_kernel()

    with pytest.raises(RemoteEgressDenied) as exc:
        ensure_remote_egress_allowed(
            "remote_llm",
            provider="openai",
            data_mode="raw",
        )

    assert exc.value.reason_code == "policy_dependency_unavailable"


def test_remote_prompt_removes_false_verified_label_and_is_idempotent():
    from core.remote_egress import sanitize_remote_system_prompt

    legacy = (
        "Ты — Velantrim ExoCortex, AI-агент с верифицированной памятью.\n"
        "Отвечай ТОЛЬКО на основе следующих фактов из памяти.\n\n"
        "Верифицированные факты:\n"
        "- [chat | conf=0.50] Это Observed запись"
    )

    safe = sanitize_remote_system_prompt(legacy)

    assert safe.startswith("[VELANTRIM REMOTE EPISTEMIC BOUNDARY]")
    assert "AI-агент с верифицированной памятью" not in safe
    assert "Верифицированные факты:" not in safe
    assert "часть может быть неподтверждённой" in safe
    assert sanitize_remote_system_prompt(safe) == safe


def test_llm_router_blocks_before_http_client_is_opened(monkeypatch):
    from core.llm_router import LlmCallConfig, chat_complete
    from core.remote_egress import RemoteEgressDenied

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("HTTP client must not be constructed")

    monkeypatch.setattr("core.llm_router.httpx.AsyncClient", ForbiddenClient)

    with pytest.raises(RemoteEgressDenied) as exc:
        asyncio.run(
            chat_complete(
                LlmCallConfig(provider="openai", api_key="test-key"),
                "private prompt",
                "private memory",
            )
        )

    assert exc.value.reason_code == "network_denied"


def test_tts_router_blocks_before_http_client_is_opened(monkeypatch):
    from core.remote_egress import RemoteEgressDenied
    from core.tts_router import gemini_tts_bytes

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("HTTP client must not be constructed")

    monkeypatch.setattr("core.tts_router.httpx.AsyncClient", ForbiddenClient)

    with pytest.raises(RemoteEgressDenied) as exc:
        asyncio.run(gemini_tts_bytes("test-key", "private text"))

    assert exc.value.reason_code == "network_denied"


def test_streaming_path_reports_policy_denial_without_network(monkeypatch):
    from core.llm_router import LlmCallConfig
    from core.llm_stream import stream_chat_events

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("HTTP client must not be constructed")

    monkeypatch.setattr("core.llm_stream.httpx.AsyncClient", ForbiddenClient)

    async def collect():
        return [
            event
            async for event in stream_chat_events(
                LlmCallConfig(provider="openai", api_key="test-key"),
                "private memory",
                "question",
            )
        ]

    events = asyncio.run(collect())

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "network_denied" in events[0]["message"]


def test_gemini_model_discovery_obeys_network_policy(monkeypatch):
    from core.gemini_models import fetch_gemini_models_from_api

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("HTTP client must not be constructed")

    monkeypatch.setattr("core.gemini_models.httpx.AsyncClient", ForbiddenClient)

    models, warnings = asyncio.run(
        fetch_gemini_models_from_api("test-key")
    )

    assert models  # static catalog remains available
    assert any("network_denied" in warning for warning in warnings)
