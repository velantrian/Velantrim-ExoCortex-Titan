# 🔐 PR #232 — OpenLoop Subject-Binding Checkpoint

**Date:** 2026-08-07  
**Repository:** `velantrian/Velantrim-ExoCortex-Titan`  
**Base:** `main@69cd6e1af6ab01679bd940fa63ac89f652a8757c`  
**Implementation + direct hash-test head:** `a5737f689ab5999afa31d2eb485f01a024ae87e5`  
**Status:** `DRAFT · IMPLEMENTED IN OPEN PR · INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED`  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Notion record:** `🔐 Continuity Source Admission — Architecture`

This checkpoint records the current branch truth for PR #232 without granting runtime authority. Canonical `main` documentation still describes OpenLoop subject binding as absent until this PR is merged.

## 1. Implemented contract

PR #232 advances OpenLoop projections to `continuity.open_loop_projection.v2` and binds subject identity through the complete deterministic chain:

```text
OpenLoopSignal.user_id
→ OpenLoopResolution.user_id
→ OpenLoopProjection.user_id
→ OpenLoopProjectionResult.subject_ids
→ content-addressed result identity
```

Implemented guarantees:

- `user_id` is mandatory for signals and resolutions;
- subject identity enters signal and resolution digests;
- subject identity is propagated to projections;
- result exposes the complete sorted subject set;
- subject set enters the result digest;
- a resolution from a different subject fails closed;
- direct constructors and affected fixtures use explicit subject identity;
- schema version advances explicitly from v1 to v2.

## 2. Direct regression proof

`tests/test_continuity_open_loop_subject_hashing.py` pins the primary security invariant directly:

```text
same OpenLoop semantics + different user_id
→ different signal_id
→ different resolution_id
→ different projection_id
→ different result_id
```

This complements the existing happy-path, multi-subject and cross-subject rejection tests.

## 3. Review state

Copilot reviewed all five original changed files and produced two comments:

1. replace positional dataclass construction with keyword arguments;
2. include actionable subject details in cross-subject mismatch errors.

Both were fixed on `81e07a8ea59f486da9f5cf147ecc2932044fa024`; both review threads are resolved. No independent `APPROVED` review is claimed.

## 4. CI state

The earlier exact head `81e07a8ea59f486da9f5cf147ecc2932044fa024` had:

```text
Full Titan CI                 PASS
Coverage ratchet core ≥74%    PASS
Docker hardening              PASS
Continuity contract-gate      NOT RUN / hosted runner acquisition failure
```

The failed workflow annotation stated that GitHub's hosted runner did not acquire the job after multiple attempts. This is not evidence of a code failure, but it is also not a PASS.

The new branch head after this checkpoint must obtain fresh exact-head CI before the PR can leave Draft or merge.

## 5. Explicit non-scope

PR #232 adds no:

- Goal or OpenLoop source adapter;
- admission evaluator or evaluator/rule registry;
- admission-aware facade;
- persistence or replay store;
- `/query`, startup, worker or scheduler wiring;
- feature flag or runtime activation;
- Canon, ESM or TruthGate mutation;
- answer, reminder, tool, action or compute-route authority.

## 6. Remaining Continuity blockers

After merge, OpenLoop subject binding will be complete, but Continuity live readiness remains `3/12 = 25%` because the following remain absent:

- Goal source adapter;
- OpenLoop source adapter;
- admission evaluator and allowlist;
- current authorization, consent, restriction and erasure checks;
- admission-aware facade;
- durable persistence/replay lifecycle;
- runtime wiring;
- controlled enablement with SLO, alerts and rollback;
- live observed evidence.

## 7. Merge gates

PR #232 may leave Draft only after:

- fresh exact-head Ruff, blocking mypy and full pytest PASS;
- coverage ratchet PASS;
- Docker hardening PASS;
- Continuity contracts PASS rather than cancelled/missing;
- unresolved review threads `0`;
- final aggregate diff review;
- GitHub and Notion status synchronized truthfully;
- PR body no longer claims `independently green` unless all required evidence exists.

After merge, canonical files under `docs/ai/` must be advanced from the PR #231 checkpoint to the final merge SHA and post-merge CI evidence.
