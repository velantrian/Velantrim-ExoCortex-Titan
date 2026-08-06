# 🔐 Continuity Source Admission Architecture

**Status:** `PROPOSED · DOCS-ONLY · NO RUNTIME AUTHORITY`  
**Base reviewed:** `main@73ef1c5e5d7acf6f60be926636cde67e52c66f24`  
**Implementation:** separate future Draft PRs only  
**Default:** disabled, unwired, fail-closed

## 1. Decision

Titan may derive typed Continuity observations from accepted projection results only through an explicit authenticated and subject-scoped admission boundary.

```text
accepted typed source result
        ↓
authenticated source context
        ↓
subject / tenant / purpose authorization
        ↓
source-envelope validation
        ↓
deterministic adapter proposal
        ↓
admission receipt
        ↓
authorized observation batch
        ↓
existing shadow signal producer
```

The source layer does not become a new truth, policy, identity, consent, memory, compute, reminder, scheduling or action authority.

Core rule:

```text
source result
≠ authorized source result
≠ admitted observation
≠ trusted aggregate
≠ compute decision
≠ user-visible behavior
```

## 2. Problem being solved

The current Continuity stack has strong deterministic contracts but no accepted live admission chain.

Existing source results expose useful typed state:

- `StateReconciliationResult` and `CurrentStateProjection` carry subject-scoped state, conflicts, displacement reasons and review requirements;
- `GoalProjectionResult` carries explicitly attested goal projections and exclusion decisions;
- `OpenLoopProjectionResult` carries typed open/resolved/overdue states;
- `ContinuitySignalObservation` carries content-addressed signal claims;
- `ContinuitySignalPolicy` filters producer, source type, confidence, evidence and scope.

The missing boundary is authorization context. Current observations and producer policy do not bind:

- authenticated principal;
- tenant or workspace;
- authorized subject;
- processing purpose;
- consent or other lawful basis;
- policy snapshot;
- retention class;
- erasure domain;
- source-result freshness and ownership proof.

The HTTP server currently authenticates requests with one shared API key. That proves possession of a deployment secret, not the identity of a user, tenant, subject or authorized processor. It must not be treated as subject authorization.

## 3. Existing owner map

| Concern | Existing owner | Source-admission rule |
|---|---|---|
| Hard runtime policy | `PolicyKernel`, `PolicySnapshot`, `CapabilityLease` | Reuse; do not create a second policy kernel |
| HTTP deployment authentication | `server.require_api_key` | Shared API key is transport authentication only |
| Actor and subject vocabulary | Continuity `ActorRef`, `SubjectRef` | Reuse typed refs; do not infer identity from text |
| State reconciliation | `StateReconciler` | Read deterministic results; do not alter reconciliation |
| Goal storage | `GoalStack` | Remains storage owner |
| Goal admission | `GoalAttestation`, `GoalProjector` | Only explicitly attested projections are eligible |
| Open-loop projection | `OpenLoopProjector` | Typed signals only; no raw-text inference |
| Observation shape | `ContinuitySignalObservation` | Existing v1 remains unchanged |
| Observation trust aggregation | `ContinuitySignalPolicy` and producer | Existing shadow aggregator remains unchanged |
| Canon and truth | TruthGate/TruthPolicy/WriteGate/PromotionGateway | No source-admission write or promotion |
| Erasure | durable erasure coordinator and subject-bound jobs | Admission artifacts must be erasure-addressable |
| Runtime route | `ComputeController` | No route ownership or behavior change |
| Activation | separate ADR + operator approval | This document authorizes none |

## 4. Non-authority boundary

This architecture creates no:

- raw-conversation parser;
- user identity provider;
- tenant directory;
- consent broker;
- new `PolicyKernel` decision type;
- Canon, TruthGate or ordinary memory write;
- `/query` behavior change;
- startup registration;
- worker, scheduler or daemon;
- automatic reminder or advice;
- tool or action execution;
- compute-route authority;
- durable observation store;
- network endpoint;
- feature enablement;
- live calibration claim.

