# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-16  
**Phase 3A implementation checkpoint:** `main@4932727c348ec967564d8babf80e25ca82bce8be` · signature `VERIFIED / valid`  
**C11 lifecycle rule:** this snapshot preserves the reconciled #52 risk record; resolve current issue/PR lifecycle from live GitHub  
**Continuity:** `12/12 = 100%` — complete  
**Runtime:** `CURRENTLY DISABLED · CURRENT OPERATOR GO ABSENT · HISTORICAL OBSERVED=true · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`  
**Governance:** active `main-governance` · solo mode · approvals `0` · review-thread resolution required · required check `Titan aggregate merge evidence`

A green CI run, manifest, config, historical canary, archive payload, audit record or
Notion update is evidence only. None of them grants current permission, runtime authority
or production authority.

## Reduced risk — World Skills admission is fail-closed; legacy corpus remains unreviewed

C9 for parent #52 is **CLOSED** through protected-merged PR #320 at signed
`main@0b2c49d701b88d12c66042148c19199638130d03`. The historical World Skills curated-ingest
path had been a real trust-boundary residual: legacy rows lacked the complete structured
`truth_status/source_refs/risk_domain/limitations/review_status/reviewer/reviewed_at`
contract and the importer directly called `promote_to_validated()`.

The admitted implementation removed that direct business-level exception. Legacy rows are
explicit Draft/unreviewed candidates with empty provenance/risk/reviewer metadata and must
remain non-canonical unless real evidence is added. Curation, filename location, Git
history, claim prose and LLM output are not substitutes for attributable `source_refs` or
reviewer evidence.

The accepted path reuses existing owners:

```text
metadata/review gates
→ TruthGate read-only precheck
→ legal ESM ladder to Supported
→ PromotionGateway
→ validate_and_promote()
→ TruthGate recheck + CAS
→ Validated / local Canon
```

High-risk metadata selects the existing `PRECISION` TruthGate mode; C9 owns no numerical
thresholds. Candidate/pack SHA-256 digests are deterministic content/replay integrity
identifiers, **not cryptographic human signatures**. Reviewer-key authentication remains
unimplemented and is not required/claimed by C9. If cryptographic reviewer signatures are
later required, they need a separately governed identity/key owner and fresh admission.

C9 closure proof is complete: exact-head Full CI #1180, Docker #778, CodeQL #18 and Ready
aggregate #1212 succeeded; protected merge `0b2c49d...` is verified/valid; post-merge Full
CI #1181, Docker #779, CodeQL #19 and aggregate #1213 succeeded; GitHub and same-page Notion
FINAL/read-back were reconciled. The remaining risk is semantic, not an admission bypass:
the historical corpus is still not retroactively reviewed until real source/reviewer
metadata is authored. C9 proves fail-closed admission, not corpus truth.

## Open risk — TruthGate evidence references remain cardinality-based pending a separate admission

The first `Typed Evidence Reference v1` increment is an **unwired draft contract only**.
It adds strict local source/fragment/lineage reference parsing and an in-memory validation
receipt prototype, but it does not change `TruthGate` thresholds, its current legacy
`metadata.evidence_refs` string-list interpretation, candidate ingestion, persistence or
canonical promotion. Therefore no claim is made that current evidence counts establish
source integrity, independent provenance or automated truth.

The draft contract explicitly rejects producer-supplied `independence_class` and records
no replacement local effective-independence result. Its receipt is a deterministic
local-validation artifact only: `validated_reference_count` is diagnostic cardinality, not
evidence sufficiency, admission, truth or promotion authority. The hardening checkpoint
also rejects noncanonical span/timestamp aliases and malformed direct outcome/receipt
construction through controlled contract errors. Conflicting payloads that reuse one
`reference_id` fail closed. This closes the prototype's self-granted-independence surface;
it does not authenticate the registry snapshot, decide contextual independence or change
current TruthGate behavior.

The future work remains intentionally split: persist a local registry only after a
separate data-classification decision; introduce `LEGACY`/`OBSERVE`/opt-in `ENFORCE`
modes only after differential and fault testing; attach a receipt only through the
existing authorized metadata/audit boundary; and migrate producers only when real stable
source artifacts exist. At ecosystem level, Titan must remain a resolver/projection or
experimental registry rather than a second trusted-evidence Canon beside Crystal.
Historical facts must not receive synthetic digests, lineage or reclassification. This
risk is **not closed** by the contract-only draft.

