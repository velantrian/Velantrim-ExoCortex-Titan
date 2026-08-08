# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.

This file keeps the recent operational hand-off compact. Older detailed entries remain traceable in Git history, merged PR descriptions and per-PR checkpoint documents under `docs/ai/`.

---

## 2026-08-08 — PR #247 post-merge canonical checkpoint finalized

```text
PR:                       #247
Merge SHA:                294bdfa6a77097e48310872a2e3fae811e8c2c9e
Full Titan CI + coverage: 31222680496
  Attempt 1:              FAILED · test_cas_contention[25] · BrokenBarrierError
  Attempt 2:              PASS · 3746 passed, 17 skipped, 1 xfailed
Aggregate push evidence:  31222680550 SUCCESS
Review threads:           0
Documentation impact:     GITHUB_AND_NOTION
Checkpoint:               docs/ai/PR247_ADMISSION_FACADE_POSTMERGE_CHECKPOINT.md (FINAL)
```

### Intent

Correct semantic drift after PR #247 merged: separate repository head, implementation
baseline and documentation checkpoint SHAs; record the correct post-merge CI incident;
mark the PR #247 checkpoint FINAL instead of DRAFT.

### Corrected incident identification

Post-merge attempt 1 failed in
`test_cas_contention_yields_exactly_one_winner_and_one_intent[25]` with
`threading.BrokenBarrierError`. This is an uncharacterized CAS-contention test failure,
not the fresh-bootstrap ADD COLUMN family and not the legacy embeddings-lock timeout
family. A green retry does not classify the root cause.

### SHA roles after correction

```text
repository_head_sha_at_verification: 294bdfa6a77097e48310872a2e3fae811e8c2c9e
implementation_baseline_sha:         9f07db6de8d32683d00bfe4f1673e84493607553
documentation_checkpoint_sha:        294bdfa6a77097e48310872a2e3fae811e8c2c9e
```

PR #248 later merged the FINAL docs correction as
`c14916214a920802c9ce6187be79ebe74ddfadfc`.

### Result

```text
Continuity readiness: 7/12 = 58.3% (unchanged)
Runtime:               NOT WIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY
```

### Next work

