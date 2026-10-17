# GitHub Actions supply-chain pinning

Third-party workflow actions are pinned to full upstream commit SHAs with a
readable version comment (`# vX`).

## Currently referenced third-party actions (2026-09-05)

Only actions that appear in `.github/workflows/**` or `.github/actions/**` are listed.
Where one action is intentionally referenced at more than one exact upstream SHA,
all currently observed pins are listed explicitly.

| Action | SHA | Version comment | Referenced from |
|---|---|---|---|
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7.0.1 | CI, CodeQL, Pages, Stage 9, Stage 10 |
| `actions/setup-python` | `5fda3b95a4ea91299a34e894583c3862153e4b97` | v7.0.0 | CI, Pages, Stage 9, Stage 10 |
| `actions/upload-artifact` | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | as pinned in workflow | CI evidence jobs |
| `astral-sh/setup-uv` | `ae62891fec2bb8e7d6c99fc78c9fec3a63790f8d` | v10.0.0 | `.github/actions/sync-python-deps` |
| `astral-sh/setup-uv` | `c18668ad3cf93ea998bef934396af7bb5c839dc7` | v10.2.0 | CI dependency-audit and reproducible-wheel jobs |
| `github/codeql-action/init` | `2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2` | v4.38.2 | CodeQL |
| `github/codeql-action/analyze` | `2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2` | v4.38.2 | CodeQL |
| `JamesIves/github-pages-deploy-action` | `fa24774553152dd7873cd16ebd8d959b010c5445` | v4.9.0 | Pages |

`actions/cache` is **not** listed: the frozen-uv CI path removed the previous pip cache steps.
Repository-local composite actions under `.github/actions/**` are referenced by path.

## Update procedure

1. Identify the official upstream release tag to adopt.
2. Resolve the tag to its commit SHA (`git rev-parse tags/<tag>^{commit}` on the
   upstream repository).
3. Update every workflow/composite reference and keep the version comment accurate.
4. Keep policy tests that intentionally assert exact action SHAs synchronized with the
   adopted immutable pins; do not weaken them to accept arbitrary revisions.
5. Keep this document synchronized with actions that are actually referenced.
6. Verify workflow syntax and run CI on the resulting exact PR head.
7. Prefer weekly Dependabot grouped PRs for routine action SHA refreshes.

## Permissions review

When changing action pins, re-check workflow `permissions:` blocks. The aggregate
merge-evidence evaluator checks out trusted default-branch code only
(`persist-credentials: false`).
