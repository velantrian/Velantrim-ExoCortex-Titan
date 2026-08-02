# ADR — Migrate `validate_fact` tool handler through PromotionGateway

**Status:** accepted for one guardian tool only  
**Date:** 2026-08-03  
**Issue:** #165  
**Dependency:** PromotionGateway foundation and the graduated, consolidation, and API caller migrations

## Context

`core.tool_handlers.validate_fact()` is a guardian-capability tool. It already calls the
hardened TruthGate + CAS authority, but it calls `core.memory.validate_and_promote()`
directly and therefore bypasses the common PromotionRequest/PromotionOutcome contract.

`core.tool_handlers` can outlive a `core.memory` module reload during tests and local
runtime reconstruction. The existing suite explicitly patches both the current memory
module and the handler's older module binding. A gateway permanently bound to the store
object present at import time would break this isolation and could write to the wrong
SQLite store.

## Decision

Migrate only `validate_fact()`:

```text
guardian tool dispatch
→ validate_fact(fact_id, by=tool:validate_fact)
→ PromotionRequest
→ PromotionGateway
→ reload-safe current-memory adapter
→ existing validate_and_promote()
→ existing TruthGate + CAS transaction
→ transient verdict snapshot mapped to the unchanged tool response
```

The adapter resolves the canonical `core.memory` module when the gateway delegates. It
adds no policy, threshold, retry, storage, or mutation of its own.

## Preserved behavior

- the default actor remains `tool:validate_fact`;
- accepted facts return `validated=True` and `epistemic_state=Validated`;
- rejected facts return `validated=False`, `epistemic_state=None`, the same reason code,
  and the same transient justification;
- weak facts remain at `Supported` after rejection;
- the existing TruthGate thresholds, CAS behavior, ESM legality, and audit path remain
  authoritative;
- no receipt is returned through the tool response;
- no automatic retry, outbox, remote authority, or feature flag is added.

PromotionRequest now fail-closes malformed actor identifiers. The registered MCP tool
manifest exposes no client actor field, so the normal guardian path continues to use the
fixed safe default.

## Validation

Focused validation must prove:

- `validate_fact()` makes one gateway call and no direct promotion-authority call;
- the request preserves fact ID and actor;
- response mapping uses the transient verdict snapshot, not the receipt;
- existing real-store weak-fact rejection remains green;
- module/store isolation in `tests/test_tool_handlers.py` remains green;
- PromotionGateway malformed-contract and reload suites remain green;
- architecture-freeze, Ruff, blocking mypy, full pytest, and Docker pass on the final
  clean head.

## Scope boundary

This PR does not migrate pipeline ingestion, compound truth-maintenance supersede,
CognitiveStore, world skills, or any non-Validated ESM transition. PromotionGateway is
not yet the sole promotion owner.
