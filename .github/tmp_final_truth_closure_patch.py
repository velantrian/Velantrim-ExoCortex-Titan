from pathlib import Path

ROOT = Path('.')


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one anchor, found {count}: {old[:80]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def insert_after_once(path: str, anchor: str, block: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    idx = text.find(anchor)
    if idx < 0:
        raise SystemExit(f'{path}: insertion anchor missing')
    if block.strip() in text:
        raise SystemExit(f'{path}: final block already present')
    pos = idx + len(anchor)
    p.write_text(text[:pos] + block + text[pos:], encoding='utf-8')

MAIN = 'c80c8d47588de3d2607c7e1b10aa1677eb84383f'
PARENT = '7a47f5dbb786fe267093857bf370fd03703207ac'
HEAD = '48817c5b0067d085135d4e8f144a620a34265597'

# ADR: accepted only after protected merge + post-merge evidence + residual inventory.
replace_once(
    'docs/adr/ADR-2026-08-12-smart-kb-fact-build-authority.md',
    '- Status: Proposed',
    '- Status: Accepted',
)
adr = ROOT / 'docs/adr/ADR-2026-08-12-smart-kb-fact-build-authority.md'
adr_text = adr.read_text(encoding='utf-8')
adr_evidence = f'''\n\n## Acceptance evidence\n\nProtected squash merge #293 established this decision on `main` at\n`{MAIN}` with parent `{PARENT}`. Exact pre-merge head `{HEAD}` passed\nFull CI `31580684106`, Docker `31580683989`, and ready-state aggregate\n`31594821320`. Post-merge Full CI `31594960307`, Docker `31594960229`,\nand aggregate `31594960289` also passed. The merge commit signature is verified/valid.\n\nA fresh current-main Truth Foundation residual inventory after #293 found\n`REAL_GAP=0`; issue #292 and parent #50 are therefore CLOSED_COMPLETED. This\nacceptance changes no runtime, Operator GO, runtime-authority, production-authority,\nContinuity, or schema state.\n'''
if '## Acceptance evidence' in adr_text:
    raise SystemExit('ADR acceptance evidence already present')
adr.write_text(adr_text.rstrip() + adr_evidence, encoding='utf-8')

# Component map: promote smart-KB candidate to current-main convergence.
replace_once(
    'docs/ai/COMPONENT_MAP.md',
    '| smart-KB fact create/classify/validate | existing `store_facts_batch()` + canonical ESM owner; builder orchestration only | REVIEW-STAGE on #292/#293 · NOT MAIN |',
    f'| smart-KB fact create/classify/validate | existing `store_facts_batch()` + canonical ESM owner; builder orchestration only | CONVERGED on merged #293 · current main `{MAIN}` |',
)
replace_once(
    'docs/ai/COMPONENT_MAP.md',
    '### Smart-KB fact-build residual — issue #292 / draft PR #293',
    '### Smart-KB fact-build convergence — merged #292 / #293',
)
replace_once(
    'docs/ai/COMPONENT_MAP.md',
    '''PR #293 is review-stage only. Its candidate removes raw fact DML from the builder,
declares curated World Skills rows as `WORLD_FACT / EXTERNAL` before admission, delegates
create/update to existing `store_facts_batch()` evidence semantics, and delegates
validation to `promote_to_validated()` / canonical ESM transitions. Batch classification
changes become VersionStore/AuditChain-evidenced changes with coherent L0/L1 state.
`--fast-fresh` becomes only an empty-database precondition, and incomplete ingest or
validation fails the build. Causal edges remain owned by the already-converged
`CausalGraph`. These guarantees are NOT main truth until protected merge and post-merge
verification.''',
    f'''Protected squash merge #293 converged this path on current main `{MAIN}`. The
builder owns no raw canonical fact INSERT/UPDATE path: curated World Skills rows are
classified as `WORLD_FACT / EXTERNAL` before admission, create/update delegates to
`store_facts_batch()`, validation delegates to `promote_to_validated()` / canonical ESM
transitions, and batch reclassification uses VersionStore/AuditChain evidence with
coherent L0/L1 state. `--fast-fresh` is only an empty-database precondition; incomplete
ingest or validation fails the build. Causal edges remain owned by `CausalGraph`.
Issue #292 is CLOSED_COMPLETED. Pre-merge and post-merge Full CI, Docker and aggregate
evidence passed, and a fresh current-main residual inventory found `REAL_GAP=0`.''',
)
replace_once(
    'docs/ai/COMPONENT_MAP.md',
    'Candidate #293 review boundary:',
    'Current-main #293 guarantee:',
)
replace_once(
    'docs/ai/COMPONENT_MAP.md',
    '- no second canonical store or general write protocol was introduced by #283/#285/#289;',
    '- no second canonical store or general write protocol was introduced by #283/#285/#289/#291/#293;',
)
replace_once(
    'docs/ai/COMPONENT_MAP.md',
    '''Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is a
separate canonical-memory hardening workstream and remains OPEN while #292/#293 is
review-stage and until a fresh post-merge current-main inventory proves no other
meaningful #50 mutation family remains. Merged #290/#291 is current-main initial raw
provenance truth and is not a pending gate. Current review work does not authorize Phase
II, 13/12, ADAO, ARM-04, wider runtime activation, production rollout or a standing
Operator GO.''',
    f'''Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is
CLOSED_COMPLETED at current main `{MAIN}` after merged #293, green post-merge evidence,
and a fresh current-main residual inventory with `REAL_GAP=0`. Merged #288/#289,
#290/#291 and #292/#293 are current-main Truth Foundation convergence, not pending gates.
Open #53 is a downstream architecture workstream that depends on #50; this closure does
not itself authorize its implementation. No Phase II, 13/12, ADAO, ARM-04, wider runtime
activation, production rollout or standing Operator GO follows from #50 closure.''',
)

# Known risks: review-stage P0 becomes reduced/converged risk.
replace_once(
    'docs/ai/KNOWN_RISKS.md',
    '## P0 — Smart-KB fact-build authority remains review-stage',
    '## Reduced risk — Smart-KB fact-build authority converged',
)
replace_once(
    'docs/ai/KNOWN_RISKS.md',
    '''Fresh post-#291 inventory found that `scripts/build_kb_graph.py` could directly insert
canonical facts and use raw SQL to classify/validate them. Because `serve_smart_kb.ps1`
can install the resulting database as ordinary `VELANTRIM_DB_PATH`, the path is not an
inert projection and remains a Truth Foundation authority risk on current main.''',
    f'''Fresh post-#291 inventory found that `scripts/build_kb_graph.py` could directly insert
canonical facts and use raw SQL to classify/validate them. Because `serve_smart_kb.ps1`
can install the resulting database as ordinary `VELANTRIM_DB_PATH`, that was a real Truth
Foundation authority gap. Protected merge #293 converged it on current main `{MAIN}`.''',
)
replace_once(
    'docs/ai/KNOWN_RISKS.md',
    '''Issue #292 / draft PR #293 is the bounded candidate. The clean implementation head
`a61d0f64a0d0df49f9c2153e3500f2b0cdd12a5d` removes raw fact DML from builder
orchestration, admits curated facts through existing `store_facts_batch()` policy,
VersionStore and AuditChain semantics, uses canonical ESM promotion, treats
`--fast-fresh` only as an empty-DB precondition, and fails incomplete builds. Existing
`CausalGraph` ownership is unchanged. Focused staging evidence `31578562991`, exact-head
Full CI `31579598960`, and Docker `31579598954` are SUCCESS before this truth-doc
reconciliation. These remain review evidence until protected merge/post-merge checks.''',
    f'''Issue #292 is CLOSED_COMPLETED and PR #293 is protected-merged. The accepted path
removes raw fact DML from builder orchestration, admits curated facts through existing
`store_facts_batch()` policy/VersionStore/AuditChain semantics, uses canonical ESM
promotion, treats `--fast-fresh` only as an empty-DB precondition, and fails incomplete
builds. Existing `CausalGraph` ownership is unchanged. Final pre-merge head `{HEAD}`
passed Full CI `31580684106`, Docker `31580683989`, and ready aggregate `31594821320`;
post-merge main passed Full CI `31594960307`, Docker `31594960229`, and aggregate
`31594960289`. A fresh current-main residual inventory found `REAL_GAP=0`, so parent #50
is CLOSED_COMPLETED. This does not imply production readiness or runtime authority.''',
)

# Work log: add authoritative final closure block and clearly mark old review block historical.
final_block = f'''\n## 2026-08-12 — P0 smart-KB convergence + Truth Foundation #50 completed\n\n```text\nParent Truth Foundation:       #50 · CLOSED_COMPLETED · fresh residual REAL_GAP=0\nTracking issue:                #292 · CLOSED_COMPLETED\nImplementation PR:             #293 · MERGED\nFinal pre-merge head:          {HEAD}\nProtected squash merge/main:   {MAIN}\nMerge parent:                  {PARENT}\nFocused identical-tree gate:   31578562991 · SUCCESS\nPre-merge Full CI:             31580684106 · SUCCESS\nPre-merge Docker:              31580683989 · SUCCESS\nReady aggregate:               31594821320 · SUCCESS\nPost-merge Full CI:            31594960307 · SUCCESS\nPost-merge Docker:             31594960229 · SUCCESS\nPost-merge aggregate:          31594960289 · SUCCESS\nMerge signature:               VERIFIED / valid\nSubmitted reviews:             0\nCodex code review:             NOT RUN — USAGE LIMIT\nUnresolved review threads:     0\nContinuity:                    12/12 = 100% · unchanged\nSchema:                        v7 · unchanged\nRuntime currently enabled:     false · unchanged\nOperator GO:                   false · unchanged\nRuntime authority:             false · unchanged\nProduction authority:          false · unchanged\n```\n\nCurrent-main smart-KB fact build no longer owns raw canonical fact DML. Curated fact\nadmission delegates to `store_facts_batch()`, validation to canonical ESM promotion,\n`--fast-fresh` is only an empty-DB precondition, incomplete builds fail closed, and\ncausal edges remain on `CausalGraph`.\n\nFresh residual inventory on `{MAIN}` rechecked fact create/update, raw provenance, ESM\ntransitions, supersede, redaction, archival rewrite, durable erasure/dependent deletion,\ncausal relations, async adapters, smart-KB build, cache-maintenance, projections/indexes,\nentity/living-context/notes/audit side stores, migration-only paths and scratch ingestion.\nNo new meaningful canonical mutation owner remained: `REAL_GAP=0`. Emergency coverage\nissue #28 is CLOSED. Open #53 is downstream architecture that depends on #50 and is not\na residual #50 mutation gap or an authorization granted by this closure.\n\n---\n'''
insert_after_once('docs/ai/WORK_LOG.md', '---\n', final_block)
replace_once(
    'docs/ai/WORK_LOG.md',
    '## 2026-08-12 — P0 smart-KB fact-build authority in protected review',
    '## Historical pre-merge evidence — P0 smart-KB fact-build authority',
)
replace_once(
    'docs/ai/WORK_LOG.md',
    '''Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 remains OPEN while #292/#293 is review-stage and until a
fresh post-merge residual inventory proves no other meaningful canonical mutation gap
remains. Merged #290/#291 is current-main initial raw-provenance truth. Issue #249 stays
separate. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator GO,
runtime authority or production authority follows from the current review block.''',
    f'''Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 is CLOSED_COMPLETED on current main `{MAIN}` after merged
#293, green post-merge evidence and a fresh residual inventory with `REAL_GAP=0`. Merged
#288/#289, #290/#291 and #292/#293 are current-main Truth Foundation history. Issue #249
stays separate. Open #53 is downstream architecture, not an automatic next implementation
authorization. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator
GO, runtime authority or production authority follows from this closure.''',
)

print('patched final Truth Foundation closure docs')
