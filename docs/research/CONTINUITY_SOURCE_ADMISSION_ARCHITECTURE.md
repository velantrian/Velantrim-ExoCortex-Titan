# 🔐 Continuity Source Admission Architecture

**Status:** `PROPOSED · DOCS-ONLY · NO RUNTIME AUTHORITY`  
**Base reviewed:** `main@73ef1c5e5d7acf6f60be926636cde67e52c66f24`  
**Implementation:** separate future Draft PRs only  
**Default:** disabled, unwired, fail-closed

## 1. Decision

Titan may derive typed Continuity observations from accepted source results only through an explicit authenticated, tenant-scoped and subject-scoped admission boundary.

```text
accepted typed source result
        ↓
authenticated principal context
        ↓
tenant / subject / purpose authorization
        ↓
source identity + subject-binding validation
        ↓
deterministic adapter proposal
        ↓
immutable admission receipt
        ↓
authorized observation batch
        ↓
future admission-aware shadow facade
        ↓
existing pure signal aggregation
```

The source layer does not become a new truth, policy, identity, consent, memory, compute, reminder, scheduling or action authority.

```text
source result
≠ subject-bound source result
≠ authorized source result
≠ admitted observation
≠ trusted aggregate
≠ compute decision
≠ user-visible behavior
```

## 2. Problem being solved

The current Continuity stack has strong deterministic contracts but no accepted live admission chain.

Existing components provide:

- `StateReconciliationResult` and `CurrentStateProjection` with typed `SubjectRef`, conflicts, displacement reasons and review requirements;
- `GoalRecordSnapshot` with legacy `user_id` and typed goal metadata;
- `GoalProjectionResult` with explicitly attested goal projections and exclusion decisions;
- `OpenLoopProjectionResult` with typed open/resolved/overdue states;
- `ContinuitySignalObservation` with content-addressed signal claims;
- `ContinuitySignalPolicy` with producer/source/confidence/evidence/scope filtering.

The missing boundary is authenticated authorization context. Current observation and producer contracts do not bind:

- authenticated principal;
- tenant or workspace;
- authorized subject;
- processing purpose;
- consent or another accepted lawful basis;
- current policy snapshot;
- retention class;
- erasure domain;
- source-result ownership and subject-binding proof.

The HTTP server authenticates requests with one shared API key. That proves possession of a deployment secret, not the identity of an end user, tenant, subject or authorized processor. It must never be promoted into subject authorization.

## 3. Critical audit findings

### 3.1 State results may contain multiple subjects

`StateReconciliationResult` contains a collection of `CurrentStateProjection` values, and each projection has a typed `SubjectRef`. One result can therefore contain more than one subject.

Required rule:

```text
subjects(source result) == subjects(source envelope) ⊆ subjects(authorization)
```

The first adapter must reject the entire result if any projection lies outside the authorized subject set. Silent pre-authorization filtering is forbidden because it can hide cross-subject contamination and create incomplete evidence.

### 3.2 Goal projections lose `user_id`

`GoalRecordSnapshot` contains `user_id`, but `GoalProjection` and `GoalProjectionResult` do not preserve that field. A `goal_ref` is not proof of user or subject ownership.

Therefore:

```text
GoalProjectionResult alone = NOT independently subject-authorizable
```

A future goal adapter is blocked until one of these is accepted:

1. a new subject-bound goal projection schema; or
2. an immutable source-owner binding receipt that proves the projection IDs were derived from specific `GoalRecordSnapshot` IDs and an authorized subject/user scope.

The adapter must not infer `user_id` from `goal_ref`, title, keywords, source strings or caller input.

### 3.3 Open-loop projections have no subject identity

`OpenLoopSignal`, `OpenLoopProjection` and `OpenLoopProjectionResult` do not carry `SubjectRef`, tenant identity or user identity. `related_goal_ref` is an optional relation, not an authorization boundary.

Therefore:

```text
OpenLoopProjectionResult alone = NOT live-eligible
```

A future open-loop adapter is blocked until a subject-bound signal/projection contract or immutable source-owner binding receipt is accepted.

### 3.4 Observation v1 is unscoped

`ContinuitySignalObservation` v1 binds producer, source type, source ID, evidence, time and signal content. It does not bind tenant, subject, principal, purpose, retention or erasure state.

It remains valid for pure deterministic shadow aggregation, but cannot independently cross a live trust boundary.