`AUTHORIZED FOR ANALYSIS ≠ AUTHORIZED FOR STORAGE ≠ AUTHORIZED FOR ACTION`.

## 5. Required contracts

### 5.1 `ContinuityPrincipalContext`

Represents the authenticated caller or internal service identity supplied by an accepted authentication owner.

```text
ContinuityPrincipalContext
├── principal_ref
├── principal_kind
├── authentication_method
├── authentication_strength
├── authenticated_at
├── session_ref?
├── issuer_ref
└── credential_fingerprint?   # never a raw secret
```

Rules:

- caller-supplied strings are not sufficient authentication;
- no raw API key, token or credential enters the contract;
- shared deployment API-key authentication cannot claim an end-user principal;
- internal services require an explicit service identity and issuer;
- authentication time is caller-supplied and timezone-aware;
- principal identity is content-addressed or backed by an immutable authentication receipt.

### 5.2 `ContinuityAuthorizationContext`

Binds one source-admission operation to tenant, subject and purpose.

```text
ContinuityAuthorizationContext
├── tenant_ref
├── subject_refs[]
├── principal_context_id
├── purpose_code
├── lawful_basis_or_consent_ref
├── policy_snapshot_id
├── authorization_receipt_ref
├── retention_class
├── erasure_domain_refs[]
├── valid_from
├── valid_until
└── data_handling_mode
```

Required rules:

- `tenant_ref`, at least one `SubjectRef`, purpose and authorization receipt are mandatory;
- authorization validity is bounded in time;
- subject and tenant scope cannot be widened by an adapter;
- policy snapshot is evidence of the decision context, not a reusable permission forever;
- `CapabilityLease` may be referenced only for a narrowly named analysis capability; it grants no Canon, network, storage or action permission by implication;
- missing, expired, malformed or unverifiable authorization fails closed;
- consent withdrawal, restriction or erasure state dominates an older authorization receipt.

### 5.3 `ContinuitySourceEnvelope`

Wraps one immutable typed source result before derivation.

```text
ContinuitySourceEnvelope
├── envelope_id
├── schema_version
├── source_type
├── source_schema_version
├── source_result_id
├── source_digest
├── source_as_of
├── source_policy_version
├── producer_adapter_id
├── producer_adapter_version
├── authorization_context_id
├── subject_refs[]
├── evidence_refs[]
├── created_at
└── authority = "analysis_proposal_only"
```

The envelope identity includes all semantic fields except non-semantic transport metadata.

The source object itself remains owned by its original component. The envelope does not copy or reinterpret arbitrary raw text.

### 5.4 `ContinuityObservationDraft`

Adapter output before authorization admission.

```text
ContinuityObservationDraft
├── draft_id
├── signal_type
├── value
├── proposed_confidence
├── source_envelope_id
├── evidence_refs[]
├── reason_codes[]
├── scope?
└── derivation_rule_id
```

A draft is not a `ContinuitySignalObservation`. It cannot enter aggregation until admitted.

### 5.5 `ContinuityObservationAdmissionReceipt`

Immutable allow/deny evidence for one envelope and one deterministic set of drafts.

```text
ContinuityObservationAdmissionReceipt
├── receipt_id
├── source_envelope_id
├── authorization_context_id
├── policy_snapshot_id
├── adapter_id / version
├── draft_ids[]
├── admitted_draft_ids[]
├── rejected_drafts[]
│   ├── draft_id
│   ├── reason_code
│   └── evidence_refs[]
├── disposition
├── evaluated_at
└── authority = "observation_admission_only"
```

The receipt cannot authorize execution, persistence, Canon writes or user-visible output.

### 5.6 `AuthorizedContinuityObservationBatch`

The only live-eligible input boundary for future integration.

```text
AuthorizedContinuityObservationBatch
├── batch_id
├── authorization_context_id
├── admission_receipt_id
├── tenant_ref
├── subject_refs[]
├── observations[]          # existing v1 observations, batch-scoped
├── source_envelope_ids[]
├── policy_snapshot_id
├── created_at
└── no_runtime_authority = true
```

Rules:

