# 🧾 AI Engineering Work Log

This is the concise hand-off log for architecture-significant work. New entries go at
the top. Re-verify historical claims before treating them as current truth.

---

## 2026-08-05 — Continuity R1 rebuilt on current main

**Scope:** PR #201; branch `agent/continuity-r1-foundation`; base
`main@bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`

### Verified before change

- `core/continuity/` was absent from current `main`;
- historical PRs #131–#147 formed a stale stacked chain and were not suitable for direct
  sequential merge;
- the R1-owned material was the architecture baseline, immutable contracts, golden
  vectors and focused conformance gate;
- a local regression check found that string assertion values also require NFC
  normalization to preserve deterministic identity.

### Changed

- rebuilt only R1 contracts on current `main`;
- added immutable actor/subject references, events, assertions and relations;
- canonicalized text with NFC and aware datetimes as UTC microseconds;
- restricted assertion values to immutable finite JSON scalars;
- added sorted duplicate-free provenance refs, canonical JSON and SHA-256 identities;
- added fixed golden vectors, focused tests and NFC/authority regression tests;
- added a path-scoped Ruff/mypy/pytest workflow;
- added an accepted ADR preserving existing ESM, Canon, WorkingMemory, ContextPack,
  ComputeController, advisory and action owners;
- updated current-state, component and risk documentation.

### Validation

- local isolated contract suite: 22 passed before repository integration;
- GitHub continuity workflow, full Titan CI and Docker remain required on final PR head;
- exact final evidence will be recorded in PR #201 and Notion.

### Decisions

- R1 is contract construction and validation only;
- origin, truth disposition and projection status remain separate axes;
- assertions remain immutable; lifecycle is represented through explicit relations;
- no DB, ledger, runtime, Canon, gate, compute, advisory or action authority is added;
- old #131/#132 are superseded only after PR #201 merges; later old PRs remain source
  material until their owning recovery layer exists.

### Remaining

1. green final-head continuity workflow, full CI and Docker;
2. final Notion synchronization and merge;
3. close old #131/#132 as superseded;
4. start R2 as a new independently green PR for ledger, read-only conversation bridge
   and deterministic thread links.

## 2026-08-05 — ARM-03 selective-memory recovery

**Scope:** PR #200; merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`

- rebuilt stale PR #102 from current `main`;
- added proposal-only extraction hardening, privacy-safe portable serialization,
  injection rejection, focused CI, benchmark, replay and ADR;
- final runs: ARM-03 `31011800847`, Docker `31011800065`, full CI `31011799630` — all
  successful;
- old PR #102 closed as superseded;
- status remains `MAIN + TESTED + DEFAULT OFF / NOT WIRED / NO ADMISSION`.

## 2026-08-05 — Connectorless GitHub → Notion hand-off

**Scope:** PR #199; merged as `e15811f20dd812282a9855dad38771528f6d7457`

GitHub now carries complete public technical/audit continuity. Missing Notion connector
access produces a structured `HANDOFF_REQUIRED`, not an abandoned task or false `SYNCED`
claim.

## 2026-08-05 — Project Cognition use-case

**Scope:** PR #196; merged as `649d12953eb141aa783729555861e788cc03c150`

Project Cognition is documented as `RESEARCH / PROPOSED`; no repository-wide runtime,
Project ContextPack execution or automatic GitHub comments are claimed.

## 2026-08-05 — AI context navigation

**Scope:** PR #198; merged as `bb87ea4f00a68581c2365e63f833a366e810289b`

Created the compact current-state, component, risk, audit and hand-off layer for AI and
human maintainers.
