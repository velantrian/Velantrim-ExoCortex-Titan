# PR-RDR-24 — Signed local benchmark artifact retention

## Status

Local deterministic operator tooling only.

Boundary:

`VERIFIED_EVIDENCE_ONLY / EXACT_ARTIFACT_COVERAGE / LOCAL_REGULAR_FILES / SIGNED_RETENTION_MANIFEST / NO_OPERATOR_GO / NO_LIVE_AUTHORITY`

## Purpose

RDR-20 receipts name replay and execution artifacts. RDR-21 preserves every
artifact ID inside signed benchmark evidence, and RDR-23 proves that the bundle,
signature, evidence indexes, report, and review are internally consistent.

An artifact ID alone does not prove that backing bytes still exist. RDR-24 closes
that local retention gap:

```text
RDR-23 verified signed evidence
        |
        | exact signed artifact-ID set
        v
canonical local source spec
        |
        | one safe relative path per artifact ID
        v
regular-file SHA-256 and byte-size verification
        |
        v
signed retention manifest
        |
        v
repeatable backing-file verification receipt
```

The retention manifest contains metadata only. It never embeds artifact bytes or
HMAC secrets.

## Verified evidence boundary

Retention starts only after the RDR-23 benchmark artifact set has been verified.
`extract_verified_evidence_artifact_index(...)`:

- requires a typed RDR-23 verification receipt;
- re-reads the canonical signed-evidence file;
- requires its complete-file SHA-256 to equal the verification receipt;
- requires evidence, bundle, signature, review decision, Operator GO, and live
  authorization fields to match the receipt;
- extracts the exact signed `artifact_ids` set;
- produces a self-verifying artifact index.

If the evidence file changes after RDR-23 verification, retention stops.

## Source specification

The operator supplies a canonical source specification containing, for every
signed artifact ID:

- one normalized relative POSIX path;
- media type;
- retention class:
  - `benchmark_output`;
  - `pipeline_trace`;
  - `measurement`;
  - `replay`;
  - `other`.

The specification must exactly cover the signed artifact-ID set. Missing and
extra entries are both errors. Artifact IDs and relative paths must be unique.

The source spec deliberately does not accept precomputed hashes. The builder
computes hashes from the local files itself.

## Path and file safety

Only files below one explicit local root are accepted.

The implementation rejects:

- absolute paths;
- backslashes;
- empty, dot, or parent path segments;
- non-normalized relative paths;
- a symlink artifact root;
- symlinks in any artifact path component;
- paths resolving outside the root;
- missing or inaccessible files;
- directories, sockets, devices, FIFOs, and other non-regular files.

Files are opened read-only, with `O_NOFOLLOW` where supported. SHA-256 is
computed incrementally. The file descriptor's device, inode, size, and
nanosecond modification time are compared before and after hashing; a file that
changes while being read is rejected.

## Resource bounds

The builder and verifier enforce explicit bounds:

- maximum bytes per artifact;
- maximum bytes across the complete manifest.

Defaults are conservative repository-side limits and are operator-overridable by
CLI flags. A manifest exceeding the verifier's configured total limit is
rejected before files are read.

## Retention manifest

For every artifact the manifest records:

- artifact ID;
- normalized relative path;
- media type;
- retention class;
- SHA-256 digest;
- byte size;
- content-addressed record ID.

The manifest also binds:

- signed evidence ID;
- RDR-23 evidence verification ID;
- benchmark bundle and signature IDs;
- full signed-evidence file SHA-256;
- source-spec ID;
- verified artifact-index ID;
- exact total byte size;
- benchmark review decision;
- immutable authority boundaries.

Artifacts use canonical artifact-ID order. The manifest has its own
content-addressed ID.

## Detached retention signature

The manifest is authenticated with detached HMAC-SHA256. The signature records:

- manifest ID;
- non-secret key ID;
- manifest SHA-256;
- HMAC digest;
- algorithm and schema;
- content-addressed signature ID.

The secret is caller-supplied bytes of at least 32 bytes and is never serialized.

