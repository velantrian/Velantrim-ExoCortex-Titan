# Independent verification audit — 2026-11-21

Scope: independent re-verification of the "Astra 6" deep audit of 2026-11-21 against
the exact repository state, plus new findings from the same pass. This is an audit
record, not runtime evidence, merge authority or production authorization.

**PRODUCTION NOT AUTHORIZED. OPERATOR GO NOT ESTABLISHED.**

## 1. Object under review

| Item | Value |
|---|---|
| Repository | `velantrian/Velantrim-ExoCortex-Titan` |
| `main` | `485c4b0906ec35829ff7231c6276bf7d817f096f` (merge of #515, 2026-11-14) |
| Open PRs | 21 (16 Draft) — heads listed in §5 |
| Open issues | 13 (#49, #51, #53, #92, #120, #404, #432, #467, #501, #510, #511, #512, #513) |
| `main` rules | required status `Titan aggregate merge evidence` (strict), review-thread resolution required, `required_approving_review_count: 0`, `require_extra_approval_for_unattributed_changes: true`, no deletion / non-fast-forward |

## 2. Method and environment

- Python 3.11.18 (scratch venv), `uv sync --frozen` with extras `server dev parsers graph-lab`,
  plus the locked `rank-bm25==0.2.2` and `numpy==2.4.6`. The `embeddings` extra
  (sentence-transformers / torch) was **not** installed, so no dense model was loaded;
  this matches the "offline, no dense model" condition of the Astra 6 runs, but is not
  the full CI extras set.
- CI test env reproduced: `VELANTRIM_API_KEY=ci-test-key`, temporary `VELANTRIM_DB_PATH`
  and `VELANTRIM_NGRAM_DB`.
- Probes used real SQLite / FTS5 in temporary directories. Probe scripts are summarized
  inline below; no production data, live providers, Docker build or Git-history secret
  scan were used.

## 3. Repository gates on `main@485c4b0`

| Check | Result |
|---|---|
| `ruff check core/` | pass |
| `mypy core/ --show-error-codes` | pass (356 source files) |
| `scripts/validate_kb_graph.py kb_graph.json` | pass — 32 302 nodes, 95 404 edges |
| Full `pytest tests/` (no `-x`) | **5 failed, 4 930 passed, 18 skipped, 1 xfailed** |
| Same 5 failing tests + #523 targeted tests on `#523@fe992ae` | 109 passed |
| Full `pytest tests/` on `#523@fe992ae` (same env) | **0 failed, 4 963 passed, 18 skipped, 1 xfailed** |

The five `main` failures (all retrieval without a dense model):

- `tests/test_embedding_projection.py::test_pipeline_still_reaches_truth_gate_regardless_of_projection_state`
- `tests/test_pipeline.py::test_pipeline_step6_modality_flag_on`
- `tests/test_pipeline.py::test_query_causal_hints_are_proposals_not_relation_writes`
- `tests/test_retrieval_d3.py::test_d3_ngram_candidate_used_directly_beyond_cap`
- `tests/test_retrieval_d3.py::test_d3_empty_ngram_falls_back_bounded`

CI installs `retrieval embeddings`, so these failures are environment-dependent and do
not contradict a green CI on `main`; they show that the model-free path is fragile
(issue #510), which #523 fixes.

## 4. Verification of Astra 6 claims

Status: **CONFIRMED** = reproduced independently at the stated SHA; **CONFIRMED (code)**
= confirmed by reading the exact code path, not by a runtime probe; **NOT RE-VERIFIED**
= accepted as a reported claim only.

| # | Astra 6 claim | Result here | Status |
|---|---|---|---|
| A1 | `main` = `485c4b0`, 21 open PRs (16 Draft), 13 issues, 0 required approvals | Same values from GitHub API | CONFIRMED |
| A2 | Aggregate gate green on #500/#506/#509/#520, red on #503, pending on 16 Draft; #473 conflicts | Same: #500/#506/#509/#520 `success`, #503 `failure` (`behind`), #473 `dirty`, rest `pending` | CONFIRMED |
| A3 | 5 offline failures on `main`; pass on #523 | 5 failed on `main`; all 5 pass on #523 | CONFIRMED |
| A4 | `main` `/query` copies raw provider exception into the response | `server.py` `/query`: `llm_answer = f"[LLM error: {exc}]"`, `llm_meta = {"error": str(exc)}` | CONFIRMED (code) |
| A5 | #514 replaces this with a safe code/event id | #514 `/query` uses `safe_llm_error_text/meta`; raw text kept only for repository-built context-limit errors | CONFIRMED (code) |
| A6 | #514 TTS streaming generator stays open after early consumer close | Not probed | NOT RE-VERIFIED |
| P1-1 | Domain loss: NGram `LIMIT 50` before domain filter, on `main`, #525, #530 | Reproduced with a real FTS5 trigram index, 50 `engineering` + 1 `science` match: `domain="science"` → **0** candidates with prefilter, **1** without. Same code on #523, #525, #530 | CONFIRMED |
| P1-2 | `/query` drops `reason_code`/`insufficient_evidence` returned by #523 core; Observer crash ≡ disabled | #523 `core/pipeline.py::_insufficient_evidence` returns `reason_code` and `insufficient_evidence=True` with `error=None`; `server.py` (#523 and #530) passes only `error=pipeline_error`; `QueryResponse` has neither field. Observer exception → `observer_block = None` (same as flag off) | CONFIRMED (code) |
| P1-3 | FactsPack drops distinct records on `main`; #509 keeps them | Not re-probed | NOT RE-VERIFIED |
| P1-4 | #531 empty poll cost grows with outbox history inside `BEGIN IMMEDIATE` | `claim_batch()` (already on `main`, wired by #531) with 0 backlog: **15 038 / 150 038 / 1 500 038** SQLite VM steps for 1 000 / 10 000 / 100 000 `acknowledged` rows. Query is `LEFT JOIN … WHERE pds.outbox_id IS NULL OR …` ordered by `created_at` — no index can skip completed history | CONFIRMED |
| P1-5 | #528 Telegram idempotency depends on `message_id`; optional on the public input | #528 `app/telegram_ingest.py`: `delivery = str(message_id) if message_id is not None else uuid.uuid4().hex`; `server.py` `message_id: str | None` | CONFIRMED (code) |
| D1 | `_parse_openai_sse_chunk`, `_check_prometheus` have no callers | Only definitions in `core/llm_stream.py:425`, `core/metrics.py:36` (no non-test references) | CONFIRMED |
| D2 | Three `spreading_activation` bodies are AST-identical | Same AST hash in `cypher_graph_base.py`, `memory_graph.py`, `sqlite_graph.py` | CONFIRMED |
| D3 | Cypher neighbors have no `ORDER BY` | `cypher_graph_base.py::get_neighbors`: `RETURN DISTINCT b.node_id … LIMIT $limit` | CONFIRMED (code) |
| D4 | `MemoryGraphStore.upsert_edge()` relabels an existing `Fact` node as `Entity` | `upsert_edge` calls `upsert_node(id)` whose default `label="Entity"` is unconditionally written (`row["label"] = label`) | CONFIRMED (code) |
| D5 | 3 461 tracked files, 831 Python; 509 broad handlers in `core/`, `api/`, `server.py` | 3 461 / 831; 509 `except Exception`/`BaseException`/bare | CONFIRMED |
| D6 | `docs/console/index.html` differs from `static/console/index.html`; Pages builds from `static/console` | Files differ; `pages.yml` watches `static/console/**` | CONFIRMED |
| D7 | `KNOWN_RISKS.md` still calls merged #515 a draft | Yes (heading and two references); corrected in this branch | CONFIRMED — fixed |
| D8 | #501 fixed on `main` by #502 | #502 merged 2026-11-07 as `1a7141c6`; #501 still open | CONFIRMED |

## 5. New findings (not in the Astra 6 report)

### N1 (P1) — NGram prefilter has no relevance order

`core/ngram_index.py::NGramIndex.query` runs
`SELECT doc_id FROM ngram_index WHERE content MATCH ? LIMIT ?` with **no `ORDER BY rank`**.
The 50 candidates passed to BM25/hybrid are therefore the first 50 matches in storage
order, not the best 50. Probe: 60 older notes containing "thermal" plus one target
"thermal coupling of the reactor vessel"; `query("thermal", limit=50)` returns 50 ids
and **excludes the target**. This is the same defect class as P1-1 but does not need a
domain filter: any query with more than 50 trigram matches silently loses later facts
before ranking. P1-1's fix should cover both (rank-ordered, scope-aware candidate
selection with a bounded budget).

### N2 (P1) — Raw user text is passed to FTS5 `MATCH`

The query text is used verbatim as FTS5 query syntax. Measured on a real FTS5 trigram
index: `thermal "coupling` (unterminated string), `reactor: vessel` (column filter →
`no such column: reactor`), `NOT thermal`, `thermal AND` all raise
`sqlite3.OperationalError`, which is caught and returns `[]`. The pipeline then takes the
"0 candidates" branch: bounded fallback to the **1 000 most recently updated facts**
(`get_fact_ids(limit=1000)` orders by `updated_at DESC`). A user query containing a
quote or a colon thus silently switches retrieval mode and makes older facts invisible.
Read-only, so not a Canon-integrity issue, but it is an unreported retrieval-mode change.
Fix: quote/escape terms (or build the MATCH expression from tokens) and report the
fallback reason in the trace.

### N3 (P2) — Bounded fallback is recency-capped before the domain filter

When the NGram index is unavailable or returns no ids, `_narrow_candidates` loads the
1 000 most recently updated facts and only then applies the domain filter. On a store
larger than 1 000 facts the same loss as P1-1 occurs without any NGram involvement.
Should be covered by the same candidate-selection fix and regression test.

### N4 (P1, priority raise) — Observer is enabled in the production compose profile

`docker-compose.prod.yml:100` sets `ENABLE_OBSERVER=1`. Therefore P1-2's
"Observer crash reports `observer: null`, same as disabled" and issue #512's lexical
faithfulness `allow/clean` on contradicting answers apply to the **selected production
profile**, not to an opt-in experiment. This raises the priority of machine-readable
check status on the `/query` boundary (and of #509 → #521 → #522) above the
background-work items.

### N5 (P2) — `/chat` and `/chat/stream` still return raw internal exception text

On `main` and on `#514@0aa60be`: if `pipeline_run` raises, `pipeline_error = str(exc)`;
when the console fallbacks find no facts, that string is returned in the response
`error` field (`/chat`) and the corresponding stream path. `/query` already maps the
same failure to `"Internal server error"`. This is internal (SQLite / path / pipeline)
text, not provider text, so it is outside #514's stated provider scope, but it is the
same disclosure class as #511. Recommend a follow-up (or an addition to #514) that
returns a stable code plus event id and logs the detail.

### N6 (docs) — Stale #515 references

Corrected in this branch (`docs/ai/KNOWN_RISKS.md`): #515 merged 2026-11-14 as
`485c4b0`; the labels are on `main`.

## 6. Priority and merge order

The Astra 6 order is supported by the evidence above, with two adjustments.

1. **#514** (security) and **#523** (Canon admission / evidence integrity) — first
   independent review. Add to #514 or a follow-up: N5.
2. **#509** — standalone after review; then **#521 → #522**. Because Observer is on in
   the production profile (N4), this stack is higher priority than its Draft status
   suggests.
3. **New owning fix (no PR yet): retrieval candidate selection** — P1-1 + N1 + N2 + N3
   in one place (`core/pipeline.py::_narrow_candidates` and
   `core/ngram_index.py::query`). It is independent of #525/#530 and should be its own
   small PR from `main` (after #523, which touches the same file).
4. **New owning fix: `/query` check status** — expose `reason_code`,
   `insufficient_evidence`, and an Observer status that distinguishes
   `disabled` / `ok` / `failed` (P1-2). Lands on top of #523.
5. #524, then the #525 stack (#526, #527, #528, #529) after #523, as in the Astra 6 table.
6. #531 stays Draft/default-off until the empty-poll cost is bounded (P1-4) — e.g. a
   partial index or a separate "pending" table, so the claim query does not scan
   acknowledged history inside `BEGIN IMMEDIATE`.
7. #500, #506, #520: narrow, green, mergeable after normal review. #530 stays
   DO NOT MERGE. #503/#508/#517/#518/#473 per the Astra 6 table.
8. Close #501 with a reference to #502 / `1a7141c6`.

## 7. Required regression tests for the new fixes

- Candidate selection: 51+ matches where the only `science` fact and the best-ranked
  fact are outside the first 50 in storage order → must be returned for
  `domain="science"` and for the unscoped query, within the bounded budget, without
  leaving the requested scope.
- FTS5 syntax: queries with `"`, `:`, `NOT`, `AND`, `*`, `(` must not raise and must
  not silently fall back; the fallback reason must be visible in the trace.
- `/query` boundary: forced FactsPack policy failure → response carries
  `insufficient_evidence=true` and `reason_code="facts_pack_policy_unavailable"`;
  Observer exception → `observer.status="failed"` distinct from flag-off.
- `/chat`: forced pipeline exception with empty fallbacks → no exception text in the
  response; stable code and event id only.
- Dispatcher: empty-poll VM steps (via `set_progress_handler`) must not grow linearly
  with acknowledged history.

## 8. Reality status of the items above

| Item | proposed | implemented | tested | wired | enabled | observed |
|---|---|---|---|---|---|---|
| Safe LLM errors (#514) | yes | PR only | PR tests (not re-run here) | PR only | — | no |
| Admission/evidence fixes (#523) | yes | PR only | 109 targeted + 5 previously failing pass here | PR only | — | no |
| Candidate-selection fix (P1-1/N1–N3) | this audit | no | no | no | no | no |
| `/query` check status (P1-2) | this audit | no | no | no | no | no |
| FTS dispatch runtime (#531) | yes | PR only | not re-run here | PR only (opt-in) | default off | no |
| Observer | — | yes (`main`) | yes | yes | **yes in `docker-compose.prod.yml`** | not verified here |

## 9. Limits of this audit

- No live providers, production load, Docker build, or Git-history secret scan.
- `embeddings` extra not installed; dense retrieval paths were not exercised.
- P1-1 was reproduced with a real FTS5 index and the real `_narrow_candidates`, but with
  an in-memory fact lookup instead of the full SQLite fact store.
- Targeted test counts reported by Astra 6 for #524–#531, #500, #514 and #509, and the
  #530 coverage figure, were not re-run here unless stated in §3/§4.
