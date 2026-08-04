# ADR — First Canon caller of the transactional projection outbox

**Status:** accepted for single-caller wiring only
**Date:** 2026-08-04
**Issue:** #191. **Parent:** #179.
**Dependency:** projection-outbox foundation #180/#179
(`ADR-2026-08-03-projection-outbox-foundation.md`); erasure/dependency ownership
#183/#188 (`ADR-2026-08-03-projection-outbox-erasure-dependency.md`); local scope
reference contract #189/#190 (`ADR-2026-08-04-local-projection-scope-reference.md`).
**Does not touch:** dispatcher, migration 020 schema, TruthGate, ESM, SubjectScope,
`PromotionGateway`'s public API/return contract.

## Context

`ADR-2026-08-03-projection-outbox-foundation.md`'s ordered increments named "first
single caller" as the next step after the foundation and erasure-ownership increments,
explicitly requiring: characterize one existing canonical mutation family, append the
intent in the same transaction as Canon + VersionStore + AuditChain, and prove both
directions of rollback — with no dispatcher yet.

A dedicated characterization pass (pre-work for this issue) confirmed:

- `SQLiteGraphStore._promote_to_validated_cas()` — the sole mutation
  `validate_and_promote()` performs — already runs the Canon CAS UPDATE, the
  VersionStore pre-image snapshot, and the AuditChain event on ONE shared
  `sqlite3.Connection`, inside one `with self._db() as conn:` transaction, before
  commit. Post-commit L0 publication happens after the block exits.
- `facts.fact_version` (migration 009) is bumped by the CAS UPDATE's own SET clause
  when the column exists, gated by the `bump_fact_version` trigger (fires only on
  `claim`/`confidence`/`epistemic_state` change — the promotion's own UPDATE always
  changes `epistemic_state`).
- `docs/operations/promotion-ownership-inventory.md` already documents five standard
  callers (`promotion_policy`, `consolidation_engine`, the PATCH endpoint,
  `tool_handlers`, `cognitive_store`) that all funnel through
  `PromotionGateway → validate_and_promote() → _promote_to_validated_cas()` — none
  bypass it. Wiring this one shared primitive is "one mutation family" exactly as the
  earlier characterization concluded, even though several existing adapters call it.
