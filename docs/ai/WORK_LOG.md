# 🧾 AI Engineering Work Log

Re-verify exact SHAs and current PR evidence.

---

## 2026-08-06 — Documentation checkpoint after PR #229 and PR #230

```text
Documentation impact: GITHUB_AND_NOTION
Verified main:        81836b4f715470c50a4c6c7768a2cde7478568c8
Code changes:         NONE
Runtime authority:    NONE
Notion state:         already synchronized with both merges
GitHub state before:  stale at the post-contract checkpoint
```

### Intent

Restore one coherent canonical record after the State Draft adapter and Goal
subject-binding correction were merged without the four primary GitHub AI
context documents being advanced to the final `main` state.

### Problem

Notion already recorded PR #229 and PR #230, but GitHub still stated:

- State Draft adapter `0/1`;
- Goal subject-binding correction `0/1`;
- Goal results lose subject identity;
- the next safe slice is the State adapter.

That drift could cause a new AI agent to repeat merged work, design from a
superseded eligibility matrix, or over-read the repository before locating the
real current boundary.

### Decision

Create a separate docs-only Draft PR before any OpenLoop code work. Update the
public GitHub technical record to match verified `main` and the already current
Notion pages. Do not combine documentation repair with OpenLoop schema changes,
an adapter, admission runtime, or wiring.

### Implementation

Updated:

- `docs/ai/CURRENT_STATE.md`;
- `docs/ai/COMPONENT_MAP.md`;
- `docs/ai/KNOWN_RISKS.md`;
- `docs/ai/WORK_LOG.md`;
- `docs/ai/CONTINUITY_SOURCE_ADMISSION_HANDOFF.md`.

The checkpoint records the accepted #223–#230 lineage, exact heads and CI,
State/Goal guarantees, OpenLoop subject-binding gap, retry caveat, privacy and
erasure blockers, and the next safe implementation boundary.

### Evidence

```text
Current main                         81836b4f715470c50a4c6c7768a2cde7478568c8
PR #229 exact tested head            aecea098ab5e3fba0539a044a77ababe32067b79
PR #229 Continuity contracts         31093141984 PASS
PR #229 Full Titan CI                31093142993 PASS
PR #229 Docker hardening             31093142155 PASS

PR #230 exact tested head            995b1a846b8f3d35c07f103430a6f6b1db007cca
PR #230 Continuity contracts         31106174878 PASS
PR #230 Full Titan CI                31106175347 PASS
PR #230 Docker hardening             31106174460 PASS
PR #230 unresolved review threads    0
```

PR #229 had an earlier unrelated erasure-recovery concurrency failure during a
coverage-instrumented run. The exact unchanged head passed on retry. The first
failure remains documented as risk evidence; the retry is not described as an
unconditional first-attempt pass.

### Non-scope

- no production code;
- no OpenLoop subject-binding implementation;
- no Goal or OpenLoop source adapter;
- no admission evaluator or facade;
- no privacy/restriction/erasure integration;
- no persistence, public export, `/query`, startup, worker or scheduler;
- no feature flag, activation, Canon, TruthGate, reminder, tool or action authority.

### Remaining work

1. Merge this documentation checkpoint after exact-head review and CI.
2. In a separate PR, correct OpenLoop subject identity only.
3. Keep Goal/OpenLoop adapters in later independent PRs.
4. Implement admission, current authorization and privacy/erasure checks before
   any runtime-capable facade.
5. Require a separate activation ADR and operator approval before enablement.

### Resulting status

```text
Documentation: synchronized in this Draft branch
State adapter: IMPLEMENTED · TESTED · INTERNAL · UNWIRED
Goal binding:  IMPLEMENTED · TESTED · INTERNAL · UNWIRED
OpenLoop bind: NOT IMPLEMENTED
Runtime:       NOT WIRED · NOT ENABLED · NOT OBSERVED
Live readiness: 3/12 = 25%
```

---

## 2026-08-06 — State Draft adapter and Goal subject binding merged

### Intent

Advance source-admission prerequisites without granting runtime authority:

1. produce deterministic proposal evidence from a fully bound State result;
2. preserve Goal subject ownership inside immutable projection evidence.

### Problem

State results had typed subjects but no accepted Draft adapter. Goal snapshots
contained `user_id`, but Goal projections and result identity lost that subject,
blocking reliable source authorization.

### Decision

- Keep the State adapter a deterministic proposal transformer, separate from
  admission evaluation.
- Reject incomplete or mismatched State subject sets as a whole; never silently
  filter unauthorized subjects.
- Correct the Goal schema rather than adding placeholder defaults for old
  constructors.
- Put subject identity into the evidence object and its content-addressed
  identity.
- Preserve `INTERNAL · UNWIRED · NO RUNTIME AUTHORITY`.

### Implementation

