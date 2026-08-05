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
- its shadow extractor was proposal-only and default-off, but listed unresolved
  hardening before ARM-04;
- required hardening included extraction-only confidence naming, subject/context identity,
  retention reasons, prompt-to-memory injection handling, privacy-safe source evidence
  serialization and a real supersession contract.

### Changed

- rebuilt ARM-03 from current `main` rather than merging/rebasing the stale branch;
- added the canonical default-off feature flag and runtime readout;
- added a bounded dependency-free candidate extractor with exact source offsets and
  SHA-256 span hashes;
- added `extraction_confidence`, `subject_ref`, `context_id` and `RetentionReason`;
- added bounded English/Russian instruction-shaped memory-injection detection with
  default rejection;
- added redacted `to_safe_dict()` representations and removed raw span text from repr;
- added deterministic within-input `POSSIBLE_UPDATE_OF` hints;
- added focused contracts, speed tests, benchmark, replay fixture and blocking workflow;
- updated current state, component map, risk register and speed/safety documentation.

### Validation

- ARM-03 workflow passed Ruff, blocking mypy, focused tests, benchmark and evaluation
  replay on the cleaned branch;
- Docker hardening checks passed on the cleaned branch;
- full Titan CI is required on the final documentation-consolidated head before merge;
- exact final run IDs and head SHA are recorded in PR #200.

### Decisions

- candidate extraction remains proposal-only and cannot admit or persist memory;
- exact raw source text may exist only as protected in-process evidence for offset/hash
  verification; portable output uses the redacted safe serializer;
- `.confidence` is a read-only compatibility alias and never truth confidence;
- supersession remains a bounded hint, not durable reconciliation;
- injection detection is a safety filter, not complete semantic detection;
- ARM-04 remains a separate operator-approved admission design.

### Remaining

1. obtain green full CI on the final head;
2. synchronize the final tested head and evidence to Notion;
3. merge PR #200 only after all final-head gates pass;
4. close old PR #102 as superseded after the merge;
5. measure candidate precision/privacy before any ARM-04 work.

## 2026-08-05 — Connectorless GitHub → Notion hand-off contract

**Scope:** PR #199; merged as `e15811f20dd812282a9855dad38771528f6d7457`

### Changed

- added the GitHub completeness invariant;
- added `docs/ai/NOTION_HANDOFF.md`;
- defined `HANDOFF_REQUIRED`, `SYNCED`, `NOT_REQUIRED` and
  `BLOCKED_PRIVACY_OR_PERMISSION`;
- updated agent rules, AI navigation, synchronization protocol and PR template.

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

- added the detailed Project Cognition & Code Review use case;
- linked it from README and a use-case index;
- synchronized the deeper rationale and PC-01…PC-06 roadmap to Notion.

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
- expanded mandatory agent rules and PR checklist;
- separated current state, components, risks, audit method and work history.

### Key findings retained

- Continuity requires a clean current-main rebuild;
- projection delivery lacks runtime lifecycle wiring;
- Identity remains legacy/unwired;
- deployment, coverage/static scope, concurrency, supply-chain and packaging risks remain.
