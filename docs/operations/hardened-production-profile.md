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
| C | External provider traffic without operator action | **Enforced at the application layer.** `VELANTRIM_NETWORK_MODE=deny` + `VELANTRIM_REMOTE_DATA_MODE=never` are pinned: every LLM/STT/TTS path is refused a capability lease before any connection opens, including a request that supplies its own `llm_provider` + `llm_api_key`. Defence in depth: no provider credential in the compose file; `LLM_PROVIDER=none`; `ENABLE_CONCEPT_LLM_NAMING=0`, `ENABLE_CROSS_DOMAIN_LLM_ROUTING=0`, `VELANTRIM_VISION_LLM=false`, `VELANTRIM_PDF_USE_MARKER_LLM=false`. Not network-level isolation — see §6 | validator asserts both variables; a denied call raises `RemoteEgressDeniedError` with no client constructed; log reports `LLM: none` |
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
| `ENABLE_OBSERVER=1` | passive read-path meta-monitor |
| `ENABLE_RESPONSE_GUARDIAN=1` | response guardian — **scope:** runs inside `core/pipeline.py`, so it covers the pipeline answer (which is the returned answer while no provider is configured), **not** an `llm_answer` |
| `ENABLE_OUTPUT_FAITHFULNESS=1` | answer/fact faithfulness check — same scope caveat |
| `ENABLE_IMMUTABLE_CORE=1` | the **manually invoked** graph-snapshot API in `core/immutable_core.py`. No automatic SHA-256 snapshot is produced — `ImmutableCoreScheduler` is never started (§7.4) |
| `ENABLE_RATE_LIMIT=1` | per-IP token bucket (`core/rate_limit.py`) |
| `ENABLE_CIRCUIT_BREAKER=1` | backpressure |
| `ENABLE_MEMORY_BUDGET=1` | bounded memory growth |
| `VELANTRIM_SQLITE_SYNCHRONOUS=FULL` | durability |
| `VELANTRIM_VERSION_SNAPSHOTS=true` | provenance pre-images |
| `COMPUTE_PROFILE=lite` | adds nothing beyond the Truth Kernel |

### Controls deliberately pinned OFF after the PR #63 review

Three controls were pinned on in the first version of this profile. Verification
against `main` showed each one either fails open or does nothing here, so the
profile no longer enables them and no longer claims them.

| Variable | Now | Why |
|---|---|---|
| `ENABLE_TRUTH_POLICY` | **0** | Fail-open. `server.py` wraps the `truth_policy.decide` call in `except Exception` that logs at DEBUG and leaves `truth_rejects_answer=False`, then generates the answer anyway. The gate opens precisely when the policy breaks, and at `LOG_LEVEL=INFO` the failure is silent. Re-enable only after a reviewed runtime fix makes that path reject. |
| `ENABLE_RESPONSE_AUDIT` | **0** | Unreachable. The only non-test caller of `core.response_audit.audit_response_generated` is the `RESPONSE_GENERATED` handler in `core/l45_bridge.py`, and `register_l45_handlers()` returns early unless the event bus is on. With `ENABLE_EVENT_BUS=0` no audit record is ever written. Reaching it by enabling the event bus would switch on unrelated background dispatch, which this profile refuses — so auditing stays off and unclaimed. |
| `ENABLE_IMMUTABLE_CORE` | 1, **claim corrected** | Still enables the manual graph-snapshot API, which is harmless and useful. But `ImmutableCoreScheduler` has no non-test caller, so nothing schedules SHA-256 snapshots. The profile no longer advertises automatic snapshotting. |

Not the fix: turning on `ENABLE_EVENT_BUS` to make auditing reachable. That is why
`ENABLE_EVENT_BUS` and `ENABLE_EVENT_BUS_BACKGROUND` both stay `0`.

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

**Denied by policy, and separately not configured.** Two independent controls;
keep them distinct, because only one of them is a boundary.

**The boundary** is the policy kernel, pinned by this profile:

