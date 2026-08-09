# ADMIN-01 — Active `main-governance` ruleset record

**Initial handoff date:** 2026-08-08 UTC  
**Final configuration verified:** 2026-08-09 UTC  
**Ruleset ID:** `20601712`  
**Ruleset name:** `main-governance`  
**Enforcement:** `active`  
**Target:** default branch (`main`)  
**Bypass list:** empty  
**Governance canary:** PR #260 merged as `a733e760732ad2c4ec6496d3f8ea4c5d0383048f`

This document began as an administrator handoff because the connected agent could not
create repository rulesets. The repository owner created and adjusted the ruleset
manually. The configuration below is the accepted current state, not the superseded
Stage-1 proposal.

## Accepted solo-workflow decision

Titan is currently maintained through one repository-owner identity working with several
AI coding/review tools. GitHub does not count an author's self-approval. Requiring one
approval therefore deadlocked ordinary owner-authored PRs unless a second trusted account
or broad bypass was introduced.

Accepted decision:

- required approvals remain `0` until an explicit multi-reviewer governance change;
- no second account is required merely to manufacture approval topology;
- no broad bypass is introduced;
- no independent approval is claimed where none exists;
- aggregate success is not described as independent review;
- retrospective audit records do not backfill historical approvals.

## Verified active configuration

| Setting | Active value | Notes |
|---|---|---|
| Pull request required | ON | changes to `main` use a PR |
| Required approvals | `0` | accepted solo workflow |
| Dismiss stale approvals | OFF | no approval gate configured |
| Conversation resolution | ON | unresolved threads block merge |
| Required status | `Titan aggregate merge evidence` | exact context |
| Require branch up to date | ON | stale-base merges blocked |
| Block force pushes | ON | `non_fast_forward` rule |
| Restrict deletions | ON | `deletion` rule |
| Code Owner review | OFF | single-CODEOWNER self-review cannot count |
| Latest-push approval | OFF | no approval gate configured |
| Restrict updates | OFF | valid protected merges remain possible |
| Bypass | empty | no actor may bypass |
| Allowed merge methods | merge, squash, rebase | repository configuration |

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

This reduces accidental and automated merge risk. It does not provide independent human
approval.

## CODEOWNERS

`.github/CODEOWNERS` remains single-owner (`* @velantrian`). Code Owner review stays OFF.
It may be reconsidered only after a real multi-reviewer topology exists and the owner
explicitly adopts that governance change.

## Dependabot aggregate compatibility

The aggregate evaluator may infer `Documentation impact: NONE` only for a trusted
`dependabot[bot]` identity and strict dependency-only allowlisted paths. Workflow, action,
governance, `pyproject.toml`, `.github/dependabot.yml`, mixed or unknown paths remain
fail-closed without explicit metadata.

PR #255 changed workflow pins, so it was treated as sensitive, updated onto the current
base, validated on exact head `c5e192acd62276cfd8968436eaaebfed319b72e0` and merged as
`c9e272d5d9da76219f8e0caaf784892e80046a31`.

## Completed canary

PR #260 completed the non-destructive protected-path canary:

```text
exact head:                 b2e618e0410b89f7b889d17ed5088a561076b556
aggregate:                  SUCCESS
unresolved review threads:  0
squash merge:               a733e760732ad2c4ec6496d3f8ea4c5d0383048f
```

The canary proves the ordinary PR merge path. It does not perform destructive direct-push,
force-push or deletion attempts against `main`; those controls are observed from ruleset
configuration.

## Issue outcomes

- #234: closed with a public record that the original one-approval criterion was
  consciously superseded by the accepted solo workflow;
- #258: closed after recording the original DoD items that were superseded and after the
  canary/documentation synchronization;
- #257: requested Phase I retrospective audit performed; public audit record is
  [`docs/audits/phase-i-retrospective-audit-2026-08-09.md`](../audits/phase-i-retrospective-audit-2026-08-09.md).

Closing #257 after the audit record merge means the audit request was completed. It does
not relabel the historical PRs as independently approved.

## Non-authority statement

Repository governance grants no runtime, Canon, TruthGate, policy, identity, Continuity,
tool, action or deployment authority.
