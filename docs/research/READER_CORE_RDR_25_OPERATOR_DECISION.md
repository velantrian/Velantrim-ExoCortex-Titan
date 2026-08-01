# PR-RDR-25 — Signed operator decision, expiry, and revocation

## Status

Repository-side governance record only.

Boundary:

`VERIFIED_BENCHMARK_AND_RETENTION_ONLY / SHADOW_APPROVAL_MAXIMUM / EXPLICIT_VALIDITY_WINDOW / SIGNED_REVOCATION / NO_LIVE_AUTHORITY`

## Purpose

The Reader Core evidence chain now establishes:

- deterministic benchmark preparation and execution;
- reproducible report and promotion review;
- signed benchmark evidence;
- independent offline verification;
- signed retention and re-verification of backing artifact bytes.

Every promotion review still says:

```text
operator_go_required = true
live_integration_authorized = false
```

Before RDR-25 there was no canonical representation of what an operator decided,
which evidence was reviewed, the decision's scope and validity window, its
conditions, or a later revocation.

RDR-25 adds that missing governance record without creating deployment
authority.

## Dispositions

An operator source record chooses exactly one disposition:

- `approve_shadow_only`;
- `defer`;
- `no_go`.

`approve_shadow_only` is accepted only when the benchmark review is
`eligible_for_operator_review`. It requires explicit condition codes.

`defer` and `no_go` require explicit rationale codes and never authorize shadow
execution.

No disposition can authorize:

- live integration;
- `/query` or any query-path wiring;
- Canon writes;
- memory writes.

Those fields are permanently `false` in decision and status contracts.

## Evidence chain

A decision is built from:

1. one canonical RDR-23 benchmark verification receipt;
2. one canonical RDR-24 retention manifest;
3. one canonical RDR-24 retention verification receipt;
4. one canonical operator decision source.

The builder requires exact agreement on:

- signed evidence ID;
- benchmark verification ID;
- benchmark bundle and signature IDs;
- promotion-review decision;
- retention manifest ID;
- retained artifact record set;
- verified artifact count;
- verified total byte size;
- Operator GO and live-authorization boundaries.

A retention record for a different evidence set cannot be combined with the
benchmark receipt.

## Operator source

The canonical source contains:

- operator identifier;
- disposition;
- `decided_at_utc`;
- `valid_from_utc`;
- `valid_until_utc`;
- sorted unique rationale codes;
- sorted unique condition codes.

Times use exactly:

```text
YYYY-MM-DDTHH:MM:SSZ
```

The decision time cannot be after the start of validity, and the end is
exclusive and must be later than the start.

No system clock is consulted when creating or evaluating a decision. Every
status evaluation receives an explicit `as_of_utc` value.

## Signed decision record

The resulting content-addressed decision binds the operator source to all
verified evidence IDs and contains explicit authority booleans.

For `approve_shadow_only`:

```text
shadow_evaluation_authorized = true
live_integration_authorized = false
query_path_wiring_authorized = false
canon_write_authorized = false
memory_write_authorized = false
```

For `defer` and `no_go`, every authorization boolean is false.

The decision is authenticated with detached HMAC-SHA256. The secret must be at
least 32 bytes and is never serialized.

HMAC proves possession of the configured secret. Key custody, identity proof,
organizational delegation, and legal authority remain external responsibilities.

## Status evaluation

At one explicit UTC instant, a valid signed decision has one status:

- `not_yet_valid`;
- `active_shadow_approval`;
- `expired`;
- `revoked`;
- `non_approving`.

Only `active_shadow_approval` sets
`shadow_evaluation_authorized = true`.

The validity end is exclusive. A decision evaluated exactly at
`valid_until_utc` is expired.

## Revocation

Revocation is a separate content-addressed and signed record. It contains:

- the decision ID;
- the exact decision signature ID;
- revoking operator identifier;
- canonical revocation time;
- non-empty rationale codes.

A revocation cannot predate the original decision. A correctly authenticated
revocation affects status at and after its `revoked_at_utc`. Before that instant,
normal validity rules apply.

A revocation is not deletion: the original decision and both signatures remain
part of the audit chain.

