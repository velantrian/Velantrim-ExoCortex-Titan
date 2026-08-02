# Bounded batch erasure recovery

**Status:** batch-adapter execution increment · no aggregate runner · no lifespan wiring

## Purpose

`core.erasure_bounded_batch_recovery.resume_batch_jobs_bounded()` gives the later startup runner a count- and time-bounded view over Titan's existing durable batch-erasure saga.

It does **not** replace `BatchErasureCoordinator.resume_incomplete_batches()`. The existing exhaustive method remains intentionally unbounded for explicit operator recovery, preserving its established fairness guarantee across an arbitrary ordinary backlog.

## Bounded startup selection

The adapter performs two bounded queries using the same predicates as the coordinator:

1. ordinary `PENDING / PARTIAL / FAILED / expired RUNNING` batches;
2. stale terminal batches whose current item rows still prove retryable work.

Both streams are ordered by `created_at, batch_id`, deduplicated and interleaved. A stale-terminal candidate receives the first slot because successful `_report()` reconciliation durably moves it into the ordinary category; when ordinary work also exists, it receives the next slot. The combined result never exceeds `max_batches`.

This is a deterministic, category-aware startup policy, not a claim of starvation freedom for every possible budget. With `max_batches=1` and both categories continuously non-empty, a stateless selector cannot prove progress for both categories. The default startup budget is larger. A durable cross-run fairness cursor, if operational evidence later requires one, needs its own reviewed state and rollback contract.

This policy bounds startup latency without applying a hidden global limit to the existing exhaustive operator API.

## Existing ownership reused

For each selected batch the adapter reuses:

- `_report()` for the coordinator's existing effective-state precedence and guarded stale-terminal self-heal;
- `_run_batch(..., wait_if_running=False)`;
- current batch claim CAS;
- lease heartbeat and lease-loss handling;
- claim-generation fencing;
- item ownership CAS;
- existing per-fact durable erasure;
- existing finalization and compliance status.

The adapter introduces no new batch state, lease, fencing token, item status or deletion primitive.

## Outcome accounting

The returned `RecoveryDomainReceipt` classifies measured reports conservatively:

- `COMPLETE` with `success=True` and no critical compliance signal → completed;
- `PARTIAL` or `COMPLETE_WITH_RESIDUAL` → partial/unresolved;
- `FAILED`, `SUBJECT_CONFLICT`, critical compliance, or terminal `COMPLETE` without success → failed with a safe typed code;
- unknown outcomes → contract failure propagated to the future aggregate runner.

Already represented complete/partial/failed batches are excluded from the post-run durable backlog, avoiding double-counting. A lost claim is counted as skipped and remains backlog only when its durable row is still recoverable.

## Time and failure semantics

The shared absolute monotonic deadline is checked between batches. An active `_run_batch()` is never interrupted mid-transaction, mid-item or while its heartbeat owns the lease.

Invalid bounds, non-finite clock values, unknown outcomes and unexpected database/schema exceptions propagate. The future aggregate runner must convert pre-measurement failures into `StartupRecoveryFailureReceipt`; the adapter never manufactures successful counters after observer failure.

## Boundary

This increment does not:

- change the existing exhaustive batch recovery API;
- assemble the aggregate startup receipt;
- modify FastAPI lifespan;
- register a scheduler or background task;
- add a durable fairness cursor;
- change erasure, compliance, lease or fencing policy;
- write Canon or affect user-visible output;
- persist startup recovery evidence.
