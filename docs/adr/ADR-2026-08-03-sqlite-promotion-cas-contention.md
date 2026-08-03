# ADR — Characterize single-winner promotion CAS contention

**Status:** accepted for evidence collection only  
**Date:** 2026-08-03  
**Dependency:** SQLite resilience #174, bounded busy timeout #175, disk-full rollback #176

## Context

Titan already has two related concurrency proofs:

- generic ESM writers sharing one stale preimage produce one successful transition and
  one CAS miss without a forked audit chain;
- adversarial API tests prove that deletion, weakening or an incompatible state change
  between TruthGate evaluation and the guarded write becomes
  `concurrent_modification`.

Those tests do not directly prove the final promotion boundary when **two independently
valid `validate_and_promote()` calls** evaluate the same `Supported` durable snapshot and
both reach `_promote_to_validated_cas()`.

## Decision

Add a permanent, test/docs-only characterization that:

1. creates one strongly evidenced fact through the public store path;
2. advances it legally to `Supported`;
3. opens two independent `SQLiteGraphStore` writers on the same database;
4. gates both immediately before their real conditional promotion UPDATE with one
   deterministic `threading.Barrier`;
5. runs both valid `validate_and_promote()` calls concurrently;
6. requires exactly one `passed / reason=passed` winner;
7. requires exactly one `passed=false / reason=concurrent_modification` loser;
8. requires one final `Validated` fact, one Validated history entry, one additional
   fact-version snapshot and one additional Validated AuditChain event;
9. requires `PRAGMA integrity_check = ok`.

## Required semantics

```text
two valid requests
+ same Supported durable snapshot
→ two conditional UPDATE attempts
→ exactly one commit winner
→ exactly one explicit concurrent_modification loser
→ one canonical Validated state
→ one version snapshot
→ one audit event
→ no automatic retry
```

The loser is not silently converted to idempotent success. A later caller may explicitly
read the now-Validated state and decide what to do, but the contested operation itself
must report that its precondition lost the race.

## Boundary

This increment changes no runtime code, threshold, TruthGate policy, timeout, retry
behavior, connection model, schema, database selection or PromotionGateway contract. It
does not introduce the transactional outbox.

## Interpretation boundary

The test proves deterministic two-writer contention at Titan's existing final promotion
CAS boundary on SQLite. It does not claim fairness, throughput under arbitrary writer
counts, distributed consensus, cross-database atomicity or correctness of future storage
backends.

## Merge gate

The final PR must contain only this ADR and the permanent characterization test.
Architecture freeze, repository hygiene, Ruff, blocking mypy and the full repository
pytest suite must pass on one pinned final head. Docker is `NOT_APPLICABLE` when the
repository's explicit test/docs path filter does not trigger it.

## Follow-up

Once this proof is green, the next independent core-hardening increment is a
transactional-outbox inventory and foundation. Outbox work must preserve the single
canonical fact mutation and append intent in the same transaction; dispatch remains a
separate post-commit concern.
