# ARM-03 Selective Memory Recovery Hand-off

**Status:** `TESTED / READY_FOR_REVIEW / SHADOW_ONLY / DEFAULT_OFF`  
**Base:** `main@649d12953eb141aa783729555861e788cc03c150`  
**Tested head before this documentation-only finalization:**
`125cf0b008f3fc0c0589dc248f1449b5a865e883`  
**Review surface:** PR #200

## Purpose

Rebuild stale/non-mergeable PR #102 on current `main` without importing old repository
files, and complete the hardening required before any future ARM-04 admission work.

## Implemented

- bounded dependency-free candidate extractor;
- default-off canonical feature flag;
- `extraction_confidence` with a read-only compatibility alias;
- explicit `subject_ref` and `context_id` bound into identity;
- deterministic `RetentionReason`;
- bounded English/Russian prompt-to-memory injection detection and default rejection;
- exact source offsets plus SHA-256 span hashes;
- raw span text excluded from dataclass repr;
- explicit safe portable serialization with contact/credential redaction;
- deterministic within-input `POSSIBLE_UPDATE_OF` hints;
- focused tests, speed tests, benchmark, replay fixture and blocking workflow;
- accepted ADR for the proposal-only authority boundary.

## Authority boundary

ARM-03 has no:

- `/query` wiring;
- background queue, worker or startup task;
- persistence or database access;
- Canon, ESM, TruthGate, WriteGate or WorkingMemory authority;
- LLM, embedding, graph or network dependency;
- user-facing answer, reminder, tool or action authority;
- ARM-04 admission path.

## Validation evidence

On head `125cf0b008f3fc0c0589dc248f1449b5a865e883`:

- ARM-03 contracts run `31011184457`: success;
- Docker hardening run `31011184150`: success;
- full Titan CI run `31011183017`: success;
- architecture-freeze accepted
  `docs/adr/ADR-2026-08-05-selective-memory-shadow-proposal-boundary.md`;
- Ruff, blocking mypy, focused tests, full pytest, benchmark and evaluation replay passed.

The PR checks on the final documentation-only head remain the merge authority.

## Residual limitations

- classification and injection detection remain bounded heuristics;
- supersession hints are within-input proposals, not durable reconciliation;
- subject/context identifiers require a trusted upstream owner;
- protected raw source evidence must not leave the in-process boundary except through the
  redacted safe serializer;
- benchmark success does not prove candidate precision or user value.

## Next boundary

ARM-04 requires a separate ADR and PR covering consent, privacy, erasure/revocation,
precision evaluation, WorkingMemoryGate disposition, explicit Write Gate receipts and
operator approval. ARM-03 does not imply that approval.

After PR #200 merges, old PR #102 should be closed as superseded by the current-main
recovery.
