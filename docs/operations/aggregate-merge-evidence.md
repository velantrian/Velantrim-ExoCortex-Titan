# 🔒 Aggregate Merge Evidence

**Status:** implemented in repository workflow; repository ruleset activation remains an administrator action.  
**Required commit-status context:** `Titan aggregate merge evidence`

## Purpose

Titan has multiple GitHub Actions workflows with path filters. A missing check can otherwise be confused with a passing check, and a cancelled or runner-starved workflow can be merged when `main` is not protected.

The aggregate gate writes one status directly to the exact pull-request head SHA. Repository rules should require this single context.

## Trusted execution model

`.github/workflows/merge-evidence-gate.yml` runs only the evaluator stored on the default branch. It is triggered by:

- pull-request metadata and head changes through `pull_request_target`;
- completion of the primary CI, Continuity, Docker or ARM-03 workflows;
- every push to `main`, which re-evaluates all open PRs for stale-base status.

The workflow never checks out or executes code from an untrusted PR branch. It reads PR metadata, changed filenames and exact-head workflow runs through the GitHub API.

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

A newer rerun of the same workflow replaces an older attempt only when its `run_number` and `run_attempt` are newer.

## Documentation synchronization enforcement

Every PR body must declare exactly one classification:

```text
Documentation impact: NONE
Documentation impact: GITHUB_ONLY
Documentation impact: GITHUB_AND_NOTION
```

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

Draft PRs receive a pending aggregate status and therefore cannot satisfy the future required status context.

## Stale-base handling

The evaluator compares the PR base SHA and head SHA. A branch that is behind its base receives failure. A push to `main` re-evaluates all open PRs, preventing an old green head from remaining accepted after the base advances.

## Required repository settings

An administrator must create a branch ruleset for `main` with:

- require pull request before merge;
- require at least one approval;
- dismiss stale approvals;
- require conversation resolution;
- require branch to be up to date;
- require status check `Titan aggregate merge evidence`;
- block force pushes;
- block branch deletion;
- restrict direct pushes and bypass actors;
- require CODEOWNERS review for owned paths.

The workflow and CODEOWNERS file do not activate these repository settings by themselves.

## Failure recovery

1. Inspect the aggregate status description and linked workflow run.
2. Fix or rerun the named missing/failed workflow on the same head.
3. Do not create an empty commit merely to replace cancelled evidence.
4. For runner-acquisition failures, rerun the failed job; the newest successful attempt becomes the accepted evidence.
5. If a workflow is classified applicable but does not start, correct the path filters rather than weakening the aggregate classifier.

## Test coverage

`tests/test_merge_evidence_gate.py` covers:

- docs-only applicability;
- Continuity and Docker coupling;
- ARM-03 and Docker coupling;
- missing workflow pending state;
- cancelled workflow fail-closed state;
- newer rerun selection;
- mandatory documentation-impact declaration;
- both valid Notion synchronization paths.

## Non-authority statement

This gate controls repository merge evidence only. It grants no runtime, Canon, TruthGate, policy, identity, Continuity, tool, action or deployment authority.
