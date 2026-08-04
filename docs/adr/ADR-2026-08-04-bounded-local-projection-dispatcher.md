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

- New file: `tests/test_bounded_local_projection_dispatcher.py` — originally 32
  tests (some parametrized), grown to 50 across three review-hardening rounds
  (see the addenda below) — covering all 26 required proofs from issue #193: successful
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
  explicitly injected `datetime`). The suite grew to 46, then 50, across the
  review-hardening rounds below; each round's own "GREEN" count in its addendum
  reflects the suite size at that point — see the final addendum for the
  current, authoritative 50/50 count.
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

## Review-hardening addendum (Copilot review, PR #197)

The automated Copilot review on the pinned head found one real gap, fixed in a
follow-up commit: `retry_claim()`'s and `park_claim()`'s CAS `UPDATE` statements
checked `lifecycle_state='leased' AND lease_token=?` but, unlike `ack_claim()`,
did not also require `lease_expires_at > now`. An expired-but-not-yet-reclaimed
holder could therefore still transition its own row to `retry` or `parked` —
inconsistent with this ADR's own stated "Lease ownership" contract ("a stale or
expired token is rejected structurally ... for ack/retry"), which was already
true for ack but not yet enforced for retry/park. Fixed by adding the same
`lease_expires_at > ?` guard to both statements; proven by two new tests,
`test_expired_lease_token_cannot_retry` and `test_expired_lease_token_cannot_park`,
mirroring the existing `test_expired_lease_token_cannot_ack`. Focused suite grew
from 32 to 34 tests; full re-validation (25× repeat, regression, Ruff, mypy,
architecture-freeze, hygiene, full pytest) re-run green — see the PR body for
exact numbers.

## Review-hardening addendum 2 (independent maintainer review, PR #197)

A second, more extensive maintainer review raised five findings. Each was
independently re-verified against the actual code (not accepted at face value)
before any change — two were confirmed as real bugs, two as legitimate scoped
hardening, one as reasonable defense-in-depth, and one proposed fix was
deliberately **not** implemented.

**1. Confirmed bug — timestamp comparisons were not timezone-normalized.**
Every lease/eligibility check in this module is a plain ISO-8601 STRING
comparison. A naive `now` could silently compare against the wrong timezone,
and two datetimes representing the SAME instant under different UTC offsets
could produce different strings that sort incorrectly — concretely, a `now`
expressed at `+05:00` can lexicographically sort AFTER a UTC-stored
`lease_expires_at` even though the real instant it represents is earlier,
incorrectly rejecting a legitimately valid ack. Fixed: a new `_normalize_now()`
helper rejects naive datetimes (raises `ProjectionDispatchContractError`) and
normalizes every aware datetime to UTC before formatting, applied uniformly in
`claim_batch()`, `apply_claimed_work()`, `ack_claim()`, `retry_claim()`, and
`park_claim()`. Proven by `test_naive_datetime_rejected_by_claim_batch`,
`test_naive_datetime_rejected_by_ack_claim`, and
`test_equal_instant_different_utc_offset_normalizes_correctly` (constructs the
exact cross-offset scenario above and confirms the ack now succeeds).

**2. Confirmed bug — real SQLite failures were misclassified as transient.**
`apply_claimed_work()` caught `sqlite3.OperationalError` specifically, then
funneled every OTHER `sqlite3.DatabaseError` (including `IntegrityError` —
confirmed empirically to carry `sqlite_errorcode=1299`/`SQLITE_CONSTRAINT_NOTNULL`,
and a corrupted-database error — confirmed empirically to carry
`sqlite_errorcode=267`/`SQLITE_CORRUPT_VTAB`, both NOT subclasses of
`OperationalError`) into the same "transient, retry" bucket. Since this module
has no maximum-attempts cap by design, a permanent constraint violation or a
corrupted database would retry forever. Fixed: a new `_classify_sqlite_failure()`
helper reads the real `sqlite_errorcode` attribute (never message
string-matching, never exception class alone) and reduces extended codes to
their primary code via `& 0xFF`; only `SQLITE_BUSY`/`SQLITE_LOCKED` (in any
extended form) are RETRY-eligible, everything else PARKs with a new
`SQLITE_PERMANENT` code (replacing the never-actually-reachable
`SQLITE_TRANSIENT`, removed from both the Python enum and migration 022's CHECK
constraint since it is unmerged). Proven by
`test_integrity_error_during_apply_becomes_parked_not_retried_forever` (a real
`BEFORE UPDATE` trigger forces a genuine `sqlite3.IntegrityError`) and
`test_busy_lock_during_apply_is_retried_not_parked` (a real second, zero-timeout
connection forces a genuine "database is locked"), confirming both directions.
`test_apply_failure_remains_unacknowledged`'s existing corrupted-FTS5-shadow-table
scenario was updated to assert the now-correct PARK/`SQLITE_PERMANENT` outcome
(it previously asserted the incorrect RETRY/transient outcome this fix corrects).

