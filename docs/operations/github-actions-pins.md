# GitHub Actions supply-chain pinning

Third-party workflow actions are pinned to full upstream commit SHAs with a
readable version comment (`# vX`).

## Pinned actions (2026-08-08)

| Action | SHA | Tag comment |
|---|---|---|
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | v4 |
| `actions/setup-python` | `a26af69be951a213d495a4c3e4e4022e16d87065` | v5 |
| `actions/cache` | `0057852bfaa89a56745cba8c7296529d2fc39830` | v4 |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | v4 |
| `astral-sh/setup-uv` | `d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86` | v5 |
| `JamesIves/github-pages-deploy-action` | `d92aa235d04922e8f08b40ce78cc5442fcfbfa2f` | v4 |

Repository-local composite actions under `.github/actions/**` are referenced by
path and are not pinned separately.

## Update procedure

1. Identify the official upstream release tag to adopt.
2. Resolve the tag to its commit SHA (`git rev-parse tags/<tag>^{commit}` on the
   upstream repository).
3. Update every workflow reference and keep the `# vX` comment accurate.
4. Verify workflow syntax and run CI on an exact-head PR.
5. Prefer weekly Dependabot grouped PRs for routine action SHA refreshes.

## Permissions review

When changing action pins, re-check workflow `permissions:` blocks. The aggregate
merge-evidence evaluator checks out trusted default-branch code only
(`persist-credentials: false`).
