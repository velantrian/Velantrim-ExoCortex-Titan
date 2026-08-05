# 🧪 Continuity R5A Recovery Hand-off

**Date:** 2026-08-05  
**PR:** #205  
**Base:** `main@529d8b6b182b1a548d27558173f0aca473bcc400`  
**Initial code head:** `574bf46646c84dc50aacb40d5c86324fe8b8396f`  
**Status:** `DRAFT / PRE-MERGE / SHADOW ONLY / NOT WIRED`

## Scope

R5A independently rebuilds historical #145/#146 on current R1–R4:

- deterministic shadow snapshots;
- baseline/replay comparison;
- zero-tolerance hard-gate counters;
- explicit private-audience Advisory signals;
- deterministic low-risk Advisory candidate selection;
- immutable candidates, receipts and result identities.

The complete orchestration runner remains R5B.

## Replay boundary

```text
WorkingMemoryPlan + ContextPack + final ComputeDecision
→ ShadowRunSnapshot
→ ReplayEvaluationReport
```

Zero tolerance:

- privacy leakage;
- inference-as-fact;
- missing provenance;
- budget overflow;
- query-time Canon write;
- replay divergence;
- silent overwrite.

R4 integration uses `ContinuityComputeAssessment.decision`; R5A never executes or wires it.

## Advisory boundary

A candidate requires passed hard gates, private audience, explicit typed signal, exact actionable projection, explicit permission, basis refs and shadow-only mode.

Deterministic priority:

```text
priority change → blocker → open loop → goal
```

Allowed candidate dispositions:

- `ASK_CONFIRMATION`;
- `REMIND`;
- `DEFER` when hard gates fail;
- `SILENCE` otherwise.

Advisory `DEFER` is not a compute path.

## Historical #146 correction

The historical final GitHub run failed mypy because one local variable was inferred as non-optional and then assigned an optional candidate. R5A v2 uses explicit optional control flow and includes a regression test where a non-actionable higher-priority signal is skipped and a lower-priority actionable signal is selected.

## Authority boundary

No runtime, query, startup, worker, raw-text inference, reminder delivery, answer modification, persistence, Canon/ESM/TruthGate mutation, tools, actions or feature activation.

## Validation checklist

- [x] initial focused Continuity gate green
- [ ] final-head Continuity gate green
- [ ] final-head full Titan CI green
- [ ] final-head Docker hardening green
- [ ] independent final-head review complete
- [ ] Notion final-head checkpoint synchronized
- [ ] final merge SHA recorded
- [ ] historical #145/#146 closed after merge

## Remaining limitations

- explicit external-effect counters are caller supplied;
- signals need a trusted producer and policy owner;
- proposed text is inspectable shadow data only;
- no delivery, anti-spam, localization, scheduling, cancellation or consent runtime;
- R5B complete disabled runner remains separate.
