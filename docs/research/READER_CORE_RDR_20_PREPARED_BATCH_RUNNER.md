# PR-RDR-20 — Explicit local prepared-batch runner

Status: **bounded local execution foundation**

Boundary:

```text
PREPARED_CASES_ONLY
CALLER_SUPPLIED_LOCAL_PIPELINE
ONE_ATTEMPT_PER_SELECTED_CASE_PER_PASS
IMMUTABLE_STATE_AND_RECEIPTS
FAILURES_RETAINED
NO_BACKGROUND_SCHEDULER
NO_PROVIDER_SELECTION
NO_PARTIAL_SUCCESS_REPORT
NO_PROMOTION_OR_LIVE_AUTHORITY
NO_QUERY_MEMORY_CANON_OR_CRYSTAL_WIRING
```

## Purpose

RDR-19 produces local benchmark cases, an evaluation manifest, a batch plan, and
an empty checkpoint. RDR-20 executes those prepared cases through an explicit
caller-supplied `ReaderLocalPipeline`.

The execution path is:

```text
ReaderBenchmarkPreparationBundle
+ EvaluationEnvironment
+ reviewed ReaderLocalPipeline
  -> ReaderPreparedBatchExecutionState (empty)
  -> explicit run_pass
  -> RDR-14 execution per selected pending case
  -> RDR-13 receipt append
  -> retained successful observations
  -> updated immutable execution state
```

The runner does not load a provider, resolve a model, import arbitrary adapter
code, start a worker, or schedule future execution. The caller must supply the
reviewed local pipeline object explicitly.

## Initial state

`ReaderPreparedBatchRunner.initial_state` requires:

- a valid RDR-19 preparation bundle;
- the exact `EvaluationEnvironment` whose content-addressed ID is recorded in the
  batch plan;
- an empty preparation checkpoint.

The resulting state contains zero receipts and zero observations and reports
status `ready`.

A foreign environment, stale checkpoint, or modified preparation fails closed.

## Explicit bounded passes

`run_pass` snapshots the checkpoint's current pending case IDs. It processes each
selected case at most once during that call.

Optional `max_cases` bounds the number of cases processed in the pass. The case
order follows the canonical batch-plan order.

This rule is important for retries:

```text
pass 1: case fails attempt 1
pass 1 ends
operator inspects state
pass 2: case may run attempt 2
```

A single call never burns through all configured retry attempts. Retrying remains
an explicit operator or higher-level orchestration decision.

## Receipts and observations

Every execution returns an RDR-13 receipt:

- success receipt: contains exactly one observation ID;
- failed receipt: contains an error code and no observation;
- prior failed attempts remain in the checkpoint after a later success.

The state retains one observation per case only when the latest receipt for that
case is successful. The observation ID must exactly match that receipt.

The constructor rejects:

- observations outside the batch plan;
- duplicate observation case IDs;
- observations without a latest success receipt;
- success receipts without the matching observation;
- foreign environments or checkpoints;
- forged state IDs.

## Execution statuses

The state exposes four statuses:

1. `ready` — no receipts exist;
2. `in_progress` — work or retries remain pending;
3. `complete_success` — every case's latest receipt is successful;
4. `complete_with_failures` — the batch is terminal but at least one case failed
   or was skipped.

A failed case with attempts remaining is `in_progress`, not complete.

## Benchmark input gate

`to_benchmark_input()` succeeds only for `complete_success`.

It builds the existing RDR-10 `ReaderBenchmarkInput` from:

- the exact prepared environment;
- one retained observation for every batch case.

A terminal batch containing failed or skipped cases cannot produce a benchmark
input. This prevents a report from silently excluding difficult documents.

The existing benchmark runner also checks that observation case IDs exactly
match the evaluation manifest, providing a second fail-closed boundary.

## Crash and resume semantics

`ReaderPreparedBatchExecutionState` is immutable and content-addressed. A caller
may serialize it after each pass and later restore the typed object. The
checkpoint preserves every attempt receipt; successful observations are retained
by case ID.

RDR-20 does not itself choose a persistence backend. Local atomic-file storage,
signatures, locking, and process fencing remain separate operational work. This
avoids granting database or scheduler authority to the execution contract.

## Pipeline boundary

The supplied pipeline must implement the existing RDR-14 protocol:

```python
def run_case(case, *, replay_index) -> ReaderLocalPipelineResult:
    ...
```

RDR-14 calls it twice per successful attempt for replay comparison. Pipeline
exceptions become failed receipts except `KeyboardInterrupt` and `SystemExit`,
which propagate to the caller.

The pipeline is responsible for producing Reader artifacts and measurements. It
receives no authority from RDR-20 to write memory, Canon, graph, policy, query,
or tool state.

## Security properties

1. Only cases already admitted by RDR-19 can execute.
2. Every selected case receives at most one attempt per pass.
3. Failed attempts remain visible after retry.
4. Observations cannot exist without successful receipts.
5. Partial success cannot become benchmark input.
6. Environment and preparation identities are exact and content-addressed.
7. No provider, network, scheduler, `/query`, memory, Canon, graph, tool,
   TruthGate, Write Gate, Crystal, or Native Kernel path is selected or invoked
   by the runner itself.

## Next operational step

After every case completes successfully, the caller may pass the generated
`ReaderBenchmarkInput`, the RDR-19 evaluation manifest, and the reviewed threshold
policy to the existing RDR-10 benchmark runner. That produces the canonical
report and promotion-review object.

A report marked `eligible_for_operator_review` is still not live authorization.
Shadow burn-in and explicit Operator GO remain mandatory.
