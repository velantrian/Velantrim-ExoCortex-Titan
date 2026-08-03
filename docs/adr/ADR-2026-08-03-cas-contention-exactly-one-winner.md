# ADR — Characterize `validate_and_promote()` CAS contention with exactly one winner

**Status:** accepted for evidence collection only
**Date:** 2026-08-03
**Dependency:** SQLite concurrency/crash baseline #174, bounded busy timeout #175, disk-full
rollback #176 (issue #178)

## Context

Prior storage increments proved bounded concurrent writes (#174), bounded lock-wait
failure (#175), and connection-scoped capacity-failure rollback (#176). None of them
put two real, independent contenders through the same single-fact promotion authority
at the same time.

`SQLiteGraphStore.validate_and_promote()` is the single canonical, TruthGate-backed
entry point for promoting a fact to `Validated` from an external/untrusted caller
(`PATCH /facts/{fact_id}/transition`). Its guarded write
(`_promote_to_validated_cas()`) commits via one atomic conditional
`UPDATE ... WHERE fact_id=? AND epistemic_state=? AND updated_at=?` against the exact
durable snapshot TruthGate evaluated — no intermediate re-read. This has an existing
adversarial regression suite
(`tests/test_truthgate_api_transition.py::TestValidateAndPromoteConcurrencyGuard`), but
every race in that suite is **asymmetric**: one validator thread against a monkeypatched
pause point on ONE shared `SQLiteGraphStore` instance, racing against a *different*
mutation (a weakening upsert, a deletion, or a direct `transition_esm()` call that
bypasses TruthGate entirely). None of them race two genuinely independent connections
both attempting `validate_and_promote()` itself.

Issue #178 asks for the **symmetric** case: several real, independent
`SQLiteGraphStore` instances (separate Python objects, each holding its own persistent
`sqlite3.Connection`, per #174's "N independent instances, one file-backed WAL database"
precedent) all read the same durable pre-mutation snapshot and reach the CAS boundary
in close proximity.

## Decision

Add a permanent test
(`tests/test_cas_contention_exactly_one_winner.py`) that:

1. seeds one fact in `Supported` with confidence/evidence strong enough to pass
   TruthGate under `CognitiveMode.BALANCED` (confidence 0.85, 2 evidence refs — the same
   thresholds `test_truthgate_api_transition.py` already documents and relies on);
2. records baseline `fact_versions` count (fact-scoped) and `memory_events` count
   (whole-table — this specific path's audit append does not carry a `fact_id`, see
   "What is proven" below) on a fresh, uninvolved connection, plus a baseline
   `PRAGMA integrity_check`;
3. constructs 5 independent `SQLiteGraphStore` instances against the same file-backed
   database and forces each one's lazy schema bootstrap
   (`SQLiteGraphStore.ensure_schema()`) sequentially, before any thread starts — see
   "Observed but out of scope" below for why this step is necessary and deliberate;
4. wraps each instance's own `_promote_to_validated_cas` in a test-only seam that waits
   on a shared `threading.Barrier(5)` immediately before delegating, unmodified, to the
   real method — the same pause-then-delegate pattern
   `test_truthgate_api_transition.py::_run_cas_race()` already uses for its one-racer
   case, generalized to five. The seam never fakes a rowcount, never mutates state
   itself, and only pins the exact moment after each contender's own durable read +
   `TruthGate.evaluate()` and before its own guarded write;
5. runs all five contenders as real `threading.Thread`s and collects each one's
   `TruthGateVerdict`;
6. asserts exactly one `passed=True` verdict with `reason == "passed"`, and that every
   other contender has `passed=False` with `reason == "concurrent_modification"` —
   never `"already_validated"` during the race itself, since every contender's durable
   read happened before any of them had committed;
7. asserts the final fact is `Validated`, durable, and visible from a brand-new,
   previously uninvolved store instance, with exactly one `Validated` history entry;
8. asserts the `fact_versions` and `memory_events` deltas are each exactly `+1` relative
   to the recorded baseline — the pre-image snapshot and the audit append are both
   written only inside the single winning transaction (a losing `_promote_to_validated_cas`
   call returns `False` before either write is attempted; see `core/memory.py`'s own
   comment at the `if not committed: return False` guard);
9. asserts `PRAGMA integrity_check = ok`;
10. makes one further, fresh `validate_and_promote()` call after the race and asserts
    it returns `passed=True, reason="already_validated"` with **no** further
    `fact_versions`/`memory_events` delta — the normal idempotent contract, not a
    second mutation.

A companion test (`test_seam_never_fabricates_rowcount_or_mutates_directly`) pins the
seam's own contract in isolation (no contention involved): it must delegate exactly
once, with the exact arguments the real call site would use, and must not alter the
returned verdict. A third test
(`test_race_is_stable_under_repetition`, `@pytest.mark.parametrize` over 3 fresh
databases) restates the same race compactly so a single `pytest` invocation already
exercises it more than once, independent of the manual repeated-run validation
recorded below.

## What is proven

- concurrency on one file-backed SQLite database, in this repository's default
  (non-WAL-pinned-elsewhere) journal configuration, with 5 real, independent
  `SQLiteGraphStore` connections;
- the existing public, hardened `validate_and_promote()` / `_promote_to_validated_cas()`
  promotion path, unmodified;
- exactly one committed winner, `reason == "passed"`;
- explicit, honest loser semantics: `passed=False`, `reason == "concurrent_modification"`,
  never a false success, never `"already_validated"` during the race;
- no automatic retry converts a loser into a winner (each contender's single verdict
  is its final outcome; a silent internal retry would have collapsed a loser's reason
  to `"passed"`/`"already_validated"`, which is independently ruled out by the explicit
  per-loser reason assertion);
- an exact, measured (not assumed) durable side-effect delta: `fact_versions` +1,
  `memory_events` (whole-table) +1, both attributable only to the single winning
  transaction;
- `PRAGMA integrity_check = ok` before and after;
- a later fresh call observes the completed transition through the normal idempotent
  contract, with zero additional mutation.

## Observed but out of scope

During development, the first version of this test — which constructed 5 brand-new
`SQLiteGraphStore` instances and immediately raced their very first operation against
each other, with no prior schema bootstrap — intermittently failed with
`sqlite3.OperationalError: view erasure_audit already exists` (2 of 3 repeated runs in
one observed batch). Root cause: `SQLiteGraphStore._db()`'s lazy DDL block
(`core/memory.py:573-575`) runs `DROP VIEW IF EXISTS erasure_audit` followed by a bare
`CREATE VIEW erasure_audit AS ...` (no `IF NOT EXISTS`), guarded only by a
**per-instance** `self._ddl_initialized_paths` set — not a cross-connection guard. Two
fresh instances whose first operation races can both pass the `DROP VIEW IF EXISTS`
step, and then collide on the unguarded `CREATE VIEW`.

This is a genuine, pre-existing schema-bootstrap race, but it is **not** the CAS
contract issue #178 asks this test to characterize, and fixing it would touch DDL/schema
code that this issue's scope boundary explicitly excludes. The permanent test instead
calls `store.ensure_schema()` for every contender, sequentially, before starting any
race thread — isolating this test to the CAS write itself. The `erasure_audit`
DDL-bootstrap race remains open and is recorded here, not fixed, so a future,
independently-scoped issue can decide whether/how to harden concurrent first-use schema
bootstrap (e.g. `CREATE OR REPLACE VIEW` equivalent, or a cross-process advisory lock
around first-use DDL). No production code changes in this PR.

## What is NOT proven

- unlimited concurrency (5 contenders were used, not an arbitrary N);
- separate OS processes or separate machines — all contenders are threads in one
  process (matching #174's own stated boundary);
- network filesystems;
- a crash injected at every possible instruction inside the guarded transaction;
- transactional outbox atomicity (explicitly out of scope; still blocked on this
  characterization per issue #178's follow-up boundary);
- compound supersede (`supersede_fact_cas()` is a separate atomic mutation family, not
  exercised here);
- performance as an SLA — no latency claims are made;
- fitness of every SQLite deployment profile (WAL vs rollback journal, remote storage,
  etc.);
- the `erasure_audit` DDL-bootstrap race noted above — observed, not fixed, not
  further characterized.

## Non-goals

This increment does not change `TruthGate` thresholds, `CognitiveMode` semantics, the
ESM transition graph, retry policy, SQLite busy timeout, WAL/synchronous mode,
connection pooling, migrations, `PromotionGateway` contracts, the `AuditChain` hash
contract, compound supersede, transactional outbox, API behavior, cache policy, or any
production authority boundary.

## Merge gate

An external package-index or dependency-resolution failure is not repository evidence
and must not be treated as a passing check. This PR remains draft until the permanent
tests, architecture freeze, lint, blocking type checks and full repository test suite
pass on the same pinned final head. Docker hardening must pass when its workflow is
triggered; an explicit test/docs path-filter skip is recorded as `NOT_APPLICABLE`, never
as `PASS`. No CI exception is granted for this characterization increment.

## Follow-up

After this gate, transactional outbox work may proceed per issue #178's stated
follow-up boundary. Compound supersede (`supersede_fact_cas()`) remains a separate
atomic mutation family and was not part of this issue. The `erasure_audit`
DDL-bootstrap race noted above is a candidate for a future, independently-scoped
characterization/fix.
