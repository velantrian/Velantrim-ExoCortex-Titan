# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.
Older detail remains traceable in Git history, merged PRs, issues, ADRs and dated checkpoints.

---

## 2026-08-13 — Post-ModelFreeCore hardening · DRAFT / REVIEW-STAGE

```text
main:                         e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96
main signature:               VERIFIED / valid
#50:                          CLOSED_COMPLETED · final REAL_GAP=0
#53:                          OPEN
#295 / #296:                  CLOSED_COMPLETED / MERGED
#297:                         OPEN · DRAFT · NOT MERGED
#297 base:                    main@e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96
pre-doc code/test head:       161c6ee3e60d11ea782d9d06525f72cfb2d7259f
independent formal approval:  NONE / NOT CLAIMED
Continuity:                   12/12
schema:                       v7
runtime enabled:              false
Operator GO:                  false
runtime authority:            false
production authority:         false
```

PR #296 put the explicit `ModelFreeCore` read-side facade on main, but no substantive
independent review occurred before merge. PR #297 is the bounded post-merge hardening
slice for logical failure paths found in #287/#296. It adds no runtime wiring, provider
or network execution, new mutation owner, Operator GO or production authority.

Codex has performed three substantive review rounds on #297. The first two rounds produced
11 actionable findings. Head `6bb577247fd8a672121cc2c0c420d88f4a261c6b` fixed all 11;
54/54 focused tests passed locally, Titan CI #1080 and Docker #700 were SUCCESS, and those
11 threads were resolved. A third round then found two P1 issues: read-side inverse
collapse trusted `inverse_of` without proving reciprocal identity, and this GitHub hand-off
still described the older review state.

The inverse-collapse defect is now fixed on the branch. Before semantic collapse,
`ModelFreeCore` validates every physical row and requires an `inverse_of` target to exist,
be the reciprocal relation tuple, match `inference_source`, carry no conflicting backlink,
and have at most one backlink. Dangling/conflicting/many-to-one identity fails closed via
`ModelFreeGraphReadError`. Dedicated adversarial regressions cover valid identity,
dangling target, non-reciprocal target, duplicate backlinks and bounded graph-read failure.

The code/test checkpoint before this documentation reconciliation is
`161c6ee3e60d11ea782d9d06525f72cfb2d7259f`; Titan CI #1082 was started for that exact
head. This docs update advances the branch, so #1082 cannot be reused as final-head proof.
Fresh Full CI and Docker are required on the new exact head before thread closure or READY
claims. PR #297 remains Draft, without protected merge or independent formal approval.

### Notion status

`Velantrim Titan 9.0` contains #296 FINAL and a historical #297 review checkpoint at
`6bb57724...`. The latter became stale after the third Codex round. Correct the same page
and read it back only after the current PR head/evidence is established. Do not create a
new Notion page.

---

## 2026-08-13 — #53 Phase 2 admission audit · READ-ONLY

Current-main audit found that Phase 2 must reuse existing policy ownership rather than
invent another global control plane.

`core/policy_kernel.py` already owns `EffectivePolicy`, `PolicySnapshot`,
`PolicyDecision`, `CapabilityLease` and `PolicyKernel.lease_capability()`. Its defaults
remain network deny, remote-data never, local canonical write, remote Canon forbidden,
mandatory WriteGate and fail-closed decisions with stable reason codes.

Classification:

```text
policy envelope / network / locality lease     ALREADY_CONVERGED
config + preset precedence                     PARTIAL
runtime flag facade                            PARTIAL
resource / retrieval budget                    PARTIAL
health / status                                PARTIAL
capability descriptor registry                 REAL_GAP
provider registry / provider health            REAL_GAP
selection explanation / trace metadata         PARTIAL / REAL_GAP
embedding / LLM / ADAO execution               OUT_OF_SCOPE
ARM-04                                         NOT AUTHORIZED / OUT_OF_SCOPE
```

The likely bounded Phase 2 gap is therefore a capability descriptor + provider-health +
effective-selection contract that composes with `PolicyKernel`; it is not a new policy
engine and cannot escalate permission.

Because #297 is still active hardening of the Phase 1/causal read foundation, Phase 2 is:

`AUDITED · REAL_GAP_PRELIMINARILY_CONFIRMED · NOT YET ADMITTED FOR IMPLEMENTATION`.

Do not open or implement a Phase 2 child until #297 and the active GitHub/Notion truth
surfaces are reconciled.

---

## Stable evidence

```text
#296 final head:               d376f146763bd70f6d725e53890e7beda4fd22e6
#296 merge/main:               e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96
pre-merge Full CI:             31670168755 · SUCCESS
pre-merge Docker:              31670168759 · SUCCESS
READY aggregate:               31676173562 · SUCCESS
post-merge Full CI:            31676260316 · SUCCESS
post-merge Docker:             31676260285 · SUCCESS
post-merge aggregate:          31676260313 · SUCCESS
```

Separate open workstreams remain #51 (ADAO), #92 (ARM; ARM-04 NOT AUTHORIZED), #120
(Reader Core production evidence), #249 (CAS contention) and #52 (trusted platform).

Next safe order:

```text
#297 exact-head CI/review reconciliation
→ #53/#49/#52/#296 truth-surface reconciliation where needed
→ same-page Notion correction + read-back
→ Phase 2 admission decision
→ only if admitted: separate bounded child issue
```

Never infer schema v8, Continuity 13/12, runtime enablement, Operator GO, runtime authority
or production authority from this work.
