# ADMIN-01 — Branch ruleset administrator handoff

**Date (UTC):** 2026-08-08  
**Tracking issue:** [#234](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/234)  
**Agent admin permission:** not available (GitHub API rulesets endpoint returned no configurable access)  
**Machine state:** `branch_ruleset_enforced = false` in `docs/state/project_state.json` (unchanged)

## Required ruleset (target: `main`)

| Setting | Required value |
|---|---|
| Changes | Pull request only |
| Required status check | `Titan aggregate merge evidence` (exact context name from aggregate workflow) |
| Review threads | All conversations resolved |
| Direct push | Blocked for ordinary actors |
| Force push | Blocked |
| Branch deletion | Blocked |
| Up to date | Require branch up to date before merge |
| Bypass | Named emergency maintainers only, documented |
| Administrators | Apply ruleset to administrators when organizationally acceptable |

## Required status checks (via aggregate gate)

The aggregate merge-evidence workflow must fail closed when applicable specialized workflows are failed, cancelled, timed out, missing, or stale. Document exact required contexts in `docs/operations/` after configuration.

## CODEOWNERS (if available)

Protect high-authority paths:

- Canon / memory / ESM / promotion
- TruthGate and policy
- Continuity
- migrations and erasure
- `.github/workflows/**`
- deployment/security configuration
- `docs/ai/**` governance files

## Proof to collect (administrator)

Save structured evidence:

- ruleset ID
- target branch
- required status context string(s)
- bypass list
- screenshot or GitHub API export
- proof that a draft PR waits for aggregate status
- confirmation of force-push/deletion policy

Do **not** perform destructive direct-push or force-push tests on `main`.

## Issue #234 closure criteria

Close #234 only after proof above is attached to GitHub (for example
`docs/operations/branch-protection-proof.md` or issue comment with API export).

Only then may documentation set `branch_ruleset_enforced = true`.

## Residual risk while open

CI workflows exist, but repository settings can still bypass required checks,
allow direct pushes, or merge with unresolved threads. This remains governance P0.
