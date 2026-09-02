# F3 Continuity admission stop-basis probe — 2026-09-02

```text
Status: PROPOSED BOUNDED RESEARCH PROBE
Implementation change: NONE
Runtime wiring change: NONE
Authority change: NONE
Production authorization: NONE
```

## Question

Can one existing Titan owner-local admission path produce the same outward no-admission result while preserving materially different stop bases and different release conditions?

Owner path:

`core/continuity/admission_evaluator.py::evaluate_continuity_admission`

## Controlled existing bases

The bounded test drives three existing rejection conditions through the same evaluator:

1. `current_authorization_not_active`
2. `confidence_below_minimum`
3. `draft_stale`

All three are expected to produce the same outward admission consequence for the controlled single draft:

```text
admitted_draft_ids = ()
rejected_drafts = one item
no_runtime_authority = True
```

while preserving distinct existing `reason_code` values.

## Release-condition observation

The probe then changes only the condition named by each existing rejection reason:

- current authorization becomes ACTIVE;
- draft confidence rises above the existing rule minimum;
- draft timestamp moves inside the existing maximum age window.

Each controlled case is expected to become admitted under the same evaluator path.

This is bounded evidence for:

```text
SAME OUTWARD NO-ADMISSION
!=
SAME MATERIAL STOP BASIS

AND

AUTHORITY STOP
!=
EVIDENCE-QUALITY STOP
!=
DRAFT-FRESHNESS STOP
```

with distinct existing release conditions on this one path.

## Strict semantic ceiling

This probe does NOT establish:

- full CLOS F3 coverage;
- task-sufficiency stopping;
- deadline/resource-exhaustion stopping;
- irreducible uncertainty;
- universal authority semantics outside this admission path;
- automatic retry/reopen policy;
- action authorization;
- production wiring;
- a universal StopReason/StopReceipt ontology.

In particular:

```text
DRAFT_STALE
!=
DEADLINE EXHAUSTED
!=
RESOURCE EXHAUSTED

ADMITTED DRAFT
!=
RUNTIME AUTHORITY
!=
ACTION AUTHORIZATION
```

The existing evaluator itself reports `no_runtime_authority = True`; the probe must preserve that ceiling.

## Disposition

Before exact-head CI:

`PROPOSED BOUNDED PROBE`

If exact-head CI passes:

```text
CONTINUITY ADMISSION BASIS PRESERVATION = OBSERVED IN BOUNDED TEST
AUTHORITY / QUALITY / FRESHNESS DISTINCTIONS = OBSERVED
FULL F3 = NOT_ESTABLISHED
F3 ARCHITECTURAL GAP = NOT_ESTABLISHED
NEW PRIMITIVE = NOT_JUSTIFIED
```

If the test fails, classify only the localized test/evaluator mismatch. Do not create a new primitive or owner automatically.

## Documentation impact

`GITHUB_ONLY`

This branch adds test/research evidence about existing behavior only and does not change architecture, ownership, runtime, authority, roadmap, or production posture.