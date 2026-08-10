#!/usr/bin/env python3
"""Validate Titan's machine-readable project-state contract (schemas v1-v6)."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Callable

PROJECT_STATE_PATH = Path("docs/state/project_state.json")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SUPPORTED_SCHEMA_VERSIONS = frozenset(range(1, 7))
NOTION_TITLE = "Velantrim Titan 9.0"
NOTION_ID = "398ac84d-0547-81fe-8ca5-d0d2727d1961"
AUDIT_MERGE = "90e221be2bed8177f4648787d713058df0f29e1f"
RESOLVER_MERGE = "dc30817f2c4abb1afcaab2f127e679d5f9b884d7"
LIFECYCLE_MERGE = "064845579c520e7464678cd0c41d9b650368dfa8"
WIRING_MERGE = "802e833fa251a8831add8a6b802a5ebb57533549"
ENABLEMENT_MERGE = "66318e6883590cb29a4565157e0a3a25b3716d81"


class ProjectStateError(ValueError):
    """Raised when project state is malformed or contradicts its schema."""


def obj(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectStateError(f"{name} must be an object")
    return value


def literal(record: dict[str, Any], field: str, expected: Any) -> Any:
    value = record.get(field)
    if value != expected:
        raise ProjectStateError(f"{field} must be {expected!r}")
    return value


def boolean(record: dict[str, Any], field: str) -> bool:
    value = record.get(field)
    if not isinstance(value, bool):
        raise ProjectStateError(f"{field} must be a boolean")
    return value


def integer(record: dict[str, Any], field: str, minimum: int = 0) -> int:
    value = record.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ProjectStateError(f"{field} must be an integer >= {minimum}")
    return value


def text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProjectStateError(f"{field} must be a non-empty string")
    return value


def sha(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise ProjectStateError(f"{field} must be a lowercase 40-character SHA")
    return value


def runs(record: dict[str, Any]) -> None:
    for field in (
        "exact_head_continuity_run", "exact_head_full_ci_run",
        "exact_head_docker_run", "exact_head_aggregate_run",
        "post_merge_continuity_run", "post_merge_full_ci_run",
        "post_merge_docker_run", "post_merge_aggregate_run",
    ):
        integer(record, field, 1)


def common(root: dict[str, Any]) -> dict[str, Any]:
    literal(root, "project", "velantrim-exocortex-titan")
    repo = obj(root.get("repository"), "repository")
    literal(repo, "default_branch", "main")
    verified = sha(repo, "repository_head_sha_at_verification")
    implementation = sha(repo, "implementation_baseline_sha")
    checkpoint = sha(repo, "documentation_checkpoint_sha")
    text(repo, "head_semantics")

    continuity = obj(root.get("continuity"), "continuity")
    completed = integer(continuity, "completed_capabilities")
    total = integer(continuity, "total_capabilities", 1)
    remaining = integer(continuity, "remaining_capabilities")
    if completed > total or remaining != total - completed:
        raise ProjectStateError("Continuity capability counts are inconsistent")
    expected_ready = round(completed * 100 / total, 1)
    expected_remaining = round(remaining * 100 / total, 1)
    for field, expected in (
        ("readiness_percent", expected_ready),
        ("remaining_percent", expected_remaining),
    ):
        value = continuity.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isclose(float(value), expected, abs_tol=0.05):
            raise ProjectStateError(f"{field} must equal {expected}")
    wired = boolean(continuity, "wired")
    enabled = boolean(continuity, "enabled")
    observed = boolean(continuity, "observed")
    authority = boolean(continuity, "runtime_authority")
    if enabled and not wired:
        raise ProjectStateError("Continuity cannot be enabled while wired=false")
    if observed and not enabled:
        raise ProjectStateError("Continuity cannot be observed while enabled=false")
    if authority and not wired:
        raise ProjectStateError("Continuity cannot have runtime authority while wired=false")

    governance = obj(root.get("governance"), "governance")
    for field in ("aggregate_merge_evidence_present", "codeowners_present", "branch_ruleset_enforced"):
        boolean(governance, field)
    kb = obj(root.get("knowledge_base"), "knowledge_base")
    literal(kb, "artifact_path", "kb_graph.json")
    literal(kb, "preservation_policy", "KEEP_VERSIONED_KNOWLEDGE_ASSET")
    literal(kb, "content_removed", False)
    boolean(kb, "runtime_authority")
    return {"repo": repo, "continuity": continuity, "completed": completed, "total": total,
            "readiness": expected_ready, "verified": verified, "implementation": implementation,
            "checkpoint": checkpoint, "governance": governance, "kb": kb}


def checkpoint(state: dict[str, Any], expected: str, label: str) -> None:
    if not (state["verified"] == state["implementation"] == state["checkpoint"] == expected):
        raise ProjectStateError(f"verified repository checkpoint must equal the {label} merge SHA")


def governance(record: dict[str, Any]) -> None:
    literal(record, "ruleset_id", 20601712)
    literal(record, "ruleset_name", "main-governance")
    literal(record, "ruleset_mode", "SOLO")
    literal(record, "required_approvals", 0)
    literal(record, "independent_review_claimed", False)
    literal(record, "retrospective_audit_issue", 257)
    literal(record, "retrospective_audit_pr", 261)
    literal(record, "retrospective_audit_head_sha", "54b4f962748610d3a57580506b7c36afa5329a71")
    literal(record, "retrospective_audit_merge_sha", AUDIT_MERGE)
    literal(record, "retrospective_audit_status", "COMPLETE")
    literal(record, "retrospective_audit_issue_state", "CLOSED_COMPLETED")


def notion(root: dict[str, Any], kind: str | None = None, merge: str | None = None) -> dict[str, Any]:
    record = obj(root.get("notion"), "notion")
    literal(record, "status", "SYNCED")
    literal(record, "audit_synchronization_finalized", True)
    literal(record, "audit_target", NOTION_TITLE)
    literal(record, "audit_page_id", NOTION_ID)
    literal(record, "audit_merge_sha_recorded", AUDIT_MERGE)
    if kind is not None and merge is not None:
        literal(record, "latest_status_target", NOTION_TITLE)
        literal(record, "latest_status_page_id", NOTION_ID)
        literal(record, "latest_synchronization_kind", kind)
        literal(record, "latest_implementation_merge_sha", merge)
        literal(record, "latest_synchronization_finalized", True)
    return record


def historical(record: dict[str, Any], *, issue: int, pr: int, head: str, merge: str, authority: str) -> None:
    literal(record, "tracking_issue", issue)
    literal(record, "implementation_pr", pr)
    literal(record, "exact_head_sha", head)
    literal(record, "merge_sha", merge)
    literal(record, "status", "COMPLETE")
    literal(record, "authority", authority)
    runs(record)
    literal(record, "unresolved_review_threads", 0)
    literal(record, "independent_review_claimed", False)


def resolver(root: dict[str, Any]) -> None:
    record = obj(root.get("continuity_current_decision_resolver"), "continuity_current_decision_resolver")
    historical(record, issue=263, pr=264, head="6dcbad3926db99e9621622acfcfc1b2db7da9d21", merge=RESOLVER_MERGE, authority="INTERNAL_EVIDENCE_ONLY")
    for field in ("concrete_live_owner_adapters_selected", "persistence_present", "runtime_wired", "operator_go"):
        literal(record, field, False)


def lifecycle(root: dict[str, Any]) -> None:
    record = obj(root.get("continuity_admission_artifact_lifecycle"), "continuity_admission_artifact_lifecycle")
    historical(record, issue=266, pr=267, head="adba2b2621458d11b3173bdb9413c81a5ef599b3", merge=LIFECYCLE_MERGE, authority="INTERNAL_STORAGE_LIFECYCLE_ONLY")
    literal(record, "storage_profile", "SQLITE_INTERNAL")
    for field in ("persistence_present", "deterministic_replay_present", "retention_cleanup_present", "erasure_addressability_present", "integrity_verification_present", "crash_safe_transactions_present"):
        literal(record, field, True)
    for field in ("concrete_live_owner_adapters_selected", "runtime_wired", "enabled", "observed", "operator_go", "producer_side_effects_present"):
        literal(record, field, False)


def composition(root: dict[str, Any]) -> None:
    record = obj(root.get("continuity_bounded_runtime_composition"), "continuity_bounded_runtime_composition")
    historical(record, issue=269, pr=270, head="7089b506e986b463929135c3d0f4a683bbe08a34", merge=WIRING_MERGE, authority="INTERNAL_RUNTIME_COMPOSITION_ONLY")
    literal(record, "composition_root", "server.py::lifespan")
    literal(record, "runtime_wired", True)
    literal(record, "user_visible_behavior", "UNCHANGED")
    literal(record, "query_behavior", "UNCHANGED")
    for field in ("enabled", "observed", "runtime_authority", "operator_go", "caller_selected_database_path", "caller_selected_owner", "caller_selected_tenant", "producer_side_effects_present", "canon_writes_present", "esm_writes_present", "truth_gate_writes_present", "goal_stack_writes_present", "reminder_created", "notification_created", "action_created", "tool_call_created"):
        literal(record, field, False)
    literal(record, "submitted_review_count", 0)
    literal(record, "codex_review_status", "NOT_RUN_USAGE_LIMIT")


def enablement(root: dict[str, Any]) -> None:
    record = obj(root.get("continuity_controlled_enablement"), "continuity_controlled_enablement")
    historical(record, issue=272, pr=273, head="c74e771d86603b0f24039446d6b405d61c32fda8", merge=ENABLEMENT_MERGE, authority="INTERNAL_CONTROLLED_ENABLEMENT_ONLY")
    literal(record, "activation_schema_version", "continuity.controlled_enablement.v1")
    literal(record, "scope", "continuity.internal.artifact_persistence_replay")
    literal(record, "composition_root", "server.py::lifespan")
    literal(record, "same_database_activation_evidence", True)
    literal(record, "enablement_mechanism_implemented", True)
    literal(record, "user_visible_behavior", "UNCHANGED")
    literal(record, "query_behavior", "UNCHANGED")
    for field in ("persisted_evidence_is_permission", "runtime_currently_enabled", "operator_authorization_present", "operator_go", "observed", "runtime_authority", "caller_selected_database_path", "caller_selected_owner", "caller_selected_tenant", "producer_side_effects_present", "canon_writes_present", "esm_writes_present", "truth_gate_writes_present", "goal_stack_writes_present", "reminder_created", "notification_created", "action_created", "tool_call_created", "scheduler_enabled"):
        literal(record, field, False)
    literal(record, "submitted_review_count", 0)
    literal(record, "codex_review_status", "NOT_RUN_USAGE_LIMIT")


def continuity_flags(record: dict[str, Any], *, wired: bool, extra: tuple[tuple[str, Any], ...] = ()) -> None:
    for field, expected in (("implemented", True), ("tested", True), ("wired", wired), ("enabled", False), ("observed", False), ("runtime_authority", False), *extra):
        literal(record, field, expected)


def validate_v1(_root: dict[str, Any], _state: dict[str, Any]) -> dict[str, str]:
    return {"audit_status": "LEGACY_OR_UNDECLARED", "notion_status": "LEGACY_OR_UNDECLARED"}


def validate_v2(root: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    if state["completed"] != 7 or state["total"] != 12 or state["verified"] != state["checkpoint"] or state["verified"] != AUDIT_MERGE:
        raise ProjectStateError("schema v2 audit checkpoint is inconsistent")
    governance(state["governance"]); record = notion(root)
    return {"audit_status": "COMPLETE", "notion_status": record["status"]}


def validate_v3(root: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    checkpoint(state, RESOLVER_MERGE, "resolver")
    if state["completed"] != 8 or state["total"] != 12: raise ProjectStateError("schema v3 Continuity readiness must be exactly 8/12")
    continuity_flags(state["continuity"], wired=False); text(state["continuity"], "next_bounded_slice")
    governance(state["governance"]); resolver(root); record = notion(root, "CONTINUITY_CURRENT_DECISION_RESOLVER", RESOLVER_MERGE)
    return {"audit_status": "COMPLETE", "notion_status": record["status"]}


def validate_v4(root: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    checkpoint(state, LIFECYCLE_MERGE, "lifecycle")
    if state["completed"] != 9 or state["total"] != 12: raise ProjectStateError("schema v4 Continuity readiness must be exactly 9/12")
    continuity_flags(state["continuity"], wired=False); governance(state["governance"]); resolver(root); lifecycle(root)
    record = notion(root, "CONTINUITY_ADMISSION_ARTIFACT_LIFECYCLE", LIFECYCLE_MERGE)
    return {"audit_status": "COMPLETE", "notion_status": record["status"]}


def validate_v5(root: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    if "continuity_controlled_enablement" in root or "enablement_mechanism_implemented" in state["continuity"]:
        raise ProjectStateError("schema v5 must remain Continuity 10/12 without controlled enablement")
    checkpoint(state, WIRING_MERGE, "runtime-wiring")
    if state["completed"] != 10 or state["total"] != 12: raise ProjectStateError("schema v5 Continuity readiness must be exactly 10/12")
    continuity_flags(state["continuity"], wired=True); governance(state["governance"]); resolver(root); lifecycle(root); composition(root)
    record = notion(root, "CONTINUITY_BOUNDED_RUNTIME_COMPOSITION", WIRING_MERGE)
    return {"audit_status": "COMPLETE", "notion_status": record["status"]}


def validate_v6(root: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    checkpoint(state, ENABLEMENT_MERGE, "controlled-enablement")
    if state["completed"] != 11 or state["total"] != 12: raise ProjectStateError("schema v6 Continuity readiness must be exactly 11/12")
    continuity_flags(state["continuity"], wired=True, extra=(("enablement_mechanism_implemented", True), ("operator_authorization_present", False), ("operator_go", False), ("user_visible_behavior_changed", False), ("side_effects_enabled", False)))
    text(state["continuity"], "next_bounded_slice"); governance(state["governance"]); resolver(root); lifecycle(root); composition(root); enablement(root)
    record = notion(root, "CONTINUITY_CONTROLLED_ENABLEMENT", ENABLEMENT_MERGE)
    return {"audit_status": "COMPLETE", "notion_status": record["status"]}


VALIDATORS: dict[int, Callable[[dict[str, Any], dict[str, Any]], dict[str, str]]] = {1: validate_v1, 2: validate_v2, 3: validate_v3, 4: validate_v4, 5: validate_v5, 6: validate_v6}


def validate_project_state(data: Any) -> dict[str, Any]:
    root = obj(data, "root")
    version = root.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ProjectStateError(f"schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}")
    state = common(root)
    report = VALIDATORS[version](root, state)
    return {"ok": True, "schema_version": version, "verified_head": state["verified"], "implementation_baseline": state["implementation"], "documentation_checkpoint": state["checkpoint"], "continuity": f"{state['completed']}/{state['total']}", "readiness_percent": state["readiness"], "audit_status": report["audit_status"], "notion_status": report["notion_status"], "kb_policy": state["kb"]["preservation_policy"]}


def load_and_validate(path: Path = PROJECT_STATE_PATH) -> dict[str, Any]:
    try:
        return validate_project_state(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectStateError(f"cannot read {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=PROJECT_STATE_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = load_and_validate(args.path)
    except ProjectStateError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2) if args.json else f"FAILED: {exc}")
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"OK: project state validated; schema=v{report['schema_version']}, Continuity={report['continuity']} ({report['readiness_percent']}%), Audit={report['audit_status']}, Notion={report['notion_status']}, KB={report['kb_policy']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
