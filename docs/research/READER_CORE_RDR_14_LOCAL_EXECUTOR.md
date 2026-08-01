# PR-RDR-14 — Local Benchmark Executor

## Purpose

PR-RDR-14 connects the existing evaluation layers without granting runtime
authority:

```text
verified corpus descriptor + adjudicated gold labels
        ↓
explicit local pipeline adapter, run twice
        ↓
normalized ReaderDocumentPrediction values
        ↓
RDR-12 deterministic scorer
        ↓
RDR-10 ReaderBenchmarkObservation
        ↓
RDR-13 success or failure receipt
```

The executor is a local evaluation boundary. It is not `/query` integration and
it is not a scheduler, worker service, model router, memory writer, Canon writer,
or promotion mechanism.

## Contracts

### ReaderLocalBenchmarkCase

Binds one benchmark case ID to:

- one content-addressed `CorpusDocumentDescriptor`;
- one fully adjudicated `HumanLabelSet`;
- exact document, revision, and descriptor identity.

Annotator-only label sets are rejected. Gold data must have
`LabelSetRole.ADJUDICATED`.

### ReaderLocalPipeline

A protocol implemented by an external local adapter. The executor calls it with
`replay_index=1` and `replay_index=2`.

The protocol does not imply network, provider, model, or tool access. Any future
adapter must declare those dependencies separately and remain outside this
module's authority.

### ReaderLocalPipelineResult

Contains:

- a normalized `ReaderDocumentPrediction`;
- explicit `ReaderExecutionMeasurement` values;
- optional content-addressed run artifact IDs.

Predictions must match the benchmark case descriptor, document ID, and immutable
source revision.

### ReaderLocalExecutionResult

Contains exactly:

- a PR-RDR-13 `ReaderBenchmarkCaseReceipt`;
- a PR-RDR-10 `ReaderBenchmarkObservation` only for successful receipts.

Failed executions never expose a partial observation.

## Replay semantics

The executor performs two explicit pipeline calls. Replay equality is not assumed
from identical configuration. RDR-12 produces ordered artifact sequences and
RDR-10 computes replay digest equality.

The first run supplies performance measurements. The replay run exists to test
output reproducibility, not to average away divergence.

## Failure semantics

Ordinary pipeline, normalization, identity, and scoring failures become explicit
`FAILED` receipts with a deterministic error code derived from exception type and
message.

`KeyboardInterrupt` and `SystemExit` are never swallowed.

The checkpoint remains immutable. The caller must append the returned receipt
through `ReaderBenchmarkBatchPlanner.append_receipt()`.

## Retry semantics

Attempt number is derived exclusively from the checkpoint:

```text
no prior receipt        → attempt 1
terminal failed receipt → next contiguous attempt
successful/skipped case → not pending, execution rejected
attempt limit reached   → not pending, execution rejected
```

The executor cannot reset or forge attempt history.

## Authority boundary

`LOCAL_EXPLICIT_EXECUTION / SHADOW_EVALUATION / NO_RUNTIME_AUTHORITY`

This PR adds no:

- `/query` wiring;
- background scheduler or daemon;
- network or provider invocation;
- model selection policy;
- memory admission or persistence;
- Canon or graph writes;
- capability issuance;
- TruthGate or Write Gate bypass;
- automatic promotion;
- Crystal integration;
- live Reader Core activation.

This work belongs to **Velantrim ExoCortex Titan**, not Crystal.

## What remains after PR-RDR-14

RDR-14 makes a complete local evaluation connection possible. It does not create
real evidence by itself. Remaining operational work is:

1. implement or select an explicit local pipeline adapter;
2. populate a rights-cleared representative corpus;
3. independently annotate and adjudicate that corpus;
4. execute complete batches and preserve authenticated reports;
5. analyze failures and repeat evaluation;
6. run a separate shadow-integration and burn-in program;
7. require explicit Operator GO before any canary or live path.
