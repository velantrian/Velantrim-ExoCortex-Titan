# PR-RDR-15 — Synthetic End-to-End Smoke

## Purpose

RDR-15 adds one executable smoke command that runs the committed synthetic
Reader Core evaluation fixtures through the existing RDR-09/RDR-10 report path.
It proves that the source-controlled manifest, benchmark observations, threshold
policy, aggregate metrics, promotion review, and canonical bundle serialization
remain connected.

```text
synthetic manifest
+ committed benchmark observations
+ committed thresholds
        ↓
ReaderBenchmarkRunner
        ↓
canonical benchmark bundle
        ↓
mandatory insufficient_evidence decision
```

## Command

```bash
python scripts/run_reader_synthetic_smoke.py \
  --output artifacts/reader-core/synthetic-smoke.json
```

The default inputs are:

- `tests/fixtures/reader_core/rdr_09_synthetic_evaluation.json`
- `tests/fixtures/reader_core/rdr_10_benchmark_input.json`
- `tests/fixtures/reader_core/rdr_10_thresholds.json`

Custom local paths may be supplied for negative and compatibility testing.

## Mandatory assertions

The smoke command fails unless all of the following remain true:

- decision is `insufficient_evidence`;
- `live_integration_authorized` is false;
- `operator_go_required` is true;
- synthetic case count equals the committed manifest size;
- real case count is zero;
- human-labelled case count is zero.

These checks prevent a future refactor from accidentally treating perfect
synthetic fixtures as production evidence.

## Failure behavior

Invalid or missing inputs return exit code `2`, write a diagnostic to stderr,
and do not create the requested output bundle.

## Boundary

`SYNTHETIC_ONLY / SMOKE_EVIDENCE / NO_PRODUCTION_CLAIM / NO_LIVE_AUTHORIZATION`

RDR-15 does not:

- run a real document corpus;
- create human labels;
- execute `/query`;
- invoke a provider or network model;
- write memory or Canon;
- grant graph or policy authority;
- promote Reader Core;
- integrate Crystal;
- replace Operator review.

## Remaining external evidence work

After RDR-15, all repository-side evaluation plumbing is executable. The work
that cannot be honestly manufactured by the implementation itself remains:

1. rights-cleared representative real documents;
2. independent human annotations;
3. explicit adjudication of disagreements;
4. real local pipeline runs and signed reports;
5. error analysis and threshold calibration;
6. shadow burn-in, canary planning, and separate Operator GO.
