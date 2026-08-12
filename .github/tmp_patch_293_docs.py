from pathlib import Path


def one(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise RuntimeError(f'{path}: anchor count={text.count(old)} for {old[:80]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def between(path, start, end, replacement):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError(f'{path}: section marker drift: {start!r} / {end!r}')
    a = text.index(start)
    b = text.index(end, a)
    p.write_text(text[:a] + replacement + text[b:], encoding='utf-8')


component = 'docs/ai/COMPONENT_MAP.md'
one(component,
'''| initial raw provenance on fact creation | existing `SQLiteGraphStore` fact-create parent transactions | REVIEW-STAGE on #290/#291 · NOT MAIN |''',
'''| initial raw provenance on fact creation | existing `SQLiteGraphStore` fact-create parent transactions | CONVERGED on merged #291 · current main `7a47f5dbb786fe267093857bf370fd03703207ac` |
| smart-KB fact create/classify/validate | existing `store_facts_batch()` + canonical ESM owner; builder orchestration only | REVIEW-STAGE on #292/#293 · NOT MAIN |''')

between(component,
'### Initial-create raw provenance residual — issue #290 / draft PR #291\n',
'## 6. Projection authority\n',
'''### Initial-create raw provenance convergence — merged #290 / #291

Protected squash merge #291 converged initial `raw_*` provenance on current main
`7a47f5dbb786fe267093857bf370fd03703207ac`. New single/batch facts and replacement-fact
creation inside `supersede_fact_cas()` verify the L0 raw parent and close matching
`l0_fact_provenance` evidence inside the owning FACT_CREATED transaction. Existing durable
pointers cannot be rebound through generic upsert, while non-raw `derived_from` remains
fact-to-fact lineage. Issue #290 is CLOSED_COMPLETED; post-merge Full CI, Docker and
aggregate evidence all passed.

### Smart-KB fact-build residual — issue #292 / draft PR #293

Fresh post-#291 current-main inventory found that `scripts/build_kb_graph.py` could bypass
canonical fact authority: `--fast-fresh` directly inserted `facts`, and build paths used
raw SQL to classify facts and drive the ESM ladder. The resulting `velantrim_kb.db` can
become the ordinary `VELANTRIM_DB_PATH`, so this is a Canon surface rather than an inert
export.

PR #293 is review-stage only. Its candidate removes raw fact DML from the builder,
declares curated World Skills rows as `WORLD_FACT / EXTERNAL` before admission, delegates
create/update to existing `store_facts_batch()` evidence semantics, and delegates
validation to `promote_to_validated()` / canonical ESM transitions. Batch classification
changes become VersionStore/AuditChain-evidenced changes with coherent L0/L1 state.
`--fast-fresh` becomes only an empty-database precondition, and incomplete ingest or
validation fails the build. Causal edges remain owned by the already-converged
`CausalGraph`. These guarantees are NOT main truth until protected merge and post-merge
verification.

''')

between(component,
'Candidate #291 review boundary:\n',
'No producer/action/reminder/notification/tool/scheduler authority is added.\n',
'''Current-main #291 guarantee:

- NEW `raw_*` facts cannot establish Canon without matching same-parent-transaction L0 provenance evidence;
- missing raw/evidence/audit failure rolls back the owning creation transaction;
- generic upsert cannot rebind existing durable raw provenance;
- non-raw fact lineage remains unchanged.

Candidate #293 review boundary:

- smart-KB builder must own no direct `INSERT INTO facts` or `UPDATE facts SET` mutation path;
- curated WSC fact admission must use the existing canonical batch owner and evidence semantics;
- ESM validation must use canonical transition ownership rather than raw SQL;
- `--fast-fresh` may require empty storage but cannot grant a bootstrap authority bypass;
- incomplete/evidence-failed build must not report an accepted active smart-KB Canon;
- causal-edge ownership must remain on `CausalGraph`.

''')

one(component,
'''Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is a
separate canonical-memory hardening workstream and remains OPEN while #290/#291 is
review-stage and until a fresh post-merge current-main inventory proves no other
meaningful #50 mutation family remains. Merged #288/#289 is already current-main
post-create provenance truth and is not a pending gate. Current review work does not
authorize Phase II, 13/12, ADAO, ARM-04, wider runtime activation, production rollout or
a standing Operator GO.''',
'''Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is a
separate canonical-memory hardening workstream and remains OPEN while #292/#293 is
review-stage and until a fresh post-merge current-main inventory proves no other
meaningful #50 mutation family remains. Merged #290/#291 is current-main initial raw
provenance truth and is not a pending gate. Current review work does not authorize Phase
II, 13/12, ADAO, ARM-04, wider runtime activation, production rollout or a standing
Operator GO.''')

risks = 'docs/ai/KNOWN_RISKS.md'
one(risks,
'''This convergence does **not** imply that every fact-create surface was already covered;
that separate residual is tracked below as #290/#291.''',
'''The separate initial-create residual was subsequently converged by merged #290/#291 on
current main `7a47f5dbb786fe267093857bf370fd03703207ac`.''')

between(risks,
'## P0 — Initial fact-create raw provenance remains review-stage\n',
'## P1 — Full causal reset can generate proportional audit volume\n',
'''## Reduced risk — Initial fact-create raw provenance converged

Issue #290 is CLOSED_COMPLETED and PR #291 is protected-merged on current main
`7a47f5dbb786fe267093857bf370fd03703207ac`. NEW `raw_*` single/batch facts and
replacement-fact creation close L0 provenance evidence inside their owning creation
transaction; non-raw lineage remains unchanged, generic upsert cannot rebind an existing
durable pointer, and failure rolls back. Pre/post-merge Full CI, Docker and aggregate
evidence passed. This is current-main truth, not review-stage evidence.

## P0 — Smart-KB fact-build authority remains review-stage

Fresh post-#291 inventory found that `scripts/build_kb_graph.py` could directly insert
canonical facts and use raw SQL to classify/validate them. Because `serve_smart_kb.ps1`
can install the resulting database as ordinary `VELANTRIM_DB_PATH`, the path is not an
inert projection and remains a Truth Foundation authority risk on current main.

Issue #292 / draft PR #293 is the bounded candidate. The clean implementation head
`a61d0f64a0d0df49f9c2153e3500f2b0cdd12a5d` removes raw fact DML from builder
orchestration, admits curated facts through existing `store_facts_batch()` policy,
VersionStore and AuditChain semantics, uses canonical ESM promotion, treats
`--fast-fresh` only as an empty-DB precondition, and fails incomplete builds. Existing
`CausalGraph` ownership is unchanged. Focused staging evidence `31578562991`, exact-head
Full CI `31579598960`, and Docker `31579598954` are SUCCESS before this truth-doc
reconciliation. These remain review evidence until protected merge/post-merge checks.

''')

work = 'docs/ai/WORK_LOG.md'
between(work,
'## 2026-08-12 — P0 initial fact-create raw provenance convergence in protected review\n',
'## 2026-08-11 — P0 raw provenance post-create convergence completed\n',
'''## 2026-08-12 — P0 smart-KB fact-build authority in protected review

```text
Parent Truth Foundation:       #50 · OPEN / reopened
Tracking issue:                #292 · OPEN
Implementation PR:             #293 · DRAFT / REVIEW-STAGE
Authoritative base main:       7a47f5dbb786fe267093857bf370fd03703207ac
Branch:                        p0/smart-kb-fact-build-authority
Clean implementation head:     a61d0f64a0d0df49f9c2153e3500f2b0cdd12a5d
Focused identical-tree gate:   31578562991 · SUCCESS
Exact-head Full CI:            31579598960 · SUCCESS
Exact-head Docker:             31579598954 · SUCCESS
Draft aggregate:               31579598885 · SUCCESS · not final merge gate
Documentation impact:          GITHUB_AND_NOTION · REVIEW sync pending final candidate
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

Fresh post-#291 inventory found direct smart-KB fact DML in `build_kb_graph.py`. The
resulting database can be launched as normal `VELANTRIM_DB_PATH`, so parent #50 remains
OPEN. The candidate removes builder-owned fact INSERT/UPDATE authority, declares curated
WSC classification before canonical batch admission, uses VersionStore/AuditChain-aware
batch reclassification and canonical ESM promotion, preserves `CausalGraph` ownership,
and makes `--fast-fresh` an empty-DB precondition rather than an authority bypass.
Incomplete ingest/validation fails the build.

The clean PR commit has exactly one parent (`main@7a47f5db...`) and six intended files;
staging helper history is not ancestral to PR #293. AI truth-doc reconciliation follows
the green code head and therefore changes the final PR head; Full CI + Docker must run
again on that final docs head before Notion REVIEW evidence or readiness/merge.

---

## 2026-08-12 — P0 initial fact-create raw provenance convergence completed

```text
Parent Truth Foundation:       #50 · OPEN / reopened after fresh residual
Tracking issue:                #290 · CLOSED_COMPLETED
Implementation PR:             #291 · MERGED
Final pre-merge head:          701e382cbd5fc08fc0d8475569bdeef7bc5fc673
Protected squash merge/main:   7a47f5dbb786fe267093857bf370fd03703207ac
Merge parent:                  902b2b6335b05f9a6f956e75151a8e801f23ba1d
Pre-merge Full CI:             31574822654 · SUCCESS
Pre-merge Docker:              31574822650 · SUCCESS
Ready aggregate:               31575538209 · SUCCESS
Post-merge Full CI:            31575663761 · SUCCESS
Post-merge Docker:             31575663848 · SUCCESS
Post-merge aggregate:          31575663733 · SUCCESS
Submitted reviews:             0
Codex code review:             NOT RUN — USAGE LIMIT
Unresolved review threads:     0
Documentation impact:          GITHUB_AND_NOTION · FINAL read-back confirmed
```

Current main closes initial `raw_*` provenance for single/batch creation and replacement
fact creation without reinterpreting non-raw fact lineage. A fresh post-merge inventory
then found the separate smart-KB build authority residual #292; #50 was explicitly
reopened. That residual does not invalidate #290/#291.

---

''')

one(work,
'''Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 remains OPEN while #290/#291 is review-stage and until a
fresh post-merge residual inventory proves no other meaningful canonical mutation gap
remains. Merged #288/#289 is current-main post-create provenance truth. Issue #249 stays
separate. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator GO,
runtime authority or production authority follows from the current review block.''',
'''Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 remains OPEN while #292/#293 is review-stage and until a
fresh post-merge residual inventory proves no other meaningful canonical mutation gap
remains. Merged #290/#291 is current-main initial raw-provenance truth. Issue #249 stays
separate. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator GO,
runtime authority or production authority follows from the current review block.''')

for path in (component, risks, work):
    text = Path(path).read_text(encoding='utf-8')
    if 'draft PR #291' in text or '#290/#291 is review-stage' in text:
        raise RuntimeError(f'{path}: stale #291 review narrative remains')

print('patched #293 AI truth docs')
