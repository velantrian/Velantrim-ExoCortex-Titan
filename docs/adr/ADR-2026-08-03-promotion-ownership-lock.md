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

It separately rejects production calls that pass a literal `Validated` target to:

- `transition_esm()`;
- `promote_esm_to()`.

The expected call-site set is keyed by file, class/function scope, and callee name. Line
numbers are deliberately excluded so harmless formatting changes do not require an
allowlist update.

## Reviewed low-level sites

Allowed low-level sites are limited to:

- `PromotionGateway.promote()` delegating to its injected store;
- two reload-safe current-memory adapters used behind PromotionGateway;
- module-level compatibility wrappers in `core.memory`;
- one exact curated World Skills ingest exception.

A new site is a blocking CI failure. Adding one requires both an ADR and a synchronized
update to `docs/operations/promotion-ownership-inventory.md`.

## Why the curated exception remains explicit

World Skills rows are curated offline knowledge units and currently lack the standard
BALANCED-mode evidence-reference contract. Automatically sending them through the
standard gateway would reject the pack; weakening TruthGate would weaken unrelated
runtime facts. The one direct call remains visible and locked until a separate curated
admission contract exists.

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
