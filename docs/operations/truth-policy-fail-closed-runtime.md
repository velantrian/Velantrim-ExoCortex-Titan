# TruthPolicy fail-closed runtime boundary

**Status:** runtime-adapter increment · no `/query` wiring yet

## Problem

The current `/query` integration evaluates TruthPolicy inside a broad `try/except`. When the feature is enabled and evaluation raises, the exception is logged and the request continues with `truth_rejects_answer=False`. That permits LLM generation after the configured truth gate failed to produce a verdict.

Feature-enabled policy failure must not collapse into permission.

## Runtime adapter

`core.truth_policy_runtime.evaluate_truth_policy_runtime()` normalizes three states:

| State | Evaluated | Blocks LLM | Client truth block |
|---|---:|---:|---|
| feature disabled | false | false | `null` |
| measured `allow` / `gap_notice` | true | false | original verdict |
| measured `reject` | true | true | original verdict |
| enabled evaluation failure | false | true | canonical content-free reject |

The failure block is:

```json
{
  "decision": "reject",
  "truth_status": "policy_unavailable",
  "reason": "truth_policy_unavailable",
  "admissible_count": 0,
  "evidence_ids": [],
  "trace_note": ""
}
```

## Failure semantics

The adapter fails closed for:

- exceptions raised by the policy;
- invalid verdict object types;
- unknown decision values;
- malformed runtime-result contracts.

Detailed exceptions remain in protected logs. Client-visible output never receives exception messages, paths, SQL, claims, fact IDs, provider secrets or payload fragments.

## Existing semantics preserved

- disabled TruthPolicy does not execute and does not alter the request;
- `allow` remains allowed;
- `gap_notice` remains an honest non-citation-grade response state;
- measured `reject` continues to block LLM generation;
- the underlying admissibility policy is not changed.

## Next increment

Replace the current broad fail-open `/query` block with one call to the adapter:

```python
_runtime_truth = evaluate_truth_policy_runtime(
    req.query,
    pipeline_facts,
    mode=eff_mode,
    enabled=is_truth_policy_enabled(),
)
truth_block = _runtime_truth.truth_block
truth_rejects_answer = _runtime_truth.blocks_llm
```

That integration must be a separate minimal `server.py` PR after the erasure startup lifecycle PR merges.