### 3.5 Producer trust is not subject authorization

`ContinuitySignalPolicy` decides whether producer/source/confidence/evidence/scope meet aggregation policy. It is not a user, tenant, purpose, consent or erasure authorization policy.

A producer allowlist must never substitute for authenticated subject authorization.

## 4. Existing owner map

| Concern | Existing owner | Source-admission rule |
|---|---|---|
| Hard runtime policy | `PolicyKernel`, `PolicySnapshot`, `CapabilityLease` | Reuse; do not create a second policy root |
| HTTP deployment authentication | `server.require_api_key` | Shared API key is transport/deployment authentication only |
| Actor and subject vocabulary | Continuity `ActorRef`, `SubjectRef` | Reuse typed refs; do not infer identity from text |
| State reconciliation | `StateReconciler` | Read deterministic results; do not alter reconciliation |
| Goal storage | `GoalStack` | Remains storage owner |
| Goal admission | `GoalAttestation`, `GoalProjector` | Explicit attestation is necessary but not sufficient for subject authorization |
| Open-loop projection | `OpenLoopProjector` | Typed source signals only; currently subject-unbound |
| Observation shape | `ContinuitySignalObservation` | Existing v1 remains unchanged |
| Observation aggregation | `ContinuitySignalPolicy` and producer | Existing pure shadow aggregator remains unchanged |
| Canon and truth | TruthGate/TruthPolicy/WriteGate/PromotionGateway | No source-admission write or promotion |
| Erasure | durable erasure coordinator and subject-bound jobs | Future derived artifacts must be erasure-addressable |
| Runtime route | `ComputeController` | No route ownership or behavior change |
| Authentication/authorization provider | no accepted end-user owner yet | Architecture defines evidence contracts, not a new identity service |
| Activation | separate ADR + operator approval | This document authorizes none |

## 5. Non-authority boundary

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

## 6. Required contracts

### 6.1 `ContinuityPrincipalContext`

Represents the authenticated caller or internal service identity supplied by an accepted authentication owner.

```text
ContinuityPrincipalContext
├── principal_context_id
├── principal_ref
├── principal_kind
├── authentication_method
├── authentication_strength
├── authenticated_at
├── session_ref?
├── issuer_ref
├── authentication_receipt_ref
└── credential_fingerprint?   # never a raw secret
```

Rules:

- caller-supplied identity strings are not sufficient authentication;
- no raw API key, token or credential enters the contract;
- shared deployment API-key authentication cannot claim an end-user principal;
- internal services require an explicit service identity and issuer;
- authentication time is caller-supplied and timezone-aware;
- identity is content-addressed or backed by an immutable authentication receipt;
- authentication expiry/revocation is evaluated before admission.

### 6.2 `ContinuityAuthorizationContext`

Binds one admission operation to tenant, subjects and purpose.

```text
ContinuityAuthorizationContext
├── authorization_context_id
├── tenant_ref
├── subject_refs[]
├── principal_context_id
├── purpose_code
├── lawful_basis_or_consent_ref
├── authorization_receipt_ref
├── policy_snapshot_id
├── capability_lease_id?       # optional, narrowly named analysis only
├── retention_class
├── erasure_domain_refs[]
├── valid_from
├── valid_until
└── data_handling_mode
```

Required rules:

- tenant, at least one `SubjectRef`, purpose and authorization receipt are mandatory;
- authorization validity is bounded in time;
- an adapter cannot widen tenant or subject scope;
- PolicySnapshot is evidence of decision context, not reusable permission forever;
- a CapabilityLease grants only its exact named analysis capability;
- no lease implies Canon, network, storage, action or user-visible authority;
- missing, expired, malformed, withdrawn or unverifiable authorization fails closed;
- current restriction and erasure state dominate historical permission.

### 6.3 `ContinuitySourceBindingReceipt`

Proves which tenant and subjects an immutable source result belongs to.

```text
ContinuitySourceBindingReceipt
├── binding_receipt_id
├── source_type
├── source_result_id
├── source_digest
├── source_owner
├── tenant_ref
├── subject_refs[]
├── source_component_version
├── source_policy_version
├── source_as_of
├── evidence_refs[]
└── issued_at
```

Rules:

- the receipt is emitted or verified by the source owner, not invented by the adapter;
- source result ID and digest must match canonical source content;
- subject refs are complete, not a caller-selected subset;
- a binding receipt cannot grant processing permission;
- absence of a binding receipt blocks source types whose contract lacks subject identity;
- conflicting binding receipts fail closed.

