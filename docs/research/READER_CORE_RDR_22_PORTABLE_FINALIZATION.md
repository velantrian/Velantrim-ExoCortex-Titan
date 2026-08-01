# PR-RDR-22 — Portable completed-batch finalization

## Status

Repository-side deterministic operator tooling only.

Boundary:

`COMPLETE_SUCCESS_EXPORT_ONLY / STRICT_CANONICAL_JSON / NO_RAW_DOCUMENTS / EXACT_THRESHOLD_POLICY / SECRET_FROM_ENV_ONLY / NO_OPERATOR_GO`

## Purpose

RDR-21 can finalize a complete successful RDR-20 state when the original RDR-19
preparation object is still available in the same Python process. That is a
strong typed contract, but it is not yet a portable operator workflow.

RDR-22 introduces a minimal post-execution envelope and a strict CLI path:

```text
RDR-19 preparation + RDR-20 COMPLETE_SUCCESS state
        |
        v
ReaderBenchmarkFinalizationEnvelope
        |
        | canonical JSON file
        v
strict loader + exact threshold file + HMAC secret from env
        |
        v
RDR-21 signed benchmark evidence
```

The envelope deliberately contains only material needed after execution:

- the exact preparation ID;
- the evaluation corpus manifest;
- the exact batch plan, including the precommitted threshold-policy ID;
- the complete RDR-20 execution state, checkpoint, receipt history, and
  successful observations;
- a self-verifying envelope ID.

It does not duplicate raw source documents, human annotation working sets,
adjudication packets, local pipeline implementations, or signing secrets.

## Why this is not a full preparation codec

After execution, report construction needs the evaluation manifest,
observations, environment, and planned threshold policy. It does not need raw
documents or adjudicated gold again because scoring already occurred inside the
local executor and the resulting observations are bound to successful receipts.

Exporting the entire original evidence corpus would:

- duplicate sensitive material unnecessarily;
- enlarge the attack and retention surface;
- complicate independent artifact handling;
- provide no additional input to the existing report aggregator.

The preparation ID remains in the envelope as the trace back to the original
RDR-19 evidence chain.

## Envelope invariants

`ReaderBenchmarkFinalizationEnvelope` rejects construction unless:

- the execution state is `COMPLETE_SUCCESS`;
- the state belongs to the supplied preparation ID;
- the checkpoint plan exactly equals the exported batch plan;
- the evaluation manifest corpus equals the planned corpus;
- manifest case IDs exactly equal planned case IDs;
- the environment equals the planned environment;
- every planned case has a latest successful receipt;
- successful observations exactly cover every planned case;
- the envelope ID matches all exported identities.

Historical failed attempts remain inside the checkpoint. A later successful
retry does not erase them.

## Strict JSON codec

`write_finalization_envelope(...)` uses the existing canonical JSON writer.

`load_finalization_envelope(...)`:

1. decodes UTF-8;
2. rejects duplicate object keys;
3. rejects missing or unknown fields at every level;
4. reconstructs typed environment, manifest, plan, receipts, checkpoint,
   observations, execution state, and envelope objects;
5. revalidates every content-addressed ID through the constructors;
6. serializes the reconstructed envelope again;
7. requires byte-for-byte equality with the source file.

Therefore semantically similar but noncanonical JSON is rejected. This includes
reordered arrays that constructors would otherwise normalize, pretty-printed
variants, forged IDs, extra fields, omitted fields, duplicate keys, and stale
cross-references.

## Unified finalization path

RDR-21 now exposes:

```python
finalizer.finalize(
    preparation=preparation,
    state=state,
    thresholds=thresholds,
    key_id=key_id,
    secret=secret,
)
```

and:

```python
finalizer.finalize_envelope(
    envelope=envelope,
    thresholds=thresholds,
    key_id=key_id,
    secret=secret,
)
```

The first path creates an envelope and delegates to the second. There is only
one report/signature/evidence implementation.

## CLI

```bash
python scripts/finalize_reader_benchmark_evidence.py \
  --envelope /secure/reader/finalization-envelope.json \
  --thresholds /secure/reader/thresholds.json \
  --bundle-output /secure/reader/benchmark-bundle.json \
  --signature-output /secure/reader/benchmark-signature.json \
  --evidence-output /secure/reader/signed-evidence.json \
  --hmac-key-env READER_BENCHMARK_HMAC_KEY \
  --key-id reader-benchmark-key-v1
```

The command:

- refuses noncanonical or forged envelopes;
- reconstructs the exact threshold object;
- requires its content-addressed ID to equal the batch plan's
  `threshold_policy_id`;
- reads the signing secret only from the named environment variable;
- refuses to overwrite any existing output artifact;
- writes separate canonical bundle, detached signature, and signed evidence
  files;
- reports decision and immutable IDs without printing the secret;
- can return exit code `3` with `--require-eligible` when the result is not
  `eligible_for_operator_review`.

Exit code `3` is a policy/reporting result, not an execution error. It does not
delete the valid evidence files.

## Security and authority boundaries

RDR-22 does not:

- execute or select a pipeline;
- read raw corpus documents;
- create or modify human labels;
- retry failed cases;
- change thresholds after observing results;
- accept a secret on the command line;
- write the secret into any artifact;
- upload files or use the network;
- schedule background work;
- wire `/query`;
- write memory or Canon;
- grant graph, policy, tool, TruthGate, or Write Gate authority;
- record Operator GO;
- authorize shadow, canary, or live integration.

The output continues to preserve:

```text
operator_go_required = true
live_integration_authorized = false
```

## Tests

Regression coverage includes:

- exact canonical round trip;
- typed and portable finalization equivalence;
- absence of raw document text from the envelope;
- duplicate-key rejection;
- unknown-field rejection;
- forged-ID rejection;
- noncanonical-byte rejection;
- incomplete-state export rejection;
- end-to-end CLI finalization;
- secret non-disclosure;
- `--require-eligible` exit semantics;
- output overwrite protection.

## Remaining external work

Portable artifacts do not create production evidence. Issue #120 still requires
rights-cleared documents, independent annotation and adjudication, a reviewed
local pipeline, actual complete runs, retained raw artifacts, measured threshold
calibration, shadow burn-in, and an explicit Operator decision.