```yaml
- VELANTRIM_NETWORK_MODE=deny
- VELANTRIM_REMOTE_DATA_MODE=never
```

Every server-side LLM/STT/TTS path must obtain a capability lease from
`core/policy_kernel.py` through `core/remote_egress.py` before opening a
connection. Under `deny` the lease is refused and `RemoteEgressDeniedError` is
raised **before any HTTP client is constructed** — this is a pre-network block,
not a response filter. It applies to a request that supplies its own credentials:

```json
{"llm_provider": "anthropic", "llm_api_key": "..."}
```

Such a request is now rejected rather than served. Both variables are validated
at startup; an invalid value refuses to boot rather than degrading a live
process. Relaxing one is not enough — `network=allow` alone still denies raw
payloads under `remote_data=never`. `ask` is fail-closed until a consent broker
exists. See `docs/REMOTE_EGRESS_POLICY.ru.md`.

**Not a boundary**, but retained as defence in depth: no provider credential is
referenced by `docker-compose.prod.yml`, and `LLM_PROVIDER` resolves to `none`,
so no provider is configured from the environment. On its own this never blocked
anything — `server.py::_resolve_llm_config_for_request` prefers a config built
from the request, and the LLM/STT/TTS routes are always registered. Do not
present `LLM_PROVIDER=none` as the control; the two policy variables are.

### What the application layer still cannot do

Enforcement lives in the process that would make the call. It stops Titan's own
code paths; it does not stop a compromised process, a sidecar, or anything else
in the network namespace. For enforced egress denial, apply it at a layer that
can — host firewall, egress proxy, NetworkPolicy. Restricting who holds
`VELANTRIM_API_KEY` remains worthwhile.

One documented limit: capability leases declaring `data_mode="none"` skip the
remote-data dimension. That set is closed to two metadata-only capabilities
(`remote_model_discovery`, `remote_llm_test`) and asserted at the boundary, and
the public probe routes forbid extra fields so no prompt, memory, audio or
attachment can ride along. But `data_mode` is caller-declared and unverifiable,
so `remote_data=never` guarantees "no caller declared a payload", not "no bytes
could leave". Under `network=deny` the question does not arise — the network
check runs first and covers metadata too.

### Configuring a provider from the environment

⚠️ Putting a credential in `.env.prod` alone does **not** reach the container.
The compose file declares an explicit `environment:` list and only the variables
named there are passed in; `--env-file` supplies values for `${...}`
interpolation and nothing more. `LLM_PROVIDER` **is** interpolated, so setting it
works — but `ANTHROPIC_API_KEY` and friends are not referenced, so they would be
silently ignored and the provider would fail to authenticate.

Pass the credential in explicitly with an uncommitted override file:

```yaml
# docker-compose.provider.yml   (add to .gitignore)
services:
  velantrim:
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:?provider key required}
```

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.provider.yml \
  --env-file .env.prod up -d