- all observations belong to the same tenant and compatible subject scope;
- all observations must be traceable to admitted drafts;
- the batch identity binds observation IDs and authorization evidence;
- an unwrapped v1 observation is never live-eligible;
- global persistence or cross-boundary transport of v1 observations is forbidden without their batch and receipt;
- mixed-tenant batches are invalid;
- mixed-subject batches require an explicit multi-subject authorization receipt;
- a batch cannot be reused after authorization expiry, withdrawal, restriction or erasure.

## 6. v1 compatibility decision

`ContinuitySignalObservation` v1 remains unchanged.

Adding tenant, subject or consent fields directly to v1 would silently change content identity and break replay compatibility. The first implementation must therefore preserve v1 as a pure shadow observation and bind authorization at the batch boundary.

```text
v1 observation alone
→ structurally valid
→ possibly accepted by the pure shadow aggregator
→ NOT live-authorized

v1 observation + valid authorized batch + admission receipt
→ eligible for a future disabled integration experiment
```

If observations later need independent persistence, transport or cross-process replay, define a new explicit schema version whose identity includes an authorization-context digest. Do not mutate v1 semantics in place.

## 7. Source adapters

Adapters are deterministic proposal producers. They do not authenticate callers or make authorization decisions.

### 7.1 State reconciliation adapter

Eligible source: `StateReconciliationResult`.

Potential derivations:

| Source condition | Proposed signal | Constraint |
|---|---|---|
| contested/unresolved projection | `context_degraded=True` | subject-scoped evidence required |
| contradiction refs present | `active_contradiction=True` | one scope per state key |
| stale/expired-only projection | context freshness | deterministic status mapping |
| current-state request requires fresh projection | `requires_current_state=True` | request purpose must permit it |
| complete current projection | evidence coverage item | only for explicitly defined required state keys |

Forbidden derivations:

- `important_claim` from arbitrary predicate text;
- user intent from model-inferred assertions;
- sensitivity from free-form content;
- truth or Canon admission;
- automatic answer or route selection.

### 7.2 Goal projection adapter

Eligible source: `GoalProjectionResult`.

Rules:

- only projections with explicit `GoalAttestation` are eligible;
- excluded goals cannot generate positive evidence coverage;
- goal `user_id`, authorization subject and tenant scope must match;
- an active goal does not imply reminder, scheduling or action permission;
- goal priority is not automatically compute sensitivity;
- model recurrence cannot create a goal or attestation.

Potential outputs are limited to evidence coverage and narrowly defined current-state requirements.

### 7.3 Open-loop projection adapter

Eligible source: `OpenLoopProjectionResult`.

Rules:

- typed `OpenLoopSignal` is required; no raw-text loop discovery in the first slice;
- `OPEN` or `OVERDUE` may propose `requires_current_state=True` only for an authorized analysis purpose;
- `RESOLVED` cannot be silently reopened;
- deadline presence does not authorize scheduling or notification;
- related goal references must belong to the same authorized subject scope;
- no action, reminder or user-visible advice is emitted.

## 8. Authorization evaluation order

Required fail-closed sequence:

```text
validate principal authentication receipt
→ validate authorization-context identity
→ validate tenant and subject scope
→ validate purpose and lawful-basis/consent reference
→ validate current restriction and erasure state
→ validate PolicySnapshot compatibility
→ validate source-result identity and freshness
→ validate adapter version and deterministic rule set
→ derive drafts
→ admit/reject each draft
→ emit immutable receipt
→ build authorized batch
```

No adapter code runs on source payloads before tenant/subject scope and source type are validated.

## 9. Reason codes

Minimum denial/rejection vocabulary:

