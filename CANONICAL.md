# 🏛️ Titan Canonical Authority Index

> **Status:** CURRENT AUTHORITY INDEX  
> **Project:** Velantrim ExoCortex Titan 9.0  
> **Purpose:** make the repository's sources of truth explicit so historical copies, research artifacts, snapshots, and live GitHub state cannot be mistaken for one another.

## 1. Repository and code authority

For the state of Titan code, the canonical repository is:

`velantrian/Velantrim-ExoCortex-Titan`

The default branch is `main`.

For **live repository facts** — current `main` HEAD, open/closed PRs and Issues, exact-head CI, reviews, merge state, branch rules, and workflow results — query GitHub directly. A dated document, audit, Notion page, or retained evidence snapshot does not override newer live GitHub state.

## 2. Public version authority

The current public version is defined by the repository's version contract:

- `pyproject.toml`
- `core.__version__`
- the version exposed by `server.py` / `/api`

See [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) for the verification procedure. Historical version strings in archived documents and comments are not current release authority.

## 3. Machine-readable project-state authority

[`docs/state/project_state.json`](docs/state/project_state.json) is Titan's machine-readable **bounded project-state checkpoint** and is CI-validated by `scripts/check_project_state.py`.

It must be read according to its own `verified_at`, SHA fields, and `head_semantics`. It is not an evergreen claim that its recorded repository SHA equals today's live `main` HEAD.

Therefore:

`live GitHub state != dated project-state checkpoint`

Both are valid evidence for different questions.

## 4. Architecture and governance authority

Current architecture/governance documents define their declared contracts and boundaries. In particular, preserve these distinctions:

- `research != runtime`
- `spec != implementation`
- `retrieval != evidence`
- `receipt != truth`
- `evidence != authority`
- `CI green != production authorization`
- `historical snapshot != current state`
- `compatibility path != canonical path`

A research document, experiment, fixture, issue, or successful CI run cannot silently grant Canon, ESM, TruthGate, policy, tool, scheduler, or production authority.

## 5. GitHub ↔ Notion precedence

Notion is a synchronized project/documentation surface and may contain decision history, rationale, research, and lifecycle records. For repository-local facts that can change independently — commit SHA, PR state, Issue state, workflow result, review state, mergeability — **fresh GitHub state has precedence**.

A Notion record remains valuable evidence of what was recorded at a point in time; it must not be treated as a substitute for a fresh exact-state GitHub check.

## 6. Historical V8.x material

The previous contents of this file described a local Windows folder for **Velantrim V8.6** and warned about multiple non-git local copies. That record was useful during the 2026-05-31 consolidation period, but it is **historical context, not current Titan authority**.

Older V8.x documents, migration notes, local paths, audit snapshots, and archived copies may be retained for provenance and design history. They must be interpreted as historical unless a current document explicitly adopts their semantics.

In particular, a local path such as the former V8.6 working directory is not allowed to override this GitHub repository as the code source of truth.

## 7. Safe interpretation rule

When sources disagree, classify the question before choosing the source:

| Question | Prefer |
|---|---|
| What code is on `main` now? | Live GitHub |
| Is a PR/Issue open, merged, or closed now? | Live GitHub |
| Did exact-head CI/review run for a candidate? | GitHub checks/reviews bound to that SHA |
| What did a bounded checkpoint record? | `docs/state/project_state.json` + retained evidence |
| What is the current public Titan version? | Version contract in repository code/config |
| What architectural boundary was explicitly specified? | Current architecture/governance docs |
| What was historically believed or tested? | Dated audit/evidence/history artifacts |
| What was synchronized into project documentation? | Notion record, with its recorded date/SHA |

## 8. Mutation boundary

This authority index does not authorize runtime activation, production deployment, Canon mutation, ESM mutation, policy change, auto-merge, or deletion of historical material.

Its purpose is narrower: **make source authority explicit and prevent stale or historical material from masquerading as current truth.**
