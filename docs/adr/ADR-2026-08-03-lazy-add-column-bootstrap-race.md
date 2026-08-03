# ADR — Eliminate concurrent lazy ADD COLUMN bootstrap races

**Status:** accepted for evidence collection only
**Date:** 2026-08-03
**Dependency:** SQLite resilience #174, bounded busy timeout #175, disk-full rollback
#176, single-winner promotion CAS #177, post-race idempotency #181 (issue #178),
erasure_audit VIEW race fix #185, its Copilot follow-up #186 (issue #182).
**Fixes:** issue #184. **Does not touch:** issue #182's VIEW fix, PromotionGateway,
TruthGate, ESM, the transactional outbox (migration 020).

## Context

`SQLiteGraphStore._db()`'s lazy schema bootstrap performs a Python-side check-then-act
upgrade for several columns:

```python
existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()}
for col in (...):
    if col not in existing_cols:
        conn.execute(f"ALTER TABLE facts ADD COLUMN {col} ...")
```

guarded only by the per-**instance** `self._ddl_initialized_paths` set — never shared
across independent `SQLiteGraphStore` instances, connections, or processes. Two fresh
instances can both read the same pre-alter `PRAGMA table_info` snapshot, both decide a
column is absent, and then race the same `ALTER TABLE ... ADD COLUMN`:

```text
A: PRAGMA table_info(facts) -> audit_subject_id absent
B: PRAGMA table_info(facts) -> audit_subject_id absent
A: ALTER TABLE facts ADD COLUMN audit_subject_id ...  -> success
B: ALTER TABLE facts ADD COLUMN audit_subject_id ...  -> OperationalError:
                                                          duplicate column name
```

This was discovered while characterizing issue #182 on branch
`agent/erasure-audit-ddl-bootstrap-race` (commit
`58b20d950a915813c9bdbc4e7f6d63ee9589e9bc`) and filed as issue #184, kept deliberately
separate from #182's `erasure_audit` VIEW race (a different statement, fixed
independently in PR #185).

### Why the per-instance guard is insufficient

`_ddl_initialized_paths` only remembers, within one Python object, whether *this*
instance has already run its bootstrap block for a given `db_path`. It says nothing
about what any *other* instance — a different `SQLiteGraphStore()` object, in the same
process or a different one — has already done to the same underlying file. Two
instances opened close together both see "not yet initialized" locally and both attempt
the same real ALTER.

## Investigation: affected check-and-add paths

| Table | Column | ALTER DDL (as issued) | In current `CREATE TABLE IF NOT EXISTS`? | Fires on virgin DB? | Migration origin |
|---|---|---|---|---|---|
| `facts` | `history` | `TEXT DEFAULT NULL` | yes | no (legacy-only) | pre-v9 bi-temporal work |
| `facts` | `t_event_valid_start` | `TEXT DEFAULT NULL` | yes | no (legacy-only) | I96 bi-temporal (V9 Sprint 1) |
| `facts` | `t_event_valid_end` | `TEXT DEFAULT NULL` | yes | no (legacy-only) | I96 bi-temporal |
| `facts` | `t_ingestion_start` | `TEXT DEFAULT NULL` | yes | no (legacy-only) | I96 bi-temporal |
| `facts` | `t_ingestion_end` | `TEXT DEFAULT NULL` | yes | no (legacy-only) | I96 bi-temporal |
| `facts` | `audit_subject_id` | `TEXT DEFAULT NULL` | **no** | **yes** | PR-C2 audit chain wiring |
| `facts` | `claim_type` | `TEXT NOT NULL DEFAULT 'UNKNOWN'` | yes | no (legacy-only) | v8.7 P0 claim-type spec |
| `facts` | `origin_type` | `TEXT NOT NULL DEFAULT 'UNKNOWN'` | yes | no (legacy-only) | v8.7 P0 claim-type spec |
| `facts` | `derived_from` | `TEXT DEFAULT NULL` | **no** | **yes** | TASK-09 (l0_raw_memory linkage) |
| `erasure_log` | `job_id` | `TEXT DEFAULT NULL` | yes | no (legacy-only) | migration 014 |

Callers: all ten reads/writes happen only inside `SQLiteGraphStore._db()`'s own lazy
bootstrap block; no other module performs a check-and-add against these tables.

