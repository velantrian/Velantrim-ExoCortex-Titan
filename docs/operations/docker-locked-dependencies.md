# Docker declared-dependency lock convergence

Tracking: #52

This bounded supply-chain lane makes Docker consume Titan's **declared project runtime dependencies** from the same authoritative `uv.lock` used by CI.

## Bounded contract

For the selected `RUNTIME_EXTRAS`:

1. Docker copies `pyproject.toml` and `uv.lock` into the builder stage.
2. `scripts/export_locked_runtime_requirements.py` validates every requested extra against `[project.optional-dependencies]`.
3. The helper runs `uv export --frozen --no-dev --no-emit-project` with the selected extras.
4. The exported requirements keep lock-derived hashes.
5. The builder installs them with `pip install --require-hashes`.
6. Titan is still built as a wheel and that wheel is installed with `--no-deps`, preserving the existing non-editable wheel-packaging contract without allowing pip to re-resolve project dependencies.
7. Docker uses the same uv release as `.github/actions/sync-python-deps/action.yml`.

## What this proves

For Python packages owned by Titan's declared project dependency graph, Docker resolution is derived from the checked-in `uv.lock` instead of independently resolving the version ranges from `pyproject.toml`.

## What this does NOT prove

This is intentionally **not yet full CI/Docker Python-environment equivalence**.

`pymorphy3` is currently installed only by the Dockerfile and is not represented in `uv.lock`. `core/lemmatizer_ru.py` treats it as optional and can fall back when it is absent, but changing that runtime choice is outside this bounded PR. The Dockerfile therefore labels `pymorphy3` as a separate #52 residual instead of hiding it behind a broader lock-equivalence claim.

This lane also does not prove:

- vulnerability absence;
- full container/OS package inventory;
- reproducible container bytes;
- Operator GO, runtime authority or production authority.

## Future closure requirement

The parent CI↔Docker lock-equivalence residual can close only after the Docker-only `pymorphy3` ownership decision is resolved and no other unowned runtime Python dependency bypass remains.
