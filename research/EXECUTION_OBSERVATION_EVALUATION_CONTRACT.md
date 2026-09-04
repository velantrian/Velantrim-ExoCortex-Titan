# 🔭 Execution Observation & Evaluation Contract — Titan Research Track

**Status:** `R1 CONTRACT · RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon / ESM write authority:** none  
**Default enabled:** false  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Date:** 2026-09-04  
**Titan base reviewed:** `main@3a4ef241cd7c9232c35eb789aa4a69a5ecdf1cd6`

## Decision

Titan may adopt a small set of observability and evaluation patterns from external LLM
systems, but only after translating them into Titan-native, read-only contracts that
preserve existing ownership and authority boundaries.

The useful primitive is **not** a new tracing product, storage stack, TruthGate, policy
engine, evaluator sovereign, or memory owner. The useful primitive is a structured
observation projection over work Titan already performs, plus a bounded evaluation path
that can turn verified failures into replayable fixtures.

```text
existing Titan execution / receipts / evidence-use stages
                    ↓
          READ-ONLY OBSERVATION PROJECTION
                    ↓
             ExecutionTraceView
            ┌────────┼────────┐
            ▼        ▼        ▼
          Span      Span     Span
                    │
                    ▼
            bounded evaluation
                    │
                    ▼
          EvaluationObservation
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       replay    research   human review

                    X
                    │
              NO DIRECT CANON,
              BELIEF OR ACTION WRITE
```

## Prior-art record

The immediate source that triggered this intake was:

```text
source_repository: comet-ml/opik
source_revision: e9adfc9f3564ca0723cc7a80a16e129aa6e59da2
source_licence: Apache-2.0
copied_code: no
modified_code: no
review_date: 2026-09-04
```

Relevant prior-art patterns observed at that revision include hierarchical trace/span
observation, asynchronous evaluation of recorded traces, immutable dataset/prompt versions,
human annotation queues, evaluation sampling, bounded evaluator drill-down over large
traces, and OpenTelemetry/OTLP interoperability.

This record does **not** make Opik an architectural authority for Titan. No Opik source code,
class names, service topology, database choices or runtime dependency is imported by this
contract.

## 1. Existing Titan problem / opportunity

Titan already has TRACE, provenance, audit artifacts, reasoning traces and the bounded
Evidence-Use distinction:

```text
R = retrieved
S = serialized
T = transmitted
U = demonstrably used
A = demonstrably answer-supporting
```

Current Titan tests establish only the stages the runtime can actually observe and keep
`U` / `A` separate when causal attribution is not established.

Titan also already documents an operational observability gap: metrics and logs exist, but
reconstructing a past request as a first-class persisted execution tree is not yet a
complete capability.

The proposed contract therefore answers a narrow question:

> Can Titan describe the externally observable execution path of one bounded operation
> without promoting observation into evidence, causal attribution, truth, belief or
> permission?

## 2. Ownership map

| Concern | Existing owner | This contract may do | This contract may not do |
|---|---|---|---|
| orchestration / provider / tool execution | Titan | project a bounded execution tree | grant new execution permission |
| evidence / provenance / Canon admission | Crystal or current Titan-local accepted owners, depending on domain | carry opaque references | redefine evidence or Canon authority |
| process continuity / long-lived thread semantics | Continuum where cross-project continuity applies | reference a process/thread ID | become continuity authority |
| policy / capability permission | existing PolicyKernel + leases | record the decision/lease refs already produced | allow, widen or replace permission |
| cognition / belief / identity | owning cognition domain | carry typed outcome refs if explicitly provided | infer belief/identity from trace shape |
| System OS composition | System OS | map owner-local observations across domains | become a new runtime or truth owner |

The contract creates **no new owner**.

## 3. Hierarchical execution observation

### 3.1 Candidate projection

```text
ExecutionTraceView
├── schema_version
├── trace_id
├── operation_id
├── owner_domain
├── process_ref
├── root_span_id
├── span_refs[]
├── policy_snapshot_ref
├── capability_lease_refs[]
├── started_at
├── completed_at
├── status
├── limitations[]
└── digest

