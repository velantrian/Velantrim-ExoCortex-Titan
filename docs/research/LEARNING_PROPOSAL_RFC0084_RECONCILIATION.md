# 🧪 Learning Proposal and RFC-0084 Reconciliation

**Status:** `PROPOSED · DOCS-ONLY · NO RUNTIME AUTHORITY`  
**Historical source:** PR #43 / RFC-0083 head `18ebafa83fa358efeed0899c37712d5d536a79ff`  
**Reconciled against:** `main@3bc3607c503c2a32b7ab4f31753b7f9c10ee620f`  
**Authoritative adaptation lifecycle:** RFC-0084  
**Disposition for PR #43:** `REVISE_AND_REPLACE`

## 1. Decision

Titan may define a typed envelope describing a proposed learned or adaptive change. It must not define a second evaluation, approval or apply lifecycle beside RFC-0084.

```text
LearningObservation
  → LearningProposal
  → structural validation
  → ShadowEvaluationReceipt
  → RFC-0084 Candidate Update
  → rehearsal corpus
  → new-capability evaluation
  → regression budget
  → stability window
  → explicit approval
  → future versioned apply service
  → update receipt
  → rollback
```

The useful idea from historical RFC-0083 is retained as **what is proposed**. RFC-0084 remains the only owner of **how a proposal is evaluated, stabilized, approved, applied and rolled back**.

## 2. Non-authority boundary

This document creates no:

- runtime code;
- automatic dialogue analyzer;
- storage or shadow journal;
- API endpoint;
- worker, scheduler or startup hook;
- retrieval-policy mutation;
- intent routing;
- lexical-index activation;
- Canon, TruthGate or ordinary relation write;
- user-visible answer change;
- tool or action authority;
- evaluator, approval or apply service.

`PROPOSAL ≠ EVIDENCE ≠ SHADOW PASS ≠ APPROVAL ≠ APPLY ≠ CANON`.

## 3. Why the historical implementation is not accepted

The old `LearningPatch` implementation contains useful proposal families and validation ideas, but its ownership model is stale.

### 3.1 Parallel lifecycle

Historical statuses:

```text
PROPOSED
SHADOW_VALID
SHADOW_REJECTED
```

and `with_shadow_result(accepted=...)` create a LearningPatch-specific state transition. This overlaps RFC-0084 and allows status confusion.

Replacement rule:

```text
LearningProposal is immutable and always proposal_only.
Shadow evaluation produces a separate immutable receipt.
The proposal itself never becomes SHADOW_VALID, APPROVED or APPLIED.
```

### 3.2 Non-deterministic identity

Historical defaults use `uuid4()` and the current clock. Equal semantic input therefore produces different proposal identity.

Replacement rule:

- proposal ID is derived from canonical serialized content;
- timestamps are supplied by the trusted caller;
- timestamps do not define semantic identity unless the profile explicitly requires a bounded observation window;
- no network, clock, random or process-global dependency is read during construction or validation.

### 3.3 Incomplete authority and provenance binding

Conversation ID, actor and optional model are insufficient for cross-user, multi-tenant or policy-controlled learning.

A proposal must bind to:

- schema version;
- producer identity and producer type;
- source type and source references;
- tenant and subject where applicable;
- purpose;
- consent/attestation reference when required;
- retention and erasure class;
- policy snapshot ID and version;
- target scope and target owner;
- base version;
- evaluation profile ID;
- explicit `proposal_only` authority.

### 3.4 Caller-controlled acceptance

A caller-provided boolean cannot represent evaluation success. Evaluation must bind to corpus, baseline, metrics, policy and exact candidate digest.

### 3.5 Regex syntax is not regex safety

`re.compile()` only proves syntax. It does not prove bounded execution, semantic precision or resistance to catastrophic backtracking.

Intent-pattern proposals require a profile that chooses one of:

- a restricted non-backtracking grammar;
- a safe regex engine with enforced resource limits;
- a deterministic token/pattern matcher;
- explicit rejection when bounded execution cannot be proven.

No pattern is executed by the proposal contract.

## 4. Proposal envelope

Illustrative neutral contract:

```text
LearningProposal
├── schema_version
├── proposal_id                  # content-addressed
├── producer_id
├── producer_type
├── source_type
├── source_refs[]
├── tenant_ref?
├── subject_ref?
├── purpose
├── consent_or_attestation_ref?
├── retention_class
├── policy_snapshot_id
├── policy_version
├── target_owner
├── target_scope
├── base_version
├── evaluation_profile_id
├── observed_at                  # caller supplied
├── items[]                      # typed tagged union
├── reason_codes[]
└── authority = proposal_only
```

Forbidden fields include:

```text
apply
execute
allowed
approved
canon_write
truth_state
runtime_override
active_policy
final_decision
answer
user_visible_output
```

