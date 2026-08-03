# ADR — Characterize SQLite disk-full rollback with `max_page_count`

**Status:** accepted for evidence collection only  
**Date:** 2026-08-03  
**Dependency:** concurrency/crash baseline #174 and bounded busy timeout #175

## Context

The prior storage increments proved bounded concurrent writes, abrupt-exit recovery and
bounded lock-wait failure. They did not prove what happens when SQLite cannot extend the
database file.

A real disk-full incident is difficult to reproduce safely in shared CI. SQLite's
`PRAGMA max_page_count` provides a deterministic local equivalent: constrain the file to
one page beyond its current size, then submit a fact whose serialized metadata requires
substantial growth.

## Decision

Add a permanent test that:

1. commits a pre-existing fact;
2. constrains the database to `page_count + 1`;
3. attempts a large ordinary `SQLiteGraphStore.store_fact()` write;
4. requires `sqlite3.OperationalError` containing `full`;
5. verifies the attempted fact is absent from public/cache-visible state;
6. verifies the pre-existing fact is unchanged;
7. scans every same-database table with `fact_id` or `derived_fact_id` and requires zero
   durable references to the failed fact;
8. requires `PRAGMA integrity_check = ok`;
9. restores capacity explicitly;
10. retries explicitly and requires exactly one durable fact row.

## Required failure semantics

```text
capacity exhausted
→ SQLITE_FULL / OperationalError
→ transaction rollback
→ no partial Canon row
→ no dependent/provenance/version row
→ prior committed data unchanged
→ no automatic retry
→ explicit operator recovery
→ explicit retry succeeds
```

The test deliberately uses the public store operation rather than direct SQL so it also
checks cache publication ordering and all multi-table side effects performed by the
normal write path.

## Interpretation boundary

A green `max_page_count` test proves transaction rollback for this deterministic SQLite
capacity failure. It does not prove operating-system behavior for every filesystem,
quota implementation, hardware failure, WAL checkpoint failure, or abrupt physical
device loss.

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
