# Bounded uv Dependabot policy

Tracking: #52

Titan uses Dependabot for routine dependency-update discovery, but dependency requirements remain human-owned architecture.

## Decision

The repository's existing GitHub Actions Dependabot owner remains unchanged. A second root update entry uses GitHub's native `uv` ecosystem support with:

- a weekly cadence;
- `versioning-strategy: lockfile-only`;
- one grouped `uv-lock-refresh` update line;
- `open-pull-requests-limit: 2` as a queue/noise ceiling.

`lockfile-only` is the key authority boundary: routine Dependabot version-update PRs may refresh versions already allowed by `pyproject.toml`, but a release that requires changing the manifest constraint is not admitted automatically.

## Merge-evidence boundary

Titan's aggregate merge-evidence validator already treats `uv.lock` as a narrow trusted-Dependabot dependency-only path. It does not grant the same inferred documentation status to `pyproject.toml`.

Therefore:

1. a trusted Dependabot PR that only refreshes `uv.lock` can use the existing dependency-only merge path;
2. a PR that changes `pyproject.toml` falls outside that inference and must satisfy the normal fail-closed documentation/evidence contract;
3. bot identity comes from GitHub API actor fields, never from PR body text.

This avoids expanding the bot's effective authority over Titan's dependency ownership or optional-feature boundaries.

## Noise and maintenance boundary

Routine eligible uv updates are grouped so the repository does not receive one PR per dependency. The open-PR ceiling prevents an unbounded update queue.

A grouped update is still subject to Titan's normal exact-head CI, vulnerability audit, coverage ratchet, and applicable Docker/aggregate gates. If a grouped refresh breaks compatibility, it is not merged merely because Dependabot proposed it; maintainers may close it and perform a bounded manual dependency change instead.

## Scope boundary

This policy does not:

- widen or rewrite dependency constraints in `pyproject.toml`;
- auto-merge Dependabot PRs;
- weaken CI, vulnerability, review, or merge-evidence gates;
- replace the C4 OSV audit;
- configure CodeQL;
- claim reproducible container bytes;
- enable runtime or production authority.
