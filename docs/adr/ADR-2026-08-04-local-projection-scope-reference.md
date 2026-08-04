# ADR — Local projection scope reference contract

**Status:** accepted for v1 (one closed value)
**Date:** 2026-08-04
**Issue:** #189. **Parent:** #179.
**Dependency:** projection-outbox foundation #180/#179 (migration 020,
`ADR-2026-08-03-projection-outbox-foundation.md`); erasure/dependency ownership #183/#188
(`ADR-2026-08-03-projection-outbox-erasure-dependency.md`).
**Does not touch:** Canon caller wiring, dispatcher, `migrations/020_projection_outbox.sql`,
`core/memory.py`, TruthGate, ESM, SubjectScope.

## Context

`core.projection_outbox.ProjectionIntent.scope_ref` has existed syntactically since the
foundation increment (`_SCOPE_REF` regex, `TEXT NOT NULL` column in migration 020) but
had no executable semantics anywhere else in the repository. A repository-wide search
found `scope_ref` referenced only inside `core/projection_outbox.py` itself and its own
tests — no tenant id, deployment id, shard id, or other existing technical identifier is
reusable for it. The foundation ADR already states this directly: *"Multi-user
activation remains blocked until an executable SubjectScope contract exists; this
foundation does not invent one."*

This left issue #179's first Canon caller increment blocked
(`BLOCKER_SCOPE_CONTRACT`, confirmed by a dedicated characterization pass): wiring a
real caller would have required inventing a `scope_ref` value at the call site, which
would silently create an unreviewed, undocumented scope contract exactly where a
reviewed one belongs.

## Decision

Define exactly one v1 value, exported as a constant:

```python
LOCAL_PROJECTION_SCOPE_REF: Final = "local:primary"
```

`ProjectionIntent.__post_init__` enforces it by exact equality, layered strictly *after*
the pre-existing `_SCOPE_REF` syntax check — a value can be syntactically valid and still
be rejected for not being this one value:

```python
if not isinstance(self.scope_ref, str) or not _SCOPE_REF.fullmatch(self.scope_ref):
    raise ValueError("ProjectionIntent.scope_ref is not a safe scope reference")
if self.scope_ref != LOCAL_PROJECTION_SCOPE_REF:
    raise ValueError(
        "ProjectionIntent.scope_ref must be exactly "
        f"{LOCAL_PROJECTION_SCOPE_REF!r} — v1 supports only this one local "
        "routing scope ..."
    )
```

No normalization, no default argument, no implicit fallback: `"local"` is never
silently coerced to `"local:primary"` — an incorrect value is rejected, not corrected.
A future caller must import and pass the exported constant explicitly.

## Meaning

`local:primary` means only:

- a local, rebuildable-projection routing namespace;
- the current single local set of FTS/graph/vector projections;
- a stable technical identifier — the same value across restarts and across every
  `ProjectionKind` (`ALL`/`FTS`/`GRAPH`/`VECTOR`) in v1.

## Non-meaning

`local:primary` is explicitly **not**:

- an authorization boundary;
- tenant isolation;
- user ownership;
- a SubjectScope;
- a privacy boundary;
- database identity;
- device identity;
- a globally unique deployment identity;
- confirmation of data access.

It is never derived from `claim`, `source`, `metadata`, `user_id`, hostname, filesystem
path, environment variable, process id, a random UUID, the database filename, model
output, or network identity. Multi-user activation remains blocked exactly as before
this ADR.

## Why a constant, not a derivation

In the current local-first, single-user regime the system has no dynamic routing scope
to express. A derived value would be actively worse than one closed constant:

- it could change unstably across restarts;
- it could be mistaken for a security boundary it does not provide;
- since `scope_ref` participates in `outbox_id`'s deterministic semantic hash, an
  unstable derivation would produce semantically different intents for the same Canon
  mutation across runs — breaking the exact idempotency the foundation ADR already
  proved;
- it would prematurely freeze shape decisions that belong to a future, independently
  reviewed SubjectScope design.

### Rejected alternatives

1. **`"default"`** — rejected as ambiguous; too easily misread later as "default
   user" or "default tenant" rather than a routing namespace.
2. **Hostname/path/database-filename-derived value** — rejected: unstable across
   environments, leaks environment details into a durable row, and its meaning would be
   accidental rather than designed.