## P0 — No current Operator GO or deployed activation

The completed bounded canary used a single-use human authorization that is exhausted.
Current runtime state remains disabled and current Operator GO remains false. Any future
real activation requires a separately scoped current decision and explicit Operator GO.

## P0 — Concrete live current-decision owner adapters remain unselected

The six Continuity current-decision ports still lack accepted live deployment adapters
for principal, authorization, consent/lawful basis, restriction, erasure and
PolicySnapshot. Continuity 12/12 does not replace those owners.

## P1 — Continuity 12/12 is not production readiness

The internal mechanism chain and one rolled-back canary do not prove production traffic,
SLOs, disaster recovery, public multi-user rollout, independent security review or
production-scale failure recovery.

## P1 — Solo governance has no independent approval gate

The active repository ruleset requires zero approvals in solo mode, while requiring PR
flow, review-thread resolution and the aggregate status check. Independent review is
therefore not implied by mergeability. Codex usage-limit failures must be recorded as
`NOT RUN — USAGE LIMIT`, never as approval.

## Reduced risk — #249 CAS contention is characterized; product CAS defect not confirmed

Issue #249's engineering characterization is complete through merged PR #346 at signed
checkpoint `main@fa09bc128b7be2f05fd46a8bd374ebf68ae7f62d`; re-check live issue lifecycle
before acting. The old blind-barrier `BrokenBarrierError` was not evidence that the
canonical CAS admitted two winners or duplicate projection intents. The final hosted
characterization isolates schema-ready contenders before the real promotion race and
passes 100/100 exact `[25]` executions on the accepted PR head plus another 100/100 on
post-merge main across Python 3.11/3.12 hosted-runner shards. Every passing iteration
retains one winner, one outbox intent, final `Validated`, canonical-version binding,
idempotent retry and SQLite integrity.

No production `_promote_to_validated_cas()` code, automatic retry, SQLite timeout, WAL
mode, backend or schema was changed. The bounded classification is **TEST HARNESS SCOPE
DEFECT / HISTORICAL RUNNER SENSITIVITY · PRODUCT CAS DEFECT NOT CONFIRMED**. This is not
proof of unlimited SQLite concurrency or production-scale multiprocess safety.

## P1 — Concurrent fresh-store bootstrap can invalidate peer SQLite statements

Hosted #249 diagnostics exposed a separate pre-CAS failure now tracked by Issue #347:
concurrent first use of multiple fresh `SQLiteGraphStore` instances against one database
can produce `sqlite3.OperationalError: database schema has changed` while per-instance
lazy schema/bootstrap work is still in flight. The observed failure occurred before the
CAS gate (25/25 workers started, 24/25 reached pre-CAS, 0/25 CAS returned), so it must not
be relabelled as a product CAS algorithm failure.

#347 remains an open storage/lifecycle characterization risk. Do not paper over it with
broad `OperationalError` swallowing, automatic mutation retry, timeout inflation, WAL or
backend changes. First establish the supported concurrent-first-use contract and exact
failing DDL/read interleaving.

## P1 — PII claim redaction is bounded, not universal physical erasure

Issue #282 / merged PR #283 converged PII **claim** redaction on
`CanonicalPiiRedactor`. Affected VersionStore claim history is intentionally sanitized so
the removed plaintext is not re-persisted. This is implementation truth at checkpoint
`493b1b6b6204cc9a7f5de82709717a1b625e2234`.

It does not prove removal from arbitrary metadata, immutable/raw origins, every external
backend, backups or unrelated historical logs. Full durable physical erasure remains a
separate ErasureCoordinator contract; no certified GDPR claim follows.

## P1 — Archival filesystem/SQLite boundary remains bounded

Issue #284 / merged PR #285 converged archival canonical claim rewrite on the existing
`SQLiteGraphStore` evidence primitives at checkpoint
`3100952f3dacf268f4d9c9b3f5a738f449663de6`.

The payload is created/fsynced before Canon may point at it; canonical claim, VersionStore,
AuditChain, archive marker, FTS and active outbox intent are one SQLite transaction. A
filesystem file cannot join that SQLite ACID transaction without another transactional
system. If the SQLite transaction fails after payload creation, cleanup remains
best-effort. An OS cleanup failure can leave a **non-canonical orphan payload**; that
residue is never canonical archival success.

