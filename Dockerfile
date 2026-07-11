# Velantrim Titan 9.0 — production Dockerfile
# Build: docker build -t velantrim-titan .
# Run:   docker run -p 8000:8000 --env-file .env velantrim-titan
#
# Multi-stage build:
#   1. "builder" — compiles a wheel for this package and installs it (plus
#      chosen runtime extras) into a throwaway virtualenv. Any compiler
#      toolchain needed by a dependency lives ONLY in this stage.
#   2. "runtime" — copies the finished virtualenv and the small set of
#      source files that are not part of the installable package
#      (server.py, server_patch/, scripts/apply_migrations.py, migrations/,
#      static/, app/, localmind/, and the 3 docs/ files the web console
#      serves) into a clean, non-root, compiler-free image.
#
# VELANTRIM_APP_ROOT tells api/web_console.py where static/ and docs/
# actually live at runtime (see api/web_console.py:_resolve_app_root) —
# needed because installing api/ as a non-editable wheel decouples
# __file__ from this directory.
#
# RUNTIME_EXTRAS controls which optional pyproject.toml extras are
# installed. Default is the minimal set server.py actually imports at
# startup. Pass a wider set at build time for a "full" image, e.g.:
#   docker build --build-arg RUNTIME_EXTRAS=server,parsers,retrieval,embeddings .
# "dev" (pytest/ruff/mypy) and "audio" (openai-whisper, GB-scale) are
# intentionally never part of the default and must be opted into explicitly.

ARG PYTHON_VERSION=3.11-slim
ARG RUNTIME_EXTRAS=server

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS builder

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

# Source must be present before the package is built (no editable install
# of an empty/partial tree, no install-then-copy ordering bugs).
COPY pyproject.toml README.md LICENSE ./
COPY core ./core
COPY api ./api

RUN pip install --upgrade pip build \
    && python -m build --wheel --outdir /wheels

# Install the built wheel (non-editable) plus the requested runtime
# extras into an isolated virtualenv that gets copied wholesale into the
# runtime stage — this is what keeps the compiler toolchain out of it.
ARG RUNTIME_EXTRAS
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN WHEEL="$(ls /wheels/*.whl)" \
    && pip install --upgrade pip \
    && pip install "${WHEEL}[${RUNTIME_EXTRAS}]" pymorphy3 \
    && python -c "import pymorphy3; pymorphy3.MorphAnalyzer(lang='ru')"

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS runtime

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
