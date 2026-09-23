# ADR — TruthGate counts only typed structural evidence references

- **Status:** Proposed / bounded enforcement repair
- **Date:** 2026-09-23
- **Scope:** `core/truth_gate.py::_count_evidence` only
- **Baseline:** `main@54c975a3b19ebf5526d4a95416aeb1e12c92e1d1`

## Context

The live TruthGate counts legacy `metadata.evidence_refs` string tokens and
returns at least one evidence item even for a missing/empty list. That violates
the repository's established boundary that a reference token is not itself
evidence and allows EXPLORATION to satisfy its evidence threshold with zero
actual references.

Titan already contains the strict local `EvidenceReference v1` parser. It was
previously contract-only and unwired.

## Decision

For TruthGate cardinality only:

1. missing/non-list `evidence_refs` counts as `0`;
2. legacy strings count as `0`;
3. malformed mappings count as `0`;
4. only mappings accepted by `EvidenceReference.from_mapping()` count;
5. duplicate typed references are deduplicated by canonical reference digest;
6. existing CognitiveMode thresholds are unchanged.

## Explicit non-claims

This repair does **not** prove source authenticity, contextual independence,
registry trust, source availability, fragment truth, or claim truth. It does
not wire `EvidenceRegistry` as a new authority and does not change promotion
ownership. A typed reference is necessary for this gate's cardinality after
this repair, but typed structure alone is not sufficient evidence sovereignty.

```text
legacy token != evidence
typed structure != authenticated source
typed structure != independence
reference count != truth
```

## Rollback

Revert this commit. No schema or persisted-data migration is introduced.