- CAS-contention characterization / stage diagnostics:
  [issue #249](https://github.com/velantrian/Velantrim-ExoCortex-Titan/issues/249),
  open draft [PR #250](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/250).
- Owner map and operator trust-root ADR: **no public PR or issue identifier assigned yet**;
  do not start until Phase I remediation PRs are rebased, reviewed and green.

---

## 2026-08-08 — PR #248 Codex P2 remediation (docs-only)

```text
Successor to:             #248 (merged as c14916214a920802c9ce6187be79ebe74ddfadfc)
Documentation impact:     GITHUB_AND_NOTION
Notion synchronization:   SYNCED (FINAL correction verified on Continuity page)
Runtime wiring:           no
Runtime authority:        no
```

Resolves the three open Codex P2 threads from PR #248:

1. FINAL correction Notion state recorded as verified `SYNCED` with page evidence;
2. private sequence labels replaced with public issue/PR references (#249, #250) or
   an explicit “no public identifier assigned” statement;
3. CAS incident reclassified as uncharacterized contention-test failure, not a proven
   harness-only flake.

---

## 2026-08-07 — Internal Continuity admission facade merged

```text
PR:                       #246
Exact tested head:        ec2966ed336ba619e987dfc1e99d45fdf87907b5
Merge:                    9f07db6de8d32683d00bfe4f1673e84493607553
Full CI + coverage:       31219904698 PASS on attempt 2, unchanged SHA
Continuity contracts:     31219904684 PASS · 514 passed
Docker hardening:         31219904770 PASS
Aggregate merge evidence: 31221208768 SUCCESS
Review threads:           0
Documentation impact:     GITHUB_AND_NOTION
Notion:                   SYNCED
```

### Intent

Add the first internal composition boundary above the pure evaluator without creating a live trust boundary.

### Implementation

Added:

- `core/continuity/admission_facade.py`;
- `tests/test_continuity_admission_facade.py`;
- `tests/test_continuity_admission_facade_hardening.py`;
- `docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`;
- `docs/ai/PR246_ADMISSION_FACADE_CHECKPOINT.md`.

The facade pins facade-policy, registry, evaluator/rule and resolver identity; verifies exact principal, authorization, tenant, source binding and complete subject scope; rejects malformed Draft sets before resolver access; obtains explicit current-decision evidence through a typed protocol; invokes only the pure evaluator; and returns content-addressed evidence.

### Governance history

The first code+docs head passed focused Continuity and Docker checks but failed the architecture-freeze guard because `ContinuityAdmissionFacadePolicy` was correctly recognized as authority-shaped. The guard was not bypassed. A concrete ADR was added to define the new composition owner and preserve existing PolicyKernel, identity, privacy and runtime owners.

### Test history

Attempt 1 of Full Titan run `31219904698` retained an existing SQLite recovery timeout in `test_drop_legacy_embeddings_lock_owner_process_is_bounded` after 20 seconds; coverage passed. Attempt 2 on the unchanged exact SHA passed repository guards, architecture freeze, machine state, KB integrity, Ruff, blocking mypy and full pytest.

The timeout is retained as intermittent recovery evidence and is not described as a facade defect.

### Authority boundary

```text
facade policy object ≠ PolicyKernel
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted concrete resolver implementation
facade result ≠ runtime permission
```

No producer invocation, persistence, runtime wiring, Canon/ESM/TruthGate/GoalStack mutation, reminder, tool, action or compute authority was introduced.

### Result

```text
Continuity readiness: 7/12 = 58.3%
Facade:                IMPLEMENTED · TESTED · INTERNAL · UNWIRED
Runtime:               NOT WIRED · NOT ENABLED · NOT OBSERVED
```

### Next work

Compose current principal, authorization, consent/lawful-basis, restriction, erasure-domain and current `PolicySnapshot` evidence through accepted owners. Remain internal and stop before producer invocation, persistence or runtime effects.

---

## 2026-08-07 — Pure Continuity admission evaluator merged

```text
PR:                       #244
Exact tested head:        52fdc9b0ef0ff7833c091a64c35d0754874cedb8
Merge:                    97fe27a37184c6c7277f54e96acd04d98d583ab3
Full CI + coverage:       31215957409 PASS
Continuity contracts:     31215957406 PASS · 502 passed
Docker hardening:         31215957402 PASS
Aggregate merge evidence: 31216560826 SUCCESS
Review threads:           0
Documentation impact:     GITHUB_AND_NOTION
Notion:                   SYNCED
```

The evaluator introduced immutable evaluator/rule definitions, exact allowlist registry, explicit current-decision evidence and deterministic Draft admission without runtime authority. The initial fixture chronology failure remains recorded; final exact-head validation passed.

---

## 2026-08-07 — Research intake normalized

```text
PR:                       #243
Exact tested head:        ca1de03bedeba0ca9817a27e7e201f3839cd55bb
Merge:                    2655ecabab400dda4b350ed90142510cf5a4f49c
Full CI + coverage:       31214588983 PASS
Aggregate merge evidence: 31215084800 SUCCESS
Notion:                   SYNCED
```

Ideas from audits, conversations and external analyses now enter one explicit classification boundary:

```text
verified current defect / accepted missing proof
→ active engineering

unproven future architecture / workload / capability
→ research intake card + return trigger
```

Current engineering such as branch protection, Continuity resolver composition, privacy closure, query-path read-only enforcement, Canon writer unification and projection lifecycle is excluded from Research Mode.

---

## 2026-08-07 — Source-adapter sequence completed

```text
Goal subject identity:      PR #230
OpenLoop subject identity:  PR #232
Goal adapter:               PR #236 → 2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d
OpenLoop adapter:           PR #240 → 42aa79338c57e9b9a67c3e3c08dd948b60c5541f
```

State, Goal and OpenLoop now produce bounded evidence-only Draft proposals with explicit subject binding. They do not admit, persist, remind, schedule, act or invoke the signal producer.

---

## Current unresolved engineering queue

1. administrator-enforced branch ruleset — issue #234;
2. operator/deployment-selected facade-policy and registry trust root;
3. concrete current principal/authorization/consent/restriction/erasure/policy resolver composition;
4. durable admission-artifact lifecycle;
5. runtime wiring and activation governance;
6. query-path read-only proof and Canon-writer unification;
7. projection dispatcher lifecycle and operational observability;
8. characterization of the intermittent SQLite legacy-lock recovery timeout;
9. independent security review and production privacy/compliance proof.

Research candidates remain in `research/FUTURE_COMPONENTS.md` and do not replace this engineering queue.
