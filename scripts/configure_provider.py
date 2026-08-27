from __future__ import annotations

import argparse
import getpass
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

PROVIDERS = {
    "openai": ("OPENAI_API_KEY", "OPENAI_MODEL", "chat-latest"),
    "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "deepseek-v4-flash"),
    "gemini": ("GEMINI_API_KEY", "GEMINI_MODEL", "gemini-2.5-flash"),
    "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_MODEL", "openai/chat-latest"),
    "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
}


class ProviderSetupError(RuntimeError):
    """A user-actionable provider-onboarding failure."""


@dataclass(frozen=True)
class ProviderSetup:
    provider: str
    api_key_name: str
    model_name: str
    model: str


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def resolve_provider(provider: str, model: str | None = None) -> ProviderSetup:
    pid = (provider or "").strip().lower()
    if pid not in PROVIDERS:
        raise ProviderSetupError(
            "Unsupported provider. Choose one of: " + ", ".join(sorted(PROVIDERS))
        )
    key_name, model_name, default_model = PROVIDERS[pid]
    selected_model = (model or "").strip() or default_model
    if "\n" in selected_model or "\r" in selected_model:
        raise ProviderSetupError("Model id must be a single line.")
    return ProviderSetup(pid, key_name, model_name, selected_model)


def _set_env_value(lines: list[str], key: str, value: str) -> None:
    if "\n" in value or "\r" in value:
        raise ProviderSetupError(f"{key} must be a single-line value.")
    prefix = f"{key}="
    for index, raw in enumerate(lines):
        stripped = raw.lstrip()
        if stripped.startswith(prefix):
            newline = "\n" if raw.endswith("\n") else ""
            lines[index] = f"{key}={value}{newline}"
            return
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(f"{key}={value}\n")


def read_env(path: Path) -> list[str]:
    if not path.exists():
        raise ProviderSetupError(
            ".env is missing. Run scripts/bootstrap_titan.py first so Titan creates a safe local configuration."
        )
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_env_atomic(path: Path, lines: list[str]) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".env.titan-", dir=path.parent, text=True)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write("".join(lines))
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def configure_env(
    env_path: Path,
    *,
    provider: str,
    api_key: str,
    model: str | None,
    allow_remote_data: bool,
) -> ProviderSetup:
    if not allow_remote_data:
        raise ProviderSetupError(
            "Remote model setup was not authorized. Titan remains local-only: "
            "network=deny, remote_data=never."
        )
    secret = (api_key or "").strip()
    if len(secret) < 4:
        raise ProviderSetupError("Provider API key is empty or too short.")
    if "\n" in secret or "\r" in secret:
        raise ProviderSetupError("Provider API key must be a single line.")

    setup = resolve_provider(provider, model)
    lines = read_env(env_path)
    _set_env_value(lines, "LLM_PROVIDER", setup.provider)
    _set_env_value(lines, setup.api_key_name, secret)
    _set_env_value(lines, setup.model_name, setup.model)
    _set_env_value(lines, "VELANTRIM_NETWORK_MODE", "allow")
    _set_env_value(lines, "VELANTRIM_REMOTE_DATA_MODE", "allowed")
    write_env_atomic(env_path, lines)
    return setup


def _confirm_remote_data(input_fn: Callable[[str], str] = input) -> bool:
    print("\nREMOTE MODEL BOUNDARY")
    print("A remote LLM receives the prompt you send and may receive selected Titan memory/context.")
    print("Titan will keep Canon/write authority local; this only enables outbound model calls.")
    answer = input_fn("Type ALLOW to enable remote network + raw prompt/context egress: ")
    return answer.strip() == "ALLOW"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely configure one supported remote LLM for the local Titan server."
    )
    parser.add_argument("--provider", choices=sorted(PROVIDERS))
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--allow-remote-data",
        action="store_true",
        help="Explicit non-interactive consent to network access and raw prompt/context egress.",
    )
    parser.add_argument("--env-file", type=Path, default=None, help=argparse.SUPPRESS)
    return parser.parse_args(list(argv) if argv is not None else None)


def run(
    argv: Iterable[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    getpass_fn: Callable[[str], str] = getpass.getpass,
) -> int:
    args = parse_args(argv)
    root = project_root()
    env_path = args.env_file or (root / ".env")

    provider = args.provider
    if not provider:
        print("Supported providers: " + ", ".join(sorted(PROVIDERS)))
        provider = input_fn("Provider: ").strip().lower()
    setup = resolve_provider(provider, args.model)

    api_key = getpass_fn(f"{setup.provider} API key (hidden): ").strip()
    allowed = bool(args.allow_remote_data) or _confirm_remote_data(input_fn)
    configured = configure_env(
        env_path,
        provider=setup.provider,
        api_key=api_key,
        model=setup.model,
        allow_remote_data=allowed,
    )

    print("\nTitan provider configuration saved locally in .env.")
    print(f"Provider: {configured.provider}")
    print(f"Model: {configured.model}")
    print("Policy: network=allow, remote_data=allowed (explicit opt-in)")
    print("API key: stored locally and not printed")
    print("Restart Titan, open /console/, enable LLM, and use 'Confirm key' to verify provider connectivity.")
    return 0


def main() -> int:
    try:
        return run()
    except ProviderSetupError as exc:
        print(f"[Titan provider setup] {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nProvider setup cancelled. No consent was granted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