## 5. Typed proposal items

A single envelope may carry more than one item, but each item has an explicit kind, target owner and evaluation profile.

### 5.1 Claim candidate

```text
ClaimCandidateProposal
├── text or structured claim
├── claim_type
├── origin_type
├── evidence_refs[]
├── extraction_confidence
├── source_scope
└── target_owner = canonical admission candidate service
```

Rules:

- it is not a Fact;
- extraction confidence is not truth confidence;
- repetition, utility and model confidence are not evidence;
- any future admission uses existing TruthGate/write boundaries;
- claim candidates may be split into a separate envelope when their data lifecycle differs from policy proposals.

### 5.2 Lexical association

```text
LexicalAssociationProposal
├── surface
├── concept_ref
├── language
├── domain
├── proposed_weight
├── observation_refs[]
└── target_owner = derived lexical index
```

Rules:

- not a canonical relation;
- not evidence of world truth;
- scope is tenant/user/domain explicit;
- activation requires precision/recall, collision and sensitive-routing evaluation;
- derived index is versioned and rebuildable.

### 5.3 Intent pattern

```text
IntentPatternProposal
├── intent_ref
├── matcher_kind
├── matcher_payload
├── language
├── positive_examples[]
├── negative_examples[]
├── scope
├── expiry?
└── target_owner = deterministic intent router profile
```

Rules:

- proposal validation does not execute the matcher;
- evaluation must include false-positive, ambiguity and safety-sensitive cases;
- one lexical trigger cannot activate medical, emotional, financial or other high-risk behavior;
- every active matcher has disable/rollback identity.

### 5.4 Retrieval policy

```text
RetrievalPolicyProposal
├── target_profile
├── base_policy_version
├── proposed_changes
├── reason_codes[]
├── expected_effect
└── target_owner = retrieval policy service
```

Rules:

- changes are relative to an exact baseline;
- partial changes cannot inherit unknown fields from an unbound runtime state;
- evaluation follows RFC-0084 with retrieval-specific corpus and regression budget;
- Safe Recall, restricted-data, provenance and latency invariants are hard failures.

### 5.5 Non-epistemic attention or charge signal

```text
AttentionSignalProposal
├── target_ref
├── signal_type
├── magnitude
├── scope
├── observation_refs[]
└── target_owner = non-epistemic projection
```

Rules:

```text
attention / charge / utility
≠ confidence
≠ evidence
≠ epistemic state
≠ identity
```

Repeated or useful content may become easier to retrieve without becoming more true.

## 6. Canonical construction and validation

Construction must:

1. reject unknown item kinds;
2. reject scalar strings/bytes where collections are required;
3. consume one-shot iterables exactly once;
4. copy caller-owned mutable structures;
5. normalize Unicode and identifiers under a versioned policy;
6. reject duplicate IDs and conflicting duplicate content;
7. sort semantically unordered collections;
8. preserve explicitly ordered examples only when order is part of the profile;
9. reject NaN, infinity, booleans-as-numbers and out-of-range values;
10. reject forbidden authority-bearing fields recursively;
11. serialize to canonical JSON;
12. derive a deterministic digest and proposal ID.

Validation reports structural suitability only. It does not claim benefit, safety, truth or approval.

## 7. Separate shadow evaluation receipt

```text
ShadowEvaluationReceipt
├── receipt_id
├── proposal_digest
├── evaluator_id
├── evaluator_version
├── repository_sha
├── policy_snapshot_id
├── evaluation_profile_id
├── baseline_version
├── corpus_digest
├── holdout_digest?
├── metrics
├── hard_invariant_results
├── errors / timeouts
├── result = PASS | FAIL | NOT_READY
├── started_at
└── completed_at
```

A PASS receipt means only that one declared evaluation run passed. It is not a stability result or approval.

The receipt must distinguish:

- absent evidence;
- malformed proposal;
- policy denial;
- evaluator/infrastructure failure;
- metric failure;
- hard-invariant failure;
- successful bounded run.

## 8. RFC-0084 ownership

RFC-0084 owns:

- candidate lifecycle;
- rehearsal and holdout corpora;
- new-capability metrics;
- regression budgets;
- hard zero-tolerance invariants;
- stability windows;
- approval receipts;
- versioned apply requirements;
- rollback targets and update receipts.

No RFC-0083-derived component may define its own:

- `APPROVED` or `APPLIED` state;
- stability threshold;
- approval authority;
- persistence or shadow journal as permission;
- apply method;
- Canon bridge;
- rollback controller.

## 9. Evaluation profiles

Different item kinds require separate profiles. Aggregate success cannot hide a failure in one kind.

### 9.1 Claim candidate profile

