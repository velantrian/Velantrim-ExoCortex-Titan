"""Pure parsing contract for connectorless Notion hand-off metadata."""

from __future__ import annotations

import re

NOTION_HANDOFF_PATH = "docs/ai/NOTION_HANDOFF.md"


def expected_handoff_path(pull_request_number: int) -> str:
    return f"{NOTION_HANDOFF_PATH}#handoff-pr-{pull_request_number}"


def has_matching_handoff_heading(text: str, pull_request_number: int) -> bool:
    heading = f"## handoff-pr-{pull_request_number}"
    return sum(line.strip() == heading for line in text.splitlines()) == 1


def full_lower_sha(value: str) -> bool:
    return re.fullmatch(r"[0-9a-f]{40}", value) is not None
