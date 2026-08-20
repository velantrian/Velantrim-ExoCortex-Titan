# 🔗 Notion synchronization hand-off queue

This file preserves a complete, public transfer package when an AI agent or contributor
can work in GitHub but cannot access the Titan Notion workspace.

A missing Notion connector is **not** a reason to abandon an audit, implementation, or
review. GitHub must remain sufficient to understand the technical state, verify evidence,
and continue the work.

## Access and synchronization states

| State | Meaning | Required action |
|---|---|---|
| `NOTION_AVAILABLE` | The current actor can read and update the intended Notion record | Synchronize GitHub and Notion in the same work cycle |
| `HANDOFF_REQUIRED` | The current actor cannot access Notion | Complete the GitHub record and add a structured item below |
| `SYNCED` | A connected human or AI verified the GitHub evidence and updated Notion | Record the safe Notion title/reference and final evidence |
| `NOT_REQUIRED` | The change is correctly classified as GitHub-only | State the reason in the PR |
| `BLOCKED_PRIVACY_OR_PERMISSION` | A real privacy, permission, or unresolved-target problem prevents safe synchronization | Keep the PR draft and escalate the exact blocker |

`HANDOFF_REQUIRED` is the normal connectorless state. Do not use
`BLOCKED_PRIVACY_OR_PERMISSION` merely because a connector is absent.

## GitHub completeness invariant

The following may never exist only in Notion:

- implemented behavior or a changed technical contract;
- a material audit or review finding;
- a known engineering, privacy, security, or authority risk;
- exact PR, commit, test, CI, benchmark, or runtime evidence required for review;
- an architectural decision that changes implementation direction;
- a required engineering next action or unresolved blocker.

GitHub and Notion do not need sentence-for-sentence duplication. GitHub carries the
complete public technical and audit package. Notion carries deeper rationale, rejected
alternatives, roadmap, cross-project context, and historical evolution. Both must retain
the same decision-bearing facts, exact status, evidence, limitations, and next actions.

## Connectorless actor procedure

1. Continue the audit or implementation from GitHub.
2. Update the affected technical documents and the relevant files under `docs/ai/`.
3. Record exact base/head SHA, PR or issue, tests, CI, limitations, and next actions.
4. Add a hand-off item below for work classified `GITHUB_AND_NOTION`.
   New pending items must use the machine-stable level-2 heading
   `## handoff-pr-<PR-NUMBER>` so the aggregate validator can bind the item to the
   current pull request without guessing GitHub-generated title slugs.
5. Set the PR fields to:
   - `Notion access: UNAVAILABLE`;
   - `Notion synchronization: HANDOFF_REQUIRED`;
   - `GitHub hand-off path: docs/ai/NOTION_HANDOFF.md#handoff-pr-<PR-NUMBER>`.
6. Never claim that Notion was updated.
7. Keep an implementation or architectural PR draft until a connected actor verifies
   the evidence and records `SYNCED`.

Documentation-only work may be reviewed according to repository policy, but its Notion
status must still remain explicit and truthful.

## Connected actor procedure

1. Verify the hand-off against the current PR, exact SHA, repository state, tests, and CI.
2. Create or update the intended Notion record.
3. Preserve the problem, decision, alternatives, boundaries, evidence, limitations, and
   next actions.
4. Add a safe Notion title or internal reference to the PR and this item.
5. Change the item status to `SYNCED`.
6. After merge, add the final merge SHA, final CI evidence, deviations from the original
   plan, and remaining work.

## Privacy boundary

Titan is public. Do not copy private workspace notes, personal information, secrets,
private datasets, inaccessible URLs, or private cross-project material into this file.
Use a safe page title or internal reference when the Notion URL must remain private.

## Hand-off item template

Copy this section for each pending synchronization and place new items above older ones.

