# ADR-2026-08-05: Trusted Continuity Signal Producer

- **Status:** PROPOSED FOR SHADOW-ONLY EVALUATION
- **Scope:** `core.continuity.observations`, `core.continuity.signal_producer`
- **Date:** 2026-08-05
- **Runtime activation:** forbidden by this ADR

## Context

R4 introduced `ContinuityComputeSignals` and `assess_compute_with_continuity()`
as a shadow-only assessment on top of the unchanged `decide_compute_path()`.
Every layer since R4 — R4 itself, R5A, and R5B — restates the same open risk:
there is no trusted producer for `ContinuityComputeSignals`. Today the only
way to obtain a `ContinuityComputeSignals` value is to construct one by hand;
`CompleteShadowRunInput.compute_signals` in R5B defaults to the all-neutral,
no-op instance and is otherwise a pure pass-through with no derivation logic.
`docs/ai/CURRENT_STATE.md` lists "trusted and authenticated producers for
events, assertions, attestations, open loops, compute signals and safety
observations" first among what is required before any live activation.

## Decision

Add one deterministic, policy-driven producer:

```text
ContinuitySignalObservation (typed, provenance-carrying, content-addressed)
      │
      ▼
produce_continuity_compute_signals(observations, policy=ContinuitySignalPolicy)
      │
      ▼
ContinuitySignalProductionResult
  ├── signals: ContinuityComputeSignals   (unchanged R4 contract)
  ├── provenance: one entry per signal dimension
  ├── rejected_observations: reason-coded
  └── result_hash: content-addressed over the whole result
```

`ContinuityComputeSignals`, `assess_compute_with_continuity()`,
`ComputeDecision`, `ComputePath`, and `decide_compute_path()` are unchanged.
The producer's only contract with the rest of Titan is that its `.signals`
field is assignable wherever a `ContinuityComputeSignals` is already
accepted today — the caller decides whether and how to do that; the producer
performs no wiring itself.

## Isolation boundary

This PR deliberately does not import or bridge to `core.evidence`,
`core.confidence`, `core.contradiction_registry`, or `core.provenance_chain`.
A trusted, deterministic, independently testable producer is this PR's whole
scope; unifying Titan's evidence/confidence/provenance primitives is a
separate, larger decision this PR does not make. The producer's local
confidence/evidence/provenance notions are a scope choice, not an accident,
and are not declared permanent architecture — a future bridge (or an explicit
decision to keep them separate long-term) belongs to its own audit,
compatibility matrix, and ADR.

## Aggregation rules

Each of the 8 `ContinuityComputeSignals` fields has one explicit, documented
rule (see `core/continuity/signal_producer.py` module docstring and function
docstrings for the authoritative version):

- `context_degraded`, `important_claim`, `requires_current_state`: `True`
  only once **distinct trusted producer identities** asserting `True` reach
  `policy.minimum_confirmations`. Counting distinct producers, not raw
  observation count, means one producer flooding duplicate observations can
  never single-handedly cross a threshold greater than 1.
- `continuity_available`: same confirmation rule, but a trusted `True` and a
  trusted `False` observed together is a conflict resolved to `False`
  (fail-conservative) and surfaced via the `continuity_available_conflict`
  reason code — never silently averaged or majority-voted.
- `context_freshness`, `sensitivity`: the most severe trusted value wins, by
  an explicit priority table derived from `core/compute_controller.py`'s own
  downstream handling (`CRITICAL_STALE`/`STALE` trigger rebuild logic;
  `HIGH`/`CRITICAL` sensitivity trigger verification under low evidence).
  Absent any trusted observation, the result is the same default the
  `ContinuityComputeSignals` dataclass already uses (`UNKNOWN`, `LOW`).
- `active_contradictions`: a count, deduplicated by a caller-supplied
  content/semantic `scope` — a duplicate report of the same contradiction
  never increments the count twice — and capped by
  `policy.max_contradiction_count`.
- `evidence_coverage`: `covered_required_items / total_required_items` over
  unique `scope`s, with two distinct empty cases resolved differently and
  intentionally:
  - **zero observations at all** → `1.0`, matching the pre-existing
    `ContinuityComputeSignals()` off-state default;
  - **some observations, but none about evidence** → `0.0`, fail-closed.
  A naive `covered / total if total else 1.0` would collapse both cases into
  the permissive answer; this producer treats that collapse as the exact
  failure mode to avoid. Conflicting `True`/`False` reports for the same
  `scope` do not count as covered.

## Trust and rejection boundary

An observation is used only if: its `schema_version` matches, its `producer`
is in `policy.trusted_producers`, its `source_type` is in
`policy.allowed_source_types`, its `confidence` clears
`policy.minimum_confidence`, it carries evidence references when
`policy.require_evidence_refs` is set, and it carries a non-empty `scope`
when its signal type requires one. Confidence-threshold and trust checks live
in the producer, against a caller-supplied policy — not hardcoded into the
observation model itself, so the same raw observation can be re-evaluated
under a different policy without being reconstructed. Every rejection is
reported in `rejected_observations` with a reason code; one malformed or
untrusted observation never blocks the rest of a batch, and never raises.

## Authority boundary

This producer adds no:

- startup registration, server route, worker, scheduler or daemon;
- persistence, database schema or durable queue;
- network, clock, environment, or global mutable state read;
- wiring into `/query`, orchestration, tool execution, retrieval, or Canon;
- new `ComputePath` value or change to `decide_compute_path()`'s signature;
- change to `ContinuityComputeSignals` or `assess_compute_with_continuity()`;
- field resembling `answer`, `action`, `tool`, `execute`, `canon_write`,
  `retrieval_write`, `final_decision`, or `runtime_override` anywhere in its
  observation, policy, provenance, or result models.

A caller may pass `ContinuitySignalProductionResult.signals` into
`assess_compute_with_continuity()` or into
`CompleteShadowRunInput.compute_signals` as a pure composition step. This PR
does not perform that wiring itself and does not derive observations from
`StateReconciliationResult`, `GoalProjectionResult`, or
`OpenLoopProjectionResult` — that integration is a separate, later decision.

## Rejected alternatives

### Bake a fixed confidence threshold into the observation model

Rejected. It would couple one observation permanently to one policy and make
it impossible to re-evaluate the same raw observation under a different,
explicitly supplied policy.

### Reuse `core.evidence`/`core.confidence`/`core.contradiction_registry` now

Rejected for this PR; see Isolation boundary above.

### Derive observations automatically from existing R5A/R5B projections

Rejected for this PR. That is real runtime wiring, not pure composition, and
is explicitly out of scope until a separate ADR authorizes it.

## Validation

Required before merge:

- `ruff check core/continuity core/compute_controller.py
  tests/test_continuity*.py`;
- `mypy core/continuity core/compute_controller.py --show-error-codes`;
- `pytest tests/test_continuity*.py` (271 passed at PR head, including all
  pre-existing R1–R5B tests unchanged);
- permutation and duplicate-observation invariance of the producer's
  `result_hash`;
- one malicious/duplicating trusted producer cannot manufacture confirmations
  by itself;
- no authority-bearing key anywhere in `ContinuitySignalObservation`,
  `ContinuitySignalPolicy`, or `ContinuitySignalProductionResult` serialized
  output;
- independent final-head review.

## Consequences

This closes the specific, repeatedly-restated "no trusted producer" gap as an
isolated, independently testable substrate component. It does not activate
continuity, does not decide who owns runtime activation, and does not resolve
the evidence/confidence/provenance unification question left open by the
Isolation boundary above — both remain separate, later decisions.