## CLIs

### Create a decision

```bash
python scripts/create_reader_operator_decision.py \
  --benchmark-verification /secure/reader/benchmark-verification.json \
  --retention-manifest /secure/reader/retention-manifest.json \
  --retention-verification /secure/reader/retention-verification.json \
  --source /secure/reader/operator-decision-source.json \
  --decision-output /secure/reader/operator-decision.json \
  --signature-output /secure/reader/operator-decision-signature.json \
  --hmac-key-env READER_OPERATOR_HMAC_KEY \
  --key-id reader-operator-key-v1
```

### Revoke a decision

```bash
python scripts/revoke_reader_operator_decision.py \
  --decision /secure/reader/operator-decision.json \
  --decision-signature /secure/reader/operator-decision-signature.json \
  --source /secure/reader/operator-revocation-source.json \
  --revocation-output /secure/reader/operator-revocation.json \
  --signature-output /secure/reader/operator-revocation-signature.json \
  --hmac-key-env READER_OPERATOR_HMAC_KEY \
  --key-id reader-operator-revocation-key-v1
```

The revocation command authenticates the original decision before issuing the
revocation.

### Evaluate status

```bash
python scripts/evaluate_reader_operator_decision.py \
  --decision /secure/reader/operator-decision.json \
  --decision-signature /secure/reader/operator-decision-signature.json \
  --as-of-utc 2026-08-01T12:00:00Z \
  --hmac-key-env READER_OPERATOR_HMAC_KEY \
  --status-output /secure/reader/operator-status.json
```

Optional revocation and revocation-signature files must be supplied together.
`--require-active-shadow-approval` returns exit code `3` for a valid but
non-active status. Authentication or contract failures return `2`.

All commands refuse to overwrite existing outputs. Secrets are read only from a
named environment variable.

## What shadow approval means

RDR-25 records permission for a later isolated shadow-evaluation mechanism. It
does not itself provide or activate that mechanism.

An active record still cannot:

- connect Reader Core to production `/query` traffic;
- return Reader Core output to users;
- write persistent state;
- mutate Canon or memory;
- invoke tools;
- authorize a canary or live rollout.

A separate shadow runtime contract must enforce those boundaries and consume an
active status receipt explicitly.

## Fail-closed cases

Decision construction or evaluation rejects:

- shadow approval over `insufficient_evidence` or `no_go` benchmark review;
- mismatched benchmark and retention evidence;
- incomplete retention coverage;
- changed authority boundaries;
- malformed or noncanonical UTC times;
- empty approval conditions;
- empty defer/no-go rationale;
- wrong HMAC keys;
- forged content-addressed IDs;
- noncanonical JSON, duplicate keys, or unknown fields;
- a revocation for another decision or decision signature;
- a revocation preceding the original decision;
- attempts to set live, query, Canon, or memory authority.

## Non-goals

RDR-25 does not:

- identify a human beyond the supplied operator ID and external key custody;
- create organizational authorization policy;
- execute shadow traffic;
- select a model or provider;
- change benchmark thresholds;
- ignore an expired or revoked decision;
- authorize canary or live deployment;
- wire `/query`;
- write memory or Canon;
- grant graph, policy, tool, TruthGate, or Write Gate authority.

## Tests

Regression coverage includes:

- eligible shadow-only approval;
- rejection of approval over insufficient evidence;
- deterministic not-yet-valid, active, and expired status;
- defer and no-go semantics;
- evidence-chain mismatch rejection;
- permanent live/query/Canon/memory prohibitions;
- correct and incorrect HMAC keys;
- signed revocation before/after status behavior;
- strict canonical receipt and source loading;
- end-to-end create, revoke, and evaluate CLIs;
- output overwrite protection;
- secret non-disclosure.

## Remaining external work

A signed record does not manufacture approval. A real operator must review real
rights-cleared corpus results, human adjudication, retained artifacts, calibrated
thresholds, and organizational policy before creating one.

After an actual shadow-only approval, the next repository-side layer would be an
isolated shadow admission/runtime contract that consumes an active status receipt
without gaining query-path or persistent-write authority.