```markdown
## handoff-pr-<PR-NUMBER>

### YYYY-MM-DD — Short title

- **Status:** `HANDOFF_REQUIRED` / `SYNCED` / `BLOCKED_PRIVACY_OR_PERMISSION`
- **Documentation impact:** `GITHUB_AND_NOTION`
- **Repository / PR / issue:**
- **Base SHA:**
- **Head SHA:**
- **Intended Notion record:** safe title or internal reference
- **Notion access for originating actor:** `UNAVAILABLE`

### Problem / opportunity

### Material findings

### Decision and rationale

### Rejected or deferred alternatives

### Authority, safety, privacy, and Canon boundaries

### GitHub files updated

### Evidence

### Known limitations

### Next actions

### Synchronization result

- Connected actor:
- Notion record:
- Status: `SYNCED`
- Final PR / merge SHA / CI:
```

For `UNAVAILABLE + HANDOFF_REQUIRED`, the merge-evidence gate reads this file from the
**exact PR head** and fails closed unless the declared path is exactly
`docs/ai/NOTION_HANDOFF.md#handoff-pr-<current-PR>`, this file is changed by that PR,
and the matching item contains the current PR reference, current base SHA, a full head SHA,
the intended Notion record, `UNAVAILABLE` origin access, and the required structured
sections. Existing historical items keep their original headings; only new pending items
need the machine-stable `handoff-pr-<PR-NUMBER>` heading.

## Queue

## handoff-pr-355

### 2026-08-19 — Typed Evidence Reference v1 Contract

- **Status:** `SYNCED` (historical checkpoint; live GitHub governs current head)
- **Documentation impact:** `GITHUB_AND_NOTION`
- **Repository / PR / issue:** `velantrian/Velantrim-ExoCortex-Titan` · PR #355
- **Base SHA:** `588ffe61c711f6e63ac42cc304d95642a0671b08`
- **Head SHA:** `8a1b3aab56c2aeaa5050872b660aed6fc9df40db` (historical)
- **Intended Notion record:** `Titan Typed Evidence Reference v1 — Trusted Independence Contract · 2026-08-19`
- **Notion access for originating actor:** `UNAVAILABLE`

### Current lifecycle truth — 2026-08-20 contract hardening

This remains a **Draft, contract-only, unwired local-validation prototype**. The current
checkpoint hardens canonical ASCII span and RFC3339 UTC timestamp input, controlled error
taxonomy, malformed input rejection and local outcome/receipt structure only. It adds no
evidence admission decision, target evidence adapter, owner integration, policy snapshot,
OBSERVE/VERIFY/ENFORCE runtime mode, TruthGate/WriteGate/PromotionGateway integration,
persistence, migration, route, worker, feature flag, telemetry pipeline, runtime enablement
or authority.

`validated_reference_count` is diagnostic local validation cardinality only. It is neither
evidence sufficiency nor a runtime input. The receipt contains no independence result and is
not authentication, admission, truth or promotion authorization. Titan remains a supplied
local resolver/prototype, not an evidence sovereign.

### Problem / opportunity

Legacy `metadata.evidence_refs` uses raw strings. It measures cardinality but cannot prove source identity, fragment integrity, lineage, or independence, making it inadequate for a strict TruthGate admission boundary.

### Material findings

The existing TruthGate logic currently accepts string arrays without validation. Changing
it directly would break compatibility. Review of the first prototype also found that its
producer-owned `EvidenceReference.independence_class` could increase the effective lineage
count. That would let a source participate in granting itself evidentiary independence.

### Decision and rationale

Introduce `EvidenceReference` and an in-memory `EvidenceRegistry` as an unwired,
local-only Python prototype. Remove independence classification from the producer
reference and do not create a registry-owned replacement. The local receipt contains no
effective-independence result because that semantic belongs to a future separately
authorized evidence owner. The contract enforces strict schema, canonical digests,
canonical ASCII spans, canonical RFC3339 UTC timestamps, deterministic ordering,
structurally valid outcomes/receipts and fail-closed conflicting-ID handling. It does not
change TruthGate thresholds, ingestion, persistence or promotion.

### Rejected or deferred alternatives