Two columns (`audit_subject_id`, `derived_from`) are **not** part of the current
`CREATE TABLE IF NOT EXISTS facts (...)` statement, so their `ALTER TABLE` fires
unconditionally even for a brand-new database — this is exactly why the original
five-contender virgin-DB harness (issue #182's investigation) observed races only on
these two. The other seven columns are already included in the fresh `CREATE TABLE`
and `erasure_log` statements, so their `ALTER TABLE` only ever fires against a genuinely
pre-existing database whose schema predates that column's addition (a "legacy upgrade"
scenario) — reproducing their race requires simulating such a database, not a virgin
one.

The check-then-add logic is structurally identical across all ten columns (same
`PRAGMA table_info` → membership check → `ALTER TABLE ADD COLUMN` shape, differing only
in table/column/type/`NOT NULL`/default), so it safely reduces to one small,
parameterized helper rather than ten independent fixes or a new migration-versioning
layer.

## Decision

### Minimal fix (Вариант A: narrow benign-duplicate recovery)

New helper, `core/memory.py::_safe_add_column_if_missing()`, replaces the raw
`conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} ...")` call at all five call
sites (the six-column loop, `claim_type`, `origin_type`, `derived_from`,
`erasure_log.job_id`) — the surrounding `if column not in existing_cols:` fast-path gate
is unchanged:

```python
try:
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
    return
except sqlite3.OperationalError as exc:
    if f"duplicate column name: {column}" not in str(exc):
        raise
# authoritative re-check, never assumed
row = next((r for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
            if r[1] == column), None)
if row is None:
    raise RuntimeError(...)
_cid, _name, decl_type, notnull, dflt_value, pk = row
if decl_type != sql_type or notnull != expected_notnull or dflt_value != default_literal or pk != 0:
    raise RuntimeError(...)
```

### Why this is cross-connection safe

The fast-path `existing_cols` check (taken from a `PRAGMA table_info` snapshot before
this call) can be stale for the same TOCTOU reason as before — that is unchanged and
unavoidable without redesigning the whole bootstrap's transaction boundaries, which
issue #184 explicitly rules out (`NO_GLOBAL_BOOTSTRAP_LOCK`). What changes is what
happens when the snapshot *was* stale: instead of letting SQLite's own
`duplicate column name` error propagate as a bootstrap failure, the helper recognizes
**exactly** that one error, for **exactly** the column it was trying to add, and then
re-reads the *authoritative*, current `PRAGMA table_info(table)` — not the earlier
snapshot — to confirm the column that actually exists now is name-for-name,
type-for-type, `NOT NULL`-for-`NOT NULL`, and default-for-default identical to what this
call itself would have created. Only then is the race treated as benign. Any mismatch —
wrong type, wrong nullability, wrong default, or the column vanishing entirely between
the failed `ALTER` and the re-read (a scenario that should be impossible given SQLite's
own atomicity per statement, but is not assumed away) — raises `RuntimeError` instead of
silently proceeding.

### Why the broader alternatives were not used

- **Вариант B (cross-connection serialization via `BEGIN IMMEDIATE`)**: would work, but
  is strictly more machinery than needed here. Unlike issue #182's VIEW fix (where
  `DROP`+bare `CREATE` has no SQL-level idempotent form at all), SQLite's own
  `duplicate column name` error IS a reliable, narrow signal that a concurrent adder won
  the race — Variant A only needs to interpret that signal correctly and verify it, not
  prevent the race from ever being attempted. Adding an explicit lock around ten
  Ⓐ call sites for a benign, already-detectable race is unnecessary surface area.
- **Вариант C (versioned migration boundary)**: explicitly reserved for cases where A/B
  cannot be made correct within the current lifecycle. Not needed here.

## Strict verification (fail-closed contract)

After a recognized benign duplicate, the helper checks, from `PRAGMA table_info`'s own
authoritative row: column name, declared type, `NOT NULL` flag, default literal, and
primary-key flag. These four checks together cover every property the original `ALTER
TABLE ADD COLUMN ...` statement would itself have declared. Never subsumed or weakened:
any other `sqlite3.OperationalError` (malformed schema, permission denial, disk I/O,
`SQLITE_FULL`, corruption, a syntax error, the wrong table, a duplicate reported for a
*different* column than the one being added, or an incompatible pre-existing column
definition) still propagates uncaught, exactly as before this change.

## Preserved semantics