3. **Random UUID** — rejected: `outbox_id` is deterministic specifically so a duplicate
   append is idempotent; a scope_ref that changes per-process would break that across
   restarts.
4. **`user_id`/metadata-derived value** — rejected: this would silently create an
   unreviewed authorization/privacy model exactly where the foundation ADR says one does
   not yet exist.
5. **Omit `scope_ref`** — rejected: migration 020's own schema (`scope_ref TEXT NOT
   NULL`) already requires an explicit routing scope; the column shape does not change.

## Preserved semantics

- `migrations/020_projection_outbox.sql` is unchanged — the existing `TEXT NOT NULL`
  column already fits a fixed string value; no schema migration needed.
- The pre-existing `_SCOPE_REF` syntax guard (empty string, whitespace, invalid
  characters, length) is unweakened — it still runs, and still rejects those inputs on
  its own, before the new exact-equality check is even reached.
- `scope_ref` continues to participate in `outbox_id`'s canonical hash exactly as
  before — proven directly (not just asserted) by replicating the published hash
  formula with an alternate scope_ref and confirming it produces a different id.
- Content minimization is unaffected: no claim, justification, evidence, payload,
  or user identity is introduced by this change.
- Issue #183's erasure/residual ownership of `projection_outbox` rows (same-DB atomic
  deletion, residual/reappearance detection, migration-020 gating) is untouched and
  re-verified green with the real constant substituted for the test placeholder it
  previously used.

## Failure behavior

Any `scope_ref` other than `"local:primary"` — including every other syntactically
valid value tested (`"local"`, `"local:secondary"`, `"tenant:default"`, `"user:123"`,
`"workspace:main"`, `"device:local"`) — raises `ValueError` at `ProjectionIntent`
construction time, before any durable row is ever considered. No caller can silently
widen the accepted scope.

## Validation

- New/updated tests in `tests/test_projection_outbox.py`:
  - `LOCAL_PROJECTION_SCOPE_REF == "local:primary"`;
  - an intent constructed with the constant is accepted;
  - 6 syntactically-valid-but-unauthorized values are rejected (parametrized);
  - the pre-existing unsafe-syntax guard (empty/whitespace/invalid chars/length/
    non-ASCII) still rejects those inputs, unweakened;
  - `scope_ref` is proven to participate in `outbox_id`'s semantic identity by
    replicating the published hash formula with an alternate value, without bypassing
    or weakening production validation to do it;
  - a real durable append (`append_projection_intent_in_transaction`, inside a real
    caller-owned transaction) stores exactly `"local:primary"` in the
    `projection_outbox.scope_ref` column.
- `tests/test_projection_outbox.py`: 22/22 passed, repeated 25× with 0 failures.
- `tests/test_erasure_projection_outbox_dependency.py` (issue #183's own suite): the
  test-only placeholder scope literal (`'scope'`) was replaced with the real
  `LOCAL_PROJECTION_SCOPE_REF` constant; 9/9 passed, confirming no regression.
- `tests/test_projection_outbox_migration.py`: 1/1 passed — migration 020 unchanged.
- Architecture-freeze, repository hygiene, Ruff, blocking mypy, full repository pytest,
  CI and Docker: see the PR body for this increment's real, verified results.

## Interpretation boundary

**Proven:** exactly one scope_ref value is now accepted through the public API;
syntactically valid but unauthorized values are rejected; the pre-existing syntax guard
is intact; the value durably persists exactly as written; `scope_ref` participates in
deterministic intent identity; issue #183's erasure ownership is unaffected.

**Not proven / explicitly out of scope:** no Canon caller was wired by this change; no
dispatcher exists; this is not a SubjectScope implementation and does not become one by
implication; multi-user activation is not enabled; `fact_version`/canonical_version
sourcing for the eventual first caller is characterized separately and is not addressed
here.

## Future

A SubjectScope contract may later replace or extend `scope_ref`'s accepted values, but
only through its own separate, reviewed design — not by widening this constant in
place. Multi-user activation remains blocked until that contract exists.

## Merge gate

Architecture freeze, repository hygiene, Ruff, blocking mypy, the focused
`projection_outbox`/erasure-outbox/migration-020 suites above, the full repository
pytest suite, and standard GitHub CI/Docker must be green on one pinned final head, with
zero unresolved review threads. This PR remains Draft and unmerged until that gate
passes and merge is explicitly requested. Issue #179 is not closed by this PR — only
#189 is.
