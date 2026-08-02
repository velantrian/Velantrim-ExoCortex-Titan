# Erasure startup recovery runtime state

**Status:** process-state and health projection increment · no server wiring · no scheduler

## Purpose

`core.erasure_startup_runtime` is the narrow bridge between the aggregate bounded recovery runner and a later FastAPI lifespan/health integration.

It provides:

- strict bounded environment parsing;
- one content-free receipt retained for the current process;
- clean/degraded/observer-failed readiness projection;
- HTTP status guidance for a dedicated recovery health endpoint.

It does not execute automatically, register a route, modify `server.py`, start a background task, or persist evidence.

## Environment contract

Defaults:

```text
VELANTRIM_ERASURE_STARTUP_MAX_SINGLE_JOBS=25
VELANTRIM_ERASURE_STARTUP_MAX_BATCHES=5
VELANTRIM_ERASURE_STARTUP_TIME_BUDGET_MS=5000
```

Hard caps:

```text
single jobs: 0..1000
batches: 0..100
time budget: 1..60000 ms
```

Both recovery domains cannot be set to zero. Invalid explicit values fail configuration instead of silently falling back to defaults.

No enable/disable feature flag is introduced. Startup recovery is a safety mechanism, not optional cognitive functionality.

## Process state

`execute_and_record_startup_recovery()` executes a supplied aggregate runner and records exactly its typed result:

- `StartupRecoveryReceipt`; or
- `StartupRecoveryFailureReceipt`.

The dataclasses are immutable and content-free. The state is protected by a process lock for concurrent health reads.

The first increment is honestly non-persistent. A restart creates a new process state and performs a new startup observation. Durable evidence storage requires a separate schema and migration review.

## Readiness mapping

| Runtime evidence | Status | Ready | HTTP |
|---|---:|---:|---:|
| no receipt | `not_observed` | false | 503 |
| `OBSERVED_ZERO` | `clean` | true | 200 |
| `OBSERVED_NONZERO` | `degraded` | false | 503 |
| `OBSERVER_FAILED` | `observer_failed` | false | 503 |

A non-empty backlog is never presented as healthy readiness. The application process may remain alive for inspection and operator recovery, but a readiness probe can refuse normal traffic.

## Data exposure

The health projection contains only:

- schema and observation states;
- count/time budgets;
- aggregate counts;
- UTC timestamps;
- safe typed reason codes;
- a pseudonymous recovery run ID.

It never includes claims, fact IDs, user IDs, exception messages, paths, SQL, provider secrets or payload fragments.

## Next increment

1. merge the aggregate runner;
2. retarget this stacked branch to `main` and run full CI/Docker;
3. invoke `execute_and_record_startup_recovery()` once through awaited `asyncio.to_thread(...)` immediately after migrations;
4. expose `get_startup_recovery_health()` at `/health/recovery`;
5. add no periodic scheduler.
