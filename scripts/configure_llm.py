from __future__ import annotations

import argparse
import getpass
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


class LlmSetupError(RuntimeError):
    """User-actionable local LLM setup error."""


@dataclass(frozen=True, slots=True)
class ProviderEnv:
    provider: str
    title: str
    key_env: str
    model_env: str
    default_model: str


# Direct server backends actually implemented by core.llm_router.chat_complete().
# Qwen remains available through OpenRouter model ids; it is not a direct Titan
# server transport and therefore must not be advertised as one here.
PROVIDERS: dict[str, ProviderEnv] = {
    "openai": ProviderEnv(
        "openai", "OpenAI", "OPENAI_API_KEY", "OPENAI_MODEL", "chat-latest"
    ),
    "deepseek": ProviderEnv(
        "deepseek",
        "DeepSeek",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_MODEL",
        "deepseek-v4-flash",
    ),
    "gemini": ProviderEnv(
        "gemini",
        "Google Gemini",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "gemini-3.5-flash",
    ),
    "openrouter": ProviderEnv(
        "openrouter",
        "OpenRouter",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "openai/gpt-chat-latest",
    ),
    "anthropic": ProviderEnv(
        "anthropic",
        "Anthropic Claude",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
        "claude-sonnet-4-6",
    ),
}


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def _validate_env_value(value: str, *, field: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise LlmSetupError(f"{field} must not be empty.")
    if "\n" in cleaned or "\r" in cleaned:
        raise LlmSetupError(f"{field} contains a forbidden newline.")
    return cleaned


def _replace_or_append(lines: list[str], key: str, value: str) -> None:
    prefix = f"{key}="
    for index, raw in enumerate(lines):
        if raw.lstrip().startswith(prefix):
            lines[index] = f"{key}={value}\n"
            return
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(f"{key}={value}\n")


def _read_env_lines(env_path: Path, template_path: Path | None = None) -> list[str]:
    if env_path.exists():
        return env_path.read_text(encoding="utf-8").splitlines(keepends=True)
    if template_path and template_path.exists():
        return template_path.read_text(encoding="utf-8").splitlines(keepends=True)
    return []


def _atomic_write_text(path: Path, text: str) -> None:
    """Replace .env atomically so an interrupted setup does not truncate it."""

    path.parent.mkdir(parents=True, exist_ok=True)
    previous_mode = path.stat().st_mode if path.exists() else None
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if previous_mode is not None:
            os.chmod(tmp_path, previous_mode)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def configure_env(
    env_path: Path,
    *,
    provider: str,
    api_key: str,
    model: str | None = None,
    remote_data_consent: bool,
    template_path: Path | None = None,
) -> ProviderEnv:
    """Persist one explicit remote-provider choice without touching unrelated env keys."""

    pid = (provider or "").strip().lower()
    spec = PROVIDERS.get(pid)
    if spec is None:
        allowed = ", ".join(PROVIDERS)
        raise LlmSetupError(
            f"Unsupported direct provider {provider!r}. Choose one of: {allowed}."
        )
    secret = _validate_env_value(api_key, field="Provider API key")
    selected_model = _validate_env_value(
        (model or "").strip() or spec.default_model,
        field="Model",
    )
    if not remote_data_consent:
        raise LlmSetupError(
            "Remote-data consent was not granted. Titan remains local-first and unchanged."
        )

    lines = _read_env_lines(env_path, template_path)
    _replace_or_append(lines, "LLM_PROVIDER", pid)
    _replace_or_append(lines, spec.key_env, secret)
    _replace_or_append(lines, spec.model_env, selected_model)
    _replace_or_append(lines, "VELANTRIM_NETWORK_MODE", "allow")
    _replace_or_append(lines, "VELANTRIM_REMOTE_DATA_MODE", "allowed")
    _atomic_write_text(env_path, "".join(lines))
    return spec


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def status(env_path: Path) -> dict[str, object]:
    """Return user-facing readiness without ever returning a provider secret."""

    env = parse_env(env_path)
    pid = (env.get("LLM_PROVIDER") or "none").lower()
    spec = PROVIDERS.get(pid)
    network = (env.get("VELANTRIM_NETWORK_MODE") or "deny").lower()
    remote_data = (env.get("VELANTRIM_REMOTE_DATA_MODE") or "never").lower()
    key_configured = bool(spec and env.get(spec.key_env, "").strip())
    model = env.get(spec.model_env, spec.default_model) if spec else None
    return {
        "provider": pid,
        "model": model,
        "key_configured": key_configured,
        "network_mode": network,
        "remote_data_mode": remote_data,
        # A connectivity probe carries only a fixed Titan-owned prompt, so it
        # needs network permission but not raw remote-data permission.
        "probe_ready": bool(key_configured and network == "allow"),
        # Normal chat sends user prompt/context and therefore requires raw data
        # permission in addition to network permission.
        "chat_ready": bool(
            key_configured and network == "allow" and remote_data == "allowed"
        ),
    }


def format_status(info: dict[str, object]) -> str:
    key_state = "yes" if info["key_configured"] else "no"
    return "\n".join(
        [
            f"Provider: {info['provider']}",
            f"Model: {info['model'] or '-'}",
            f"API key configured: {key_state}",
            f"Network policy: {info['network_mode']}",
            f"Remote-data policy: {info['remote_data_mode']}",
            f"Connection test ready: {'yes' if info['probe_ready'] else 'no'}",
            f"Remote chat ready: {'yes' if info['chat_ready'] else 'no'}",
        ]
    )


def _choose_provider(input_fn: Callable[[str], str] = input) -> str:
    ids = list(PROVIDERS)
    print("Supported direct server providers:")
    for index, pid in enumerate(ids, 1):
        print(f"  {index}. {PROVIDERS[pid].title} ({pid})")
    raw = input_fn("Choose provider [1]: ").strip()
    if not raw:
        return ids[0]
    if raw.isdigit() and 1 <= int(raw) <= len(ids):
        return ids[int(raw) - 1]
    pid = raw.lower()
    if pid not in PROVIDERS:
        raise LlmSetupError(f"Unknown provider: {raw}")
    return pid


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explicitly configure a remote LLM for the local Titan server."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show provider/policy readiness without revealing secrets.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def run(
    argv: Iterable[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    secret_fn: Callable[[str], str] = getpass.getpass,
    root: Path | None = None,
) -> int:
    args = parse_args(argv)
    root = root or project_root()
    env_path = root / ".env"
    template_path = root / ".env.example"

    if args.status:
        print(format_status(status(env_path)))
        return 0

    provider = _choose_provider(input_fn)
    spec = PROVIDERS[provider]
    model = input_fn(f"Model [{spec.default_model}]: ").strip() or spec.default_model
    api_key = secret_fn(f"{spec.title} API key (hidden): ").strip()
    if not api_key:
        raise LlmSetupError("API key was empty. No changes were made.")

    print("\nRemote LLM privacy boundary:")
    print("- the connection test sends only a fixed Titan-owned synthetic prompt;")
    print("- normal remote chat sends your prompt and selected memory/context to the provider;")
    print("- this opt-in changes local egress policy from deny/never to allow/allowed;")
    print("- Canon writes remain local; no runtime or production authority is granted.")
    consent = input_fn("Type ALLOW REMOTE DATA to continue: ").strip()
    if consent != "ALLOW REMOTE DATA":
        raise LlmSetupError("Consent phrase did not match. No changes were made.")

    configure_env(
        env_path,
        provider=provider,
        api_key=api_key,
        model=model,
        remote_data_consent=True,
        template_path=template_path,
    )
    print(f"\nConfigured {spec.title} / {model} in .env.")
    print("Secret was not printed. Restart Titan, then use Console -> Test LLM key.")
    print(
        "Run `python scripts/configure_llm.py --status` "
        "to verify readiness without secrets."
    )
    return 0


def main() -> int:
    try:
        return run()
    except LlmSetupError as exc:
        print(f"[Titan LLM setup] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
