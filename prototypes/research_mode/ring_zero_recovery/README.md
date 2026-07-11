# Ring Zero Recovery Kernel — Research Mode

> **Status:** research-only concept / simulation target / not production runtime
>
> **Scope:** architecture, threat model, checkpoint contract, invariant enforcement, rollback semantics
>
> **Non-goal:** this document does not claim that Titan currently has an immutable kernel, secure enclave, self-healing runtime, or production-safe automatic rollback.

## 1. Research question

Can Titan separate a **minimal protected policy-and-recovery kernel** from its larger mutable runtime so that failures become bounded, detectable, auditable, and reversible?

The proposal is inspired by a two-layer model:

- **Ring Zero / Recovery Kernel** — a minimal authority responsible only for validating critical transitions, verifying checkpoints, authorizing rollback, and emitting receipts.
- **Mutable Runtime** — graph, memory, inference, tools, routing, learning, LLM interaction, and experimental modules.

The mutable runtime may evolve. It must not be able to silently rewrite the policy bundle, forge checkpoint validity, or bypass the recovery boundary.

## 2. Why this may matter

A long-running AI memory system can fail without a single catastrophic crash. More realistic failure modes include:

- graph corruption or inconsistent edge semantics;
- invalid promotion of weak or contradictory claims;
- broken migrations or partial writes;
- accidental deletion or restriction bypass;
- audit-chain discontinuity;
- tool or agent behavior that mutates protected state;
- policy drift after configuration changes;
- a bad deployment that passes startup but violates invariants later.

The goal is not to make Titan infallible. The goal is to make important failures:

1. **bounded** — one component cannot silently compromise the whole system;
2. **detectable** — violations produce explicit machine-readable reasons;
3. **auditable** — each intervention produces a durable receipt;
4. **reversible** — a verified prior revision can be restored atomically;
5. **reviewable** — humans can inspect why the system blocked or rolled back an action.

## 3. Proposed trust split

```text
┌─────────────────────────────────────────────────────────┐
│ Ring Zero Recovery Kernel                              │
│ - signed/versioned policy bundle                       │
│ - typed invariant evaluator                            │
│ - checkpoint verifier                                  │
│ - rollback authorizer                                  │
│ - receipt emitter                                      │
└──────────────────────────┬──────────────────────────────┘
                           │ narrow typed interface
┌──────────────────────────▼──────────────────────────────┐
│ Titan Mutable Runtime                                  │
│ - graph and memory                                     │
│ - TruthGate / promotion flows                          │
│ - tools, routing, learning, LLM                        │
│ - experimental Research Mode modules                   │
└─────────────────────────────────────────────────────────┘
```

The important property is not the name “Ring Zero.” The important property is a **small, explicit, testable trust boundary**.

## 4. What belongs in the recovery kernel

Only a minimal set of responsibilities should be considered:

### 4.1 Policy bundle verification

The kernel verifies that the active policy bundle is:

- versioned;
- integrity-checked;
- loaded from an approved source;
- compatible with the current schema and migration set;
- not silently modified by ordinary runtime code.

A future implementation may use signed manifests, read-only mounts, process separation, or another stronger boundary. A normal Python object is not sufficient evidence of immutability.

### 4.2 Typed invariant evaluation

Checks must operate on structured actions and state, not on word matching such as `"lie" in action`.

Example action envelope:

```json
{
  "action_type": "fact.promote",
  "actor": "tool:validate_fact",
  "subject_id": "fact-123",
  "from_state": "Observed",
  "to_state": "Validated",
  "policy_version": "truthgate-v3",
  "revision": 812
}
```

Possible result:

```json
{
  "decision": "deny",
  "reason_code": "EVIDENCE_THRESHOLD_NOT_MET",
  "policy_version": "truthgate-v3",
  "evaluated_revision": 812
}
```

### 4.3 Checkpoint verification

A checkpoint is not “good” because the mutable runtime reports a high `truth_level`. It must be independently verifiable.

Candidate checkpoint fields:

```text
checkpoint_id
created_at
state_revision
schema_version
migration_set_digest
policy_bundle_digest
graph_digest
audit_chain_head
restricted_data_summary
erasure_state_summary
created_by
validation_receipt_id
```

A checkpoint is eligible for recovery only when its validation receipt confirms all required invariants.

