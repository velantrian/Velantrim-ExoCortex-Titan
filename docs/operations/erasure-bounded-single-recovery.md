# Bounded single-fact erasure recovery

**Status:** coordinator-adapter execution increment · no batch recovery · no lifespan wiring

## Purpose

`core.erasure_bounded_recovery.resume_single_fact_jobs_bounded()` executes a deterministic prefix of the existing durable single-fact recovery queue without replacing or weakening `ErasureCoordinator.resume_incomplete_jobs()`.

The bounded adapter exists for a later application-startup runner. The existing exhaustive coordinator method remains the operator API for intentionally draining all resumable jobs.

## Bounds

The caller supplies:

- `max_jobs` — maximum candidate rows admitted from the durable queue;
- `deadline_monotonic` — a finite shared absolute monotonic deadline;
- an injectable monotonic clock for deterministic tests;
- optionally, an explicit `ErasureCoordinator` for dependency injection.

The deadline is checked between jobs. A running erasure saga is not interrupted mid-step; existing backend transaction and CAS boundaries remain authoritative.

## Existing authority reused

For every admitted job the adapter reuses:

1. exact job-scoped tombstone reconciliation;
2. `_run_job(..., wait_if_running=False)`;
3. the existing positive resumable-status allowlist;
4. the existing CAS claim and terminal-state protection.

The adapter is intentionally separate from the mature saga implementation: it adds orchestration bounds without editing or duplicating the deletion state machine. It adds no new erasure state, deletion path, scheduler, worker or policy.

## Accounting

The returned `RecoveryDomainReceipt` records:

- selected and attempted counts;
- complete, partial, failed and skipped outcomes;
- a post-run durable backlog count;
- a safe generic error code when measured outcomes include failures.

Jobs already represented as complete, partial or failed in the receipt are excluded from `remaining_backlog`, preventing double-counting. A lost claim remains backlog only when its durable row is still resumable. Selected-but-unattempted work is conservatively retained when the deadline stops the run.

Unknown outcome strings, invalid bounds and unexpected schema/database exceptions propagate. The future aggregate startup runner must convert them to `StartupRecoveryFailureReceipt`; this adapter never manufactures counters after observer or contract failure.

## Boundary

This increment does not:

- modify the existing exhaustive coordinator API;
- execute batch recovery;
- modify FastAPI lifespan;
- register a recurring scheduler or background task;
- change erasure/tombstone policy;
- write Canon or affect user-visible output;
- persist the aggregate startup receipt.