### 6.4 `ContinuitySourceEnvelope`

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
├── source_binding_receipt_id
├── producer_adapter_id
├── producer_adapter_version
├── authorization_context_id
├── tenant_ref
├── subject_refs[]
├── evidence_refs[]
├── created_at
└── authority = "analysis_proposal_only"
```

Invariants:

```text
envelope tenant == binding tenant == authorization tenant
envelope subjects == binding subjects
envelope subjects ⊆ authorization subjects
```

The source object remains owned by its original component. The envelope does not copy or reinterpret arbitrary raw text.

### 6.5 `ContinuityObservationDraft`

Adapter output before admission.

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

A draft is not a `ContinuitySignalObservation` and cannot enter aggregation until admitted.

### 6.6 `ContinuityObservationAdmissionReceipt`

Immutable allow/deny evidence for one envelope and deterministic draft set.

```text
ContinuityObservationAdmissionReceipt
├── receipt_id
├── source_envelope_id
├── source_binding_receipt_id
├── authorization_context_id
├── policy_snapshot_id
├── adapter_id / version              # source adapter
├── admission_evaluator_id / version
├── admission_rule_id
├── evaluation_evidence_refs[]
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

The receipt cannot authorize persistence, execution, Canon writes or user-visible output.

The source adapter and admission evaluator are separate provenance axes. Evaluator ID/version, admission rule ID and nonempty evaluation evidence are mandatory and enter receipt identity. These fields are evidence references only: a future admission gate must resolve and allowlist the evaluator/rule and verify current policy, authorization, restriction and erasure state rather than trusting caller-supplied strings.

### 6.7 `AuthorizedContinuityObservationBatch`

The only future live-eligible input boundary.

```text
AuthorizedContinuityObservationBatch
├── batch_id
├── authorization_context_id
├── admission_receipt_ids[]
├── source_binding_receipt_ids[]
├── tenant_ref
├── subject_refs[]
├── observations[]             # existing v1 observations, batch-scoped
├── source_envelope_ids[]
├── policy_snapshot_id
├── created_at
├── valid_until
└── no_runtime_authority = true
```

Rules:

- all observations belong to one tenant and compatible subject scope;
- all observations trace to admitted drafts and receipts;
- batch identity binds observations, envelopes, bindings and authorization evidence;
- an unwrapped v1 observation is never live-eligible;
- global persistence or transport of v1 observations is forbidden without the batch and receipts;
- mixed-tenant batches are invalid;
- mixed-subject batches require explicit complete multi-subject authorization;
- a batch cannot be reused after expiry, withdrawal, restriction, erasure or incompatible policy change;
- receipt/batch mismatch rejects the whole batch.

## 7. Composition enforcement gate

A future live-capable composition path must not call the existing pure producer directly.

Required shape:

```text
produce_authorized_continuity_signals(
    authorized_batch,
    signal_policy,
    current_authorization_state,
    current_restriction_erasure_state,
)
```

The facade must:

1. validate batch identity;
2. validate all binding/admission receipts;
3. re-check current authorization expiry/withdrawal;
4. re-check current restriction and erasure state;
5. validate tenant and complete subject scope;
6. validate compatible PolicySnapshot/current policy;
7. only then pass batch observations to the existing pure aggregator;
8. bind the aggregate result to the batch and receipt IDs.

The existing `produce_continuity_compute_signals()` remains a pure shadow/test API. Passing bare v1 observations to it never creates live authorization.

Static and runtime guards must prevent any future `/query`, startup, worker, scheduler or advisory path from importing/calling the bare producer as its trust boundary.

## 8. v1 compatibility decision

`ContinuitySignalObservation` v1 remains unchanged.

Adding tenant, subject or consent fields directly to v1 would change content identity and break replay compatibility. The first implementation preserves v1 as a pure observation shape and binds authorization at the batch boundary.

```text
v1 observation alone
→ structurally valid
→ eligible for pure shadow aggregation
→ NOT live-authorized

v1 observation + valid batch + binding/admission receipts
→ eligible only for a future disabled admission-aware experiment
```

If observations later need independent persistence, transport or cross-process replay, define a new explicit schema version whose identity includes tenant/subject/authorization-context digest. Do not mutate v1 semantics in place.

