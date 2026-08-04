# ADR — Projection policy v1 and version-monotonic FTS apply contract

**Status:** accepted for policy v1 (FTS only)
**Date:** 2026-08-04
**Issue:** #194. **Parent:** #193. **Refs:** #179.
**Dependency:** projection-outbox foundation #180/#179, erasure/dependency ownership
#183/#188, local scope contract #189/#190, first Canon caller #191/#192.
**Does not touch:** migration 020, dispatcher claim/lease/retry/ack, Canon callers,
TruthGate/ESM, compound supersede, graph/vector implementation.

## Context

Issue #193's Phase 0 characterization (pre-work for a bounded local projection
dispatcher) found two blockers that made any dispatcher lease/retry/ack state machine
premature:

1. `ProjectionKind.ALL` had no executable interpretation anywhere in runtime code —
   nothing read an intent's `projection_kind` and branched on it.
2. FTS, graph, and vector targets exposed no version to compare against. Nothing
   prevented an older or redelivered `projection_outbox` intent from overwriting a
   projection already derived from a newer Canon version.

A third finding shaped this decision: graph and vector are not fact-addressable
default-runtime projections today. The graph backend is keyed by entity name (ETIR),
not `fact_id`, and is feature-flagged off by default; the vector store's
version-aware layer (`core/embedding_projection.py`) exists but has zero production
callers and is also feature-flagged off. Only FTS (`facts_fts`) is genuinely wired by
default, with an existing (best-effort, non-version-aware) sync convention already in
`core/memory.py`.

## Decision

### Policy v1 `ALL` expansion

`core.projection_apply.resolve_projection_targets(policy_version, projection_kind)` is
a pure function of its two arguments — no environment variable, feature flag, or
runtime configuration is ever consulted:

```python
resolve_projection_targets("v1", ProjectionKind.ALL) == (ProjectionKind.FTS,)
resolve_projection_targets("v1", ProjectionKind.FTS) == (ProjectionKind.FTS,)
resolve_projection_targets("v1", ProjectionKind.GRAPH)  # raises UnsupportedPolicyTargetError
resolve_projection_targets("v1", ProjectionKind.VECTOR)  # raises UnsupportedPolicyTargetError
```

`ALL` under policy v1 means **all targets defined by projection policy v1** — currently
just FTS — not every reserved `ProjectionKind` enum value. This is a deliberate,
narrow reading: widening it to include graph/vector requires its own reviewed policy
version and its own fact-addressable, idempotent, version-monotonic primitives, never
a silent expansion of `v1` in place.

An explicit `GRAPH`/`VECTOR` intent under policy v1 raises
`UnsupportedPolicyTargetError` — parked, never silently skipped, never treated as
acknowledged/delivered. A future dispatcher processing such an intent gets an
exception it must surface, not an empty target tuple it could mistake for "nothing to
do here."

### FTS apply primitive — two layers

**A. Low-level SQL helpers** (`upsert_fts_row()`, `remove_fts_row()`,
`core/projection_apply.py`): the exact `INSERT OR REPLACE INTO facts_fts(...)` /
`DELETE FROM facts_fts WHERE ...` statements, factored out of their two previous
duplicated inline sites in `core/memory.py` (`store_fact()`, `supersede_fact_cas()`).
No transaction management, no policy logic — callers decide everything. **Historical
best-effort semantics at both call sites are unchanged**: each site keeps its own
pre-existing `try: ... except sqlite3.OperationalError: pass` wrapping around the call
to the shared helper — this ADR does not make either path fail-closed.

**B. Strict apply helper** (`apply_fts_projection()`): Canon/version/policy-aware,
implementing the current-Canon rule and monotonic checkpoint below. Accepts a
caller-owned, already-open connection; never commits, rolls back, retries, sleeps, or
makes a network call; never uses content captured in the outbox intent — every apply
re-reads `facts.fact_version`, `claim`, `source` fresh from `facts` at apply time.

### Current-Canon rule

For an intent with `canonical_version = V_intent`:

- **Canon missing** (`facts` row gone — erased): remove any FTS row and checkpoint
  for the fact. Outcome `MISSING_CANON_REMOVED`. Never recreates data.
- **Canon version < V_intent**: raise `CanonVersionBehindIntentError` — fail closed,
  no partial write. An intent should never claim a version Canon has not yet reached;
  this is a durable inconsistency, not a normal race.
