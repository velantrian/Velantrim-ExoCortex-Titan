# ARM-03 Selective Memory Recovery Hand-off

**Status:** `IMPLEMENTED_ON_BRANCH / SHADOW_ONLY / CI_PENDING`  
**Base:** `main@649d12953eb141aa783729555861e788cc03c150`  
**Branch:** `agent/arm03-selective-memory-recovery`

## Purpose

Rebuild the old conflicting PR #102 on current `main` without importing stale repository
files, and complete the hardening required before any future ARM-04 admission work.

## Implemented on this branch

- bounded dependency-free candidate extractor;
- default-off canonical feature flag;
- `extraction_confidence` with a read-only compatibility alias;
- explicit `subject_ref` and `context_id` bound into candidate identity;
- deterministic retention reasons;
- English/Russian prompt-to-memory injection detection and rejection;
- exact source offsets plus SHA-256 span hashes;
- raw span text excluded from dataclass repr;
- explicit safe portable serialization with contact/credential redaction;
- deterministic within-input supersession hints;
- focused tests, speed-contract tests, benchmark and replay fixture.

## Authority boundary

ARM-03 has no:

- `/query` wiring;
- persistence or database access;
- Canon, ESM, TruthGate, WriteGate or WorkingMemory authority;
- LLM, embeddings, graph or network dependency;
- user-visible answer or action authority.

## Validation required

- Ruff over changed Python files;
- blocking mypy over changed core files;
- focused selective-memory tests;
- full repository pytest;
- dependency-free benchmark;
- evaluation replay with no critical regression;
- review of portable serialization for raw synthetic PII/credential absence.

## Completion rule

Do not merge until CI, benchmark, replay, GitHub documentation and Notion evidence are
complete. After merge, close PR #102 as superseded by the current-main recovery PR.
