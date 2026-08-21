from __future__ import annotations

from pathlib import Path

import pytest

from core.provider_catalog import list_providers
from scripts import configure_llm


def test_server_provider_catalog_is_unique_and_executable():
    catalog = {str(item["id"]): item for item in list_providers()}
    ids = [str(item["id"]) for item in list_providers()]

    assert len(ids) == len(set(ids)), "provider catalog must not contain duplicate ids"
    assert set(ids) == set(configure_llm.PROVIDERS)
    assert {
        provider_id: str(item["default_model"])
        for provider_id, item in catalog.items()
    } == {
        provider_id: spec.default_model
        for provider_id, spec in configure_llm.PROVIDERS.items()
    }
    assert catalog["openrouter"]["default_model"] == "openai/gpt-chat-latest"


def test_requires_explicit_remote_data_consent(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "VELANTRIM_NETWORK_MODE=deny\nVELANTRIM_REMOTE_DATA_MODE=never\n",
        encoding="utf-8",
    )
    before = env.read_text(encoding="utf-8")

    with pytest.raises(configure_llm.LlmSetupError, match="consent"):
        configure_llm.configure_env(
            env,
            provider="openai",
            api_key="sk-test",
            remote_data_consent=False,
        )

    assert env.read_text(encoding="utf-8") == before


def test_configure_openai_preserves_unrelated_env(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "VELANTRIM_API_KEY=titan-secret\n"
        "CUSTOM_FLAG=keep\n"
        "LLM_PROVIDER=none\n"
        "VELANTRIM_NETWORK_MODE=deny\n"
        "VELANTRIM_REMOTE_DATA_MODE=never\n",
        encoding="utf-8",
    )

    configure_llm.configure_env(
        env,
        provider="openai",
        api_key="sk-provider",
        model="gpt-5.5",
        remote_data_consent=True,
    )

    text = env.read_text(encoding="utf-8")
    assert "VELANTRIM_API_KEY=titan-secret" in text
    assert "CUSTOM_FLAG=keep" in text
    assert "LLM_PROVIDER=openai" in text
    assert "OPENAI_API_KEY=sk-provider" in text
    assert "OPENAI_MODEL=gpt-5.5" in text
    assert "VELANTRIM_NETWORK_MODE=allow" in text
    assert "VELANTRIM_REMOTE_DATA_MODE=allowed" in text


def test_status_never_returns_or_prints_secret(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "LLM_PROVIDER=gemini\n"
        "GEMINI_API_KEY=super-secret\n"
        "GEMINI_MODEL=gemini-3.5-flash\n"
        "VELANTRIM_NETWORK_MODE=allow\n"
        "VELANTRIM_REMOTE_DATA_MODE=allowed\n",
        encoding="utf-8",
    )

    info = configure_llm.status(env)
    rendered = configure_llm.format_status(info)

    assert info["key_configured"] is True
    assert info["probe_ready"] is True
    assert info["chat_ready"] is True
    assert "super-secret" not in repr(info)
    assert "super-secret" not in rendered


def test_network_only_is_probe_ready_but_not_chat_ready(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "LLM_PROVIDER=deepseek\n"
        "DEEPSEEK_API_KEY=sk-test\n"
        "VELANTRIM_NETWORK_MODE=allow\n"
        "VELANTRIM_REMOTE_DATA_MODE=never\n",
        encoding="utf-8",
    )

    info = configure_llm.status(env)

    assert info["probe_ready"] is True
    assert info["chat_ready"] is False


def test_rejects_non_executable_qwen_direct_provider(tmp_path: Path):
    env = tmp_path / ".env"

    with pytest.raises(configure_llm.LlmSetupError, match="Unsupported direct provider"):
        configure_llm.configure_env(
            env,
            provider="qwen",
            api_key="qwen-secret",
            remote_data_consent=True,
        )

    assert not env.exists()


def test_cancelled_interactive_setup_does_not_create_env(tmp_path: Path):
    answers = iter(["1", "", "NO"])

    with pytest.raises(configure_llm.LlmSetupError, match="Consent phrase"):
        configure_llm.run(
            [],
            root=tmp_path,
            input_fn=lambda _: next(answers),
            secret_fn=lambda _: "sk-secret",
        )

    assert not (tmp_path / ".env").exists()


def test_interactive_setup_uses_template_and_preserves_titan_key(tmp_path: Path):
    (tmp_path / ".env.example").write_text(
        "VELANTRIM_API_KEY=titan-key\n"
        "LLM_PROVIDER=none\n"
        "VELANTRIM_NETWORK_MODE=deny\n"
        "VELANTRIM_REMOTE_DATA_MODE=never\n",
        encoding="utf-8",
    )
    answers = iter(["gemini", "", "ALLOW REMOTE DATA"])

    rc = configure_llm.run(
        [],
        root=tmp_path,
        input_fn=lambda _: next(answers),
        secret_fn=lambda _: "AIza-secret",
    )

    assert rc == 0
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "VELANTRIM_API_KEY=titan-key" in text
    assert "LLM_PROVIDER=gemini" in text
    assert "GEMINI_API_KEY=AIza-secret" in text
    assert "GEMINI_MODEL=gemini-3.5-flash" in text
