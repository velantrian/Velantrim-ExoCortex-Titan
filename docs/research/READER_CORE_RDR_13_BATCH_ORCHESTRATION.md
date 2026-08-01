# PR-RDR-13 — deterministic benchmark batch orchestration

## Status

`SHADOW_EVALUATION / LOCAL_STATE_ONLY / NO_EXECUTION_AUTHORITY / NO_LIVE_AUTHORIZATION`

PR-RDR-13 defines the immutable plan and checkpoint layer required to run a
Reader Core corpus benchmark in multiple local steps without losing provenance
or silently dropping failed cases.

It does **not** execute Reader Core, call a model, access the network, schedule a
worker, write memory or Canon, invoke TruthGate or Write Gate, or authorize live
integration.

## Why this layer exists

RDR-10 can build a canonical evaluation bundle from observations. RDR-11 can
verify corpus descriptors and adjudicated human labels. RDR-12 can score one
prediction set against one gold label set. A real corpus run still needs a
reproducible answer to four operational questions:

1. Which exact cases belong to this run?
2. Which environment and threshold policy were used?
3. Which cases completed, failed, or were skipped?
4. Can an interrupted run resume without replaying or losing work silently?

RDR-13 answers those questions with content-addressed plans and checkpoints.

## Core contracts

### `ReaderBenchmarkBatchPlan`

Binds one corpus, environment, threshold policy, ordered case set, and retry
limit. Input case order is canonicalized; duplicate case IDs fail closed.

### `ReaderBenchmarkCaseReceipt`

Records one attempt for one case. Terminal semantics are explicit:

- `SUCCEEDED` requires an `observation_id` and forbids an error code;
- `FAILED` and `SKIPPED` require an error code and forbid an observation ID;
- `PENDING` and `RUNNING` cannot carry result fields.

Artifact IDs are references only. Raw corpus text, prompts, model outputs, and
secrets do not belong in the receipt.

### `ReaderBenchmarkBatchCheckpoint`

Stores an immutable receipt chain. It verifies:

- every receipt belongs to the same plan;
- every case is part of the plan;
- attempts are unique, contiguous, and bounded;
- a new attempt can follow only a terminal previous attempt;
- successful observations cannot be read as a final set before completion.

## Resume semantics

A failed case remains pending only while attempts remain. A skipped case is
terminal and must preserve a reason code such as `missing-gold-labels` or
`corpus-hash-mismatch`. Nothing disappears from the run merely because it could
not be scored.

```text
plan
  -> checkpoint 0
  -> attempt receipt
  -> checkpoint 1
  -> retry receipt
  -> checkpoint 2
  -> final observation IDs
  -> RDR-10 canonical bundle
```

## Explicit non-scope

- no model or Reader Core execution;
- no multiprocessing or remote scheduler;
- no database schema or long-running service;
- no automatic retry timer;
- no corpus distribution or licensing policy;
- no hidden fuzzy scorer;
- no automatic promotion;
- no `/query`, memory, Canon, graph, tool, or Native Kernel integration.

## Next layer

A later local executor may consume `pending_case_ids`, run the already-approved
Reader pipeline in an isolated environment, score results through RDR-12, and
append typed receipts. That executor must preserve this plan/checkpoint contract
and remain shadow-only until real benchmark evidence and explicit Operator GO.
