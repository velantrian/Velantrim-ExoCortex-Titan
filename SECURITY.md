# Security Policy — Velantrim Titan 9.0

**Status: research-grade prototype moving toward production hardening.**

This document describes Velantrim Titan 9.0's security model as it actually is today —
what is enforced, what is opt-in, and what is still a gap — so reviewers and operators
can make an informed decision before deploying it.

---

## 1. Security model: local-first

Velantrim Titan is a **local-first verifiable memory runtime**. By default it runs as a
single process against a local SQLite store (`data/velantrim.db`) with no required
outbound network calls except the LLM provider you explicitly configure. There is no
multi-tenant control plane, no telemetry, and no third-party service the runtime talks
to on its own.

Practical implications:

- All facts, embeddings, and provenance data live on the disk of the machine (or
  container) you run it on. You own the data lifecycle.
- The HTTP API (`server.py`) is the only network-facing surface. Everything else
  (`core/`) is a library that can be used offline / embedded without a server at all.
- Because it is local-first, the biggest realistic risk is **misconfigured exposure**
  (binding an unauthenticated instance to a public interface), not a multi-tenant data
  leak between unrelated users. Sections 2–5 below exist to prevent exactly that.

## 2. API key requirement

`server.py` requires `VELANTRIM_API_KEY` at startup:

- If `VELANTRIM_API_KEY` is unset **and** `VELANTRIM_ALLOW_OPEN` is not `true`, the
  process **refuses to start** (`RuntimeError`).
- If you explicitly set `VELANTRIM_ALLOW_OPEN=true` with no key, it starts in an
  **open, unauthenticated** mode — logged loudly as a development-only state. Never set
  this in a deployment reachable from anything but `localhost`.
- When a key is configured, protected routes require the `X-Api-Key` header. Comparison
  uses `hmac.compare_digest` (constant-time) to resist timing attacks.
- Outbound LLM/STT/TTS routes (`register_llm_routes(..., auth_dependency=require_api_key)`)
  are gated behind the same key — an unauthenticated caller cannot use your configured
  LLM provider key as a free relay.

