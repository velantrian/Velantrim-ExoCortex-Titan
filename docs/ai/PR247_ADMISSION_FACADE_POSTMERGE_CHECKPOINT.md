# 📚 PR #247 — Admission Facade Post-Merge Canonical Checkpoint

**Status:** `DRAFT · DOCS-ONLY · GITHUB_AND_NOTION`  
**Implementation baseline:** `main@9f07db6de8d32683d00bfe4f1673e84493607553`  
**Implementation PR:** `#246`  
**Implementation exact tested head:** `ec2966ed336ba619e987dfc1e99d45fdf87907b5`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

## Purpose

Synchronize canonical GitHub and Notion state after PR #246 merged the internal admission-aware facade.

This checkpoint contains no runtime implementation change. It corrects current-state, authority-map, risk, handoff, work-log and machine-readable readiness surfaces from evaluator-era `6/12 = 50.0%` to facade-era `7/12 = 58.3%`.

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

Attempt 1 of Full Titan run `31219904698` retained one existing SQLite recovery timeout in `test_drop_legacy_embeddings_lock_owner_process_is_bounded`; coverage passed. Attempt 2 on the unchanged exact SHA passed the complete blocking suite. This remains intermittent recovery risk evidence and is not attributed to the facade.

The architecture-freeze guard initially required a concrete ADR for `ContinuityAdmissionFacadePolicy`. PR #246 added `docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`; the guard was not bypassed.

## Post-merge main evidence

For `main@9f07db6de8d32683d00bfe4f1673e84493607553`:

```text
Full Titan CI + coverage:  31221241450 PASS
Continuity contracts:      31221241503 PASS
Docker hardening:          31221241412 PASS
Aggregate push evidence:   31221241453 SUCCESS
```

## Updated canonical surfaces

- `docs/ai/CURRENT_STATE.md`;
- `docs/ai/COMPONENT_MAP.md`;
- `docs/ai/KNOWN_RISKS.md`;
- `docs/ai/WORK_LOG.md`;
- `docs/ai/CONTINUITY_SOURCE_ADMISSION_HANDOFF.md`;
- `docs/state/project_state.json`;
- `tests/test_check_project_state.py`.

## Corrected evidence metadata

The Notion facade merge block temporarily contained two non-existent workflow IDs for exact-head Continuity and Docker checks. This checkpoint corrects them to:

- Continuity `31219904684`;
- Docker `31219904770`.

The valid aggregate run `31221175073` is retained as an earlier success; the latest exact-head aggregate success before merge is `31221208768`.

## Trust and authority boundary

```text
facade policy object ≠ PolicyKernel
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted concrete resolver implementation
facade result ≠ runtime permission
```

No producer invocation, persistence, runtime wiring, public export, Canon/ESM/TruthGate/GoalStack mutation, reminder, notification, delivery, tool, action or compute authority is introduced by this docs-only checkpoint.

## Next bounded engineering slice

Compose current principal, authorization, consent/lawful-basis, restriction, erasure-domain and current `PolicySnapshot` evidence through accepted owners.

The slice must remain internal and fail closed on incomplete or conflicting multi-subject state. It must stop before producer invocation, persistence, runtime wiring or user-visible effects.

## Documentation synchronization

```text
Documentation impact:   GITHUB_AND_NOTION
Notion access:           AVAILABLE
Notion targets:          Velantrim Titan 9.0
                         Continuity Source Admission — Architecture
Notion synchronization: PENDING FINAL DRAFT CHECKPOINT
```

Final docs exact head, CI, aggregate result and merge SHA must be recorded after they exist.
