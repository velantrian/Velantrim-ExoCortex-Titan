# Python dependency lock (uv)

Titan uses a single canonical lock mechanism:

- source: `pyproject.toml`
- lock: `uv.lock`
- installer: `uv` (pinned in CI composite action)

## CI profile

Full Titan CI installs the frozen graph with optional groups:

`server`, `dev`, `parsers`, `retrieval`, `embeddings`, `graph-lab` on Python 3.11.

Continuity and ARM contract workflows install the frozen `dev` profile only.

## Local install

```bash
uv lock --check
uv sync --frozen --extra server --extra dev --extra parsers --extra retrieval --extra embeddings --extra graph-lab
```

## Updating dependencies

1. Change `pyproject.toml` intentionally (no drive-by upgrades).
2. Run `uv lock`.
3. Commit both `pyproject.toml` and `uv.lock`.
4. Verify `uv lock --check` passes.
5. Run focused tests and full CI on the PR head.

CI fails closed when `pyproject.toml` and `uv.lock` drift (`uv lock --check`).

## Docker

The Dockerfile exports selected runtime dependencies from `uv.lock`, installs with
hash verification, and installs the built wheel without resolving dependencies again.
`RUNTIME_EXTRAS` selects locked extras; editable source installation is not the runtime
image contract. See the export and wheel stages in `Dockerfile`.

## Supply-chain pinning

GitHub Actions external inputs are pinned separately in workflow files; see
`.github/workflows/` and Dependabot/Renovate updates for action SHA rotation.
