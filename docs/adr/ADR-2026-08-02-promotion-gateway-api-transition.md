# ADR — Migrate the public Validated transition through PromotionGateway

**Status:** accepted for one public caller only  
**Date:** 2026-08-02  
**Issue:** #165

## Context

`PATCH /facts/{fact_id}/transition` already routes the `Validated` target through the
hardened `validate_and_promote()` TruthGate + CAS path. Its adversarial regression suite
proves authentication, ESM legality, Ring Zero protection, atomic rejection, durable
snapshot use, deletion/weaken races, conflict status and audit-history integrity.

The endpoint still calls the store authority directly, so it does not use the common
PromotionGateway ownership contract. Its public error body also includes
`justification`, while the replayable `PromotionReceipt` intentionally excludes that
text.

## Decision

Migrate only the `Validated` branch:

```text
PATCH authentication + actor derivation
→ PromotionRequest(requested_by=api:<key digest>)
→ process-global PromotionGateway
→ existing validate_and_promote()
→ existing TruthGate + CAS transaction
→ transient verdict snapshot mapped to the unchanged HTTP contract
```

Ordinary non-Validated transitions continue through `transition_esm()`.

## Transient justification boundary

`PromotionVerdictSnapshot` preserves the validated verdict justification for the
immediate in-process caller. `PromotionReceipt` remains content-minimized and does not
contain justification, claim text, evidence payloads, API keys, SQL, paths or exception
messages. Future outbox persistence may use only the receipt.

## Preserved HTTP semantics

- missing fact → `404` with the existing justification string;
- CAS race/deletion/weaken conflict → `409 concurrent_modification`;
- TruthGate rejection → `422 truth_gate_rejected` with reason, justification, mode,
  confidence and evidence count;
- successful promotion → existing `200` fact response;
- illegal ESM jump → `400` before TruthGate;
- Ring Zero and ImmutableCore protections remain unchanged;
- authentication and API actor hashing remain unchanged;
- no retry is added.

## Scope boundary

This change does not alter TruthGate thresholds, ESM transitions, response models,
request models, authentication, pipeline ingestion, tool handlers, compound supersede,
receipt persistence or remote authority.

## Validation

The final clean head must pass:

- static single-gateway wiring invariants;
- transient-justification/receipt-minimization tests;
- the complete `test_truthgate_api_transition.py` adversarial suite;
- architecture-freeze, Ruff, blocking mypy, full repository pytest and Docker.

Focused validation passed 44/44 tests after the exact server patch was applied. The
first run exposed a test-only false positive: a raw substring assertion treated
`validate_and_promote` mentions in the endpoint docstring as executable bypasses. The
wiring gate now parses `server.py` with `ast`, rejects direct name or attribute calls in
`transition_fact`, and separately rejects importing `validate_and_promote` from
`core.memory`. Documentation text cannot satisfy or fail this authority check.

The one-shot workflow and patch script removed themselves after focused success. The
final pull-request diff contains only the gateway snapshot adjustment, server wiring,
caller ADR and two permanent regression-test files.

## Non-claims

After this migration the gateway owns three callers, but it is still not the sole
promotion owner. This does not create a transactional outbox or general production
readiness.
