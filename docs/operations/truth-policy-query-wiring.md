# TruthPolicy `/query` fail-closed integration

**Status:** hot-path integration · no threshold or feature-default change

## Previous behavior

When `ENABLE_TRUTH_POLICY` was enabled, `/query` evaluated the policy in a broad `try/except`. Any exception from feature configuration, imports or policy evaluation was logged at debug level and the request continued with `truth_rejects_answer=False`.

That meant a configured truth gate could fail and unverified LLM generation would still run.

## New behavior

`/query` calls one boundary:

```python
_truth_runtime = evaluate_configured_truth_policy_runtime(
    req.query,
    pipeline_facts,
    mode=eff_mode,
)
truth_block = _truth_runtime.truth_block
truth_rejects_answer = _truth_runtime.blocks_llm
```

The runtime adapter owns both feature-resolution and policy-evaluation failure semantics.

| Runtime state | Truth block | LLM generation |
|---|---|---|
| feature disabled | `null` | unchanged/allowed |
| measured `allow` | measured verdict | allowed |
| measured `gap_notice` | measured gap | allowed with honest gap state |
| measured `reject` | measured reject | blocked |
| resolver/policy failure | content-free `policy_unavailable` reject | blocked |

## Client evidence

Failure returns only:

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

Exception messages, paths, SQL, claims, fact IDs, provider secrets and request payloads are not exposed.

## Preserved behavior

This integration does not change:

- TruthPolicy thresholds or fact admissibility;
- verdict vocabulary;
- the default disabled feature state;
- pipeline retrieval or pipeline answer generation;
- Canon writes;
- deployment profiles;
- `allow`, `gap_notice` or measured `reject` semantics.

Only the confirmed fail-open exception path changes.

## Validation boundary

The exact self-removing patch compiled `server.py` and passed all 29 focused TruthPolicy tests after the source-order assertions were updated to inspect the new boundary. Temporary workflow/script files are absent from the final branch.

Merge evidence must come only from standard architecture-freeze, Ruff, blocking mypy, full repository pytest and Docker checks attached to this final maintainer-authored head.
