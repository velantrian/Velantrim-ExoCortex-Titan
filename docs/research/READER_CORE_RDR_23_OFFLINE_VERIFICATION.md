# PR-RDR-23 — Offline signed-evidence verification

## Status

Read-only deterministic operator tooling.

Boundary:

`OFFLINE_ONLY / READ_ONLY_INPUTS / FULL_DETERMINISTIC_RECONSTRUCTION / HMAC_VERIFIED / NO_OPERATOR_GO / NO_LIVE_AUTHORITY`

## Purpose

RDR-22 can emit three portable canonical artifacts:

1. `benchmark-bundle.json`;
2. `benchmark-signature.json`;
3. `signed-evidence.json`.

Checking only the detached HMAC would prove that the bundle bytes were signed by
someone holding the key. It would not independently prove that:

- the report and review are the deterministic result of the supplied state;
- the bundle uses the exact planned thresholds;
- the evidence file contains the same bundle and signature;
- receipt and artifact indexes match the execution checkpoint;
- Operator GO and live-authorization boundaries remain intact.

RDR-23 performs all of those checks offline.

## Verification flow

```text
bundle file -----------+
signature file --------+----> canonical JSON checks
signed evidence file --+             |
                                     v
                         reconstruct execution state
                                     |
                                     v
                         reconstruct manifest/thresholds
                                     |
                                     v
                         state -> benchmark input
                                     |
                                     v
                         existing deterministic runner
                                     |
                                     v
                         regenerated report/review/bundle
                                     |
                         byte-for-byte equality with bundle file
                                     |
                                     v
                         typed signature + HMAC verification
                                     |
                                     v
                         regenerated signed evidence
                                     |
                         byte-for-byte equality with evidence file
                                     |
                                     v
                         verification receipt
```

No model, provider, document parser, network service, scheduler, or runtime path is
invoked.

## Canonical file checks

Each input file must:

- be valid UTF-8 JSON;
- be a top-level object;
- contain no duplicate keys;
- contain no `NaN`, positive infinity, or negative infinity;
- be exactly equal to the project's canonical JSON serialization, including the
  final newline.

Pretty-printed, reordered, duplicate-key, or otherwise noncanonical variants are
rejected before semantic verification.

## Deterministic bundle reconstruction

The verifier reconstructs typed values from the files:

- `ReaderPreparedBatchExecutionState`;
- `EvaluationEnvironment`;
- `EvaluationCorpusManifest` and each case manifest;
- `ReaderBenchmarkBatchPlan`, checkpoint, receipts, and observations;
- `ReaderPromotionThresholds`;
- `ReaderBenchmarkInput`.

It creates a `ReaderBenchmarkFinalizationEnvelope`, which rechecks preparation,
plan, corpus, environment, case coverage, successful latest receipts, and
observation coverage.

The existing `ReaderBenchmarkRunner` then regenerates:

- per-case evaluation results;
- aggregate metrics;
- promotion review;
- complete benchmark bundle.

The canonical regenerated bundle bytes must exactly equal the supplied bundle
file. A changed metric, warning, threshold, report ID, review decision, Operator
flag, live flag, or other field therefore fails before signature acceptance.

## Signature verification

The detached signature file is reconstructed as a typed
`ReaderBenchmarkSignature`. This rechecks:

- algorithm;
- schema;
- bundle ID;
- bundle digest;
- signature digest formatting;
- content-addressed signature ID.

The existing `ReaderBenchmarkSigner.verify(...)` then verifies the HMAC using the
caller-supplied secret. The secret is never written into an artifact or
verification receipt.

## Signed evidence reconstruction

The verifier requires the nested `benchmark_bundle` and `bundle_signature`
inside `signed-evidence.json` to exactly match their external files.

It then reconstructs `ReaderSignedBenchmarkEvidence` using:

- the typed execution state;
- the regenerated benchmark bundle;
- the typed detached signature;
- supplied receipt IDs;
- historical failed-attempt receipt IDs;
- artifact IDs;
- supplied schema and evidence ID.

The constructor rechecks complete success, plan ownership, exact benchmark input,
threshold policy, receipt order, failed-attempt history, artifact union, Operator
GO requirement, and the prohibition on live authorization.

The canonical reconstructed evidence bytes must exactly equal the supplied
evidence file.

## Verification receipt

Successful verification returns a content-addressed
`ReaderBenchmarkEvidenceVerificationReceipt` containing:

- reconstructed envelope ID;
- evidence ID;
- benchmark bundle ID;
- signature ID and non-secret key ID;
- SHA-256 digests of all three complete files;
- promotion-review decision;
- `operator_go_required`;
- `live_integration_authorized`;
- verification receipt ID.

A verification receipt can exist only with:

```text
operator_go_required = true
live_integration_authorized = false
```

It contains no HMAC secret.

## CLI

```bash
python scripts/verify_reader_benchmark_evidence.py \
  --bundle /secure/reader/benchmark-bundle.json \
  --signature /secure/reader/benchmark-signature.json \
  --evidence /secure/reader/signed-evidence.json \
  --hmac-key-env READER_BENCHMARK_HMAC_KEY \
  --verification-output /secure/reader/verification-receipt.json
```

The command is read-only with respect to the three supplied artifacts. An
optional verification receipt is written only after every check succeeds, and
an existing receipt file is never overwritten.

With `--require-eligible`, exit code `3` means the evidence is valid but its
review is not `eligible_for_operator_review`. It does not mean verification
failed. Verification errors use exit code `2`.

## Fail-closed examples

Verification rejects:

- a wrong HMAC key;
- a modified bundle even when the evidence file is modified to match it;
- a modified external bundle that no longer matches the evidence copy;
- a modified signature file;
- a forged signature ID;
- missing or extra evidence fields;
- dropped receipt IDs;
- dropped historical failed-attempt receipts;
- incomplete artifact indexes;
- altered Operator or live-authorization flags;
- duplicate JSON keys;
- noncanonical JSON bytes;
- stale or foreign content-addressed IDs.

## Non-goals

RDR-23 does not:

- prove that a human annotation was intellectually correct;
- prove that a retained artifact ID still has backing bytes outside the supplied
  evidence files;
- execute Reader Core;
- retry failed cases;
- calibrate thresholds;
- select a provider;
- access the network;
- upload or mutate evidence;
- record Operator GO;
- authorize shadow, canary, or live integration;
- write memory or Canon;
- grant graph, policy, tool, TruthGate, or Write Gate authority.

## Remaining external evidence

The verifier establishes internal integrity and deterministic reproducibility of
the supplied artifact set. Issue #120 still requires the external facts that the
repository cannot manufacture: representative rights-cleared documents,
independent human labels, adjudication, reviewed local execution, retained raw
artifacts, measured calibration, shadow burn-in, and an explicit Operator
decision.