## Reduced risk — Causal ownership + post-merge failure-path hardening verified

Issue #286 / merged PR #287 converged SQLite `relations` mutation on `CausalGraph` at
checkpoint `615201ec1073dafb047028e88ce94463f4ef9b77`. Relation create/batch/remove/reset
uses the bounded canonical owner with same-transaction lifecycle AuditChain evidence.
Automatic/non-manual input defaults to hypothesis/pending, derived snapshots cannot
self-promote authority labels, and Neo4j/Graphiti reload cannot destructively replace
local Canon. `RelationStore` / `fact_relations` remains a separate associative model.

The subsequent post-merge audit found additional logical failure paths around snapshot
admission, reset ownership/concurrency, inverse identity/deletion, legacy duplicate
ambiguity and malformed metadata. Those defects are now closed by merged PR #297:

```text
exact tested head:       9830212159b092af2b3867d52e02fc7aaa57afa1
protected squash merge:  c96b734b94f30e1d96e8bcb992dec429bda5c8fd
review threads:          13/13 RESOLVED
READY aggregate:         #914 · 31725868065 · SUCCESS
post-merge Full CI:      #1085 · 31725945373 · SUCCESS
post-merge Docker:       #705 · 31725945362 · SUCCESS
```

Snapshot/WriteGate/AuditChain/reset failures are propagated fail-closed; reset epochs are
serialized; cold durable reset cannot silently no-op; canonical inverse identity is
reserved and cross-validated; ambiguous/corrupt legacy pairing fails closed instead of
guessing. The fresh fourth Codex review did not run because of usage limits; no independent
approval is claimed or required by the active solo ruleset.

Remaining causal risks are bounded rather than silently closed: explicit future
accepted-label callers still need their own authorized admission surface, and full graph
reset cost/audit volume grows with graph size. Neither risk justifies raw-SQL bypass or
remote truth authority.

## Reduced risk — Post-create raw provenance binding converged

Issue #288 is CLOSED_COMPLETED and PR #289 is protected-merged at checkpoint
`902b2b6335b05f9a6f956e75151a8e801f23ba1d`. For an already-existing unbound fact,
`SQLiteGraphStore.link_raw_to_fact()` owns first-binding CAS semantics with VersionStore
pre-image, `l0_fact_provenance` and AuditChain evidence in one SQLite transaction.
Same-source retries are idempotent, conflicting second sources fail closed, and legacy
`RawMemoryStore.link_fact()` no longer owns an independent canonical UPDATE.

The separate initial-create residual was subsequently converged by merged #290/#291.

## Reduced risk — Initial fact-create raw provenance converged

Issue #290 is CLOSED_COMPLETED and PR #291 is protected-merged at checkpoint
`7a47f5dbb786fe267093857bf370fd03703207ac`. NEW `raw_*` single/batch facts and
replacement-fact creation close L0 provenance evidence inside their owning creation
transaction; non-raw lineage remains unchanged, generic upsert cannot rebind an existing
durable pointer, and failure rolls back. Pre/post-merge Full CI, Docker and aggregate
evidence passed.

## Reduced risk — Smart-KB fact-build authority converged

Fresh post-#291 inventory found that `scripts/build_kb_graph.py` could directly insert
canonical facts and use raw SQL to classify/validate them. Because `serve_smart_kb.ps1`
can install the resulting database as ordinary `VELANTRIM_DB_PATH`, that was a real Truth
Foundation authority gap. Protected merge #293 converged it at checkpoint
`c80c8d47588de3d2607c7e1b10aa1677eb84383f`.

Issue #292 is CLOSED_COMPLETED and PR #293 is protected-merged. The accepted path removes
raw fact DML from builder orchestration, admits curated facts through existing
`store_facts_batch()` policy/VersionStore/AuditChain semantics, uses canonical ESM
promotion, treats `--fast-fresh` only as an empty-DB precondition, and fails incomplete
builds. Existing `CausalGraph` ownership is unchanged. A fresh current-main residual
inventory found `REAL_GAP=0`, so parent #50 is CLOSED_COMPLETED. This does not imply
production readiness or runtime authority.

## P1 — Full causal reset can generate proportional audit volume

