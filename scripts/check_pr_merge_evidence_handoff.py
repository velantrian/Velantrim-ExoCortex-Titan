"""Thin trusted adapter that adds strict Notion hand-off validation to the aggregate gate."""

from __future__ import annotations

import base64
import binascii
from typing import Any
from urllib.parse import quote

from scripts import check_pr_merge_evidence as gate
from scripts import notion_handoff_contract as handoff_contract

_BASE_EVALUATE = gate.evaluate_pull_request_once


def _handoff_text_at_head(api: gate.GitHubApi, head_sha: str) -> str:
    path = handoff_contract.NOTION_HANDOFF_PATH
    repository = api._repository
    result = api.get(
        f"/repos/{repository}/contents/{quote(path, safe='/')}?ref={quote(head_sha, safe='')}"
    )
    if not isinstance(result, dict) or result.get("type") != "file":
        raise RuntimeError("hand-off path is not a repository file")
    if result.get("encoding") != "base64" or not isinstance(result.get("content"), str):
        raise RuntimeError("hand-off file content is unavailable")
    try:
        raw = base64.b64decode("".join(result["content"].split()), validate=True)
        return raw.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("hand-off file is not valid UTF-8") from exc


def evaluate_pull_request_once(
    api: gate.GitHubApi, *, pull_request: dict[str, Any]
) -> tuple[str, gate.Evaluation]:
    head_sha, evaluation = _BASE_EVALUATE(api, pull_request=pull_request)
    if bool(pull_request.get("draft")) or evaluation.state == "failure":
        return head_sha, evaluation

    body = str(pull_request.get("body") or "")
    if not handoff_contract.connectorless_handoff_declared(body):
        return head_sha, evaluation

    number = int(pull_request["number"])
    base = pull_request.get("base")
    base_sha = str(base.get("sha") or "") if isinstance(base, dict) else ""
    if not base_sha:
        return head_sha, gate.Evaluation("failure", "pull request base SHA is missing")

    changed_paths = api.pull_request_files(number)
    try:
        handoff_text = _handoff_text_at_head(api, head_sha)
    except RuntimeError:
        return head_sha, gate.Evaluation(
            "failure",
            "structured Notion hand-off artifact is missing or unreadable at exact PR head",
        )

    contract = handoff_contract.evaluate_structured_handoff(
        body,
        handoff_text,
        changed_paths=changed_paths,
        pull_request_number=number,
        base_sha=base_sha,
    )
    if contract.state == "failure":
        return head_sha, gate.Evaluation("failure", contract.description)
    return head_sha, evaluation


def main(argv: list[str] | None = None) -> int:
    gate.evaluate_pull_request_once = evaluate_pull_request_once
    return gate.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
