#!/usr/bin/env python3
"""Export selected project runtime extras from the authoritative uv.lock."""

from __future__ import annotations

import argparse
import subprocess
import tomllib
from pathlib import Path


def parse_extras(raw: str, pyproject_path: Path) -> tuple[str, ...]:
    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    optional = project.get("project", {}).get("optional-dependencies", {})
    if not isinstance(optional, dict):
        raise ValueError("pyproject.toml has no [project.optional-dependencies] table")

    extras: list[str] = []
    for item in raw.split(","):
        extra = item.strip()
        if not extra:
            continue
        if extra not in optional:
            raise ValueError(f"unknown runtime extra: {extra}")
        if extra in extras:
            raise ValueError(f"duplicate runtime extra: {extra}")
        extras.append(extra)
    return tuple(extras)


def build_export_command(extras: tuple[str, ...], output: Path) -> list[str]:
    command = [
        "uv",
        "export",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--format",
        "requirements-txt",
        "--output-file",
        str(output),
    ]
    for extra in extras:
        command.extend(("--extra", extra))
    return command


def export_locked_requirements(
    *,
    extras_raw: str,
    pyproject_path: Path,
    output: Path,
) -> None:
    extras = parse_extras(extras_raw, pyproject_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(build_export_command(extras, output), check=True)
    if not output.exists():
        raise RuntimeError("uv export completed without creating the requirements file")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extras", default="server")
    parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/velantrim-runtime-requirements.txt"),
    )
    args = parser.parse_args()

    try:
        export_locked_requirements(
            extras_raw=args.extras,
            pyproject_path=args.project,
            output=args.output,
        )
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, tomllib.TOMLDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
