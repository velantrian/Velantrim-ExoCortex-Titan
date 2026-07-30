# 🛡️ Failure, Memory Lifecycle & Reliability — Research Contract

**Status:** `RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Contract ID:** `titan.failure-lifecycle-reliability`  
**Contract version:** `flr-research-v1`  
**Date:** 2026-07-30  
**Scope:** provider-neutral failure disposition, representation lifecycle and read-only reliability projections

## Decision

Titan must not collapse three different concerns into one generic fallback or one
self-model object:

```text
Execution failure
→ FailureDisposition

Representation aging
→ MemoryLifecycleDecision

What the runtime can do and how dependable this result is
→ RuntimeCapabilitySnapshot + AnswerReliabilityMetadata
```

These contracts describe deterministic proposal and receipt semantics. They do
not create a new controller, memory authority, truth authority or self-aware
module. Existing owners remain authoritative:

- `PolicyKernel`, fresh `PolicySnapshot` and current `CapabilityLease` govern
  permission;
- Recall Policy governs admissible retrieval;
- TruthGate / promotion policy govern epistemic admission;
- Canon and its revision path govern durable canonical knowledge;
- ErasureCoordinator governs user/legal erasure;
- AuditChain remains append-only;
- D16 remains a proposal-only research contract with `LEGACY_QUERY` as the
  authoritative fallback.

## 1. Failure Disposition Contract

### 1.1 Purpose

A failure disposition answers:

```text
Given this failed operation, its intended effect and current policy state,
what is the narrowest safe next disposition?
```

It must never answer by broad exception type alone. The same technical failure
can require different behaviour depending on whether the attempted effect was a
read, rebuildable projection, remote call, canonical write or irreversible
external action.

### 1.2 Effect classes

```text
PURE_READ
REBUILDABLE_PROJECTION
LOCAL_REVERSIBLE_WRITE
CANONICAL_WRITE
REMOTE_READ
REMOTE_SIDE_EFFECT
IRREVERSIBLE_EFFECT
AUDIT_APPEND
ERASURE_OPERATION
```

Unknown or malformed effect classes are treated as the most restrictive
applicable class. A caller may not label an effect as `PURE_READ` merely because
its local code path is read-only when the operation can trigger remote access,
resource acquisition or another external effect.

### 1.3 Dispositions

```text
DENY
FALLBACK
BOUNDED_RESULT
REQUEST_EVIDENCE
CLARIFY
DEFER
RETRY_LATER
QUARANTINE
ESCALATE_OPERATOR
```

There is no generic `CONTINUE_ANYWAY`, silent `IGNORE`, or permission-expanding
fallback.

### 1.4 Required decision order

1. validate a fresh, healthy `PolicySnapshot`;
2. validate current leases for every optional capability;
3. classify the intended effect;
4. evaluate whether the failed component is authoritative or rebuildable;
5. preserve evidence, audit and erasure invariants;
6. select the narrowest disposition;
7. emit a structured receipt;
8. preserve the legacy authoritative result when a shadow/projection path fails.

### 1.5 Deterministic matrix

| Situation | Required disposition | Permitted continuation |
|---|---|---|
| Missing, stale, mismatched or unhealthy policy snapshot | `DENY` | none; optional action is not attempted |
| Missing, stale, revoked or scope-mismatched lease | `DENY` | none for that capability |
| Canonical write cannot prove version/precondition | `DENY` or `ESCALATE_OPERATOR` | no fallback write |
| Irreversible effect has unknown execution state | `QUARANTINE` + `ESCALATE_OPERATOR` | recovery inspection only |
| Vector/embedding index unavailable | `FALLBACK` | authorised FTS/BM25, graph or canonical-local retrieval |
| Optional model/provider unavailable | `FALLBACK` or `RETRY_LATER` | zero-model local/template path within the same authority |
| Passive shadow/projection fails | `BOUNDED_RESULT` | return unchanged authoritative legacy result and record limitation |
| Research budget exhausted | `BOUNDED_RESULT` or `DEFER` | partial result with explicit missing work |
| Critical evidence is absent | `REQUEST_EVIDENCE` | no fabricated completion |
| User intent is materially ambiguous | `CLARIFY` | no irreversible or policy-sensitive action |
| Recall candidate is malformed/restricted/erased | `QUARANTINE` or `DENY` | keep it out of active context |
| Audit append fails for an auditable write/effect | `DENY` or recovery-specific `QUARANTINE` | no claim of successful completion |
| Erasure completeness cannot be proven | `ESCALATE_OPERATOR` | do not report erasure complete |

### 1.6 Non-expansion invariant

> Fallback may change the execution mechanism, latency, cost or completeness. It
> must never increase permission, data visibility, truth status, write authority
> or external effect scope.

Examples:

```text
remote provider denied
→ local deterministic path ✅
→ a different unleased provider ❌

vector index unavailable
→ FTS over already-authorised local data ✅
→ broaden retrieval to restricted memory ❌

