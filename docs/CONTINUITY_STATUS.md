# Continuity Milestone 1 — Stack Status

**Current `main`:** `0d07bc9f74a4e8e0bf4a0d615a0bb40ec529f5e7`  
**Stack state:** 15 open draft PRs · not merged to `main` · no `/query` wiring  
**Required posture:** shadow-only until scope, privacy, durable ledger, replay and failure-isolation gates pass.

## Correct dependency order

### Foundation

1. #131 — architecture baseline
2. #132 — immutable continuity contracts
3. #133 — neutral in-memory shadow ledger
4. #135 — read-only conversation bridge
5. #136 — deterministic Thread Weaver
6. #138 — Continuity/Synaptic ownership ADR

### Composition

7. #139 — shadow ContinuityContextPack
8. #140 — conversation-to-WorkingMemory adapter
9. #141 — current-state reconciler
10. #142 — qualified goals and typed open loops
11. #143 — projection-to-WorkingMemory adapter
12. #144 — continuity-aware ComputeController signals

### Evaluation

13. #145 — replay evaluation and hard gates
14. #146 — Advisory Shadow gate
15. #147 — complete Milestone 1 shadow runner

PR #134 and PR #137 are Reader Core PRs and are not Continuity stack members.

## Merge posture

Before the first merge:

- rebase #131 onto current `main`;
- run one holistic integration build of the complete stack;
- add minimal `SubjectScope(owner_ref, namespace_ref)`;
- enforce privacy non-widening;
- use Reality Lock observation states so unavailable/failed observers cannot pass;
- define and implement a durable SQLite shadow-ledger follow-up;
- prove shadow failure cannot change the answer or write Canon.

Before every sequential merge:

- pin expected head SHA;
- resolve all blocking review threads;
- run focused and full Titan CI;
- prove no new runtime authority;
- rebase the next PR and remove already merged diff.

## User activation boundary

`ASK_CONFIRMATION`, `REMIND`, `SUGGEST`, `WARN`, Canon promotion, external actions and notifications remain unauthorized. Candidate generation may be evaluated only in isolated shadow mode until owner dogfooding produces safety and utility evidence.
