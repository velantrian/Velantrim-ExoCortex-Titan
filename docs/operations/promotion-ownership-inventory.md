# Promotion ownership inventory

**Baseline:** `main@dae864606db75edfe04a3ee24af7d6bfde3e7ca8`  
**Issue:** #165  
**Status:** runtime-wired for five standard callers; not yet the sole owner

## Canonical hardened primitive

`SQLiteGraphStore.validate_and_promote()` remains the authoritative single-fact write to
`Validated`:

```text
durable L1 snapshot
→ ESM legality check
→ TruthGate evaluation
→ CAS-guarded canonical update
→ VersionStore + AuditChain in the same transaction
→ post-commit L0 publication
```

`PromotionGateway` owns the typed request, fail-closed verdict validation, transient
outcome, and content-minimized receipt. It delegates exactly once to the primitive and
does not duplicate thresholds or database mutation logic.

## Runtime-wired standard callers

| Caller | Status | Preserved boundary |
|---|---|---|
| `core/promotion_policy.py::run_graduated_promotion` | merged via #168 | module thresholds remain pre-vetting; TruthGate rejection remains separately accounted |
| `core/consolidation_engine.py` | merged via #169 | ladder to `Supported`, retryable rejection, checksum-maintenance separation |
| `PATCH /facts/{fact_id}/transition` | merged via #170 | existing 404/409/422/200 HTTP contract, auth, CAS and Ring Zero protections |
| `core/tool_handlers.py::validate_fact` | merged via #171 | guardian response contract and reload-safe current-memory store resolution |
| `core/cognitive_store.py::CognitiveFactStore.transition` | merged via #172 | auto-ladder only to `Supported`, gated final hop, no rejected/idempotent phantom event; covers `CognitiveRuntime` delegation |

These paths are `RUNTIME_WIRED`. This is code/test evidence, not a claim that the feature
is globally activated, runtime-observed in production, or backed by a transactional
outbox.

## Reviewed direct authority calls

Production code still contains a small set of low-level calls. They are intentionally
locked by `tests/test_promotion_ownership_guard.py`:

1. `PromotionGateway.promote()` delegates to its injected store authority.
2. Reload-safe adapters in `core/tool_handlers.py` and `core/cognitive_store.py` resolve
   the current `core.memory` module, then delegate for the gateway.
3. Module-level compatibility wrappers in `core/memory.py` delegate to `_GLOBAL_STORE`.
4. `core/world_skills_ingest.py` is the explicit curated-ingest exception described
   below.

Any new production call to `validate_and_promote()` or `promote_to_validated()` fails CI
until this inventory and an ADR are deliberately updated. CI also rejects literal plain
`transition_esm(..., "Validated")` and `promote_esm_to(..., "Validated")` caller paths.

## Explicit exception: curated World Skills ingest

`core/world_skills_ingest.py::ingest_facts()` promotes a reviewed offline knowledge pack
through `store.promote_to_validated()`.

This is **not** silently classified as a standard PromotionGateway caller because:

- the pack is curated and uses a separate knowledge-store workflow;
- current rows have confidence and provenance metadata but do not carry the normal
  BALANCED-mode `evidence_refs` contract;
- routing it through the current gateway without a separate design would reject the
  pack, while weakening TruthGate to accept it would weaken every standard caller.

Disposition:

```text
KNOWN_EXCEPTION
→ no threshold bypass expansion
→ no use as a template for runtime/user facts
→ design a curated-pack admission contract separately
→ remove the exception only after that contract has signed provenance,
  deterministic pack identity, review evidence and replay tests
```

The exception remains one exact, CI-locked call site.

## Separate mutation families

| Family | Current behavior | Decision |
|---|---|---|
| `core/truth_maintenance.py::supersede` | TruthGate evaluates a replacement, then `supersede_fact_cas()` atomically creates/validates the new fact and deprecates the old fact | do not force into the single-fact v1 request; design a compound mutation request later |
| contradiction/deprecation/collapse | ordinary legal ESM transitions | outside PromotionGateway |
| invalidation | CAS-guarded temporal close with audit evidence | outside PromotionGateway |
| relation lifecycle in `core/relations.py` | relation-state ladder, not fact Canon promotion | outside PromotionGateway |
| Ring Zero seed/immutable paths | protected special-case authority | outside PromotionGateway |

## Generic helper classification

`SQLiteGraphStore.promote_esm_to()` remains a broad ESM ladder helper. Current production
classification is:

- ConsolidationEngine: literal target `Supported`, followed by PromotionGateway;
- CognitiveFactStore: non-Validated targets remain generic; Validated is intercepted,
  laddered only to `Supported`, then gated;
- relation store: a different relation-state implementation;
- memory module wrapper: compatibility primitive, not a business caller.

No reviewed production caller passes a literal `Validated` target to the generic fact
ladder. The ownership guard makes a future literal bypass a blocking test failure.

## Pipeline status

`core/pipeline.py::run()` is read-only with respect to ESM promotion. It retrieves and
scores memory but explicitly does not store or promote facts. It therefore requires no
PromotionGateway migration. Any future pipeline write authority would be a new
architecture decision and must first satisfy the architecture-freeze and ownership
guards.

## Current status

```text
DESIGNED                 ✅
MERGED_IN_MAIN           ✅
RUNTIME_WIRED            ✅ five standard callers
FEATURE_ENABLED          caller/profile dependent
RUNTIME_OBSERVED         not claimed
SOLE_SINGLE_FACT_OWNER   ❌ curated ingest exception + compatibility primitives remain
OUTBOX_ATOMIC             ❌ not implemented
```

## Migration gates

Every additional standard caller migration must prove:

- exactly one gateway call per promotion attempt;
- no new direct route to `Validated`;
- unchanged TruthGate mode and thresholds;
- unchanged rejection/accounting semantics;
- `concurrent_modification` remains visible and is not silently retried;
- no claim/evidence/justification payload in the replayable receipt;
- architecture-freeze, ownership guard, Ruff, blocking mypy, full pytest and Docker are
  green;
- final merge is pinned to the reviewed head SHA.

## Outbox boundary

No caller persists `PromotionReceipt` independently. Receipt persistence begins only
when a transactional outbox can write the mutation-evidence intent in the same SQLite
transaction as the canonical mutation. Until then receipts remain in-process results.
