# 🗺️ Component and Authority Map

**Repository checkpoint inspected:** `main@064845579c520e7464678cd0c41d9b650368dfa8`  
**Continuity implementation baseline:** PR #267 → `064845579c520e7464678cd0c41d9b650368dfa8`  
**Phase I audit checkpoint:** PR #261 → `90e221be2bed8177f4648787d713058df0f29e1f`  
**Machine state:** [`docs/state/project_state.json`](../state/project_state.json) · schema v4  
**Rule:** presence is not wiring; integrity is not authenticity; storage is not activation.

## 1. Canon and core runtime

| Responsibility | Primary owner | State | Authority |
|---|---|---|---|
| Durable facts and ESM | `core/memory.py` / canonical store services | implemented, tested, wired | Canon state owner |
| Truth admission | `core/truth_gate.py`, accepted write services | implemented, tested, partly unified | evidence/confidence decision |
| Hard policy and data mode | `core/policy_kernel.py`, `PolicySnapshot`, `CapabilityLease` | implemented, tested | policy owner |
| Provenance and audit | `core/provenance_chain.py`, `core/audit_chain.py` | implemented, tested | trace and mutation evidence |
| Retrieval coordination | `core/pipeline.py`, `core/hybrid_retriever.py` | implemented, wired | read-side proposal only |
| Projection delivery | projection outbox / dispatcher primitives | implemented, tested, not lifecycle-wired | rebuildable derived state |

No Continuity component owns Canon, TruthGate, PolicyKernel, GoalStack, reminders, tools,
actions or compute routing.

## 2. Continuity accepted lineage

