# Selective Memory — Speed and Safety Contract

**Status:** `IMPLEMENTED_ON_BRANCH / SHADOW_ONLY / CI_PENDING`  
**Scope:** ARM-03 candidate extraction only; no admission, persistence, Canon or response authority  
**Primary goal:** improve memory-candidate quality without increasing user-visible answer latency

## 1. Core decision

Selective-memory analysis must not become a mandatory synchronous stage of the normal
answer path.

```text
User query
  -> retrieval and evidence assembly
  -> Guardian / TruthGate
  -> answer

After or beside the answer path
  -> bounded shadow dispatch
  -> selective-memory candidate extraction
  -> evaluation receipt
  -> no write
```

ARM-03 is a dependency-free rule baseline. It does not import or call an LLM, embedding
model, graph traversal, network client, Canon store, WorkingMemoryGate, Write Gate,
Guardian or TruthGate. It only proposes bounded candidates for offline or shadow
evaluation.

## 2. User-visible latency invariant

```text
flag OFF
-> no extraction call
-> no candidate scan
-> no model/network work
-> legacy response unchanged
```

Any future runtime integration must preserve these rules:

1. The legacy answer remains authoritative.
2. Shadow extraction is never awaited before returning an already-computed answer.
3. Queue saturation, timeout or extractor failure may drop optional shadow work but must
   not delay or fail the answer.
4. Admission and persistence remain separate later stages and must never run on the query
   path implicitly.
5. Feature flags OFF preserve legacy behavior except explicitly documented additive
   diagnostics.

ARM-03 itself is not wired into `/query`.

## 3. Cheap-first execution

```text
cheap validation
-> bounded exact source spans
-> local regex classification
-> local sensitivity and injection detection
-> local redaction
-> deterministic deduplication/supersession hints
-> bounded immutable result
-> explicit safe serialization
```

Expensive work is absent:

- no provider call;
- no embedding generation;
- no reranker;
- no graph expansion;
- no database read or write;
- no truth evaluation;
- no autonomous admission.

## 4. Hard budgets

| Budget | Default | Purpose |
|---|---:|---|
| source spans scanned | 64 | bound parsing work |
| candidates returned | 12 | bound downstream review |
| characters per candidate | 500 | reject oversized statements |
| total candidate characters | 2,000 | bound result size |
| minimum candidate characters | 4 | remove low-value fragments |

These are execution budgets, not truth or retention policy. ARM-04 may reject every
candidate.

## 5. Hardened candidate contract

A candidate carries:

- deterministic candidate ID;
- type and temporal scope;
- explicit `RetentionReason`;
- `extraction_confidence`, never truth confidence;
- optional `subject_ref` and `context_id`, both bound into identity;
- exact source offsets plus SHA-256 span hash;
- sensitivity flags;
- redacted candidate text;
- deterministic within-input supersession hint;
- extractor and policy versions.

The old `.confidence` name is retained only as a read-only compatibility property that
returns `extraction_confidence`.

## 6. Prompt-to-memory injection boundary

Instruction-shaped text is not memory authority. ARM-03 detects bounded English and
Russian patterns including requests to:

- ignore prior instructions;
- remember content permanently;
- write directly into Canon;
- disable security checks;
- bypass truth/write/policy gates.

Default disposition:

```text
UNTRUSTED_INSTRUCTION
+ MEMORY_INJECTION_RISK
+ SECURITY / HIGH_RISK
-> rejected proposal
-> no admission
-> no write
```

A policy may retain such material for explicit offline security evaluation, but the
result remains proposal-only and has no policy or execution authority.

## 7. Safe source-span serialization

Exact raw source text may be needed inside the in-process result to verify offsets against
protected source evidence. It must not be copied into portable logs, fixtures or
receipts.

`SourceSpan` therefore:

- stores exact character offsets;
- computes a SHA-256 hash over the exact span;
- excludes raw text from dataclass `repr`;
- exposes `to_safe_dict()` with redacted `safe_text`;
- preserves source reference and hash for protected provenance verification.

`CandidateExtractionResult.to_safe_dict()` is the supported portable representation.
Regression tests prove synthetic email, phone and credential values are absent from it.

## 8. Failure disposition

```text
shadow disabled       -> empty diagnostic result
shadow queue full     -> future integration drops shadow job
extractor timeout     -> future integration discards proposal
invalid input         -> empty/rejected result
credential detected   -> reject; safe serialization redacts
memory injection      -> reject/quarantine
budget exceeded       -> deterministic truncation
```

Fallback may reduce optional capability but must never expand permission, visibility or
write authority.

## 9. Performance measurement

The dependency-free benchmark reports:

- mean, median and p95 latency;
- processed characters and characters per second;
- candidate and rejection counts;
- truncation state;
- safe-serialization assertions;
- zero Canon writes;
- zero memory writes;
- zero Write Gate calls;
- zero model and network calls.

Absolute CI latency thresholds are intentionally avoided because shared runners are
noisy. Regression decisions compare the same fixture, Python version, hardware class and
policy version.

## 10. Promotion gates before ARM-04

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

Active admission requires a separate ARM-04 PR with WorkingMemoryGate disposition,
explicit Write Gate, provenance, revocation/erasure compatibility, audit receipts and
operator approval.

## 11. Reality boundary

Implemented on the recovery branch:

- `extraction_confidence` naming;
- subject/context identity;
- retention reason;
- injection detection and rejection;
- safe portable serialization with span hash;
- deterministic within-input supersession hints;
- default-off feature flag;
- focused tests, speed contract, benchmark and replay fixture.

Not claimed until CI completes:

- repository-wide test compatibility;
- benchmark results on the final head;
- replay classification on the final head;
- merge into `main`.

Not included:

- `/query` wiring;
- queues or background workers;
- admission or persistence;
- Canon, ESM, TruthGate, WriteGate or WorkingMemory changes;
- user-visible memory behavior.
