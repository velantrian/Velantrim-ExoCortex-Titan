# Velantrim Titan 9.0 — production Dockerfile
# Build: docker build -t velantrim-titan .
# Run:   docker run -p 8000:8000 --env-file .env velantrim-titan
#
# Multi-stage build:
#   1. "builder" — compiles a wheel for this package (core/, api/, utils/)
#      and installs it (plus chosen runtime extras) into a throwaway
#      virtualenv. Any compiler toolchain needed by a dependency lives
#      ONLY in this stage.
#   2. "runtime" — copies the finished virtualenv and the small set of
#      source files that are not part of the installable package
#      (server.py, server_patch/, scripts/apply_migrations.py, migrations/,
#      static/, app/, localmind/, the 3 docs/ files the web console
#      serves, the umwelt seed, and the deployment-profile env files)
#      into a clean, non-root, compiler-free image.
#
# VELANTRIM_APP_ROOT tells api/web_console.py, core/deployment_profiles.py,
# and core/umwelt_store.py where static/, docs/, and config/ actually live
# at runtime (see core/app_paths.resolve_app_root) — needed because
# installing core/api as a non-editable wheel decouples __file__ from
# this directory.
#
# RUNTIME_EXTRAS controls which optional pyproject.toml extras are
# installed. Default is the minimal set server.py actually imports at
# startup. Pass a wider set at build time for a "full" image, e.g.:
#   docker build --build-arg RUNTIME_EXTRAS=server,parsers,retrieval,embeddings .
# "dev" (pytest/ruff/mypy) and "audio" (openai-whisper, GB-scale) are
# intentionally never part of the default and must be opted into explicitly.
#
# Supply-chain boundary (#52): both stages intentionally use the same
# immutable Docker Official Image index digest. The human-readable tag keeps
# the Python line visible, but the digest is authoritative for image content.
# Rotate this pin only as a deliberate supply-chain change and rerun the
# Docker workflow on the exact PR head.
#
# Runtime Python dependencies are resolved from the repository's uv.lock.
# The helper validates requested extras against pyproject.toml, runs a frozen
# uv export, and pip installs that export with --require-hashes. The wheel is
# then installed with --no-deps so pip cannot re-resolve project dependencies.
# The default server extra owns pymorphy3 because multilingual routing is
# enabled by default in server.py; no runtime Python package is installed by a
# separate Docker-only pip resolution path.

ARG UV_VERSION=0.12.3
ARG RUNTIME_EXTRAS=server

# Docker Official Image: python:3.11.15-slim / python:3.11-slim
# Resolved index digest: 2026-08-14
# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:3.11.15-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Build toolchain: only needed here, in case a runtime extra pulls in a
# dependency without a prebuilt wheel for this platform. Never copied
# into the runtime stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Source and the authoritative dependency lock must be present before the
# package is built. The helper is copied explicitly rather than widening the
# Docker context with the whole scripts/ tree.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY scripts/export_locked_runtime_requirements.py ./scripts/export_locked_runtime_requirements.py
COPY core ./core
COPY api ./api
COPY utils ./utils

# Use the same uv release as the repository CI dependency-sync owner. uv is a
# builder-only tool; it is not copied into the runtime image.
ARG UV_VERSION
RUN pip install --upgrade pip build "uv==${UV_VERSION}" \
    && python -m build --wheel --outdir /wheels

# Install the selected declared runtime dependencies from a frozen uv.lock
# export, then install the project wheel itself without dependency resolution.
# The hash gate makes pip fail if an exported registry requirement lacks the
# lock-derived hashes expected by this bounded path.
ARG RUNTIME_EXTRAS
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN python scripts/export_locked_runtime_requirements.py \
        --extras "${RUNTIME_EXTRAS}" \
        --output /tmp/velantrim-runtime-requirements.txt \
    && pip install --require-hashes -r /tmp/velantrim-runtime-requirements.txt \
    && WHEEL="$(ls /wheels/*.whl)" \
    && pip install --no-deps "${WHEEL}" \
    && pip check \
    && python -c "import pymorphy3; pymorphy3.MorphAnalyzer(lang='ru')"

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.11.15-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HOME=/app \
    VELANTRIM_APP_ROOT=/app

# Fixed, non-root UID/GID (not 0, not the first free host UID) so bind
# mounts and multi-host deployments get stable ownership.
RUN groupadd --gid 10001 velantrim \
    && useradd --uid 10001 --gid velantrim --no-create-home \
        --shell /usr/sbin/nologin velantrim

WORKDIR /app

# Only the finished virtualenv is copied — no compilers, no build cache,
# no source tree from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Runtime source that lives outside the installable `core`/`api` package
# (see pyproject.toml packages.find — server.py, server_patch/, app/,
# localmind/, and scripts/apply_migrations.py are deliberately excluded
# from the wheel and must be placed on disk next to it).
COPY server.py ./
COPY server_patch ./server_patch
COPY scripts/apply_migrations.py ./scripts/apply_migrations.py
COPY migrations ./migrations
COPY static ./static
COPY app ./app
COPY localmind ./localmind

# The three docs/ files api/web_console.py actually serves at runtime
# (/console/help, /console/research-mode.md, /console/research-roadmap.md).
# .dockerignore excludes the rest of docs/ — do not widen this to `COPY docs .`.
COPY docs/CONSOLE_BROWSER_TEST.ru.md docs/RESEARCH_MODE.ru.md docs/EITI_PWA_RESEARCH_ROADMAP.ru.md ./docs/

# core/umwelt_store.py's default seed, loaded automatically at startup
# when ENABLE_UMWELT_STORE + ENABLE_UMWELT_AUTO_SEED are on (both default
# "1"). Only this one file from docs/seed/ — see .dockerignore.
COPY docs/seed/umwelt_mvp_seed.json ./docs/seed/umwelt_mvp_seed.json

# core/deployment_profiles.py's VELANTRIM_PROFILE=<id> env files. Only
# config/profiles/*.env and the "developer" profile's exocortex-dev.env —
# not the rest of config/ (see .dockerignore for exocortex-dev.env, which
# is otherwise excluded like every other top-level config/*.env).
COPY config/profiles ./config/profiles
COPY config/exocortex-dev.env ./config/exocortex-dev.env

# Writable runtime state. VELANTRIM_DB_PATH/NGRAM_DB/KUZU_DB_PATH etc.
# default under /app/data (see docker-compose.yml); pymorphy3/huggingface
# caches (when the embeddings extra is installed) fall back to $HOME/.cache.
RUN mkdir -p /app/data /app/data/backups /app/.cache \
    && chown -R velantrim:velantrim /app

USER velantrim

EXPOSE 8000

# Explicit socket timeout in the health probe itself — do not rely only
# on the outer HEALTHCHECK --timeout to bound a hung request.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]