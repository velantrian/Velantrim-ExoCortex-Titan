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

**Default contract:** Every PR body must declare exactly one classification:

```text
Documentation impact: NONE
Documentation impact: GITHUB_ONLY
Documentation impact: GITHUB_AND_NOTION
```

**Narrow exception (trusted Dependabot only):**

The aggregate evaluator may infer `Documentation impact: NONE` for trusted Dependabot PRs **only when**:

- Actor identity comes from GitHub API bot fields (`dependabot[bot]` with `type: Bot`)
- All changed files are in the strict dependency-only allowlist:
  - Exact root-level files: `uv.lock`, `requirements.txt`
  - Root-level `requirements-<fragment>.txt` (single filename, no `/`)
  - One level deep: `requirements/<filename>.txt` only
- No PR-body text claim can establish bot trust (API identity only)
- Mixed paths (valid + invalid in same PR) fail closed
- Empty path sets fail closed
- Workflows, actions, pyproject.toml, .github/dependabot.yml, and all governance/docs paths remain fail-closed without explicit metadata

Human authors, unknown bots, spoofed body text, and Dependabot changes to sensitive paths remain **fail-closed** without explicit metadata.

When explicit metadata is present, ordinary validation applies even for Dependabot.

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

### Stage 1 (current, designed for single-CODEOWNER topology)

An administrator must create a branch ruleset for `main` with:

| Setting | Required value | Reason |
|---|---|---|
| Pull request required | yes | Enforce code review path before merge |
| Required approvals | ≥ 1 (non-author) | At least one independent reviewer |
| Dismiss stale approvals | yes | New commits reset approval status |
| Conversation resolution | yes | All review threads resolved before merge |
| Status checks | `Titan aggregate merge evidence` | Gate is mandatory exactly as named |
| Require branch up to date | yes | Prevent stale-base merges |
| Block force pushes | yes | Prevent history rewriting |
| Block deletion | yes | Prevent branch erasure |
| Require Code Owner review | **OFF** | Not viable with single effective CODEOWNER who may author PRs (deadlock risk) |
| Direct push / update restriction | Blocked via PR-required setting; no "Restrict updates" toggle | Merging PR is allowed after all checks pass |
| Bypass | Named emergency maintainers only; no broad role bypass | Minimize exception scope |
| Apply to administrators | yes (only when non-author approval path is proven viable) | No self-approval; administrators subject to same rules |

**Stage 1 reviewer topology:**
- PR author: `cursor[bot]` / non-`@velantrian` agent (not self-authored)
- Approval: `@velantrian` (independent, non-author)
- Code Owner review: **OFF**

Do not enable "Require review from Code Owners" while `@velantrian` is the sole effective CODEOWNER and may also author pull requests.

### Stage 2 (future, requires topology expansion)

Code Owner review is **intentionally deferred** to Stage 2. Enable only after:

- A second trusted write collaborator is added as CODEOWNER and can submit counting approvals; **OR**
- Another topology that provably eliminates self-approval deadlock without a broad bypass

Stage 2 is not the current state. Do not claim current governance supports Code Owner review.

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
