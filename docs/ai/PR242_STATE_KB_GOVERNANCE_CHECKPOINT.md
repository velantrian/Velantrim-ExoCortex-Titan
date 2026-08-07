# PR #242 — Machine-readable state and KB integrity checkpoint

**Documentation impact:** `GITHUB_AND_NOTION`  
**Notion access:** `NOTION_AVAILABLE`  
**Notion synchronization:** `PRE_MERGE_SYNCED`  
**Base:** `main@9dfbfe5822221550389d95b751c8d85b044f6372`  
**Implementation baseline represented:** `42aa79338c57e9b9a67c3e3c08dd948b60c5541f`  
**Runtime authority:** `NONE`  
**KB content change:** `NONE`

## Problem

After docs-only PR #241, the exact repository head was `9dfbfe582...`, while the
canonical GitHub and Notion summaries still called the earlier implementation merge
`42aa793...` the current `main`. This conflated three different roles:

- exact repository head at verification;
- latest implementation-bearing Continuity baseline;
- documentation checkpoint built on that implementation.

The portable `kb_graph.json` was also discussed as a large artifact without an explicit
preservation and portable-JSON integrity contract. The project already had deterministic
build/export tooling, a SQLite graph audit, and release-manifest SHA verification; the
missing piece was a non-duplicative portable graph boundary.

## Decision

1. Add `docs/state/project_state.json` as a machine-readable status projection.
2. Keep the three SHA roles separate and named.
3. Validate Continuity readiness arithmetic and fail-closed maturity ordering.
4. Preserve `kb_graph.json` under `KEEP_VERSIONED_KNOWLEDGE_ASSET`.
5. Extend the existing KB toolchain with portable graph referential-integrity checks.
6. Treat those checks as `ARTIFACT_INTEGRITY_ONLY`.
7. Do not change runtime, Canon, TruthGate, promotion, policy, answers, tools, actions,
   compute routing, startup, workers, schedulers, or Continuity readiness.

## Delivered surfaces

### Machine-readable status

- `docs/state/project_state.json`
- `scripts/check_project_state.py`
- `tests/test_check_project_state.py`

The state guard validates:

- complete 40-character SHA roles;
- `5/12 = 41.7%` readiness and `7/12 = 58.3%` remaining arithmetic;
- `enabled → wired`, `observed → enabled`, and runtime-authority ordering;
- explicit KB preservation policy;
- governance state, including the still-open ruleset gap.

### KB governance

- `docs/knowledge/KB_GRAPH_GOVERNANCE.md`
- `scripts/validate_kb_graph.py`
- `tests/test_validate_kb_graph.py`

The portable validator checks:

- JSON root and array shape;
- non-empty unique node IDs;
- supported edge endpoint contracts;
- dangling, duplicate and self edges;
- relation type presence;
- `meta.total_nodes` / `meta.total_edges` consistency;
- byte size and SHA-256 for the loaded asset.

It reuses rather than replaces:

- `core/world_skills_ingest.py`;
- `core/knowledge_linker.py`;
- `scripts/build_kb_graph.py`;
- `scripts/export_kb_graph.py`;
- `scripts/audit_kb_graph.py`;
- `scripts/verify_release_bundle.py`.

### CI and documentation

The primary CI now runs the project-state guard and validates the complete committed
`kb_graph.json` before Ruff, blocking mypy and pytest. Canonical AI context files now
separate repository head, implementation baseline and documentation checkpoint.

## Authority boundary

```text
portable graph parses
→ node/edge references are internally consistent
→ counts and SHA can be reproduced
→ STOP
```

It does not establish:

- truth or freshness of every claim;
- provenance or licensing completeness;
- deterministic equality with a fresh source rebuild;
- semantic quality of inferred relations;
- admission into Canon;
- current authorization, privacy or erasure compatibility;
- answer, action, tool, compute or runtime authority.

## Evidence state

Focused tests are committed. The exact final PR-head CI result is intentionally not
claimed inside this pre-merge checkpoint until GitHub Actions completes. The PR remains
Draft while CI and review are incomplete.

## Notion synchronization

Pre-merge Draft checkpoints were inserted at the top of:

- `🧭 Velantrim Titan 9.0 🗺️`;
- `🔄 Titan — Code ↔ Documentation Sync Protocol`.

They state that the KB is preserved, no runtime authority is added, and CI is pending.
Final merge SHA and post-merge evidence remain a required second synchronization step.

## Remaining work

1. administrator enforcement of the `main` ruleset and aggregate context — issue #234;
2. unified structural EvidencePolicy across TruthGate, WriteGate, recall and responses;
3. fail-closed TruthPolicy and final provider-answer validation;
4. separate current Notion views from historical checkpoints;
5. semantic before/after diff for future KB regeneration;
6. deterministic Continuity admission evaluator as a later independent slice.
