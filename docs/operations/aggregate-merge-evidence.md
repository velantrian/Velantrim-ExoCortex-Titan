# 🔒 Aggregate Merge Evidence

**Status:** implemented and required by active ruleset `main-governance`  
**Ruleset ID:** `20601712`  
**Required commit-status context:** `Titan aggregate merge evidence`

## Purpose

Titan has several path-filtered GitHub Actions workflows. A missing, cancelled or stale
check must not be confused with a passing check. The aggregate gate writes one fail-closed
status to the exact pull-request head SHA, and the repository ruleset requires that exact
context with an up-to-date branch.

## Trusted execution model

`.github/workflows/merge-evidence-gate.yml` executes the evaluator from the trusted default
branch. It is triggered by PR metadata/head changes, completion of primary workflows and
pushes to `main` that may make open PR bases stale.

It does not check out or execute untrusted PR-head code under `pull_request_target`.

## Required workflow classification

`CI — Velantrim Titan 9.0` is always required.

| Workflow | Applicability |
|---|---|
| `Continuity contracts` | Continuity package, compute-controller contract, Continuity tests/fixtures or its workflow |
| `Docker — build and runtime hardening checks` | Docker/runtime watched paths including core, API, server, migrations and deployment assets |
| `ARM-03 selective-memory contracts` | ARM-03 implementation, flags, tests, benchmark, replay fixture, safety doc or workflow |

A required workflow must exist for the exact head, complete and conclude `success`.

```text
missing / queued / running → pending
cancelled / failure / timed_out / skipped / neutral → failure
success → accepted
```

A newer rerun replaces an older attempt only when its run number/attempt is newer.

## Documentation synchronization contract

Every ordinary PR must declare exactly one:

```text
Documentation impact: NONE
Documentation impact: GITHUB_ONLY
Documentation impact: GITHUB_AND_NOTION
```

For `GITHUB_AND_NOTION`, accepted connected state is:

```text
Notion access: AVAILABLE
Notion synchronization: SYNCED
```

The unavailable path requires:

```text
Notion access: UNAVAILABLE
Notion synchronization: HANDOFF_REQUIRED
GitHub hand-off path: docs/ai/NOTION_HANDOFF.md#<anchor>
```

A narrow trusted-Dependabot exception may infer `NONE` only when GitHub API identity is
`dependabot[bot]` / `Bot` and every changed path is in the strict dependency-only
allowlist. Workflow, action, governance, docs, `pyproject.toml`, `.github/dependabot.yml`,
mixed, spoofed or unknown paths remain fail-closed without explicit metadata.

Draft PRs receive pending aggregate status and cannot satisfy the required context.

## Stale-base handling

The evaluator compares the PR base/head state. A branch behind `main` receives failure. A
push to `main` re-evaluates open PRs so an old green head cannot remain accepted after the
base advances.

## Active ruleset

| Setting | Active value |
|---|---|
| Pull request required | ON |
| Required approvals | `0` |
| Dismiss stale approvals | OFF |
| Conversation resolution | ON |
| Required status | `Titan aggregate merge evidence` |
| Branch up to date | ON |
| Force pushes | blocked |
| Deletions | restricted |
| Code Owner review | OFF |
| Latest-push approval | OFF |
| Restrict updates | OFF |
| Bypass | empty |

The earlier non-author-approval proposal is superseded by the accepted solo workflow.

## Evidence boundary

Aggregate status is automated merge evidence. It is not an independent review and does
not prove that another human/account approved the change.

The absence of submitted reviews on historical Phase I PRs is preserved. Issue #257's
requested retrospective audit was completed and recorded in
[`docs/audits/phase-i-retrospective-audit-2026-08-09.md`](../audits/phase-i-retrospective-audit-2026-08-09.md).
That audit does not backfill approvals.

## Completed protected-path evidence

PR #260:

```text
exact head:                 b2e618e0410b89f7b889d17ed5088a561076b556
aggregate:                  SUCCESS
unresolved review threads:  0
squash merge:               a733e760732ad2c4ec6496d3f8ea4c5d0383048f
```

Dependabot PR #255 was processed separately because it changed workflow pins:

```text
exact head:                 c5e192acd62276cfd8968436eaaebfed319b72e0
CI / Continuity / Docker / ARM-03: SUCCESS
aggregate:                  SUCCESS
squash merge:               c9e272d5d9da76219f8e0caaf784892e80046a31
```

## Failure recovery

1. Inspect the aggregate status description and linked run.
2. Fix or rerun the named workflow on the same head.
3. Do not weaken path classification to hide a missing check.
4. For runner-acquisition failure, rerun the failed job; newest successful evidence wins.
5. If an applicable workflow does not start, correct its path filters.

## Test coverage

`tests/test_merge_evidence_gate.py` covers docs-only applicability, Continuity/Docker and
ARM coupling, missing/cancelled workflows, newer rerun selection, documentation metadata,
Notion synchronization paths and trusted-Dependabot fail-closed inference.

## Non-authority statement

This gate controls repository merge evidence only. It grants no runtime, Canon, TruthGate,
policy, identity, Continuity, tool, action or deployment authority.