- **Canon version >= V_intent**: project the **current** Canon row (its own current
  `fact_version`, `claim`, `source`), not the intent's own captured content or
  version. This is what makes an old/redelivered intent safe to replay: it refreshes
  to current state rather than regressing to stale content.

### Version checkpoint (migration 021)

`projection_checkpoints` — composite PK `(aggregate_type, aggregate_id, scope_ref,
projection_kind)`, content-minimized to `applied_canonical_version` + `updated_at`.
Policy v1 closes every dimension except `aggregate_id` and the version to exactly one
value each (`aggregate_type='fact'`, `scope_ref='local:primary'`,
`projection_kind='fts'`, enforced by `CHECK` constraints). No claim, evidence, model
output, payload JSON, or identity of any kind.

**Monotonic guard** — an explicit UPSERT ... WHERE, not a plain `INSERT OR REPLACE`:

```sql
INSERT INTO projection_checkpoints (...) VALUES (...)
ON CONFLICT(aggregate_type, aggregate_id, scope_ref, projection_kind)
DO UPDATE SET applied_canonical_version = excluded.applied_canonical_version, ...
WHERE excluded.applied_canonical_version > projection_checkpoints.applied_canonical_version
```

Verified empirically (and pinned by test): attempting to write a lower or equal
version than what's already stored is a no-op — the existing row (value and
timestamp) is untouched. `apply_fts_projection()` re-reads the checkpoint's actual
final value after this attempt and **only writes FTS content if its own value won or
tied** — if a concurrent/earlier writer already advanced the checkpoint past this
call's own (now-stale) Canon read, this call skips the FTS write entirely rather than
overwriting newer content with older content it happened to read. The checkpoint
number and the FTS content it describes can therefore never disagree about which
version is authoritative.

FTS mutation and checkpoint mutation are committed in one transaction — proven by
forcing a real failure on each side independently (see Validation) and confirming the
other side rolls back with it.

### FTS unavailable

If `facts_fts` does not exist (missing table, or the SQLite build lacks FTS5),
`apply_fts_projection()` returns `FTS_UNAVAILABLE` immediately — no checkpoint is
written, no partial write occurs. A future dispatcher must never acknowledge this as
delivered; it is a structured, permanent-until-schema-changes non-delivery, not a
retryable transient failure and not a silent skip.

### Erasure ownership

`projection_checkpoints` is added to `core/memory.py`'s shared
`_SAME_DB_DEPENDENT_TABLES` registry — the exact same mechanism issue #183 used for
`projection_outbox` — with the identical `aggregate_type = 'fact' AND aggregate_id = ?`
shape. This automatically wires it into both `erase_fact_dependents_atomic()`'s atomic
purge and `same_db_dependents_present()`'s residual/reappearance check, with no
separate code path and no reliance on any foreign-key cascade.

## Rejected alternatives

- **Widening `ALL` to include graph/vector with a silent-skip fallback** — rejected:
  explicitly forbidden by issue #193's own Apply Contract ("must either apply every
  configured local target successfully or remain unacknowledged/retryable; no silent
  partial success") and by #194's own decision boundary.
- **Deriving the target set from environment/feature flags** (e.g. `enable_etir`,
  `STORAGE_BACKEND`) — rejected: the target set must be deterministic from the
  durable intent's own `policy_version` alone, proven by a dedicated test that flips
  every relevant flag and confirms no change in output. A flag-derived set could
  differ between the process that appended the intent and the process that later
  applies it.
- **Plain `INSERT OR REPLACE` for the checkpoint** — rejected: silently allows
  regression; the explicit `UPSERT ... WHERE` guard is the only form that makes "a
  lower version can never replace a higher version" true by construction, not by
  caller discipline.
- **Reordering the transaction to write FTS before the checkpoint** — considered, to
  make both rollback-direction tests symmetric, then rejected: writing FTS content
  before knowing whether this call's own Canon read is the winning one would risk
  writing stale content that a concurrent writer's newer checkpoint has already
  superseded. Checkpoint-then-conditionally-FTS is the only order that keeps the two
  in agreement.
- **A fail-closed rewrite of `store_fact()`/`supersede_fact_cas()`'s existing FTS
  sync** — rejected: out of this issue's scope. Their historical best-effort
  (`try/except sqlite3.OperationalError: pass`) behavior is preserved exactly; only the
  duplicated SQL was factored into a shared, reusable low-level helper.

