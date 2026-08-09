# Main governance canary

This document records the non-destructive canary for the active `main-governance`
ruleset. It separates settings observed through the GitHub Rulesets API from behavior
actually exercised by pull request #260.

## Observed ruleset configuration

Observed on 2026-08-09 through the GitHub API:

- ruleset ID: `20601712`;
- name: `main-governance`;
- enforcement: `active`;
- target: default branch (`~DEFAULT_BRANCH`, currently `main`);
- bypass list: empty;
- pull request required before merge;
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

## What PR #260 exercises

A successful squash merge of PR #260 on its exact head, after the aggregate status is
`SUCCESS` and all review conversations are resolved, demonstrates the ordinary
non-destructive protected path:

```text
pull request
→ exact-head aggregate evidence
→ up-to-date branch
→ resolved conversations
→ protected merge
```

PR #260 does not claim to provide an independent approval. Aggregate success is not a
substitute for independent review.

## Evidence boundary

This canary does not perform destructive direct-push, force-push, or branch-deletion
tests against `main`. Those protections are recorded as observed ruleset configuration,
not as destructive canary observations. Approval dismissal and latest-push approval are
also not exercised because both settings are intentionally OFF in solo mode.

No runtime behavior, authority, or Continuity state is changed.
