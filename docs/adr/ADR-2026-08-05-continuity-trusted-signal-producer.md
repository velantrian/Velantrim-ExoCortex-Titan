# ADR-2026-08-05: Trusted Continuity Signal Producer

- **Status:** PROPOSED FOR SHADOW-ONLY EVALUATION
- **Scope:** `core.continuity.observations`, `core.continuity.signal_producer`
- **Date:** 2026-08-05
- **Runtime activation:** forbidden by this ADR

## Context

R4 introduced `ContinuityComputeSignals` and
`assess_compute_with_continuity()` as a shadow-only assessment layered over
Titan's unchanged public compute-routing contract. R5A and R5B preserved that
boundary, but no trusted producer existed: callers could only construct the
signals manually.

This ADR authorizes one deterministic and independently testable producer.
It does not authorize runtime wiring, persistence, Canon writes, tool use, or
user-visible behavior.

## Decision

```text
ContinuitySignalObservation
      │
      ▼
produce_continuity_compute_signals(observations, policy=...)
      │
      ▼
ContinuitySignalProductionResult
  ├── signals: ContinuityComputeSignals
  ├── provenance: one record per signal dimension
  ├── rejected_observations: reason-coded
  └── result_hash: deterministic content identity
```

The following contracts remain unchanged:

- `ComputePath`;
- `ComputeDecision`;
- `decide_compute_path()`;
- `ContinuityComputeSignals`;
- `assess_compute_with_continuity()`.

## Public policy-input contract

`ContinuitySignalPolicy.create()` accepts `Iterable[str]` for
`trusted_producers` and `allowed_source_types`.

Accepted examples include list, tuple, set, frozenset, and a one-shot
generator. Values are consumed once and normalized to `frozenset`.

`str` and `bytes` are explicitly rejected: although iterable, they represent
one malformed identifier collection rather than a collection of identifiers.
Empty collections and non-string elements also fail closed.

## Aggregation rules

### Warning and safety booleans

The following fields use trusted-OR semantics:

- `context_degraded`;
- `important_claim`;
- `requires_current_state`.

One applicable trusted observation asserting `True` is sufficient. Lack of a
second producer must not erase a trusted degradation, importance, or
current-state warning.

False-only or absent trusted observations leave the output `False`.

### Positive availability claim

`continuity_available=True` is a positive capability claim and remains gated
by `policy.minimum_confirmations` distinct trusted producer identities.
Multiple observations from one producer cannot manufacture confirmation.

Trusted positive and negative availability observations together resolve to
`False` and emit `continuity_available_conflict`.

### Other fields

- `context_freshness` and `sensitivity`: most-severe trusted value wins;
- `active_contradictions`: unique scopes are counted and capped by policy;
- `evidence_coverage`: covered unique scopes divided by total unique scopes;
- zero observations at all preserve the existing off-state coverage default
  of `1.0`;
- non-empty input with no trusted evidence observations yields `0.0`;
- conflicting evidence for one scope does not count as covered.

## Trust and rejection boundary

An observation contributes only when:

- its schema version is supported;
- its producer is allowlisted;
- its source type is allowed;
- confidence meets policy;
- evidence references exist when required;
- a scope exists for scope-bearing signal types.

Rejected observations are returned with reason codes and cannot affect the
aggregated signals.

## Isolation boundary

This PR deliberately does not bridge to:

- `core.evidence`;
- `core.confidence`;
- `core.contradiction_registry`;
- `core.provenance_chain`.

That unification requires a separate compatibility audit and ADR.

## Authority boundary

The producer adds no:

- startup registration, worker, route, scheduler, or daemon;
- database schema, durable queue, or persistence;
- network, clock, environment, or global mutable-state read;
- `/query`, orchestration, retrieval, tool-execution, or Canon wiring;
- answer, action, tool, execution, final-decision, or write authority.

A caller may compose the returned signals into an existing shadow input. This
ADR does not authorize or implement that caller.

## Validation gates

Before merge, the exact final head must pass:

- Ruff;
- blocking mypy;
- focused Continuity tests;
- full Titan CI;
- Docker hardening;
- permutation and duplicate invariance;
- iterable-input regression coverage;
- one-trusted-warning preservation for all three warning booleans;
- distinct-producer availability confirmation;
- fail-conservative availability conflict;
- authority-field serialization scan;
- independent final-head review.

## Consequences

The PR provides a typed trusted producer while keeping Continuity shadow-only.
It does not prove that upstream observations are truthful, does not activate
runtime behavior, and does not resolve evidence/provenance unification.