Canon CAS conflict
→ re-read and propose a new revision ✅
→ overwrite without version check ❌
```

### 1.7 Failure receipt

```text
FailureDispositionReceipt
├── schema_version
├── operation_id
├── effect_class
├── failure_code
├── disposition
├── authoritative_path_preserved
├── fallback_path
├── retryable
├── retry_after_hint
├── policy_snapshot_id
├── policy_version
├── capability_lease_refs[]
├── evidence_gap_ids[]
├── limitations[]
├── audit_event_ref
└── generated_at
```

`retryable` describes whether a later attempt can be meaningful. It does not
permit an immediate retry loop beyond a separately bounded retry policy.

## 2. Memory Lifecycle Policy

### 2.1 Purpose

Memory lifecycle decisions must distinguish accessibility, validity, physical
retention, canonical history, audit integrity and user/legal erasure.

```text
Attention decay ≠ expiry ≠ deletion ≠ erasure ≠ Canon revision
```

### 2.2 Representation classes

```text
CANON_RECORD
CANON_REVISION_HISTORY
AUDIT_EVENT
ERASURE_RECEIPT
SOURCE_ARTIFACT
EPISODIC_RECORD
HYPOTHESIS
REBUILDABLE_INDEX
CACHE
SUMMARY_PROJECTION
SHADOW_RECEIPT
TRACE
TEMPORARY_WORKING_ITEM
```

Each persistent representation must declare:

```text
representation_class
owner
source_of_truth
rebuildable
retention_basis
expiry_basis
supersession_policy
erasure_adapter
audit_requirements
```

A store without an owner and erasure contract cannot be added as a durable
memory surface.

### 2.3 Independent lifecycle mechanisms

#### FSRS / attention decay

Changes retrieval priority or rehearsal urgency. It does not delete source data,
change epistemic status or satisfy erasure.

#### TTL

Permitted only for temporary or reproducible representations whose source of
truth survives. TTL expiry removes the representation, not the underlying claim
or history.

Typical TTL-eligible classes:

- cache;
- rebuildable index entries;
- temporary working items;
- bounded traces;
- shadow projections and temporary receipts, subject to audit requirements.

#### Epistemic expiry

Marks a claim, hypothesis or source-dependent conclusion as stale, review-needed
or no longer safe to rely on. It preserves lineage and does not silently delete
the historical object.

#### Canon revision

Uses explicit revision operations such as `supersede`, `deprecate`, `retract` or
`review_required`. Canon records are not removed by ordinary TTL.

#### Erasure

A separate user/legal operation coordinated across authoritative and derived
stores. It requires completeness tracking and an erasure receipt. Rebuildability
never exempts a derived store from erasure coverage while the data remains
present.

#### Audit retention

AuditChain integrity cannot be broken by generic TTL. Privacy-preserving
redaction or cryptographic erasure, when required, needs an explicit audited
protocol rather than ordinary deletion.

### 2.4 Lifecycle decision

```text
MemoryLifecycleDecision
├── schema_version
├── representation_id
├── representation_class
├── action
├── reason_codes[]
├── source_of_truth_ref
├── rebuildable
├── epistemic_status_before
├── epistemic_status_after
├── retention_deadline
├── review_trigger
├── supersedes_ref
├── erasure_operation_id
├── policy_snapshot_id
└── audit_event_ref
```

Allowed actions:

```text
KEEP
DECAY_ACCESS
REVIEW_REQUIRED
SUPERSEDE
DEPRECATE
RETRACT
EXPIRE_PROJECTION
REBUILD
ERASE
QUARANTINE
```

`DELETE_CANON_BY_TTL` and `DELETE_AUDIT_BY_TTL` are invalid actions.

### 2.5 Lifecycle matrix

| Representation | Decay | TTL | Epistemic expiry | Supersession | Erasure | Ordinary deletion |
|---|---:|---:|---:|---:|---:|---:|
| Canon record | access only | no | review/retract | yes | coordinated | no |
| Canon revision history | no | no | no | append new revision | coordinated | no |
| Audit event | no | no | no | no | special protocol | no |
| Hypothesis | attention | optional only if explicitly ephemeral | yes | resolution lineage | coordinated | only under owner policy |
| Source artifact | access | source policy | freshness metadata | new source revision | coordinated | source-owner policy |
| Rebuildable index | optional | yes | inherited | rebuild | coordinated | yes |
| Cache | optional | yes | inherited | replace | coordinated | yes |
| Summary projection | optional | yes | inherited + review | rebuild | coordinated | yes |
| Shadow receipt/trace | optional | bounded | n/a | replace | coordinated | yes, if audit contract permits |

### 2.6 Lifecycle invariants

- expiring a projection never changes its source-of-truth object;
- a stale hypothesis cannot become a fact merely because newer evidence is
  absent;
- erasure completion is not reported until every registered adapter reaches a
  terminal state;
- a summary may be rebuilt only from currently admissible source material;
- supersession preserves lineage;
- retention policy cannot bypass legal hold or policy restrictions;
- no learned score may silently delete durable knowledge.

## 3. Runtime Capability Snapshot

### 3.1 Purpose

`RuntimeCapabilitySnapshot` is a read-only projection of what this runtime can
currently attempt under a specific healthy policy state. It is not a self-model,
identity claim or grant of permission by itself.

```text
RuntimeCapabilitySnapshot
├── schema_version
├── snapshot_id
├── policy_snapshot_id
├── policy_version
├── supervisor_mode
├── health
├── local_capabilities[]
├── optional_capabilities[]
├── unavailable_components[]
├── degraded_components[]
├── active_limits
├── budgets
├── lease_refs[]
├── zero_model_path_available
├── authoritative_memory_available
├── generated_at
└── expires_at
```

### 3.2 Rules

- built only from observable component state and policy outputs;
- deterministic for equivalent canonical inputs;
- expires and is re-created rather than mutated in place;
- never converts component availability into policy permission;
- records `unknown` instead of guessing capability;
- separates local availability, optional remote availability and authorised
  action scope;
- may be attached to an internal receipt before any user-visible exposure.

An unhealthy policy dependency makes the capability snapshot unhealthy even when
local components remain technically available.

## 4. Answer Reliability Metadata

### 4.1 Purpose

`AnswerReliabilityMetadata` describes the evidence and limitations of one result.
It is not a universal confidence score and must not masquerade as truth.

```text
AnswerReliabilityMetadata
├── schema_version
├── result_id
├── evidence_strength
├── evidence_refs[]
├── provenance_coverage
├── calibrated_confidence
├── uncertainty_sources[]
├── critical_gaps[]
├── contradictions[]
├── fallback_path
├── omitted_work[]
├── capability_snapshot_id
├── policy_snapshot_id
├── authoritative_path
├── reliability_class
└── generated_at
```

Candidate reliability classes:

```text
SUPPORTED
PARTIALLY_SUPPORTED
LIMITED_BY_CAPABILITY
LIMITED_BY_POLICY
LIMITED_BY_BUDGET
EVIDENCE_REQUIRED
CONFLICTED
UNKNOWN
```

### 4.2 Rules

- confidence is calibrated only against a named evaluation set and version;
- evidence strength and confidence are separate fields;
- `UNKNOWN` is valid and preferable to fabricated precision;
- unsupported model prose cannot increase reliability;
- fallback and omitted work are always visible;
- critical gaps prevent `SUPPORTED` classification;
- contradictions cannot be averaged away;
- user-visible metadata, if later enabled, must be a projection of the same
  internal receipt rather than independently generated prose.

### 4.3 Initial integration boundary

The first permitted integration is internal and shadow-only:

```text
existing authoritative result
+ healthy RuntimeCapabilitySnapshot
+ existing evidence/provenance receipts
→ AnswerReliabilityMetadata
→ attach to UnderstandingReceipt / evaluation record
→ no answer control
```

No user-visible badge, confidence percentage or automatic route change is
introduced by this contract.

## 5. Cross-contract composition

```text
fresh healthy PolicySnapshot
+ current CapabilityLease(s)
        │
        ├──► RuntimeCapabilitySnapshot
        │