| Capability | Merge SHA | Primary surface | Runtime state |
|---|---|---|---|
| Immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | `core/continuity/contracts.py` | tested, unwired |
| Source-admission evidence | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | source-admission contracts | evidence only |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | `state_source_adapter.py` | tested, internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | `goal_open_loop.py` | tested correction |
| OpenLoop subject binding v2 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | `goal_open_loop.py` | tested correction |
| Goal Draft adapter | `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | `goal_source_adapter.py` | tested, internal, unwired |
| OpenLoop Draft adapter | `42aa79338c57e9b9a67c3e3c08dd948b60c5541f` | `open_loop_source_adapter.py` | tested, internal, unwired |
| Admission evaluator | `97fe27a37184c6c7277f54e96acd04d98d583ab3` | `admission_evaluator.py` | tested, internal, unwired |
| Admission-aware facade | `9f07db6de8d32683d00bfe4f1673e84493607553` | `admission_facade.py` | tested, internal, unwired |
| Current-decision composition | `dc30817f2c4abb1afcaab2f127e679d5f9b884d7` | `current_decision_resolver.py` | tested, internal, unwired |
| Durable artifact lifecycle | `064845579c520e7464678cd0c41d9b650368dfa8` | `admission_artifact_lifecycle.py` | tested, internal, unwired |

## 3. Admission and lifecycle path

```text
State / Goal / OpenLoop result
→ deterministic source adapter
→ source envelope + complete Draft set
→ operator-selected facade policy + registry identity
→ six injected read-only current-decision owner ports
→ exact scoped owner snapshots
→ CurrentDecisionEvidence
→ internal admission-aware facade
→ pure admission evaluator
→ content-addressed accepted result
→ explicitly invoked internal lifecycle owner
→ atomic append / verified replay / bounded cleanup / erasure tombstone
→ STOP
```

The lifecycle invocation is not wired into a server, startup path, worker or scheduler.
The path does not invoke the signal producer, write Canon, create reminders/actions or
change compute routing.

## 4. Current-decision ownership

| Domain | Composition role | Runtime owner selected? |
|---|---|---|
| Principal | must return exact scoped `ACTIVE` snapshot | no |
| Authorization | represented status preserved | no |
| Lawful basis / consent | represented status preserved | no |
| Restriction | `CLEAR`, `BLOCKED` or `UNKNOWN` preserved | no |
| Erasure | `CLEAR`, `BLOCKED` or `UNKNOWN` preserved | no |
| PolicySnapshot | must return exact scoped `ACTIVE` snapshot | no |

`current_decision_resolver.py` owns only composition and verification. It is not a second
identity, policy, consent, restriction or erasure system.

## 5. Durable lifecycle ownership

| Concern | Lifecycle responsibility | Authority boundary |
|---|---|---|
| Artifact identity | canonical content-derived identity | integrity only |
| Append | atomic/idempotent SQLite transaction | explicitly invoked internal owner |
| Replay | exact-scope read + full verification | no new authorization decision |
| Retention | execute supplied bounded policy | lifecycle does not invent policy |
| Cleanup | deterministic bounded neutralization + receipt | no scheduler or runtime owner |
| Erasure | require exact external owner `ALLOW` evidence | lifecycle does not decide eligibility |
| Tombstone | retain scope and neutralization evidence | source payload removed |
| Recovery | transaction rollback and retry stability | tested fault seams, not live observation |

The lifecycle is a storage/evidence owner only. It cannot authorize use, activate a
producer, select live adapters or grant runtime authority.

## 6. Decision ownership

| Decision | Accepted owner |
|---|---|
| Canon / ESM state | canonical memory and write services |
| Truth admission | accepted TruthGate/write path |
| hard policy, locality and data mode | PolicyKernel / PolicySnapshot |
| source result identity | source component owners |
| source adaptation | deterministic proposal transform only |
| evaluator rules | pure admission evaluator |
| anti-substitution | internal admission facade and resolver composition |
| current owner decisions | six injected domain owners |
| artifact retention/replay/cleanup execution | internal lifecycle owner |
| erasure eligibility | external accepted erasure owner |
| concrete live owner/lifecycle adapters | no accepted deployment selection yet |
| runtime activation | no accepted owner |

## 7. Fail-closed boundary

The accepted resolver and lifecycle reject:

- missing, duplicate or wrong-domain owner snapshots;
- malformed content identity, digest, JSON, schema or version;
- owner ID/version mutation;
- principal, authorization, source, binding, tenant or subject substitution;
- stale or future-effective decision evidence;
- cross-tenant artifact reuse;
- conflicting artifact identity and silent overwrite;
- replay or re-append after cleanup/erasure neutralization;
- owner/storage exceptions and injected partial transaction failures.

Negative and unknown represented decisions are not converted into allow decisions.

## 8. Remaining integration boundary

Before any controlled enablement, separately implement and prove:

- operator-selected lifecycle and six-domain owner adapters;
- startup/shutdown and database-path ownership;
- one accepted runtime call site with anti-bypass guards;
- fail-closed error propagation and bounded recovery;
- backup/restore and deployment filesystem behavior;
- metrics, reconciliation and operational evidence;
- an explicit stop before feature enablement and Operator GO.

## 9. Governance and operations

- ruleset `main-governance` ID `20601712` remains active;
- PR, aggregate evidence, up-to-date branch and conversation resolution are required;
- force pushes are blocked, deletion restricted and bypass empty;
- accepted solo mode uses approvals `0`;
- aggregate success is not independent review;
- Phase I audit identity remains issue #257 / PR #261 / merge `90e221...`;
- schema v4 preserves historical schema v1/v2/v3 validation and records PR #267 separately;
- Notion synchronization targets the existing page `Velantrim Titan 9.0`;
- no runtime authority is implied.

## 10. Next audit checklist

1. Are live owner and lifecycle adapters operator-selected outside caller payloads?
2. Is authenticity proven rather than inferred from hashes?
3. Is the complete exact subject set preserved at the runtime call site?
4. Do missing, stale, ambiguous and conflicting states fail closed?
5. Is there exactly one accepted lifecycle invocation path with anti-bypass evidence?
6. Does output remain evidence-only before a separate activation decision?
7. Are producer invocation and user-visible effects absent?
8. Are exact-head and post-merge checks attached?
9. Are GitHub and the exact Notion page synchronized?
10. Are `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` separate?
