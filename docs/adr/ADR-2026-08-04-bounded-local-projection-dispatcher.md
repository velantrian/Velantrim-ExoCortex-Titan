# ADR — Bounded local projection dispatcher with crash recovery

**Status:** accepted for the callable primitive only (not runtime-wired)
**Date:** 2026-08-04
**Issue:** #193. **Parent:** #179.
**Dependency:** projection-outbox foundation #180/#179, erasure ownership #183/#188,
local scope contract #189/#190, first Canon caller #191/#192, policy v1 FTS checkpoint
#194/#195.
**Does not touch:** migrations 020/021, Canon mutation, TruthGate/ESM, compound
supersede, graph/vector implementation, server startup, any background scheduler.

## Context

Issue #193's own Phase 0 characterization identified two blockers before any
dispatcher state machine could be designed — both resolved by issue #194:
`ProjectionKind.ALL` now has an executable, environment-independent expansion
(`{FTS}`), and `apply_fts_projection()` gives that one target a version-monotonic,
current-Canon apply contract. Nothing, however, yet *reads* `projection_outbox`
rows or decides when to call `apply_fts_projection()`. This ADR adds exactly that:
a bounded claim/lease/retry/ack state machine and the one-shot primitive that
drives it — still never registered anywhere at runtime.

## Decision

### Immutable intent vs mutable dispatch state

Three tables, three authorities, never merged:

```text
projection_outbox          (020) — immutable intent, never rewritten
projection_checkpoints     (021) — version-monotonic record of what Canon
                                   state a projection actually reflects
projection_dispatch_state  (022) — mutable claim/lease/retry/ack bookkeeping
                                   for ONE outbox_id; absence = pending
```

