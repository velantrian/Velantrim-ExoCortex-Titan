# ADR — Migrate graduated promotion through PromotionGateway

**Status:** accepted for one caller only  
**Date:** 2026-08-02  
**Issue:** #165  
**Dependency:** PromotionGateway foundation PR #166

## Context

`core.promotion_policy.run_graduated_promotion()` already treats its own
corroboration, age and confidence checks as pre-vetting.  Its final
`Supported → Validated` hop calls `store.validate_and_promote()` directly and
uses the returned `TruthGateVerdict.passed` value for existing report accounting.

The call is already safe at the store boundary, but it bypasses the new typed
PromotionGateway ownership and does not produce the common content-minimized
receipt.

## Decision

Migrate only the graduated-promotion final hop:

```text
pre-vetting remains unchanged
→ PromotionRequest(target=Validated, actor=graduated_promotion)
→ PromotionGateway
→ existing validate_and_promote()
→ existing TruthGate + CAS mutation
→ receipt.passed mapped to existing report accounting
```

The gateway is constructed once per `run_graduated_promotion()` invocation and
called exactly once for each candidate whose recommended target is `Validated`.

## Preserved behavior

- `recommend_transition()` thresholds are unchanged;
- the feature flag and default-disabled state are unchanged;
- `Observed → Hypothesized` and `Hypothesized → Supported` still use the existing
  legal ESM transition path;
- a rejected final candidate remains `Supported` and increments
  `rejected_by_truthgate`;
- an accepted candidate increments the existing `Supported->Validated` bucket;
- store/gateway exceptions still increment `errors` through the existing caller
  exception boundary;
- no retry is introduced for `concurrent_modification`;
- no receipt persistence or outbox write is introduced.

## Scope boundary

This decision does not migrate:

- `ConsolidationEngine`;
- the direct API transition endpoint;
- MCP/tool handlers;
- pipeline ingestion;
- `truth_maintenance.supersede()` compound mutation;
- CognitiveStore, relations, world-skills or Ring Zero paths.

Those require separate characterization and PRs.

## Validation

Focused tests must prove:

- no direct store validation call from graduated promotion;
- exactly one gateway request for a qualifying candidate;
- accepted and rejected accounting remains unchanged;
- existing real-store ladder tests remain green;
- architecture-freeze, Ruff, blocking mypy, full pytest and Docker pass on the
  final branch head.

## Non-claims

After this migration PromotionGateway is `RUNTIME_WIRED` for one optional caller,
but it is not yet the sole promotion owner and the feature is not necessarily
`FEATURE_ENABLED` in a deployment.
