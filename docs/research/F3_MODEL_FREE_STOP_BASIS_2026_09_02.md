# F3 ModelFreeCore stop-basis probe — 2026-09-02

```text
Status: BOUNDED RESEARCH EVIDENCE
Implementation change: NONE
Runtime wiring change: NONE
Authority change: NONE
Production authorization: NONE
```

## Question

Can one existing Titan owner path produce the same outward STOP-like result for materially different failure bases without collapsing those bases into one undifferentiated `sufficient=true` state?

This is a bounded probe for CLOS F3 — Same Stop / Different Reason. It is not a universal STOP contract and does not import CLOS authority into Titan.

## Exact baseline

`velantrian/Velantrim-ExoCortex-Titan@1996086ef12ea5922f89262177258070a361e9dc`

Owner path under observation:

`core/model_free_core.py::ModelFreeCore.query`

## Controlled cases

The test `tests/test_f3_same_stop_different_reason_model_free.py` drives four existing failure bases through the same `ModelFreeCore.query()` path:

1. `no_local_lexical_retrieval_results`;
2. `guardian_rejected`;
3. `truth_gate_rejected`;
4. `causal_graph_read_failed`.

All four are expected to produce the same outward bounded answer:

```text
Недостаточно подтверждённых локальных данных.
```

and:

```text
insufficient_evidence = true
```

while preserving distinct existing `reason_code` values.

The path also exposes existing gate-state differences across the cases through `guardian_passed` and `truth_gate_passed`.

## What this can establish

If the exact-head test passes:

```text
SAME OUTWARD INSUFFICIENT ANSWER
!=
SAME MATERIAL FAILURE BASIS
```

for this one bounded existing owner path.

It would show that Titan already preserves more than a single generic STOP label on this path.

## What this does not establish

This probe does **not** establish:

- task-sufficiency stopping;
- deadline stopping;
- resource-budget stopping as a dedicated semantic category;
- authority-prohibition semantics as a universal STOP category;
- reopen conditions;
- durable stop receipts;
- cross-project preservation;
- action authorization consequences;
- a universal `StopReason` ontology;
- F3 end-to-end completion.

In particular:

```text
REASON BASIS PRESERVED
!=
REOPEN SEMANTICS PRESERVED
```

Reopen semantics are not represented by this `L2Result` contract and are therefore `NOT_OBSERVABLE` in this probe rather than failed.

## Disposition

Before exact-head test evidence:

`PROPOSED BOUNDED PROBE`

If exact-head test passes:

```text
MODEL-FREE BASIS PRESERVATION = OBSERVED IN BOUNDED TEST
F3 FULL PASS = NOT_ESTABLISHED
F3 ARCHITECTURAL GAP = NOT_ESTABLISHED
NEW PRIMITIVE = NOT_JUSTIFIED
```

If the test fails because the four bases collapse:

`LOCALIZED PRESERVATION GAP`

That result still would not automatically justify a new primitive or owner.

## Documentation impact

`GITHUB_ONLY`

Reason: this branch adds test/research evidence about existing behavior. It does not change architecture, runtime wiring, ownership, authority, roadmap, or production posture; no Notion synchronization is required for the branch itself.
