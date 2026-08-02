# Aggregate bounded erasure startup runner

**Status:** aggregate execution increment · no FastAPI lifespan wiring · no scheduler

## Purpose

`core.erasure_startup_runner.run_startup_recovery()` combines the already bounded single-fact and batch erasure adapters into one measured startup pass.

The runner is synchronous. A later FastAPI increment must invoke it once through an awaited `asyncio.to_thread(...)` call after database migrations and before readiness is announced.

## Shared budget

One `StartupRecoveryBudget` provides:

- `max_single_jobs`;
- `max_batches`;
- `time_budget_ms`.

The runner samples one finite monotonic start value and derives one absolute deadline. Both domain adapters receive that same deadline.

Single-fact recovery runs first. Batch recovery still performs its bounded candidate observation when the execution deadline has already expired, allowing selected-but-unattempted batch work to remain visible instead of being reported as clean.

A running erasure saga is never interrupted mid-step, transaction, item, heartbeat or lease. The deadline is an admission boundary between units of durable work.

## Aggregate evidence

A successful measured pass returns `StartupRecoveryReceipt` containing:

- single-fact domain receipt;
- batch domain receipt;
- shared count/time budget;
- UTC start/completion timestamps;
- one run ID;
- combined unresolved count;
- derived `OBSERVED_ZERO` or `OBSERVED_NONZERO` state;
- explicit time-budget stop state.

The first runtime increment remains honestly non-persistent:

```text
persisted = false
storage_ref = null
```

Durable receipt storage requires its own ledger/migration contract and is not implied by configuration.

## Failure semantics

Schema, database, monotonic-clock, wall-clock, run-ID and aggregate-contract failures return `StartupRecoveryFailureReceipt` with `OBSERVER_FAILED`.

Receipts contain only safe typed codes such as:

- `single_fact_database_failed`;
- `batch_contract_failed`;
- `startup_clock_contract_failed`;
- `startup_wall_clock_failed`;
- `startup_identity_failed`;
- `aggregate_contract_failed`.

Exception messages, database paths, SQL, payload fragments and secrets are never copied into the receipt. Detailed exceptions remain only in protected server logs.

If one domain was already executed before the second domain fails, the aggregate result still fails closed as `OBSERVER_FAILED`; it does not manufacture a partial aggregate success claim. The underlying durable erasure ledgers remain authoritative for the work already performed.

## Explicit non-goals

This increment does not:

- modify `server.py` or application lifespan;
- announce readiness;
- expose health status;
- register a recurring scheduler or worker;
- persist the aggregate receipt;
- modify erasure, compliance, lease or fencing policy;
- write Canon;
- affect user-visible answers.

## Next increment

1. merge the bounded batch adapter;
2. retarget this stacked branch to `main`;
3. run full CI and Docker validation;
4. wire one awaited startup pass after migrations;
5. retain the latest content-free receipt in process state;
6. expose clean/degraded/observer-failed recovery state in health.
