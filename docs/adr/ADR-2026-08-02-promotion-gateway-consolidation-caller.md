# ADR — Migrate ConsolidationEngine through PromotionGateway

**Status:** accepted for one caller only  
**Date:** 2026-08-02  
**Issue:** #165  
**Dependency:** PromotionGateway foundation #166 and graduated caller #168

## Context

`ConsolidationEngine` already has a hardened two-stage path for candidates selected by
its confidence, claim-length and utility pre-vetting:

1. walk the legal ESM ladder to `Supported` with `promote_esm_to()`;
2. call `validate_and_promote()` for the final TruthGate + CAS hop to `Validated`.

It also has mature accounting rules:

- TruthGate rejection increments `rejected_by_truthgate` and leaves the fact at
  `Supported` for a later rescan;
- ordinary exceptions increment `errors`;
- checksum/integrity refresh runs only after a successful promotion and can increment
  only `checksum_refresh_errors`;
- an illegal ladder jump may use the existing Hypothesized fallback;
- a failed bare Hypothesized transition is an error, not a TruthGate rejection.

The final validation call is safe, but it bypasses the common typed request/receipt
contract introduced by PromotionGateway.

## Decision

Migrate only the final single-fact validation call:

```text
ConsolidationEngine pre-vetting
→ legal ladder to Supported
→ PromotionRequest(requested_by=consolidation_engine)
→ PromotionGateway
→ existing validate_and_promote()
→ existing TruthGate + CAS transaction
→ receipt.passed mapped to existing ConsolidationReport accounting
```

A gateway instance is created once with the engine and reused for the engine's batch.
The gateway does not own scanning, utility decisions, ladder movement, report counters,
checksum refresh or retries.

## Preserved behavior

- confidence, claim-length, utility and batch thresholds are unchanged;
- `prefer_validated=False` continues to use the existing Hypothesized transition path;
- `promote_esm_to(..., "Supported")` remains before the gateway call;
- a gateway/TruthGate rejection increments `rejected_by_truthgate`;
- the rejected fact remains `Supported` and is eligible for the existing rescan;
- a gateway exception increments `errors` through the existing exception boundary;
- no automatic retry is added for `concurrent_modification`;
- the existing `ValueError` fallback behavior is unchanged;
- checksum refresh remains outside the promotion decision and cannot alter its outcome;
- no receipt persistence, outbox dispatch or remote authority is introduced.

## Validation

The self-removing exact-patch run completed successfully and proved:

- a qualifying Validated candidate makes one gateway request;
- the engine does not directly call `validate_and_promote()`;
- request actor is `consolidation_engine`;
- accepted/rejected/error accounting is unchanged;
- failure to reach `Supported` does not call the gateway;
- existing P0-D real-store rejection and later-evidence retry tests remain green;
- issue #26 checksum accounting tests remain green;
- PromotionGateway reload-safe and malformed-contract suites remain green.

Temporary workflow/script files removed themselves and are absent from the final
three-file diff. Architecture-freeze, Ruff, blocking mypy, full pytest and Docker on the
final maintainer-authored head remain the merge evidence.

## Scope boundary

This decision does not migrate:

- the direct API transition endpoint;
- tool handlers;
- pipeline ingestion;
- compound truth-maintenance supersede;
- CognitiveStore, relations, world-skills or Ring Zero paths.

It does not introduce the transactional outbox. PromotionGateway remains an in-process
ownership and evidence boundary.

## Non-claims

After this PR the gateway is runtime-wired for two optional internal callers. It is not
the sole promotion owner, and this is not evidence of general production readiness.