`projection_dispatch_state` is a pure sidecar. Deleting every row in it changes
nothing about what Canon has been projected — it only forgets in-flight delivery
bookkeeping, which `claim_batch()` would simply reconstruct on the next claim
(the row's absence is itself the "pending/unclaimed" state).

### State machine

```text
(no row)  --claim-->  leased  --ack----->  acknowledged   (terminal)
                       |   ^
                       |   |  reclaim (lease expired)
                       |   +-------------------+
                       |
                       +---retry--> retry --(next_attempt_at <= now)--> leased
                       |
                       +---park---> parked        (terminal, never auto-retried)
```

`acknowledged` and `parked` are both terminal and both excluded from
`claim_batch()`'s eligibility query — a parked row is never silently retried,
dropped, or later treated as delivered.

### Claim serialization

`claim_batch()` opens one `BEGIN IMMEDIATE` transaction for its entire batch:
SQLite's single-writer model means no second claimer can even begin its own claim
until this one commits or rolls back — the strongest serialization SQLite offers,
not a best-effort lock. On top of that, every claim/reclaim write is still an
explicit `INSERT ... ON CONFLICT DO UPDATE ... WHERE` CAS guard (never a plain
`INSERT OR REPLACE`), matching this codebase's standing rule of never trusting lock
timing alone. `aggregate_id` is copied via the INSERT's own `SELECT ... FROM
projection_outbox`, never taken from a Python-level parameter — a caller cannot
inject a mismatched aggregate_id even by constructing a hand-rolled `ClaimedWork`.

Eligibility is exactly three shapes, strictly ordered by
`(projection_outbox.created_at, projection_outbox.outbox_id)`:

- no `projection_dispatch_state` row (pending, never claimed);
- `retry` with `next_attempt_at <= now`;
- `leased` with `lease_expires_at <= now` (an expired holder — reclaimed, not
  double-owned).

`batch_size` is validated against `MAX_BATCH_SIZE = 100` before any transaction
opens; an invalid size raises `InvalidBatchSizeError` and touches nothing.

### Lease ownership

A lease is exactly `(lease_token, lease_expires_at)`. Every subsequent operation
that acts on a specific claim — apply, ack, retry, park — re-checks the CURRENT
`projection_dispatch_state` row's own token and expiry, never trusts the
`ClaimedWork` DTO's own copy as still valid. A stale (superseded) or expired token
is rejected structurally (`LeaseValidationOutcome.STALE_TOKEN` /
`.EXPIRED` for apply; `AckOutcome.ACK_REJECTED` / `RetryOutcome.RETRY_REJECTED` for
ack/retry) — never silently treated as success, and never allowed to mutate a
projection, park, or ack on another holder's behalf.

### Apply/ack transaction separation — the proven crash window

`apply_claimed_work()` and `ack_claim()`/`retry_claim()`/`park_claim()` are
DELIBERATELY separate short transactions on the same connection, never one
combined commit:

```text
transaction 1: apply_claimed_work()
  -> validate lease (same transaction, same connection, consistent snapshot)
  -> resolve_projection_targets(policy_version, projection_kind)  [v1: -> {FTS}]
  -> apply_fts_projection(conn, fact_id=..., intent_canonical_version=...)
  -> COMMIT  (FTS + checkpoint mutation now durable)
                                     |
                          <-- crash window -->
                                     |
transaction 2: ack_claim() / retry_claim() / park_claim()
  -> CAS UPDATE ... WHERE lifecycle_state='leased' AND lease_token=?
  -> COMMIT
```

A crash inside that window leaves the projection already correctly applied but
the intent still `leased`, under a token nobody will ever present again. When
that lease expires, `claim_batch()` reclaims it with a fresh token and a bumped
`attempt_count`, and `apply_claimed_work()` runs again — this is safe ONLY because
`apply_fts_projection()`'s current-Canon, version-monotonic contract (issue #194)
makes every reapply idempotent: it always re-reads Canon fresh and its checkpoint
UPSERT is a true no-op if a later value is already stored. `test_bounded_local_
projection_dispatcher.py::test_crash_after_apply_before_ack_restart_reclaims_
idempotently` proves this exact window: FTS row count and checkpoint value are
identical before and after the reclaim+reapply, never duplicated or regressed.

### At-least-once, not exactly-once

This module never claims exactly-once delivery. The crash window above is the
proof: the projection can legitimately be applied more than once for the same
outbox intent (idempotently, per above) if a crash separates apply from ack. No
test in this file, and no line in this module, treats "applied" as equivalent to
"acknowledged and therefore guaranteed delivered exactly once."

### Retry classification and backoff

`apply_claimed_work()` classifies every outcome into a closed action
(`ACKNOWLEDGE` / `RETRY` / `PARK` / `REJECTED`) and a closed, allowlisted
`DispatchErrorCode` — never a raw exception message or stack trace (enforced both
in Python and by migration 022's own CHECK constraint on `last_error_code`):

| Apply outcome | Action | Error code |
|---|---|---|
| `ProjectionApplyOutcome.APPLIED` | ACKNOWLEDGE | — |
| `ProjectionApplyOutcome.MISSING_CANON_REMOVED` | ACKNOWLEDGE | — |
| `ProjectionApplyOutcome.FTS_UNAVAILABLE` | PARK | `FTS_UNAVAILABLE` |
| `UnsupportedPolicyTargetError` (GRAPH/VECTOR/unknown policy) | PARK | `UNSUPPORTED_POLICY_TARGET` |
| `CanonVersionBehindIntentError` | PARK | `CANON_VERSION_BEHIND_INTENT` |
| `ProjectionApplyContractError` | PARK | `INTERNAL_CONTRACT` |
| `sqlite3.OperationalError` (locked/busy) | RETRY | `SQLITE_BUSY` |
| other `sqlite3.DatabaseError` | RETRY | `SQLITE_TRANSIENT` |

`MISSING_CANON_REMOVED` is acknowledged, not parked: the projection has correctly
been removed (never resurrected), which IS the intent's completion, not a failure.

Retry delay is `compute_retry_delay_seconds()` — deterministic bounded exponential
backoff from an explicitly injected `now`, no jitter, no `time.sleep()`:

```python
delay = min(
    BASE_RETRY_SECONDS * 2 ** min(attempt_count - 1, MAX_RETRY_EXPONENT),
    MAX_RETRY_SECONDS,
)
```

No jitter in v1: jitter would only matter once multiple independent dispatcher
processes exist and contend on the same retry windows, which this ADR does not
introduce (no runtime wiring at all yet) — adding it speculatively would be an
untested parameter with no test able to prove it does anything here.

### Parked semantics

`parked` is terminal and permanent until an operator or a future reviewed
mechanism intervenes — `claim_batch()`'s eligibility query structurally excludes
it (it matches none of the three eligibility shapes). No maximum-attempts cap
exists in this version: issue #193's own instruction was "do not introduce one
without a separate reason," and none has been reviewed. If one is added later, its
own ADR must specify that exhaustion becomes `PARKED`, never a silent drop and
never treated as delivered — this ADR does not pre-empt that design.

### Erasure ownership

`projection_dispatch_state` is registered in `core/memory.py`'s
`_SAME_DB_DEPENDENT_TABLES`, selected directly by `aggregate_id = ?` (this table
carries no `aggregate_type` column). Purge order for the projection family is
explicit — dispatch state, then checkpoint, then outbox intent, then the FTS row,
then every other Canon dependent — documented intent matching this table's own
`REFERENCES projection_outbox(outbox_id)`, even though the whole purge is one
atomic transaction where no reader can ever observe an intermediate state
regardless of order. `same_db_dependents_present()` gained the same fail-closed
exception issues #183/#194 already established for `projection_outbox`/
`projection_checkpoints`: a database whose `PRAGMA user_version >= 22` but whose
`projection_dispatch_state` table is missing is a corruption shape, not a
legitimately older database, and fails CLOSED (residual present) rather than
silently reporting "not applicable."

## Rejected alternatives

- **Per-row retry loops with random jitter** — rejected for v1: no second
  dispatcher process exists yet to contend against, so jitter has nothing to
  prove; deterministic backoff keeps every test's timing exact and reproducible.
- **A maximum-attempts cap with automatic dead-lettering** — rejected: issue
  #193 explicitly forbids introducing one without a separate reviewed reason, and
  none exists yet. `parked` (a human/future-reviewed intervention point) already
  exists as the fail-closed outcome for every currently-known permanent failure
  mode (`FTS_UNAVAILABLE`, `UNSUPPORTED_POLICY_TARGET`,
  `CANON_VERSION_BEHIND_INTENT`, `INTERNAL_CONTRACT`).
- **Combining apply and ack into one transaction** — rejected: this would make
  "applied" and "acknowledged" atomic together, which sounds safer but actually
  removes the ability to detect and recover from a crash between them —
  ADR-2026-08-04-projection-policy-v1-fts-checkpoint.md's own idempotent-reapply
  guarantee exists precisely so this window can be safe to leave open, and closing
  it would need a cross-database two-phase commit this project does not have.
- **Treating a claimed batch as one big apply transaction** — rejected: one
  intent's failure must never block or roll back every other intent in the same
  batch; each `apply_claimed_work()` call is its own independent transaction.
- **Trusting SQLite's single-writer lock alone for claim exclusivity** — rejected
  even though it is in fact sufficient (BEGIN IMMEDIATE fully serializes writers):
  every claim/reclaim/ack/retry/park write is still an explicit CAS guard, matching
  this codebase's standing "never rely on lock timing alone" convention and
  remaining correct even if this module is later adapted to a backend without
  SQLite's exact locking semantics.

## Preserved semantics

- Migrations 020 and 021 are byte-for-byte untouched.
- `core.projection_outbox.append_projection_intent_in_transaction()` and
  `core.projection_apply.apply_fts_projection()`/`resolve_projection_targets()`
  are called, never modified or duplicated.
- No Canon mutation, TruthGate/ESM change, or compound supersede integration.
- No graph/vector target is ever applied — `UnsupportedPolicyTargetError` always
  parks such an intent, matching policy v1's own closed target set.

## Validation

- New file: `tests/test_bounded_local_projection_dispatcher.py` — 32 tests
  (some parametrized) covering all 26 required proofs from issue #193: successful
  claim/apply/ack; 2- and 10-way concurrent claim exclusivity; strict batch
  bound; deterministic ordering; invalid batch size; crash-after-claim and
  crash-after-apply recovery (both with real separate connections modeling
  separate dispatcher instances); stale/expired token rejection for apply, ack,
  and retry; deterministic backoff and retry-claimability boundaries; every apply
  outcome's classification (FTS_UNAVAILABLE, GRAPH/VECTOR, unknown policy version,
  CanonVersionBehindIntent, MISSING_CANON_REMOVED, stale-intent-reads-current-
  Canon, genuine apply failure remains unacknowledged); full erasure ownership;
  migration-022 fail-closed corruption check; residual-survivor and reappearance
  detection; a `dispatch_once()` end-to-end smoke test; and a hard-boundary check
  that `dispatch_once()` exposes no async/background scheduling surface.
- RED confirmed on the unmodified baseline: `ModuleNotFoundError`
  (`core.projection_dispatcher` did not exist).
- GREEN after implementation: 32/32 passed, repeated **25×** with 0 failures
  (no `time.sleep()` anywhere in the module or its tests — every "wait" is an
  explicitly injected `datetime`).
- Regression (255 passed): `test_projection_policy_v1_fts_apply.py`,
  `test_projection_outbox.py`, `test_projection_outbox_migration.py`,
  `test_promotion_projection_outbox_caller.py`,
  `test_erasure_projection_outbox_dependency.py`, `test_erasure.py`,
  `test_erasure_coordinator.py`, `test_truth_maintenance_supersede.py`,
  `test_migrations.py`, `test_sprint1_integrity.py`.
- Architecture-freeze guard: no authority markers detected in the diff (no new
  feature flag, canonical write-path call, background-execution primitive, remote
  transport construction, or `*Worker`/`*Scheduler`/`*Controller`/`*Policy`/`*Gate`
  class) — this ADR is added regardless, per issue #193's own documentation
  requirement.
- Repository hygiene (`check_no_tracked_artifacts.py`): OK.
- Ruff (pinned `ruff==0.4.10`) and blocking mypy (pinned): PASS on every touched
  file.
- Full repository `pytest tests/`, CI, Docker: see the PR body for this
  increment's real, verified results.

## Interpretation boundary

**Proven:** the claim/lease/retry/ack state machine is race-free under 2- and
10-way concurrency; a crash at either proven window (after claim, after apply) is
recoverable without duplication or regression; every apply outcome maps to a
closed, content-minimized action and error code; a parked row is never
auto-retried; erasure atomically owns all four projection-family tables together.

**Not proven / explicitly out of scope:** this primitive is not registered
anywhere at runtime — no server startup wiring, no background worker, no asyncio
task, no scheduler, no infinite loop exists. No exactly-once claim is made
(at-least-once only, by design). No remote/distributed dispatch, no distributed
lock, no multi-user/SubjectScope activation, no GRAPH/VECTOR support. No claim is
made that any of this is observed running against real production traffic.

## Relationship to #179

This closes the last item the foundation ADR's "Next increment" section named as
outstanding for the dispatcher itself. Runtime activation (server startup wiring,
a real invocation cadence) is explicitly deferred to a separately reviewed future
change — see the foundation ADR's updated status.

## Merge gate

Architecture freeze, repository hygiene, Ruff, blocking mypy, the focused suite
above, the full repository pytest suite, and standard GitHub CI/Docker must be
green on one pinned final head, with zero unresolved review threads. This PR
remains Draft and unmerged until that gate passes and merge is explicitly
requested.
