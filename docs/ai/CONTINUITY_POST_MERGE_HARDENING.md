# Continuity Trusted Producer — Post-Merge Hardening

## Status

```text
FOLLOW-UP TO PR #214
SHADOW ONLY · NOT WIRED · NOT ENABLED
NO CANON / TRUTHGATE / TOOL / ACTION AUTHORITY
```

PR #214 merged the deterministic trusted producer for
`ContinuityComputeSignals`. A final independent review identified four
additional defensive-hardening requirements that are addressed in this
follow-up:

1. verify the content-addressed `observation_id` before trusting a supported
   observation;
2. reject an ID/content mismatch through the reason-coded rejection contract;
3. replace raw categorical-map `KeyError` leakage with a controlled
   `ContinuitySignalProducerError`;
4. count contradictions by unique scope while retaining provenance for every
   trusted contributing observation.

The existing `UNKNOWN_SCHEMA_VERSION` reason remains more specific and is
classified before canonical ID verification. This preserves the established
public rejection behavior while still verifying IDs for supported schemas.

## Validation boundary

The focused patch gate passed:

- Ruff;
- blocking mypy for Continuity and compute-controller surfaces;
- 108 focused Continuity tests, including new tamper and provenance
  regressions.

The follow-up PR must additionally pass the repository's complete exact-head
CI, coverage ratchet, Continuity contracts, Docker hardening and independent
final review before merge.

This hardening adds no runtime wiring, data source, persistence, feature flag,
activation, autonomous decision authority, or user-visible behavior.