ExecutionSpanView
├── schema_version
├── span_id
├── trace_id
├── parent_span_id
├── operation_kind
├── owner_domain
├── stage_marker
├── input_refs[]
├── output_refs[]
├── evidence_refs[]
├── policy_decision_refs[]
├── started_at
├── completed_at
├── status
├── error_code
├── limitations[]
└── digest
```

Candidate `operation_kind` values may describe observable work such as retrieval, prompt
serialization, provider packing, model call, tool call, policy check, Reader step, handoff,
or bounded local transformation. They are descriptive categories, not permissions.

### 3.2 Non-conflation invariants

```text
SPAN != EVIDENCE
TRACE != PROOF OF USE
TRACE TREE != CAUSAL PROOF
PARENT_SPAN != AUTHORITY PARENT
OBSERVED TRANSMISSION != U
U != A
EVALUATION SCORE != TRUTH
OBSERVATION != CANON
```

A parent/child relation states that one observed operation was nested or linked under
another execution context. It does not by itself prove semantic causation.

A trace may show that evidence was retrieved, serialized and transmitted. It may not claim
that the model internally used that evidence or that the final answer was supported by it
unless a separate accepted attribution contract establishes `U` or `A`.

### 3.3 Privacy and retention boundary

Observation must prefer references, digests, reason codes, sizes, timings and bounded
previews over copying full sensitive payloads.

A persistent observation store, if ever selected, requires a separate retention, erasure,
access-control, storage-owner and incident-recovery decision. This R1 contract does not
select a database and does not authorize storing hidden chain-of-thought.

## 4. Evaluation plane

Evaluation is a **non-authoritative consumer** of recorded or fixture-bound observations.
It may classify, score, compare or request human review. It may not mutate the observed
runtime result or target-domain authoritative state.

```text
ExecutionTraceView
        ↓
EvaluationRule / deterministic assertion / reviewed rubric
        ↓
EvaluationObservation
        ↓
report / replay / fixture candidate / human review
```

Candidate output:

```text
EvaluationObservation
├── schema_version
├── evaluation_id
├── trace_ref
├── span_refs[]
├── evaluator_kind
├── evaluator_version
├── fixture_package_ref
├── prompt_or_rule_version
├── scores[]
├── deterministic_failures[]
├── reason_codes[]
├── reopen_refs[]
├── cost_usage
├── limitations[]
└── digest
```

`EvaluationObservation` is not an admission decision. If an evaluation result should later
influence Canon, policy, belief or an external action, it must travel through the existing
target-domain candidate/admission path.

## 5. Reuse the existing immutable replay protocol

Titan already has [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md). This
contract does not create a second experiment system.

The execution-observation layer should feed that existing protocol by preserving enough
version identity to reproduce a run:

```text
fixture/package digest
+ code revision
+ configuration snapshot
+ policy snapshot
+ model/provider fixture versions
+ evaluator version
+ prompt/rule version
+ observation schema version
= reproducibility envelope
```

No single metric is allowed to hide a critical authority, provenance, privacy or
non-interference failure.

## 6. Failure → fixture admission

A useful external pattern is to turn real failures into regression cases. Titan must make
that process stricter than simple automatic capture.

```text
observed failure
      ↓
Failure / Trace observation
      ↓
owner-local classification
      ↓
sanitize + minimize + remove secrets
      ↓
FixtureCandidate
      ↓
expected invariant / acceptable set / forbidden behavior
      ↓
operator or designated reviewer admission
      ↓
NEW immutable evaluation-package version
```

### Rules

- a production failure is **not** automatically a gold label;
- a model judge result is **not** automatically the expected answer;
- raw production prompts, personal data or secrets are not copied into repository fixtures;
- ambiguous cases may define a set of acceptable outcomes instead of one manufactured gold
  answer;
- the fixture records the owner and reason for admission;
- the previous package version remains immutable;
- fixing one failure must not silently relax critical gates for other cases.

Candidate fixture provenance:

```text
FailureDerivedFixture
├── fixture_id
├── source_trace_ref
├── source_failure_ref
├── owner_domain
├── sanitization_manifest
├── admitted_by
├── admitted_at
├── expected_invariants[]
├── acceptable_outcomes[]
├── forbidden_outcomes[]
├── limitation_notes[]
└── fixture_digest
```

## 7. Bounded selective drill-down

Large traces should not require an evaluator to receive every payload up front.

The candidate pattern is:

```text
bounded trace preview
       ↓
