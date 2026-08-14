import tomllib
from pathlib import Path


WORKFLOW = Path(".github/workflows/ci.yml")
PYPROJECT = Path("pyproject.toml")
PDF_PARSER = Path("core/file_parsers/pdf_parser.py")


def test_dependency_audit_is_frozen_lock_bound_and_fail_closed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "name: Dependency vulnerability audit" in text
    assert "uv --preview-features audit-command,json-output audit" in text
    assert "--frozen" in text
    assert "--output-format json" in text
    assert "--ignore " not in text
    assert "--ignore-until-fixed" not in text
    assert "name: titan-dependency-audit" in text
    assert "titan-dependency-audit.metadata.txt" in text
    assert "titan-dependency-audit.exit-code" in text
    assert "Fail closed on reported vulnerability or audit error" in text


def test_dependency_audit_uses_repository_uv_and_pinned_artifact_action() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    audit_section = text.split("  dependency-audit:\n", 1)[1]
    assert "astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86" in audit_section
    assert "version: 0.12.3" in audit_section
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in audit_section
    assert "if: always()" in audit_section
    assert "service_url=https://api.osv.dev/" in audit_section
    assert "lock_sha256=" in audit_section


def test_direct_dependency_security_floors_and_archived_owners() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    with PYPROJECT.open("rb") as handle:
        payload = tomllib.load(handle)

    build_system = payload["build-system"]
    assert build_system["build-backend"] == "setuptools.build_meta"

    build_requires = build_system["requires"]
    assert isinstance(build_requires, list)
    assert len(build_requires) == 1
    setuptools_requirement = build_requires[0]
    assert isinstance(setuptools_requirement, str)
    assert setuptools_requirement.startswith("setuptools>=")
    setuptools_floor = int(setuptools_requirement.removeprefix("setuptools>=").split(",", 1)[0])
    assert setuptools_floor >= 83
    assert not any(requirement.lower().startswith("wheel") for requirement in build_requires)

    assert '"pypdf>=6.14.2,<7"' in text
    assert '"pypdf2>=' not in text.lower()
    assert '"pillow>=12.3.0"' in text
    assert '"pytest>=9.0.3,<10"' in text
    assert '"pytest-asyncio>=1.4.0,<2"' in text
    assert '"kuzu>=' not in text
    assert '"ladybug>=0.17"' in text


def test_pdf_fallback_cannot_silently_reintroduce_pypdf2() -> None:
    text = PDF_PARSER.read_text(encoding="utf-8")

    assert 'PYPDF_AVAILABLE = _check_available("pypdf")' in text
    assert "from pypdf import PdfReader" in text
    assert "from PyPDF2 import PdfReader" not in text
    assert "PYPDF2_AVAILABLE" not in text