## Preserved semantics

- `migrations/020_projection_outbox.sql` and `ProjectionIntent`'s immutable semantic
  fields are untouched.
- `store_fact()` and `supersede_fact_cas()`'s FTS sync keeps its exact prior
  transaction scope and exception handling — refactored to call a shared primitive,
  not made fail-closed.
- No dispatcher claim, lease, retry, acknowledgement, or background worker/scheduler
  exists. `apply_fts_projection()` is a plain function a test (today) or a future,
  separately reviewed dispatcher (issue #193) calls directly inside its own
  transaction.
- No Canon mutation, TruthGate/ESM change, or compound supersede integration.

## Validation

- New file: `tests/test_projection_policy_v1_fts_apply.py` — 18 tests covering the
  resolver (exact expansion, environment-independence, GRAPH/VECTOR rejection, unknown
  policy version), the apply primitive (first refresh, idempotent repeat, current-Canon
  projection of a stale/redelivered intent, monotonic checkpoint under out-of-order
  apply, fail-closed on Canon-behind-intent, missing-Canon removal, FTS-unavailable,
  both rollback directions using genuine SQLite-level failures — a real trigger for
  `projection_checkpoints`, and a corrupted FTS5 shadow table for `facts_fts` since
  SQLite does not permit triggers on virtual tables at all — concurrent apply at 2 and
  10 contenders, and erasure removal + reappearance detection).
- RED confirmed on the unmodified baseline (`core.projection_apply` did not exist):
  `ModuleNotFoundError` at collection.
- GREEN after implementation: 18/18 passed, repeated **25×** with 0 failures (no
  sleep-based synchronization anywhere).
- Two pre-existing tests (`test_projection_outbox_migration.py`,
  `test_promotion_projection_outbox_caller.py`) hardcoded `PRAGMA user_version == 20`
  as "the latest version" — updated to `21` with an explanatory comment, since adding
  any new migration necessarily advances what "latest" means for a full migration run;
  this is not a regression in either file's own tested behavior.
- Regression, all green (221 passed): `test_truth_maintenance_supersede.py`,
  `test_erasure_coordinator.py`, `test_erasure_projection_outbox_dependency.py`,
  `test_erasure.py`, `test_migrations.py` (uses `LATEST_VERSION` dynamically, needed no
  change), `test_projection_outbox.py`, `test_projection_outbox_migration.py`,
  `test_promotion_projection_outbox_caller.py`, `test_sprint1_integrity.py`.
- Architecture-freeze guard (`--base main`): PASS.
- Repository hygiene (`check_no_tracked_artifacts.py`): OK.
- Ruff (pinned `ruff==0.4.10`): PASS.
- Blocking mypy (pinned): PASS — no issues in 291 source files.
- Full repository pytest, CI, Docker: see the PR body for this increment's real,
  verified results.

## Interpretation boundary

**Proven:** policy v1's `ALL`→`{FTS}` expansion is deterministic and
environment-independent; GRAPH/VECTOR under v1 are never silently skipped; a stale or
redelivered intent always projects current Canon, never regressing content or
checkpoint version; FTS mutation and checkpoint mutation commit and roll back
together; concurrent applies converge to one monotonic final state; erasure owns the
checkpoint atomically with everything else.

**Not proven / explicitly out of scope:** no dispatcher claim/lease/retry/ack exists;
no background worker or scheduler; graph/vector remain unimplemented and explicitly
parked, not merely "not yet configured"; this does not resolve issue #193's blockers
for any projection family other than FTS.

## Relationship to #193 and #179

This is the prerequisite issue #193's own Phase 0 characterization named before any
dispatcher state machine could be safely designed. It resolves both confirmed
blockers (`ALL` semantics, version-monotonic apply) **for FTS only**. Issue #193
remains blocked until this PR merges and post-merge verification confirms the
checkpoint contract on real `main`. Graph/vector activation is explicitly deferred to
a future, separately reviewed policy version.

## Merge gate

Architecture freeze, repository hygiene, Ruff, blocking mypy, the focused suite above,
the full repository pytest suite, and standard GitHub CI/Docker must be green on one
pinned final head, with zero unresolved review threads. This PR remains Draft and
unmerged until that gate passes and merge is explicitly requested. Issue #193 is not
started in this branch and is not unblocked until this PR merges.
