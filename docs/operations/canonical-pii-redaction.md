# Canonical PII redaction — ownership and residual boundary

**Tracking:** issue #282 · parent #50  
**Implementation PR:** #283 (review-stage until merged)  
**Architecture decision:** `docs/adr/ADR-2026-08-10-pii-redaction-privacy-history-exception.md`

## Current ownership

```text
legacy callers
    |
    v
ForgettingEngine.redact_pii_fact()/redact_pii_batch()
    |
    v
CanonicalPiiRedactor
    |
    v
existing SQLiteGraphStore transaction
    +-- CAS-guarded facts.claim mutation
    +-- refreshed integrity metadata
    +-- fact_version bump
    +-- privacy-sanitized VersionStore history/boundary
    +-- content-free AuditChain event
    +-- synchronous FTS refresh when present
    `-- content-free projection outbox refresh when migration 020 is active
```

`CanonicalPiiRedactor` is the single owner for the PII **claim-redaction mutation
family**. It is not a general Canon service and does not own ESM promotion, physical
erasure, archival, causal relations, scheduling, runtime activation, or policy
escalation.

## Privacy-history rule

Ordinary Titan lifecycle mutations preserve their exact pre-image in `fact_versions`.
PII redaction is intentionally different: exact plaintext recovery of the removed PII
would make the version store itself a residual PII store.

For a successful redaction, affected historical `fact_versions.claim` values are
sanitized in the same transaction and their integrity metadata/checksum is recomputed.
The redaction boundary VersionStore row is also inserted with the sanitized claim. A
content-free AuditChain event records that the canonical fact was updated without
persisting the removed claim in the new event.

This is a narrow privacy exception, not a general permission to rewrite history.

## Atomicity / failure semantics

A successful changed claim commits as one SQLite transaction. Any of the following
aborts the whole operation:

- source snapshot no longer matches the canonical row;
- VersionStore evidence cannot be written/sanitized;
- AuditChain append fails;
- an activated projection-outbox contract cannot accept its refresh intent;
- another SQLite/storage failure occurs before commit.

No-PII is a true no-op and must not create version, audit or outbox evidence.

Batch redaction is bounded and all-or-nothing for its selected candidates. One stale
candidate rolls back changes to every other candidate in the same batch.

## Explicit non-claims

This mechanism redacts PII found by `core.forgetting.redact_pii()` from the fact's
**claim surface**. It does not prove physical erasure from all possible locations.
Specifically, this PR does not claim removal from arbitrary metadata, immutable raw
origins, every graph/vector/external backend, backups, third-party systems, or legacy
logs. Full data-subject erasure remains the durable erasure coordinators' contract.

No GDPR certification, production readiness, current runtime enablement, current
Operator GO, runtime authority or production authority follows from this mechanism.

## Review checklist

Before treating PR #283 as implementation truth, verify its exact tested head and that:

- `core/forgetting.py` has no direct `UPDATE facts ... claim` redaction owner;
- state/confidence are preserved;
- current/historical claim surfaces covered by the contract contain no original PII;
- VersionStore integrity remains valid;
- new audit evidence is content-free;
- FTS/outbox behavior matches the ADR;
- rollback/concurrency tests pass;
- the PR is merged through protected `main` and post-merge CI is green.