There is a single shared API key, not per-user accounts or scoped tokens. Treat it as a
deployment secret (put it in `.env` / your orchestrator's secret store), not something
to hardcode or commit.

## 3. LLM provider key handling

Provider credentials (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and other provider keys
under `config/llm.example.env`) are read from environment variables at startup and used
only to make outbound calls to that provider on the caller's behalf.

- Provider keys are never returned in API responses. `test_console_security.py::test_bootstrap_never_leaks_key`
  exists specifically to catch a regression here.
- Provider keys are not written into the fact store; only the resulting generated text
  (subject to the Truth Gate, see `docs/REVIEWER_README.md`) is.
- If you do not configure a provider (`LLM_PROVIDER=none`), no outbound LLM calls are
  made at all — the runtime still works as a pure memory/retrieval system.

## 4. Docker production warning

- `docker-compose.yml` is the **production** profile. It requires an explicit
  `VELANTRIM_API_KEY` (`${VELANTRIM_API_KEY:?VELANTRIM_API_KEY is required}`) — it will
  refuse to start `docker compose config`/`up` without one. There is no built-in default
  key in this file.
- `docker-compose.dev.yml` is **local development only**. It falls back to a
  well-known, public default (`dev-key-change-me`) when `VELANTRIM_API_KEY` is unset.
  **Do not use `docker-compose.dev.yml`, or that default key, in any environment
  reachable from outside your own machine.**
- Both files expose port `8000` directly. Put a reverse proxy (TLS termination, WAF,
  rate limiting at the edge) in front of any deployment reachable from the internet —
  the app-level rate limiter (§6) is a courtesy, not a substitute.

## 5. Dev vs. production distinction

| | Development | Production |
|---|---|---|
| API key | optional (`VELANTRIM_ALLOW_OPEN=true`) or `dev-key-change-me` | **required**, no default |
| Compose file | `docker-compose.dev.yml` | `docker-compose.yml` |
| Swagger/OpenAPI (`/docs`, `/redoc`) | `ENABLE_API_DOCS=true` to inspect | leave unset (default `false`) — it is an admin-adjacent surface |
| CORS | permissive during local iteration if you choose | set `CORS_ORIGINS` explicitly to the origins you actually serve |
| Encryption at rest | optional | recommended once you hold real user data (see §7) |

If you are reviewing this project for a security assessment, assume the **production**
column is the one that matters; the development column exists purely to lower the
barrier to running and testing the code locally.

## 6. Rate limiting

An in-process, per-IP token-bucket rate limiter (`core/rate_limit.py`) is available and
gated behind `ENABLE_RATE_LIMIT` (default off). It is intentionally simple (stdlib only,
single-process, no shared state across replicas) — treat it as a courtesy backstop, not
a substitute for rate limiting at your load balancer/WAF in front of a public
deployment.

## 7. CORS / API docs note

- `CORS_ORIGINS` defaults to an **empty list** (CORS effectively disabled), not `*`.
  This was an intentional audit fix: the previous `*` default silently broke once
  credentialed requests were introduced, since browsers reject
  `Access-Control-Allow-Credentials: true` combined with a wildcard origin. Set
  `CORS_ORIGINS` explicitly to a comma-separated allowlist for any browser client you
  actually serve.
- Swagger UI / ReDoc / the raw OpenAPI schema (`/docs`, `/redoc`, `/openapi.json`) are
  **disabled by default** and only mounted when `ENABLE_API_DOCS=true`. They are an
  admin-adjacent surface (they enumerate every route) — only enable them where you also
  control network access.
- Additional always-on response headers (`X-Content-Type-Options: nosniff`, etc.) are
  applied via a small security-headers middleware in `server.py`; they are defensive
  depth, not a replacement for the controls above.

## 8. Encryption at rest (optional)

`core/crypto.py` provides opt-in field-level encryption (Fernet + HMAC, PBKDF2-HMAC-SHA256
key derivation) for values that should not be stored in plaintext, gated behind
`VELANTRIM_ENCRYPTION_KEY`. It is off by default because most fields need to remain
full-text-searchable / JSON-queryable — see the module docstring for the exact scope.
The key-derivation salt is fixed by design (so the same passphrase yields the same key
across restarts); this means the salt itself must never be rotated once real data has
been encrypted with it, or that data becomes unrecoverable.

## 9. Data subject rights (GDPR-style erasure)

`core/forgetting.py` implements three operations — `FORGET_ONE`, `FORGET_ALL`, and
`REDACT_PII` — with dependency checks before deletion and an audit trail for each
`FORGET_ALL` call. Ring Zero / ImmutableCore facts are never deleted, even on request
(this is enforced, not configurable).

Be precise about what this is: it is a working erasure/redaction **mechanism**, not a
certified, audited GDPR compliance program (no Records of Processing Activities, no
consent-management layer, no legal review). If you operate on real personal data under
a specific regulatory regime, treat this as a foundation to build a compliance program
on top of, not as a substitute for one.

## 10. Reporting a vulnerability

<!--
TODO(maintainer): replace this placeholder with a real, monitored contact before
accepting reports from the public — e.g. a security@ mailbox or a GitHub Security
Advisory contact for this repository.
-->

If you find a security issue in Velantrim Titan, please **do not open a public GitHub
issue**. Instead:

1. Open a private security advisory via this repository's GitHub **Security** tab
   (Security → Advisories → "Report a vulnerability"), or
2. Contact the maintainer through the channel listed in the repository's GitHub profile.

Please include: the affected version (`GET /` or `GET /api` reports the running
version), a minimal reproduction, and the potential impact. This is a small,
research-stage project — please give a reasonable amount of time to respond and ship a
fix before any public disclosure.

## 11. Current status

Velantrim Titan 9.0 is a **research-grade prototype moving toward production
hardening**. The controls above are real and enforced by tests where noted, but this
project has not undergone an independent third-party security audit or penetration
test. Treat it accordingly: suitable for local use, research, and evaluation today;
additional hardening (see `docs/PROJECT_STATUS.md` for the roadmap) is expected before
it should hold real users' sensitive data in a production, internet-facing deployment.

---

See also: [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) for a broader map of the
codebase, and [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for what is stable vs.
experimental and the current hardening roadmap.
