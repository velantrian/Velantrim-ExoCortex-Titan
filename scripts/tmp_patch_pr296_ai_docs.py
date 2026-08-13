from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exact anchor once, found {count}")
    p.write_text(text.replace(old, new, 1))


component_old = '''## 9. Current continuation boundary

Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is
CLOSED_COMPLETED at current main `c80c8d47588de3d2607c7e1b10aa1677eb84383f` after merged #293, green post-merge evidence,
and a fresh current-main residual inventory with `REAL_GAP=0`. Merged #288/#289,
#290/#291 and #292/#293 are current-main Truth Foundation convergence, not pending gates.
Open #53 is a downstream architecture workstream that depends on #50; this closure does
not itself authorize its implementation. No Phase II, 13/12, ADAO, ARM-04, wider runtime
activation, production rollout or standing Operator GO follows from #50 closure.
'''
component_new = '''## 9. Current continuation boundary

Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is
CLOSED_COMPLETED; the protected documentation-truth baseline entering this bounded block
is `main@2699963547a42c4fbcd6b0273125c890a038654b` with the fresh Truth Foundation
residual inventory at `REAL_GAP=0`.

Current bounded work is child issue #295 / draft PR #296 under open architecture issue
#53: Phase 1 explicit `ModelFreeCore`. The exact pre-documentation code head
`4d40229ce746a164534682b3443f9de6e729b6da` passed Full CI `31669587920` and Docker
`31669587884`, but remains REVIEW-STAGE / NOT MAIN until final-head gates, review/thread
reconciliation and protected merge complete. The candidate composes the existing
`QueryRouter` + lexical-only retrieval + FactsPack + Guardian + TruthGate + optional
read-only CausalGraph into typed `L2Query`/`L2Result` evidence output; it does not change
the general pipeline default or add runtime/server wiring.

Issue #53 remains OPEN for later bounded phases. No CapabilityRegistry, new vector
architecture, ADAO, LLM role enablement, remote provider path, schema v8, Continuity
13/12, runtime activation, standing Operator GO, runtime authority or production
authority follows from Phase 1.
'''
replace_exact('docs/ai/COMPONENT_MAP.md', component_old, component_new)

risk_anchor = '''## Operational residuals
'''
risk_insert = '''## Review-stage boundary — ModelFreeCore Phase 1 is not runtime wiring

Issue #295 / draft PR #296 is the current bounded implementation slice under open #53.
The exact pre-documentation code head `4d40229ce746a164534682b3443f9de6e729b6da`
passed Full CI `31669587920` and Docker `31669587884`. A full-suite-only test isolation
failure on the earlier head was reproduced by diagnostic run `31669157724` and corrected
without changing production semantics; the accepted code head then passed both full-suite
and coverage gates.

The candidate is still REVIEW-STAGE / NOT MAIN. It is a typed read-only facade over
existing local primitives and deliberately selects lexical retrieval. It does not prove
runtime routing, default-route replacement, CapabilityRegistry, embedding/vector
architecture, ADAO, LLM execution, network/provider access or production readiness.
Optional capability absence must not block a model-free result, and query execution must
not mutate Canon, ESM state or causal relations.

## Operational residuals
'''
replace_exact('docs/ai/KNOWN_RISKS.md', risk_anchor, risk_insert)

work_top = '''---

## 2026-08-12 — P0 smart-KB convergence + Truth Foundation #50 completed
'''
work_new_top = '''---

## 2026-08-13 — #53 Phase 1 ModelFreeCore · REVIEW-STAGE / NOT MAIN

```text
Parent architecture:            #53 · OPEN
Tracking issue:                 #295 · OPEN
Implementation PR:              #296 · DRAFT / REVIEW-STAGE
Authoritative base main:        2699963547a42c4fbcd6b0273125c890a038654b
Clean pre-doc code head:        4d40229ce746a164534682b3443f9de6e729b6da
Exact-head Full CI:             31669587920 · SUCCESS
Exact-head Docker:              31669587884 · SUCCESS
Diagnostic first-failure run:   31669157724 · reproduced full-suite isolation leak
Documentation impact:           GITHUB_AND_NOTION
Notion synchronization:         REVIEW_PENDING until final docs head is green
Continuity:                     12/12 = 100% · unchanged
Schema:                         v7 · unchanged
Runtime currently enabled:      false · unchanged
Operator GO:                    false · unchanged
Runtime authority:              false · unchanged
Production authority:           false · unchanged
```

Phase 1 composes existing deterministic/read-only primitives behind typed
`L2Query`/`L2Result` contracts. It explicitly selects the existing lexical path and keeps
Dense/RRF/reranker/LLM/provider/network paths out of this facade. FactsPack, Guardian and
TruthGate remain the evidence policy; CausalGraph is read-only. No server/default-route
wiring or new mutation authority is introduced.

The first PR head passed focused tests but failed full-suite because the new acceptance
test retained `core.*` module objects across repository tests that deliberately purge and
re-import `sys.modules`. Diagnostic run `31669157724` proved the exact failure after 2705
passes. The fix changed only test isolation: reload-sensitive modules are resolved at test
execution time. Production semantics remained unchanged, and the clean replacement code
head passed full pytest plus coverage and Docker.

AI truth docs are being reconciled after that green code head. They will change the final
PR head, so Full CI + Docker must run again before Notion REVIEW evidence, readiness or
merge. PR #296 is explicitly NOT MAIN at this checkpoint.

---

## 2026-08-12 — P0 smart-KB convergence + Truth Foundation #50 completed
'''
replace_exact('docs/ai/WORK_LOG.md', work_top, work_new_top)

work_tail = '''## Stable continuation boundary

Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 is CLOSED_COMPLETED on current main `c80c8d47588de3d2607c7e1b10aa1677eb84383f` after merged
#293, green post-merge evidence and a fresh residual inventory with `REAL_GAP=0`. Merged
#288/#289, #290/#291 and #292/#293 are current-main Truth Foundation history. Issue #249
stays separate. Open #53 is downstream architecture, not an automatic next implementation
authorization. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator
GO, runtime authority or production authority follows from this closure.
'''
work_new_tail = '''## Stable continuation boundary

Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 is CLOSED_COMPLETED; authoritative base main for the
current bounded block is `2699963547a42c4fbcd6b0273125c890a038654b` and its fresh
Truth Foundation residual inventory is `REAL_GAP=0`. Merged #288/#289, #290/#291 and
#292/#293 remain current-main Truth Foundation history. Issue #249 stays separate.

Open #53 now has one explicitly bounded Phase 1 implementation child: #295 / draft PR
#296. Its pre-documentation code head passed Full CI and Docker, but the work remains
REVIEW-STAGE / NOT MAIN until final-head gates, Notion REVIEW evidence, readiness,
thread reconciliation and protected merge. Later #53 phases remain unimplemented and
unauthorized by this slice. No schema v8, Phase II, ADAO, ARM-04, runtime activation,
standing Operator GO, runtime authority or production authority follows from Phase 1.
'''
replace_exact('docs/ai/WORK_LOG.md', work_tail, work_new_tail)