### 4.4 Rollback authorization

The kernel should authorize a rollback only after:

- validating the target checkpoint;
- comparing schema and policy compatibility;
- generating a dry-run plan;
- identifying data loss or restricted-state impact;
- recording a reason and actor;
- verifying that the activation can occur atomically.

### 4.5 Recovery receipt

Every rollback attempt should produce a durable receipt, whether it succeeds or fails.

Minimum fields:

```text
receipt_id
requested_by
reason_code
source_revision
target_revision
checkpoint_id
pre_validation_result
activation_result
post_validation_result
audit_head_before
audit_head_after
timestamp
```

## 5. Explicit non-goals

This research concept must not be presented as:

- a moral “conscience” implemented in code;
- proof that the system cannot be compromised;
- a replacement for backups;
- a replacement for database transactions;
- a replacement for TruthGate, provenance, erasure, or restriction controls;
- permission for an LLM to decide autonomously that production should roll back;
- a claim of hardware-level isolation when only a Python class exists.

## 6. Failure modes to study

Research should test at least the following cases:

1. **Corrupted checkpoint** — digest mismatch or incomplete snapshot.
2. **Policy drift** — checkpoint created under incompatible policy version.
3. **Audit discontinuity** — target checkpoint does not connect to a trusted audit head.
4. **Partial rollback** — process fails between storage activation steps.
5. **Concurrent mutation** — writes continue while recovery is being prepared.
6. **Restricted-data regression** — rollback would re-expose restricted information.
7. **Erasure regression** — rollback would restore data previously hard-erased.
8. **Migration mismatch** — snapshot schema is older or newer than runtime code.
9. **Compromised runtime** — runtime tries to self-approve a checkpoint.
10. **False-positive invariant** — policy blocks a legitimate transition.

## 7. Relationship to existing Titan architecture

This proposal should extend, not duplicate, existing boundaries:

- **TruthGate** remains responsible for admission and promotion quality.
- **Atomic supersede / CAS** remains responsible for safe fact replacement.
- **Provenance and audit** remain responsible for traceability.
- **Restriction and erasure controls** remain authoritative for data governance.
- **Recovery Kernel** would coordinate system-level recovery using receipts and verified revisions.

The recovery kernel must never become an alternate write path around these controls.

## 8. Research phases

### Phase R0 — specification only

- define threat model;
- define typed action envelope;
- define checkpoint manifest;
- define invariant result codes;
- define rollback receipt schema;
- no runtime integration.

### Phase R1 — isolated simulation

- in-memory mock state;
- synthetic checkpoints;
- deterministic invariant evaluator;
- simulated failures;
- no production database access;
- no automatic rollback of real data.

### Phase R2 — disposable integration environment

- temporary SQLite database;
- explicit revision snapshots;
- transaction and crash-injection tests;
- restricted/erased-data regression tests;
- manual authorization only.

### Phase R3 — guarded prototype

- separate process or service boundary;
- read-only policy bundle;
- signed or integrity-checked checkpoint manifests;
- dry-run recovery plans;
- human approval required;
- complete receipts.

Production consideration should occur only after the threat model and crash-consistency properties are independently reviewed.

## 9. Acceptance criteria for a useful prototype

A prototype is not considered successful merely because a demo prints “rollback complete.” It should demonstrate:

- deterministic typed policy decisions;
- inability of ordinary runtime code to self-approve recovery;
- atomic activation or clean failure;
- no restoration of erased data;
- no removal of active restrictions;
- preserved audit continuity;
- reproducible post-recovery invariant scan;
- complete recovery receipts;
- fault-injection tests for interrupted recovery.

## 10. Open research questions

- What is the smallest useful recovery authority?
- Which invariants must be synchronous, and which may be checked asynchronously?
- Should recovery operate on the entire database, per graph partition, or per revision domain?
- How should policy updates interact with old checkpoints?
- How can GDPR-style erasure remain irreversible across rollback?
- Can restricted facts remain cryptographically inaccessible even when old snapshots exist?
- What evidence is sufficient for a checkpoint to become recovery-eligible?
- Which actions always require human approval?

## 11. Current status

This is a **research specification only**. No existing Titan runtime behavior should be inferred from this document. Any future implementation must begin in an isolated Research Mode prototype and must not modify the canonical production write path without a separate reviewed design and PR.