Measures provenance completeness and admission-candidate hygiene. It does not judge truth admission by itself.

### 9.2 Lexical association profile

Measures:

- precision and recall;
- collision/ambiguity rate;
- language/domain segmentation;
- sensitive-routing false positives;
- bounded index growth;
- tenant leakage;
- deterministic lookup behavior.

### 9.3 Intent pattern profile

Measures:

- positive/negative example accuracy;
- catastrophic matcher complexity rejection;
- ambiguity and priority conflicts;
- high-risk false activation;
- timeout/resource ceilings;
- deterministic conflict resolution.

### 9.4 Retrieval policy profile

Measures:

- relevant-fact recall;
- precision;
- contradiction and evidence coverage;
- restricted/erased-data leakage rate;
- provenance retention;
- latency, context size and resource cost;
- unsafe fallback behavior.

### 9.5 Attention signal profile

Measures utility and retrieval behavior only. Epistemic state must remain unchanged in every test.

## 10. Data governance

Every proposal and evaluation artifact must support:

- tenant scope;
- subject scope where applicable;
- purpose limitation;
- restricted/credential/contact data redaction;
- retention expiry;
- erasure closure across source references, fixtures, derived indexes and receipts;
- prevention of cross-tenant learning;
- explicit policy for aggregate statistics after erasure.

Erased or prohibited content cannot remain in rehearsal fixtures merely because it was once useful for evaluation.

## 11. Derived projections

A future derived lexical index, intent router profile or attention projection must be:

- versioned;
- bound to exact approved proposal/update receipts;
- rebuildable;
- independently disableable;
- scope- and tenant-aware;
- excluded from Canon and TruthGate evidence;
- rollback-capable;
- observable through bounded metrics;
- never activated by the proposal contract itself.

## 12. Relationship to Continuity and Project Cognition

Continuity observations, open loops and advisory candidates do not automatically become learning observations.

Project/repository behavior may produce code-review learning proposals, but project context remains separate from user/world memory and requires its own target profile.

```text
recurrence
≠ user preference
≠ learned rule
≠ identity
≠ approval
```

## 13. Threat model

Minimum threats:

- prompt-to-memory or prompt-to-policy injection;
- poisoned examples;
- cross-tenant learning;
- popularity-to-truth leakage;
- catastrophic regex/matcher behavior;
- policy drift through repeated small updates;
- metric gaming;
- evaluation overfitting;
- status confusion (`PASS` interpreted as approval);
- receipt forgery or missing identity binding;
- unbounded proposal/index growth;
- sensitive fixture retention;
- stale-base apply;
- rollback target loss;
- evaluator failure reported as success.

Every profile defines hard failures that cannot be averaged away.

## 14. Implementation sequence

### Stage A — architecture only

- merge this reconciliation document;
- close historical PR #43 as superseded;
- keep RFC-0084 `Proposed` and unwired;
- record GitHub ↔ Notion synchronization.

### Stage B — proposal contracts

Separate Draft PR:

- stdlib-only immutable contracts;
- content-addressed IDs;
- typed tagged union;
- deterministic validation;
- forbidden-authority scan;
- serialization/replay tests;
- no persistence or runtime wiring.

### Stage C — evaluator receipts

Separate Draft PR:

- immutable receipt schema;
- profile identity;
- corpus/baseline binding;
- deterministic result taxonomy;
- no approval or apply.

### Stage D — RFC-0084 evaluator implementation

Only after architecture approval:

- isolated snapshots;
- objective evaluators;
- regression budgets;
- hard invariant suite;
- stability window;
- tenant/erasure closure.

### Stage E — apply boundary

Requires a separate RFC, policy owner, canonical transaction design, rollback proof and explicit Operator GO.

## 15. Stop conditions

Stop and keep Draft if any change introduces:

- proposal status promotion to approved/applied;
- random or clock-derived semantic identity;
- direct Canon, TruthGate, relation or retrieval-policy write;
- regex/matcher execution without bounded profile;
- missing tenant/subject/purpose/retention design;
- cross-tenant fixtures or derived indexes;
- parallel governance lifecycle;
- worker, scheduler, startup or `/query` wiring;
- user-visible effect;
- activation bundled with contract creation.

## 16. Progress by state

```text
Architecture reconciliation:  1/1 = 100%
Proposal implementation:       0/5 =   0%
Evaluator implementation:      0/5 =   0%
Tests/evaluation corpus:       0/5 =   0%
Runtime wiring:                0/1 =   0%
Runtime readiness:             0/1 =   0%
```

## 17. Final disposition

```text
PR #43 = REVISE_AND_REPLACE
RFC-0083 = proposal-envelope profile under RFC-0084
RFC-0084 = sole adaptive-update governance lifecycle
```

The historical implementation remains a research source and must not be merged directly.