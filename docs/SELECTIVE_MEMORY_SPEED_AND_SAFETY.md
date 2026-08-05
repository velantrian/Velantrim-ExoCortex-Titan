# Selective Memory — Speed and Safety Contract

**Status:** `TESTED / SHADOW_ONLY / DEFAULT_OFF / NOT_RUNTIME_WIRED`  
**Scope:** ARM-03 candidate extraction only; no admission, persistence, Canon or response authority  
**Review:** PR #200 and
`docs/adr/ADR-2026-08-05-selective-memory-shadow-proposal-boundary.md`

## Core decision

Selective-memory analysis must not become a mandatory synchronous stage of the normal
answer path.

```text
User query
→ retrieval and evidence
→ Guardian / TruthGate
→ answer

Separate future shadow path
→ bounded candidate extraction
→ evaluation receipt
→ no write
```

ARM-03 itself is not wired into `/query`, a worker, startup or persistence.

## Flag-off invariant

```text
ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW=0
→ run_shadow_extraction returns before extraction
→ no candidate scan
→ no model/network/database work
→ no write
→ legacy behavior unchanged
```

Future runtime integration must remain non-blocking: queue saturation, timeout or
extractor failure may discard optional shadow work but must not delay or fail an
already-computed answer.

## Cheap-first execution

```text
bounded exact spans
→ local rule classification
→ sensitivity and injection checks
→ redaction
→ deterministic dedup/supersession hints
→ immutable proposal result
→ explicit safe serialization
```

Absent by contract:

- provider or model calls;
- embeddings, reranking or graph traversal;
- database access;
- truth evaluation;
- memory admission;
- autonomous actions.

## Hard budgets

| Budget | Default |
|---|---:|
| source spans | 64 |
| returned candidates | 12 |
| characters per candidate | 500 |
| total candidate characters | 2,000 |
| minimum candidate characters | 4 |

These are execution budgets, not retention or truth policy.

## Candidate contract

A candidate carries:

- deterministic ID;
- candidate type and temporal scope;
- explicit `RetentionReason`;
- `extraction_confidence`, never truth confidence;
- optional `subject_ref` and `context_id`, bound into identity;
- exact source offsets and SHA-256 span hash;
- sensitivity markers;
- redacted candidate text;
- deterministic within-input `POSSIBLE_UPDATE_OF` hint;
- extractor and policy versions.

`.confidence` remains only a read-only compatibility alias for
`extraction_confidence`.

## Prompt-to-memory injection

Instruction-shaped content has no memory authority. The bounded English/Russian filter
covers examples asking the system to ignore instructions, remember permanently, write
to Canon, disable safety checks or bypass gates.

Default disposition:

```text
UNTRUSTED_INSTRUCTION
+ MEMORY_INJECTION_RISK
+ SECURITY / HIGH_RISK
→ rejected proposal
→ no admission
→ no write
```

This is a conservative heuristic, not complete semantic injection detection.

## Safe source evidence

Exact raw source text may exist only inside protected in-process evidence to verify
character offsets and hashes. It must not be copied into ordinary logs, fixtures or
receipts.

`SourceSpan`:

- stores exact offsets;
- computes SHA-256 over the exact text;
- excludes raw text from dataclass repr;
- exposes `to_safe_dict()` with redacted `safe_text`;
- preserves source reference and hash.

`CandidateExtractionResult.to_safe_dict()` is the supported portable representation.
Tests prove synthetic email, phone and credential strings are absent from it.

## Failure disposition

```text
shadow disabled     → empty diagnostic result
invalid input       → empty/rejected result
credential          → reject + redact portable evidence
memory injection    → reject/quarantine
budget exceeded     → deterministic truncation
future queue full   → drop optional shadow work
future timeout      → discard proposal
```

Fallback may reduce optional capability but never expand permission, visibility or write
authority.

## Validation

Tested head before final documentation-only edits:
`125cf0b008f3fc0c0589dc248f1449b5a865e883`.

- ARM-03 contracts run `31011184457`: success;
- Docker hardening run `31011184150`: success;
- full Titan CI run `31011183017`: success;
- Ruff and blocking mypy passed;
- focused and full pytest passed;
- dependency-free benchmark passed;
- evaluation replay passed;
- architecture-freeze guard passed with the accepted ADR.

Final PR-head checks remain authoritative for merge.

## Gates before ARM-04

```text
truth_gate_bypass_count == 0
query_path_write_count == 0
memory_write_count == 0
write_gate_call_count == 0
flag_off_extraction_count == 0
raw_sensitive_portable_output_count == 0
memory_injection_admission_count == 0
replay critical regressions == 0
candidate precision accepted by operator
```

ARM-04 requires a separate ADR and PR for trusted identity/scope, consent, privacy,
erasure/revocation, WorkingMemoryGate disposition, explicit Write Gate receipts and
operator approval.

## Reality boundary

Implemented and tested:

- hardened proposal contract;
- default-off diagnostic flag;
- safe portable serialization;
- injection rejection;
- focused workflow, benchmark and replay.

Not included:

- runtime wiring or background dispatch;
- admission or persistence;
- Canon, ESM, TruthGate, WriteGate or WorkingMemory changes;
- user-visible memory behavior;
- proof of candidate precision or value.
