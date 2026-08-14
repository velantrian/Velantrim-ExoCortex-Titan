from pathlib import Path


WORKFLOW = Path(".github/workflows/ci.yml")


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
