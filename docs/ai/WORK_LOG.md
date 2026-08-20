# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.
Older detail remains traceable in Git history, merged PRs, issues, ADRs and dated checkpoints.

---

## 2026-08-20 — Typed Evidence Reference v1 · CURRENT LIFECYCLE TRUTH

> **Reality status:** `DRAFT / CONTRACT-ONLY / LOCAL VALIDATION ONLY / UNWIRED / NOT ENABLED / NO RUNTIME AUTHORITY / NO PRODUCTION AUTHORITY`.
> Re-query live GitHub for exact head/base and CI before acting; dated checkpoints below remain history, not evergreen state.

This current hardening checkpoint accepts only one canonical EvidenceReference span and
captured-at representation, rejects malformed mapping keys and reference elements through
controlled contract errors, and structurally validates local outcomes/receipts. The receipt
contains no independence result. `validated_reference_count` is diagnostic local validation
cardinality only; it is not evidence sufficiency and has no runtime consumer.

No EvidenceAdmissionDecision, target evidence adapter, policy snapshot, OBSERVE/VERIFY/ENFORCE
runtime mode, TruthGate/WriteGate/PromotionGateway integration, persistence, migration, route,
worker, telemetry pipeline, runtime activation or authority is created here. Validation is not
admission; a receipt is not authority or truth; Titan remains a local resolver/prototype rather
than an evidence sovereign.

---

## 2026-08-19 — Typed Evidence Reference v1 · DRAFT CONTRACT-ONLY IMPLEMENTATION

> **Reality status:** `PROPOSED / IMPLEMENTED ON DRAFT BRANCH / FOCUSED-TESTED / UNWIRED / NOT ENABLED / NO RUNTIME AUTHORITY`.
> Re-resolve the live PR and exact head before treating this draft record as merged reality.

The first bounded increment adds `core/evidence_reference.py` and
`core/evidence_registry.py`, plus a focused test suite and ADR. It defines immutable,
versioned source/fragment/lineage references, strict local validation and deterministic,
content-minimized validation receipts. The in-memory registry is a Python prototype only.

Historical review of the first draft found and removed a self-grant surface:
`EvidenceReference.independence_class` was producer-controlled and affected an effective
lineage count. That early registry-owned classification idea is **superseded by the current
contract truth above**: v1 records no independence result because local validation does not
own that semantic. The corrected reference contains no independence classification.
Conflicting payloads that reuse one `reference_id` fail closed, and validation is ordered
deterministically. No same-lineage or effective-independence policy is implemented here.

It does **not** alter `TruthGate` thresholds or outcomes, `metadata.evidence_refs`,
canonical promotion/CAS, SQLite schema, source ingestion, network/provider behavior,
runtime wiring, feature flags, Operator GO, runtime authority or production authority.
The existing `EvidenceItem` scoring model remains its own owner. A future admission must
separately decide persistence, observe/enforce modes, receipt attachment and producer
migration; no historical fact is auto-converted or reclassified by this draft.

Focused local evidence after this correction: 25 contract tests passed; the combined
EvidenceReference/Evidence authenticity/TruthGate suite passed 55 tests; repository-wide
Ruff and Mypy passed for all 332 `core/` source files. Repository guard checks for
branding, tracked artifacts, project state and KB graph integrity also passed.

The local Python 3.12 full-suite characterization was not green: after excluding one
separately reproduced baseline failure, it completed with 4 failed, 4,323 passed,
17 skipped, 1 deselected and 1 xfailed. The excluded failure and all four completed-run
failures were each reproduced with the same environment against unchanged
`main@588ffe61`; none touches the EvidenceReference files or behavior. This is bounded
baseline/environment evidence, not a waiver. The earlier GitHub checks belong to an
ancestor head.

The corrected code checkpoint
`8a1b3aab56c2aeaa5050872b660aed6fc9df40db` then passed GitHub Main CI #1325,
Docker #872 and CodeQL #164. Aggregate evaluator run 32232797602 completed successfully;
the combined context remains `PENDING` while PR #355 remains a DRAFT. A dedicated Notion
record, `Titan Typed Evidence Reference v1 — Trusted Independence Contract · 2026-08-19`
(`3c1ac84d-0547-811f-8f81-ff62f45b659d`), was created under the Titan hub and verified by
read-back. Fresh CI on the final documentation-sync head and review remain required; no
merge, runtime enablement or authority follows from this synchronization.

