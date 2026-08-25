from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


class UpdateError(RuntimeError):
    """A user-actionable bounded update failure."""


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def _run(
    command: list[str],
    *,
    root: Path,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=root,
        check=check,
        text=True,
        capture_output=capture,
    )


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    if shutil.which("git") is None:
        raise UpdateError("Git is required for in-place updates. Install Git or use a fresh Titan checkout.")
    try:
        return _run(["git", *args], root=root, check=check)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        suffix = f" Details: {detail}" if detail else ""
        raise UpdateError(f"Git command failed: git {' '.join(args)}.{suffix}") from exc


def validate_checkout(root: Path) -> None:
    if not (root / ".git").exists():
        raise UpdateError(
            "This directory is not a Git checkout. In-place update is unavailable; "
            "download/clone a fresh Titan checkout and preserve your local .env and data files."
        )
    if not (root / "pyproject.toml").exists() or not (root / "scripts" / "bootstrap_titan.py").exists():
        raise UpdateError("Titan project files are missing. Run the updater from a complete Titan checkout.")


def require_clean_tree(root: Path) -> None:
    status = git(root, "status", "--porcelain").stdout.strip()
    if status:
        raise UpdateError(
            "Local changes are present. Commit, stash, or remove them before updating; "
            "Titan will not overwrite a modified working tree."
        )


def current_branch(root: Path) -> str:
    return git(root, "branch", "--show-current").stdout.strip()


def current_sha(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").stdout.strip()


def remote_sha(root: Path) -> str:
    return git(root, "rev-parse", "origin/main").stdout.strip()


def fetch_main(root: Path) -> None:
    git(root, "fetch", "--prune", "origin", "main")


def require_fast_forward(root: Path, old_sha: str, new_sha: str) -> None:
    result = git(root, "merge-base", "--is-ancestor", old_sha, new_sha, check=False)
    if result.returncode != 0:
        raise UpdateError(
            "Local main and origin/main have diverged. Automatic update is refused. "
            "Resolve the Git history explicitly instead of forcing an update."
        )


def venv_python(root: Path) -> Path:
    if sys.platform == "win32":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def refresh_runtime(root: Path) -> bool:
    py = venv_python(root)
    if not py.exists():
        return False
    try:
        _run(
            [
                str(py),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-e",
                f"{root}[server,parsers]",
            ],
            root=root,
            capture=False,
        )
    except subprocess.CalledProcessError as exc:
        raise UpdateError(
            "Code was updated, but runtime dependencies could not be refreshed. "
            "Fix package-index/network access and re-run this updater."
        ) from exc
    return True


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check or apply a bounded fast-forward Titan V1 update from origin/main."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the update. Without this flag the command only checks and reports.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    validate_checkout(root)

    branch = current_branch(root)
    if branch != "main":
        raise UpdateError(
            f"Current branch is {branch or '<detached>'}, not main. "
            "Switch to a clean main checkout before updating."
        )

    require_clean_tree(root)
    old_sha = current_sha(root)
    fetch_main(root)
    new_sha = remote_sha(root)

    print(f"Current: {old_sha}")
    print(f"Remote main: {new_sha}")

    if old_sha == new_sha:
        print("Titan is already up to date.")
        return 0

    require_fast_forward(root, old_sha, new_sha)
    if not args.apply:
        print("Update available. Re-run with --apply to fast-forward safely.")
        return 0

    git(root, "merge", "--ff-only", "origin/main")
    refreshed = refresh_runtime(root)

    print(f"Updated Titan: {old_sha} -> {new_sha}")
    if refreshed:
        print("Runtime dependencies refreshed in the existing .venv.")
    else:
        print("No .venv found. Run: python scripts/bootstrap_titan.py")
    print("Local .env and ignored SQLite state are not modified by this updater.")
    print(f"Rollback reference (if explicitly needed): {old_sha}")
    return 0


def main() -> int:
    try:
        return run()
    except UpdateError as exc:
        print(f"[Titan update] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
