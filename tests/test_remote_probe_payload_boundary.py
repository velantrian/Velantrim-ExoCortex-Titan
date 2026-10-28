"""Metadata-only exceptions cannot relabel arbitrary chat payloads."""
import asyncio
import importlib
import json

import httpx
import pytest

from core import llm_router
from core.remote_egress import ensure_remote_egress_allowed


@pytest.mark.parametrize("mode", ["none", " NONE ", "NoNe", None])
@pytest.mark.parametrize("provider", ["openai", "deepseek", "gemini", "openrouter", "anthropic"])
def test_general_chat_rejects_metadata_only_mode(monkeypatch, provider, mode):
    def forbidden(*args, **kwargs):
        raise AssertionError("must reject before HTTP client construction")
    monkeypatch.setattr(llm_router.httpx, "AsyncClient", forbidden)
    with pytest.raises(ValueError, match="test_connection"):
        asyncio.run(llm_router.chat_complete(
            llm_router.LlmCallConfig(provider=provider, api_key="synthetic-key"),
            "private prompt", "private system", data_mode=mode,
        ))


@pytest.mark.parametrize("mode", ["none", " NONE ", "NoNe", None])
def test_egress_whitelist_checks_normalized_mode(mode):
    with pytest.raises(ValueError, match="may not declare"):
        ensure_remote_egress_allowed("remote_llm", provider="openai", data_mode=mode)


@pytest.mark.parametrize("adapter", ["openai", "gemini", "anthropic"])
def test_provider_adapters_reject_arbitrary_metadata_payload(monkeypatch, adapter):
    def forbidden(*args, **kwargs):
        raise AssertionError("must reject before HTTP client construction")
    monkeypatch.setattr(llm_router.httpx, "AsyncClient", forbidden)
    cfg = llm_router.LlmCallConfig(provider=adapter, api_key="synthetic-key")
    if adapter == "openai":
        call = llm_router._openai_compatible_chat(
            cfg, "private prompt", "private memory", "https://example.invalid", data_mode="none",
        )
    elif adapter == "gemini":
        call = llm_router._gemini_chat(cfg, "private prompt", "private memory", data_mode="none")
    else:
        call = llm_router._anthropic_chat(cfg, "private prompt", "private memory", data_mode="none")
    with pytest.raises(ValueError, match="fixed connectivity probe"):
        asyncio.run(call)


@pytest.mark.parametrize("provider", ["openai", "deepseek", "gemini", "openrouter", "anthropic"])
def test_fixed_probe_still_works_without_user_data_permission(monkeypatch, provider):
    # Earlier API tests purge core.* after collection. Patch the live module
    # used by remote_egress, rather than an obsolete collection-time instance.
    policy_kernel = importlib.import_module("core.policy_kernel")
    kernel = policy_kernel.PolicyKernel()
    snapshot = kernel._make_snapshot(
        policy_kernel.EffectivePolicy(
            network=policy_kernel.NetworkMode.ALLOW, remote_data=policy_kernel.RemoteDataMode.NEVER,
        ), supervisor_mode="normal", writes_allowed=True, source="test", reason_code="ok",
    )
    monkeypatch.setattr(kernel, "capture_snapshot", lambda: snapshot)
    monkeypatch.setattr(policy_kernel, "get_policy_kernel", lambda: kernel)
    requests = []
    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "OK"}}],
            "candidates": [{"content": {"parts": [{"text": "OK"}]}}],
            "content": [{"type": "text", "text": "OK"}],
        })
    original = httpx.AsyncClient
    monkeypatch.setattr(llm_router.httpx, "AsyncClient", lambda **kw: original(
        transport=httpx.MockTransport(respond), trust_env=False,
    ))
    result = asyncio.run(llm_router.test_connection(
        llm_router.LlmCallConfig(provider=provider, api_key="synthetic-key"),
    ))
    assert result["ok"] is True
    assert len(requests) == 1
    payload = json.dumps(requests[0], ensure_ascii=False)
    assert llm_router._CONNECTIVITY_PROBE_PROMPT in payload
    assert llm_router._CONNECTIVITY_PROBE_SYSTEM in payload


def test_probe_rejects_missing_key():
    with pytest.raises(ValueError, match="API key"):
        asyncio.run(llm_router.test_connection(llm_router.LlmCallConfig(provider="openai", api_key="")))


@pytest.mark.parametrize("provider, model", [
    ("gemini", "gemini-private-memory-42"),
    ("openai", "private-memory-42"),
    ("deepseek", "private-memory-42"),
    ("openrouter", "private-memory-42"),
    ("anthropic", "private-memory-42"),
])
def test_metadata_probe_rejects_non_catalog_model_before_http(monkeypatch, provider, model):
    """Even a fixed prompt must not carry caller text through its model field."""
    def forbidden(*args, **kwargs):
        raise AssertionError("unknown probe model must fail before HTTP")
    monkeypatch.setattr(llm_router.httpx, "AsyncClient", forbidden)
    with pytest.raises(ValueError, match="reviewed .* catalog"):
        asyncio.run(llm_router.test_connection(
            llm_router.LlmCallConfig(
                provider=provider, api_key="synthetic-key", model=model,
            )
        ))


def test_public_probe_handler_rejects_gemini_model_payload(monkeypatch):
    """The existing /llm/test handler must reject model-field smuggling."""
    from fastapi import HTTPException
    from api.llm_routes import LlmTestBody, _run_llm_test

    def forbidden(*args, **kwargs):
        raise AssertionError("no HTTP for non-catalog metadata-only probe")
    monkeypatch.setattr(llm_router.httpx, "AsyncClient", forbidden)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(_run_llm_test(LlmTestBody(
            provider="gemini", api_key="synthetic-key",
            model="gemini-private-memory-42",
        )))
    assert exc.value.status_code == 400


def test_non_catalog_model_remains_permitted_in_raw_chat():
    """Only metadata-only probes are narrowed, not normal consented chat."""
    llm_router.assert_model_allowed(llm_router.LlmCallConfig(
        provider="gemini", api_key="synthetic-key",
        model="gemini-private-memory-42",
    ))