**3. Legitimate scoped hardening — scope_ref was never validated at apply time.**
Migration 020 has no SQL-level CHECK narrowing `projection_outbox.scope_ref`
(unlike `aggregate_type`/`projection_kind`/`operation`, which do) — a
raw/malformed row could carry a scope outside policy v1's one supported value,
and `apply_claimed_work()` never checked it. Fixed, purely within this PR's own
new code (no change to the already-merged #194 apply contract): re-reads
`scope_ref` fresh from `projection_outbox` alongside `aggregate_id` and PARKs
with a new `UNSUPPORTED_SCOPE` code if it is not `LOCAL_PROJECTION_SCOPE_REF`.
Proven by `test_unsupported_scope_becomes_parked`.

Explicitly **not** changed: this same finding argued the dispatcher should also
give `ProjectionIntent.operation` (REFRESH vs REMOVE) its own executable
semantics rather than delegating entirely to `apply_fts_projection()`'s
current-Canon-based outcome. That behavior — "a REMOVE-shaped outcome
regardless of the intent's own `operation`" — is a deliberate, already-reviewed,
already-merged decision from issue #194
(`ADR-2026-08-04-projection-policy-v1-fts-checkpoint.md`), not a gap introduced
by this PR. Overriding it here would be scope creep beyond issue #193 and would
contradict a decision this PR has no mandate to revisit.

**4. Legitimate scoped hardening — retry backoff trusted a caller-supplied
attempt_count.** `retry_claim()` took `attempt_count` as a parameter and
computed backoff from it directly — even a caller holding a genuinely valid
lease token could pass a wrong value and reset or manipulate backoff timing.
Fixed: `retry_claim()` no longer accepts `attempt_count` as a parameter at
all — it reads the DURABLE value from `projection_dispatch_state` inside the
same CAS transaction as the UPDATE, so there is no longer any input for a
caller to forge. Proven by `test_retry_backoff_uses_durable_attempt_count_not_caller_input`
(three successive claim/retry cycles produce exactly the 1s/2s/4s delays
implied by the durable count) and
`test_retry_backoff_ignores_forged_attempt_count_even_with_valid_token`.

**5. Defense-in-depth, not a proven exploitable bug — no executable invariant
tied `projection_dispatch_state.aggregate_id` to `projection_outbox.aggregate_id`.**
`claim_batch()`'s own INSERT already cannot produce a mismatch (it sources
`aggregate_id` from a `SELECT` of the very row it references) and no other
write path in this module touches the column, so no exploit through the actual
shipped API could be constructed. Added anyway, matching this codebase's
existing belt-and-suspenders style (e.g. `prevent_fact_delete`, the closed CHECK
constraints on every projection table): `BEFORE INSERT`/`BEFORE UPDATE` triggers
on `projection_dispatch_state` (migration 022, still unmerged, edited directly —
no migration 023 needed) that abort unless a `projection_outbox` row with the
same `outbox_id` AND `aggregate_id` exists. Proven by
`test_dispatch_state_aggregate_id_mismatch_insert_rejected`,
`test_dispatch_state_nonexistent_outbox_insert_rejected`,
`test_dispatch_state_aggregate_id_mismatch_update_rejected`, and
`test_erasure_still_works_with_aggregate_id_triggers_installed` (confirms the
DELETE-only erasure purge is unaffected). This also required fixing the
pre-existing `test_reappearance_of_dispatch_state_after_clean_erasure_detected`,
whose synthetic reappearance row referenced a nonexistent `outbox_id` — the new
trigger correctly rejected it, so the test was updated to insert a matching
orphaned `projection_outbox` row too, genuinely modeling the out-of-band
reappearance shape it intends to prove.