- Do not auto-convert legacy string facts.
- Do not persist the registry without a separate data classification decision.
- Do not attach the receipt to TruthGate yet.
- Do not synthesize digests for missing data.
- Do not retain a producer `claimed_independence_class` in v1 without a demonstrated
  observe-mode need; it can be introduced later only as explicitly untrusted metadata.

### Authority, safety, privacy, and Canon boundaries

This is a **contract-only increment**. It does NOT change `TruthGate` outcomes,
`metadata.evidence_refs`, canonical promotion, SQLite schema, network/provider behavior or
runtime authority. `EvidenceItem` remains the separate scoring owner. The in-memory Titan
registry is a supplied resolver/prototype, not a second global evidence Canon and not a
replacement for a separately authorized evidence-admission authority. Local validation is
not admission; a local receipt is not a bounded policy result, authority or objective truth.

### GitHub files updated

- `core/evidence_reference.py`
- `core/evidence_registry.py`
- `tests/test_evidence_reference.py`
- `docs/adr/ADR-2026-08-19-typed-evidence-reference-contract.md`
- `docs/ai/COMPONENT_MAP.md`
- `docs/ai/KNOWN_RISKS.md`
- `docs/ai/WORK_LOG.md`
- `docs/ai/NOTION_HANDOFF.md`

### Evidence

- 25 focused contract tests passed locally after the effective-independence correction.
- The combined EvidenceReference/Evidence authenticity/TruthGate suite passed 55 tests.
- Repository-wide Ruff and Mypy passed for all 332 `core/` source files; branding,
  tracked-artifact, project-state and KB-integrity guards passed.
- The local Python 3.12 suite completed (with one separately reproduced baseline test
  excluded) at 4 failed, 4,323 passed, 17 skipped, 1 deselected and 1 xfailed. That
  excluded failure and all four completed-run failures were each reproduced against
  unchanged `main@588ffe61` in the same environment. This is baseline/environment
  characterization, not a waiver or exact-head CI evidence.
- Exact code-checkpoint GitHub evidence is green: Main CI #1325, Docker #872 and
  CodeQL #164 succeeded on `8a1b3aab56c2aeaa5050872b660aed6fc9df40db`.
- Aggregate evaluator run 32232797602 completed successfully; the combined status context
  remains `PENDING` while PR #355 remains a DRAFT.
- The dedicated Notion architecture record was created under the Titan hub and verified
  by read-back. Fresh final documentation-sync-head CI and review remain required.

### Known limitations

The prototype is in-memory and unwired. Its supplied registry snapshot is not an
authenticated authority merely because it is typed. Independence may be contextual; v1
therefore records no local independence result. Persistence, evidence-admission decisions,
OBSERVE/VERIFY/ENFORCE modes and producer migration require separate PRs, ownership
decisions and admission decisions.

### Next actions

1. Publish this repository-side synchronization checkpoint.
2. Verify fresh CI and aggregate evidence on the final documentation-sync head.
3. Re-read head/base, changed files, Notion and unresolved review threads.
4. Review/merge #355 only through a separate lifecycle decision.
5. Decide OBSERVE integration separately; do not proceed automatically to persistence.

### Synchronization result

- **Connected actor:** connected AI work cycle with GitHub + Notion access
- **Notion record:** `Titan Typed Evidence Reference v1 — Trusted Independence Contract
  · 2026-08-19` · page ID `3c1ac84d-0547-811f-8f81-ff62f45b659d`
- **Status:** `SYNCED` · read-back verified 2026-08-19
- **Final PR / merge SHA / CI:** PR #355 remains DRAFT and unmerged · code checkpoint
  `8a1b3aab56c2aeaa5050872b660aed6fc9df40db` · Main CI #1325 SUCCESS · Docker #872
  SUCCESS · CodeQL #164 SUCCESS · aggregate evaluator 32232797602 SUCCESS / combined
  context PENDING

## 2026-08-13 — PR #297 post-merge hardening final synchronization

