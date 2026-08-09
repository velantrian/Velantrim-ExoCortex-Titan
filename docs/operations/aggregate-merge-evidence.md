# 🔒 Aggregate Merge Evidence

**Status:** implemented and required by the active `main-governance` repository ruleset.  
**Ruleset ID:** `20601712`  
**Required commit-status context:** `Titan aggregate merge evidence`

## Purpose

Titan has multiple GitHub Actions workflows with path filters. A missing check can
otherwise be confused with a passing check, and a cancelled or runner-starved workflow
could be merged without one always-present fail-closed decision.

The aggregate gate writes one status directly to the exact pull-request head SHA. The
active repository ruleset requires this exact context and requires the branch to be up to
date before merge.

## Trusted execution model

`.github/workflows/merge-evidence-gate.yml` runs only the evaluator stored on the default
branch. It is triggered by:

- pull-request metadata and head changes through `pull_request_target`;
- completion of the primary CI, Continuity, Docker or ARM-03 workflows;
- every push to `main`, which re-evaluates all open PRs for stale-base status.

The workflow never checks out or executes code from an untrusted PR branch. It reads PR
metadata, changed filenames and exact-head workflow runs through the GitHub API.

## Required workflow classification

`CI — Velantrim Titan 9.0` is always required.

The following checks are conditionally required from the actual changed-file set:

| Workflow | Applicability |
|---|---|
| `Continuity contracts` | Continuity package, compute-controller contract, Continuity tests/fixtures or its workflow |
| `Docker — build and runtime hardening checks` | Any path watched by `docker.yml`, including `core/**`, API, server, migrations, deployment and runtime assets |
| `ARM-03 selective-memory contracts` | ARM-03 implementation, flags, tests, benchmark, replay fixture, safety document or its workflow |

A required workflow must exist for the exact head, be completed and conclude `success`.

```text
missing   → pending → timeout → failure
queued    → pending
running   → pending
cancelled → failure
failure   → failure
timed_out → failure
skipped   → failure
neutral   → failure
success   → accepted
```

A newer rerun of the same workflow replaces an older attempt only when its `run_number`
and `run_attempt` are newer.

## Documentation synchronization enforcement

**Default contract:** Every PR body must declare exactly one classification:

```text
Documentation impact: NONE
Documentation impact: GITHUB_ONLY
Documentation impact: GITHUB_AND_NOTION
```

**Narrow exception (trusted Dependabot only):**

The aggregate evaluator may infer `Documentation impact: NONE` for trusted Dependabot PRs
only when:

- actor identity comes from GitHub API bot fields (`dependabot[bot]` with `type: Bot`);
- all changed files are in the strict dependency-only allowlist:
  - exact root-level files: `uv.lock`, `requirements.txt`;
  - root-level `requirements-<fragment>.txt` (single filename, no `/`);
  - one level deep: `requirements/<filename>.txt` only;
- no PR-body text claim can establish bot trust;
- mixed paths and empty path sets fail closed;
- workflows, actions, `pyproject.toml`, `.github/dependabot.yml`, governance and docs paths
  remain fail-closed without explicit metadata.

Human authors, unknown bots, spoofed body text and Dependabot changes to sensitive paths
remain fail-closed without explicit metadata. When explicit metadata is present, ordinary
validation applies even for Dependabot.

For `GITHUB_AND_NOTION`, the gate accepts only:

```text
Notion access: AVAILABLE
Notion synchronization: SYNCED
```

or the explicit unavailable path:

```text
Notion access: UNAVAILABLE
Notion synchronization: HANDOFF_REQUIRED
GitHub hand-off path: docs/ai/NOTION_HANDOFF.md#<anchor>
```

Draft PRs receive a pending aggregate status and therefore cannot satisfy the required
status context.

## Stale-base handling

The evaluator compares the PR base SHA and head SHA. A branch that is behind its base
receives failure. A push to `main` re-evaluates all open PRs, preventing an old green head
from remaining accepted after the base advances.

## Active repository settings

The verified `main-governance` ruleset uses the accepted solo workflow:

| Setting | Active value | Reason |
|---|---|---|
| Pull request required | ON | Changes to `main` use the protected PR path |
| Required approvals | `0` | Avoid self-approval deadlock in the accepted solo workflow |
| Dismiss stale approvals | OFF | No approval gate is configured |
| Conversation resolution | ON | Unresolved review threads block merge |
| Status checks | `Titan aggregate merge evidence` | Exact gate is mandatory |
| Require branch up to date | ON | Prevent stale-base merges |
| Block force pushes | ON | Prevent history rewriting |
| Restrict deletions | ON | Prevent branch deletion |
| Require Code Owner review | OFF | Single-CODEOWNER topology cannot provide a counting self-review |
| Require latest-push approval | OFF | No approval gate is configured |
| Restrict updates | OFF | PR requirement protects `main` without blocking valid merges |
| Bypass | empty | No actor may bypass the ruleset |
| Allowed merge methods | merge, squash, rebase | Active ruleset configuration |

The earlier proposal requiring a non-author approval, stale-approval dismissal and latest
reviewable-push approval is superseded. Do not claim those controls are active.

## Solo-mode evidence boundary

The aggregate gate is automated merge evidence, not an independent review. A green
aggregate result proves that the configured CI/evidence contract passed for the exact
head. It does not prove that another human or independent account approved the change.

Retrospective independent-review debt for the Phase I chain remains tracked by issue
#257. Do not backfill fictional approvals.

## Failure recovery

1. Inspect the aggregate status description and linked workflow run.
2. Fix or rerun the named missing/failed workflow on the same head.
3. Do not create an empty commit merely to replace cancelled evidence.
4. For runner-acquisition failures, rerun the failed job; the newest successful attempt
   becomes the accepted evidence.
5. If a workflow is classified applicable but does not start, correct the path filters
   rather than weakening the aggregate classifier.

## Test coverage

`tests/test_merge_evidence_gate.py` covers:

- docs-only applicability;
- Continuity and Docker coupling;
- ARM-03 and Docker coupling;
- missing workflow pending state;
- cancelled workflow fail-closed state;
- newer rerun selection;
- mandatory documentation-impact declaration;
- both valid Notion synchronization paths;
- trusted Dependabot metadata inference and fail-closed path validation.

## Non-authority statement

This gate controls repository merge evidence only. It grants no runtime, Canon,
TruthGate, policy, identity, Continuity, tool, action or deployment authority.
