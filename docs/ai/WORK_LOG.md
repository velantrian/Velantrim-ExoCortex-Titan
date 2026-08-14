# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.
Older detail remains traceable in Git history, merged PRs, issues, ADRs and dated checkpoints.

---

## 2026-08-14 — #52 C8 closed → C9 World Skills admission · IN PROGRESS

```text
C8 protected squash main:         1909e3f10330c4032641970ad0934a67649681e3
C8 signature:                     VERIFIED / valid
C8 post-merge Full CI:            #1170 · 31829982550 · SUCCESS
C8 post-merge Docker:             #769 · 31829982337 · SUCCESS
C8 post-merge CodeQL:             #8 · 31829982439 · SUCCESS
C8 post-merge aggregate:          #1171 · 31829982414 · SUCCESS
C9 tracking PR:                   #320 · DRAFT
C9 branch:                        agent/issue-52-world-skills-admission
C9 base:                          1909e3f10330c4032641970ad0934a67649681e3
C9 exact candidate head:          RESOLVE LIVE — changes still under review
C9 Notion DRAFT/read-back:        SYNCED
parent #52:                       OPEN
Continuity:                       12/12
schema:                           v7
runtime enabled:                  false
Operator GO:                      false
runtime authority:                false
production authority:             false
Canon:                            local
remote Canon:                     forbidden
```

Fresh #52 audit after C8 confirmed that World Skills remained a real current residual,
not stale issue prose. `core/world_skills_ingest.py` directly called
`promote_to_validated()` for curated rows; the parser did not expose the complete #52
provenance/risk/review metadata contract; the focused ingest test explicitly expected
legacy rows to auto-validate; and the promotion ownership inventory already documented the
route as a `KNOWN_EXCEPTION` requiring separate convergence.

C9 is therefore bounded to that exception. The candidate does **not** weaken TruthGate or
create a second Canon owner. It introduces explicit candidate metadata:

```text
truth_status
source_refs
confidence
risk_domain
limitations
review_status
reviewer
reviewed_at
```

Legacy rows receive safe non-claims and remain quarantined. The proposed admission chain is:

```text
Draft
→ Quarantine
→ Provenance Check
→ Domain Review
→ existing TruthGate precheck
→ legal ESM ladder to Supported
→ existing PromotionGateway
→ existing validate_and_promote()
→ TruthGate recheck + CAS
→ Validated / local Canon
```

A high-risk candidate selects the existing `PRECISION` mode; ordinary explicit risk uses
existing `BALANCED`. Numerical truth/evidence thresholds remain entirely TruthGate-owned.
Candidate and pack SHA-256 identifiers provide deterministic replay/content binding, not
cryptographic reviewer authentication.

Focused candidate tests cover legacy quarantine, successful reviewed low-risk admission,
high-risk TruthGate rejection, self-review rejection and order-independent/content-bound
pack identity. `tests/test_promotion_ownership_guard.py` removes World Skills from the
reviewed direct-promotion allowlist, so a reintroduced business-level bypass fails CI.

C9 also reconciles the promotion ownership inventory, the World Skills authoring/source
rules, ADR and operator documentation. The existing Notion `Velantrim Titan 9.0` page has
a C9 DRAFT checkpoint and was read back. No FINAL/merge claim is made yet: exact-head Full
CI, Docker, CodeQL, review/race audit, Ready aggregate, protected merge, post-merge evidence
and FINAL GitHub/Notion reconciliation remain required.

---

## 2026-08-13 — Phase 2A capability registry · FINAL / POST-MERGE VERIFIED

```text
implementation main:             c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
documentation closure main:      840b5aa231fe7d8cc0383c072ad953ca9bf4f46a
main signature:                   VERIFIED / valid
#50:                              CLOSED_COMPLETED · final REAL_GAP=0
#53:                              OPEN
#299:                             CLOSED_COMPLETED
#300:                             MERGED
#301:                             MERGED
#300 final tested head:           f0b893bac1b6fe1f58a71c70ac631f3c14becb59
#300 protected squash merge:      c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
#301 exact docs head:             b1376ac74c713773fa1fd6fd723bb05d53490bd1
#301 protected squash merge:      840b5aa231fe7d8cc0383c072ad953ca9bf4f46a
pre-merge Full CI:                #1105 · 31735939941 · SUCCESS
pre-merge Docker:                 #723 · 31735939929 · SUCCESS
READY aggregate:                  #981 · 31736858130 · SUCCESS
post-merge Full CI:               #1106 · 31736925690 · SUCCESS
post-merge Docker:                #724 · 31736925695 · SUCCESS
post-merge aggregate:             #982 · 31736925705 · SUCCESS
#301 exact-head Full CI:          #1107 · 31737790013 · SUCCESS
#301 READY aggregate:             #987 · 31738384462 · SUCCESS
#301 post-merge Full CI:          #1108 · 31738432888 · SUCCESS
#301 post-merge aggregate:        #988 · SUCCESS
Codex review:                     NOT RUN — USAGE LIMIT
independent formal approval:      NONE / NOT CLAIMED
Continuity:                       12/12
schema:                           v7
runtime enabled:                  false
Operator GO:                      false
runtime authority:                false
production authority:             false
```

