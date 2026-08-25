from __future__ import annotations

import argparse
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
import webbrowser
from pathlib import Path
from typing import Iterable

MIN_PYTHON = (3, 11)
DEFAULT_PORT = 8755
REQUIRED_PROJECT_FILES = (
    "pyproject.toml",
    "server.py",
    "static/console/index.html",
)
RUNTIME_IMPORTS = (
    "fastapi",
    "uvicorn",
    "dotenv",
    "pydantic",
    "httpx",
    "aiosqlite",
    "pymorphy3",
    "pypdf",
    "docx",
    "openpyxl",
    "yaml",
    "PIL",
)


class BootstrapError(RuntimeError):
    """A user-actionable first-run failure."""


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def require_supported_python(version_info=None) -> None:
    version_info = version_info or sys.version_info
    if tuple(version_info[:2]) < MIN_PYTHON:
        raise BootstrapError(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required; "
            f"found {version_info[0]}.{version_info[1]}."
        )


def validate_project(root: Path) -> None:
    missing = [name for name in REQUIRED_PROJECT_FILES if not (root / name).exists()]
    if missing:
        raise BootstrapError(
            "Titan project files are missing: " + ", ".join(missing) + ". "
            "Run this script from a complete Titan checkout."
        )


def venv_python(root: Path, *, platform: str | None = None) -> Path:
    platform = platform or os.name
    if platform == "nt":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def _replace_or_append(lines: list[str], key: str, value: str, *, only_if_blank: bool = False) -> None:
    prefix = f"{key}="
    for index, raw in enumerate(lines):
        if not raw.lstrip().startswith(prefix):
            continue
        current = raw.split("=", 1)[1].strip()
        if only_if_blank and current:
            return
        lines[index] = f"{key}={value}\n"
        return
    lines.append(f"{key}={value}\n")


def ensure_env(root: Path) -> tuple[Path, bool]:
    env_path = root / ".env"
    created = not env_path.exists()
    if created:
        template = root / ".env.example"
        if template.exists():
            lines = template.read_text(encoding="utf-8").splitlines(keepends=True)
        else:
            lines = []
    else:
        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)

    _replace_or_append(lines, "VELANTRIM_API_KEY", secrets.token_urlsafe(32), only_if_blank=True)

    if created:
        _replace_or_append(lines, "VELANTRIM_ALLOW_OPEN", "false")
        _replace_or_append(lines, "VELANTRIM_NETWORK_MODE", "deny")
        _replace_or_append(lines, "VELANTRIM_REMOTE_DATA_MODE", "never")
        _replace_or_append(lines, "LLM_PROVIDER", "none")

    env_path.write_text("".join(lines), encoding="utf-8")
    return env_path, created


def create_venv(root: Path) -> Path:
    target = root / ".venv"
    py = venv_python(root)
    if py.exists():
        return py
    try:
        venv.EnvBuilder(with_pip=True).create(target)
    except Exception as exc:
        raise BootstrapError(
            "Could not create .venv. Ensure the Python venv module is installed "
            "and the project directory is writable."
        ) from exc
    if not py.exists():
        raise BootstrapError(".venv was created but its Python executable is missing.")
    return py


def dependency_check_command(py: Path) -> list[str]:
    imports = "; ".join(f"import {name}" for name in RUNTIME_IMPORTS)
    return [str(py), "-c", imports]


def dependencies_ready(py: Path, *, runner=subprocess.run) -> bool:
    result = runner(
        dependency_check_command(py),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def install_server_dependencies(root: Path, py: Path, *, runner=subprocess.run) -> None:
    try:
        runner(
            [
                str(py),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-e",
                f"{root}[server,parsers]",
            ],
            cwd=root,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise BootstrapError(
            "Titan V1 runtime dependencies could not be installed. Check internet access, "
            "Python package index access, and the error above."
        ) from exc


def port_is_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def wait_until_ready(process: subprocess.Popen, base_url: str, timeout_s: float = 45.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise BootstrapError(
                f"Titan server exited during startup with code {process.returncode}. "
                "Review the server error printed above."
            )
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as response:
                if 200 <= response.status < 500:
                    return
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                return
            last_error = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(0.5)
    detail = f" Last error: {last_error}" if last_error else ""
    raise BootstrapError(f"Titan did not become ready within {timeout_s:.0f}s.{detail}")


def build_server_command(py: Path, port: int) -> list[str]:
    return [
        str(py),
        "-m",
        "uvicorn",
        "server:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the bounded Titan V1 runtime and launch the local web console."
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Do not install missing runtime dependencies; fail with a clear message instead.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    require_supported_python()
    root = project_root()
    validate_project(root)

    if not (1 <= args.port <= 65535):
        raise BootstrapError("Port must be between 1 and 65535.")
    if not port_is_available(args.port):
        raise BootstrapError(
            f"Port {args.port} is already in use. Stop the existing process or pass --port <free-port>."
        )

    env_path, env_created = ensure_env(root)
    py = create_venv(root)

    if not dependencies_ready(py):
        if args.no_install:
            raise BootstrapError(
                "Titan V1 runtime dependencies are missing in .venv. Re-run without --no-install."
            )
        print("[Titan] Installing bounded V1 server + file parser dependencies into .venv ...", flush=True)
        install_server_dependencies(root, py)
        if not dependencies_ready(py):
            raise BootstrapError("Dependency installation finished, but required imports still fail.")

    base_url = f"http://127.0.0.1:{args.port}"
    console_url = f"{base_url}/console/"
    child_env = os.environ.copy()
    child_env.setdefault("PORT", str(args.port))
    child_env.setdefault("SLEEP_WORKER_ENABLED", "false")
    child_env.setdefault("LLM_PROVIDER", "none")

    print("\nVELANTRIM TITAN 9.0")
    print(f"Project: {root}")
    print(f"Environment: {env_path}{' (created)' if env_created else ''}")
    print(f"Console: {console_url}")
    print("LLM is optional for first run and remains off until you configure a provider.")
    print("File parsing for the bounded V1 formats is installed with this runtime.")
    print("Press Ctrl+C to stop Titan.\n")

    process = subprocess.Popen(
        build_server_command(py, args.port),
        cwd=root,
        env=child_env,
    )
    try:
        wait_until_ready(process, base_url)
        print(f"[Titan] Ready: {console_url}", flush=True)
        if not args.no_browser:
            webbrowser.open(console_url)
        return process.wait()
    except KeyboardInterrupt:
        print("\n[Titan] Stopping ...", flush=True)
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main() -> int:
    try:
        return run()
    except BootstrapError as exc:
        print(f"[Titan] First-run error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
