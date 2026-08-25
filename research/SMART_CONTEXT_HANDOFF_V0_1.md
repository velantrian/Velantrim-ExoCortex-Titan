# 🧠 Smart Context / Handoff v0.1

**Status:** `RESEARCH DESIGN · SHADOW CANDIDATE · NOT CANON · NOT RUNTIME AUTHORITY`  
**Primary implementation host:** Titan research/shadow infrastructure  
**Continuity research reference:** Velantrim Continuum  
**V1 impact:** none — this is not Titan Stage 12 and does not reopen Titan V1

## 1. Goal

Preserve enough explicit work/process state for a successor AI context to continue long-running human↔AI work correctly after context-window replacement, without treating a transcript, one model instance, or an AI-generated summary as durable truth.

The long-lived object is the work/process state, not a particular chat window.

```text
              🧬 LONG-LIVED WORK
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Chat A        Chat B       Chat C
        │            │            │
        └────────────┼────────────┘
                     ▼
              🧠 Process State
```

## 2. Interaction model

```text
👤 Human ↔ 🤖 Working AI (Window A)
                │ semantic observation
                ▼
         🧩 Context Observer (Window B)
```

The Context Observer is a bounded sidecar role. It does not answer instead of the Working AI, silently mutate project state, approve decisions, or gain authority merely because it observes the session.

Its only responsibility is to maintain a compact, explicit candidate `ContextState` and meaningful `StateDelta` records for shadow evaluation.

## 3. Candidate ContextState contract

```yaml
schema: smart-context-state-v0.1
session_id:
project:
goal:
current_state:
completed:
decisions:
rejected_or_deferred_paths:
constraints:
open_questions:
blockers:
artifacts:
evidence_refs:
external_state_refs:
last_transition:
next_step:
obsolete_or_drop:
handoff_notes:
```

Interpretation rules:

- fields are explicit process-state candidates, not Canon;
- absent information remains absent/unknown rather than inferred as settled;
- user statements, external evidence, and model inference must remain distinguishable;
- artifact references do not imply the referenced artifact is still authoritative;
- current external state must be revalidated before protected action.

## 4. StateDelta

The Observer should track semantic transitions instead of repeatedly summarizing the whole transcript.

```text
S(t-1) → S(t)
```

Example:

```text
BEFORE
fragmented first-run path
PR draft
ordinary-user bootstrap not unified

AFTER
bounded cross-platform bootstrap
safe .env handling
loopback health wait
review remains open
```

A delta should capture only a meaningful change to goal, position, decision, constraint, blocker, artifact state, or next action.

## 5. Context pressure and rollover

The first research hypothesis is that a rollover can be handled by freezing the latest explicit process state and generating a minimal successor package.

```text
OLD WINDOW
    ↓
🧩 semantic consolidation
    ↓
📦 SuccessorContextPack
    ↓
NEW WINDOW / NEW INFERENCE INSTANCE
    ↓
continuation verification
```

`SuccessorContextPack` should preserve only still-useful state:

- current goal;
- current position;
- completed work;
- accepted decisions;
- rejected/deferred paths when still relevant;
- constraints and prohibitions;
- open loops and blockers;
- relevant artifacts/evidence references;
- last meaningful transition;
- next bounded step.

It should preferentially drop repetition, obsolete plans, superseded artifacts, resolved intermediate reasoning, and raw transcript content that no longer changes the continuation decision.

No context-pressure threshold is frozen by this document.

## 6. Ownership boundaries

| Surface | Responsibility | Non-responsibility |
|---|---|---|
| 🗿 Titan | candidate Observer execution, conversation/thread composition, ContextState assembly, shadow UI experiments | no new truth/identity/Canon authority |
| 🌎 Continuum | falsifiable research on minimum sufficient continuation state and rollover quality | no automatic Titan integration/runtime authorization |
| 💠 Crystal | optional admitted evidence/provenance references | Observer output or summary is not automatically Crystal Canon |
| 🌀 Mentaury Soul | possible future human-facing interpretation if separately authorized | second-model analysis is not identity/belief authority |
| 🧬 Native Kernel | technology-neutral semantic invariants for provenance, uncertainty, lineage and non-escalation | no runtime orchestration role |
| 🪁 Mentaury Kernel | cross-domain transfer/composition constraints | no central authority |
| 🗺️ Knowledge Atlas | orientation/navigation to relevant project state/contracts/docs | not the live process-state store and not an owning-project override |

