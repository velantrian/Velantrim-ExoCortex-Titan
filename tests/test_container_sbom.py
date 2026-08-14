from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_container_sbom import validate_container_sbom


WORKFLOW = Path(".github/workflows/docker.yml")


def _package(name: str, purl: str) -> dict[str, object]:
    return {
        "name": name,
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": purl,
            }
        ],
    }


def _spdx() -> dict[str, object]:
    return {
        "SPDXID": "SPDXRef-DOCUMENT",
        "spdxVersion": "SPDX-2.2",
        "name": "titan-runtime",
        "packages": [
            _package("libc6", "pkg:deb/debian/libc6@2.36"),
            _package("fastapi", "pkg:pypi/fastapi@1.0.0"),
        ],
    }


def test_validator_accepts_direct_spdx_with_os_and_python_packages() -> None:
    summary = validate_container_sbom(_spdx())

    assert summary["package_count"] == 2
    assert summary["debian_os_package_count"] == 1
    assert summary["python_pypi_package_count"] == 1


def test_validator_accepts_in_toto_spdx_predicate() -> None:
    wrapped = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://spdx.dev/Document",
        "predicate": _spdx(),
    }

    summary = validate_container_sbom(wrapped)
    assert summary["spdx_version"] == "SPDX-2.2"


def test_validator_fails_closed_without_os_or_python_inventory() -> None:
    no_os = _spdx()
    no_os["packages"] = [_package("fastapi", "pkg:pypi/fastapi@1.0.0")]
    with pytest.raises(ValueError, match="Debian/OS"):
        validate_container_sbom(no_os)

    no_python = _spdx()
    no_python["packages"] = [_package("libc6", "pkg:deb/debian/libc6@2.36")]
    with pytest.raises(ValueError, match="Python/PyPI"):
        validate_container_sbom(no_python)


def test_docker_workflow_generates_and_publishes_final_image_sbom() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "docker buildx build --no-cache" in text
    assert "--sbom=true" in text
    assert "--output type=local,dest=container-sbom-out" in text
    assert "--load" in text
    assert "container-sbom-out/sbom.spdx.json" in text
    assert "scripts/validate_container_sbom.py" in text
    assert "name: titan-container-sbom" in text
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in text
    assert "docker login" not in text.lower()
    assert "--push" not in text


def test_validator_summary_is_json_serializable() -> None:
    json.dumps(validate_container_sbom(_spdx()), sort_keys=True)
