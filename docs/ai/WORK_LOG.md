# 🧾 AI Engineering Work Log

This is the concise hand-off log for architecture-significant work. New entries go at
the top. It complements Git history, PR discussion, ADRs and current code.

For older history, see [`../../COLLAB_JOURNAL.md`](../../COLLAB_JOURNAL.md). Re-verify
historical claims before using them as current truth.

## Entry template

```markdown
## YYYY-MM-DD — Short title

**Scope:** PR/issue/commit/component

### Verified before change
### Changed
### Validation
### Decisions
### Remaining
```

Use exact status words: proposed, implemented, tested, wired, enabled and observed.

---

## 2026-08-05 — ARM-03 selective-memory recovery from current main

**Scope:** PR #200; branch `agent/arm03-selective-memory-recovery`; base
`main@649d12953eb141aa783729555861e788cc03c150`

### Verified before change

- old PR #102 was based on stale `main` and was not mergeable;
- its extractor was proposal-only and default-off but left hardening unresolved;
- missing contracts included extraction-only confidence naming, subject/context identity,
  retention reasons, prompt-to-memory injection handling, privacy-safe source evidence
  serialization and a non-empty supersession design.

### Changed

- rebuilt ARM-03 from current `main` instead of merging the stale branch;
- added the canonical default-off feature flag and runtime readout;
- added a bounded dependency-free extractor with exact source offsets and SHA-256 hashes;
- added `extraction_confidence`, `subject_ref`, `context_id` and `RetentionReason`;
- added bounded English/Russian instruction-shaped injection detection with default
  rejection;
- added redacted safe serialization and excluded raw span text from repr;
- added deterministic within-input `POSSIBLE_UPDATE_OF` hints;
- added focused tests, speed tests, benchmark, replay and blocking workflow;
- added an accepted ADR for proposal-only authority;
- updated current state, component map, risk register and hand-off documentation.

### Validation

On tested head `125cf0b008f3fc0c0589dc248f1449b5a865e883`:

- ARM-03 contracts run `31011184457`: success;
- Docker hardening run `31011184150`: success;
- full Titan CI run `31011183017`: success;
- architecture-freeze, Ruff, blocking mypy, focused tests, full pytest, benchmark and
  evaluation replay passed.

Final PR-head checks after documentation-only finalization remain the merge authority.

### Decisions

- candidate extraction remains proposal-only and cannot admit or persist memory;
- exact raw source text may exist only as protected in-process evidence for offset/hash
  verification; portable output uses the redacted safe serializer;
- `.confidence` is a read-only compatibility alias and never truth confidence;
- supersession remains a bounded hint, not durable reconciliation;
- injection detection is a safety heuristic, not complete semantic detection;
- ARM-04 requires a separate ADR, PR and operator decision.

### Remaining

- merge PR #200 only after final-head checks pass;
- close PR #102 as superseded after merge;
- measure candidate precision and privacy behavior before ARM-04;
- keep runtime wiring and admission out of scope until separately approved.

## 2026-08-05 — Connectorless GitHub → Notion hand-off contract

**Scope:** PR #199; merged as `e15811f20dd812282a9855dad38771528f6d7457`

### Changed

- added the GitHub completeness invariant and `docs/ai/NOTION_HANDOFF.md`;
- defined connectorless and privacy/permission synchronization states;
- updated agent rules, AI navigation, sync protocol and PR template.

### Validation

CI run `31008743181` passed branding, hygiene, architecture freeze, Ruff, blocking mypy
and full pytest. Notion contains the final merge SHA and evidence.

### Decision

Missing Notion connector access does not stop GitHub analysis. A connectorless actor
completes the public record and creates a hand-off; a connected actor verifies and
synchronizes it.

## 2026-08-05 — Project Cognition use-case documentation

**Scope:** PR #196; merged as `649d12953eb141aa783729555861e788cc03c150`

### Changed

- added the Project Cognition & Code Review use case;
- linked it from README and the use-case index;
- synchronized the PC-01…PC-06 roadmap to Notion.

### Validation

CI run `31009057160` passed branding, hygiene, architecture freeze, Ruff, blocking mypy
and full pytest.

### Decision

Project Cognition remains `RESEARCH / PROPOSED`: no repository-wide ingestion, Project
ContextPack runtime or automatic GitHub comments are claimed.

## 2026-08-05 — AI context navigation and audit hand-off

**Scope:** PR #198; merged as `bb87ea4f00a68581c2365e63f833a366e810289b`

### Changed

- created the compact `docs/ai/` orientation pack;
- expanded agent rules and PR checklist;
- separated current state, components, risks, audit method and work history.

### Key findings retained

- Continuity requires a clean current-main rebuild;
- projection delivery lacks runtime lifecycle wiring;
- Identity remains legacy/unwired;
- deployment, verification scope, concurrency, supply-chain and packaging risks remain.