An explicit destructive causal reset enumerates physical relation IDs and appends a
structured `relation_removed` event for each removed row in the same transaction. This
maximizes audit fidelity but means transaction work grows with graph size. It is an
explicit admin/KB operation, not a background loop.

Production-scale reset latency/size is not proven by #287/#297 and must not be represented
as such. This risk does not justify bypassing the canonical owner or dropping audit
evidence.

## Reduced risk — async canonical mutation bypass

`AsyncSQLiteStore` is an async execution adapter over exact synchronous canonical methods
using `asyncio.to_thread`. The former native aiosqlite write implementation remains
explicitly disabled. Existing equivalence and cancellation tests prove the adapter does
not own an independent SQL mutation path.

## Reduced risk — ModelFreeCore post-merge hardening verified

Issue #295 / PR #296 introduced the explicit `ModelFreeCore` facade at checkpoint
`e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96`. The subsequent audit found that green CI did
not cover several logical guarantees: an opt-in cognitive reranker could violate the
model-free boundary; graph collection could initialize a DDL-capable singleton and swallow
read failures; restricted relation endpoints could leak; inverse physical pairs could
double-count; relation provenance could be dropped; FactsPack failure could fall back to
raw rows; unverified evidence could be rendered as confirmed; malformed typed input could
be accepted; and later review rounds found additional reset/identity/corrupt-metadata,
policy-TOCTOU and semantic-collapse defects.

Merged PR #297 closes that bounded hardening lane. `ModelFreeCore` now remains lexical and
read-side only, avoids cognitive reranking/provider/network paths, does not initialize an
absent graph, fails boundedly when a present graph cannot be trusted, validates every
physical relation row before semantic collapse, validates reciprocal inverse identity,
rechecks endpoint recall policy on the admitted snapshot, preserves relation provenance,
requires FactsPack policy, validates typed input, and separates verified evidence from
attributed/unverified reports with one-line escaping.

This does **not** prove runtime routing, default-route replacement, embedding/vector
architecture, ADAO, LLM execution, network/provider access or production readiness.
Optional graph absence remains non-blocking; a graph that is present but unreadable must
not produce a falsely complete answer.

## Reduced risk — Phase 2A descriptor/provider-health contract converged, runtime remains unwired

Issue #299 / merged PR #300 closed the bounded architectural gap for a generic typed
capability descriptor + explicit provider-health + selection-explanation contract.

```text
exact tested head:       f0b893bac1b6fe1f58a71c70ac631f3c14becb59
protected squash merge:  c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
pre-merge Full CI:       #1105 · 31735939941 · SUCCESS
pre-merge Docker:        #723 · 31735939929 · SUCCESS
READY aggregate:         #981 · 31736858130 · SUCCESS
post-merge Full CI:      #1106 · 31736925690 · SUCCESS
post-merge Docker:       #724 · 31736925695 · SUCCESS
post-merge aggregate:    #982 · 31736925705 · SUCCESS
```

`core/capability_registry.py` reuses the existing process-wide `PolicyKernel` through
`get_policy_kernel()` and exposes no production policy/leaser constructor injection.
Provider metadata cannot hide remote network requirements; capability-specific data mode
is PolicyKernel input, not consent; unknown/unavailable health fails closed; explicit
preference cannot override a lease denial; policy evaluation failure or mixed snapshots
cannot fall back to selection.

The following **remain unproved and unauthorized** by Phase 2A:

- runtime wiring of the registry into the query/pipeline path;
- active provider probing or provider invocation;
- embeddings/vector or reranker execution;
- LLM execution;
- ADAO execution;
- remote-consent implementation or network activation;
- ARM-04;
- Operator GO, runtime authority or production authority.

A later wiring/activation phase must be separately admitted. `auto` remains preference,
never permission.

## Reduced risk — Phase 3A embedding-space identity converged; semantic execution remains unwired

Issue #327 / protected-merged PR #328 closes the bounded correctness gap between Titan's
existing embedding registry, persistent projection/storage identity and legacy dense
scorer.

The accepted `EmbeddingSpaceDescriptor` binds provider, model, model revision, dimension,
normalization, pooling, distance metric, chunker version and preprocessing version into a
canonical JSON + SHA-256 `embedding_space_id`. Same dimension is not sufficient for
compatibility. Legacy rows that lack the complete identity are not auto-adopted; they fail
closed to lexical fallback. The existing EmbeddingStore/Projection owners are reused and
schema remains v7.

