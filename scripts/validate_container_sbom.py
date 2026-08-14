"""Validate the BuildKit SPDX SBOM for Titan's final runtime image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SPDX_PREDICATE = "https://spdx.dev/Document"


def _spdx_document(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept either direct SPDX JSON or an in-toto SPDX predicate wrapper."""
    if isinstance(payload.get("spdxVersion"), str):
        return payload

    if payload.get("predicateType") == SPDX_PREDICATE and isinstance(payload.get("predicate"), dict):
        return payload["predicate"]

    raise ValueError("container SBOM is neither direct SPDX JSON nor an in-toto SPDX predicate")


def _package_purls(package: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    refs = package.get("externalRefs", [])
    if not isinstance(refs, list):
        return ()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        locator = ref.get("referenceLocator")
        if isinstance(locator, str) and locator.startswith("pkg:"):
            values.append(locator)
    return tuple(values)


def validate_container_sbom(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a compact validation summary or raise ValueError fail-closed."""
    document = _spdx_document(payload)

    spdx_version = document.get("spdxVersion")
    if not isinstance(spdx_version, str) or not spdx_version.startswith("SPDX-"):
        raise ValueError("container SBOM has no valid SPDX version")

    packages = document.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ValueError("container SBOM contains no packages")

    purls: list[str] = []
    for package in packages:
        if isinstance(package, dict):
            purls.extend(_package_purls(package))

    debian_purls = [value for value in purls if value.startswith("pkg:deb/")]
    python_purls = [value for value in purls if value.startswith("pkg:pypi/")]

    if not debian_purls:
        raise ValueError("container SBOM does not identify any Debian/OS packages by purl")
    if not python_purls:
        raise ValueError("container SBOM does not identify any Python/PyPI packages by purl")

    return {
        "spdx_version": spdx_version,
        "document_name": str(document.get("name") or ""),
        "package_count": len(packages),
        "purl_count": len(purls),
        "debian_os_package_count": len(debian_purls),
        "python_pypi_package_count": len(python_purls),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("container SBOM root must be a JSON object")

    try:
        summary = validate_container_sbom(payload)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