#### PR #229 — State Draft adapter

Merge: `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1`

Added `core/continuity/state_source_adapter.py` and adversarial tests.
The adapter validates canonical result/projection identities, complete subject
binding, source digest, policy, chronology and evidence before producing a
`ContinuitySourceEnvelope` and bounded Draft proposals for:

- `context_degraded`;
- `active_contradiction`;
- `context_freshness`.

#### PR #230 — Goal subject binding

Merge: `81836b4f715470c50a4c6c7768a2cde7478568c8`

Advanced Goal projection schema to `continuity.goal_projection.v2` and made
`user_id` explicit through:

```text
GoalAttestation
→ GoalProjection
→ GoalProjectionDecision
→ GoalProjectionResult.subject_ids
→ result digest
```

Cross-subject attestations fail closed. Multi-subject results remain explicit
and content-addressed. Direct advisory, shadow-runner and WorkingMemory test
fixtures were migrated rather than weakening the production contract.

### Evidence

Both exact final heads passed Continuity contracts, Ruff, blocking mypy, full
pytest, the blocking `core ≥74%` coverage ratchet and Docker hardening. Exact
workflow IDs are recorded in the preceding checkpoint entry and
`CURRENT_STATE.md`.

### Non-scope

PR #229 did not create an admission decision, batch, producer call, persistence
or runtime route. PR #230 did not create a Goal adapter. Neither PR changed
Canon, TruthGate, compute routing, answers, reminders, tools or actions.

### Remaining work

- OpenLoop subject binding;
- Goal source adapter;
- OpenLoop source adapter;
- admission evaluator and evaluator/rule allowlist;
- current authorization, consent, restriction and erasure checks;
- admission-aware facade;
- runtime wiring, enablement and observed evidence.

### Resulting status

```text
State adapter                   IMPLEMENTED · TESTED · UNWIRED
Goal subject binding            IMPLEMENTED · TESTED · UNWIRED
OpenLoop subject binding        NOT IMPLEMENTED
Goal/OpenLoop adapters          NOT IMPLEMENTED
Admission/runtime authority     ABSENT
Continuity live readiness       3/12 = 25%
```

---

## 2026-08-06 — Trusted Continuity Signal Producer (merged and hardened)

```text
Status:        IMPLEMENTED IN MAIN · SHADOW ONLY · NOT WIRED · NOT ENABLED
Implementation: PR #214 → 5f1ce06199ebabd6a23f3656ddd91c5c968170fe
CI isolation:  PR #218 → 3c73eab991c305d174f6c2c5805595c7998d4068
Hardening:     PR #220 → e37a5d13332628bcdbd0d9441d7a61d5f8a8d523
ADR:           docs/adr/ADR-2026-08-05-continuity-trusted-signal-producer.md
```

Addresses the "no trusted producer for `ContinuityComputeSignals`" gap
restated at R4, R5A, and R5B by adding `core/continuity/observations.py` and
`core/continuity/signal_producer.py`: typed, content-addressed
`ContinuitySignalObservation` inputs → policy-driven trust filtering →
deterministic aggregation → the unchanged `ContinuityComputeSignals`
contract, with full per-signal provenance and reason-coded rejections.

This PR does not import `core.evidence`, `core.confidence`,
`core.contradiction_registry`, or `core.provenance_chain` (isolation
decision, see ADR); does not change `ComputePath`, `ComputeDecision`,
`decide_compute_path()`, `ContinuityComputeSignals`, or
`assess_compute_with_continuity()`; and performs no runtime wiring into
`/query`, the shadow runner, or any live projection.

### Final validation checkpoint

The complete merged lineage passed exact-head review and validation:

```text
PR #214 implementation merge  5f1ce06199ebabd6a23f3656ddd91c5c968170fe
PR #218 CI isolation merge     3c73eab991c305d174f6c2c5805595c7998d4068
PR #220 hardening merge        e37a5d13332628bcdbd0d9441d7a61d5f8a8d523

PR #220 focused run            31077257141 → Ruff · mypy · 108 tests PASS (temporary workflow, not retained)
PR #220 Full Titan CI          31077329680 → PASS
PR #220 Continuity contracts   31077329650 → PASS
PR #220 Docker hardening       31077329644 → PASS
Copilot final review                         4/4 files · 0 comments
Unresolved review threads                    0
```

The merged producer verifies canonical observation IDs, rejects malformed
references and tampered content fail-closed, preserves trusted-negative and
duplicate-scope provenance, and emits controlled errors for malformed
categorical values.

### Next phase

Still not authorized by the merged lineage: production runtime wiring,
trusted runtime source adapters deriving observations from
`StateReconciliationResult` / `GoalProjectionResult` /
`OpenLoopProjectionResult`, live telemetry, automated policy tuning, Canon
authority, Action Gate authority, autonomous switching, or real-world
calibration. Those require separate architecture, privacy/consent boundaries,
staged activation and live evidence.

