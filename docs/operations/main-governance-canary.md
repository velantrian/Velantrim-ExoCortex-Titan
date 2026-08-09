# Main governance canary — final record

This document records the completed non-destructive canary for the active
`main-governance` ruleset. It separates settings observed through the GitHub Rulesets API
from behavior exercised by pull request #260.

## Observed ruleset configuration

Observed on 2026-08-09 through the GitHub API:

- ruleset ID: `20601712`;
- name: `main-governance`;
- enforcement: `active`;
- target: default branch (`main`);
- bypass list: empty;
- pull request required;
- required approvals: `0` for the accepted solo workflow;
- stale-approval dismissal: OFF;
- Code Owner review: OFF;
- latest-reviewable-push approval: OFF;
- conversation resolution: required;
- exact required status: `Titan aggregate merge evidence`;
- branch must be up to date before merge;
- force pushes blocked (`non_fast_forward` rule);
- deletions restricted (`deletion` rule);
- update restriction: OFF / no update-restriction rule.

## Completed canary

```text
Pull request:               #260
Exact tested head:          b2e618e0410b89f7b889d17ed5088a561076b556
Aggregate status:           SUCCESS
Unresolved review threads:  0
Squash merge:               a733e760732ad2c4ec6496d3f8ea4c5d0383048f
Documentation impact:       GITHUB_AND_NOTION
```

The successful merge demonstrates the ordinary non-destructive protected path:

```text
pull request
→ exact-head aggregate evidence
→ up-to-date branch
→ resolved conversations
→ protected squash merge
```

PR #260 did not provide or claim independent approval. Aggregate success is not a
substitute for independent review.

## Evidence boundary

The canary did not perform destructive direct-push, force-push or branch-deletion tests
against `main`. Those protections are recorded as observed ruleset configuration, not as
destructive canary observations. Approval dismissal and latest-push approval were not
exercised because both controls are intentionally OFF in solo mode.

## Follow-up completed

- issue #234 received the explicit solo-mode variance record and remains closed;
- issue #258 received the superseded-DoD record and closed;
- Dependabot PR #255 was validated separately and merged as
  `c9e272d5d9da76219f8e0caaf784892e80046a31`;
- issue #257's retrospective Phase I audit was performed and recorded in
  [`docs/audits/phase-i-retrospective-audit-2026-08-09.md`](../audits/phase-i-retrospective-audit-2026-08-09.md).

The retrospective audit does not backfill approvals for historical PRs.

## Non-authority statement

Repository governance changes no runtime behavior, Canon, TruthGate, policy, identity,
Continuity, tool, action or deployment authority.
