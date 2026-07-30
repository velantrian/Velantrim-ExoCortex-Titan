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
→ attach a `synaptic_shadow` observation after LEGACY_QUERY completes
→ `source_mode = legacy_fact_projection`; `mode = shadow_only`
→ passive receipt only; no answer, tool, memory or route change
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

PR-SYN-06 is not a second route. It attaches a passive `synaptic_shadow`
observation to the completed `LEGACY_QUERY` response. The emitted receipt is
identified by `source_mode = legacy_fact_projection` and
`mode = shadow_only`; evaluation must never treat it as a selectable route.

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

### Compute path is an orthogonal recorded dimension

The existing `ComputeController` emits `FAST_PATH`, `NORMAL_PATH`, `DEEP_PATH`,
`VERIFY_PATH` and `CREATIVE_PATH`. Those values describe **how much and what kind
of computation is proposed**, while a D16 route describes **what continuation is
proposed**. They are not aliases and there is no implicit many-to-one translation.

A research receipt may therefore record:

```text
route        = FAST_LOCAL | DELIBERATE_LOCAL | REQUEST_EVIDENCE | CLARIFY | DEFER
compute_path = FAST_PATH | NORMAL_PATH | DEEP_PATH | VERIFY_PATH | CREATIVE_PATH | null
```

Any experiment that derives a D16 route from a compute path must declare a
separate, versioned `compute_path_mapping_id`, publish the complete mapping and
measure it independently. The mapping is evaluation metadata only; it grants no
authority and cannot make results from differently versioned mappings directly
comparable.

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
├── route_payload
├── compute_path
├── compute_path_mapping_id
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
not visible to the request, policy identity is missing, or the payload does not
match the selected route. `compute_path` and `compute_path_mapping_id` are
nullable; when either is present, both must satisfy the versioned mapping rule
above.

### Route-specific payloads

`route_payload` is a tagged union keyed by `route`:

| Route | Required payload |
|---|---|
| `FAST_LOCAL` | `{}` or an explicitly empty payload; no optional capability |
| `DELIBERATE_LOCAL` | bounded `budget` and `stop_conditions[]` |
| `REQUEST_EVIDENCE` | `gap_ids[]`, `acceptable_evidence_types[]`, and a `completion_condition` |
| `CLARIFY` | a concrete `question` and `blocking_ambiguity_ids[]` |
| `DEFER` | `reason_codes[]`, `review_trigger`, `expires_at`, and `operator_override` |

A missing field, an empty required list/string, or payload fields belonging to a
different route invalidate the proposal. `DEFER` remains reversible and
auditable; it never means `IGNORE` or task deletion.

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

Before any future execution, the runtime must capture a **fresh active
`PolicySnapshot` immediately before each optional action**. Its `snapshot_id`
and `policy_version` must match the projection, proposal, receipt and every
referenced lease. The snapshot itself must come from a verified, healthy policy
source: `reason_code = policy_dependency_unavailable`,
`supervisor_mode = unavailable`, a failed dependency-health indicator, or an
unverifiable snapshot origin makes the snapshot invalid even when IDs are
present. A non-missing but unhealthy snapshot never authorises a lease-free local
proposal.

The lease must also be revalidated as current, unexpired, unrevoked and scoped to
the exact capability, locality and data mode being attempted. Comparing an old
projection only with an old lease is never sufficient. Any stale, partial,
revoked, unhealthy or mismatched identity is a hard denial. A denial may produce
a new proposal or auditable `DEFER`; it may not be converted into permission.

## Selection semantics

A future controller candidate must apply this order:

1. enforce PolicyKernel, Recall Policy, provenance and evidence dependencies;
2. reject unhealthy snapshots, stale leases and unknown route labels;
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
- route and separately recorded compute path/mapping identity;
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
| Snapshot reports unavailable/unhealthy policy dependency | reject proposal; no local or optional action |
| Snapshot or policy-version mismatch | reject as stale |
| Missing required provenance/evidence | `REQUEST_EVIDENCE` or `DEFER` |
| Unknown route | reject and use `LEGACY_QUERY` baseline |
| Unknown or unversioned compute-path mapping | ignore mapping for route validity; mark receipt incomparable |
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
- stale-lease and unhealthy-snapshot rejection rates;
- policy non-interference;
- deterministic stability.

No average metric may hide a failure in a high-risk task class.

## Activation gates

A bounded active D16 slice requires all of:

1. stable PR-SYN-06 passive receipts;
2. versioned schemas and deterministic IDs;
3. operator-labelled evaluation data;
4. approved unsafe-fast and false-defer thresholds;
5. lease replay, unhealthy-snapshot and policy-version mismatch tests;
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
The D16 research contract names proposal vocabulary; research validators may validate it.
The active, healthy PolicySnapshot and current leases bound what may be attempted.
Compute path is separate evaluation metadata, not executive authority.
LEGACY_QUERY remains the authoritative fallback.
No runtime controller exists until evidence and Operator GO say otherwise.
```