---

## 2026-08-05 — Governance cleanup and truthful CI completed

Claude Code correctly identified the open-PR count, ARM-03 recovery and documentation merges, but its proposed bulk classification of eight old PRs as disposable was not safe. Every PR was inspected against current `main`, changed files, review findings and fresh CI.

### Closed without merge

| PR | Disposition |
|---:|---|
| #10 | unsafe generated KB artifact; confirmed trust-label, graph-connectivity and parser defects |
| #20 | superseded by stronger current budget-signal integration |
| #22 | superseded by the accepted repository hygiene guard |

### Recovered before closing historical branches

| Historical PR | Current replacement/result | Merge SHA |
|---:|---|---|
| #1 | clean Titan 9 cosmetic cleanup via #209 | `e6d6002eaf6e771f13d5842db4f083512e0fc0bc` |
| #21 | fail-closed production bundle contract via #210 | `5d4881e6ab1414b3917eb225c55e0f02458af27a` |
| #19 | measured blocking coverage ratchet via #211 | `c7ad5a171ccc6da5015b67b8cefd6d60649d6792` |

Historical #1, #21 and #19 were then closed as superseded. Their stale branches were not merged.

### Useful old PR accepted directly

PR #58 was revalidated on current `main` and merged as `b9847f0599092ef5eef78d698b58b92ace2eaf98`. It adds tests for emergency `prevent_fact_delete` trigger reconstruction, original-error preservation, exception chaining and restored guard enforcement.

### Coverage evidence

Final coverage head: `6f314ae94bcd731b27d90959fc995852c1312a0a`.

- full CI run `31046470206` — success;
- Docker hardening `31046469060` — success;
- `43,398` executable statements;
- `11,233` missed;
- approximately `74.12%` covered;
- blocking floor `74%`;
- coverage suite: `3,364 passed`, `17 skipped`, `18 deselected`, `1 xfailed`;
- coverage XML artifact `8946843485` retained for 14 days.

The per-thread trace-hook bootstrap stress test remains blocking in normal full pytest but is excluded from simultaneous `coverage.py` tracing because both systems install trace hooks and interfere.

### Remaining open PRs

Exactly four PRs remain open, all intentionally retained architecture/research drafts:

- #17 — Ring Zero recovery research;
- #30 — Code Structural Memory Adapter RFC;
- #33 — epistemic/cognitive runtime specification requiring current-doc reconciliation;
- #43 — LearningPatch shadow contract requiring RFC-0084/governance reconciliation.

Do not bulk-close or directly merge these stale branches.

### Corrected architecture status

- `core/identity_layer.py` is already formally quarantined as `LEGACY/UNWIRED` by current AI context and mandatory repository guidance;
- RFC-0084 remains Proposed, unwired and forbidden from Canon writes;
- projection dispatcher remains implemented/tested but not connected to production startup/runtime.

---

## 2026-08-05 — Continuity Milestone 1 recovery completed

The historical #131–#147 stacked sequence was replaced by independently reviewed recovery PRs on current `main`:

| Recovery | PR | Merge SHA |
|---|---:|---|
| R1 immutable foundation | #201 | `06529700d70854504b88629eeecf737bdc6b81d5` |
| R2 shadow read-side and threads | #202 | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` |
| R3 projections and WorkingMemory adapters | #203 | `a19d16656676ad5c98c92d4776e9709edbfb920c` |
| R4 compatible compute assessment | #204 | `529d8b6b182b1a548d27558173f0aca473bcc400` |
| R5A replay gates and Advisory Shadow | #205 | `58e29bba26299ce7003b62e73fd3b25e028956de` |
| R5B disabled complete shadow runner | #206 | `27b91a59f9e9291092b220ac1f53bfeae2daea28` |

### Final R5B evidence

- final tested head: `8517c0d909b1e3465528f0bcc115265d8c1d1024`;
- Continuity run `31025608097` — success;
- full Titan CI `31025605121` — success;
- Docker hardening `31025606554` — success;
- independent final-head review completed;
- historical #147 closed without merge.

### Final architecture state

Milestone 1 exists as a complete, deterministic, in-memory shadow composition. It is disabled by default, not connected to startup or `/query`, and has no persistence, Canon, answer, delivery, tool or action authority.

---

## 2026-08-05 — ARM-03 selective-memory recovery

PR #200 merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`; old #102 closed as superseded. The extractor remains proposal-only, default-off and unwired.

## 2026-08-05 — Documentation continuity governance

- PR #199 merged the mandatory GitHub ↔ Notion synchronization contract;
- PR #196 merged Project Cognition as research/proposed documentation;
- PR #198 merged the compact AI context pack.
