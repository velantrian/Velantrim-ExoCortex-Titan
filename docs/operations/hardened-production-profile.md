# 🛡️ Hardened production profile — operations guide

> **Status:** additive deployment profile · does not change development behaviour
> **Files:** `docker-compose.prod.yml` · `.env.prod.example` · `scripts/validate_production_profile.py` · `tests/test_production_profile.py`
> **Base commit:** `ac6296181d65566ababc13f8d8a888eb1df2ed65`

## 1. Purpose

`docker-compose.yml` is labelled "production" but enables seven cognitive layers
(`ENABLE_CONCEPT_EMERGENCE`, `ENABLE_WORKING_NOTEBOOK`, `ENABLE_CAUSAL_GRAPH`,
`ENABLE_EVENT_BUS`, `ENABLE_COGNITIVE_RUNTIME`, `ENABLE_VELUM`, `ENABLE_ESSENCE`)
while leaving every epistemic and protective control at its default-off value,
publishes `8000` on all interfaces, and applies no container hardening.

This profile is the inverse: **minimum services, minimum features, minimum
exposure, deny by default.** It adds a new file rather than changing the
existing ones, so `docker-compose.yml` and `docker-compose.dev.yml` keep working
exactly as before.

## 2. Quick start

```bash
cp .env.prod.example .env.prod
# put a real key in VELANTRIM_API_KEY:
#   python -c "import secrets; print(secrets.token_urlsafe(32))"

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

Health check:

```bash
curl -fsS http://127.0.0.1:8000/health | python -m json.tool
```

Validate the profile at any time (no Docker daemon required):

```bash
python scripts/validate_production_profile.py
pytest tests/test_production_profile.py -q
```

## 3. Threat model and what was done about it

| # | Risk | Mitigation | Verified |
|---|------|-----------|----------|
| A | Experimental features enabled in production | 33 research/experimental/debug variables pinned to `0`/`false`. An explicit `ENABLE_X=0` beats `COMPUTE_PROFILE` escalation (`core/compute_profile.py::resolve_flag` reads the environment first), so the pins hold even under `COMPUTE_PROFILE=heavy` | startup log shows none of Velum / Etir / Welfare / EventBus / CognitiveRuntime / CognitiveFactStore / Umwelt initialising |
| B | Background cognitive workers start automatically | `SLEEP_WORKER_ENABLED=false`. **This is mandatory, not cosmetic:** `server.py:60` defaults it to `"true"`, so the worker would otherwise self-activate on idle, rewrite CoreMemoryBlocks/notebook state, and receive a live LLM callable | no `SleepTimeWorker: ✅ запущен` line in the startup log |
| C | External provider traffic without operator action | No provider credential appears in the compose file at all; `LLM_PROVIDER=none`; `ENABLE_CONCEPT_LLM_NAMING=0`, `ENABLE_CROSS_DOMAIN_LLM_ROUTING=0`, `VELANTRIM_VISION_LLM=false`, `VELANTRIM_PDF_USE_MARKER_LLM=false` | log reports `LLM: none`; resolved config contains zero credential variables |
| D | Ports exposed too broadly | Exactly one published port, bound to `127.0.0.1` by default | `docker port` → `8000/tcp -> 127.0.0.1:8000` |
| E | Secrets committed | `.env.prod.example` assigns no values; `.gitignore` extended with `.env.*` (the bare `.env` rule did **not** cover `.env.prod`) while keeping `*.example` trackable | `git check-ignore -v .env.prod` matches; a test asserts both directions |
| F | Container runs as root | `user: "10001:10001"` restated on top of the image's `USER velantrim` | `id` → `uid=10001(velantrim)` |
| G | Writable filesystem where unnecessary | `read_only: true` with three narrow writable paths only | writes to `/app`, `/app/server.py`, `/etc`, `/usr/local`, `/opt/venv` all denied |
| H | Excess Linux capabilities | `cap_drop: [ALL]`, no `cap_add` | `/proc/1/status` → `CapPrm/CapEff/CapBnd = 0000000000000000` |
| I | Privileged / host namespaces | none of `privileged`, `network_mode: host`, `pid: host`, `ipc: host` | asserted structurally in tests and the validator |
| J | Unbounded process/memory/log growth | `pids_limit: 512`, `mem_limit`/`memswap_limit` (default 2g), `cpus` (default 2.0), json-file logging with `max-size=10m`, `max-file=3` | resolved config |
| K | Missing health/startup checks | `healthcheck` with `start_period: 20s`; migrations run fail-loud at startup (`server.py:338-352`) | container reaches `(healthy)` |
| L | Writable source bind mount | no bind mount at all — the image already contains the three `docs/*.md` files the console serves (`Dockerfile:112`), so `./docs` does not need mounting | test asserts no bind mount |
| M | Docker socket exposure | not mounted | `ls /var/run/docker.sock` → No such file |
| N | Silent promotion / autonomous ingestion | `ENABLE_GRADUATED_PROMOTION=0`, `ENABLE_CONCEPT_PROMOTE=0`, `ENABLE_SEMANTIC_DEDUP=0`, `ENABLE_CONTRADICTION_RESOLVER=0`, `ENABLE_TELEGRAM_INGEST=0`, `ENABLE_UMWELT_AUTO_SEED=0` | flags asserted; no Umwelt seed line in the log |
| O | Overclaiming network isolation | **Not claimed.** See §7 | — |

## 4. Enabled controls

| Variable | Why |
|---|---|
| `ENABLE_WRITE_GATE=1` | canonical write-protocol gate. `core/write_gate.py::is_write_gate_enabled()` always returns `True`; this pin is the documented compatibility readout, not an off switch |
| `ENABLE_TRUTH_GATE=1` | epistemic admission gate on supported paths |
| `ENABLE_TRUTH_POLICY=1` | explicit read-path verdict |
| `ENABLE_OBSERVER=1` | passive read-path meta-monitor |
| `ENABLE_RESPONSE_GUARDIAN=1` | response guardian |
| `ENABLE_OUTPUT_FAITHFULNESS=1` | answer/fact faithfulness check |
| `ENABLE_RESPONSE_AUDIT=1` | audit trail of responses |
| `ENABLE_IMMUTABLE_CORE=1` | SHA-256 delta snapshots of the immutable core |
| `ENABLE_RATE_LIMIT=1` | per-IP token bucket (`core/rate_limit.py`) |
| `ENABLE_CIRCUIT_BREAKER=1` | backpressure |
| `ENABLE_MEMORY_BUDGET=1` | bounded memory growth |
| `VELANTRIM_SQLITE_SYNCHRONOUS=FULL` | durability |
| `VELANTRIM_VERSION_SNAPSHOTS=true` | provenance pre-images |
| `COMPUTE_PROFILE=lite` | adds nothing beyond the Truth Kernel |

`ENABLE_CAUSAL_GRAPH=1` is deliberately retained: it is the default-on relation
substrate (`flag("ENABLE_CAUSAL_GRAPH", "1")`), and the read path degrades
rather than fails without it. `CAUSAL_PERSIST=0` keeps it non-durable.

`VELANTRIM_MULTILINGUAL` is left at its default (`1`). It patches retrieval for
RU/EN lemmatisation — local, deterministic, no network, no memory writes.

## 5. Public port policy

One published port, `127.0.0.1:8000` by default. To expose it beyond the host,
set `VELANTRIM_BIND_ADDR=0.0.0.0` **and put a TLS-terminating reverse proxy in
front** — the application speaks plain HTTP and has no TLS of its own.

There is no database service and therefore no database port: this profile pins
`STORAGE_BACKEND=sqlite`, which is in-process.

## 6. External provider policy

Disabled by default, with no credentials present. Enabling one is a deliberate
two-step act — choose the provider *and* supply its key:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<secret>
```

A credential alone activates nothing: `server.py:150-176` only builds a provider
config for the selected `LLM_PROVIDER`.

> ⚠️ Before enabling a provider, read §7. On this commit the PolicyKernel
> network/remote-data policy is **declarative only**.

## 7. Known limitations and residual gaps

These are real and deliberately not papered over.

1. **No egress enforcement.** `core/policy_kernel.py` returns
   `EffectivePolicy()` with `network=deny` and `remote_data=never`, but nothing
   env-configurable resolves it and, per PR #59, the server-side LLM/STT/TTS
   paths do not acquire a capability lease before opening a connection. Outbound
   denial here rests on `LLM_PROVIDER=none` and the absence of credentials —
   **not** on an enforced boundary. PR #59 (`agent/p0-egress-epistemic-boundary`,
   draft) is the tracked fix.
2. **The Compose network is not `internal: true`.** An internal network removes
   the gateway, which also removes published-port reachability, so it cannot
   host the API entrypoint. If your environment requires enforced egress denial,
   apply it at the layer that can actually enforce it (host firewall, egress
   proxy, Kubernetes NetworkPolicy, or a sidecar). This profile does not claim
   complete egress isolation.
3. **`VELANTRIM_ALLOW_OPEN` still exists in runtime code** (`server.py:69`) as an
   unauthenticated development bypass. This profile does not supply it, and
   `server.py:85` refuses to import without a key, but the code path remains.
   Removing it is a runtime change and out of scope here.
4. **TruthGate does not cover every write path.** `core/memory.py::promote_esm_to`
   ends its ladder walk with a plain `transition_esm()` into `Validated` for
   `world_skills_ingest`, `CognitiveStore.transition` and test fixtures. Setting
   `ENABLE_TRUTH_GATE=1` does not change that. Unifying admission is explicitly
   out of scope.
5. **Contradiction detection is unavailable.** `core/truth_gate.py` accepts
   `contradiction_detector` of `none` (default), `naive` (documented
   false-positive-prone, development only) or `nli` (raises
   `NotImplementedError`). No production-safe detector exists yet.
6. **A fresh deployment reports `DEGRADED`.** With zero facts the MHI is 0.375,
   below the 0.50 healthy threshold, so `/health` returns HTTP 200 with
   `status: degraded`. Only MHI < 0.30 produces SAFE_MODE/503. This is expected
   on an empty store, not a deployment fault.
7. **Pre-existing log error, unrelated to this profile:**
   `LLM API: /console/llm/test ❌ не зарегистрирован` is emitted at ERROR by
   `server.py:438-442`. Reproduced with the unmodified image and default
   environment, so it predates this change. Reported, not fixed here.
8. **`ENABLE_PROMETHEUS_METRICS` is inert.** Both existing compose files set it,
   but no Python code reads it. This profile omits it rather than carry a
   misleading flag.
9. **No image digest pinning.** The Dockerfile uses the `python:3.11-slim` tag.
   Digest pinning is tracked in issue #52 and left alone here.

## 8. Writable paths

`read_only: true` with exactly three writable locations:

| Path | Type | Contents |
|---|---|---|
| `/app/data` | named volume `velantrim_prod_data` | SQLite DBs plus `-wal`/`-shm`, migration backups, ngram DB, graph DB, metrics JSONL, notes, archive |
| `/tmp` | tmpfs 64m, `noexec,nosuid,nodev` | process scratch |
| `/app/.cache` | tmpfs 64m, `noexec,nosuid,nodev`, `uid=10001,gid=10001` | `$HOME/.cache` (pymorphy3 / HF fallback) |

> The `uid`/`gid` options on `/app/.cache` are required. A tmpfs mount shadows
> the image's `chown`, and Docker creates a non-`/tmp` tmpfs root-owned with mode
> 755 — uid 10001 then cannot write to it. This was caught empirically; without
> those options the directory exists but every write fails with `EACCES`.

Every Titan writer defaults under `./data`, which is `/app/data` here — verified
against `VELANTRIM_DB_PATH`, `VELANTRIM_NGRAM_DB`, `SQLITE_GRAPH_PATH`,
`SQLITE_AUDIT_PATH`, `SQLITE_FOCUS_PATH`, `VELANTRIM_METRICS_PATH`,
`VELANTRIM_NOTES_DB`, `VELANTRIM_ARCHIVE_PATH`, and the sleep worker's
`CORE_BLOCKS_DB_PATH` / `NOTEBOOK_DB_PATH`.

## 9. Backup

State lives entirely in the `velantrim_prod_data` volume. `scripts/apply_migrations.py`
also takes an automatic pre-migration backup into `/app/data/backups`.

```bash
# cold backup (stop first for a consistent SQLite snapshot)
docker compose -f docker-compose.prod.yml --env-file .env.prod stop
docker run --rm -v velantrim-exocortex-titan_velantrim_prod_data:/data:ro \
  -v "$PWD:/backup" busybox tar czf /backup/velantrim-prod-$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C /data .
docker compose -f docker-compose.prod.yml --env-file .env.prod start
```

Verify the volume name for your project prefix with `docker volume ls`.

## 10. Shutdown, upgrade, rollback

```bash
# graceful stop (30s grace period for the lifespan handler)
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# upgrade: back up first, then rebuild and recreate
docker compose -f docker-compose.prod.yml --env-file .env.prod build --pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# rollback: redeploy the previous image tag
docker compose -f docker-compose.prod.yml --env-file .env.prod down
docker tag velantrim-titan:<previous> velantrim-titan:prod
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --no-build
```

Migrations are forward-only and idempotent via `PRAGMA user_version`. A rollback
to an image expecting an older schema is **not** covered by an automatic down
migration — restore the backup taken before the upgrade instead.

`down` without `-v` preserves the data volume. **`down -v` destroys it.**

## 11. Claim boundary

This profile improves production defaults and container hardening. It adds a
hardened deny-by-default production deployment profile.

It does **not** prove or provide:

- complete Titan security;
- complete network isolation or egress denial;
- complete admission-path unification;
- complete TruthGate coverage of every write path;
- contradiction detection;
- formal verification;
- Native Kernel conformance;
- GDPR certification;
- any security certification;
- autonomous-agent safety.
