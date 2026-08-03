# ADR — Characterize SQLiteGraphStore concurrency and crash recovery

**Status:** accepted for evidence collection only  
**Date:** 2026-08-03  
**Roadmap phase:** Core Hardening / SQLite WAL, concurrency, and crash suite

## Context

`SQLiteGraphStore` currently uses:

- one reusable SQLite connection per store instance;
- an instance-local re-entrant lock;
- `check_same_thread=False`;
- `busy_timeout=30000`;
- WAL journal mode when supported;
- `synchronous=FULL` by default;
- commit on successful `_db()` exit and rollback on exception.

This is a plausible local-first durability model, but architecture decisions must not
infer either adequacy or inadequacy from the word “SQLite”. The repository needs
repeatable evidence before considering PostgreSQL, a connection pool, altered
synchronous settings, or transactional outbox coupling.

## Decision

Add two evidence surfaces without changing runtime behavior:

1. a deterministic pytest resilience suite;
2. a reproducible command-line writer probe.

### Blocking correctness checks

The pytest suite proves:

- one store instance can serialize 100 threaded writes without loss;
- 25 independently connected store instances can commit unique facts to one WAL file;
- mixed multi-instance readers and writers observe complete rows;
- a completed `store_fact()` commit survives abrupt process termination;
- an update whose `_db()` context never reaches commit is rolled back after abrupt exit;
- every scenario ends with `PRAGMA integrity_check = ok`.

### Writer probe

`scripts/sqlite_store_probe.py` runs independent-store writer levels:

```text
1 → 10 → 25 → 50 → 100
```

For each level it records:

- successful writes;
- observed durable row count;
- total duration;
- p50/p95/p99 per-write latency;
- exact error classes/messages;
- SQLite integrity result.

It also records platform, Python version, SQLite version, and DB-API thread-safety mode.
The probe exits non-zero on lost writes, errors, count mismatch, or integrity failure.

## Recorded baseline

The one-shot GitHub-hosted run passed the full matrix and the crash/mixed-concurrency
pytest suite. The retained machine-readable evidence is:

`docs/evidence/sqlite-concurrency-baseline-2026-08-03.json`

Environment:

- Linux Azure runner;
- Python 3.11.15;
- SQLite 3.45.1;
- DB-API `threadsafety=3`.

Observed writer results:

| Writers | Successful / durable | Errors | Integrity | p50 | p95 | p99 |
|---:|---:|---:|---|---:|---:|---:|
| 1 | 1 / 1 | 0 | ok | 93.073 ms | 93.073 ms | 93.073 ms |
| 10 | 10 / 10 | 0 | ok | 51.214 ms | 77.574 ms | 77.574 ms |
| 25 | 25 / 25 | 0 | ok | 103.947 ms | 157.034 ms | 187.171 ms |
| 50 | 50 / 50 | 0 | ok | 189.759 ms | 256.004 ms | 340.361 ms |
| 100 | 100 / 100 | 0 | ok | 370.341 ms | 495.394 ms | 544.044 ms |

The non-monotonic 1-vs-10 latency and all absolute timings are runner observations, not
performance guarantees. The load trend does show expected serialized-writer pressure,
while correctness remained intact for this bounded workload.

## Interpretation boundary

Correctness is a hard gate. Latency values are observational and hardware-specific; they
are not a service-level objective and must not be compared across machines without
matching filesystem, CPU, runner load, Python, and SQLite versions.

A green GitHub-hosted baseline means only that this workload passed on that recorded
runner. It does not prove:

- unlimited multi-process scale;
- network-filesystem safety;
- acceptable latency for every product profile;
- disk-full behavior;
- bounded lock-wait behavior below the current 30-second timeout;
- atomic mutation + outbox evidence;
- production readiness.

## Non-goals

This increment does not:

- change WAL, synchronous, timeout, transaction, cache, or connection behavior;
- add retry loops;
- migrate to PostgreSQL or another database;
- introduce a connection pool;
- add the transactional outbox;
- establish performance thresholds from a single runner.

## Follow-up gates

After this baseline, separate increments may add:

1. configurable bounded lock-timeout characterization;
2. deterministic disk-full/max-page rollback tests;
3. CAS contention and exactly-one-winner stress;
4. transactional outbox coupling in the same mutation transaction;
5. profile-specific benchmarks and only then a datastore decision.
