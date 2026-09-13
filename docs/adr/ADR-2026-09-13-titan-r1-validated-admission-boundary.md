# ADR — Titan R1: close ungated Validated ESM admission

- **Status:** Accepted
- **Date:** 2026-09-13
- **Scope:** local enforcement gap only (`SQLiteGraphStore` ESM helpers)
- **Classification:** `LOCAL_ENFORCEMENT_GAP` closed; `NO_ARCHITECTURAL_CHANGE`
- **Baseline:** `main` tip at branch start `54c975a3b19ebf5526d4a95416aeb1e12c92e1d1`

## Context

Architecture already requires Supported → Validated durable minting to go through
TruthGate evaluation, `validate_and_promote()`, and the CAS writer
(`_promote_to_validated_cas`), typically via PromotionGateway for external callers.

A local enforcement gap remained: `transition_esm(..., "Validated")` and the
generic ladder helpers `promote_esm_to(..., "Validated")` /
`promote_to_validated()` could still call plain `update_state` and mint
`Validated` without TruthGate + CAS. That path matched existing
`AUTHORITY_PATTERNS` in the architecture-freeze guard when the R1 diff added
calls to `transition_esm(` / `validate_and_promote(` in `core/memory.py`.

This is not a new authority surface. It closes an ungated route to the
**existing** protected admission path.

## Decision

Close the gap inside `core/memory.py` only:

1. `transition_esm(..., new_state="Validated")` raises `ValueError` before any
   `update_state` call. Generic ESM must not mint Validated.
2. `promote_esm_to(..., "Validated")` advances the ladder at most to
   `Supported`, then requests protected admission via
   `self.validate_and_promote(fact_id, by=by)` and returns
   `bool(verdict.passed)`.
3. `promote_to_validated()` remains a bool compatibility wrapper over
   `promote_esm_to(..., "Validated")`.

Validated admission remains exactly:

```text
TruthGate.evaluate
  → validate_and_promote
  → _promote_to_validated_cas
```

(PromotionGateway continues to delegate to the same store authority.)

## Non-claims / non-scope

R1 does **not**:

- introduce a new service, engine, ledger, worker, scheduler, or feature flag;
- change TruthGate thresholds, evidence policy, or CAS semantics;
- replace PromotionGateway or invent a second promotion owner;
- authorize `update_state(..., "Validated")` as a public admission path;
- redesign compound supersede, World Skills curated admission, or Ring Zero seed.

## Authority boundary

| Concern | Owner after R1 |
|---|---|
| Mint Validated | Existing `validate_and_promote` / PromotionGateway + TruthGate + CAS |
| Generic ESM ladder (non-Validated) | Existing `transition_esm` / `promote_esm_to` |
| Reject ungated Validated via ESM | New local guards in the helpers above |

## Consequences

- Weak / ineligible facts stay at Supported and yield False / raise on the
  generic helpers; eligible facts still reach Validated only through protected
  admission.
- Architecture-freeze markers in the R1 diff are covered by this concrete ADR
  (not README/template).
- Rollback: revert the `core/memory.py` guards and related test/doc adaptations;
  no schema or data migration.

## Validation

Focused suites covering tool handlers, ESM, and promotion ownership; plus
repository CI-equivalent gates (branding, hygiene, architecture freeze with
this ADR, project-state, KB graph, Ruff, mypy, targeted pytest).