**Not implemented — resampling an injected clock at every transaction
boundary.** The review proposed replacing the injected `datetime` value with a
callable resampled after each `BEGIN IMMEDIATE` acquires its lock, reasoning
that a long lock wait could leave `now` stale relative to real wall-clock time.
Rejected: issue #193's own ТЗ explicitly asked for an injected clock (a value
the caller controls, exactly what was built) — a callable resampled internally
is a materially different, broader API contract, not a bug fix. More
importantly, the actual safety guarantee this module provides against the
described race is NOT the timestamp comparison — it is the exact-lease-token
CAS on every ack/retry/park. If another process reclaims a row (because real
wall-clock time has actually passed lease_expires_at), the token in the
database changes, and this process's own `apply_claimed_work()`/`ack_claim()`/
`retry_claim()`/`park_claim()` calls will all fail with `STALE_TOKEN`/rejected
regardless of what `now` value this process happens to be using — the token
compare, not the timestamp compare, is what makes concurrent claim/apply/ack
race-free (see `test_concurrent_claimers_one_owner_per_intent` and the two
crash-recovery tests). No test was written for this proposal since it was not
implemented.

Full re-validation after all fixes above: focused suite grew 34→46 tests, all
passing, re-run 25× with 0 failures; full regression (269 passed across every
outbox/erasure/checkpoint-adjacent suite); Ruff/mypy clean; architecture-freeze
and hygiene guards PASS; full repository `pytest tests/`: **3096 passed**, 22
skipped, 1 xfailed, 0 failed — see the PR body for the exact pinned-head numbers.

## Review-hardening addendum 3 (second maintainer follow-up, PR #197)

A second maintainer follow-up raised two more findings. Both were re-verified,
and one of them reverses a position taken in addendum 2 above.

**1. Confirmed bug, reversing addendum 2's "not changed" position — REMOVE
was silently applied as REFRESH.** Addendum 2 argued that giving
`ProjectionIntent.operation` its own executable semantics was out of scope,
citing `apply_fts_projection()`'s "REMOVE-shaped outcome regardless of the
intent's own `operation`" as a deliberate, already-merged #194 decision. On
closer inspection this was wrong: that #194 contract describes what happens
when Canon is **missing** (a remove-shaped outcome regardless of what
`operation` says); it never addressed — because `apply_fts_projection()` does
not even accept `operation` as a parameter — what should happen when Canon
**still exists** and the intent explicitly declared REMOVE. Nothing had ever
reviewed that combination; issue #193's own dispatcher was silently choosing
"treat it as REFRESH" by omission, not by any reviewed decision. **Fixed**:
`apply_claimed_work()` now re-reads `operation` fresh alongside `aggregate_id`/
`scope_ref` and PARKs with a new `UNSUPPORTED_OPERATION` code for anything
other than REFRESH — the same fail-closed pattern already used for
GRAPH/VECTOR and unsupported scope, never inventing a new REMOVE semantic
(that remains a future, separately reviewed policy decision), and never
silently refreshing an intent that asked for removal. Proven by
`test_remove_operation_becomes_parked_not_applied` (FTS/checkpoint untouched,
immutable intent survives, never acknowledged) and
`test_dispatch_once_summary_excludes_parked_remove_from_acknowledged`.

