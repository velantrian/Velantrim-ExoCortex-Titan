# Main governance canary

This file is a disposable governance proof artifact for the Stage-1 `main-governance` ruleset.

It verifies that a pull request targeting `main` is subject to:

- one non-author approval;
- stale-approval dismissal;
- approval of the latest reviewable push;
- conversation resolution;
- the exact `Titan aggregate merge evidence` status check;
- branch up-to-date enforcement;
- blocked force pushes and branch deletion protection.

No runtime behavior, authority, or continuity state is changed.
