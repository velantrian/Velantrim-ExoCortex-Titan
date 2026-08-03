# ADR — Characterize SQLite disk-full rollback with `max_page_count`

**Status:** accepted for evidence collection only  
**Date:** 2026-08-03  
**Dependency:** concurrency/crash baseline #174 and bounded busy timeout #175

## Context

The prior storage increments proved bounded concurrent writes, abrupt-exit recovery and
bounded lock-wait failure. They did not prove what happens when SQLite cannot extend the
database file.

A real disk-full incident is difficult to reproduce safely in shared CI. SQLite's
`PRAGMA max_page_count` provides a deterministic local equivalent: constrain the actual
write connection to one page beyond the current database size, then submit a fact whose
serialized metadata requires substantial growth.

`SQLiteGraphStore._db()` intentionally closes its SQLite connection after each operation
because RelationStore and VersionStore use separate connections to the same path.
`max_page_count` is connection-scoped, so setting it in a preliminary connection does
not constrain a later `store_fact()` call. The permanent test therefore installs a
**test-only `_db()` wrapper** that applies the limit inside every real public-store
connection while the fault is enabled. Production connection behavior is unchanged.

## Decision

Add a permanent test that:

1. commits a pre-existing fact;
2. records the current page count and page size;
3. enables a test-only connection wrapper that applies `max_page_count = page_count + 1`
   to the exact connection used by each public store operation;
4. attempts a large ordinary `SQLiteGraphStore.store_fact()` write;
5. requires `sqlite3.OperationalError` containing `full`;
6. verifies the attempted fact is absent from public/cache-visible state;
7. verifies the pre-existing fact is unchanged;
8. scans every same-database table with `fact_id` or `derived_fact_id` and requires zero
   durable references to the failed fact;
9. requires `PRAGMA integrity_check = ok`;
10. removes the injected capacity fault explicitly;
11. retries explicitly through the same public store and requires exactly one durable
    fact row.

## Required failure semantics

```text
connection-scoped capacity fault enabled
→ SQLITE_FULL / OperationalError
→ transaction rollback
→ no partial Canon row
→ no dependent/provenance/version row
→ prior committed data unchanged
→ no automatic retry
→ explicit fault removal / capacity recovery
→ explicit public retry succeeds
```

The test deliberately uses the public store operation rather than direct SQL so it also
checks cache publication ordering and all multi-table side effects performed by the
normal write path.

## Interpretation boundary

A green `max_page_count` test proves transaction rollback for this deterministic,
connection-scoped SQLite capacity failure. It does not prove operating-system behavior
for every filesystem, quota implementation, hardware failure, WAL checkpoint failure,
or abrupt physical-device loss. Clearing the test-only fault models explicit capacity
recovery; it is not a claim that every real disk-full incident is resolved by reopening
a connection.

## Non-goals

This increment does not change runtime code, page size, WAL, synchronous mode, timeout,
retry policy, database selection, connection pooling or outbox behavior.

## Merge gate

An external package-index or dependency-resolution failure is not repository evidence
and must not be treated as a passing check. This PR remains draft until the permanent
test, architecture freeze, lint, blocking type checks and full repository test suite
pass on the same pinned final head. Docker hardening must pass when its workflow is
triggered; an explicit test/docs path-filter skip is recorded as `NOT_APPLICABLE`, never
as `PASS`. No CI exception is granted for this characterization increment.

## Follow-up

After this gate, the next independent storage proof is CAS contention with exactly one
winner and explicit loser semantics. Transactional outbox work begins only after those
storage failure properties are established.
