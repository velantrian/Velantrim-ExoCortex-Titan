from __future__ import annotations

from pathlib import Path

WORK_LOG = Path("docs/ai/WORK_LOG.md")
SCRIPT = Path(".github/scripts/temporary_append_openloop_work_log.py")
WORKFLOW = Path(".github/workflows/temporary-openloop-work-log.yml")

MARKER = """# 🧾 AI Engineering Work Log

Re-verify exact SHAs and current PR evidence.

---

"""

ENTRY = """## 2026-08-07 — OpenLoop source adapter merged and canonical checkpoint

```text
Documentation impact: GITHUB_AND_NOTION
Verified main:        42aa79338c57e9b9a67c3e3c08dd948b60c5541f
Implementation PR:    #240
Exact tested head:    9623d60f262d00ab4551f5342f7ef1792723e594
Runtime authority:    NONE
Notion state:         SYNCED
```

### Intent

Complete the third bounded Continuity source adapter and restore one coherent
GitHub + Notion current-state record before beginning admission evaluation.

### Decision

Implement OpenLoop v2 as an evidence-only proposal adapter. Recompute the
identities actually available in `OpenLoopProjectionResult`, validate complete
subject and binding evidence, and stop at `ContinuityObservationDraft`.
Do not claim to recompute original signal/resolution payload identities because
the result contract contains only their content-addressed references.

### Implementation

PR #240 added:

- `core/continuity/open_loop_source_adapter.py`;
- the main adversarial adapter suite;
- a result-level `as_of` ownership regression;
- a binding-receipt chronology regression.

Only `OPEN` and `OVERDUE` projections may derive
`EVIDENCE_COVERAGE_ITEM=True`. `RESOLVED` and `NOT_YET_OPEN` derive no positive
Draft. Summary, kind, due date, related goal and loop key grant no reminder,
scheduling, action, current-state, answer, tool, delivery or compute authority.

### Evidence

```text
Pre-merge CI + coverage       31168858623 PASS
Pre-merge Continuity          31168858622 PASS
Pre-merge Docker              31168858691 PASS
Pre-merge aggregate           31200451054 PASS
Unresolved review threads     0
Merge SHA                     42aa79338c57e9b9a67c3e3c08dd948b60c5541f
Post-merge CI + coverage      31200627655 PASS
Post-merge Continuity         31200627704 PASS
Post-merge Docker             31200627678 PASS
Post-merge aggregate          31200627647 PASS
```

Codex did not provide a substantive review because its code-review usage limit
was reached. This remains unavailable evidence and was not treated as approval.

### Documentation synchronization

The canonical checkpoint updates:

- `docs/ai/CURRENT_STATE.md`;
- `docs/ai/COMPONENT_MAP.md`;
- `docs/ai/KNOWN_RISKS.md`;
- `docs/ai/WORK_LOG.md`;
- `docs/ai/CONTINUITY_SOURCE_ADMISSION_HANDOFF.md`.

Notion records `🧭 Velantrim Titan 9.0 🗺️` and
`🔐 Continuity Source Admission — Architecture` were updated with the final
merge SHA, pre/post-merge evidence, readiness and next bounded slice.

### Resulting status

```text
State adapter             IMPLEMENTED · TESTED · INTERNAL · UNWIRED
Goal adapter              IMPLEMENTED · TESTED · INTERNAL · UNWIRED
OpenLoop adapter          IMPLEMENTED · TESTED · INTERNAL · UNWIRED
Continuity live readiness 5/12 = 41.7%
Runtime                   NOT WIRED · NOT ENABLED · NOT OBSERVED
```

### Remaining work

1. deterministic admission evaluator and allowlisted evaluator/rule registry;
2. current principal/tenant/subject authorization, consent, restriction,
   erasure and policy resolution;
3. admission-aware facade and anti-bypass guards;
4. durable retention, replay and cleanup only after privacy proofs;
5. runtime wiring, activation ADR, feature flag, operator controls and observed
   disabled-shadow evidence;
6. administrator enforcement of the aggregate status and CODEOWNERS through
   repository rules (issue #234).

### Next safe slice

Implement the pure internal evaluator only:

```text
validated envelope + complete Draft set
+ immutable allowlisted evaluator/rule definitions
+ explicit current decision evidence
→ complete deterministic allow/deny partition
→ immutable admission receipt
→ optional bounded authorized batch
→ STOP
```

No producer invocation, persistence, public facade, `/query`, startup, worker,
scheduler, feature flag, Canon/ESM/TruthGate/GoalStack write or user-visible
authority belongs in that slice.

---

"""


def main() -> None:
    text = WORK_LOG.read_text(encoding="utf-8")
    if text.count(MARKER) != 1:
        raise SystemExit("work-log header marker must match exactly once")
    if "## 2026-08-07 — OpenLoop source adapter merged and canonical checkpoint" in text:
        raise SystemExit("work-log entry already exists")
    WORK_LOG.write_text(text.replace(MARKER, MARKER + ENTRY, 1), encoding="utf-8")
    SCRIPT.unlink()
    WORKFLOW.unlink()


if __name__ == "__main__":
    main()
