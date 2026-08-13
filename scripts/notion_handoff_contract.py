"""Pure fail-closed contract for connectorless Notion hand-off metadata."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

NOTION_HANDOFF_PATH = "docs/ai/NOTION_HANDOFF.md"
_HANDOFF_PATH_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?github\s+hand-?off\s+path\s*:\s*`?([^`\s]+)`?\s*$"
)


@dataclass(frozen=True)
class ContractResult:
    state: str
    description: str

    def __post_init__(self) -> None:
        if self.state not in {"success", "failure"}:
            raise ValueError(f"unsupported contract state: {self.state}")


def expected_handoff_path(pull_request_number: int) -> str:
    return f"{NOTION_HANDOFF_PATH}#handoff-pr-{pull_request_number}"


def connectorless_handoff_declared(body: str) -> bool:
    upper = body.upper()
    return (
        (
            "NOTION ACCESS: `UNAVAILABLE`" in upper
            or "NOTION ACCESS: UNAVAILABLE" in upper
        )
        and (
            "NOTION SYNCHRONIZATION: `HANDOFF_REQUIRED`" in upper
            or "NOTION SYNCHRONIZATION: HANDOFF_REQUIRED" in upper
        )
    )


def _handoff_section(text: str, *, pull_request_number: int) -> str | None:
    heading = f"## handoff-pr-{pull_request_number}"
    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line.strip() == heading]
    if len(matches) != 1:
        return None
    start = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def _handoff_field(section: str, label: str) -> str | None:
    pattern = re.compile(
        rf"(?im)^\s*-\s*\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$"
    )
    matches = tuple(pattern.finditer(section))
    if len(matches) != 1:
        return None
    return matches[0].group(1).strip().strip("`").strip()


def full_lower_sha(value: str) -> bool:
    return re.fullmatch(r"[0-9a-f]{40}", value) is not None


def evaluate_structured_handoff(
    body: str,
    handoff_text: str,
    *,
    changed_paths: Iterable[str],
    pull_request_number: int,
    base_sha: str,
) -> ContractResult:
    path_matches = tuple(_HANDOFF_PATH_RE.finditer(body))
    if len(path_matches) != 1:
        return ContractResult(
            "failure",
            "HANDOFF_REQUIRED requires exactly one GitHub hand-off path",
        )

    expected_path = expected_handoff_path(pull_request_number)
    if path_matches[0].group(1) != expected_path:
        return ContractResult(
            "failure",
            f"GitHub hand-off path must be {expected_path}",
        )

    if NOTION_HANDOFF_PATH not in set(changed_paths):
        return ContractResult(
            "failure",
            "HANDOFF_REQUIRED requires docs/ai/NOTION_HANDOFF.md in the PR diff",
        )

    section = _handoff_section(
        handoff_text,
        pull_request_number=pull_request_number,
    )
    if section is None:
        return ContractResult(
            "failure",
            f"structured hand-off item handoff-pr-{pull_request_number} is missing",
        )

    if _handoff_field(section, "Status") != "HANDOFF_REQUIRED":
        return ContractResult(
            "failure",
            "structured hand-off Status must be HANDOFF_REQUIRED",
        )

    if _handoff_field(section, "Documentation impact") != "GITHUB_AND_NOTION":
        return ContractResult(
            "failure",
            "structured hand-off Documentation impact must be GITHUB_AND_NOTION",
        )

    repository_pr = _handoff_field(section, "Repository / PR / issue")
    if (
        repository_pr is None
        or re.search(rf"PR\s+#{pull_request_number}(?!\d)", repository_pr) is None
    ):
        return ContractResult(
            "failure",
            "structured hand-off must reference the current PR",
        )

    if _handoff_field(section, "Base SHA") != base_sha:
        return ContractResult(
            "failure",
            "structured hand-off Base SHA must match the current PR base",
        )

    item_head_sha = _handoff_field(section, "Head SHA")
    if item_head_sha is None or not full_lower_sha(item_head_sha):
        return ContractResult(
            "failure",
            "structured hand-off Head SHA must be a full lowercase commit SHA",
        )

    notion_record = _handoff_field(section, "Intended Notion record")
    if (
        notion_record is None
        or not notion_record
        or notion_record.lower() in {"safe title or internal reference", "tbd"}
    ):
        return ContractResult(
            "failure",
            "structured hand-off must name the intended Notion record",
        )

    if _handoff_field(section, "Notion access for originating actor") != "UNAVAILABLE":
        return ContractResult(
            "failure",
            "structured hand-off originating Notion access must be UNAVAILABLE",
        )

    required_sections = (
        "### Problem / opportunity",
        "### Material findings",
        "### Decision and rationale",
        "### Authority, safety, privacy, and Canon boundaries",
        "### Evidence",
        "### Next actions",
        "### Synchronization result",
    )
    missing_sections = [name for name in required_sections if name not in section]
    if missing_sections:
        return ContractResult(
            "failure",
            f"structured hand-off is missing section: {missing_sections[0][4:]}",
        )

    return ContractResult(
        "success",
        f"structured Notion hand-off handoff-pr-{pull_request_number} is bound to current PR/base",
    )
