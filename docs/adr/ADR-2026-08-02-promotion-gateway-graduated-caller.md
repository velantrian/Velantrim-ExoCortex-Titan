# ADR — Migrate graduated promotion through PromotionGateway

**Status:** accepted for one caller only  
**Date:** 2026-08-02  
**Issue:** #165  
**Dependency:** PromotionGateway foundation PR #166

## Context

`core.promotion_policy.run_graduated_promotion()` already treats its own
corroboration, age and confidence checks as pre-vetting. Its final
`Supported → Validated` hop called `store.validate_and_promote()` directly and
used `TruthGateVerdict.passed` for existing report accounting.

The call was already safe at the store boundary, but it bypassed the typed
PromotionGateway ownership contract and could not produce the common
content-minimized receipt.

## Decision

Migrate only the graduated-promotion final hop:

```text
pre-vetting remains unchanged
→ PromotionRequest(target=Validated, requested_by=graduated_promotion)
→ PromotionGateway
→ existing validate_and_promote()
→ existing TruthGate + CAS mutation
→ receipt.passed mapped to existing report accounting
```

The gateway is constructed once per `run_graduated_promotion()` invocation and
called exactly once for each candidate whose recommended target is `Validated`.

## Verdict actor boundary

Focused integration exposed an existing distinction in the store contract:

- the caller passes `by="graduated_promotion"` when requesting evaluation;
- a rejected TruthGate verdict is returned with `by="truth_gate"`;
- a passed verdict that commits the CAS transition is returned with the caller
  actor.

The gateway therefore records two explicit fields:

- `requested_by` — the component requesting the promotion attempt;
- `decided_by` — the component issuing the verdict.

A rejection may be decided by `truth_gate`. A passed or idempotent-success verdict
must be attributed to `requested_by`, because it claims mutation semantics for that
caller. Any other actor value fails closed. This preserves rejection accounting
without allowing an ambiguous actor to claim a commit.

## Reload-safe verdict contract

The full repository suite reloads selected `core` modules while testing import and
configuration isolation. That exposed a Python class-identity hazard: a verdict
created by a reloaded `core.truth_gate.TruthGateVerdict` has the correct fields and
semantics but is not an `isinstance` of the class object imported by
`core.promotion_gateway` before the reload.

The gateway therefore validates the verdict structurally rather than trusting
concrete class identity. This is not permissive duck typing: the gateway requires
and validates every decision-bearing field:

- `passed`, `fact_id`, `reason`, `justification`;
- `by`, `mode`, `confidence`, `evidence_count`;
- `contradictions`, `checked_at`.

It then enforces actor attribution, target fact identity, stable cognitive-mode
value, finite confidence bounds, evidence-count type, contradiction-reference type,
known commit semantics and timestamp presence. Missing or malformed fields fail
closed with `PromotionContractError`.

The immutable outcome normalizes the mode to the request's local `CognitiveMode`
instance. This prevents a reloaded enum identity from escaping into receipts while
preserving the stable mode value that the store evaluated.

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

Focused validation covers:

- no direct store validation call from graduated promotion;
- exactly one gateway request for a qualifying candidate;
- accepted and rejected accounting unchanged;
- rejected candidates remain retryable after evidence is added;
- request/decision actor separation;
- malformed verdicts fail closed;
- a structurally valid verdict from a different/reloaded class identity is accepted;
- existing real-store ladder and TruthGate enforcement tests.

The clean current-main PR must additionally pass architecture-freeze, Ruff,
blocking mypy, full repository pytest and Docker on its final head.

## Non-claims

After this migration PromotionGateway is `RUNTIME_WIRED` for one optional caller,
but it is not the sole promotion owner and the feature is not necessarily
`FEATURE_ENABLED` in a deployment. This does not introduce transactional outbox
persistence or a general production-readiness claim.
