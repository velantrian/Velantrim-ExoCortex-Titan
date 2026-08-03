# ADR — Make SQLite busy timeout configurable and bounded

**Status:** accepted for one storage-control increment  
**Date:** 2026-08-03  
**Dependency:** SQLite concurrency/crash baseline PR #174

## Context

The baseline proved bounded local workloads through 100 independent writers without
lost rows or integrity failure. It did not prove acceptable behavior when another
connection holds the SQLite write lock.

`SQLiteGraphStore` currently hard-codes both connection timeout and
`PRAGMA busy_timeout` to 30 seconds. That default is conservative for data safety, but a
fixed 30-second wait prevents deterministic profile-specific failure bounds and makes a
lock incident look like an unresponsive process.

## Decision

Add `VELANTRIM_SQLITE_BUSY_TIMEOUT_MS` with these rules:

- resolved once per `SQLiteGraphStore` instance;
- integer milliseconds;
- accepted range: 1 through 120000;
- invalid, empty, zero, negative, or above-bound values fail closed to 30000;
- default remains exactly 30000;
- the same resolved value configures `sqlite3.connect(timeout=...)` and
  `PRAGMA busy_timeout`;
- all three initial/reopen connection paths use that one resolved value;
- no automatic retry is added.

## Failure semantics

When a competing connection holds the write lock beyond the configured bound:

```text
write attempt
→ sqlite3.OperationalError(database is locked)
→ _db() rollback
→ no partial fact
→ caller receives the failure
→ later explicit retry may succeed after lock release
```

The store must not silently convert the error into success, extend the timeout beyond the
configured bound, or retry automatically.

## Validation evidence

Focused tests proved:

- the default remains 30 seconds;
- malformed and out-of-range values revert to the default;
- a valid value reaches both the connection and `PRAGMA busy_timeout`;
- a held `BEGIN IMMEDIATE` lock causes a bounded failure at 100 ms;
- the failed write leaves no row;
- releasing the lock and explicitly retrying produces exactly one row;
- `PRAGMA integrity_check` remains `ok`;
- the full SQLite resilience suite from PR #174 remains green.

The first exact-patch run stopped before changing the branch because the current store
has three, not two, connection/reopen sites. The patch was corrected to require exactly
three matches; the second run applied the same timeout to all three paths, passed the
focused suites, removed the temporary workflow/script, and published a clean three-file
change-set.

Standard architecture-freeze, Ruff, blocking mypy, full repository pytest and Docker
must pass on the final maintainer-authored head before merge.

## Scope boundary

This increment does not change WAL, synchronous mode, transaction structure, connection
pooling, mutation APIs, retry policy, PostgreSQL strategy, or outbox behavior. It adds a
bounded operator control while preserving the prior default.