```text
AUTHENTICATION_MISSING
AUTHENTICATION_UNVERIFIED
AUTHENTICATION_TOO_WEAK
PRINCIPAL_MISMATCH
TENANT_MISSING
TENANT_MISMATCH
SUBJECT_MISSING
SUBJECT_MISMATCH
CROSS_SUBJECT_REFERENCE
PURPOSE_MISSING
PURPOSE_NOT_ALLOWED
CONSENT_OR_BASIS_MISSING
AUTHORIZATION_EXPIRED
AUTHORIZATION_WITHDRAWN
RESTRICTION_ACTIVE
ERASURE_DOMAIN_BLOCKED
POLICY_SNAPSHOT_MISSING
POLICY_SNAPSHOT_INCOMPATIBLE
SOURCE_TYPE_NOT_ALLOWED
SOURCE_SCHEMA_UNSUPPORTED
SOURCE_ID_MISMATCH
SOURCE_TOO_OLD
SOURCE_FROM_FUTURE
ADAPTER_NOT_ALLOWED
ADAPTER_VERSION_UNSUPPORTED
DERIVATION_NOT_ALLOWED
EVIDENCE_SCOPE_MISMATCH
MIXED_TENANT_BATCH
MIXED_SUBJECT_BATCH
```

Reason codes are stable identifiers. Human-readable messages are projections and do not enter semantic identity.

## 10. Privacy, retention and erasure

Admission artifacts are derived personal-data surfaces when they reference a person or user-owned goal.

Required design:

- every envelope, draft, receipt and batch carries erasure-domain references;
- retention is explicit and bounded;
- no indefinite cache by default;
- source references are opaque identifiers, not copied content;
- sensitive category/level from Continuity contracts constrains admission and logging;
- logs must not contain raw user text, credentials or sensitive values;
- erased/restricted source refs invalidate dependent batches;
- replay must check current restriction/erasure state, not only historical authorization;
- a completed erasure job must be able to locate all persisted derived artifacts before persistence is approved;
- the existing append-only L0 residual limitation must be surfaced honestly and cannot be hidden by an admission receipt.

The architecture PR introduces no persistence, so no migration is permitted in this phase.

## 11. Security threat model

Minimum threats:

- shared API key misrepresented as user identity;
- caller chooses another user or tenant ID;
- model-generated `SubjectRef` treated as authenticated scope;
- cross-tenant observation aggregation;
- stale authorization replay;
- consent withdrawal ignored by cached batches;
- erased source resurrected by replay;
- adapter maps arbitrary text into `important_claim` or sensitivity;
- untrusted producer name copied into the trusted allowlist;
- source ID points to different content;
- source result belongs to another subject;
- mixed subject refs hidden in evidence lists;
- policy snapshot reused after runtime policy changed;
- batch detached from its receipt;
- unscoped v1 observations persisted globally;
- high-cardinality evidence causing resource exhaustion;
- raw secrets or personal text written to logs;
- admission receipt mistaken for execution permission.

## 12. Determinism and replay

All semantic timestamps are caller-supplied and timezone-aware.

Identity inputs are canonical JSON with sorted sets/lists where order is non-semantic.

Repeated evaluation of identical source, authorization context, policy snapshot and adapter version must produce identical:

- envelope ID;
- draft IDs;
- receipt ID;
- batch ID;
- observation IDs.

Wall-clock time, random UUIDs, process IDs, database row IDs and request ordering do not enter semantic identity.

Replay must fail closed if current erasure, restriction or policy state invalidates historical admission.

## 13. Resource budgets

The future implementation must define hard limits for:

- source results per admission call;
- projections per source result;
- subjects per authorization context;
- evidence refs per draft;
- drafts per envelope;
- observations per batch;
- serialized bytes;
- adapter execution time;
- batch age;
- nested/cross references.

Budget overflow rejects or truncates only under an explicit deterministic policy. Silent partial admission is forbidden.

## 14. First implementation slice

A future implementation PR may add contracts only:

- principal context;
- authorization context;
- source envelope;
- observation draft;
- admission receipt;
- authorized batch;
- deterministic validators and canonical serialization;
- unit/property tests.

It must not add:

- source adapters;
- server dependency injection;
- database migration;
- persistence;
- feature flag;
- runtime producer call;
- `/query` integration;
- background processing;
- user-visible output.

### Second slice

One adapter only: `StateReconciliationResult` → drafts, still invoked explicitly in tests or a local developer command. No runtime wiring.

### Third slice