**2. Legitimate scoped hardening — `dispatch_once()` reused one `now` for a
whole batch.** The lower-level primitives' own expiry checks are correct for
whatever `now` they are handed — this was never in question. The gap was
narrower: `dispatch_once()` sampled `now` once and passed the SAME value to
every step (claim, then every item's apply, then that item's ack/retry/park),
so a lease that genuinely expired partway through a slow batch (no other
worker ever reclaiming it) would still pass every check `dispatch_once()`
itself performed, using its own stale snapshot. The originally-proposed fix —
resampling inside each low-level primitive after its own `BEGIN IMMEDIATE` —
was declined again for the reasons in addendum 2 (the primitives' own
correctness does not depend on when they sample `now`; that remains the
caller's job). What changed: `dispatch_once()` itself now accepts
`clock: Callable[[], datetime]` instead of a single `now: datetime`, and calls
`clock()` fresh immediately before every step — the claim, each item's apply,
and that item's own ack/retry/park. This is a narrower, lower-risk change than
the original proposal: it touches only the one orchestration function that
would ever run for real, leaves every tested/reviewed primitive signature
unchanged, and still gives the caller full, deterministic control over time
(a fake clock is a plain callable/iterator, no wall-clock or sleep involved).
Proven by `test_dispatch_once_resamples_clock_between_items_expired_item_rejected`
(a two-item batch with a lease shorter than processing time; item 1
acknowledges normally, item 2 is rejected as expired rather than silently
applied using the stale batch-start time) and, at the primitive level directly,
`test_expired_lease_token_cannot_apply_even_without_reclaim` (proves
`apply_claimed_work()` already correctly rejects an expired lease under the
SAME, never-reclaimed token, given an honestly later `now` — confirming the
primitive itself needed no change, only its caller's clock discipline did).

Full re-validation: focused suite grew 46→50 tests, all passing, re-run 25×
with 0 failures; regression (273 passed); Ruff/mypy clean; architecture-freeze
and hygiene guards PASS; full repository `pytest tests/`: **3100 passed**, 22
skipped, 1 xfailed, 0 failed — see the PR body for the exact pinned-head numbers.

## Review-hardening addendum 4 (final maintainer comment, PR #197)

One more finding, confirmed real: `apply_claimed_work()` re-read `aggregate_id`,
`scope_ref`, and `operation` fresh from the durable `projection_outbox` row
(addenda 2 and 3 above), but still used `claimed.projection_kind`,
`claimed.policy_version`, and `claimed.canonical_version` directly from the
`ClaimedWork` snapshot for `resolve_projection_targets()` and
`apply_fts_projection()`. Addendum 2's earlier justification for not re-reading
these three ("guaranteed immutable for a given `outbox_id` by construction, via
the semantic hash") answered the wrong question: it is true that the DURABLE
row itself cannot carry two different values for a given `outbox_id`, but that
says nothing about whether a CALLER-CONSTRUCTED `ClaimedWork` — a public,
frozen-but-replaceable dataclass — can diverge from that durable row.
`dataclasses.replace(work, projection_kind=ProjectionKind.FTS)` produces
exactly such a divergent object, and nothing stopped `apply_claimed_work()`
from trusting it. A caller genuinely holding the correct `outbox_id` and
`lease_token` (real ownership credentials) could still turn a durable GRAPH or
unsupported-policy intent into an FTS/v1 apply, or override the durable
`canonical_version` entirely.

**Fixed**: the `intent_row` re-read inside `apply_claimed_work()`'s transaction
now includes `projection_kind`, `canonical_version`, and `policy_version`
alongside the already-re-read `aggregate_id`/`scope_ref`/`operation` — all six
semantic fields of the durable intent, in one query. `resolve_projection_targets()`
and `apply_fts_projection()` now receive ONLY these durable values; `claimed.*`
is never read for anything except `outbox_id` (identity) and `lease_token`
(ownership CAS). `ClaimedWork`'s docstring now states explicitly that every
semantic field is informational-only once returned from `claim_batch()`.

Proven by five new tests: `test_forged_projection_kind_cannot_override_durable_graph_intent`,
`test_forged_policy_version_cannot_override_durable_unsupported_policy_version`,
`test_forged_canonical_version_does_not_affect_apply` (a forged value high
enough to trigger `CanonVersionBehindIntentError` if it were actually used —
confirms the durable value is used instead, and the apply succeeds normally),
`test_genuine_unmodified_claim_still_follows_normal_success_path` (regression
proof that the normal, unmodified flow is unaffected), and
`test_forged_dto_leaves_fts_checkpoint_and_state_untouched_when_durable_intent_parks`
(explicit before/after snapshot proof that `apply_claimed_work()` itself
mutates nothing when the durable intent must park, regardless of what the
forged DTO claims).

Full re-validation: focused suite grew 50→55 tests, all passing, re-run 25×
with 0 failures; regression (278 passed); Ruff/mypy clean; architecture-freeze
and hygiene guards PASS; full repository `pytest tests/`: **3105 passed**, 22
skipped, 1 xfailed, 0 failed — see the PR body for the exact pinned-head numbers.

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