## 9. Source eligibility and adapters

Adapters are deterministic proposal producers. They do not authenticate callers or authorize subjects.

### 9.1 Eligibility matrix

| Source | Current subject binding | Architecture disposition |
|---|---|---|
| `StateReconciliationResult` | each projection has `SubjectRef`; result may contain multiple subjects | conditionally eligible after complete-set validation |
| `GoalProjectionResult` | `GoalRecordSnapshot.user_id` is not preserved in projection result | blocked until subject-bound schema or source binding receipt |
| `OpenLoopProjectionResult` | no subject/user/tenant identity | blocked until subject-bound schema or source binding receipt |

### 9.2 State reconciliation adapter

Potential derivations:

| Source condition | Proposed signal | Constraint |
|---|---|---|
| contested/unresolved projection | `context_degraded=True` | authorized subject-scoped evidence required |
| contradiction refs present | `active_contradiction=True` | one deterministic scope per state key |
| stale/expired-only projection | context freshness | explicit deterministic status mapping |
| fresh current state required | `requires_current_state=True` | purpose must permit this analysis |
| complete current projection | evidence coverage item | only for explicitly defined required state keys |

Required source checks:

- enumerate the complete set of projection subjects before derivation;
- reject the whole result if any subject is unauthorized;
- reject duplicate/conflicting projection identity;
- reject future or stale source beyond explicit policy;
- reject source digest/result-ID mismatch.

Forbidden derivations:

- `important_claim` from arbitrary predicate text;
- user intent from model-inferred assertions;
- sensitivity from free-form content;
- truth or Canon admission;
- automatic answer or route selection.

### 9.3 Goal projection adapter — blocked pending subject binding

A future adapter requires either a subject-bound goal projection schema or source binding receipt that links:

```text
GoalRecordSnapshot IDs + user/subject scope
→ GoalProjection IDs
→ GoalProjectionResult ID
```

Additional rules:

- only explicit `GoalAttestation` projections are eligible;
- excluded goals produce no positive evidence coverage;
- goal ownership must be proven, not inferred from goal_ref;
- active goal does not imply reminder, scheduling or action permission;
- priority does not automatically become compute sensitivity;
- recurrence cannot create goal identity or attestation.

### 9.4 Open-loop adapter — blocked pending subject binding

A future adapter requires a subject-bound signal/projection schema or source binding receipt.

Additional rules:

- typed `OpenLoopSignal` remains necessary but is not sufficient;
- `related_goal_ref` is not subject authorization;
- `OPEN`/`OVERDUE` may propose `requires_current_state=True` only under proven subject scope and allowed purpose;
- `RESOLVED` cannot be silently reopened;
- deadline does not authorize scheduling or notification;
- no commitment, action, reminder or user-visible advice is emitted.

## 10. Authorization evaluation order

Required fail-closed sequence:

```text
validate principal authentication receipt
→ validate authorization-context identity
→ validate tenant and authorized subjects
→ validate purpose and lawful basis/consent reference
→ validate current restriction and erasure state
→ validate PolicySnapshot/current policy compatibility
→ validate source-result ID and digest
→ validate complete source subject-binding receipt
→ compare source subjects with authorization subjects
→ validate source freshness
→ validate adapter version and deterministic rule set
→ derive drafts
→ admit/reject each draft
→ emit immutable receipt
→ build authorized batch
```

No semantic adapter derivation runs before source type, identity and complete subject binding are validated.

