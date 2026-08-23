# Documentation Audit — 2026-08-23

**Scope:** accuracy/currency (точность и актуальность) and completeness/structure (полнота и структура) of this repository's documentation (`*.md`, README, `docs/`), assessed against a snapshot of the default branch on 2026-08-23. This is a documentation snapshot audit, not a code-quality or security review, and does not cover unmerged branches. Given the scale of this repository (2,475 markdown files), the bulk `docs/knowledge/world_skills_core/{en,ru}/` corpus (2,159 files) received a structural parity check rather than a file-by-file read; the remaining ~316 hand-maintained documentation files were read in depth.

## Overall Health Assessment

The maintained documentation (root docs + docs/ minus the bulk world_skills_core corpus) is **fair**: unusually disciplined for its size on file/path/command/config-key accuracy, and the project has a genuinely sophisticated status-tracking culture (docs/PROJECT_STATUS.md, AGENTS.md, docs/ai/*). But that same culture has proliferated into multiple parallel, mutually-unlinked status/reading-order systems that now disagree with each other, and a cluster of root-level "canonical" files (CANONICAL.md, root WORK_LOG.md, docs/HORIZONS.md, the RFC-008x set) is frozen at the V8.6/May-2026 era and was never re-synced or marked legacy when the project rebranded to Titan 9.0. Several ADRs also never got their status field updated after the PR they describe actually merged — exactly the proposed-vs-shipped contradiction this audit was asked to catch.

## Findings

1. **README.md** | accuracy | high | Root README's maturity ladder marks Working Memory Gate and ContextPack as merely "planned," but both are fully implemented, tested, and wired (core/working_memory_gate.py 573 lines, core/context_pack.py 995 lines, each with tests and consumers).

2. **README.en.md / SYSTEM_OVERVIEW.en.md** | accuracy | high | The English "companion" root docs are stale, structurally divergent forks of the Russian originals, and drop the mandatory AI-agent entry-point instructions entirely (zero mentions of AGENTS.md/docs/ai/README.md, vs 4+ mentions in the Russian README).

3. **docs/HORIZONS.md, docs/horizons/README.md** | accuracy | high | Both still declare themselves scoped to "VELANTRIM V8.6 Complex" even though the project rebranded to Titan 9.0, and HORIZONS.md is still linked from the current README.en.md.

4. **docs/archive/legacy/README.md** | structure | high | All three relative links in this "legacy version index" file are broken (off by one directory level) — the doc cannot reach the files it exists to point to.

5. **docs/adr/ADR-2026-08-10-causal-truth-edge-canonical-mutation.md + ADR-2026-08-10-archival-canonical-claim-convergence.md** | accuracy | high | Two ADRs remain frozen at "Proposed ... until protected merge" for PRs (#287, #285) that docs/ai/KNOWN_RISKS.md explicitly says are merged, with no cross-reference to the update.

6. **CANONICAL.md** | accuracy | high | Root file titled the canonical source of truth is entirely obsolete (pre-git, Windows-local-disk path, V8.6-era, line counts don't match actual server.py), no legacy banner, yet still cross-referenced by current docs (COLLAB_JOURNAL.md, CHANGELOG.md).

7. **docs/adr/README.md** | accuracy | medium | The ADR log's own naming-convention rule ("ADR-NNNN-short-title.md") is contradicted by every one of the 50 actual ADR files (all use ADR-YYYY-MM-DD-slug.md or similar).

8. **docs/adr/ADR-2026-08-15-csm-stage-c-explicit-scanner.md** | accuracy | medium | ADR status still reads "PROPOSED IN DRAFT PR #335" while docs/ai/CURRENT_STATE.md says Issue #333 is closed and PR #335 is merged.

9. **AGENTS.md vs docs/ai/README.md** | accuracy | medium | The two files that each define "the" mandatory AI-agent reading order disagree with each other on both order and content (10 items vs 12 items, different ordering).

10. **docs/PROJECT_STATUS.md vs docs/project_status/FOR_AI.json + FOR_HUMAN.md** | structure | medium | Two parallel, never-cross-linked "project status" tracks exist, reachable only from different entry points, with different dates (2026-08-14 vs 2026-08-21) and different in-flight items.

11. **docs/knowledge/KNOWLEDGE_0_OVERVIEW.md (+ KNOWLEDGE_1-6, KNOWLEDGE_BASE_LAWS)** | accuracy | medium | A hand-curated ~2,500-fact "v3.0" KB plan (~2026-05-20) is silently superseded by the far larger World Skills Core corpus (2,159 files), with zero cross-reference either way.

12. **docs/TITAN_EXECUTION_STATUS.md, docs/CONTINUITY_STATUS.md** | structure/accuracy | medium | Two dated status docs are completely unreferenced anywhere else in the repo and stale relative to later status (CONTINUITY_STATUS.md: "15 open draft PRs, not merged" vs KNOWN_RISKS.md: "Continuity: 12/12 = 100% complete"); TITAN_EXECUTION_STATUS.md also defines a third, parallel status vocabulary.

13. **docs/adr/ (continuity-r sub-series)** | structure | medium | Numbering gap: R1, R2, R4, R5a, R5b each have an ADR, R3 does not, despite having its own PR (#203) and handoff doc.

14. **WORK_LOG.md (root)** | accuracy | medium | The root work journal, still cited elsewhere as the project's log of record, hasn't been updated in three months (last entry 2026-05-20 of 749 lines) with no pointer to its actively-updated successor docs/ai/WORK_LOG.md.

15. **ROADMAP.md** | accuracy | medium | The root "Current Roadmap" (updated 2026-07-30) has zero mentions of the Continuity initiative despite it being reported elsewhere as 100% complete.

16. **docs/research/, docs/operations/** | structure | medium | The two largest maintained doc directories (36 and 33 files) have no README/index, unlike comparable directories (docs/adr, docs/horizons, docs/use_cases, docs/strategy, research/ all have one).

17. **research/archive/FUTURE_COMPONENTS_LEGACY_2026-07-30.md; docs/DEDUP_AND_SCALE_1M.ru.md** | structure | medium | Broken relative links off by one directory level to sibling docs/code.

18. **docs/knowledge/world_skills_core/{en,ru}/** | structure | low | Structural parity check: en/ (1077 files) vs ru/ (1082 files) differ by 1 EN-only placeholder and 6 RU-only structural/index files — EN side has no navigational index at all. Spot-checked 3 matched pairs, no gross content loss beyond normal translation variance.

19. **docs/CONTINUITY_AND_RESTART.ru.md vs the "Continuity" subsystem docs** | structure | low | Naming collision: "Continuity" denotes two unrelated concepts (process-restart/DB persistence vs. cross-session epistemic-continuity subsystem) with nothing disambiguating them.

20. **docs/ARCHITECTURE_RECONCILIATION_MAP.md, docs/RFC-0080/0081/0082_*.md** | structure | low | A cluster of substantive, dated (2026-05-31) architecture docs is undiscoverable from primary navigation (not linked from README.md, README.en.md, AGENTS.md, or docs/ai/README.md) and carries no legacy banner despite being explicitly V8.6-era.

---
*Generated by an automated documentation audit (Claude Code).*
