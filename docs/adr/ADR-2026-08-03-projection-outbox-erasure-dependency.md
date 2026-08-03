# ADR — Include projection_outbox intents in the atomic same-DB erasure proof

**Status:** accepted for erasure ownership only
**Date:** 2026-08-03
**Issue:** #183. **Parent:** #179.
**Dependency:** projection-outbox foundation #180/#179 (migration 020,
`ADR-2026-08-03-projection-outbox-foundation.md`); lazy ADD COLUMN bootstrap race fix
#184/#187; erasure_audit VIEW race fix #182/#185.
**Does not touch:** Canon caller wiring, any dispatcher, retry/lease/acknowledgement,
TruthGate, PromotionGateway, ESM, L0/Ring Zero residual policy, the SQLite bootstrap
fixes from #185/#187.

## Context

`ADR-2026-08-03-projection-outbox-foundation.md` established `projection_outbox`
(migration 020) as an immutable, transaction-owned intent table, and explicitly deferred
one thing: *"No Canon caller may be wired until erasure/dependency handling for these
rows is added and tested."* This ADR is that increment — it does not wire any caller.

`SQLiteGraphStore.erase_fact_dependents_atomic()` already deletes every same-DB
dependent row for a `fact_id` (relations, provenance, mentions, versions, FTS, ...) as
one atomic transaction, and `same_db_dependents_present()` — sharing the exact same
`_SAME_DB_DEPENDENT_TABLES` registry, by design, so the two can never drift apart — is
the read-only residual check `core.erasure_coordinator._residual_data_present()` uses to
decide whether a job's terminal outcome can still be trusted. Before this change,
`projection_outbox` was absent from that registry: once a future Canon caller starts
appending intents, a fact's erasure would leave its outbox row behind untouched, and the
residual checker would have no way to notice.

## Decision

Add one entry to the existing shared registry:

```python
_SAME_DB_DEPENDENT_TABLES: tuple[tuple[str, str], ...] = (
    ...,
    ("projection_outbox", "aggregate_type = 'fact' AND aggregate_id = ?"),
)
```

`aggregate_type` is written as the literal `'fact'` rather than a second `?` — it is the
only value migration 020's own `CHECK` constraint permits today — so only `aggregate_id`
is bound to the fact being erased. Because this registry is already generically consumed
by both `erase_fact_dependents_atomic()`'s `_purge()` helper and
`same_db_dependents_present()`'s loop, this one entry gives `projection_outbox`, for
free and with no new code path:

- deletion inside the same single `BEGIN IMMEDIATE` transaction as `facts` and every
  other dependent (same atomicity, same rollback-on-any-failure guarantee already
  proven for the other nine tables);
- the deleted-row count surfacing in the existing `erase_fact_dependents_atomic()`
  receipt/`l1_same_db` step detail under `tables["projection_outbox"]`;
  no new receipt field was added;
- residual detection (`same_db_dependents_present()`) and, through it,
  `_residual_data_present()`/`is_erased()`/generation-reopening — a surviving or
  reappeared intent is treated exactly like a surviving `relations` or `fact_mentions`
  row already is.

### Rejected alternative: a dedicated outbox-specific erasure step

A new, separate erasure saga step (or a bespoke outbox-cleanup helper called alongside
`erase_fact_dependents_atomic()`) was considered and rejected: it would duplicate the
atomicity and residual-detection machinery this registry already provides for nine other
tables, for no behavioral gain, and would violate this issue's own
`NO_NEW_SAGA_STEP` boundary.

## Migration-020 gating: absence must be safe only pre-activation

