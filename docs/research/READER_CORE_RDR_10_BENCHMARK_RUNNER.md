# PR-RDR-10 — Executable benchmark runner and authenticated report

Status: **shadow evaluation foundation**

Boundary:

```text
LOCAL_FILES_ONLY
OBSERVATION_ONLY
NO_MODEL_EXECUTION
NO_QUERY_WIRING
NO_MEMORY_OR_CANON_WRITE
OPERATOR_GO_REQUIRED
NO_LIVE_AUTHORIZATION
```

## Purpose

PR-RDR-09 introduced immutable evaluation contracts, metrics and promotion
review. PR-RDR-10 makes those contracts executable from source-controlled JSON
inputs and produces one canonical artifact that can be replayed, compared and
authenticated.

```text
manifest + measured observations + thresholds
    -> strict local loader
    -> replay comparisons
    -> aggregate metrics
    -> promotion review
    -> canonical benchmark bundle
    -> optional detached HMAC-SHA256 authenticator
```

The runner does **not** execute Reader Core or an LLM. A benchmark adapter must
first measure a run and write explicit observations. This separation prevents
model execution, scoring policy and promotion authority from collapsing into
one opaque command.

## Files

- `core/reader_benchmark_runner.py`
- `scripts/run_reader_benchmark.py`
- `tests/test_reader_benchmark_runner.py`
- `tests/fixtures/reader_core/rdr_10_benchmark_input.json`
- `tests/fixtures/reader_core/rdr_10_thresholds.json`

The existing PR-RDR-09 manifest remains the synthetic corpus manifest:

- `tests/fixtures/reader_core/rdr_09_synthetic_evaluation.json`

## Input contracts

### Evaluation manifest

Schema:

```text
reader-core.evaluation-manifest.v1
```

The manifest declares expected labelled counts and corpus kind. It is not a
prediction file.

### Benchmark input

Schema:

```text
reader-core.benchmark-input.v1
```

It contains:

- explicit environment identity;
- one observation for every manifest case;
- two ordered artifact-ID sequences for replay comparison;
- measured quality counts;
- measured latency, resource and resume counts;
- explicit safety counters;
- warnings.

Observation IDs are content-addressed. Input order is canonicalized by
`case_id`, but artifact order is preserved because replay is order-sensitive.
The runner rejects missing and extra cases.

### Promotion thresholds

Schema:

```text
reader-core.promotion-thresholds.v1
```

Thresholds are explicit, content-addressed inputs. They are not hidden defaults
inside the runner.

## Running the synthetic fixture

```bash
python scripts/run_reader_benchmark.py \
  --manifest tests/fixtures/reader_core/rdr_09_synthetic_evaluation.json \
  --input tests/fixtures/reader_core/rdr_10_benchmark_input.json \
  --thresholds tests/fixtures/reader_core/rdr_10_thresholds.json \
  --output artifacts/reader-core/benchmark-bundle.json
```

The committed fixture is intentionally synthetic-only. Even with perfect
synthetic measurements, its expected decision is:

```text
INSUFFICIENT_EVIDENCE
```

because real and independently human-labelled corpora are absent.

## Detached authentication

The CLI accepts no secret value on the command line. The secret must come from
an environment variable:

```bash
export READER_EVAL_HMAC_KEY='at-least-32-bytes-of-secret-material'

python scripts/run_reader_benchmark.py \
  --manifest tests/fixtures/reader_core/rdr_09_synthetic_evaluation.json \
  --input tests/fixtures/reader_core/rdr_10_benchmark_input.json \
  --thresholds tests/fixtures/reader_core/rdr_10_thresholds.json \
  --output artifacts/reader-core/benchmark-bundle.json \
  --signature-output artifacts/reader-core/benchmark-bundle.signature.json \
  --hmac-key-env READER_EVAL_HMAC_KEY \
  --key-id operator-evaluation-key-v1
```

The detached artifact contains:

- bundle ID;
- key ID;
- SHA-256 digest of canonical bundle bytes;
- HMAC-SHA256 value;
- self-verifying signature ID.

The secret is never serialized.

### Cryptographic limitation

HMAC is symmetric authentication. Anyone who can verify with the shared secret
can also create a new valid MAC. Therefore this artifact proves integrity and
shared-secret possession; it is **not** a publicly verifiable Ed25519 signature
and does not establish independent third-party authorship.

Public-key signing, hardware-backed keys and external transparency logs remain
future operational work.

## Exit codes

- `0`: bundle was built successfully;
- `2`: invalid input, signature configuration or file operation;
- `3`: `--require-eligible` was used and the review was not
  `eligible_for_operator_review`.

Exit code `0` means only that evaluation executed correctly. It does not mean
that quality passed.

## Invariants

1. Duplicate JSON keys are rejected.
2. Unknown and missing fields are rejected.
3. Every manifest case has exactly one observation.
4. Replay compares ordered artifact sequences.
5. Unknown denominators remain `None` through PR-RDR-09 metrics.
6. Canonical JSON uses UTF-8, sorted keys and compact separators.
7. Bundle and signature IDs are content-addressed.
8. Output replacement is atomic on the target filesystem.
9. Signature keys are never accepted as CLI values or written to artifacts.
10. Promotion review always keeps `operator_go_required=true`.
11. Promotion review always keeps `live_integration_authorized=false`.

## Still required for production evidence

PR-RDR-10 provides the runner, not the evidence. The following remain outside
this PR:

- licensed or otherwise approved real-document corpus;
- independent human labels and adjudication records;
- an adapter that executes Reader Core in an isolated benchmark environment;
- repeated runs across pinned hardware/model configurations;
- calibrated thresholds based on measured distributions;
- public-key or hardware-backed signing;
- Operator review;
- shadow integration, canary rollout and live authorization.
