# ADR — TruthGate stops phantom evidence fallback

- **Status:** Proposed / bounded enforcement repair
- **Date:** 2026-09-23
- **Scope:** `core/truth_gate.py::_count_evidence` only
- **Review baseline:** `main@74d2a7ecf713f78698f6224f125648d0fdb3222c`

## Context

The live TruthGate legacy compatibility path returns at least one evidence item
for a missing or empty `metadata.evidence_refs` value. That creates evidence
cardinality from absence and lets EXPLORATION satisfy its minimum evidence
threshold even when the fact carries no reference token at all.

A separate Typed Evidence Reference v1 contract exists in Titan, but its accepted
ADR explicitly keeps it contract-only and unwired. Structural validity,
registry-local validation, and receipt cardinality are not authorized runtime
evidence-sufficiency signals.

## Decision

This repair changes only the phantom fallback:

1. missing `evidence_refs` counts as `0`;
2. non-list `evidence_refs` counts as `0`;
3. an empty list counts as `0`;
4. blank/whitespace-only string tokens count as `0`;
5. duplicate non-empty legacy string tokens deduplicate by exact string value;
6. distinct non-empty legacy string tokens retain the existing compatibility
   cardinality behavior;
7. CognitiveMode thresholds are unchanged.

## Explicit boundary

This is **not** a claim that a legacy string token is sufficient evidence.
The remaining legacy-token cardinality rule is compatibility debt and stays an
open evidence-admission problem.

This ADR does **not** wire `EvidenceReference`, `EvidenceRegistry`, or
`EvidenceValidationReceipt` into TruthGate. In particular:

```text
absence != evidence
reference token != evidence proof
typed structure != authenticated source
registry-local validation != evidence sufficiency
reference count != independence
evidence != truth
```

Any migration from legacy token cardinality to source-resolved or
independence-aware evidence admission requires a separate owner/policy decision,
differential tests, and explicit authorization.

## Rollback

Revert this bounded change. No schema, persistence, producer migration, or
runtime-authority change is introduced.