---

## 2026-08-16 — #249 hosted CAS characterization · ENGINEERING CHARACTERIZATION COMPLETE

> **Live-state rule:** re-check Issue #249 and current `main` before acting. This dated
> record freezes the engineering classification proven by PR #346; it does not make a
> dated OPEN/CLOSED issue literal evergreen.

```text
characterization issue:            #249 · RE-VERIFY LIVE LIFECYCLE
implementation / evidence PR:      #346 · MERGED
exact accepted PR head:            26fc2e6f8f7712740394d305f79596801eed4045
protected squash merge/checkpoint: fa09bc128b7be2f05fd46a8bd374ebf68ae7f62d
merge parent:                      6120fdbb386a6b90391e05398c19d56e1f576339
merge signature:                   VERIFIED / valid
classification:                    TEST HARNESS SCOPE DEFECT / HISTORICAL RUNNER SENSITIVITY
product CAS defect:                NOT CONFIRMED
separate bootstrap residual:       #347 · OPEN · RE-VERIFY LIVE
production CAS code changed:       NO
runtime / authority changed:       NO
Phase 3B:                          NOT ADMITTED / NOT STARTED
```

### What the hosted evidence established

The historical #249 failure was a `BrokenBarrierError` in the old blind pre-CAS barrier.
PR #250 had already replaced that barrier with stage-aware diagnostics, but local repeated
passes alone were not closure-grade evidence for GitHub-hosted scheduling. PR #346 added
a repeatable hosted matrix for the exact current `[25]` projection-outbox contention test.

The first hosted diagnostic run (`31958543077`) did **not** show a two-winner or duplicate-
intent CAS failure. Instead, three of four independent jobs failed before the CAS gate was
released with `sqlite3.OperationalError: database schema has changed`; stage evidence was
25/25 workers started, 24/25 pre-CAS reached and 0/25 CAS returned. Fresh inspection showed
that the test created 25 fresh `SQLiteGraphStore` instances whose per-instance lazy schema
bootstrap could race before the intended promotion contention. That distinct storage /
lifecycle question is now isolated as Issue #347 rather than hidden inside #249.

The #249 harness was then narrowed to its actual causal question: every contender store is
made schema-ready sequentially before the synchronized real `validate_and_promote()` /
`_promote_to_validated_cas()` race. No product CAS implementation, retry policy, SQLite
timeout, WAL mode, backend or schema was changed.

### Accepted exact-head evidence

```text
hosted CAS characterization #4: 31959073081 · SUCCESS
  Python 3.11 × 2 shards + Python 3.12 × 2 shards
  25/25 repetitions per job = 100/100 exact hosted invariant executions
Full CI #1288:                  31959073075 · SUCCESS
CodeQL #126:                    31959073069 · SUCCESS
post-Ready aggregate #1565:     31959620687 · SUCCESS
Docker:                         NOT SPAWNED · no Docker success claimed
submitted reviews:              0
unresolved review threads:      0
```

### Protected-merge evidence on `main@fa09bc128…`

```text
hosted CAS characterization #5: 31959660584 · SUCCESS
  4/4 required jobs = another 100/100 exact hosted invariant executions
Full CI #1289:                  31959660561 · SUCCESS
CodeQL #127:                    31959660558 · SUCCESS
post-merge aggregate #1568:     31959660557 · SUCCESS
Docker:                         NOT SPAWNED on the #346 exact-main path
```

Every passing exact `[25]` execution retains the product invariants: exactly one winner,
exactly one projection-outbox intent, final `Validated` state, canonical-version binding,
idempotent post-race retry with no second intent, and `PRAGMA integrity_check = ok`.

The evidence therefore supports **TEST HARNESS SCOPE DEFECT / HISTORICAL RUNNER
SENSITIVITY; PRODUCT CAS DEFECT NOT CONFIRMED**. It does **not** prove unlimited SQLite
concurrency, arbitrary multiprocess safety, or that the fresh-store bootstrap residual is
closed. Issue #347 owns that separate P1 characterization.

### Authority boundary unchanged

```text
Continuity:             12/12
project-state schema:   v7
runtime enabled:        false
Operator GO:            false
runtime authority:      false
production authority:   false
Canon:                  local
remote Canon:           forbidden
Phase 3B:               NOT ADMITTED / NOT STARTED
```