- **Status:** `SYNCED`
- **Documentation impact:** `GITHUB_AND_NOTION`
- **Repository / PR / issue:** `velantrian/Velantrim-ExoCortex-Titan` · PR #297 · parent architecture #53
- **Base SHA:** `e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96`
- **Head SHA:** `9830212159b092af2b3867d52e02fc7aaa57afa1`
- **Intended Notion record:** `Velantrim Titan 9.0`
- **Notion access for originating actor:** `UNAVAILABLE`

### Problem / opportunity

The originating merge actor could complete GitHub review/merge work but could not access
Notion. It therefore used `UNAVAILABLE + HANDOFF_REQUIRED`. The PR body linked a public
risk file rather than creating the structured queue item required by this protocol, and
the aggregate validator accepted that weaker metadata form. A later connected actor had
to repair both the actual Notion synchronization and this missing public queue record.

### Material findings

- PR #297 is protected-squash merged as `c96b734b94f30e1d96e8bcb992dec429bda5c8fd`.
- Merge signature is `VERIFIED / valid`; parent is `e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96`.
- All 13 review conversations are resolved.
- Ready-state aggregate #914 / `31725868065` is SUCCESS.
- Post-merge Full CI #1085 / `31725945373` is SUCCESS.
- Post-merge Docker #705 / `31725945362` is SUCCESS.
- The fresh fourth Codex review returned `NOT RUN — USAGE LIMIT`; no approval is inferred.
- The connected work cycle updated the existing Notion page and verified read-back.

### Decision and rationale

Treat #297 as `MERGED + POST-MERGE VERIFIED` for its bounded causal/ModelFree hardening
scope. Preserve the original connectorless claim as truthful for that actor, but close the
lifecycle as `SYNCED` now that a connected actor independently verified the GitHub evidence
and updated the intended existing Notion record.

### Rejected or deferred alternatives

- Do not pretend the connectorless actor synchronized Notion.
- Do not create a new Notion page.
- Do not reinterpret green CI as independent approval.
- Do not fold Phase 2 implementation into this reconciliation.
- Harden the aggregate validator's hand-off-path verification only in a separate bounded
  governance workstream.

### Authority, safety, privacy, and Canon boundaries

Continuity remains 12/12; schema remains v7; runtime enabled remains false; current
Operator GO remains false; runtime authority remains false; production authority remains
false. Canon remains local and remote Canon remains forbidden. No ARM-04, ADAO,
embedding/LLM, provider/network or production activation is authorized by this sync.

### GitHub files updated

- `docs/ai/WORK_LOG.md`
- `docs/ai/KNOWN_RISKS.md`
- `docs/ai/NOTION_HANDOFF.md`

### Evidence

```text
PR #297 head:             9830212159b092af2b3867d52e02fc7aaa57afa1
merge/main checkpoint:    c96b734b94f30e1d96e8bcb992dec429bda5c8fd
signature:                VERIFIED / valid
review threads:           13/13 RESOLVED
READY aggregate:          #914 · 31725868065 · SUCCESS
post-merge Full CI:       #1085 · 31725945373 · SUCCESS
post-merge Docker:        #705 · 31725945362 · SUCCESS
```

### Known limitations

The #53 Phase 2 registry/provider gaps remain separate architectural work. Production
readiness, production-scale reset behavior, Reader Core production evidence (#120), CAS
contention (#249), ADAO (#51), trusted-platform work (#52) and ARM-04 (#92) are not closed
by #297.

### Next actions

1. Merge the bounded post-#297 documentation reconciliation after its own required evidence.
2. Re-read GitHub + the existing Notion page.
3. Decide Phase 2 admission separately under #53.
4. Track the aggregate-validator/hand-off-anchor mismatch as a separate governance residual.

### Synchronization result

- **Connected actor:** connected AI work cycle with GitHub + Notion access
- **Notion record:** `Velantrim Titan 9.0`
- **Status:** `SYNCED`
- **Final PR / merge SHA / CI:** #297 · `c96b734b94f30e1d96e8bcb992dec429bda5c8fd` · post-merge CI #1085 SUCCESS · Docker #705 SUCCESS