Core design rule:

```text
Titan executes a bounded shadow candidate.
Continuum defines/tests what continuation requires.
```

## 7. Required non-conflation invariants

```text
observer summary != fact
state delta != decision authority
handoff != Canon
context survival != identity continuity
conversation continuity != epistemic truth
retrieved artifact != current authoritative state
second AI analysis != independent approval
separate AI session != automatically independent reviewer
automatic rollover != authorization to mutate external systems
shadow usefulness != production authorization
```

## 8. Shadow-only candidate flow

```text
ConversationEpisode / explicit user+tool events
                ↓
        bounded Observer pass
                ↓
          ContextState v0.1
                ↓
             StateDelta
                ↓
       SuccessorContextPack
                ↓
       simulated successor
                ↓
      continuation evaluation
```

The candidate must remain read-side/shadow-only. No live reminder, answer modification, tool action, Canon write, project mutation, or external-system mutation follows from Observer output.

## 9. Evaluation surface

Evaluate at minimum:

- goal retention;
- decision retention;
- constraint/prohibition retention;
- task-position retention;
- open-loop retention;
- blocker retention;
- provenance/reference retention;
- ambiguity preservation;
- hallucinated-state rate;
- superseded/obsolete carryover;
- successor task-continuation success;
- replay/order consistency;
- handoff size/context efficiency.

Hard-fail examples for a future shadow evaluation contract:

- inventing a user decision;
- dropping an explicit prohibition that remains active;
- reviving a superseded decision as current;
- converting model inference into user attestation;
- presenting stale external state as freshly verified;
- treating handoff content as Canon/approval/authority;
- mutating external state from the Observer path.

No weighted single continuity score is defined here.

## 10. Bounded development sequence

1. **Contract only:** stabilize `ContextState v0.1`, `StateDelta`, and `SuccessorContextPack` semantics.
2. **Shadow Observer:** generate candidate state from bounded recorded sessions with zero runtime authority.
3. **Offline evaluation:** compare candidate state against human-authored continuation references.
4. **Simulated rollover:** feed only the successor pack to a fresh inference instance and measure continuation quality.
5. **Replay/adversarial tests:** reordered events, stale artifacts, conflicting decisions, ambiguous user language, missing evidence.
6. **Optional UI:** only after the state model is useful enough, expose a separate read-only Context Observer panel.
7. **Any live activation:** requires a separate owning-project decision and is outside this document.

## 11. Reuse before new machinery

A future implementation should first evaluate reuse of existing Titan Continuity components such as conversation episodes/threads, `ContinuityContextPack`, WorkingMemory adapters, replay evaluation, hard gates, and the disabled shadow runner. This document does not assert that those components already satisfy Smart Context semantics.

Do not build a second prompt pack, second PolicyKernel, second truth gate, global authority router, or giant transcript database merely to support this research track.

## 12. Continuum relationship

Continuum already researches the stronger question:

> What explicit durable state is sufficient for functional continuation after replaceable inference disappears?

Smart Context/Handoff is therefore a concrete application/research candidate, not a replacement for Continuum Experiment 0 and not evidence that any richer process-state architecture is required.

The simple baseline remains valid: a carefully maintained current-state representation may outperform or make unnecessary a more complex observer architecture.

## 13. Promotion / stop rule

This document is a research contract only.

```text
documented
!= implemented
!= tested
!= wired
!= enabled
!= observed
!= production authorized
```

Stop after documentation unless a separate bounded implementation scope is explicitly selected. Titan V1 remains closed; this work must not be described as a mandatory post-V1 stage.
