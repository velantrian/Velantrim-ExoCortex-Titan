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
**Require review from Code Owners:** **DO NOT ENABLE YET**

| Setting | Required value |
|---|---|
| Changes | Pull request only |
| Required approvals | ≥ 1 (must be a non-author reviewer) |
| Dismiss stale approvals | yes — dismiss previous approvals when new commits are pushed |
| Require conversation resolution | yes |
| Require status checks to pass | yes |
| Required status check | `Titan aggregate merge evidence` (exact context name) |
| Require branches to be up to date before merging | yes |
| Block force pushes | yes |
| Restrict deletions | yes |
| Restrict direct updates | yes |
| Bypass | Named emergency maintainers only, documented; no broad bypass |
| Administrators | Apply ruleset to administrators when a non-author approval path exists |

Stage-1 reviewer topology:

```text
PR author:   cursor[bot] / non-@velantrian author
Approval:    @velantrian (satisfies required approvals ≥ 1)
Code Owners: OFF
```

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
- proof that Code Owner review is **not** enabled
- required status context string(s)
- bypass list (minimal)
- canary acceptance evidence
- confirmation of force-push/deletion/direct-update policy

Do **not** perform destructive direct-push or force-push tests on `main`.

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