Goal/OpenLoop adapters with explicit subject matching and adversarial tests. Still disabled.

### Fourth slice

Optional process-local shadow composition behind a separate feature flag, activation ADR and operator approval. No user-visible behavior.

## 15. Mandatory tests before any implementation merge

### Contract tests

- content-addressed IDs are stable across ordering and process runs;
- strings/bytes are rejected where collections are required;
- naive datetimes are rejected;
- duplicate refs are rejected;
- empty tenant/subject/purpose/receipt fields are rejected;
- authorization expiry and invalid intervals are rejected;
- semantic identity excludes transport-only metadata.

### Authorization tests

- shared API key cannot construct a user principal automatically;
- tenant mismatch rejects the entire envelope;
- subject mismatch rejects the entire envelope;
- mixed-tenant batch is impossible;
- cross-subject evidence is rejected;
- expired/withdrawn authorization is denied;
- active restriction/erasure state overrides old permission;
- PolicySnapshot mismatch is denied;
- denied receipt produces no batch.

### Adapter tests

- state conflict maps deterministically to a scoped contradiction draft;
- duplicate contradictions retain provenance but count unique scopes;
- model-inferred assertions cannot become user-attested goals;
- excluded goal produces no positive evidence-coverage draft;
- open loop never creates reminder/scheduler/action authority;
- arbitrary predicate/summary text cannot create `important_claim`;
- unsupported source schema fails closed;
- source digest mismatch fails closed.

### Isolation tests

- no Canon/TruthGate/PromotionGateway call;
- no GoalStack mutation;
- no ComputeController route change;
- no network, clock, environment or global mutable-state read in pure contracts;
- no `/query`, startup, worker or scheduler registration;
- no raw text or credential in logs/receipts.

## 16. Metrics for a future disabled shadow experiment

Only after contracts and adapters are accepted:

- envelopes evaluated;
- authorization denials by reason code;
- drafts proposed/admitted/rejected;
- subject/tenant mismatch count;
- stale-source rejection count;
- erasure/restriction invalidation count;
- observations per batch;
- producer aggregation result distribution;
- latency and budget rejection;
- replay-determinism failures;
- zero user-visible effect assertion.

Metrics must be bounded and must not contain raw personal content.

## 17. Stop conditions

Stop and keep Draft if any change introduces:

- principal identity derived from request text;
- tenant or subject chosen without an authorization receipt;
- shared API key treated as end-user identity;
- observation trust based only on producer name;
- unscoped persistence of v1 observations;
- automatic raw conversation extraction;
- Canon, TruthGate, memory or goal writes;
- compute-route, answer, reminder, scheduler, tool or action authority;
- current erasure/restriction bypass;
- new policy root parallel to `PolicyKernel`;
- hidden network access;
- runtime wiring mixed with contract approval;
- claims of live readiness without measured disabled-shadow evidence.

## 18. Progress by state

```text
Source-boundary audit:             1/1 = 100%
Architecture contract:             1/1 = 100%
Neutral contract implementation:   0/6 =   0%
State adapter:                     0/1 =   0%
Goal/OpenLoop adapters:            0/2 =   0%
Authorization integration:         0/1 =   0%
Privacy/erasure integration:        0/1 =   0%
Runtime wiring:                    0/1 =   0%
Runtime enabled:                   0/1 =   0%
Live observed evidence:            0/1 =   0%
```

## 19. Acceptance criteria for this document

The architecture is acceptable only if review confirms:

1. existing policy, truth, goal, erasure and compute owners remain authoritative;
2. shared API-key authentication is not confused with principal/subject authorization;
3. tenant, subject, purpose and current erasure/restriction state are mandatory;
4. v1 observation compatibility is preserved;
5. live eligibility exists only through an authorized batch and immutable receipt;
6. adapters are deterministic proposal producers with no authority;
7. raw conversation extraction and runtime wiring are explicitly deferred;
8. no new persistence or migration is introduced;
9. the staged implementation plan keeps every slice default-off;
10. architecture, implementation, testing, wiring, enablement and observation remain separate states.
