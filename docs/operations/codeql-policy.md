# Bounded CodeQL policy

Tracking: #52

Titan evaluates CodeQL as a repository supply-chain control with explicit noise, maintenance, and authority boundaries.

## Live-state constraint

At C7 admission time the connected GitHub App could read repository contents, workflows, checks, statuses, pull requests, and actions, but GitHub's Code Scanning default-setup and analyses endpoints returned `403 Resource not accessible by integration`. That permission boundary must not be misreported as proof that default setup is disabled.

The repository workflow registry contained no CodeQL advanced workflow before C7, and no CodeQL-named workflow was observed in the inspected Actions history. Those facts prove the absence of a repository-owned advanced workflow; they do not by themselves prove the platform default-setup state.

## Candidate decision

C7 therefore uses a bounded same-repository pull-request probe before any merge:

- Python only, matching Titan's primary implementation language;
- GitHub CodeQL Action pinned to the verified v4.37.3 commit;
- `build-mode: none`, so no duplicate application build is introduced;
- default CodeQL security queries only — no `security-extended` or `security-and-quality` suite in this first admission;
- pull request, default-branch push, and one weekly scheduled analysis;
- minimal permissions: `security-events: write`; `actions`, `contents`, and `packages` read-only;
- no SARIF post-processing, no alert suppression, and no auto-dismissal.

If the exact-head pull-request analysis uploads successfully, the advanced workflow is an admissible explicit owner and may proceed through Titan's normal merge lifecycle. If GitHub rejects the upload because default setup already owns CodeQL, the workflow must not be blindly merged; C7 must instead reconcile to the platform owner proven by that failure.

## Noise boundary

The initial policy deliberately uses the default security query suite. Broader query suites can increase findings and maintenance burden and require a separate evidence-backed decision. A CodeQL alert is a security signal, not automatically a release blocker or a statement of exploitability; findings still require triage.

## Maintenance boundary

The CodeQL Action is pinned to an immutable commit for supply-chain integrity. Titan's existing GitHub Actions Dependabot owner remains responsible for surfacing action updates; maintainers must review and intentionally move the pin.

## Authority boundary

CodeQL is static-analysis evidence only. It cannot change Canon, runtime flags, Operator GO, production authority, dependency manifests, or release state. Its presence does not replace the C4 dependency vulnerability audit, C2/C5 SBOM evidence, tests, review, or merge-evidence gates.
