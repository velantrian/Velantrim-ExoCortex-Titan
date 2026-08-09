# ADMIN-01 — Branch ruleset administrator handoff

**Date (UTC):** 2026-08-08  
**Tracking issues:** [#234](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/234) (ruleset enforcement), [#258](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/258) (Stage-1 preconditions)  
**Agent admin permission:** not available (GitHub API rulesets create returns `403`)  
**Machine state:** `branch_ruleset_enforced = false` in `docs/state/project_state.json` (unchanged)  
**Ruleset existence:** **absent until an administrator creates it manually**. This document is a contract, not proof of enforcement.

## Current CODEOWNERS topology

`.github/CODEOWNERS` is **single-owner** (`* @velantrian`).

Consequences:

- GitHub does not count self-approval toward required reviews.
- Enabling **Require review from Code Owners** while `@velantrian` is the sole effective Code Owner and may also author pull requests creates a **merge deadlock** unless a bypass is used.
- Stage-1 protection therefore relies on **non-author approval** (preferred: PR author = `cursor[bot]` / agent; independent approval = `@velantrian`).
- Code Owner review is **intentionally deferred** to Stage 2 after a real multi-reviewer topology exists.
- Do **not** invent CODEOWNERS entries for accounts/teams that are not real trusted reviewers with repository access.

## Stage 1 — enable now (recommended first Active ruleset)

**Ruleset name:** `main-governance`  
**Enforcement:** Active  
**Target:** Include default branch / `main`  
**Require review from Code Owners:** **OFF**

| Setting | Required value | Note |
|---|---|---|
| Pull request required | yes | Enforce review before merge |
| Required approvals | ≥ 1 | Must be a non-author reviewer |
| Dismiss stale approvals | yes | New commits reset approval status |
| Require conversation resolution | yes | All review threads resolved |
| Require status checks to pass | yes | Aggregate gate is mandatory |
| Required status check | `Titan aggregate merge evidence` | Exact context name from workflow |
| Require branches to be up to date before merging | yes | Prevent stale-base merges |
| Block force pushes | yes | Prevent history rewriting |
| Restrict deletions | yes | Prevent branch erasure |
| Require Code Owner review | **OFF** | Not viable with single-CODEOWNER topology (deadlock risk) |
| Restrict updates | **OFF** | Merging PR must be allowed; "Require PR" already blocks direct pushes |
| Bypass | Named emergency maintainers only; no broad role bypass | Minimize exception scope |
| Administrators | Apply ruleset to administrators when a non-author approval path exists | No self-approval |

**Stage 1 reviewer topology:**

```text
PR author:      cursor[bot] / non-@velantrian agent
Approval:       @velantrian (independent, satisfies required approvals ≥ 1)
Code Owners:    OFF (intentionally)
Self-approval:  GitHub rejects as non-counting
Deadlock risk:  Mitigated by non-author author topology
```

**Why Code Owner review is OFF in Stage 1:**

GitHub does not count self-approval toward required reviews. With `@velantrian` as the sole effective CODEOWNER (and possibly author), enabling "Require review from Code Owners" creates a merge deadlock:

- If `@velantrian` authors the PR, self-approval doesn't count.
- No other CODEOWNER exists to provide the required review.
- Bypass would be required, defeating the protection.

Code Owner review is intentionally deferred to Stage 2, when the topology is expanded.

## Stage 2 — deferred (do not enable yet)

| Setting | Status |
|---|---|
| Require review from Code Owners | **DO NOT ENABLE YET** |

Enable Stage 2 only after at least one of:

- a second real trusted write collaborator is added as CODEOWNER and can submit counting approvals; or
- another proven topology that eliminates self-approval deadlock without a broad bypass.

**Warning:** Do not enable Code Owner review while `@velantrian` is the sole effective Code Owner and may also author pull requests.

## Dependabot aggregate compatibility

The aggregate evaluator (`scripts/check_pr_merge_evidence.py`) may infer
`Documentation impact: NONE` for **trusted Dependabot** PRs only when:

- actor identity comes from GitHub API bot fields (`dependabot[bot]` / `Bot`);
- changed paths are dependency-only allowlisted paths;
- no documentation-sensitive / Notion-authoritative paths are present.

Human authors, unknown bots, spoofed body text, and Dependabot changes to sensitive paths remain **fail-closed** without explicit Documentation impact metadata.

Do **not** fix Dependabot compatibility by executing untrusted PR-head code under privileged `pull_request_target`.

## Required status checks (via aggregate gate)

The aggregate merge-evidence workflow must fail closed when applicable specialized workflows are failed, cancelled, timed out, missing, or stale.

## Proof to collect (administrator) after Stage-1 creation

Save structured evidence:

- ruleset ID
- target branch
- required approval count (≥ 1) and dismiss-stale-approvals setting
- proof that Code Owner review is **not** enabled (must be OFF)
- proof that "Restrict updates" is **not** enabled (must be OFF; "Require PR" blocks direct pushes)
- required status context string(s)
- bypass list (minimal; preferably empty)
- test evidence: a governance PR authored by `cursor[bot]` / agent, approved by `@velantrian`, merged successfully
- confirmation of force-push/deletion blocking

Do **not** perform destructive direct-push, force-push, or deletion tests on `main`. The ruleset itself will reject unauthorized changes.

## Issue #234 closure criteria

Close #234 only after:

1. Stage-1 ruleset is Active with API proof (ruleset ID recorded);
2. canary acceptance evidence is recorded;
3. governance proof PR merges through the protected path;
4. documentation sets `branch_ruleset_enforced = true`.

Until that proof exists, leave `branch_ruleset_enforced = false` and keep #234 open.

`PR #253 merged ≠ ruleset applied.` Stage-1 precondition docs (issue #258 / PR-A) also do **not** create the ruleset.

## Residual risk while ruleset is absent

CI workflows exist, but repository settings can still bypass required checks,
allow direct pushes, or merge with unresolved threads. This remains governance P0.