- `LOCAL_PROJECTION_SCOPE_REF = "local:primary"` (issue #189) closed the scope_ref
  blocker that had stopped this increment from starting.

## Decision

Inside `_promote_to_validated_cas()`'s existing transaction, strictly after the CAS
UPDATE has succeeded and after VersionStore's snapshot and AuditChain's event have both
succeeded — but before the `with self._db() as conn:` block exits (commit) — read the
just-written `facts.fact_version` on the SAME `conn` and append one `ProjectionIntent`:

```python
canonical_version = conn.execute(
    "SELECT fact_version FROM facts WHERE fact_id = ?", (fact_id,),
).fetchone()[0]

append_projection_intent_in_transaction(
    conn,
    ProjectionIntent(
        aggregate_id=fact_id,
        scope_ref=LOCAL_PROJECTION_SCOPE_REF,
        canonical_version=canonical_version,
        projection_kind=ProjectionKind.ALL,
        operation=ProjectionOperation.REFRESH,
    ),
)
```

`canonical_version` is never assumed, precomputed, or derived from a timestamp/row
count — it is read from the durable row this same transaction just wrote, on the same
connection, before commit.

## Activation gating

```text
PRAGMA user_version >= 20 (migration 020 activated)
├── projection_outbox exists AND facts.fact_version exists
│   → append the intent; any append failure rolls back everything
├── projection_outbox missing
│   → ProjectionOutboxActivationError, full rollback (fail closed)
└── facts.fact_version missing
    → ProjectionOutboxActivationError, full rollback (fail closed)

PRAGMA user_version < 20 (not activated)
→ no-op — promotion behaves exactly as before this ADR, never labeled outbox-backed

PRAGMA read itself fails
→ propagates, full rollback (fail closed by construction — no special-case needed)
```

`ProjectionOutboxActivationError(RuntimeError)` is a new, specific exception (in
`core/memory.py`, alongside `TriggerReconstructionError`): an activated database
(`user_version >= 20`) missing either required object is a schema-inconsistency, never
a legitimately older/unmigrated database — the same distinction
`ADR-2026-08-03-projection-outbox-erasure-dependency.md` already drew for
`same_db_dependents_present()`'s residual check, now applied to the write path too.
Raising inside the transaction is sufficient for fail-closed behavior: `_db()`'s own
`except Exception: conn.rollback(); raise` undoes the Canon UPDATE, the VersionStore
snapshot, and the AuditChain event together — no separate rollback logic was needed.

### Why gate in the write path at all, not only the read-side residual check

Issue #183 already fails closed on the *read* side (residual/tombstone trust) when
`projection_outbox` is missing on an activated database. This ADR adds the matching
*write*-side guard: without it, an activated database missing the table could still
accept promotions that silently skip the required intent, and issue #183's own
read-side check would have nothing to report residual about — the intent would simply
never have existed. Gating at the point of mutation is the only way to make "no silent
outbox-backed promotion without its intent" actually true.

## Rejected alternatives

- **Best-effort append after commit** — rejected outright by this issue's own
  boundary (`SAME_SQLITE_TRANSACTION`) and by the foundation ADR's atomicity proof: a
  post-commit append could observe a promotion that "succeeded" with no intent on a
  crash between commit and append, exactly the class of bug the whole outbox exists to
  prevent.
- **A second database connection for the outbox append** — rejected: breaks the
  same-transaction guarantee entirely; `append_projection_intent_in_transaction()`
  itself already refuses a connection with no active transaction.
- **Silently skipping the intent when `fact_version` is absent, even on an activated
  DB** — rejected: this is exactly the "no silent table-missing success after schema
  version 20" principle from issue #183, extended to `fact_version`. An activated
  database is asserting these objects exist; silently working around their absence
  would hide a real inconsistency.
- **A new global feature flag for outbox activation** — rejected: `PRAGMA user_version`
  is already the project's own migration-activation signal (used identically in
  #183); a second, parallel flag would be redundant and could disagree with it.

## Preserved semantics

- `PromotionGateway`'s public API and `TruthGateVerdict` contract are unchanged — no
  new field, no delivery acknowledgement returned to callers.
  `ProjectionAppendReceipt` (the outbox's own internal receipt) is never surfaced as
  proof of delivery.
- The five existing standard callers documented in
  `docs/operations/promotion-ownership-inventory.md` are unmodified — they all still
  call `validate_and_promote()` exactly as before; the outbox append is entirely
  internal to the shared primitive underneath them.
- An intent is created ONLY on a genuinely new, committed promotion — never on
  TruthGate rejection, CAS loss (`concurrent_modification`), `already_validated`,
  missing fact, illegal ESM transition, VersionStore failure, or AuditChain failure
  (all of these either return before `_promote_to_validated_cas()` is even called, or
  return `False`/raise before the new gating code is reached).
- CAS contention: exactly one winner still produces exactly one Canon mutation, one
  VersionStore row, one AuditChain event, and now exactly one intent — proven at 2, 10,
  and 25 concurrent contenders. A post-race retry still resolves to
  `already_validated` and creates no second intent.
- Issue #183's erasure ownership requires no changes: a real intent created by a real
  promotion is deleted by `erase_fact_dependents_atomic()` exactly like any other
  `projection_outbox` row, proven directly (not just inferred) in this increment's own
  tests.

## Failure behavior

No exception class is newly swallowed. A real failure appending the outbox row (proven
with a genuine `BEFORE INSERT ON projection_outbox ... RAISE(ABORT, ...)` trigger)
rolls back the Canon UPDATE, the VersionStore snapshot, and the AuditChain event
together. The reverse directions were already proven by existing tests and re-confirmed
here: a VersionStore failure or an AuditChain failure both roll back the Canon UPDATE
and (now) prevent any intent from ever being appended, since the outbox code runs after
both in transaction order.

## Validation

- New file: `tests/test_promotion_projection_outbox_caller.py` — 13 tests:
  - successful promotion: Canon + VersionStore + AuditChain + exactly one intent, with
    `canonical_version` matching the durable `facts.fact_version`;
  - a real outbox INSERT trigger failure rolls back Canon + VersionStore + AuditChain
    together, then a clean retry succeeds;
  - a real VersionStore (`fact_versions`) INSERT trigger failure rolls back Canon and
    prevents any intent;
  - a real AuditChain (`memory_events`) INSERT trigger failure rolls back Canon +
    VersionStore and prevents any intent;
  - TruthGate rejection creates no intent;
  - `already_validated` creates no new version, audit event, or intent;
  - CAS contention at 2, 10, and 25 concurrent contenders: exactly one winner, exactly
    one intent, correct `canonical_version`, post-race retry stays
    `already_validated` with no second intent;
  - a pre-migration-020 database promotes unchanged, with no `projection_outbox`
    table involved at all;
  - an activated database (`user_version >= 20`) missing `projection_outbox` fails
    closed — Canon rolls back;
  - an activated database missing `facts.fact_version` (column AND its
    `bump_fact_version` trigger both absent, matching a genuine "migration 009 never
    ran" shape rather than an orphaned-trigger side effect) fails closed;
  - a real intent created by a real promotion is removed by
    `erase_fact_dependents_atomic()`.
- `PRAGMA integrity_check = ok` asserted after every scenario above.
- RED confirmed against the unmodified baseline: 10/13 failed for the expected reason
  (no outbox wiring existed yet); 3 passed because they assert pre-existing, unrelated
  invariants (VersionStore-failure rollback, TruthGate rejection, pre-v20 behavior)
  this change must not break.
- GREEN after the fix: 13/13 passed, repeated **25×** with 0 failures (no
  sleep-based synchronization anywhere — CAS contention uses a
  `threading.Barrier`-gated proxy on `_promote_to_validated_cas` itself, the same
  deterministic technique `tests/test_sqlite_promotion_cas_contention.py` already
  established).
- Regression suites, all green: `test_sqlite_promotion_cas_contention.py`,
  `test_promotion_policy.py`, `test_promotion_gateway.py`,
  `test_p0d_truthgate_enforcement.py`, `test_truthgate_api_transition.py`,
  `test_audit_chain_transition_ledger.py`, `test_audit_chain_lifecycle_paths.py` (134
  passed); `test_version_store_temporal_consistency.py`, `test_projection_outbox.py`,
  `test_projection_outbox_migration.py`, `test_erasure_projection_outbox_dependency.py`,
  `test_erasure_coordinator.py`, `test_erasure.py` (167 passed); every Ring Zero test
  across the repository (15 passed); `test_promotion_ownership_guard.py` (2 passed,
  unaffected — no new direct caller of `validate_and_promote()`/`promote_to_validated()`
  was introduced).
- Architecture-freeze guard (`--base main`): PASS — no authority markers detected.
- Repository hygiene (`check_no_tracked_artifacts.py`): OK.
- Ruff (pinned `ruff==0.4.10`): PASS.
- Blocking mypy (pinned): PASS — no issues in 290 source files.
- Full repository pytest, CI, Docker: see the PR body for this increment's real,
  verified results.

## Interpretation boundary

**Proven:** a successful single-fact promotion appends exactly one durable, correctly
versioned intent in the same transaction as Canon/VersionStore/AuditChain; any failure
anywhere in that transaction (Canon, VersionStore, AuditChain, or the outbox append
itself) rolls back all of it; no intent is ever created on a non-mutating outcome;
exactly-one-winner CAS contention still holds at 25 concurrent contenders and now also
produces exactly one intent; activation gating fails closed rather than silently
promoting without a required intent; a real intent is genuinely removed by existing
erasure ownership.

**Not proven / explicitly out of scope:** no dispatcher exists — nothing reads, claims,
leases, retries, or applies these intents; no exactly-once delivery is claimed, only
exactly-one committed Canon mutation under tested contention; no other mutation family
(compound supersede, contradiction/deprecation/collapse, invalidation, relation
lifecycle, Ring Zero, curated World Skills ingest) is wired; no SubjectScope or
multi-user activation; no change to migration 020's schema.

## Relationship to #179, #183, #189

This is the "first single caller" increment #179 itself names. It builds directly on
#183's shared same-DB dependent registry (no changes needed there — the erasure path
already owns whatever `projection_outbox` rows exist) and on #189's
`LOCAL_PROJECTION_SCOPE_REF` (the only scope_ref this increment ever uses). The
dispatcher increment #179 also names remains separate and later.

## Merge gate

Architecture freeze, repository hygiene, Ruff, blocking mypy, the promotion ownership
guard, the focused suites above, the full repository pytest suite, and standard GitHub
CI/Docker must be green on one pinned final head, with zero unresolved review threads.
This PR remains Draft and unmerged until that gate passes and merge is explicitly
requested. Issue #179 is not closed by this PR — only #191 is.

## Non-goals

- no dispatcher, worker, scheduler, lease, claim, or acknowledgement;
- no projection application, no remote transport, no exactly-once delivery claim;
- no compound supersede integration;
- no TruthGate or ESM changes;
- no `migrations/020_projection_outbox.sql` change;
- no SubjectScope or multi-user activation;
- no broad `core/memory.py` refactor.
