# Docker Python dependency lock convergence

Tracking: #52

Titan's Docker runtime consumes its Python dependency graph from the same authoritative `uv.lock` used by CI.

## Contract

For the selected `RUNTIME_EXTRAS`:

1. Docker copies `pyproject.toml` and `uv.lock` into the builder stage.
2. `scripts/export_locked_runtime_requirements.py` validates every requested extra against `[project.optional-dependencies]`.
3. The helper runs `uv export --frozen --no-dev --no-emit-project` with the selected extras.
4. The exported requirements keep lock-derived hashes.
5. The builder installs them with `pip install --require-hashes`.
6. Titan is still built as a wheel and that wheel is installed with `--no-deps`, preserving the non-editable wheel-packaging contract without allowing pip to re-resolve project dependencies.
7. Docker uses the same uv release as `.github/actions/sync-python-deps/action.yml`.
8. `pip check` verifies the resulting runtime dependency graph before the virtualenv is copied into the runtime stage.

## Multilingual runtime ownership

`server.py` enables the Multilingual Router by default. Its primary Russian morphology implementation uses `pymorphy3`, so `pymorphy3>=2.0.6,<3` is owned by the existing `server` optional-dependency group and resolved through `uv.lock`.

The previous Docker-only `pip install pymorphy3` override has been removed. The default Docker build still performs an explicit `MorphAnalyzer(lang="ru")` smoke check, but the package now arrives only through the frozen lock-derived requirements path.

The lock currently resolves the morphology graph to:

- `pymorphy3==2.0.6`;
- `dawg2-python==0.9.0`;
- `pymorphy3-dicts-ru==2.4.417150.4580142`.

## What this proves

For Python packages in Titan's selected runtime extras, Docker version resolution is derived from the checked-in `uv.lock` instead of independently resolving version ranges from `pyproject.toml` or installing a Docker-only runtime package.

Builder-only packaging tools (`pip`, `build`, `uv`) remain outside the copied runtime dependency graph and are not a runtime-equivalence bypass.

## What this does NOT prove

This does not prove:

- vulnerability absence;
- full container/OS package inventory;
- byte-for-byte reproducible container images;
- equivalence between every possible optional-extra combination and the default image;
- Operator GO, runtime authority or production authority.

The `utils/text_utils.py` legacy `pymorphy2` fallback is a separate code-path cleanup concern; Docker does not install `pymorphy2`, and this supply-chain lane does not silently turn that legacy fallback into a new dependency owner.

## Verification

Closure requires both exact-head and post-merge evidence from:

- Full CI (`uv lock --check`, frozen dependency sync, tests, coverage, deterministic lock SBOM);
- Docker no-cache build and runtime hardening checks;
- regression tests proving `pymorphy3` is in the `server` lock graph and no Docker-only runtime install remains;
- merge-evidence aggregate and documentation synchronization.