---

## 2026-08-16 — #343 post-hardening current-truth convergence · FINAL RECONCILIATION RECORD

> **Live-state rule:** this dated record does not encode the current open/closed state of
> Issue #343. Re-check the live GitHub issue before acting. The block below records the
> verified #344 reconciliation evidence and removes lifecycle-sensitive wording that became
> stale after post-merge closure/reopen activity.

```text
tracking issue:                    #343 · RE-VERIFY LIVE LIFECYCLE
reconciliation base:               8ed2fb60c1edaa96d9af9955184c4abc31ef8500
original reconciliation PR:        #344 · MERGED
#344 exact accepted head:          59d1074f913be4b65d212d7480a0acdf20b28829
#344 protected squash merge/main:  62ab18eb199c90b04401f6da478d5f833e3771f3
#344 post-merge Full CI:           #1282 · 31942430316 · SUCCESS
#344 post-merge CodeQL:            #120  · 31942430394 · SUCCESS
#344 post-merge aggregate:         #1549 · 31942430354 · SUCCESS
#344 Docker:                       NOT SPAWNED · no Docker success claimed
CSM Stage C issue / PR:            #333 CLOSED / #335 MERGED
CSM Stage C merge:                 b4c6f0c16ef9920607d95e590a75df8176d92d71
multilingual lifecycle issue / PR: #340 CLOSED / #341 MERGED
multilingual merge checkpoint:     8ed2fb60c1edaa96d9af9955184c4abc31ef8500
documentation class:               GITHUB_AND_NOTION
project-state schema:              v7 · UNCHANGED
runtime enabled:                   false
Operator GO:                       false
runtime authority:                 false
production authority:              false
Phase 3B:                          NOT ADMITTED / NOT STARTED
```

