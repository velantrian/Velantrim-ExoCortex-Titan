# 🧪 Evaluation Replay Protocol — Titan Research Contract

**Status:** `RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Date:** 2026-07-30  
**Scope:** deterministic, replayable comparison of Titan configurations on fixed corpora and questions

## Decision

Titan needs a repeatable way to answer a practical question:

> Did this architectural change improve understanding, retrieval, memory and answers, or did it only make the implementation more complicated?

The first permitted implementation is an **offline evaluation harness**. It records a bounded dataset, configuration, policy snapshot, fixtures, outputs and metrics. It may replay the same test cases and fork a run with one declared change. It does not control production routing, write to Canon or replay irreversible external effects.

```text
fixed corpus + fixed questions + fixed policy/configuration
→ baseline run
→ immutable evaluation receipts
→ candidate fork with one declared change
→ structural diff + metrics
→ operator review
```

## Goals

The protocol must make it possible to measure:

- what Titan extracted from a source;
- what it retained or rejected as memory;
- what evidence it retrieved for a question;
- how it represented time, contradiction and supersession;
- whether the answer is supported by the selected evidence;
- whether equivalent inputs remain stable;
- whether latency or resource cost improved;
- whether any policy, write or truth boundary was bypassed.

## Non-goals

This contract does not create:

- a production event-sourced kernel;
- hidden chain-of-thought storage;
- automatic model grading as the source of truth;
- permission to record secrets or personal data in public fixtures;
- execution of email, payments, deployments or other external side effects during replay;
- a universal scalar score that hides critical failures;
- automatic promotion of the winning configuration.

## Evaluation package

Each dataset is a versioned package:

```text
EvaluationPackage
├── package_id
├── protocol_version
├── corpus_snapshot
├── cases[]
├── expected_claims[]
├── expected_evidence_spans[]
├── expected_temporal_relations[]
├── expected_conflicts[]
├── expected_memory_dispositions[]
├── answer_rubrics[]
├── risk_labels[]
├── policy_fixture
├── provider/tool fixtures[]
├── redaction_manifest
└── package_digest
```

The package digest is computed from canonical JSON with sorted keys and stable ordering. Mutable timestamps, machine paths and random IDs must not affect identity.

## Corpus design

The minimum corpus should include the following classes.

### 1. Direct factual extraction

A source contains explicit statements with exact expected spans.

Measures:

- claim precision and recall;
- exact span accuracy;
- modality classification;
- preservation of source text;
- extraction confidence separation from truth confidence.

### 2. Distractors and irrelevant text

A source mixes useful facts with decorative prose, repetition and unrelated details.

Measures:

- noise rejection;
- context budget efficiency;
- false memory candidate rate;
- retrieval precision.

### 3. Contradictory sources

Two sources disagree explicitly or appear to disagree because of scope.

Measures:

- contradiction recall;
- conflict type classification;
- whether disagreement is surfaced rather than averaged away;
- whether unsupported resolution is avoided.

### 4. Temporal change and supersession

A fact changes over time, or a later source corrects an earlier one.

Measures:

- valid-time accuracy;
- known-time accuracy;
- supersession lineage;
- historical query accuracy;
- resistance to treating “newer” as automatically “truer”.

### 5. User-reported and sensitive information

Synthetic user statements include preferences, temporary context and sensitive material.

Measures:

- user-report modality;
- sensitivity flags;
- durable-versus-ephemeral memory selection;
- policy denial and redaction;
- zero direct writes from the extractor.

Only synthetic or explicitly approved data is allowed in repository fixtures.

### 6. Procedural knowledge

A source describes a method with preconditions, ordered steps and failure conditions.

Measures:

- step order;
- precondition preservation;
- omission of unsupported steps;
- distinction between a described procedure and an authorised action.

### 7. Ambiguous questions

Questions are intentionally underspecified.

Measures:

- clarification recall;
- unsafe assumption rate;
- RCO/D16 proposal quality when enabled in shadow mode;
- evidence requests instead of fabricated completion.

### 8. High-risk questions

Synthetic medical, legal, financial or operational examples require stronger evidence.

Measures:

- unsafe-fast rate;
- evidence sufficiency detection;
- policy non-interference;
- reliability classification;
- no high-risk failure hidden by aggregate scores.

## Evaluation case contract

```text
EvaluationCase
├── case_id
├── task_class
├── risk_class
├── source_refs[]
├── question
├── conversation_context[]
├── expected_claim_refs[]
├── expected_evidence_span_refs[]
├── expected_memory_dispositions[]
├── expected_route_set[]
├── forbidden_outputs[]
├── answer_rubric
├── deterministic_seed
└── tags[]
```

`expected_route_set` may contain more than one acceptable route when several continuations are safe. The evaluator must not manufacture a single gold label for genuinely ambiguous cases.

## Run contract

```text
EvaluationRun
├── run_id
├── protocol_version
├── package_id
├── code_revision
├── configuration_snapshot
├── feature_flags
├── policy_snapshot_fixture
├── model/provider_fixture_versions
├── environment_manifest
├── ordered_case_receipts[]
├── aggregate_metrics
├── critical_failures[]
├── started_at
├── completed_at
└── result_digest
```

The result digest excludes wall-clock timestamps and machine-specific paths. It includes all semantic outputs, version identities and reason codes.

## Baseline and fork rules

A candidate comparison must declare one primary change:

```text
ExperimentFork
├── parent_run_id
├── fork_id
├── changed_dimension
├── before_value
├── after_value
├── secondary_changes[]
├── justification
└── expected_effect
```

Examples of valid primary changes:

- lexical versus hybrid retrieval;
- old versus new embedding projection contract;
- memory extractor disabled versus shadow-only;
- baseline temporal view versus candidate temporal view;
- existing receipts versus a normalized envelope;
- procedural-skill retrieval disabled versus read-only enabled.

If multiple architectural changes are bundled, the run must be labelled exploratory and cannot support causal claims about one component.

## Required receipts per case

Each case should retain structured artifacts where available:

```text
CaseEvaluationReceipt
├── case_id
├── input_digest
├── extracted_claims[]
├── rejected_claims[]
├── evidence_refs[]
├── retrieval_result[]
├── memory_candidates[]
├── memory_dispositions[]
├── temporal_view[]
├── conflicts[]
├── route_or_proposal
├── answer
├── reliability_metadata
├── policy_reason_codes[]
├── write_attempts
├── external_calls
├── latency_breakdown
├── resource_counts
├── warnings[]
└── output_digest
```

Hidden chain-of-thought is not required and must not be stored. Structured reasons, visible evidence references and decision codes are sufficient.

## Metrics

### Extraction

```text
claim_precision
claim_recall
exact_span_precision
exact_span_recall
modality_accuracy
unsupported_claim_rate
```

### Retrieval

```text
recall_at_k
precision_at_k
mean_reciprocal_rank
nDCG_at_k
evidence_coverage
irrelevant_context_rate
lexical_fallback_success_rate
```

### Memory

```text
memory_candidate_precision
memory_candidate_recall
sensitive_block_rate
duplicate_candidate_rate
supersession_hint_accuracy
ephemeral_retention_error_rate
unauthorised_write_count = 0
```

### Temporal and conflict reasoning

```text
valid_time_accuracy
known_time_accuracy
historical_query_accuracy
supersession_lineage_accuracy
contradiction_recall
false_contradiction_rate
unsupported_conflict_resolution_rate
```

### Answers

```text
answer_supported_claim_rate
answer_evidence_coverage
forbidden_output_rate
critical_gap_recall
clarification_precision
reliability_class_accuracy
```

### Routing and orientation

```text
reviewed_route_accuracy
unsafe_fast_rate
false_defer_rate
request_evidence_recall
clarify_recall
proposal_stability
```

### System properties

```text
p50_latency_ms
p95_latency_ms
model_call_count
tool_call_count
dense_call_count
retriever_rebuild_count
context_token_cost
peak_memory_hint
truth_gate_bypass_count = 0
query_path_write_count = 0
policy_non_interference_rate = 1.0
```

## Critical gates

A candidate cannot be called better when any of these regress beyond an approved threshold:

- `truth_gate_bypass_count > 0`;
- `query_path_write_count > 0`;
- high-risk `unsafe_fast_rate` exceeds its class-specific limit;
- restricted or erased information appears in active context;
- provenance coverage materially decreases;
- temporal history is silently rewritten;
- lexical fallback stops working without embeddings/providers;
- equivalent deterministic inputs produce unexplained semantic drift;
- a cache or projection survives revocation/erasure incorrectly.

A lower average latency does not compensate for a critical safety regression.

## Grading hierarchy

Use the strongest available evidence in this order:

1. exact deterministic assertions;
2. source-span and structured-field comparison;
3. executable policy and invariant checks;
4. operator-reviewed labels;
5. model-assisted grading for bounded semantic criteria;
6. unstructured human impression.

A model grader must be versioned, blinded to baseline/candidate labels where possible and prevented from overriding deterministic failures.

## Stability classes

Results should be separated into:

```text
BIT_IDENTICAL
STRUCTURALLY_EQUIVALENT
SEMANTICALLY_ACCEPTABLE
REVIEW_REQUIRED
REGRESSION
INVALID_RUN
```

`BIT_IDENTICAL` is not required for provider-generated prose, but source selection, policy decisions, deterministic routes and structured receipts should be stable under equivalent fixtures.

## Replay constraints

- External provider responses must use recorded fixtures or a separately labelled live-evaluation mode.
- Tool calls are simulated unless the tool is explicitly read-only, local and fixture-bound.
- Irreversible effects are never replayed.
- Randomness uses an explicit seed where supported.
- Time is supplied by a test clock.
- Environment variables and feature flags are captured explicitly.
- Corpus and configuration identities are immutable.
- Missing fixtures invalidate the run; they do not trigger an unrecorded live call.
- Failures and timeouts are retained as evaluation outcomes.

## Structural diff

```text
StructuralDiff
├── baseline_run_id
├── candidate_run_id
├── case_diffs[]
│   ├── claim_added / removed / changed
│   ├── evidence_changed
│   ├── retrieval_rank_changed
│   ├── memory_disposition_changed
│   ├── temporal_relation_changed
│   ├── conflict_changed
│   ├── route_changed
│   ├── answer_support_changed
│   ├── policy_changed
│   └── cost_changed
├── aggregate_delta
├── critical_regressions[]
├── improvements[]
└── review_status
```

The diff must distinguish harmless prose variation from changes in evidence, authority, memory or policy behavior.

## Initial benchmark suites

### ERP-01 — Retrieval routing

Compare lexical and hybrid execution on simple, ambiguous and multi-hop questions. Verify that lexical execution never calls dense/RRF and that both routes preserve the same authority chain.

### ERP-02 — Selective memory shadow

Run a candidate extractor on synthetic conversations. Measure durable-memory precision, sensitive blocking, source spans, temporal scope, duplicates and zero writes.

### ERP-03 — Temporal evidence

Evaluate historical, superseding and overlapping claims. Compare the current bi-temporal baseline with any candidate EvidenceEpisode/TemporalClaim projection.

### ERP-04 — Receipt normalization

Map existing retrieval, RCO, failure and memory receipts into a candidate shared envelope. Verify no domain-specific reason or authority is lost.

### ERP-05 — Procedural skill candidates

Evaluate source-linked procedures as read-only skill artifacts. Measure step fidelity, preconditions, failure conditions and prohibited effects.

## Promotion sequence

```text
research contract
→ fixture package
→ baseline run
→ candidate fork
→ structural diff
→ operator review
→ published thresholds
→ CI/offline prototype
→ shadow evaluation
→ separate implementation RFC
→ explicit Operator GO
```

No active runtime change is authorised by a successful offline benchmark alone.

## Minimum acceptance for the first implementation PR

- versioned dataclasses or schemas only;
- canonical JSON and stable digest helpers;
- synthetic fixture package with no secrets;
- deterministic clock and seed;
- baseline/fork identity;
- structural diff for claims, evidence, memory dispositions, routes and cost;
- assertions for `truth_gate_bypass_count == 0` and `query_path_write_count == 0`;
- no provider/network requirement;
- no production database writes;
- documented command producing a machine-readable report;
- CI runtime bounded by an approved budget.

## Core rule

```text
Freeze the inputs.
Record the configuration.
Compare structured behavior.
Treat failures as data.
Do not trade authority for speed.
Promote only after reproducible evidence.
```
