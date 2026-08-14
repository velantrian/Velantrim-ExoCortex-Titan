# Promotion ownership inventory

**C9 base:** `main@1909e3f10330c4032641970ad0934a67649681e3`  
**Issues:** #165, #52  
**C9 tracking:** PR #320  
**Status:** five standard runtime callers are gateway-routed; C9 removes the World Skills business-level direct-promotion exception while preserving reviewed compatibility primitives

## Canonical hardened primitive

`SQLiteGraphStore.validate_and_promote()` remains the authoritative single-fact write to
`Validated`:

```text
durable L1 snapshot
→ ESM legality check
→ TruthGate evaluation
→ CAS-guarded canonical update
→ VersionStore + AuditChain in the same transaction
→ (if migration 020 activated) projection_outbox intent, same transaction — issue #191
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
is globally activated or runtime-observed in production.

## Reviewed direct authority calls

Production code still contains a small set of low-level calls. They are intentionally
locked by `tests/test_promotion_ownership_guard.py`:

1. `PromotionGateway.promote()` delegates to its injected store authority.
2. Reload-safe adapters in `core/tool_handlers.py` and `core/cognitive_store.py` resolve
   the current `core.memory` module, then delegate for the gateway.
3. Module-level compatibility wrappers in `core/memory.py` delegate to `_GLOBAL_STORE`.

World Skills is deliberately absent from this direct-call inventory under C9. Its final
single-fact Canon admission is routed through `PromotionGateway`; reintroducing a direct
`promote_to_validated()` or `validate_and_promote()` call in that business path fails the
ownership guard.

Any new production call to `validate_and_promote()` or `promote_to_validated()` fails CI
until this inventory and an ADR are deliberately updated. CI also rejects literal plain
`transition_esm(..., "Validated")` and `promote_esm_to(..., "Validated")` caller paths.

## Curated World Skills admission — C9 convergence

The historical World Skills exception existed because curated rows were promoted through
`store.promote_to_validated()` without the standard TruthGate evidence contract. Fresh C9
audit showed that the legacy corpus also does **not** contain the complete #52 structured
provenance/risk/review metadata required to justify that shortcut.

PR #320 therefore does not weaken TruthGate and does not manufacture missing evidence.
Instead, `core/world_skills_ingest.py` treats every row as a candidate and enforces:

```text
Draft
→ Quarantine
→ Provenance Check
→ Domain Review
→ existing TruthGate precheck
→ legal ESM ladder to Supported
→ existing PromotionGateway
→ existing validate_and_promote()
→ TruthGate recheck + CAS
→ Validated / local Canon
```

Required candidate metadata is:

```text
truth_status
source_refs
confidence
risk_domain
limitations
review_status
reviewer
reviewed_at
```

Legacy rows receive explicit non-claims (`Draft`, empty source/review/risk fields,
`unreviewed`) and remain quarantined from Canon admission. The parser's historical
`confidence=0.85` value is retained for compatibility but cannot compensate for missing
provenance or review evidence.

C9 also provides deterministic candidate and order-independent pack SHA-256 identifiers
for content/replay binding. These digests are integrity identifiers, **not cryptographic
human signatures**. The older phrase "signed provenance" was underspecified: no reviewer
key or signature authority existed to support such a claim. C9 admits attributable
`source_refs`, explicit reviewer identity/timestamp, deterministic content binding, and
TruthGate evaluation. Any future cryptographic reviewer-signature protocol requires a
separate key/identity owner and separate admission.

The old `KNOWN_EXCEPTION` is therefore removed by C9 rather than expanded. World Skills
remains a curated offline ingestion surface, not a template for ordinary runtime/user
facts and not an alternate truth authority.

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
- World Skills C9: literal target `Supported` is reachable only after provenance/domain
  gates and a read-only TruthGate precheck; final `Validated` remains PromotionGateway-owned;
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
DESIGNED                              ✅
MERGED_FOUNDATION                     ✅
RUNTIME_WIRED_STANDARD_CALLERS        ✅ five standard callers
WORLD_SKILLS_DIRECT_EXCEPTION         ❌ removed by C9 candidate
WORLD_SKILLS_FINAL_GATEWAY_ROUTE       ✅ C9 candidate
LOW_LEVEL_COMPATIBILITY_PRIMITIVES     reviewed / intentionally retained
FEATURE_ENABLED                       caller/profile dependent
RUNTIME_OBSERVED                      not claimed
SOLE_BUSINESS_LEVEL_VALIDATED_BYPASS   none admitted by current ownership guard
OUTBOX_ATOMIC                         ✅ issue #191 — see below; still not a dispatcher or delivery guarantee
```

Do not reinterpret this table as runtime activation, production readiness, or a claim
that all World Skills rows are Canon-admissible. Legacy rows are intentionally quarantined
until real provenance and review metadata exists.

## Migration gates

Every additional standard or curated caller migration must prove:

- exactly one gateway call per final promotion attempt;
- no new direct business route to `Validated`;
- no duplicated or weakened TruthGate thresholds;
- unchanged rejection/accounting semantics unless an ADR explicitly changes them;
- `concurrent_modification` remains visible and is not silently retried;
- no claim/evidence/justification payload in the replayable PromotionGateway receipt;
- any pre-gateway ESM movement is non-Validated, legally bounded, and policy-evidenced;
- architecture-freeze, ownership guard, Ruff, blocking mypy, full pytest and Docker are
  green;
- final merge is pinned to the reviewed head SHA.

## Outbox boundary

No caller persists `PromotionReceipt` independently — this is unchanged by issue #191.
What changed there: `_promote_to_validated_cas()` (the one shared primitive under
`validate_and_promote()`, and therefore under all gateway-routed single-fact final
promotions) appends one content-minimized `projection_outbox` intent —
`aggregate_type="fact"`, technical `aggregate_id`, `scope_ref=LOCAL_PROJECTION_SCOPE_REF`,
`canonical_version=facts.fact_version` read on the same connection after the CAS
succeeds — in the SAME SQLite transaction as the Canon CAS UPDATE, VersionStore
pre-image and AuditChain event, on databases where migration 020 is activated (`PRAGMA
user_version >= 20`). A pre-v20 database is unaffected: no outbox feature exists there,
so no intent is appended and nothing about promotion changes. An activated database
missing either `projection_outbox` or `facts.fact_version` fails closed — the whole
promotion transaction, including Canon, rolls back rather than promoting without the
required intent (`ProjectionOutboxActivationError`, see
`ADR-2026-08-04-first-canon-caller-projection-outbox.md`).

This is durable intent, not a delivery guarantee: `PromotionReceipt` itself still is
not persisted independently of the in-process result.

## Dispatcher status (issue #193)

`core.projection_dispatcher` (migration 022, `projection_dispatch_state`) now exists
as a bounded, tested claim/lease/retry/ack primitive —
`claim_batch()` / `apply_claimed_work()` / `ack_claim()` / `retry_claim()` /
`park_claim()` / `dispatch_once()` — see
`ADR-2026-08-04-bounded-local-projection-dispatcher.md`. It is a plain callable, not
runtime-wired: no server startup registration, no background worker/scheduler, no
invocation cadence, no automatic repetition. Nothing today ever calls
`dispatch_once()` outside this primitive's own tests. At-least-once, not
exactly-once — a crash between a committed apply and its acknowledgement is
recoverable only because `apply_fts_projection()`'s idempotent, version-monotonic
contract makes every reapply safe.
