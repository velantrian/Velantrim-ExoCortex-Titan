import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _generate(output: Path) -> bytes:
    subprocess.run(
        [
            sys.executable,
            "scripts/generate_sbom.py",
            "--output",
            str(output),
        ],
        check=True,
    )
    return output.read_bytes()


def test_sbom_from_uv_lock_is_deterministic_and_bound(tmp_path: Path) -> None:
    first = _generate(tmp_path / "first.json")
    second = _generate(tmp_path / "second.json")
    assert first == second

    document = json.loads(first)
    assert document["bomFormat"] == "CycloneDX"
    assert document["specVersion"] == "1.6"
    assert document["serialNumber"].startswith("urn:uuid:")
    assert document["metadata"]["component"]["name"] == "velantrim-titan"

    properties = {
        item["name"]: item["value"]
        for item in document["metadata"]["properties"]
    }
    assert properties["velantrim:sbom-scope"] == "uv-lock-universe"
    assert properties["velantrim:uv-lock-sha256"] == hashlib.sha256(
        Path("uv.lock").read_bytes()
    ).hexdigest()
    assert properties["velantrim:pyproject-sha256"] == hashlib.sha256(
        Path("pyproject.toml").read_bytes()
    ).hexdigest()
    assert properties["velantrim:reproducible"] == "true"

    components = document["components"]
    assert components
    assert len({component["bom-ref"] for component in components}) == len(components)
    assert any(component["name"] == "fastapi" for component in components)
    assert all(
        component.get("purl", "").startswith("pkg:pypi/")
        for component in components
        if any(
            prop["name"] == "velantrim:uv-source-kind" and prop["value"] == "registry"
            for prop in component["properties"]
        )
    )

    sort_keys = [
        (
            _normalize_name(component["name"]),
            component["version"],
            component["bom-ref"],
        )
        for component in components
    ]
    assert sort_keys == sorted(sort_keys)
