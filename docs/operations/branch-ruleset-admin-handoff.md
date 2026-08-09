# ADMIN-01 — Active `main-governance` ruleset record

**Initial handoff date (UTC):** 2026-08-08  
**Active configuration verified:** 2026-08-09  
**Tracking issues:** [#234](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/234), [#258](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/258)  
**Ruleset ID:** `20601712`  
**Ruleset name:** `main-governance`  
**Enforcement:** `active`  
**Target:** default branch (`main`)  
**Bypass list:** empty

This document began as an administrator handoff because the connected agent could not
create repository rulesets. The repository owner subsequently created and adjusted the
ruleset manually. The configuration below is the verified current state, not the older
Stage-1 proposal.

## Accepted solo-workflow decision

Titan is currently maintained by one repository owner working with Cursor, Claude Code,
Codex and ChatGPT. GitHub does not count an author's self-approval. Requiring one approval
therefore created a deadlock whenever the PR author was `@velantrian`, unless a second
trusted account or broad bypass was introduced.

The accepted decision is:

- do not require a second GitHub account;
- required approvals remain `0` unless the owner explicitly changes the governance model;
- do not claim independent approval where none exists;
- do not use aggregate success as a substitute for independent review;
- keep retrospective independent audit debt visible in issue #257.

This supersedes the earlier proposed topology of `cursor[bot]` as author and
`@velantrian` as mandatory independent reviewer.

## Verified active configuration

| Setting | Active value | Notes |
|---|---|---|
| Pull request required | ON | Changes to `main` must pass through a PR |
| Required approvals | `0` | Accepted solo workflow |
| Dismiss stale approvals | OFF | No approval gate is configured |
| Require conversation resolution | ON | Unresolved review threads block merge |
| Required status checks | ON | Exact aggregate gate is mandatory |
| Required status check | `Titan aggregate merge evidence` | Exact context, GitHub Actions integration |
| Require branch up to date | ON | Strict status-check policy |
| Block force pushes | ON | `non_fast_forward` rule |
| Restrict deletions | ON | `deletion` rule |
| Require Code Owner review | OFF | Single-CODEOWNER deadlock avoided |
| Require latest-push approval | OFF | No approval gate is configured |
| Restrict updates | OFF | PR requirement protects `main` without blocking valid merges |
| Bypass | empty | `current_user_can_bypass = never` |
| Allowed merge methods | merge, squash, rebase | Repository ruleset values |

GitHub API evidence:

```text
GET /repos/velantrian/Velantrim-ExoCortex-Titan/rulesets
→ main-governance · id=20601712 · active

GET /repos/velantrian/Velantrim-ExoCortex-Titan/rulesets/20601712
→ target=~DEFAULT_BRANCH
→ required_approving_review_count=0
→ dismiss_stale_reviews_on_push=false
→ require_code_owner_review=false
→ require_last_push_approval=false
→ required_review_thread_resolution=true
→ strict_required_status_checks_policy=true
→ required status: Titan aggregate merge evidence
→ bypass_actors=[]
→ deletion + non_fast_forward rules present
→ no update-restriction rule
```

## Protection model

```text
PR required
  + exact-head aggregate SUCCESS
  + branch up to date with main
  + all review conversations resolved
  + force-push protection
  + deletion protection
  + empty bypass list
  = accepted solo-mode protected merge path
```

This model reduces accidental and automated merge risk. It does not provide independent
human approval. That limitation is explicit rather than hidden.

## Code Owner review

`.github/CODEOWNERS` remains single-owner (`* @velantrian`). Code Owner review stays OFF.
It may be reconsidered only after a real multi-reviewer topology exists and the owner
explicitly adopts that governance change. Do not invent CODEOWNERS entries or enable a
setting that recreates the self-approval deadlock.

## Dependabot aggregate compatibility

The aggregate evaluator (`scripts/check_pr_merge_evidence.py`) may infer
`Documentation impact: NONE` for trusted Dependabot PRs only when:

- actor identity comes from GitHub API bot fields (`dependabot[bot]` / `Bot`);
- changed paths are dependency-only allowlisted paths;
- no documentation-sensitive, workflow, action, governance or other protected paths are
  present.

Human authors, unknown bots, spoofed body text and mixed/sensitive Dependabot changes
remain fail-closed without explicit metadata. Do not execute untrusted PR-head code under
privileged `pull_request_target` to make Dependabot pass.

## Canary evidence and limits

PR #260 is the non-destructive protected-path canary. Merge it only when:

1. its current exact head has `Titan aggregate merge evidence` = `SUCCESS`;
2. its branch is up to date with `main`;
3. unresolved review threads = `0`;
4. the merge uses the expected exact head SHA.

The canary proves the ordinary PR merge path. It does not perform destructive direct-push,
force-push or deletion attempts against `main`; those controls are verified from ruleset
configuration.

## Issue handling

- Issue #234 may remain closed only with a public variance comment explaining that the
  original one-approval criterion was superseded by the accepted solo workflow.
- Issue #258 must not be closed silently. After PR #260 merges, record which original DoD
  items were superseded and close it only after documentation synchronization is complete.
- Issue #257 remains open until the requested retrospective independent audit is actually
  performed or explicitly deferred with written rationale.

## Non-authority statement

Repository governance changes no runtime, Canon, TruthGate, policy, identity, Continuity,
tool, action or deployment authority.
