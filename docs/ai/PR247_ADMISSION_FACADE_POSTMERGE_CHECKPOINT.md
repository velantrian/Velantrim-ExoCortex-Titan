# 📚 PR #247 — Admission Facade Post-Merge Canonical Checkpoint

**Status:** `FINAL · HISTORICAL SNAPSHOT · DOCS-ONLY · GITHUB_AND_NOTION`  
**Merge SHA:** `294bdfa6a77097e48310872a2e3fae811e8c2c9e`  
**Verified:** 2026-08-08 UTC  
**Implementation baseline:** `main@9f07db6de8d32683d00bfe4f1673e84493607553` (PR #246)  
**Implementation PR:** `#246`  
**Implementation exact tested head:** `ec2966ed336ba619e987dfc1e99d45fdf87907b5`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

> This document is an exact, dated, historical snapshot. It is not an evergreen claim
> about the current repository head. Re-query GitHub before treating any SHA here as
> current truth.

## Purpose

Synchronize canonical GitHub and Notion state after PR #246 merged the internal
admission-aware facade and PR #247 merged the post-merge documentation checkpoint.

This checkpoint contains no runtime implementation change. It corrects current-state,
authority-map, risk, handoff, work-log and machine-readable readiness surfaces from
evaluator-era `6/12 = 50.0%` to facade-era `7/12 = 58.3%`.

## SHA role separation

| Field | Value | Role |
|---|---|---|
| `repository_head_sha_at_verification` | `294bdfa6a77097e48310872a2e3fae811e8c2c9e` | Exact `main` inspected at verification |
| `implementation_baseline_sha` | `9f07db6de8d32683d00bfe4f1673e84493607553` | Latest implementation-bearing Continuity merge (PR #246) |
| `documentation_checkpoint_sha` | `294bdfa6a77097e48310872a2e3fae811e8c2c9e` | Merged docs-only post-merge checkpoint (PR #247) |

## Canonical state after PR #246

Completed capability categories:

1. accepted source-admission architecture;
2. seven primary immutable evidence contracts;
3. State Draft adapter;
4. Goal Draft adapter;
5. OpenLoop Draft adapter;
6. pure deterministic evaluator and content-addressed registry;
7. internal admission-aware facade, typed resolver boundary and anti-substitution checks.

Remaining categories:

1. concrete current-decision resolver composition through accepted owners;
2. durable retention/replay/cleanup/erasure lifecycle;
3. runtime wiring with one lifecycle owner;
4. enablement, SLO, monitoring, rollback and Operator GO;
5. live observed evidence.

```text
Completed: 7/12 = 58.3%
Remaining: 5/12 = 41.7%
WIRED:     false
ENABLED:   false
OBSERVED:  false
AUTHORITY: false
```

This count is internal implementation readiness, not production or live readiness.

## PR #246 exact evidence

```text
Exact tested head:          ec2966ed336ba619e987dfc1e99d45fdf87907b5
Merge SHA:                  9f07db6de8d32683d00bfe4f1673e84493607553
Full Titan CI + coverage:   31219904698 PASS on attempt 2, unchanged SHA
Continuity contracts:       31219904684 PASS · 514 passed
Docker hardening:           31219904770 PASS
Aggregate merge evidence:   31221208768 SUCCESS
Unresolved review threads:  0
```

Attempt 1 of Full Titan run `31219904698` retained one existing SQLite recovery timeout
in `test_drop_legacy_embeddings_lock_owner_process_is_bounded`; coverage passed. Attempt
2 on the unchanged exact SHA passed the complete blocking suite. This remains
intermittent legacy embeddings-lock recovery risk evidence and is **not** attributed to
the facade.

The architecture-freeze guard initially required a concrete ADR for
`ContinuityAdmissionFacadePolicy`. PR #246 added
`docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`; the guard was not
bypassed.

## PR #247 merge and post-merge main evidence

```text
Merge SHA:                  294bdfa6a77097e48310872a2e3fae811e8c2c9e
Full Titan CI + coverage:   31222680496
  Attempt 1:                FAILED
  Attempt 2:                PASS · 3746 passed, 17 skipped, 1 xfailed
Aggregate push evidence:    31222680550 SUCCESS
Unresolved review threads:  0
```

### Post-merge CI incident (correct identification)

The first attempt of Full Titan run `31222680496` on merge SHA
`294bdfa6a77097e48310872a2e3fae811e8c2c9e` failed in:

```text
tests/test_promotion_projection_outbox_caller.py::
test_cas_contention_yields_exactly_one_winner_and_one_intent[25]
```

Failure:

```text
threading.BrokenBarrierError
  at barrier.wait(timeout=15)
```

Attempt 2 on the unchanged exact SHA passed. Local audit runs on the same test family
reported 30/30 targeted parameterized passes.

This is an **uncharacterized CAS-contention test failure**. `BrokenBarrierError` proves
only that all 25 contenders did not reach the barrier within its timeout. It does not
distinguish runner scheduling, test orchestration, or a worker exiting or blocking in
the production pre-CAS path. A stage-based harness is a diagnostic hypothesis, not proof
that production CAS is healthy or that the failure is only a test flake.

This incident is **not** the historical SQLite family
`test_concurrent_fresh_bootstrap_add_column_no_duplicate_error` and **not** the
historical timeout family `test_drop_legacy_embeddings_lock_owner_process_is_bounded`.
Those three failure families must remain separate in audit history.

## Updated canonical surfaces

- `docs/ai/CURRENT_STATE.md`;
- `docs/ai/COMPONENT_MAP.md`;
- `docs/ai/KNOWN_RISKS.md`;
- `docs/ai/WORK_LOG.md`;
- `docs/ai/CONTINUITY_SOURCE_ADMISSION_HANDOFF.md`;
- `docs/state/project_state.json`;
- `tests/test_check_project_state.py`.

## Corrected evidence metadata

The Notion facade merge block temporarily contained two non-existent workflow IDs for
exact-head Continuity and Docker checks. This checkpoint corrects them to:

- Continuity `31219904684`;
- Docker `31219904770`.

The valid aggregate run `31221175073` is retained as an earlier success; the latest
exact-head aggregate success before PR #246 merge is `31221208768`.

## Trust and authority boundary

```text
facade policy object ≠ PolicyKernel
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted concrete resolver implementation
facade result ≠ runtime permission
```

No producer invocation, persistence, runtime wiring, public export, Canon/ESM/TruthGate/
GoalStack mutation, reminder, notification, delivery, tool, action or compute authority is
introduced by this docs-only checkpoint.

## Next bounded engineering slice

Compose current principal, authorization, consent/lawful-basis, restriction, erasure-domain
and current `PolicySnapshot` evidence through accepted owners.

The slice must remain internal and fail closed on incomplete or conflicting multi-subject
state. It must stop before producer invocation, persistence, runtime wiring or user-visible
effects.

## Documentation synchronization

```text
Documentation impact:   GITHUB_AND_NOTION
Notion access:           AVAILABLE
Notion targets:          Velantrim Titan 9.0
                         Continuity Source Admission — Architecture
Notion synchronization: SYNCED
Verified:                2026-08-08 UTC
Evidence:                Continuity Source Admission page contains the
                         "2026-08-08 — PR #247 checkpoint FINAL correction"
                         block with SHA roles, CAS-contention incident
                         identification, and 7/12 readiness boundary
```

Titan Hub / Continuity Source Admission records facade-era `7/12 = 58.3%`, PR #246 merge,
corrected exact workflow IDs, post-merge main evidence, the uncharacterized CAS-contention
test failure above, and the next resolver-composition boundary.
