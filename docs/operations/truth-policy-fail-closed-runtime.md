# TruthPolicy fail-closed runtime boundary

**Status (2026-11-27):** runtime adapter and `/query` wiring in main; hardened profile remains disabled.
**Verified code checkpoint:** `a83ed9ffba151a93732a5eb6e354e42e23e15b30` (static review; no activation claim).

## Problem

The historical `/query` integration evaluated TruthPolicy inside a broad `try/except`. When the feature was enabled and evaluation raised, the request could continue with `truth_rejects_answer=False`. This motivated the adapter below.

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

## Current wiring and remaining work

`server.py::query` uses `evaluate_configured_truth_policy_runtime`, including
configuration resolution inside the fail-closed boundary, and applies its
`blocks_llm` result to the LLM-generation branch. See
`tests/test_truth_policy_runtime.py`, `tests/test_truth_policy_configured_runtime.py`
and `tests/test_truth_policy_query_wiring.py`. The latter checks source-level wiring;
it is not a substitute for end-to-end deployed observation.

`ENABLE_TRUTH_POLICY=0` remains pinned in the hardened profile. This change does
not authorize activation or claim that all routes, the legacy pipeline answer,
logs or semantic support have been proven safe. Review those boundaries separately.