```

Note that the answer-integrity checks do not cover a provider answer — see §7.3.

## 7. Known limitations and residual gaps

These are real and deliberately not papered over. Items 7.1–7.4 are the
**unresolved runtime gaps carried over from the PR #63 review**; each is a
runtime defect that configuration cannot fix, and each needs its own reviewed PR.

1. ~~**Remote providers are reachable per request (P1, runtime).**~~
   **RESOLVED.** `core/policy_kernel.py` now resolves `VELANTRIM_NETWORK_MODE`
   and `VELANTRIM_REMOTE_DATA_MODE` from the environment, and every server-side
   LLM/STT/TTS path takes a capability lease through `core/remote_egress.py`
   before opening a connection. A request supplying `llm_provider` +
   `llm_api_key` is refused pre-network under the pinned `deny` + `never`. This
   profile pins both explicitly and the validator asserts them (§4).

   Residual, narrower items rather than the original gap: `data_mode` is
   caller-declared and unverifiable (bounded to two metadata-only capabilities,
   see §6), and application-layer enforcement cannot bind anything outside this
   process (see §6, "What the application layer still cannot do").
2. **TruthPolicy is fail-open (P1, runtime).** `server.py` catches any exception
   from `truth_policy.decide`, logs at DEBUG, leaves `truth_rejects_answer=False`
   and proceeds to answer generation — so the verdict permits an answer exactly
   when the policy is unavailable, silently at `LOG_LEVEL=INFO`. This profile
   sets `ENABLE_TRUTH_POLICY=0` as the safe configuration-only response. The
   runtime path must be made to reject or fail the request before the flag can be
   turned back on.
3. **Answer-integrity checks do not cover a provider answer (P1, runtime).**
   `apply_response_guardian` and `check_response_faithfulness` run inside
   `core/pipeline.py`. `server.py` generates `llm_answer` afterwards and returns
   it; `/chat` returns the provider reply directly. With no provider configured
   the pipeline answer *is* the returned answer, so the checks apply — but a
   request-configured provider (7.1) bypasses both. They must be applied to the
   final selected response.
4. **No automatic integrity snapshots (P1, runtime).**
   `core/immutable_core_scheduler.py::ImmutableCoreScheduler` has no non-test
   caller, so the server never constructs or starts it.
   `ENABLE_IMMUTABLE_CORE=1` enables only the manually invoked graph-snapshot
   API. Either the lifespan must start and stop the scheduler, or no automatic
   SHA-256 snapshot may be claimed — this profile takes the latter position.
5. **Response auditing is unreachable without the event bus (P1, runtime).**
   The sole non-test caller of `audit_response_generated` is the
   `RESPONSE_GENERATED` handler in `core/l45_bridge.py`, whose registration
   returns early unless the event bus is enabled. `ENABLE_RESPONSE_AUDIT=0` here;
   auditing needs an invocation path independent of the bus.
6. **The Compose network is not `internal: true`.** An internal network removes
   the gateway, which also removes published-port reachability, so it cannot
   host the API entrypoint. If your environment requires enforced egress denial,
   apply it at the layer that can actually enforce it (host firewall, egress
   proxy, Kubernetes NetworkPolicy, or a sidecar). This profile does not claim
   complete egress isolation.
7. **`VELANTRIM_ALLOW_OPEN` still exists in runtime code** (`server.py:69`) as an
   unauthenticated development bypass. This profile does not supply it, and
   `server.py:85` refuses to import without a key, but the code path remains.
   Removing it is a runtime change and out of scope here.
8. **TruthGate does not cover every write path.** `core/memory.py::promote_esm_to`
   ends its ladder walk with a plain `transition_esm()` into `Validated` for
   `world_skills_ingest`, `CognitiveStore.transition` and test fixtures. Setting
   `ENABLE_TRUTH_GATE=1` does not change that. Unifying admission is explicitly
   out of scope.
9. **Contradiction detection is unavailable.** `core/truth_gate.py` accepts
   `contradiction_detector` of `none` (default), `naive` (documented
   false-positive-prone, development only) or `nli` (raises
   `NotImplementedError`). No production-safe detector exists yet.
10. **A fresh deployment reports `DEGRADED`.** With zero facts the MHI is 0.375,
   below the 0.50 healthy threshold, so `/health` returns HTTP 200 with
   `status: degraded`. Only MHI < 0.30 produces SAFE_MODE/503. This is expected
   on an empty store, not a deployment fault.
11. **Pre-existing log error, unrelated to this profile:**
   `LLM API: /console/llm/test ❌ не зарегистрирован` is emitted at ERROR by
   `server.py:438-442`. Reproduced with the unmodified image and default
   environment, so it predates this change. Reported, not fixed here.
12. **`ENABLE_PROMETHEUS_METRICS` is inert.** Both existing compose files set it,
   but no Python code reads it. This profile omits it rather than carry a
   misleading flag.
13. **No image digest pinning.** The Dockerfile uses the `python:3.11-slim` tag.
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
