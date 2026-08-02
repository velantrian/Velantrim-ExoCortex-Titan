# Erasure startup recovery — FastAPI wiring

**Status:** lifecycle/readiness increment · one awaited pass · no scheduler

## Startup order

The server performs recovery in this order:

```text
validate configuration
→ apply database migrations
→ load bounded recovery budget
→ await one asyncio.to_thread recovery pass
→ record content-free process receipt
→ rebuild NGram index
→ initialize optional subsystems
→ announce application start
```

Recovery therefore sees the current erasure tables and runs before normal readiness is announced.

## Execution semantics

The lifecycle invokes:

```python
await asyncio.to_thread(
    execute_and_record_startup_recovery,
    load_startup_recovery_budget(),
)
```

The aggregate runner remains synchronous and owns the measured single/batch pass. FastAPI only moves that bounded operation off the event loop and waits for completion.

No `create_task`, periodic scheduler, polling loop or detached worker is introduced.

## Startup outcomes

- `clean`: the process continues and `/health/recovery` returns HTTP 200.
- `degraded`: the process remains available for inspection/operator recovery, but `/health/recovery` returns HTTP 503.
- `observer_failed`: the process remains available for inspection, but `/health/recovery` returns HTTP 503.
- invalid explicit budget configuration: startup fails before recovery execution.

This separates process liveness from readiness. A server with unresolved GDPR recovery work is not advertised as ready for normal traffic.

## Health endpoint

`GET /health/recovery` returns the content-free process projection from `core.erasure_startup_runtime` and uses its fail-closed HTTP status.

The endpoint is intentionally unauthenticated so container/orchestrator readiness probes can use it. Its payload contains no claims, fact IDs, user IDs, exception messages, database paths, SQL, provider secrets or request content.

## Logging boundary

Startup logs contain only:

- `clean`, `degraded` or `observer_failed`;
- aggregate unresolved count;
- safe typed reason code.

The complete receipt is not logged. Detailed exceptions remain in the protected module logger that generated the typed failure evidence.

## Non-goals

This increment does not:

- create a recovery scheduler;
- retry periodically after startup;
- persist aggregate receipts;
- add a bypass/disable feature flag;
- change erasure state machines, leases or fencing;
- write Canon;
- affect response generation.

Explicit operator recovery remains available through the existing exhaustive APIs. A future recurring recovery policy, if operational evidence requires it, needs a separate authority/ADR review.