Column meanings, SQL types, defaults and nullability are byte-for-byte unchanged from
what the original bare `ALTER TABLE` statements declared — the helper only wraps the
*execution* of those same statements, it does not alter what they declare. One
pre-existing quirk is deliberately left untouched (out of scope, not this issue's
concern): the fresh `CREATE TABLE` path defaults `facts.history` to `'[]'`, while the
legacy-upgrade `ALTER TABLE ... ADD COLUMN history TEXT DEFAULT NULL` path defaults it
to `NULL` — a divergence that predates this fix and is not a column-semantics change
introduced here.

## Legacy upgrade coverage

Seven of the ten guarded columns only ever exercise their `ALTER TABLE` against a
database that predates that column — this fix's regression test builds representative
legacy fixtures (a `facts`/`erasure_log` table with every current column present except
one target column) to exercise those paths directly, rather than relying on incidental
coverage from a virgin-database race.

## Validation

- RED (unmodified baseline, `main@7ecba30`): 18/18 parametrized cases (6 representative
  columns — `facts.audit_subject_id`, `facts.derived_from` on a virgin database;
  `erasure_log.job_id`, `facts.t_ingestion_start`, `facts.history`, `facts.claim_type` on
  representative legacy-schema fixtures — × 2/5/10 contenders) deterministically
  reproduced `sqlite3.OperationalError: duplicate column name: <column>`, and *only*
  that error for the exact column under test; no unrelated failure (no VIEW race, no
  broken barrier, no timeout, no `SQLITE_FULL`) leaked through.
- GREEN (this fix): the same 18 cases, 50 full-file repeats: 0 failures.
- Combined suite (`test_sqlite_store_resilience.py`, `test_sqlite_busy_timeout.py`,
  `test_sqlite_disk_full.py`, `test_sqlite_promotion_cas_contention.py`,
  `test_erasure_audit_view_bootstrap_race.py`,
  `test_sqlite_lazy_add_column_concurrency.py`) × 25: 0 failures.
- Issue #182's own regression suite (`test_erasure_audit_view_bootstrap_race.py`) and
  post-race idempotency assertions (`test_sqlite_promotion_cas_contention.py`) both
  still pass unmodified — this fix does not touch the VIEW race or its fix.
- `test_projection_outbox.py` / `test_projection_outbox_migration.py` (migration 020)
  unaffected.
- Erasure suites (228 tests), migration suites (17 tests): unaffected.
- `PRAGMA integrity_check = ok` before and after every concurrent bootstrap scenario.

## Interpretation boundary

### What this proves

- Cross-connection safety for all ten guarded `PRAGMA table_info → ALTER TABLE ADD
  COLUMN` paths, under real concurrent threads with independent SQLite connections
  against one file-backed database, at 2/5/10-way contention, for both virgin-schema and
  representative legacy-schema starting states.
- Exact schema verification: a benign race never silently accepts an incompatible
  column definition.
- `PRAGMA integrity_check = ok` throughout; no unrelated schema object lost; append-only
  triggers and the `erasure_audit` VIEW remain intact after concurrent bootstrap.
- Idempotency: a second concurrent bootstrap round against an already-upgraded database
  adds nothing further.

### What this does NOT prove

- Network filesystems.
- Distributed locking across separate machines/processes beyond real OS threads in one
  process.
- Arbitrary future migrations' interaction with this exact helper.
- Unlimited concurrency (2/5/10 contenders were exercised, not an arbitrary N).
- Recovery from physical disk corruption.
- Absence of every possible SQLite DDL race in this codebase — only the ten paths issue
  #184 names.
- Issue #182's VIEW race or its fix (untouched, separately owned).
- Transactional outbox atomicity (untouched by this PR).

## Relationship to issue #182 and PRs #185/#186

Issue #182 (the `erasure_audit` VIEW race) was fixed independently in PR #185, with a
documentation follow-up in PR #186 addressing post-merge Copilot review comments.
Neither this fix nor its regression test modifies `tests/test_erasure_audit_view_bootstrap_race.py`,
`docs/adr/ADR-2026-08-03-erasure-audit-view-bootstrap-race.md`, or the one-line
`CREATE VIEW IF NOT EXISTS` change in `core/memory.py` from that work — this PR's own
combined-suite validation re-runs that regression test unmodified to confirm no
interaction.

## Merge gate

This PR remains draft until the permanent regression test, architecture freeze,
repository hygiene, Ruff, blocking mypy and the full repository pytest suite pass on one
pinned final head. Docker is scheduled and required whenever the diff touches
`core/memory.py` (matching `.github/workflows/docker.yml`'s `core/**` path filter, per
the lesson recorded in PR #185's Copilot follow-up) — its result is reported in the PR,
not assumed.
