# ADR — Eliminate concurrent erasure_audit VIEW bootstrap race

**Status:** accepted for evidence collection only
**Date:** 2026-08-03
**Dependency:** SQLite resilience #174, bounded busy timeout #175, disk-full rollback
#176, single-winner promotion CAS #177, post-race idempotency #181 (issue #178).
**Fixes:** issue #182. **Explicitly does not fix:** issue #184.

## Context

`SQLiteGraphStore._db()`'s lazy schema bootstrap performs, unconditionally on every
first use of a given `db_path` per instance:

```sql
DROP VIEW IF EXISTS erasure_audit;
CREATE VIEW erasure_audit AS ...;
```

guarded only by the per-**instance** `self._ddl_initialized_paths` set — never shared
across independent `SQLiteGraphStore` instances, connections, or processes. Two fresh
instances against the same database file can interleave:

```text
A: DROP VIEW IF EXISTS erasure_audit
B: DROP VIEW IF EXISTS erasure_audit
A: CREATE VIEW erasure_audit ...  -> success
B: CREATE VIEW erasure_audit ...  -> OperationalError: view erasure_audit already exists
```

This was discovered while developing PR #181 (issue #178) and characterized on branch
`agent/erasure-audit-ddl-bootstrap-race` (commit
`58b20d950a915813c9bdbc4e7f6d63ee9589e9bc`), filed as issue #182.

### A second, independent defect was found during characterization — not fixed here

The same investigation's barrier-gated harness, when gated on *any* statement (not
specifically the VIEW boundary), also intermittently hit:

```text
sqlite3.OperationalError: duplicate column name: audit_subject_id
sqlite3.OperationalError: duplicate column name: derived_from
```

Root cause: the same lazy bootstrap block guards **nine** separate
`ALTER TABLE ... ADD COLUMN` statements (`facts.history`,
`facts.t_event_valid_start`/`_end`, `facts.t_ingestion_start`/`_end`,
`facts.audit_subject_id`, `facts.claim_type`, `facts.origin_type`,
`facts.derived_from`, `erasure_log.job_id`) with a **Python-side**
`PRAGMA table_info(...) → membership check → ALTER TABLE` sequence — the identical
structural flaw (per-instance guard, no cross-connection protection) as the VIEW race,
just on different statements/tables. This is a genuinely separate defect family and is
tracked independently as **issue #184**. It is explicitly out of scope for this PR — see
"Scope boundary" below for how this PR's own regression test avoids exercising it.

## Decision

### Minimal fix (Вариант A from issue #182)

Change exactly one statement:

```diff
-CREATE VIEW erasure_audit AS
+CREATE VIEW IF NOT EXISTS erasure_audit AS
```

`DROP VIEW IF EXISTS erasure_audit` is unchanged.

### Why this is sufficient without a broader lock

The view's definition **has** evolved historically — migration 012 created it without
the correction-aware `COALESCE`, and migration 016 later redefined it with
`COALESCE(c.corrected_user_id, el.user_id)`. This confirms `CREATE VIEW IF NOT EXISTS`
alone, WITHOUT the preceding `DROP`, would be unsafe in general: it would silently keep
whatever (possibly stale) definition already existed, never upgrading it. That is not
what this fix does. The `DROP VIEW IF EXISTS` stays exactly where it was, so every
**single, uncontested** call still unconditionally replaces the view with the current
Python-embedded (migration-016-equivalent) definition — upgrade behavior is fully
preserved for the ordinary, sequential case.

The only behavior that changes is under genuine **concurrent** contention at the CREATE
boundary specifically:

```text
A: DROP VIEW IF EXISTS erasure_audit
B: DROP VIEW IF EXISTS erasure_audit
A: CREATE VIEW IF NOT EXISTS erasure_audit ...  -> creates it
B: CREATE VIEW IF NOT EXISTS erasure_audit ...  -> sees it already exists (A's just-
                                                    committed one) -> silent no-op,
                                                    not an exception
```

and symmetrically for `A`/`B` swapped, and for the interleaving where one contender's
`DROP` removes the *other* contender's freshly-created view before that contender's own
`CREATE` — the final state is unaffected either way, because both contenders execute the
exact same statement text (this repository ships one canonical view definition, not
per-caller variants), so whichever one's `CREATE` actually runs last produces an
identical result to either one running alone.

A broader, whole-bootstrap serialization lock was deliberately **not** used —
issue #182 explicitly requires not expanding any lock to the general schema bootstrap
(that could incidentally paper over or change issue #184's separate, still-open ADD
COLUMN race, which must remain independently reproducible and fixed on its own terms).

## Preserved semantics

- `erasure_audit` columns, order and types: unchanged
  (`erasure_id, fact_id, user_id, reason, claim_hash, erased_at, request_ref`).
