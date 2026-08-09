#!/usr/bin/env python3
"""Validate the machine-readable Titan project-state contract.

The state file deliberately records the exact main SHA inspected, not an evergreen
claim that a hard-coded SHA is still the current repository head. CI can therefore
validate semantics and arithmetic without pretending to query GitHub at runtime.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PROJECT_STATE_PATH = Path("docs/state/project_state.json")
TITAN_AUDIT_PAGE_ID = "398ac84d-0547-81fe-8ca5-d0d2727d1961"


class ProjectStateError(ValueError):
    """Raised when the project-state contract is malformed or inconsistent."""


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectStateError(f"{field} must be an object")
    return value


def _require_bool(mapping: dict[str, Any], field: str) -> bool:
    value = mapping.get(field)
    if not isinstance(value, bool):
        raise ProjectStateError(f"{field} must be a boolean")
    return value


def _require_int(mapping: dict[str, Any], field: str, *, minimum: int = 0) -> int:
    value = mapping.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ProjectStateError(f"{field} must be an integer >= {minimum}")
    return value


def _require_string(mapping: dict[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProjectStateError(f"{field} must be a non-empty string")
    return value


def _require_literal(mapping: dict[str, Any], field: str, expected: str) -> str:
    value = _require_string(mapping, field)
    if value != expected:
        raise ProjectStateError(f"{field} must be {expected!r}")
    return value


def _require_sha(mapping: dict[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ProjectStateError(f"{field} must be a lowercase 40-character SHA")
    return value


def validate_project_state(data: Any) -> dict[str, Any]:
    """Validate shape, SHA semantics, readiness arithmetic and safety boundaries."""

    root = _require_mapping(data, "root")
    if root.get("schema_version") != 1:
        raise ProjectStateError("schema_version must be 1")
    if root.get("project") != "velantrim-exocortex-titan":
        raise ProjectStateError("project must be 'velantrim-exocortex-titan'")

    repository = _require_mapping(root.get("repository"), "repository")
    verified_head = _require_sha(repository, "repository_head_sha_at_verification")
    implementation = _require_sha(repository, "implementation_baseline_sha")
    checkpoint = _require_sha(repository, "documentation_checkpoint_sha")
    if verified_head != checkpoint:
        raise ProjectStateError(
            "repository_head_sha_at_verification must equal documentation_checkpoint_sha"
        )
    if not isinstance(repository.get("head_semantics"), str) or not repository[
        "head_semantics"
    ].strip():
        raise ProjectStateError("repository.head_semantics must explain the three SHA roles")

    continuity = _require_mapping(root.get("continuity"), "continuity")
    completed = continuity.get("completed_capabilities")
    total = continuity.get("total_capabilities")
    remaining = continuity.get("remaining_capabilities")
    readiness = continuity.get("readiness_percent")
    remaining_percent = continuity.get("remaining_percent")
    if not all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in (completed, total, remaining)
    ):
        raise ProjectStateError("Continuity capability counts must be integers")
    if total <= 0 or completed < 0 or completed > total:
        raise ProjectStateError("Continuity capability counts are out of range")
    if remaining != total - completed:
        raise ProjectStateError("remaining_capabilities must equal total - completed")
    expected_readiness = round(100.0 * completed / total, 1)
    expected_remaining = round(100.0 * remaining / total, 1)
    if not isinstance(readiness, (int, float)) or not math.isclose(
        float(readiness), expected_readiness, abs_tol=0.05
    ):
        raise ProjectStateError(
            f"readiness_percent must equal {expected_readiness} for {completed}/{total}"
        )
    if not isinstance(remaining_percent, (int, float)) or not math.isclose(
        float(remaining_percent), expected_remaining, abs_tol=0.05
    ):
        raise ProjectStateError(
            f"remaining_percent must equal {expected_remaining} for {remaining}/{total}"
        )

    wired = _require_bool(continuity, "wired")
    enabled = _require_bool(continuity, "enabled")
    observed = _require_bool(continuity, "observed")
    runtime_authority = _require_bool(continuity, "runtime_authority")
    if enabled and not wired:
        raise ProjectStateError("Continuity cannot be enabled while wired=false")
    if observed and not enabled:
        raise ProjectStateError("Continuity cannot be observed while enabled=false")
    if runtime_authority and not wired:
        raise ProjectStateError("Continuity cannot have runtime authority while wired=false")

    governance = _require_mapping(root.get("governance"), "governance")
    _require_bool(governance, "aggregate_merge_evidence_present")
    _require_bool(governance, "codeowners_present")
    _require_bool(governance, "branch_ruleset_enforced")
    _require_int(governance, "tracking_issue", minimum=1)
    _require_int(governance, "ruleset_id", minimum=1)
    _require_literal(governance, "ruleset_name", "main-governance")
    _require_literal(governance, "ruleset_mode", "SOLO")
    required_approvals = _require_int(governance, "required_approvals")
    if required_approvals != 0:
        raise ProjectStateError("governance.required_approvals must be 0 in SOLO mode")
    if _require_bool(governance, "independent_review_claimed"):
        raise ProjectStateError("governance must not claim independent historical review")
    _require_int(governance, "governance_canary_pr", minimum=1)
    _require_sha(governance, "governance_canary_merge_sha")
    _require_int(governance, "retrospective_audit_issue", minimum=1)
    _require_int(governance, "retrospective_audit_pr", minimum=1)
    audit_head = _require_sha(governance, "retrospective_audit_head_sha")
    audit_merge = _require_sha(governance, "retrospective_audit_merge_sha")
    _require_literal(governance, "retrospective_audit_status", "COMPLETE")
    _require_literal(
        governance, "retrospective_audit_issue_state", "CLOSED_COMPLETED"
    )
    if audit_head == audit_merge:
        raise ProjectStateError(
            "governance retrospective audit head and merge SHAs must differ"
        )
    if audit_merge != verified_head or audit_merge != checkpoint:
        raise ProjectStateError(
            "repository audit checkpoint SHAs must equal retrospective_audit_merge_sha"
        )

    notion = _require_mapping(root.get("notion"), "notion")
    _require_literal(notion, "status", "SYNCED_FINAL")
    audit_target = _require_literal(notion, "audit_target", "Velantrim Titan 9.0")
    _require_literal(notion, "audit_page_id", TITAN_AUDIT_PAGE_ID)
    notion_merge = _require_sha(notion, "audit_merge_sha_recorded")
    if notion_merge != audit_merge:
        raise ProjectStateError(
            "notion.audit_merge_sha_recorded must equal retrospective_audit_merge_sha"
        )
    safe_targets = notion.get("safe_targets")
    if not isinstance(safe_targets, list) or not safe_targets or not all(
        isinstance(target, str) and target.strip() for target in safe_targets
    ):
        raise ProjectStateError("notion.safe_targets must be a non-empty string list")
    if audit_target not in safe_targets:
        raise ProjectStateError("notion.audit_target must be included in safe_targets")

    kb = _require_mapping(root.get("knowledge_base"), "knowledge_base")
    if kb.get("artifact_path") != "kb_graph.json":
        raise ProjectStateError("knowledge_base.artifact_path must preserve kb_graph.json")
    if kb.get("preservation_policy") != "KEEP_VERSIONED_KNOWLEDGE_ASSET":
        raise ProjectStateError("KB preservation policy must remain explicit")
    if kb.get("content_removed") is not False:
        raise ProjectStateError("project state must not claim KB content was removed")
    _require_bool(kb, "runtime_authority")

    return {
        "ok": True,
        "verified_head": verified_head,
        "implementation_baseline": implementation,
        "documentation_checkpoint": checkpoint,
        "continuity": f"{completed}/{total}",
        "readiness_percent": expected_readiness,
        "audit_status": governance["retrospective_audit_status"],
        "notion_status": notion["status"],
        "kb_policy": kb["preservation_policy"],
    }


def load_and_validate(path: Path = PROJECT_STATE_PATH) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectStateError(f"cannot read {path}: {exc}") from exc
    return validate_project_state(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=PROJECT_STATE_PATH)
    parser.add_argument(
        "--json", action="store_true", help="emit the validation report as JSON"
    )
    args = parser.parse_args()

    try:
        report = load_and_validate(args.path)
    except ProjectStateError as exc:
        if args.json:
            print(
                json.dumps(
                    {"ok": False, "errors": [str(exc)]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"FAILED: {exc}")
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "OK: project state validated; "
            f"Continuity={report['continuity']} ({report['readiness_percent']}%), "
            f"Audit={report['audit_status']}, Notion={report['notion_status']}, "
            f"KB={report['kb_policy']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
