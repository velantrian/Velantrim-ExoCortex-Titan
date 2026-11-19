# ADR — Opt-in FastAPI lifecycle for local FTS projection delivery

**Status:** Proposed in a draft PR
**Date:** 2026-11-19
**Audited base:** `485c4b0906ec35829ff7231c6276bf7d817f096f`

## Context

Participating Canon writes commit immutable intents with their existing
transaction. The [bounded dispatcher ADR](ADR-2026-08-04-bounded-local-projection-dispatcher.md)
defines at-least-once delivery, including recoverable lease expiry and
version-monotonic replay after apply commits. The audited FastAPI service has no
caller for that dispatcher. The existing synchronous FTS writes remain part of
their respective mutation paths.

## Decision

- `VELANTRIM_PROJECTION_DISPATCH_ENABLED` defaults to off. Enable explicitly
  with `true` and a `VELANTRIM_DB_PATH` that identifies the same SQLite file
  for Canon and migrations. The server and store have different fallback paths
  when `VELANTRIM_DB_PATH` is unset. Opt-in startup rejects a path mismatch
  before running migrations and verifies the migrated FTS schema before polling.
- FastAPI owns one polling task per application lifespan. Start it after the
  existing migration step. Work uses a dedicated connection to the existing
  SQLite file, a short busy timeout and a SQLite execution budget. Each pass
  runs off the event loop and calls the existing bounded `dispatch_once()` with
  UTC time. Shutdown stops polling, signals the active pass and waits for it
  to release its connection. A SQLite interruption leaves any committed lease
  recoverable after expiry.
- Keep claim, apply and final state transitions in their existing SQLite
  transactions. Retry uses the existing deterministic schedule. An expired
  lease can be claimed again. An intent with a non-integer durable canonical
  version uses the existing park transition. Parked work requires operator
  intervention.
- Report the worker's state, last successful pass, failures, bounded backlog
  counts and oldest pending age on authenticated `GET /health/projection`.
  Check the response state even when HTTP status is 200. Pending includes
  unclaimed, retry and leased work. Parked work has a separate count. Both
  counts are capped at 1001. Diagnostic data is process-local and includes
  batch totals without facts, paths, intent IDs, tokens or exception text.
- Apply the [FTS-only policy v1](ADR-2026-08-04-projection-policy-v1-fts-checkpoint.md).
  Existing index routing, migration files and Canon/ESM writers retain their
  current ownership. Use the current single-worker deployment topology.

## Alternatives and limits

An eager startup drain would make startup depend on backlog size. A separate
scheduler would add a lifecycle owner and deployment surface. The existing
dispatcher already supplies retry and park semantics.

Outbox backlog measures only mutations that generated an intent. Oldest pending
age is a delivery-lag indicator for that subset. An empty claim with 10,000
acknowledged rows used roughly 150,000 SQLite VM operations in a disposable
database. Capped diagnostic output does not bound the historical scan.

The existing dispatcher samples time before acquiring the SQLite write lock. A
disposable test showed apply can proceed after the nominal expiry following a
lock wait. Acknowledgement rejected the expired lease and an old token stayed
fenced after takeover. The runtime's 0.2-second SQLite busy timeout and 30-second
lease limit the effect of a lock wait. Strict expiry remains unverified.

Delivery rates on production data and multi-process FastAPI startup require
separate evidence. Production activation requires an operator decision.

## Verification

The draft PR records the exact results for default-off and opt-in FastAPI
lifespan tests, FTS delivery and restart, crash/retry regressions and stale lease
fencing. The test scope uses disposable SQLite databases and local services.
