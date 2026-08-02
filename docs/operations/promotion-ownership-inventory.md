# Promotion ownership inventory

**Baseline:** `main@acb04085847da839c400a0e4a55fcf8692e5751d`  
**Issue:** #165  
**Status:** inventory for incremental migration; not a claim of unified ownership

## Canonical hardened primitive

`SQLiteGraphStore.validate_and_promote()` is the current hardened single-fact path to
`Validated`:

```text
durable L1 snapshot
→ ESM legality check
→ TruthGate evaluation
→ CAS-guarded canonical update
→ VersionStore + AuditChain in the same transaction
→ post-commit L0 publication
```

This primitive remains authoritative during the migration.  `PromotionGateway` wraps
it; it does not replace or reimplement the transaction.

## Confirmed direct callers

| Caller | Current behavior | Migration disposition |
|---|---|---|
| `server.py` direct transition endpoint | calls `validate_and_promote()` for external `Validated` requests | migrate after API response characterization |
| `core/tool_handlers.py::validate_fact` | calls `memory_api.validate_and_promote()` and exposes verdict reason/justification | migrate after tool contract characterization |
| `core/consolidation_engine.py` | pre-vets, walks to `Supported`, then calls `validate_and_promote()` | first runtime migration candidate after foundation |
| `core/promotion_policy.py` | graduated pre-vetting, then direct `validate_and_promote()` | first runtime migration candidate after foundation |

These callers already use the correct TruthGate + CAS primitive.  Migration is about
single ownership, typed receipts and later outbox integration, not changing thresholds.

## Separate mutation families

| Family | Current behavior | Decision |
|---|---|---|
| `core/truth_maintenance.py::supersede` | TruthGate evaluates a replacement, then `supersede_fact_cas()` atomically creates/validates the new fact and deprecates the old fact | do not force into the single-fact v1 request; design a compound mutation request later |
| contradiction/deprecation/collapse | ordinary legal ESM transitions | outside PromotionGateway; keep existing transition ownership |
| invalidation | CAS-guarded temporal close with audit evidence | outside PromotionGateway |
| Ring Zero seed/immutable paths | protected special-case authority | outside PromotionGateway |

## Legacy or broad helpers requiring characterization

`SQLiteGraphStore.promote_esm_to()` is a generic ladder walker.  Its own documentation
states that it can finish with a plain transition into `Validated` for callers outside
graduated promotion and consolidation.  Current code search identifies at least:

- `core/cognitive_store.py`;
- `core/relations.py`;
- internal uses in `core/memory.py`;
- `core/consolidation_engine.py` for the pre-validated walk to `Supported`.

These paths must not be bulk-rewritten.  For each caller first determine whether the
operation is:

1. only moving to `Hypothesized`/`Supported`;
2. test/seed-only;
3. Ring Zero/system initialization;
4. a genuine path to `Validated` that requires TruthGate + CAS;
5. a compound mutation that needs a different gateway contract.

## Pipeline status

Project status documentation records that pipeline ingestion and other internal
promotion paths use their own pre-vetting and do not yet share one contract-tested
promotion policy.  Before migration, add characterization tests for:

- target state;
- current-state assumptions;
- failure accounting;
- concurrent modification behavior;
- retriever-dirty and checksum side effects;
- whether the caller depends on `TruthGateVerdict.justification`;
- whether a rejected candidate remains retryable.

## Foundation status

The first `PromotionGateway` increment is:

```text
DESIGNED
→ IMPLEMENTED_IN_BRANCH
→ not runtime wired
→ not feature enabled
→ not runtime observed
→ not sole owner
```

It becomes `RUNTIME_WIRED` only after at least one real caller is migrated and tested.
It becomes the sole promotion owner only after direct single-fact paths are removed or
explicitly classified as exceptions.

## Migration gates

Every caller migration must prove:

- exactly one gateway call per promotion attempt;
- no direct new route to `Validated`;
- unchanged TruthGate mode and thresholds;
- unchanged rejection/accounting semantics;
- `concurrent_modification` remains visible and is not silently retried;
- no claim/evidence payload in the receipt;
- architecture-freeze, Ruff, blocking mypy, full pytest and Docker green;
- final merge pinned to the reviewed head SHA.

## Outbox boundary

No caller should persist `PromotionReceipt` independently.  Receipt persistence begins
only when the transactional outbox can write the mutation evidence intent in the same
SQLite transaction as the canonical mutation.  Until then receipts are in-process
results only.