## 11. Reason codes

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
SOURCE_SUBJECT_BINDING_MISSING
SOURCE_SUBJECT_BINDING_CONFLICT
SOURCE_CONTAINS_UNAUTHORIZED_SUBJECT
CROSS_SUBJECT_REFERENCE
GOAL_PROJECTION_SUBJECT_UNBOUND
OPEN_LOOP_SUBJECT_UNBOUND
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
SOURCE_DIGEST_MISMATCH
SOURCE_TOO_OLD
SOURCE_FROM_FUTURE
ADAPTER_NOT_ALLOWED
ADAPTER_VERSION_UNSUPPORTED
DERIVATION_NOT_ALLOWED
EVIDENCE_SCOPE_MISMATCH
MIXED_TENANT_BATCH
MIXED_SUBJECT_BATCH
BATCH_RECEIPT_MISMATCH
BATCH_EXPIRED
```

Reason codes are stable identifiers. Human-readable messages are projections and do not enter semantic identity.

## 12. Privacy, retention and erasure

Admission artifacts are derived personal-data surfaces when they reference a person or user-owned goal.

Required design:

- every envelope, draft, receipt and batch carries erasure-domain references;
- retention is explicit and bounded;
- no indefinite cache by default;
- source references are opaque identifiers, not copied content;
- sensitivity category/level constrains admission and logging;
- logs contain no raw user text, credentials or sensitive values;
- erased/restricted source refs invalidate dependent batches;
- replay checks current restriction/erasure state, not only historical authorization;
- persisted artifacts must be discoverable by subject/erasure domain before persistence is approved;
- completed erasure must invalidate caches and replay eligibility;
- existing append-only L0 residual limitations remain explicit and cannot be hidden by a receipt.

This architecture introduces no persistence or migration.

## 13. Security threat model

Minimum threats:

- shared API key misrepresented as user identity;
- caller chooses another tenant or subject;
- model-generated `SubjectRef` treated as authenticated scope;
- state result contains an additional unauthorized subject;
- caller silently filters unauthorized source projections;
- goal_ref is treated as user identity;
- related_goal_ref is treated as open-loop subject proof;
- cross-tenant observation aggregation;
- stale authorization replay;
- consent withdrawal ignored by cached batches;
- erased source resurrected by replay;
- arbitrary text becomes `important_claim` or sensitivity;
- trusted producer name substitutes for authorization;
- source ID points to different content;
- source binding receipt is incomplete or conflicting;
- policy snapshot reused after policy change;
- batch detached from receipts;
- bare v1 observations passed directly into a future live path;
- high-cardinality evidence causes resource exhaustion;
- raw secrets or personal text enter logs;
- admission receipt is mistaken for persistence or execution permission.

## 14. Determinism and replay

All semantic timestamps are caller-supplied and timezone-aware.

Identity uses canonical JSON and sorted collections where ordering is non-semantic.

Identical source content, binding receipt, authorization context, policy snapshot and adapter version must produce identical:

- binding receipt verification result;
- envelope ID;
- draft IDs;
- admission receipt ID;
- batch ID;
- observation IDs.

Wall-clock reads, random UUIDs, process IDs, database row IDs and request ordering do not enter semantic identity.

Replay fails closed when current authorization, restriction, erasure or policy state invalidates historical admission.

## 15. Resource budgets

Future implementation must define hard limits for:

- source results per call;
- projections per result;
- subjects per authorization context;
- subjects per source result;
- evidence refs per draft;
- drafts per envelope;
- observations and receipts per batch;
- serialized bytes;
- adapter execution time;
- batch age;
- nested/cross references.

Budget overflow rejects under an explicit deterministic policy. Silent partial admission is forbidden.

## 16. Staged implementation

### Slice A — neutral contracts only

A future PR may add:

- principal context;
- authorization context;
- source binding receipt;
- source envelope;
- observation draft;
- admission receipt;
- authorized batch;
- deterministic validators/serialization;
- unit and property tests.

It must not add adapters, persistence, server integration, feature flags or producer calls.

### Slice B — State adapter only

- explicit invocation in tests/local developer command;
- complete subject-set validation;
- deterministic rules;
- no runtime wiring.

### Slice C — source subject-binding corrections

Before Goal/OpenLoop adapters:

- add accepted subject-bound projection contracts or source-owner binding receipts;
- preserve compatibility through new explicit schema versions when needed;
- prove no identity inference from goal_ref or related_goal_ref.

### Slice D — Goal/OpenLoop adapters

- only after Slice C acceptance;
- explicit invocation;
- adversarial authorization tests;
- still disabled/unwired.

### Slice E — admission-aware process-local shadow facade

Requires:

- separate feature flag;
- static import guard against bare producer use in runtime paths;
- current authorization/restriction/erasure re-check;
- metrics and rollback/disable procedure;
- activation ADR and operator approval;
- zero user-visible effect.

## 17. Mandatory tests before implementation merge

### Contract tests

- content IDs stable across ordering/process runs;
- strings/bytes rejected where collections required;
- naive datetimes rejected;
- duplicate refs rejected;
- empty tenant/subject/purpose/receipt fields rejected;
- invalid authorization intervals rejected;
- semantic identity excludes transport metadata.

### Source-binding tests

- State result complete subject set is deterministic;
- one unauthorized state subject rejects the whole result;
- silent subset filtering is impossible;
- goal result without binding receipt is rejected;
- open-loop result without binding receipt is rejected;
- goal_ref cannot prove subject ownership;
- related_goal_ref cannot prove subject ownership;
- source digest/result-ID mismatch is rejected;
- conflicting binding receipts are rejected.

### Authorization tests

- shared API key cannot construct end-user principal automatically;
- tenant mismatch rejects the envelope;
- subject mismatch rejects the envelope;
- mixed-tenant batch impossible;
- cross-subject evidence rejected;
- expired/withdrawn authorization denied;
- current restriction/erasure overrides old permission;
- PolicySnapshot mismatch denied;
- denied receipt produces no batch;
- batch/receipt mismatch rejected.

### Adapter tests

- state conflict maps deterministically to scoped contradiction draft;
- duplicate contradictions retain provenance but count unique scopes;
- model-inferred assertion cannot become user-attested goal;
- excluded goal produces no positive evidence-coverage draft;
- open loop never creates reminder/scheduler/action authority;
- arbitrary text cannot create `important_claim`;
- unsupported source schema fails closed.

### Composition isolation tests

- admission-aware facade accepts only `AuthorizedContinuityObservationBatch`;
- bare v1 observation cannot enter future live composition;
- runtime modules cannot import/call bare producer as trust boundary;
- no Canon/TruthGate/PromotionGateway call;
- no GoalStack mutation;
- no ComputeController route change;
- no network, clock, environment or global mutable-state read in pure contracts;
- no `/query`, startup, worker or scheduler registration;
- no raw text or credential in logs/receipts.

## 18. Metrics for a future disabled experiment

Only after contracts/adapters are accepted:

- source envelopes evaluated;
- source-binding failures by reason code;
- authorization denials by reason code;
- drafts proposed/admitted/rejected;
- subject/tenant mismatch count;
- stale-source rejection count;
- erasure/restriction invalidation count;
- observations per batch;
- aggregation result distribution;
- latency/budget rejection;
- replay-determinism failures;
- bare-producer bypass attempts;
- zero user-visible effect assertion.

Metrics are bounded and contain no raw personal content.

## 19. Stop conditions

Stop and keep Draft if any change introduces:

- principal identity derived from request text;
- tenant/subject chosen without authorization receipt;
- shared API key treated as end-user identity;
- source subset filtering before complete subject validation;
- goal_ref or related_goal_ref treated as subject proof;
- observation trust based only on producer name;
- unscoped persistence of v1 observations;
- bare producer used as a future runtime trust boundary;
- automatic raw conversation extraction;
- Canon, TruthGate, memory or goal writes;
- compute-route, answer, reminder, scheduler, tool or action authority;
- restriction/erasure bypass;
- new policy root parallel to PolicyKernel;
- hidden network access;
- runtime wiring mixed with contract approval;
- live-readiness claims without measured disabled-shadow evidence.

## 20. Progress by state

```text
Source-boundary audit:             1/1 = 100%
Architecture contract Draft:       1/1 = 100%
Neutral contract implementation:   0/7 =   0%
State adapter:                     0/1 =   0%
Goal subject-binding correction:   0/1 =   0%
OpenLoop subject-binding correction: 0/1 = 0%
Goal/OpenLoop adapters:            0/2 =   0%
Authorization integration:         0/1 =   0%
Privacy/erasure integration:        0/1 =   0%
Admission-aware facade:            0/1 =   0%
Runtime wiring:                    0/1 =   0%
Runtime enabled:                   0/1 =   0%
Live observed evidence:            0/1 =   0%
```

## 21. Acceptance criteria

Architecture is acceptable only if review confirms:

1. existing policy, truth, goal, erasure and compute owners remain authoritative;
2. shared API-key authentication is not confused with principal/subject authorization;
3. tenant, subjects, purpose and current restriction/erasure state are mandatory;
4. State results require complete subject-set validation;
5. current Goal/OpenLoop results are blocked until subject binding is proven;
6. observation v1 compatibility is preserved;
7. live eligibility exists only through authorized batch + receipts;
8. future composition cannot bypass the admission-aware facade;
9. adapters remain deterministic proposal producers with no authority;
10. raw conversation extraction, persistence and runtime wiring are deferred;
11. every implementation slice remains default-off;
12. architecture, implementation, testing, wiring, enablement and observation remain separate states.
