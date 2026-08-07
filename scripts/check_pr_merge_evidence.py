"""Fail-closed aggregate merge evidence for Titan pull requests.

The workflow using this module runs only trusted code from the default branch.
It inspects the pull-request diff and exact-head workflow runs through the
GitHub API, then writes one commit status that repository rules can require.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import fnmatch
import json
import os
import re
import sys
import time
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

STATUS_CONTEXT = "Titan aggregate merge evidence"
API_VERSION = "2022-11-28"

CI_WORKFLOW = "CI — Velantrim Titan 9.0"
CONTINUITY_WORKFLOW = "Continuity contracts"
DOCKER_WORKFLOW = "Docker — build and runtime hardening checks"
ARM03_WORKFLOW = "ARM-03 selective-memory contracts"

CONTINUITY_PATHS = (
    "core/continuity/**",
    "core/compute_controller.py",
    "tests/test_continuity*.py",
    "tests/fixtures/continuity_contracts_v1.json",
    ".github/workflows/continuity-contracts.yml",
)

ARM03_PATHS = (
    "core/selective_memory_candidates.py",
    "core/feature_config.py",
    "core/runtime_flags.py",
    "tests/test_selective_memory_candidates.py",
    "tests/test_selective_memory_speed_contract.py",
    "tests/fixtures/evaluation_replay/selective_memory_candidates.json",
    "benchmarks/bench_selective_memory_candidates.py",
    "docs/SELECTIVE_MEMORY_SPEED_AND_SAFETY.md",
    ".github/workflows/arm03-contracts.yml",
)

DOCKER_PATHS = (
    "Dockerfile",
    ".dockerignore",
    "pyproject.toml",
    "server.py",
    "server_patch/**",
    "scripts/apply_migrations.py",
    "migrations/**",
    "static/**",
    "app/**",
    "localmind/**",
    "core/**",
    "api/**",
    "docs/CONSOLE_BROWSER_TEST.ru.md",
    "docs/RESEARCH_MODE.ru.md",
    "docs/EITI_PWA_RESEARCH_ROADMAP.ru.md",
    "docs/seed/umwelt_mvp_seed.json",
    "utils/**",
    "config/profiles/**",
    "config/exocortex-dev.env",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    ".env.prod.example",
    "scripts/validate_production_profile.py",
    "tests/test_production_profile.py",
    "docs/operations/hardened-production-profile.md",
    ".github/workflows/docker.yml",
)

_DOCUMENTATION_IMPACT_RE = re.compile(
    r"documentation\s+impact\s*:\s*`?(NONE|GITHUB_ONLY|GITHUB_AND_NOTION)`?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Evaluation:
    state: str
    description: str

    def __post_init__(self) -> None:
        if self.state not in {"pending", "success", "failure"}:
            raise ValueError(f"unsupported evaluation state: {self.state}")


class GitHubApi:
    def __init__(self, *, token: str, repository: str, api_url: str) -> None:
        self._token = token
        self._repository = repository
        self._api_url = api_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, object] | None = None,
    ) -> Any:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self._api_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "velantrim-titan-aggregate-merge-evidence",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API {method} {path} failed: {exc.code} {body}"
            ) from exc
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, payload: dict[str, object]) -> Any:
        return self._request("POST", path, payload=payload)

    def paginated(self, path: str, key: str | None = None) -> list[dict[str, Any]]:
        separator = "&" if "?" in path else "?"
        page = 1
        values: list[dict[str, Any]] = []
        while True:
            response = self.get(f"{path}{separator}per_page=100&page={page}")
            page_values = response[key] if key is not None else response
            if not isinstance(page_values, list):
                raise RuntimeError(f"expected a list from GitHub API path: {path}")
            values.extend(item for item in page_values if isinstance(item, dict))
            if len(page_values) < 100:
                return values
            page += 1

    def pull_request(self, number: int) -> dict[str, Any]:
        result = self.get(f"/repos/{self._repository}/pulls/{number}")
        if not isinstance(result, dict):
            raise RuntimeError("pull request response must be an object")
        return result

    def pull_request_files(self, number: int) -> tuple[str, ...]:
        values = self.paginated(f"/repos/{self._repository}/pulls/{number}/files")
        return tuple(
            sorted(
                str(value["filename"])
                for value in values
                if isinstance(value.get("filename"), str)
            )
        )

    def workflow_runs(self, head_sha: str) -> list[dict[str, Any]]:
        encoded_sha = quote(head_sha, safe="")
        return self.paginated(
            f"/repos/{self._repository}/actions/runs"
            f"?head_sha={encoded_sha}&event=pull_request",
            key="workflow_runs",
        )

    def compare(self, base_sha: str, head_sha: str) -> dict[str, Any]:
        result = self.get(
            f"/repos/{self._repository}/compare/"
            f"{quote(base_sha, safe='')}...{quote(head_sha, safe='')}"
        )
        if not isinstance(result, dict):
            raise RuntimeError("compare response must be an object")
        return result

    def open_pull_requests(self) -> list[dict[str, Any]]:
        return self.paginated(
            f"/repos/{self._repository}/pulls?state=open&sort=updated&direction=desc"
        )

    def set_status(
        self,
        *,
        sha: str,
        state: str,
        description: str,
        target_url: str,
    ) -> None:
        self.post(
            f"/repos/{self._repository}/statuses/{quote(sha, safe='')}",
            {
                "state": state,
                "context": STATUS_CONTEXT,
                "description": description[:140],
                "target_url": target_url,
            },
        )


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def classify_required_workflows(filenames: Iterable[str]) -> dict[str, bool]:
    paths = tuple(filenames)
    return {
        CI_WORKFLOW: True,
        CONTINUITY_WORKFLOW: any(
            _matches(path, CONTINUITY_PATHS) for path in paths
        ),
        DOCKER_WORKFLOW: any(_matches(path, DOCKER_PATHS) for path in paths),
        ARM03_WORKFLOW: any(_matches(path, ARM03_PATHS) for path in paths),
    }


def evaluate_documentation_metadata(body: str) -> Evaluation:
    match = _DOCUMENTATION_IMPACT_RE.search(body)
    if match is None:
        return Evaluation(
            "failure",
            "PR body must declare Documentation impact: NONE, GITHUB_ONLY, or GITHUB_AND_NOTION",
        )
    impact = match.group(1).upper()
    if impact != "GITHUB_AND_NOTION":
        return Evaluation("success", f"documentation impact is {impact}")

    upper = body.upper()
    available_synced = (
        "NOTION ACCESS: `AVAILABLE`" in upper
        or "NOTION ACCESS: AVAILABLE" in upper
    ) and (
        "NOTION SYNCHRONIZATION: `SYNCED`" in upper
        or "NOTION SYNCHRONIZATION: SYNCED" in upper
    )
    unavailable_handoff = (
        "NOTION ACCESS: `UNAVAILABLE`" in upper
        or "NOTION ACCESS: UNAVAILABLE" in upper
    ) and (
        "NOTION SYNCHRONIZATION: `HANDOFF_REQUIRED`" in upper
        or "NOTION SYNCHRONIZATION: HANDOFF_REQUIRED" in upper
    ) and (
        "GITHUB HAND-OFF PATH:" in upper
        or "GITHUB HANDOFF PATH:" in upper
    )
    if available_synced or unavailable_handoff:
        return Evaluation("success", "documentation synchronization evidence is complete")
    return Evaluation(
        "failure",
        "GITHUB_AND_NOTION requires SYNCED or UNAVAILABLE + HANDOFF_REQUIRED + hand-off path",
    )


def _latest_run(
    runs: Iterable[dict[str, Any]], workflow_name: str
) -> dict[str, Any] | None:
    candidates = [run for run in runs if run.get("name") == workflow_name]
    if not candidates:
        return None

    def key(run: dict[str, Any]) -> tuple[int, int, str, int]:
        return (
            int(run.get("run_number") or 0),
            int(run.get("run_attempt") or 0),
            str(run.get("created_at") or ""),
            int(run.get("id") or 0),
        )

    return max(candidates, key=key)


def evaluate_required_runs(
    required: dict[str, bool], runs: Iterable[dict[str, Any]]
) -> Evaluation:
    run_values = tuple(runs)
    pending: list[str] = []
    failed: list[str] = []
    for workflow_name, applicable in required.items():
        if not applicable:
            continue
        run = _latest_run(run_values, workflow_name)
        if run is None:
            pending.append(f"{workflow_name}: missing")
            continue
        status = str(run.get("status") or "")
        conclusion = run.get("conclusion")
        if status != "completed":
            pending.append(f"{workflow_name}: {status or 'pending'}")
            continue
        if conclusion != "success":
            failed.append(f"{workflow_name}: {conclusion or 'unknown'}")

    if failed:
        return Evaluation("failure", "; ".join(failed))
    if pending:
        return Evaluation("pending", "; ".join(pending))
    return Evaluation("success", "all applicable exact-head workflows passed")


def evaluate_pull_request_once(
    api: GitHubApi, *, pull_request: dict[str, Any]
) -> tuple[str, Evaluation]:
    number = int(pull_request["number"])
    head = pull_request.get("head")
    base = pull_request.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise RuntimeError("pull request head/base metadata is missing")
    head_sha = str(head.get("sha") or "")
    base_sha = str(base.get("sha") or "")
    if not head_sha or not base_sha:
        raise RuntimeError("pull request head/base SHA is missing")

    if bool(pull_request.get("draft")):
        return head_sha, Evaluation("pending", "pull request is Draft")

    metadata = evaluate_documentation_metadata(str(pull_request.get("body") or ""))
    if metadata.state == "failure":
        return head_sha, metadata

    comparison = api.compare(base_sha, head_sha)
    if int(comparison.get("behind_by") or 0) > 0:
        return head_sha, Evaluation("failure", "pull request branch is behind base")

    filenames = api.pull_request_files(number)
    required = classify_required_workflows(filenames)
    runs = api.workflow_runs(head_sha)
    return head_sha, evaluate_required_runs(required, runs)


def _target_url() -> str:
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    repository = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not run_id:
        return f"{server}/{repository}/actions"
    return f"{server}/{repository}/actions/runs/{run_id}"


def _api_from_environment() -> GitHubApi:
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is required")
    return GitHubApi(token=token, repository=repository, api_url=api_url)


def aggregate_one(
    api: GitHubApi,
    *,
    pull_request_number: int,
    timeout_seconds: int,
    poll_seconds: int,
) -> int:
    target_url = _target_url()
    deadline = time.monotonic() + timeout_seconds
    last_description = ""
    while True:
        pull_request = api.pull_request(pull_request_number)
        head_sha, evaluation = evaluate_pull_request_once(
            api, pull_request=pull_request
        )
        if evaluation.description != last_description:
            print(f"{evaluation.state}: {evaluation.description}")
            last_description = evaluation.description
        api.set_status(
            sha=head_sha,
            state=evaluation.state,
            description=evaluation.description,
            target_url=target_url,
        )
        if evaluation.state == "success":
            return 0
        if evaluation.state == "failure":
            return 1
        if bool(pull_request.get("draft")):
            return 0
        if time.monotonic() >= deadline:
            api.set_status(
                sha=head_sha,
                state="failure",
                description=f"timed out: {evaluation.description}",
                target_url=target_url,
            )
            return 1
        time.sleep(poll_seconds)


def refresh_all_open(api: GitHubApi) -> int:
    target_url = _target_url()
    for pull_request in api.open_pull_requests():
        head_sha, evaluation = evaluate_pull_request_once(
            api, pull_request=pull_request
        )
        api.set_status(
            sha=head_sha,
            state=evaluation.state,
            description=evaluation.description,
            target_url=target_url,
        )
        print(
            f"PR #{pull_request['number']} {head_sha[:12]}: "
            f"{evaluation.state} — {evaluation.description}"
        )
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--all-open", action="store_true")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=int(os.environ.get("MERGE_EVIDENCE_TIMEOUT_SECONDS", "1200")),
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=int(os.environ.get("MERGE_EVIDENCE_POLL_SECONDS", "15")),
    )
    args = parser.parse_args(argv)
    if args.all_open == (args.pull_request is not None):
        parser.error("choose exactly one of --pull-request or --all-open")
    if args.timeout_seconds < 1 or args.poll_seconds < 1:
        parser.error("timeouts must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    api = _api_from_environment()
    if args.all_open:
        return refresh_all_open(api)
    return aggregate_one(
        api,
        pull_request_number=args.pull_request,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
    )


if __name__ == "__main__":
    raise SystemExit(main())