- Correction-aware resolution: unchanged — `COALESCE(c.corrected_user_id, el.user_id)
  AS user_id`, joined via `LEFT JOIN erasure_log_subject_corrections c ON
  c.erasure_id = el.erasure_id`.
- `ORDER BY el.erased_at DESC`: unchanged.
- Append-only triggers on `erasure_log` / `erasure_log_subject_corrections`: untouched.
- `facts` / `erasure_log` columns, migrations, `PromotionGateway`, `TruthGate`, the
  transactional outbox (migration 020) and busy-timeout/WAL/synchronous policy: all
  untouched.

## Failure behavior

No exception type is swallowed. A `duplicate column name` error (issue #184's family)
is explicitly asserted to be **absent** from this PR's regression evidence rather than
silently tolerated — if it appeared, that would mean this PR's test isolation had
failed, not that issue #182 was fixed. Any other `sqlite3.OperationalError`
(malformed schema, permission failure, disk I/O, `SQLITE_FULL`, corruption, an
incompatible existing view) still propagates uncaught through the unchanged `_db()`
context manager, exactly as before this change.

## Validation

- A regression test (`tests/test_erasure_audit_view_bootstrap_race.py`) seeds a
  database's schema **completely**, sequentially, through one ordinary store
  (`ensure_schema()`) before racing any contender — every `ALTER TABLE ADD COLUMN`
  check a racer's own first-use bootstrap performs then sees its column already
  present and takes no write action, so issue #184's family cannot fire inside this
  test. Only the unconditional `DROP`/`CREATE VIEW` pair remains exercised by fresh
  contenders.
- A test-only connection proxy pauses each contender on a shared `threading.Barrier`
  immediately before a statement matching the `erasure_audit` CREATE boundary (matching
  either `CREATE VIEW erasure_audit ...` or, after this fix,
  `CREATE VIEW IF NOT EXISTS erasure_audit ...`) — `DROP VIEW IF EXISTS erasure_audit`
  is never gated, and no SQL is rewritten, no exception is hidden, and the proxy never
  creates/drops the view or substitutes commit/rollback itself.
- RED (unmodified baseline): 2/5/10-contender parametrized runs all reproduced
  `sqlite3.OperationalError: view erasure_audit already exists` — and, critically,
  *only* that error; no `duplicate column name` leaked through, confirming the
  seeded-schema isolation from issue #184 works.
- GREEN (this fix): the same test, 2/5/10 contenders, 50 full-file repeats: 0 failures.
- The combined SQLite suite (`test_sqlite_store_resilience.py`,
  `test_sqlite_busy_timeout.py`, `test_sqlite_disk_full.py`,
  `test_sqlite_promotion_cas_contention.py`) — which, before this fix, intermittently
  hit this exact race at roughly 30-80% failure rates across repeated batches when run
  together in one session (see PR #181's report) — ran 25/25 times with 0 failures
  after this fix.

## Interpretation boundary

### What this proves

- Cross-connection safety for the specific `erasure_audit` DROP/CREATE pair, under real
  concurrent threads with independent SQLite connections against one file-backed
  database, in this repository's default (non-WAL-pinned-elsewhere for this path)
  configuration, at 2/5/10-way contention.
- The view's projection semantics (correction-aware `user_id` resolution) are
  unaffected by the fix.
- `PRAGMA integrity_check = ok` before and after contention, in both the freshly-seeded
  and already-bootstrapped-then-re-raced scenarios.
- Append-only erasure triggers survive concurrent bootstrap unchanged.

### What this does NOT prove

- Issue #184's separate `ALTER TABLE ADD COLUMN` race — deliberately excluded from this
  PR's scope and test isolation; remains open and independently reproducible.
- Correctness on network filesystems.
- Distributed locking across separate machines/processes beyond real OS threads in one
  process.
- Recovery from physical disk corruption.
- Any future DDL migration's interaction with this specific `IF NOT EXISTS` mechanism —
  a future schema change to this view would need its own review of whether `DROP` +
  `CREATE IF NOT EXISTS` remains the right idempotency strategy.
- Unlimited concurrency (2/5/10 contenders were exercised, not an arbitrary N).
- Absence of every possible SQLite race in this codebase — only the one issue #182
  names.
- Transactional outbox atomicity (untouched by this PR).

## Merge gate

This PR remains draft until the permanent regression test, architecture freeze,
repository hygiene, Ruff, blocking mypy and the full repository pytest suite pass on one
pinned final head. Docker: `REQUIRED` and `PASS` for PR #185 because `core/memory.py`
matches the workflow's `core/**` `pull_request.paths` filter in
`.github/workflows/docker.yml` — Docker run #414 completed successfully (build, runtime
smoke tests and hardening checks all passed) for this PR's pinned final head.

## Follow-up

Issue #184 (`PRAGMA table_info → ALTER TABLE ADD COLUMN` race) remains open and is an
independent, separately-scoped fix. It is not touched, weakened, or accidentally
resolved by this PR.
