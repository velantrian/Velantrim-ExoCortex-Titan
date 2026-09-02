# F3 later-task reopen UNKNOWN release-condition probe — 2026-09-02

```text
Status: PROPOSED BOUNDED RESEARCH PROBE
Implementation change: NONE
Runtime wiring change: NONE
Authority change: NONE
Production authorization: NONE
```

## Question

Can one existing Titan owner path produce the same outward stop-like result while preserving materially different reasons and different conditions that release that stop?

Owner path:

`core/later_task_reopen.py::LaterTaskReopenPlanner.plan`

Exact baseline:

`velantrian/Velantrim-ExoCortex-Titan@5b9ec3db2f5de45bd13eccdbecbbadf484fc7a98`

## Controlled existing stop bases

The bounded test drives three existing cases through the same planner:

1. `no_later_task_claim_selection`
2. `no_unsupported_claim_signal`
3. `reopen_budget_insufficient`

All three are expected to produce the same outward planning result:

```text
disposition = UNKNOWN
targets = ()
```

while preserving distinct existing `reason_code` values.

## Release-condition observation

The probe then changes only the condition named by each existing reason:

- explicit claim selection is supplied;
- unsupported-claim signal is supplied;
- reopen budget is increased.

Each corresponding case is expected to transition to:

```text
disposition = READY
targets != ()
```

This is bounded evidence for:

```text
SAME OUTWARD UNKNOWN / NO-PLAN-NOW
!=
SAME MATERIAL STOP BASIS

AND

DIFFERENT STOP BASIS
->
DIFFERENT RELEASE CONDITION
```

on this one existing owner-local planning path.

## What this does not establish

This probe does **not** establish:

- full CLOS F3 six-case coverage;
- task-sufficiency stopping;
- deadline stopping;
- universal source-unavailable semantics;
- universal authority-prohibition semantics;
- irreducible uncertainty semantics;
- automatic reopen policy;
- scheduler or durable resume;
- action authorization;
- production wiring;
- a universal `StopReason` or `StopReceipt` ontology;
- F3 end-to-end completion.

In particular:

```text
RELEASE CONDITION OBSERVED IN PLANNER INPUTS
!=
AUTOMATIC REOPEN POLICY

READY PLAN
!=
REOPEN EXECUTED

REOPEN EXECUTED
!=
ANSWER SUPPORT
!=
DECISION AUTHORITY
```

## Disposition

Before exact-head CI:

`PROPOSED BOUNDED PROBE`

If exact-head test passes:

```text
LATER-TASK UNKNOWN BASIS PRESERVATION = OBSERVED
DISTINCT RELEASE CONDITIONS = OBSERVED IN BOUNDED PLANNER TEST
FULL F3 = NOT_ESTABLISHED
F3 ARCHITECTURAL GAP = NOT_ESTABLISHED
NEW PRIMITIVE = NOT_JUSTIFIED
```

If the test fails because the reasons or release conditions collapse, classify only the exact localized planner/test gap. Do not automatically create a new primitive or owner.

## Documentation impact

`GITHUB_ONLY`

This branch adds test/research evidence about existing behavior and does not change architecture, ownership, authority, runtime, roadmap, or production posture.
