# ADR — Fresh-store SQLite bootstrap serialization

Date: 2026-08-16
Status: ACCEPTED · BOUNDED STORAGE FIX
Issue: #347

## Context

`SQLiteGraphStore` lazily initializes its runtime schema the first time a store instance opens a database. The in-process `_db_lock` and `_ddl_initialized_paths` guard are per store instance. Multiple independent, never-opened stores pointing at the same SQLite file could therefore enter the lazy DDL/bootstrap region concurrently on distinct SQLite connections.

Issue #347 was separated from #249 because the observed failure occurred before the real promotion CAS. The reproduced signature was:

- 25/25 workers started;
- 25/25 stores ready;
- 24/25 contenders reached the pre-CAS gate;
- 0/25 CAS calls returned;
- one contender failed with `sqlite3.OperationalError: database schema has changed`.

A GitHub-hosted exact pre-#346 replay reproduced the residual on current code: Python 3.11 completed 49/50 iterations successfully and reproduced the pre-CAS failure once. The failure therefore is not evidence that `_promote_to_validated_cas()` violates its one-winner semantics; the failing worker did not reach the synchronized CAS release.

Earlier narrow fixes remain valid and separate:

- Issue #182 / PR #185: erasure-audit view bootstrap race;
- Issue #184 / PR #187: lazy `ADD COLUMN` concurrency/error-classification race.

They did not provide a connection-level serialization boundary for the whole remaining lazy bootstrap region.

## Decision

When a store instance must execute the lazy bootstrap region, it begins an explicit SQLite write transaction with:

```sql
BEGIN IMMEDIATE
```

The existing bootstrap DDL then runs inside that transaction. The existing `commit()` ends the bootstrap transaction before the caller's later application operation or promotion CAS executes.

This deliberately serializes only first-use schema/bootstrap work across independent SQLite connections. It does not serialize the subsequent product CAS race.

If bootstrap raises, the store must fail closed and release the write transaction/connection:

1. attempt `rollback()`;
2. attempt `close()`;
3. clear `self._sqlite_conn`;
4. re-raise the original exception.

Rollback/close cleanup failures are logged and do not replace the original bootstrap failure.

## Evidence

Hosted characterization established both the defect and the bounded candidate:

- exact pre-#346 replay: reproduced `database schema has changed` before CAS;
- runner-only `BEGIN IMMEDIATE` candidate: 100/100 PASS on Python 3.11 and 100/100 PASS on Python 3.12;
- rollback-safe candidate: clean on both Python versions, including a malformed-schema failure probe proving a new independent connection can immediately acquire `BEGIN IMMEDIATE` after the failed bootstrap;
- real promotion invariants remain unchanged: one canonical winner, one projection-outbox intent, matching canonical version, idempotent `already_validated` retry, SQLite integrity OK.

A permanent regression test restores the fresh-store race without the #346 sequential pre-initialization control and gates contenders immediately before the real CAS, proving that all independent stores first survive normal lazy bootstrap while the later CAS remains concurrent.

## Rejected alternatives

The following are not admitted for this defect:

- changing `_promote_to_validated_cas()`;
- automatic retry of `OperationalError`;
- increasing SQLite busy timeout as a speculative workaround;
- changing WAL or synchronous settings;
- replacing SQLite/backend architecture;
- swallowing broad `OperationalError` classes;
- a process-global Python lock that would not provide cross-process SQLite semantics.

## Consequences

Positive:

- independent fresh stores no longer race schema mutations inside the supported local SQLite file;
- serialization is delegated to SQLite's own writer-lock transaction semantics;
- the later CAS path remains unchanged and concurrent;
- bootstrap failure explicitly releases the writer transaction and reusable connection.

Cost:

- simultaneous first-use store instances may wait behind the bootstrap writer transaction, bounded by the repository's existing SQLite connection timeout policy.

## Limits

This decision does not prove or claim:

- network-filesystem safety;
- unlimited writer scale or fairness;
- distributed consensus;
- a new production SLO;
- production readiness;
- runtime enablement or Operator GO;
- any Canon, TruthGate, PolicyKernel, or authority change.

Runtime authority remains false. Phase 3B remains NOT ADMITTED / NOT STARTED.