## Repeatable verification

`ReaderBenchmarkArtifactRetentionVerifier` first authenticates the manifest,
then securely opens and hashes every referenced local file again. It requires
exact size and digest equality and exact total-byte equality.

Successful verification produces a content-addressed receipt containing:

- retention manifest and signature IDs;
- evidence and RDR-23 verification IDs;
- every verified record ID;
- verified file count and total bytes;
- benchmark review decision;
- unchanged Operator GO and live-authorization boundaries.

A new receipt proves that the named bytes were present and matched at that
verification run. It is not a perpetual storage guarantee.

## Build CLI

```bash
python scripts/retain_reader_benchmark_artifacts.py \
  --bundle /secure/reader/benchmark-bundle.json \
  --benchmark-signature /secure/reader/benchmark-signature.json \
  --evidence /secure/reader/signed-evidence.json \
  --artifact-root /secure/reader/artifacts \
  --spec /secure/reader/artifact-retention-spec.json \
  --manifest-output /secure/reader/artifact-retention-manifest.json \
  --retention-signature-output /secure/reader/artifact-retention-signature.json \
  --verification-output /secure/reader/artifact-retention-verification.json \
  --hmac-key-env READER_BENCHMARK_HMAC_KEY \
  --key-id reader-retention-key-v1
```

The command:

1. independently repeats RDR-23 benchmark evidence verification;
2. derives the exact signed artifact-ID set;
3. strictly loads the canonical source spec;
4. hashes all safe local files;
5. creates and signs the retention manifest;
6. immediately re-verifies the signature and backing files;
7. writes canonical manifest, signature, and verification receipt files.

Output paths must be distinct and absent. Partially written outputs are removed
if a later write fails.

## Later verification CLI

```bash
python scripts/verify_reader_benchmark_artifact_retention.py \
  --artifact-root /secure/reader/artifacts \
  --manifest /secure/reader/artifact-retention-manifest.json \
  --signature /secure/reader/artifact-retention-signature.json \
  --hmac-key-env READER_BENCHMARK_HMAC_KEY \
  --verification-output /secure/reader/artifact-retention-recheck.json
```

This command is read-only with respect to the manifest, signature, and artifact
files. It may write one new verification receipt, but never overwrites an
existing receipt.

## Authority boundary

Every artifact index, manifest, and verification receipt requires:

```text
operator_go_required = true
live_integration_authorized = false
```

Therefore:

```text
backing bytes retained != semantic correctness
semantic correctness != thresholds passed
thresholds passed != Operator GO
Operator GO != automatic live integration
```

## Non-goals

RDR-24 does not:

- decide whether artifact contents are intellectually correct;
- parse or execute artifact contents;
- prove who originally created the files;
- provide encrypted storage;
- provide replication, backup, retention-period, or deletion-policy guarantees;
- defeat a privileged operating-system or storage administrator;
- upload artifacts or use a remote object store;
- execute Reader Core;
- retry benchmark cases;
- calibrate thresholds;
- record Operator GO;
- authorize shadow, canary, or live integration;
- write memory or Canon;
- grant graph, policy, tool, TruthGate, or Write Gate authority.

## Tests

Regression coverage includes:

- exact artifact-ID coverage;
- deterministic manifest and verification receipts;
- signature verification and wrong-key rejection;
- modified-file rejection;
- path traversal rejection;
- symlink rejection;
- per-file size limits;
- strict canonical source-spec, manifest, and signature loading;
- forged ID and duplicate-key rejection;
- end-to-end build and later-verification CLIs;
- output overwrite protection;
- secret non-disclosure;
- immutable Operator GO and live-authorization boundaries.

## Remaining external work

RDR-24 proves local byte availability at explicit verification times. Issue #120
still requires the external evidence the repository cannot manufacture:
rights-cleared representative documents, independent human annotation and
adjudication, a reviewed production pipeline, real benchmark execution,
threshold calibration, durable storage policy, shadow burn-in, and explicit
Operator GO.