A database that has never gone through `scripts/apply_migrations.py`
(`SQLiteGraphStore`'s bare runtime bootstrap alone) has no `projection_outbox` table at
all — the runtime lazy-DDL path in `_db()` does not create migration-020-only objects,
exactly as it does not create `relations` or `fact_mentions` (migrations 008/012). For
that database, `_table_exists()` returning `False` and the loop treating it as
`"not applicable"` is correct and unchanged.

But once the migration runner's own bookkeeping (`PRAGMA user_version`) claims migration
020 is applied (`>= 20`), the table's absence is no longer a legitimate "older install"
shape — it is corruption or out-of-band tampering. Silently reporting `"not applicable"`
in that case would let a completion tombstone be trusted while an outbox intent might
still (or again) exist. `same_db_dependents_present()` therefore special-cases exactly
this one table:

```python
if not self._table_exists(conn, table):
    if table == "projection_outbox" and self._migration_020_activated(conn):
        return True  # residual might be present — fail closed
    continue
```

`_migration_020_activated()` reads `PRAGMA user_version` and also fails closed (returns
`True`) if the read itself errors. This is the only place this ADR adds
schema-version-aware logic — deliberately not inside `erase_fact_dependents_atomic()`'s
per-table delete loop, which keeps reporting `{"applicable": False, "deleted": 0}`
honestly for every table regardless of why it is missing; residual/tombstone trust is
where the fail-closed enforcement belongs, and it is the only place that determines
whether an erasure is ever reported COMPLETE.

## Preserved semantics

- `aggregate_id = ?` scopes deletion/residual-checking to exactly the fact being erased
  — an outbox row for a *different* `aggregate_id` is never touched (proven by test).
- `aggregate_type = 'fact'` is not currently reachable with any other value (the
  migration's own `CHECK` constraint), so "a row of a different `aggregate_type` is
  left alone" is not independently testable today; the literal is written anyway so the
  WHERE clause's own intent matches the schema's, and remains correct if that constraint
  is ever relaxed.
- Ring Zero / `IMMUTABLE_FACT_IDS` protection in `erase_fact_dependents_atomic()` is
  untouched — the immutability check runs before any table (including
  `projection_outbox`) is ever touched.
- No Canon caller was added; no dispatcher was added; `core/projection_outbox.py`'s
  `append_projection_intent_in_transaction()` contract is unchanged.

## Failure behavior

No exception class is newly swallowed. A real DELETE failure on `projection_outbox`
(malformed schema, I/O, corruption) aborts the whole `erase_fact_dependents_atomic()`
transaction exactly like a failure on any other dependent table already does — proven by
forcing a real DB-level trigger failure on the subsequent `facts` DELETE (which always
runs after every `_SAME_DB_DEPENDENT_TABLES` entry, including this new one) and
confirming the fact row, the outbox row, and every other dependent all survive the
rollback together.

## Validation

- New: `tests/test_erasure_projection_outbox_dependency.py` — 9 focused tests covering:
  fact+intent removed together (unit-level and full saga); a real forced mid-transaction
  failure rolling back the fact, the outbox intent, and other dependents together;
  residual detection of a surviving orphaned intent; a reappeared intent after a COMPLETE
  erasure making that result untrusted and triggering a new generation that cleans it;
  Ring Zero protection unchanged; a pre-migration-020 database treating absence as not
  applicable; a `PRAGMA user_version >= 20` database with the table missing failing
  closed; rows for a different `aggregate_id` surviving untouched.
- RED confirmed on the unmodified baseline (`git stash` of the runtime change): 7/9 fail
  meaningfully (`KeyError: 'projection_outbox'`, or an assertion proving the missing
  registry entry never gets checked/deleted); the other 2 pass on the unmodified
  baseline because they assert pre-existing, unrelated invariants this change must not
  break — Ring Zero protection, and the `PRAGMA user_version >= 20` residual read
  itself failing closed on an unrelated `sqlite3.Error` path that predates this change.
- GREEN after the fix: 9/9 passed, repeated 25× with 0 failures.
- Combined suite (`test_erasure_coordinator.py`, `test_projection_outbox.py`,
  `test_projection_outbox_migration.py`, `test_migrations.py`, this file): 128 passed.
- Full erasure suite (10 files): 135 passed (unrelated pre-existing deprecation
  warnings only).
- SQLite resilience + lazy-add-column suites (`test_sqlite_store_resilience.py`,
  `test_sqlite_busy_timeout.py`, `test_sqlite_disk_full.py`,
  `test_sqlite_promotion_cas_contention.py`,
  `test_sqlite_lazy_add_column_concurrency.py`,
  `test_sqlite_lazy_add_column_error_classification.py`): 38 passed — confirms no
  interaction with #184/#187's ADD COLUMN fix.
- Architecture-freeze guard (`--base main`): PASS — no authority markers detected.
- Repository hygiene (`check_no_tracked_artifacts.py`): OK.
- Ruff (pinned `ruff==0.4.10`): PASS.
- Blocking mypy (pinned): PASS — no issues in 290 source files.
- Full repository `pytest tests/`: see PR body for the final pinned-head run.

## Interpretation boundary

**Proven:** atomic same-DB deletion of a `projection_outbox` row alongside its fact and
every other dependent; rollback of all three together on a genuine mid-transaction
failure; residual detection of a surviving or reappeared intent; fail-closed behavior
when migration bookkeeping claims the table should exist but it does not; scoping to
exactly one `aggregate_id`.

**Not proven / explicitly out of scope:** no Canon caller writes intents yet — this ADR
proves ownership of rows that do not exist in any current production path;
exactly-once delivery (not claimed, not attempted); dispatcher, lease, retry or
acknowledgement semantics (none exist); multi-row/batch outbox erasure beyond one
`aggregate_id` at a time; `aggregate_type` values other than `'fact'` (not currently
constructible); interaction with a future SubjectScope contract (unaddressed, per the
foundation ADR).

## Foundation status, restated

Per the foundation ADR, this subsystem remains:

```text
DESIGNED
IMPLEMENTED_IN_BRANCH  (erasure ownership, this increment)
MERGED_IN_MAIN         (pending merge of this PR)
```

Still not `RUNTIME_WIRED`, `FEATURE_ENABLED`, or `RUNTIME_OBSERVED`. No Canon path writes
an outbox row after this change either. Projection remains rebuildable and
non-authoritative; this increment only ensures that IF a row exists, erasure owns it —
same-DB, same transaction, same residual proof as every other dependent table.

## Merge gate

Architecture freeze, repository hygiene, Ruff, blocking mypy, the focused erasure/outbox
tests above, the full erasure suite, the migration-020 suite, the full repository pytest
suite, and standard GitHub CI/Docker must be green on one pinned final head, with zero
unresolved review threads. This PR remains Draft and unmerged until that gate passes and
merge is explicitly requested.

## Non-goals (unchanged from this issue's boundary)

- no Canon caller wiring;
- no dispatcher, worker, scheduler, lease, retry or acknowledgement;
- no new erasure saga step;
- no best-effort cleanup outside the shared atomic transaction;
- no change to L0/Ring Zero residual policy;
- no exactly-once claim;
- no change to ProjectionOutbox authority, TruthGate, PromotionGateway or ESM;
- no mixing with issue #179's future caller wiring;
- no change to the SQLite bootstrap fixes from PR #185/#187.