operation/result
        ├──► FailureDispositionReceipt
        ├──► MemoryLifecycleDecision
        └──► AnswerReliabilityMetadata

all outputs
→ structured receipt / AuditChain according to existing owner contracts
→ no new truth, policy, task or Canon authority
```

D16 may reference these receipts in future experiments. D16 does not own their
underlying policy, lifecycle or truth decisions.

## 6. Validation and falsification

A future implementation candidate must prove:

- deterministic output for equivalent canonical inputs;
- fail-closed behaviour for malformed/unknown policy and effect classes;
- no permission expansion through fallback;
- no Canon or AuditChain TTL deletion path;
- complete erasure registration for every new persistent representation;
- accurate retryable semantics for transient versus permanent failures;
- preservation of the authoritative legacy response when shadow analysis fails;
- explicit uncertainty and critical-gap handling;
- zero-model operation;
- bounded latency, memory and receipt size;
- no direct Canon, ESM, policy or task-state mutation.

Reject or redesign the proposal when it requires:

- a second PolicyKernel, TruthGate, AuditChain or ErasureCoordinator;
- a generic self-aware `SelfModel` authority;
- one scalar confidence replacing evidence and uncertainty;
- TTL as a universal deletion policy;
- silent fallback to a broader data source or capability;
- hidden chain-of-thought retention;
- mandatory LLMs, embeddings, remote providers or graph traversal.

## 7. Implementation sequence

1. merge this docs-first contract;
2. add pure dataclasses/enums and validators with no runtime wiring;
3. add deterministic unit tests and malformed-input tests;
4. attach internal-only capability/reliability projections to a shadow receipt;
5. collect metrics and operator-labelled examples;
6. propose any user-visible metadata separately;
7. require explicit Operator GO for any active D16 or lifecycle write path.

## Core rule

```text
Failure handling may reduce capability, never expand authority.
Lifecycle may expire projections, never erase Canon or audit by accident.
Capability metadata describes current limits, never grants permission.
Reliability metadata exposes evidence and uncertainty, never manufactures truth.
```
