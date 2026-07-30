# 🎛️ D16 Executive Control — Research Contract

**Status:** `RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Decision ID:** D16 (existing architecture decision; this document does not create D23 or another controller)  
**Date:** 2026-07-30  
**Scope:** versioned proposal vocabulary, policy binding and baseline semantics for future executive-control experiments

## Decision

D16 is currently a **contract target**, not an implemented runtime controller.
Its purpose is to prevent research components from inventing incompatible route
labels or claiming authority that does not exist.

The authoritative behaviour on `main` remains:

```text
POST /query
→ legacy retrieval and answer path
→ authoritative response

optional ENABLE_SYNAPTIC_SHADOW
→ SYNAPTIC_SHADOW_PREVIEW
→ passive receipt only
→ no answer, tool, memory or route change
```

Rapid Calibrated Orientation may emit a proposal conforming to this contract.
Nothing in this document permits that proposal to execute.

## Contract version

```text
contract_id      = titan.d16.executive-control
contract_version = d16-research-v1
authority        = proposal_only
fallback         = LEGACY_QUERY
```

Any future semantic change to routes, snapshot binding, fallback or authority
requires a contract-version increment and explicit Operator review.

## Route vocabulary

### Observed baseline routes

| Route | Current meaning | Authority |
|---|---|---|
| `LEGACY_QUERY` | Existing `/query` retrieval and answer path | Authoritative current runtime |
| `SYNAPTIC_SHADOW_PREVIEW` | PR-SYN-06 passive Gate/ContextPack observation | Receipt only; cannot affect the answer |

### Proposal-only routes

| Route | Intended research meaning | Required evidence before activation |
|---|---|---|
| `FAST_LOCAL` | Existing local path appears sufficient | unsafe-fast evaluation, policy checks and rollback |
| `DELIBERATE_LOCAL` | More local reasoning or retrieval appears necessary | bounded cost and latency contract |
| `REQUEST_EVIDENCE` | A critical evidence gap must be filled | explicit gap and acceptable evidence type |
| `CLARIFY` | User intent or constraints are materially ambiguous | concrete clarification question |
| `DEFER` | Work should be revisited later | reason, review trigger, expiry and operator override |

`RETRIEVE`, `COMPUTE`, `RESEARCH` and `PARALLEL` are not contract routes
in v1. An experiment may record them as internal labels only when it maps them to
one route above in its receipt.

## Proposal schema

Illustrative research notation, not a committed Python API:

```text
CognitiveRouteProposal
├── contract_id
├── contract_version
├── proposal_id
├── request_id
├── projection_id
├── route
├── reason_codes[]
├── evidence_refs[]
├── critical_gaps[]
├── confidence
├── estimated_cost
├── policy_snapshot_id
├── policy_version
├── capability_lease_refs[]
├── fallback = LEGACY_QUERY
└── generated_at
```

A proposal is invalid when the route is unknown, fallback is absent, evidence is
not visible to the request, or policy identity is missing.

## Policy and capability binding

D16 proposals never carry a generic “allowed” flag. They bind to the immutable
policy view used to create them:

```text
OrientationProjection.policy_snapshot_id
  == CognitiveRouteProposal.policy_snapshot_id
  == UnderstandingReceipt.policy_snapshot_id
```

For every optional tool, provider or network action, the receipt must retain the
full current `CapabilityLease` identity:

- capability;
- locality;
- data mode;
- allowed;
- reason code;
- `snapshot_id`;
- `policy_version`.

Before any future execution, both `snapshot_id` and `policy_version` must
match the active projection and plan. A stale, partial or mismatched lease is a
hard denial. A denial may produce a new proposal or auditable `DEFER`; it may
not be converted into permission.

## Selection semantics

A future controller candidate must apply this order:

1. enforce PolicyKernel, Recall Policy, provenance and evidence dependencies;
2. reject stale leases and unknown route labels;
3. preserve the authoritative fallback;
4. assess critical gaps and risk;
5. select only among routes permitted for the current snapshot;
6. emit an `UnderstandingReceipt`;
7. leave Canon, ESM and task state unchanged unless a separate authorised write
   service is explicitly invoked.

Soft confidence, attention score or model prose can never override steps 1–3.

## Receipt requirements

The receipt must explain:

- proposal and fallback;
- input/projection digests;
- evidence used and evidence omitted;
- critical gaps and contradictions;
- policy and lease identities;
- reason codes;
- estimated and actual cost;
- whether the proposal agreed with the legacy baseline;
- whether any action was attempted;
- final non-interference result.

Hidden chain-of-thought is neither required nor stored. The receipt contains
structured reasons and evidence references only.

## Failure behaviour

| Failure | Required result |
|---|---|
| Missing policy snapshot | reject proposal |
| Snapshot or policy-version mismatch | reject as stale |
| Missing required provenance/evidence | `REQUEST_EVIDENCE` or `DEFER` |
| Unknown route | reject and use `LEGACY_QUERY` baseline |
| Budget unavailable or malformed | fail closed; no optional action |
| Proposal exception | isolate failure; preserve legacy response |
| Conflicting evidence | surface conflict; never auto-promote |
| Operator threshold unavailable | remain shadow-only |

## Shadow evaluation

The first implementation candidate must only compare:

```text
actual LEGACY_QUERY outcome
vs
proposal-only D16 route
vs
operator-labelled sufficient route
```

Minimum segmented metrics:

- route agreement and reviewed routing accuracy;
- unsafe-fast rate;
- false-defer rate;
- critical-gap recall;
- confidence calibration;
- latency and compute cost;
- stale-lease rejection rate;
- policy non-interference;
- deterministic stability.

No average metric may hide a failure in a high-risk task class.

## Activation gates

A bounded active D16 slice requires all of:

1. stable PR-SYN-06 passive receipts;
2. versioned schemas and deterministic IDs;
3. operator-labelled evaluation data;
4. approved unsafe-fast and false-defer thresholds;
5. lease replay and policy-version mismatch tests;
6. fail-isolated fallback tests;
7. zero-model local path;
8. feature flag and rollback;
9. no direct Canon or ESM write;
10. explicit Operator GO in a separate PR.

## Explicit non-goals

This contract does not create:

- a second PolicyKernel, TruthGate, Recall Policy or task store;
- an `EssenceEngine`, D23 or new C-level;
- active routing authority;
- silent `IGNORE`;
- mandatory LLM, embeddings or remote provider;
- automatic truth promotion;
- hidden policy weakening.

## Core rule

```text
D16 names and validates proposals.
Policy and leases bound what may be attempted.
LEGACY_QUERY remains the authoritative fallback.
No runtime controller exists until evidence and Operator GO say otherwise.
```
