# Query Read-Side Purity — Block A Final Evidence

**Implementation date:** 2026-08-15  
**Final evidence reconciliation:** 2026-08-16  
**Issue:** #330 — **CLOSED / completed**  
**Implementation PR:** #331 — **MERGED**  
**Implementation base:** `main@185d91be70e63eafde819c3bb0c5d15a5f974caa`  
**Exact accepted PR head:** `67b5fa07e6283c07c76391ac48898227952d9b97`  
**Protected squash merge:** `43e20f2a777079bf382c4c6512061edb83c6c0d5`  
**Accepted/merged tree:** `e3665155db1010d2082b9ef24ce6722cfd03203f`  
**Merge signature:** `VERIFIED / valid`  
**Documentation impact:** `GITHUB_ONLY`  
**Block A:** **CLOSED · IMPLEMENTED · TESTED · MERGED · POST-MERGE REVALIDATED**

## Problem

The legacy/default query path could request causal evidence through the initializing
`_get_causal_graph()` helper. On a valid store with no causal schema yet, that helper may
open SQLite, execute `_RELATIONS_DDL`, commit, and install the process singleton. A logical
query could therefore mutate persistent SQLite schema even though the query path does not
own Canon fact/ESM or causal-relation mutation.

The caller audit found three query-facing initialization sites in `core/pipeline.py`:

1. contradiction extraction in `run()`;
2. `_expand_with_graph_neighbors()`;
3. `_essence_relations_for()` when no graph is supplied.

The server lifecycle already has an explicit migration owner. Query execution does not need
to act as a hidden fallback migrator.

## Bounded fix

The existing non-initializing `_peek_causal_graph()` boundary is reused:

```text
explicit lifecycle / setup / reset / mutation
  -> _get_causal_graph() may initialize

query-side causal evidence
  -> _peek_causal_graph()
  -> already-open graph when available
  -> otherwise bounded no-graph fallback
```

No graph manager, schema, authority owner, runtime flag, Canon path or Phase 3B capability
was added.

## Regression contract

The merged regression coverage proves that a default query on an isolated seeded database
with no open causal singleton:

- returns a normal bounded answer;
- leaves the non-internal `sqlite_master` snapshot unchanged at the SQL-row level
  (`schema_after == schema_before`);
- does not create `relations`, `relation_paths`, `idx_relations_from`, or
  `idx_relations_to`;
- leaves `(fact_id, epistemic_state)` unchanged;
- leaves the causal singleton detached.

The graph-expansion no-graph regression also makes `_get_causal_graph()` raise if called,
proving the read helper cannot silently fall back to initialization. Existing positive
graph tests explicitly initialize graph state before reading it. The Essence causal-chain
test injects the read-only peek hook.

## Exact implementation evidence

Production commit:

`393225fc4a0b7c977098e3555c8c61035ff2314c`

Test commits:

- `b750ac1d0b291f81142c6e9b1c033e274392df8c` — schema/ESM/no-init regressions and graph
  fixture cleanup;
- `ead6bde638f1399ab7293091f4d0f1e4847486cd` — Essence test uses the read-only hook.

Final accepted PR head:

`67b5fa07e6283c07c76391ac48898227952d9b97`

The accepted head and protected squash merge have the same Git tree:

`e3665155db1010d2082b9ef24ce6722cfd03203f`

Therefore the protected merge did not introduce different source bytes from the accepted
PR tree.

## Final exact-head acceptance

For `67b5fa07e6283c07c76391ac48898227952d9b97`:

```text
Full CI:                  #1224 · 31898673936 · SUCCESS
Docker:                   #808  · 31898673941 · SUCCESS
CodeQL:                   #62   · 31898673945 · SUCCESS
Aggregate merge evidence: #1363 · 31898953358 · SUCCESS
```

Full CI included the architecture freeze guard, machine-readable project-state guard,
portable-KB integrity guard, Ruff, blocking mypy, full pytest and coverage ratchet. The
final aggregate gate was green immediately before merge.

Codex did not provide an independent review verdict because the code-review usage limit was
reached. That notification is not represented as approval. No independent formal approval
is claimed.

## Protected merge and lifecycle

PR #331 was protected-squash-merged as
`43e20f2a777079bf382c4c6512061edb83c6c0d5`. GitHub reports the merge signature as
`VERIFIED / valid`. Issue #330 is `CLOSED / completed`.

Exact post-merge security/container evidence on that merge SHA:

```text
Docker:  #809 · 31899003194 · SUCCESS
CodeQL:  #63  · 31899003209 · SUCCESS
```

## Full CI #1225 forensic record

Post-merge Full CI #1225 / run `31899003155` executed on the exact merge SHA
`43e20f2a777079bf382c4c6512061edb83c6c0d5`.

### Attempt 1 — OBSERVED

Attempt 1 concluded **FAILURE**. The failing job was `lint-and-test` / `95046610806`.
The preserved job metadata shows:

- repository/setup guards reached success;
- architecture freeze guard — success;
- machine-readable project-state guard — success;
- portable-KB integrity guard — success;
- Ruff — success;
- blocking mypy — success;
- `Pytest` — failure / process exit code 1.

The currently accessible GitHub evidence does **not** preserve the failing pytest node or
traceback through the connector surfaces used for this reconciliation:

- check annotations contain only the generic `Process completed with exit code 1` failure;
- the raw historical job-log endpoint currently returns an empty content payload;
- run artifacts contain coverage, reproducible-wheel, dependency-audit and deterministic
  lock-SBOM evidence, but no JUnit/test-failure artifact identifying the failed node.