Phase 2A was admitted through #299 after the #297/#298 foundation and public-truth closure.
It is implemented and protected-merged through #300, with the public documentation closure
completed through #301 and tracking issue #299 subsequently closed as `CLOSED_COMPLETED`.
The registry remains deliberately **UNWIRED / NOT ENABLED**. No provider/model/network call
path was activated.

### Implemented bounded owner

`core/capability_registry.py` now provides a process-local metadata contract for:

- stable `ProviderDescriptor` and `CapabilityDescriptor` identity;
- capability-specific declared `data_mode`;
- explicit `ProviderHealth` states: UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE;
- deterministic candidate selection/no-selection;
- separate health and policy/selection reason codes;
- trace-ready selection metadata without TRACE persistence.

The existing process-wide `PolicyKernel` remains the sole permission owner. Production
`CapabilityRegistry()` has no policy/leaser injection parameter and always resolves the
owner through `get_policy_kernel()`. Every HEALTHY/DEGRADED candidate must receive an
existing PolicyKernel lease; explicit preference and `auto` cannot reinterpret a denial.

### Authority-bypass hardening

Self-review found an early constructor-injection surface that would have allowed a future
caller to substitute an arbitrary leaser. That was treated as a blocking authority defect
and removed before Ready. Tests patch `get_policy_kernel()` only inside the test process;
there is no production alternate-policy extension point.

Additional fail-closed boundaries include malformed typed metadata, remote provider
metadata that hides network requirements, unknown/unavailable health, PolicyKernel
exceptions and mixed policy snapshot/version values during one selection pass.

### Review and governance evidence

A Codex review request on ancestor head `009e5fbc11b03fd4033c939ae04ff0a8835e797b`
returned `NOT RUN — USAGE LIMIT`. This is neither approval nor a finding. The active solo
ruleset requires zero approving reviews, review-thread resolution and the
`Titan aggregate merge evidence` status check; no independent review is claimed.

The first Ready aggregate (#980) failed only because the PR-body Notion lifecycle token did
not use the validator's accepted `SYNCED` value. The existing Notion page had already been
updated and read back. PR metadata was corrected without changing the exact head; fresh
Ready aggregate #981 then succeeded.

### Documentation closure

The implementation merge left review-stage language in public AI context files. Docs-only
PR #301 reconciled those truth surfaces without touching `core/**` or changing Phase 2A
behavior. It protected-merged as
`840b5aa231fe7d8cc0383c072ad953ca9bf4f46a`; its exact-head Full CI #1107 and Ready
aggregate #987 succeeded, followed by post-merge Full CI #1108 and aggregate #988. No
Docker run was spawned for docs-only #301, so no Docker success is claimed for it. The
existing `Velantrim Titan 9.0` page was synchronized/read back, and issue #299 was then
closed with state reason `completed`.

---

## 2026-08-13 — #297 / #298 foundation closure · FINAL

```text
#297 hardening merge:            c96b734b94f30e1d96e8bcb992dec429bda5c8fd
#297 review threads:             13/13 RESOLVED
#297 READY aggregate:            #914 · 31725868065 · SUCCESS
#297 post-merge Full CI:         #1085 · 31725945373 · SUCCESS
#297 post-merge Docker:          #705 · 31725945362 · SUCCESS
#298 truth reconciliation merge: 51058f2d5662edfdb91b037a46dce9297c441a1b
#298 exact-head Full CI:         #1086 · 31729146690 · SUCCESS
#298 READY aggregate:            #920 · 31729778909 · SUCCESS
#298 post-merge Full CI:         #1087 · 31729908579 · SUCCESS
#298 post-merge aggregate:       #921 · 31729908264 · SUCCESS
```

---

## Stable authority boundary

```text
Continuity:             12/12
schema:                 v7
runtime enabled:        false
Operator GO:            false
runtime authority:      false
production authority:   false
Canon:                  local
remote Canon:           forbidden
```

Phase 2A and #52 hardening do not authorize embeddings/vector execution, reranker/LLM
execution, ADAO, ARM-04, provider probing/invocation, remote consent implementation,
network activation, runtime route replacement, runtime enablement, Continuity 13/12 or
schema v8.

Phase 2A closure sequence completed:

```text
#301 exact-head CI SUCCESS
→ same-page Notion sync + read-back
→ Ready aggregate #987 SUCCESS
→ protected docs merge 840b5aa231fe7d8cc0383c072ad953ca9bf4f46a
→ post-merge Full CI #1108 SUCCESS
→ post-merge aggregate #988 SUCCESS
→ FINAL Notion read-back
→ #299 CLOSED_COMPLETED
```
