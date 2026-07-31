# Selective Memory — Speed and Safety Contract

**Status:** PR-ARM-03 draft contract  
**Scope:** shadow extraction only; no memory admission or Canon write authority  
**Primary goal:** improve memory quality without increasing user-visible answer latency

## 1. Core decision

Selective-memory analysis must not become a mandatory synchronous stage of the normal answer path.

```text
User query
  -> legacy/adaptive retrieval
  -> FactsPack / ContextPack
  -> Guardian / TruthGate
  -> answer

After or beside the answer path
  -> bounded shadow dispatch
  -> selective-memory candidate extraction
  -> evaluation receipt
  -> no write
```

The current PR-ARM-03 extractor is a dependency-free rule baseline. It does not import or call an LLM, embedding model, graph traversal, network client, Canon store, WorkingMemoryGate, Write Gate, Guardian or TruthGate. It only proposes bounded candidates for offline or shadow evaluation.

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
3. Queue saturation, timeout, parser failure or extractor failure may drop shadow work but must not delay or fail the answer.
4. Admission and persistence remain separate later stages and must never run on the query path implicitly.
5. Feature flags OFF preserve byte-compatible legacy behavior except explicitly documented additive diagnostics.

## 3. Cheap-first execution

The extractor uses a bounded deterministic sequence:

```text
cheap validation
-> bounded sentence spans
-> local regex classification
-> local sensitivity detection
-> local redaction
-> deterministic deduplication
-> bounded immutable result
```

Expensive work is intentionally absent:

- no provider call;
- no embedding generation;
- no reranker;
- no graph expansion;
- no database write;
- no automatic supersession search;
- no truth evaluation;
- no autonomous memory admission.

If later versions introduce optional classifiers, they must be ambiguity-only, locally policy-gated, timeout-bounded and fail back to the deterministic baseline.

## 4. Hard budgets

Default PR-ARM-03 limits are deliberately small:

| Budget | Default | Purpose |
|---|---:|---|
| source spans scanned | 64 | bound parsing work |
| candidates returned | 12 | bound downstream review |
| characters per candidate | 500 | reject oversized statements |
| total candidate characters | 2,000 | bound result size |
| minimum candidate characters | 4 | remove low-value fragments |

These are execution budgets, not truth or retention policy. ARM-04 may reject every proposed candidate.

## 5. Failure disposition

```text
shadow disabled       -> empty diagnostic result
shadow queue full     -> drop shadow job
extractor timeout     -> discard proposal
invalid input         -> empty/rejected result
sensitive credential  -> block and redact
answer path failure   -> handled by existing Titan policy, not by this module
```

Fallback may reduce optional capability but must never expand permission, data visibility or write authority.

## 6. Performance measurement

The benchmark must report measurements rather than fixed marketing claims:

- mean latency;
- median latency;
- p95 latency;
- processed input characters;
- characters per second;
- candidate and rejection counts;
- truncation state;
- zero Canon writes;
- zero memory writes;
- zero Write Gate calls;
- zero model and network calls.

Absolute CI latency thresholds are intentionally avoided because shared runners are noisy. Regression decisions should compare the same fixture, Python version, hardware class and policy version through the evaluation replay protocol.

## 7. Conditions before active integration

PR-ARM-03 may remain shadow-only until replay evidence shows:

```text
truth_gate_bypass_count == 0
query_path_write_count == 0
answer_latency_delta == 0 on flag-off path
shadow_failure_answer_delta == 0
sensitive_block_rate within approved policy
candidate precision acceptable for ARM-04 review
```

Active memory admission requires a separate PR-ARM-04 review, WorkingMemoryGate disposition, explicit Write Gate, provenance, revocation/erasure compatibility and audit receipts.

## 8. Safety hardening required before ARM-04

The following contract changes should be completed before any candidate can be admitted:

1. Rename generic `confidence` to `extraction_confidence`; never imply truth confidence.
2. Add explicit subject/context identity so a statement is not attached to the wrong person or project.
3. Add a retention reason explaining why the candidate is durable and useful.
4. Detect untrusted instruction and prompt-to-memory injection patterns; they may be audited but not admitted as policy or memory authority.
5. Use a safe serialization form for source spans so raw contact or secret material is not copied into logs, fixtures or receipts.
6. Either implement deterministic supersession hints or remove the currently always-empty field until its contract exists.

These items improve correctness and safety. They must not be added as mandatory expensive stages in the answer path.

## 9. Architecture summary

```text
Fast answer path
  -> cheap adaptive retrieval
  -> evidence and policy gates
  -> answer

Optional memory-learning path
  -> bounded shadow job
  -> deterministic candidate proposal
  -> replay and metrics
  -> later explicit admission
```

**Rule:** cheap checks now; expensive analysis only when necessary, bounded and outside the critical response path.