is evidence sufficient for this evaluation?
       ├── yes → finish evaluation
       └── no  → targeted read(trace/span/ref)
                       ↓
                  exact bounded item
```

Allowed drill-down must be:

- fixture-bound or read-only;
- explicitly budgeted by count/bytes/tokens/time/cost where applicable;
- recorded in `reopen_refs[]`;
- deterministic for offline replay when deterministic evaluation is claimed;
- unable to widen data visibility beyond the original evaluation scope;
- unable to call an unleased provider or external tool as a fallback.

This is an evaluation and inspection pattern, not a new general agent authority.

## 8. OpenTelemetry / transport position

OpenTelemetry or OTLP may later be evaluated as a **transport/interoperability profile** for
execution observations because they are vendor-neutral and widely supported.

```text
transport compatibility != Titan semantic authority
span export != evidence admission
OTLP ingestion != Canon write
```

No OpenTelemetry dependency is admitted by this document. A docs-only or adapter-based
interoperability experiment must be preferred over a new mandatory runtime dependency.

## 9. Explicitly rejected transfers

Do not import from external observability platforms:

- a second TruthGate, policy engine, memory Canon or admission authority;
- LLM-as-judge scores as truth or canonical evidence;
- automatic guardrail decisions as a replacement for Titan permission/admission owners;
- ClickHouse/MySQL/Redis/MinIO or any other storage topology as an architectural law;
- a mandatory SaaS or network dependency for the local-first path;
- full raw prompt/response persistence without retention and erasure ownership;
- automatic optimization that changes prompts, routing or tools without a separately
  authorized candidate/evaluation/promotion sequence;
- hidden chain-of-thought capture.

## 10. Cheapest useful experiments

### EO-01 — R/S/T execution tree fixture

Build an **offline fixture only** from the existing evidence-use contract. Represent the
retrieval, serialization and provider-packing stages as a parent/child trace tree and prove:

```text
R observable
S observable
T observable
T may be lossy
U NOT ESTABLISHED
A NOT ESTABLISHED
```

Acceptance requires zero new runtime caller and zero Canon/policy mutation.

### EO-02 — Failure-derived regression fixture

Take one synthetic or already-public deterministic failure case, pass it through explicit
classification and sanitization, create a fixture candidate, and verify that admitting it
creates a new immutable package version without rewriting the previous package.

### EO-03 — Selective evaluator reopen

On a synthetic oversized trace, give the evaluator a bounded preview and allow only
fixture-local reads of explicitly addressed spans. Measure reopen count, bytes/tokens read,
result stability and scope violations.

## 11. Promotion evidence

No runtime implementation follows from this R1 contract. Promotion requires at minimum:

1. a concrete Titan workload or the already-documented historical-trace reconstruction gap;
2. owner review confirming no duplicate TRACE/audit/evidence/continuity authority;
3. privacy/retention/erasure review for any persistent trace storage;
4. deterministic EO-01 / EO-02 fixtures;
5. explicit resource ceilings for drill-down and storage;
6. proof that observation cannot mutate Canon, ESM, policy or runtime decisions;
7. comparison against the simpler existing TRACE/logging baseline;
8. a separate bounded implementation PR;
9. separate activation / Operator GO if runtime authority or production posture changes.

## 12. Reality status

```text
architecture contract documented:     yes (this R1 proposal)
external source reviewed:             yes
external code copied:                 no
trace/span runtime implementation:    not added here
persistent trace store:               not added here
OpenTelemetry dependency:             not added here
failure-derived fixture pipeline:     not implemented here
selective evaluator drill-down:       not implemented here
Canon / ESM / TruthGate authority:    unchanged
PolicyKernel authority:               unchanged
runtime enabled:                      unchanged
Operator GO:                          unchanged
production authority:                 unchanged
```

## Core rule

```text
Observe execution without inventing causation.
Evaluate behavior without acquiring authority.
Turn established failures into replayable fixtures, not automatic truth.
Reuse existing owners and replay contracts.
Borrow patterns, never external sovereignty.
```