Accordingly:

```text
exact failing test in attempt 1: UNKNOWN
attempt-1 traceback:             UNKNOWN
attempt-1 root cause:            UNKNOWN
relation to Issue #249:          UNKNOWN / NOT PROVEN
```

No test name, traceback or root cause is inferred from absence of preserved evidence.

### Controlled exact-SHA revalidation — OBSERVED

On 2026-08-16 the failed job was rerun through GitHub Actions without changing source.
Run #1225 advanced to `run_attempt=2` on the same merge SHA/tree. The replacement
`lint-and-test` job `95115660246` completed **SUCCESS**, including:

- architecture freeze guard — success;
- machine-readable project-state guard — success;
- portable-KB integrity guard — success;
- Ruff — success;
- blocking mypy — success;
- full pytest — success.

All other Full CI jobs in attempt 2 also completed successfully, including the coverage
ratchet, dependency vulnerability audit, deterministic lock SBOM and reproducible-wheel
verification. Run #1225 therefore now has final conclusion **SUCCESS** for attempt 2.

This proves that the attempt-1 failure did not deterministically reproduce on the exact
post-merge source tree. It does **not** identify the missing attempt-1 traceback and does
not establish a causal link to any known flake.

## Issue #249 boundary

Issue #249 remains a separate **OPEN** characterization risk for the projection-outbox CAS
contention harness and its historical `threading.BrokenBarrierError`. Its own evidence
explicitly requires characterization beyond a rerun-to-green.

Because Full CI #1225 attempt 1 no longer exposes its exact failing pytest node/traceback,
this Block A reconciliation does **not** claim that #1225 was Issue #249. The relationship
remains `UNKNOWN`.

Keeping #249 open therefore does not contradict Block A closure: #249 is not evidence of a
deterministic Query Read-Side Purity regression and is tracked under its own bounded scope.

## Descendant-main non-regression evidence

Before this final documentation reconciliation, live `main` had advanced through separate
bounded fixes to signed `main@9dc0bdc7b2bc5dee18156ff333f55ba376bced07` without removing
the Block A implementation. Full CI #1250 / run `31905622936` completed **SUCCESS** on that
descendant main, including full pytest, Ruff, blocking mypy, repository guards, coverage,
dependency audit, deterministic SBOM and reproducible-wheel evidence.

This is supporting non-regression evidence only; it does not replace the exact PR-head and
exact merge-SHA evidence above.

## Evidence classification

### OBSERVED

- PR #331 exact head passed Full CI, Docker, CodeQL and the final aggregate merge gate.
- The protected merge carries the same Git tree as the accepted PR head and is signed
  `VERIFIED / valid`.
- Issue #330 is closed/completed.
- Post-merge Docker #809 and CodeQL #63 passed on the exact merge SHA.
- Full CI #1225 attempt 1 failed only when it reached pytest after the listed guards,
  lint and type checks had passed.
- Full CI #1225 attempt 2 on the same merge SHA/tree passed full pytest and all Full CI jobs.
- A later descendant main also passed a complete Full CI run.

### INFERRED

- The available evidence weighs against a deterministic Block A implementation regression,
  because the exact accepted tree passed before merge and the identical merged tree passed
  controlled revalidation without source changes.

### UNKNOWN

- The exact pytest node that failed in #1225 attempt 1.
- The attempt-1 traceback/root cause.
- Whether attempt 1 was related to Issue #249 or to any other transient condition.

## Authority / non-goals

Unchanged:

- Canon ownership;
- ESM ownership;
- causal-relation mutation ownership;
- TruthGate and PolicyKernel;
- embedding Phase 3A posture;
- Titan project-state schema v7;
- Continuity `12/12`;
- runtime enabled = `false`;
- Operator GO = `false`;
- runtime authority = `false`;
- production authority = `false`;
- remote Canon = forbidden;
- Phase 3B = `NOT ADMITTED / NOT STARTED`.

Direct GraphLab lifecycle/signature repair, IndexCoordinator work, storage observability,
multilingual lifecycle hygiene, CSM stages, broad truth-surface cleanup, Notion history
cleanup and Issue #249 characterization remain separate bounded workstreams.

## Documentation synchronization

PR #331 classified this bounded correctness convergence as `GITHUB_ONLY`. The complete
technical/audit context is stored in GitHub, and no architecture/authority decision changed.
Therefore:

```text
Documentation impact:      GITHUB_ONLY
Notion access:             NOT_REQUIRED
Notion synchronization:    NOT_REQUIRED
ADR:                       NOT_REQUIRED
new Notion page:           none
CURRENT_STATE mutation:    NOT_REQUIRED for Block A authority/status semantics
```

The existing Notion page is not mutated merely to duplicate this GitHub-only forensic
closure.

## Final completion rule

The original Block A completion requirements are now satisfied:

1. final exact-head Full CI / Docker / CodeQL / aggregate evidence — **SATISFIED**;
2. review/merge gate reconciliation — **SATISFIED**;
3. protected merge — **SATISFIED**;
4. post-merge acceptance/revalidation — **SATISFIED**, with the attempt-1 forensic unknown
   explicitly preserved rather than guessed;
5. Issue #330 closure/read-back — **SATISFIED**.

**Query Read-Side Purity Block A is CLOSED.**

This closure does not admit or start Block B. `Block B = NOT ADMITTED / NOT STARTED` until
a separate bounded admission is performed after this closure is read back from protected
main.
