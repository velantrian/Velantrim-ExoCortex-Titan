# PR-RDR-21 — Signed completed-batch finalization

## Status

Repository-side deterministic foundation only.

Boundary:

`COMPLETE_SUCCESS_ONLY / EXACT_THRESHOLD_POLICY / SIGNED_BUNDLE / FULL_RECEIPT_INDEX / OPERATOR_GO_STILL_REQUIRED / NO_LIVE_AUTHORITY`

## Purpose

RDR-19 prepares benchmark cases and an empty batch checkpoint. RDR-20 executes
explicit bounded passes and can expose `ReaderBenchmarkInput` only after every
planned case has a latest successful receipt. RDR-10 already computes the
canonical evaluation report, promotion review, benchmark bundle, and detached
HMAC-SHA256 authenticator.

RDR-21 closes the ownership gap between those layers. It proves that one signed
benchmark bundle came from:

1. one exact RDR-19 preparation;
2. one exact RDR-20 complete-success state;
3. the exact evaluation corpus and environment in the batch plan;
4. the exact threshold policy ID fixed before execution;
5. every retained receipt, including failed attempts that preceded success;
6. every artifact ID referenced by those receipts.

It does not introduce another scorer, evaluator, promotion reviewer, scheduler,
pipeline adapter, or runtime integration path.

## Flow

```text
RDR-19 preparation
        |
        | exact preparation_id / plan / corpus / environment / threshold policy
        v
RDR-20 COMPLETE_SUCCESS execution state
        |
        | complete observations + full receipt history
        v
ReaderBenchmarkInput
        |
        v
existing RDR-10 ReaderBenchmarkRunner
        |
        +--> EvaluationSuiteReport
        +--> ReaderPromotionReview
        +--> ReaderBenchmarkBundle
        |
        v
existing RDR-10 HMAC-SHA256 signature
        |
        v
ReaderSignedBenchmarkEvidence
```

## Contracts

### `ReaderCompletedBatchFinalizer`

The finalizer rejects input unless:

- the preparation, state, and thresholds use their exact typed contracts;
- the execution status is `COMPLETE_SUCCESS`;
- the state belongs to the supplied preparation;
- the state checkpoint plan exactly equals the preparation batch plan;
- the evaluation manifest corpus equals the planned corpus;
- the execution environment equals the planned environment;
- `thresholds.thresholds_id` equals the plan's precommitted
  `threshold_policy_id`;
- every planned case has a latest successful receipt;
- `state.to_benchmark_input()` succeeds without partial coverage.

The finalizer then delegates report and review construction to the existing
`ReaderBenchmarkRunner` and delegates detached authentication to the existing
`ReaderBenchmarkSigner`.

### `ReaderSignedBenchmarkEvidence`

The evidence record contains:

- the exact preparation ID;
- the full immutable RDR-20 execution state;
- the canonical RDR-10 benchmark bundle;
- the detached benchmark bundle signature;
- every receipt ID in canonical checkpoint order;
- a separate index of historical failed-attempt receipt IDs;
- the sorted union of every artifact ID referenced by all receipts;
- a self-verifying content-addressed evidence ID.

The evidence record checks all cross-layer ownership again during construction.
It cannot be instantiated with a partial state, foreign bundle, foreign
threshold policy, reordered receipt history, dropped failure receipt, or
incomplete artifact index.

## Retry evidence is not erased

A case may fail on attempt 1 and succeed on attempt 2. The final benchmark input
contains only the successful observation, as required by the scorer. The signed
finalization evidence still indexes both receipts:

```text
case A attempt 1 -> FAILED receipt retained
case A attempt 2 -> SUCCEEDED receipt retained
latest case result -> successful observation
final evidence -> both receipt IDs + all referenced artifact IDs
```

This prevents a successful retry from rewriting history into an apparently
failure-free run.

## Authentication

`ReaderCompletedBatchFinalizer.verify(...)` delegates to the existing detached
HMAC-SHA256 verifier. A wrong secret or modified signature returns `False`.
Secrets remain caller-supplied bytes and are never included in identity payloads
or evidence artifacts.

The content-addressed evidence ID and the detached authenticator have different
roles:

- the evidence ID detects internal content mismatch;
- the HMAC verifies possession of the configured signing secret for the
  canonical benchmark bundle.

## Promotion semantics

The finalized bundle may produce one of the existing decisions:

- `insufficient_evidence`;
- `no_go`;
- `eligible_for_operator_review`.

All three preserve:

```text
operator_go_required = true
live_integration_authorized = false
```

Therefore:

```text
signed evidence != passing thresholds
passing thresholds != Operator GO
Operator GO != automatic live integration
```

## Explicit non-goals

RDR-21 does not:

- create or infer human labels;
- select or execute a `ReaderLocalPipeline`;
- retry cases;
- calibrate or mutate thresholds after seeing results;
- suppress failed attempts;
- upload artifacts;
- schedule background work;
- wire `/query`;
- write memory or Canon;
- grant graph, policy, tool, TruthGate, or Write Gate authority;
- open shadow or canary integration;
- record an Operator decision.

## Tests

Regression coverage includes:

- successful deterministic finalization;
- correct and incorrect HMAC secrets;
- incomplete and exhausted-failure rejection;
- exact threshold-policy enforcement;
- preparation ownership enforcement;
- deterministic evidence IDs;
- failed-attempt retention after successful retry;
- receipt-order and artifact-index fail-closed checks;
- forged evidence-ID rejection;
- immutable Operator GO and live-authorization boundaries.

## What remains external

Repository contracts cannot manufacture production evidence. Issue #120 still
requires:

1. a rights-cleared representative corpus;
2. independent human annotation and adjudication;
3. a reviewed concrete local pipeline adapter;
4. actual full-batch execution in fixed environments;
5. retained raw artifacts referenced by receipt IDs;
6. threshold calibration from measured results;
7. shadow burn-in;
8. an explicit Operator decision.
