from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "configure_provider.py"
spec = importlib.util.spec_from_file_location("configure_provider", MODULE_PATH)
assert spec and spec.loader
provider_setup = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = provider_setup
spec.loader.exec_module(provider_setup)


def _env(tmp_path: Path, content: str | None = None) -> Path:
    path = tmp_path / ".env"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    return path


def test_refuses_without_explicit_remote_data_consent(tmp_path):
    env_path = _env(
        tmp_path,
        "VELANTRIM_API_KEY=server-secret\n"
        "VELANTRIM_NETWORK_MODE=deny\n"
        "VELANTRIM_REMOTE_DATA_MODE=never\n",
    )
    before = env_path.read_text(encoding="utf-8")

    with pytest.raises(provider_setup.ProviderSetupError, match="not authorized"):
        provider_setup.configure_env(
            env_path,
            provider="openai",
            api_key="sk-test-secret",
            model=None,
            allow_remote_data=False,
        )

    assert env_path.read_text(encoding="utf-8") == before


def test_configures_provider_and_existing_policy_only_after_consent(tmp_path):
    env_path = _env(
        tmp_path,
        "VELANTRIM_API_KEY=server-secret\n"
        "VELANTRIM_ALLOW_OPEN=false\n"
        "VELANTRIM_NETWORK_MODE=deny\n"
        "VELANTRIM_REMOTE_DATA_MODE=never\n"
        "LLM_PROVIDER=none\n"
        "UNRELATED_SETTING=keep-me\n",
    )

    result = provider_setup.configure_env(
        env_path,
        provider="deepseek",
        api_key="sk-provider-secret",
        model=None,
        allow_remote_data=True,
    )
    text = env_path.read_text(encoding="utf-8")

    assert result.provider == "deepseek"
    assert "VELANTRIM_API_KEY=server-secret" in text
    assert "VELANTRIM_ALLOW_OPEN=false" in text
    assert "UNRELATED_SETTING=keep-me" in text
    assert "LLM_PROVIDER=deepseek" in text
    assert "DEEPSEEK_API_KEY=sk-provider-secret" in text
    assert "DEEPSEEK_MODEL=deepseek-v4-flash" in text
    assert "VELANTRIM_NETWORK_MODE=allow" in text
    assert "VELANTRIM_REMOTE_DATA_MODE=allowed" in text


def test_switch_provider_preserves_previous_provider_secret(tmp_path):
    env_path = _env(
        tmp_path,
        "VELANTRIM_API_KEY=server-secret\n"
        "LLM_PROVIDER=openai\n"
        "OPENAI_API_KEY=old-openai-secret\n"
        "OPENAI_MODEL=chat-latest\n"
        "VELANTRIM_NETWORK_MODE=allow\n"
        "VELANTRIM_REMOTE_DATA_MODE=allowed\n",
    )

    provider_setup.configure_env(
        env_path,
        provider="gemini",
        api_key="AIza-new-secret",
        model="gemini-2.5-flash",
        allow_remote_data=True,
    )
    text = env_path.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY=old-openai-secret" in text
    assert "LLM_PROVIDER=gemini" in text
    assert "GEMINI_API_KEY=AIza-new-secret" in text


def test_missing_env_requires_bootstrap_first(tmp_path):
    with pytest.raises(provider_setup.ProviderSetupError, match="bootstrap_titan.py"):
        provider_setup.configure_env(
            _env(tmp_path),
            provider="openai",
            api_key="sk-secret",
            model=None,
            allow_remote_data=True,
        )


def test_rejects_unknown_provider_without_writing(tmp_path):
    env_path = _env(tmp_path, "VELANTRIM_API_KEY=server-secret\n")
    before = env_path.read_text(encoding="utf-8")

    with pytest.raises(provider_setup.ProviderSetupError, match="Unsupported provider"):
        provider_setup.configure_env(
            env_path,
            provider="unknown",
            api_key="secret-key",
            model=None,
            allow_remote_data=True,
        )

    assert env_path.read_text(encoding="utf-8") == before


def test_cli_consent_requires_exact_allow():
    assert provider_setup._confirm_remote_data(lambda _: "ALLOW") is True
    assert provider_setup._confirm_remote_data(lambda _: "yes") is False


def test_model_and_secret_reject_newlines(tmp_path):
    env_path = _env(tmp_path, "VELANTRIM_API_KEY=server-secret\n")
    with pytest.raises(provider_setup.ProviderSetupError, match="single line"):
        provider_setup.resolve_provider("openai", "bad\nmodel")
    with pytest.raises(provider_setup.ProviderSetupError, match="single line"):
        provider_setup.configure_env(
            env_path,
            provider="openai",
            api_key="bad\nsecret",
            model=None,
            allow_remote_data=True,
        )
