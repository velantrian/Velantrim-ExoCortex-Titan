# SalienceDetector ingest ownership/lifecycle audit — 2026-10-31

**Status:** `AUDIT_ONLY / SCOPE_NOT_ESTABLISHED / NO_RUNTIME_WIRING`

**Exact audited source:** Draft PR #489, head
`9e8bf29ef74ef36406f76ffbadab265993e5a990`.
This is a **stacked documentation-and-test follow-up** to #489, not a main
closure or an activation request. Do not merge this before resolving #489.

## Scope and observed call graph

```text
server.py: POST /facts (created only)
         or POST /ingest/text (batch background task)
   -> core/exocortex_hooks.py: observe_ingest_chunk(chunk, episode_id)
      -> (only if ENABLE_VELUM) core/velum_bridge.py:
         observe_episode_from_ingest(episode_id, entity_names,
                                    episode_text, graphiti=None)
         -> (only if ENABLE_SALIENCE) core/salience.py:
            analyze_episode_salience(text, episode_id)
            -> new SalienceDetector() per unscoped call
```

The path retains lexical signals; it cannot accumulate `topic_streak_3d`
or `topic_return_24h` across separate ingest calls. These flags are off by
default. The current `get_salience_detector()` legacy singleton would
incorrectly aggregate observations from independent callers and is not a fix.

This review does not claim that Velum, entity salience, persistence or all
other memory subsystems are tenant-isolated. In particular, `get_velum()`
still owns a process-global Velum.

## Candidate scope/owner surfaces inspected

| Surface | What exists at the audited source | Safe for Salience owner binding? |
| --- | --- | --- |
| HTTP `X-Api-Key` / `require_api_key` (`server.py`) | Optional deployment-wide shared secret; no per-user principal returned to ingest | **No** |
| `IngestRequest.source`, `metadata` (`server.py`) | Supplied by request client | **No**, forgeable |
| `fact_id`, `episode_id` (`server.py`, `core/exocortex_hooks.py`) | Episode/event identity only; `"local"` fallback exists | **No**, not owner/workspace |
| `core/feature_config.py:knowledge_group_id` | Deployment-global Graphiti grouping value, not authenticated ownership | **No** |
| `core/tool_registry.py:PrincipalContext` / MCP transport | Capability and credential fingerprint; its own contract explicitly states a shared API key is **not** an authenticated user. This context is not passed along these ingest calls | **No** |
| `app/telegram_ingest.py` | `chat_id` / `user_id` in source/metadata, with `unknown` allowed; separate raw/fact path | **Not yet**: no verified identity handoff into Salience; update authenticity and chat-vs-person semantics need explicit treatment |
| Continuity `tenant_ref` / admission artefacts | Separate bounded, authority-governed composition; no accepted adapter binding it to this generic HTTP ingest and per-subject Salience storage | **Not on this path** |

**Conclusion: `SCOPE_NOT_ESTABLISHED`.** No safe existing ingestion owner
may be inferred from the exposed parameters. Do not silently substitute
`source`, `group_id`, `episode_id`, MCP session, Telegram labels or an
API-key hash for an authenticated owner. Even a trusted *deployment* owner
would not by itself distinguish multiple people sharing its storage.

## Required prerequisites before any runtime experiment

1. **Verified owner binding at the actual entrypoint:** derive trusted tenant
   and subject/workspace identifiers from a server-controlled authenticated
   context (or an explicitly governed single-owner deployment contract),
   not JSON/metadata. Specify delegated callers, multiple users in one chat,
   anonymous calls, missing context, and logout/account changes.
2. **Explicit scope identity and lifecycle:** define an immutable
   `(tenant, subject/workspace, memory namespace)` identity and provide the
   explicitly owned `SalienceDetector` to the bridge. No process-wide
   singleton and no unbounded key-to-detector global dictionary.
3. **State ownership and restart policy:** choose a per-scope bounded in-memory
   lifecycle or durable storage with scope-qualified keys and documented
   reload/expiry semantics. Temporal state disappears on restart today; it is
   not durable. Bound retention, memory, deletion/erasure, and lifecycle
   invalidation without changing the existing 14-day topic observation rule.
4. **Replay/concurrency constraints:** define event time and clock ordering;
   prevent double-counted retries, stale observations and concurrent writes
   from corrupting last-seen / streak behavior; preserve per-scope ordering.
5. **Privacy and authorization checks:** verify read/write/delete against
   the trusted current scope; prevent cross-tenant lookup, telemetry leakage,
   retained-session reuse or scope escalation. Salience weight is neither
   evidence nor truth and must not acquire admission/Canon authority.
6. **Fail-closed fallback:** without a verified scope, retain the #489
   one-shot lexical path. Never enable temporal accumulation solely because
   a caller supplied `owner_id` or `source`.

The future owner binding should be reviewed separately from enabling
`ENABLE_VELUM`/`ENABLE_SALIENCE`, and must not change their defaults.

## Synthetic tests in this stacked draft

`tests/test_salience_ingest_scope.py` includes:
- **negative:** anonymous bridge calls A/B on overlapping dates or separated
  dates cannot inherit each other's streak or return history;
- **negative:** old explicit legacy singleton observations cannot contaminate
  a new unscoped ingest call;
- **positive:** two explicit test-owned detector instances independently
  accumulate correct 3-day streaks and 24-hour returns;
- **positive lexical:** unscoped bridge calls retain existing textual signals.

Tests use in-memory synthetic episodes, a fake Velum observer, a fixed clock,
no Graphiti connection and no model/provider/API requests. They do **not**
establish end-to-end multi-user protection or justify runtime activation.

Run locally:

```bash
python -m pytest tests/test_salience.py tests/test_salience_ingest_scope.py -q
ruff check tests/test_salience_ingest_scope.py
```

**Evidence note:** test cases are proposed in this Draft follow-up. Until
a matching exact-head test run is observed, no test-success or full-CI claim
is made. Existing #489 success cannot be inherited by this branch.

## Invariants / disposition

- No modifications to weights, thresholds, TruthGate, Canon, ESM,
  capability or runtime permission, feature-flag defaults or live ingest.
- No global temporal state, new persistent table, or imported donor code.
- No automatic PR merge or enablement.
- Next bounded decision: approve an authenticated ingestion owner and scope
  contract (including cleanup, concurrency and fail-closed behavior), *then*
  consider a separate deliberately disabled runtime experiment.