DenseRetriever now preflights the complete candidate batch against the query dimension
before any similarity multiplication, closing the future persistent-vector `zip()`
truncation trap without wiring persistent projection into the live route.

Accepted evidence:

```text
final PR head:             96f4aad2ae4a65203cc133dbe2af40ed869c99e8
protected squash merge:    4932727c348ec967564d8babf80e25ca82bce8be
signature:                 VERIFIED / valid
exact-head Full CI:        #1210 · 31882948349 · SUCCESS
exact-head Docker:         #799  · 31882948356 · SUCCESS
exact-head CodeQL:         #48   · 31882948357 · SUCCESS
READY aggregate:           #1315 · 31883253917 · SUCCESS
post-merge Full CI:        #1211 · 31883324866 · SUCCESS
post-merge Docker:         #800  · 31883324890 · SUCCESS
post-merge CodeQL:         #49   · 31883324957 · SUCCESS
post-merge aggregate:      #1316 · 31883324900 · SUCCESS
```

The remaining semantic risks are intentionally open for future admission rather than
silently closed:

- persistent projection is not wired into live retrieval;
- no provider execution/probing/network/remote embedding is enabled;
- no Titan-specific semantic retrieval-quality benchmark has been admitted or passed;
- legacy projection rows require explicit bounded rebuild under complete typed metadata;
- background indexing remains unauthorized;
- Phase 3A grants no Operator GO, runtime authority or production authority.

These residuals do not invalidate Phase 3A; they define the boundary of what it proved.

## Reduced risk — Documentation hand-off validation converged

Issue #305 / merged PR #306 closes the bounded mismatch between the written connectorless
Notion hand-off protocol and aggregate merge-evidence validation.

```text
exact tested head:       d5767cb9db5aa257128ca34c049f7902c9b7e227
protected squash merge:  5cd4003d62d8f5e09971f2b46f89e61ab58bffca
exact-head Full CI:      #1114 · 31750358527 · SUCCESS
READY aggregate:         #1004 · 31751015239 · SUCCESS
review threads:          0 unresolved
post-merge Full CI:      #1115 · 31751070147 · SUCCESS
post-merge aggregate:    #1005 · 31751070170 · SUCCESS
Docker:                  not spawned / not claimed
```

The existing `scripts/check_pr_merge_evidence.py` remains the aggregate owner. A thin
trusted adapter now reads `docs/ai/NOTION_HANDOFF.md` from the actual exact PR head and
fails connectorless `UNAVAILABLE + HANDOFF_REQUIRED` evidence unless the declared path is
the machine-stable `#handoff-pr-<current-PR>` anchor, the hand-off file is part of that PR,
and the matching structured item is bound to the current PR/base with the required
provenance and sections. Arbitrary paths, missing items, stale other-PR items and wrong
base SHA fail closed. The ordinary `AVAILABLE + SYNCED` route remains unchanged.

Post-merge aggregate #1005 executed the adapter's `--all-open` entrypoint from trusted
default-branch code, so the new workflow entrypoint is proven in real Actions execution.
This governance hardening changes no runtime, Canon, capability, provider, Continuity,
schema, Operator GO, runtime-authority or production-authority semantics.

## Operational residuals

Still not proved:

- multi-process write contention under production load;
- large-graph full-reset latency/audit volume under production load;
- disk-full/filesystem-permission behavior at production scale;
- live backup/restore and disaster-recovery orchestration;
- external audit service/SLO/alerting coverage;
- independent security review or penetration test;
- complete production evidence for Reader Core (#120);
- persistent semantic projection runtime integration;
- Titan-specific semantic retrieval quality.

## Risk update rule

Keep these states separate:

```text
IMPLEMENTED
TESTED
WIRED
RUNTIME CURRENTLY ENABLED
OPERATOR AUTHORIZATION PRESENT
OPERATOR GO
OBSERVED                 <- durable historical evidence
RUNTIME AUTHORITY
PRODUCTION AUTHORITY
PRODUCTION-READY
```

Never infer a later state from an earlier one. In particular, historical observation,
Phase 3A's tested compatibility contract and 12/12 Continuity never imply current
permission or production authority.
