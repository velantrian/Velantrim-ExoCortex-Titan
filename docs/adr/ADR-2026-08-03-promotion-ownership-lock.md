# ADR — Lock reviewed fact-promotion authority call sites in CI

**Status:** accepted  
**Date:** 2026-08-03  
**Issue:** #165  
**Baseline:** five standard callers migrated through PromotionGateway

## Context

Migration of known callers reduces current bypasses but does not prevent a future module
from importing a compatibility wrapper or calling a store method directly. A textual
search is not a sufficient merge gate because comments and docstrings create false
positives, while attribute calls can bypass an import-based check.

The repository also has two operations that must not be conflated with ordinary
single-fact promotion:

- curated World Skills admission, currently one explicit direct exception;
- compound truth-maintenance supersede, which atomically validates a replacement and
  deprecates the old fact.

## Decision

Add an AST-based production ownership test that scans `server.py` and every Python file
under `core/`.

It maintains an exact reviewed set of calls to:

- `validate_and_promote()`;
- `promote_to_validated()`.

It separately maintains an exact reviewed set of literal `Validated` calls to:

- `transition_esm()`;
- `promote_esm_to()`.

The expected call-site sets are keyed by file, class/function scope, and callee name.
Line numbers are deliberately excluded so harmless formatting changes do not require an
allowlist update.

## Reviewed low-level sites

Allowed low-level sites are limited to:

- `PromotionGateway.promote()` delegating to its injected store;
- two reload-safe current-memory adapters used behind PromotionGateway;
- module-level compatibility wrappers in `core.memory`;
- `SQLiteGraphStore.promote_to_validated()`, the one reviewed compatibility primitive
  that internally invokes the generic ladder with a literal `Validated` target;
- one exact curated World Skills ingest exception.

The compatibility primitive is not a business caller exception: it is the implementation
behind an already inventoried low-level API. No external module is allowed to add another
literal plain transition to `Validated`.

A new site is a blocking CI failure. Adding one requires both an ADR and a synchronized
update to `docs/operations/promotion-ownership-inventory.md`.

## Why the curated exception remains explicit

World Skills rows are curated offline knowledge units and currently lack the standard
BALANCED-mode evidence-reference contract. Automatically sending them through the
standard gateway would reject the pack; weakening TruthGate would weaken unrelated
runtime facts. The one direct call remains visible and locked until a separate curated
admission contract exists.

## Validation evidence

The first full repository run proved the guard was active and found one mismatch: the
initial literal-target set incorrectly assumed there were zero literal `Validated`
steps, while `SQLiteGraphStore.promote_to_validated()` implements its compatibility
primitive by calling `promote_esm_to(..., "Validated")`.

A temporary dependency-free AST diagnostic reproduced the exact production inventory:

- six reviewed direct authority sites;
- one literal Validated step inside the low-level compatibility primitive;
- no additional business/runtime caller.

The diagnostic workflow, script, and output file were removed. The permanent guard now
locks that single primitive by exact file, semantic scope, and callee instead of broadly
allowing all calls originating from `core.memory`.

The final three-file change-set must pass architecture-freeze, Ruff, blocking mypy and
full repository pytest. Docker is `NOT_APPLICABLE` because the PR changes only tests and
documentation and the Docker workflow's path filter does not schedule a runtime build.

## Non-goals

This guard does not:

- make PromotionGateway the sole owner by declaration;
- authorize the curated exception for user/runtime facts;
- redesign compound supersede;
- inspect tests, docs, or generated examples;
- replace architecture-freeze, type checking, full pytest, Docker, or human review;
- introduce receipt persistence or an outbox.

## Exit condition

The explicit World Skills exception may be removed from the allowlist only after a
curated-pack admission contract proves deterministic pack identity, signed/reviewed
provenance, bounded authority, replay, and atomic audit evidence.