Fresh reconciliation originally confirmed that implementation closure had advanced beyond
public AI context. PR #344 corrected the mandatory current-state surfaces for protected-
merged CSM Stage C (#335) and multilingual retrieval lifecycle hardening (#341) without
changing runtime behavior or authority.

A post-closure independent audit then found a smaller residual in this same top work-log
block: it still labelled #343 `OPEN / IN PROGRESS`, called the #341 merge checkpoint
`current main`, and left the documentation-drift row open after #344 had already merged.
The audit's proposed patch also referred to aggregate #1548 as post-merge evidence; live
GitHub verification shows #1548 is the successful post-Ready **pre-merge** aggregate on
PR head `59d1074f…`, while #1549 / `31942430354` is the true successful post-merge
aggregate on `main@62ab18eb…`.

This final reconciliation record therefore uses lifecycle-stable wording: the live issue
state is resolved from GitHub, historical merge checkpoints are labelled as checkpoints,
and exact #344 post-merge evidence is bound to the merged main SHA. No Python runtime,
project-state schema, feature flag, Canon, Truth, Policy, CSM behavior, retrieval behavior,
or activation posture changes in this correction.

### CSM Stage C factual closure

PR #335 final accepted head `2be69dc8c9007dd3fd7d9eae998e137095f1d4a1` protected-squash-merged as
`b4c6f0c16ef9920607d95e590a75df8176d92d71`.

```text
exact-head Full CI:        #1273 · 31927808211 · SUCCESS
exact-head Docker:         #855  · 31927808219 · SUCCESS
exact-head CodeQL:         #111  · 31927808241 · SUCCESS
READY aggregate:           #1519 · 31928109777 · SUCCESS
post-merge Full CI:        #1274 · 31928517680 · SUCCESS
post-merge Docker:         #856  · 31928517601 · SUCCESS
post-merge CodeQL:         #112  · 31928517705 · SUCCESS
post-merge aggregate:      #1520 · 31928517687 · SUCCESS
unresolved review threads: 0
```

Current factual Stage C status at the #344 reconciliation checkpoint is:

`IMPLEMENTED · TESTED · PROTECTED-MERGED · POST-MERGE VERIFIED · UNWIRED · NOT ENABLED · NON-CANONICAL`.

CSM remains `DERIVED · REBUILDABLE · REPOSITORY-SCOPED · SNAPSHOT-BOUND`. No Stage D,
runtime route, startup hook, worker, watcher, daemon, MCP adapter, Canon/Truth/Policy owner
or production authority follows from #335.

### Multilingual retrieval patch lifecycle closure

PR #341 final head `848f8c694cc6d884be6a1aa7f5d97d33879450c9` protected-squash-merged as
checkpoint `8ed2fb60c1edaa96d9af9955184c4abc31ef8500`; PR #344 later advanced main to
`62ab18eb199c90b04401f6da478d5f833e3771f3`.

```text
exact-head Full CI:        #1276 · SUCCESS
exact-head Docker:         #858  · SUCCESS
exact-head CodeQL:         #114  · SUCCESS
READY aggregate:           #1532 · SUCCESS
post-merge Full CI:        #1277 · SUCCESS
post-merge Docker:         #859  · SUCCESS
post-merge CodeQL:         #115  · SUCCESS
post-merge aggregate:      #1533 · SUCCESS
submitted reviews:         0
unresolved review threads: 0
```

The existing multilingual patch is idempotent/reversible with exact original identity
restoration, external-replacement non-clobbering and safe stale-ownership cleanup. The
final test-only repair resolved intentionally re-imported `core.*` modules at execution
time; production retrieval semantics were not weakened or altered to make CI green.

### Previous findings reconciliation matrix

| Finding | Current status | Evidence / boundary |
|---|---|---|
| Query read-side purity | **CLOSED** | #331 / #342; query path must not initialize DDL-capable causal schema |
| `/query/roles` LLM provenance | **CLOSED** | #332 / #334; deterministic fallback cannot masquerade as LLM success |
| IndexCoordinator ↔ NGram API contract | **CLOSED** | #336 / #337; real public NGram API + degraded health semantics |
| `storage_info()` stale lifecycle cache | **CLOSED** | #338 / #339; reset clears cached backend metadata |
| multilingual wrapper lifecycle | **CLOSED** | #340 / #341; merge checkpoint `8ed2fb60…` |
| CSM Stage C scanner | **IMPLEMENTED / TESTED / MERGED / UNWIRED / NON-CANONICAL** | #333 / #335; merge `b4c6f0c…` |
| AI-context documentation drift | **RECONCILED** | #343 / #344; live issue lifecycle must be re-verified before action |
| CAS contention characterization | **CHARACTERIZED / HARNESS SCOPE DEFECT** | #249 / #346; product CAS defect not confirmed; separate fresh-store bootstrap residual is #347 |
| independent approval | **KNOWN GOVERNANCE RISK / ACTIVATION PREREQUISITE** | solo ruleset currently requires 0 approvals; green CI is not independent review |
| production-scale evidence | **OPEN** | SLO/recovery/backup-restore/security/real production evidence not established |
| warning/deprecation debt | **P2 / CHARACTERIZE LATER** | separate bounded matrix required; not mixed into #343 |

This matrix is status reconciliation, not a claim that an omitted historical finding is
resolved. Any older finding outside this bounded inventory must be rechecked before it is
used as current truth.

### Why `project_state.json` is intentionally unchanged

`docs/state/project_state.json` schema v7 is a governed machine record whose repository
SHA fields are explicitly bound to the Continuity bounded-observation canary checkpoint.
Neither #335, #341, #344 nor this work-log correction changes Continuity completion,
schema, current enablement, Operator GO, runtime authority, production authority or the
canary semantics represented there. Changing that file merely to mirror the latest
documentation SHA would therefore create a false semantic mutation.

### Risk surface intentionally unchanged

`docs/ai/KNOWN_RISKS.md` already states the current #249 characterization, solo-governance
risk, no current Operator GO, production-readiness gap and other durable residuals. The
transient public-documentation drift is a current-truth reconciliation concern rather than
a new long-lived runtime risk entry.

---

## 2026-08-15 — #53 Phase 3A embedding-space identity · IMPLEMENTED_BOUNDED / POST-MERGE VERIFIED

```text
admission / closure issue:        #327
implementation PR:                #328 · MERGED
final accepted PR head:           96f4aad2ae4a65203cc133dbe2af40ed869c99e8
protected squash merge/main:      4932727c348ec967564d8babf80e25ca82bce8be
implementation parent:            86ed963d2d31b9da174c88f0cf05cc27faced2b9
merge signature:                  VERIFIED / valid
exact-head Full CI:               #1210 · 31882948349 · SUCCESS
exact-head Docker:                #799  · 31882948356 · SUCCESS
exact-head CodeQL:                #48   · 31882948357 · SUCCESS
READY aggregate:                  #1315 · 31883253917 · SUCCESS
post-merge Full CI:               #1211 · 31883324866 · SUCCESS
post-merge Docker:                #800  · 31883324890 · SUCCESS
post-merge CodeQL:                #49   · 31883324957 · SUCCESS
post-merge aggregate:             #1316 · 31883324900 · SUCCESS
submitted reviews:                0
review threads:                   0
PR comments:                      0
Continuity:                       12/12
schema:                           v7
runtime enabled:                  false
Operator GO:                      false
runtime authority:                false
production authority:             false
Canon:                            local
remote Canon:                     forbidden
```

Fresh live admission under parent #53 confirmed that Titan already had an embedding
registry, persistent vector store, rebuildable projection contract and legacy on-demand
DenseRetriever. The real gap was not missing embeddings but missing complete semantic-space
identity across those owners.

Phase 3A evolved the existing `core/embedding_registry.py` instead of creating a second
registry/store. `EmbeddingSpaceDescriptor` binds provider, model, model revision, dimension,
normalization, pooling, distance metric, chunker version and preprocessing version.
Canonical JSON + SHA-256 produces deterministic `embedding-space-v1:<digest>` identity;
equal dimensions alone never imply compatibility.

The existing projection/storage TEXT identity axis is reused, so project schema remains
v7. Historical plain-model rows lack complete typed metadata and fail closed to lexical
fallback rather than being auto-reused.

A separate correctness trap was closed in `DenseRetriever.retrieve()`: the complete
candidate batch is dimension-validated against the query before any similarity
multiplication. Python `zip()` can therefore no longer silently truncate unequal vectors
and yield a dense score.

Focused Phase 3A tests prove all nine identity axes, deterministic hashing,
same-dimension incompatibility, existing storage reuse, legacy fail-close, erasure
preservation, pre-score mismatch rejection and normal equal-dimension scoring. Full CI
also passed blocking mypy, full pytest, coverage ratchet ≥74%, dependency audit,
reproducible wheel, deterministic SBOM and architecture/project-state/KB guards.

The implementation is deliberately **UNWIRED / NOT ENABLED**. It did not change
`pipeline.py`, activate persistent projection, invoke/probe providers, enable network or
remote embeddings, add background indexing, mutate Canon/ESM, grant Operator GO, runtime
authority or production authority. No semantic retrieval-quality claim is made.

The existing Notion `Velantrim Titan 9.0` page was synchronized to the final PR candidate
and read back before Ready. After implementation merge, Issue #327 was temporarily reopened
so documentation/Notion lifecycle could be reconciled before final `CLOSED_COMPLETED`.

---

## 2026-08-14 — #52 C8 closed → C9 World Skills admission · IN PROGRESS

```text
C8 protected squash main:         1909e3f10330c4032641970ad0934a67649681e3
C8 signature:                     VERIFIED / valid
C8 post-merge Full CI:            #1170 · 31829982550 · SUCCESS
C8 post-merge Docker:             #769 · 31829982337 · SUCCESS
C8 post-merge CodeQL:             #8 · 31829982439 · SUCCESS
C8 post-merge aggregate:          #1171 · 31829982414 · SUCCESS
C9 tracking PR:                   #320 · DRAFT
C9 branch:                        agent/issue-52-world-skills-admission
C9 base:                          1909e3f10330c4032641970ad0934a67649681e3
C9 exact candidate head:          RESOLVE LIVE — changes still under review
C9 Notion DRAFT/read-back:        SYNCED
parent #52:                       OPEN
Continuity:                       12/12
schema:                           v7
runtime enabled:                  false
Operator GO:                      false
runtime authority:                false
production authority:             false
Canon:                            local
remote Canon:                     forbidden
```

Fresh #52 audit after C8 confirmed that World Skills remained a real current residual,
not stale issue prose. `core/world_skills_ingest.py` directly called
`promote_to_validated()` for curated rows; the parser did not expose the complete #52
provenance/risk/review metadata contract; the focused ingest test explicitly expected
legacy rows to auto-validate; and the promotion ownership inventory already documented the
route as a `KNOWN_EXCEPTION` requiring separate convergence.

C9 is therefore bounded to that exception. The candidate does **not** weaken TruthGate or
create a second Canon owner. It introduces explicit candidate metadata:

```text
truth_status
source_refs
confidence
risk_domain
limitations
review_status
reviewer
reviewed_at
```

Legacy rows receive safe non-claims and remain quarantined. The proposed admission chain is:

```text
Draft
→ Quarantine
→ Provenance Check
→ Domain Review
→ existing TruthGate precheck
→ legal ESM ladder to Supported
→ existing PromotionGateway
→ existing validate_and_promote()
→ TruthGate recheck + CAS
→ Validated / local Canon
```

A high-risk candidate selects the existing `PRECISION` mode; ordinary explicit risk uses
existing `BALANCED`. Numerical truth/evidence thresholds remain entirely TruthGate-owned.
Candidate and pack SHA-256 identifiers provide deterministic replay/content binding, not
cryptographic reviewer authentication.

Focused candidate tests cover legacy quarantine, successful reviewed low-risk admission,
high-risk TruthGate rejection, self-review rejection and order-independent/content-bound
pack identity. `tests/test_promotion_ownership_guard.py` removes World Skills from the
reviewed direct-promotion allowlist, so a reintroduced business-level bypass fails CI.

C9 also reconciles the promotion ownership inventory, the World Skills authoring/source
rules, ADR and operator documentation. The existing Notion `Velantrim Titan 9.0` page has
a C9 DRAFT checkpoint and was read back. No FINAL/merge claim is made yet: exact-head Full
CI, Docker, CodeQL, review/race audit, Ready aggregate, protected merge, post-merge evidence
and FINAL GitHub/Notion reconciliation remain required.

---

## 2026-08-13 — Phase 2A capability registry · FINAL / POST-MERGE VERIFIED

```text
implementation main:             c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
documentation closure main:      840b5aa231fe7d8cc0383c072ad953ca9bf4f46a
main signature:                   VERIFIED / valid
#50:                              CLOSED_COMPLETED · final REAL_GAP=0
#53:                              OPEN
#299:                             CLOSED_COMPLETED
#300:                             MERGED
#301:                             MERGED
#300 final tested head:           f0b893bac1b6fe1f58a71c70ac631f3c14becb59
#300 protected squash merge:      c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
#301 exact docs head:             b1376ac74c713773fa1fd6fd723bb05d53490bd1
#301 protected squash merge:      840b5aa231fe7d8cc0383c072ad953ca9bf4f46a
pre-merge Full CI:                #1105 · 31735939941 · SUCCESS
pre-merge Docker:                 #723 · 31735939929 · SUCCESS
READY aggregate:                  #981 · 31736858130 · SUCCESS
post-merge Full CI:               #1106 · 31736925690 · SUCCESS
post-merge Docker:                #724 · 31736925695 · SUCCESS
post-merge aggregate:             #982 · 31736925705 · SUCCESS
#301 exact-head Full CI:          #1107 · 31737790013 · SUCCESS
#301 READY aggregate:             #987 · 31738384462 · SUCCESS
#301 post-merge Full CI:          #1108 · 31738432888 · SUCCESS
#301 post-merge aggregate:        #988 · SUCCESS
Codex review:                     NOT RUN — USAGE LIMIT
independent formal approval:      NONE / NOT CLAIMED
Continuity:                       12/12
schema:                           v7
runtime enabled:                  false
Operator GO:                      false
runtime authority:                false
production authority:             false
```

Phase 2A was admitted through #299 after the #297/#298 foundation and public-truth closure.
It is implemented and protected-merged through #300, with the public documentation closure
completed through #301 and tracking issue #299 subsequently closed as `CLOSED_COMPLETED`.
The registry remains deliberately **UNWIRED / NOT ENABLED**. No provider/model/network call
path was activated.

### Implemented bounded owner

`core/capability_registry.py` now provides a process-local metadata contract for:

- stable `ProviderDescriptor` and `CapabilityDescriptor` identity;
- capability-specific declared `data_mode`;
- explicit `ProviderHealth` states: UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE;
- deterministic candidate selection/no-selection;
- separate health and policy/selection reason codes;
- trace-ready selection metadata without TRACE persistence.

The existing process-wide `PolicyKernel` remains the sole permission owner. Production
`CapabilityRegistry()` has no policy/leaser injection parameter and always resolves the
owner through `get_policy_kernel()`. Every HEALTHY/DEGRADED candidate must receive an
existing PolicyKernel lease; explicit preference and `auto` cannot reinterpret a denial.

### Authority-bypass hardening

Self-review found an early constructor-injection surface that would have allowed a future
caller to substitute an arbitrary leaser. That was treated as a blocking authority defect
and removed before Ready. Tests patch `get_policy_kernel()` only inside the test process;
there is no production alternate-policy extension point.

Additional fail-closed boundaries include malformed typed metadata, remote provider
metadata that hides network requirements, unknown/unavailable health, PolicyKernel
exceptions and mixed policy snapshot/version values during one selection pass.

### Review and governance evidence

A Codex review request on ancestor head `009e5fbc11b03fd4033c939ae04ff0a8835e797b`
returned `NOT RUN — USAGE LIMIT`. This is neither approval nor a finding. The active solo
ruleset requires zero approving reviews, review-thread resolution and the
`Titan aggregate merge evidence` status check; no independent review is claimed.

The first Ready aggregate (#980) failed only because the PR-body Notion lifecycle token did
not use the validator's accepted `SYNCED` value. The existing Notion page had already been
updated and read back. PR metadata was corrected without changing the exact head; fresh
Ready aggregate #981 then succeeded.

### Documentation closure

The implementation merge left review-stage language in public AI context files. Docs-only
PR #301 reconciled those truth surfaces without touching `core/**` or changing Phase 2A
behavior. It protected-merged as
`840b5aa231fe7d8cc0383c072ad953ca9bf4f46a`; its exact-head Full CI #1107 and Ready
aggregate #987 succeeded, followed by post-merge Full CI #1108 and aggregate #988. No
Docker run was spawned for docs-only #301, so no Docker success is claimed for it. The
existing `Velantrim Titan 9.0` page was synchronized/read back, and issue #299 was then
closed with state reason `completed`.

---

## 2026-08-13 — #297 / #298 foundation closure · FINAL

```text
#297 hardening merge:            c96b734b94f30e1d96e8bcb992dec429bda5c8fd
#297 review threads:             13/13 RESOLVED
#297 READY aggregate:            #914 · 31725868065 · SUCCESS
#297 post-merge Full CI:         #1085 · 31725945373 · SUCCESS
#297 post-merge Docker:          #705 · 31725945362 · SUCCESS
#298 truth reconciliation merge: 51058f2d5662edfdb91b037a46dce9297c441a1b
#298 exact-head Full CI:         #1086 · 31729146690 · SUCCESS
#298 READY aggregate:            #920 · 31729778909 · SUCCESS
#298 post-merge Full CI:         #1087 · 31729908579 · SUCCESS
#298 post-merge aggregate:       #921 · 31729908264 · SUCCESS
```

---

## Stable authority boundary

```text
Continuity:             12/12
schema:                 v7
runtime enabled:        false
Operator GO:            false
runtime authority:      false
production authority:   false
Canon:                  local
remote Canon:           forbidden
Phase 3B:               NOT ADMITTED / NOT STARTED
```

Phase 2A and #52 hardening do not authorize embeddings/vector execution, reranker/LLM
execution, ADAO, ARM-04, provider probing/invocation, remote consent implementation,
network activation, runtime route replacement, runtime enablement, Continuity 13/12 or
schema v8.

Phase 3A adds a tested embedding-space identity / dimension-safety contract only. It does
not authorize persistent projection live retrieval, embedding provider execution,
background semantic indexing, semantic-quality claims or Phase 3B.

Phase 2A closure sequence completed:

```text
#301 exact-head CI SUCCESS
→ same-page Notion sync + read-back
→ Ready aggregate #987 SUCCESS
→ protected docs merge 840b5aa231fe7d8cc0383c072ad953ca9bf4f46a
→ post-merge Full CI #1108 SUCCESS
→ post-merge aggregate #988 SUCCESS
→ FINAL Notion read-back
→ #299 CLOSED_COMPLETED
```

CSM Stage C adds a tested structural scanner lifecycle only. It remains unwired,
not enabled and non-canonical. PR #341 hardens only the ownership lifecycle of the existing
multilingual retrieval wrapper. Neither grants runtime or production authority.
