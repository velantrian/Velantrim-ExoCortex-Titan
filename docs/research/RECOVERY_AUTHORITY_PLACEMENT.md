# 🛡️ Recovery Authority Placement

**Status:** `PROPOSED · DOCS-ONLY · NO RUNTIME AUTHORITY`  
**Historical source:** PR #17 head `648ccb89091c1bf58fef6dcd77586be47c13fc69`  
**Reconciled against:** `main@3bc3607c503c2a32b7ab4f31753b7f9c10ee620f`  
**Disposition for PR #17:** `ARCHIVE_AS_RESEARCH_SOURCE`  
**Titan Ring Zero runtime root:** rejected

## 1. Decision

Titan must not introduce an in-process component called `Ring Zero` as a new root of trust, policy owner or autonomous rollback authority.

The historical research captures useful failure and recovery questions, but its proposed placement overlaps existing Titan policy/mutation boundaries and risks implying independence that ordinary Python code in the same process, filesystem and administrative domain cannot provide.

Accepted placement:

```text
Neutral Native Kernel / substrate
    → event integrity
    → deterministic reduction
    → rebuildable projection
    → receipt verification

Titan PolicyKernel + PolicySnapshot + CapabilityLease
    → current policy/capability decisions

Titan mutation gates + SAFE_MODE + write/version services
    → current mutation denial and authorised storage actions

Future Recovery Coordinator
    → observe failure evidence
    → produce bounded dry-run plan
    → verify backup/event compatibility
    → request explicit operator approval
    → invoke existing authorised service
    → verify postconditions
    → emit recovery receipt
```

The coordinator may diagnose, propose and orchestrate already-authorised services. It does not become a new root, database writer, policy source, Canon owner or self-approving controller.

## 2. Non-authority boundary

This document creates no:

- recovery runtime module;
- startup hook, worker, scheduler or watchdog;
- automatic rollback;
- checkpoint database or migration;
- policy, TruthGate or Canon authority;
- mutation-gate bypass;
- filesystem, credential or deployment capability;
- backup restore command;
- operator-lockout mechanism;
- hardware-root or immutability claim;
- change to Native Kernel contracts;
- runtime activation.

`RECOVERY PLAN ≠ APPROVAL ≠ EXECUTION ≠ SUCCESS`.

## 3. Why a Titan Ring Zero root is rejected

### 3.1 Second root of trust

A Titan-specific Ring Zero would overlap:

- PolicyKernel;
- SAFE_MODE;
- mutation/write gates;
- TruthGate and Canon admission;
- version/rollback tooling;
- Native Kernel event/receipt integrity.

Overlapping roots make failure behavior ambiguous: each may attempt to deny, repair or restore state under a different policy snapshot.

### 3.2 Unproven independence

An in-process object is not independent when it shares:

- the same interpreter/process;
- the same writable database;
- the same filesystem and credentials;
- the same deployment administrator;
- the same dependency and build chain;
- the same logging/receipt store.

Naming it Ring Zero does not create hardware isolation, secure boot, TPM-backed keys or an independently administered control plane.

### 3.3 Erasure resurrection

Restoring an older checkpoint can reintroduce:

- hard-erased user data;
- revoked consent;
- later restrictions;
- invalidated credentials;
- superseded policy;
- vulnerable derived artifacts.

A valid hash or signature proves checkpoint integrity, not present-day admissibility.

### 3.4 Different reversibility domains

The following cannot be represented safely by one global rollback revision:

- canonical memory;
- policy and capability state;
- erasure/restriction tombstones;
- derived projections;
- credentials and keys;
- database schema migrations;
- sent notifications;
- remote tool/network writes;
- external billing, deployment or repository actions.

External effects require compensation or reconciliation records. Database replacement cannot undo them.

### 3.5 Audit continuity

Replacing current state with an old snapshot can fork or truncate history. Recovery must preserve:

- the original failure evidence;
- the selected recovery plan;
- approval identity;
- every invoked action;
- validation result;
- incomplete/failed recovery evidence.

Recovery is a new event sequence, not an erasure of the failed timeline.

## 4. Accepted recovery principles

### 4.1 Prefer forward reconstruction

```text
validated backup / event log
→ verify integrity and schema compatibility
→ apply current irreversible tombstones/restrictions
→ deterministic forward reduction
→ rebuild derived projections
→ compare invariants
→ explicit operator approval
→ activate through existing authorised service
→ post-activation validation
→ recovery receipt
```

Restoring an opaque full snapshot directly is the least preferred path.

### 4.2 Current policy dominates old policy

Recovery cannot weaken current policy to match historical data.

```text
current restriction / revocation / erasure
> historical checkpoint content
```

If current policy cannot be verified, recovery remains dry-run/read-only.

### 4.3 No self-approval

The same component cannot:

- detect the failure;
- choose the checkpoint;
- approve the plan;
- execute it;
- declare success.

At minimum, plan generation, approval, execution service and postcondition verification are separately identified in receipts. High-risk recovery may require quorum or a break-glass procedure.

### 4.4 Fail closed and remain observable

Failure to verify any required input yields:

```text
NO_ACTIVATION
SAFE_MODE / READ_ONLY
RECOVERY_NOT_READY receipt
```

It must not silently select a weaker backup or policy.

## 5. Component placement

### 5.1 Native Kernel / neutral substrate

Owns neutral integrity concepts:

- immutable event identity;
- event ordering/causal references where defined;
- deterministic reduction;
- projection checkpoints;
- receipt identity and verification;
- replay and corruption detection.

It must use neutral terms rather than Titan-specific cognitive levels or policy roles.

### 5.2 Titan PolicyKernel and mutation gates

Remain owners of current runtime permission and mutation denial.

A recovery plan binds to a fresh healthy `PolicySnapshot` and exact capability leases. Old checkpoint policy cannot authorise current actions.

### 5.3 Authorised storage/version services

Actual backup verification, restoration, migration, projection rebuild and activation belong to narrowly scoped services with explicit interfaces, not to a cognitive coordinator.

### 5.4 Recovery Coordinator

Future proposal-only role:

```text
RecoveryCoordinator
├── accepts typed failure evidence
├── enumerates candidate recovery sources
├── checks declared compatibility
├── produces dry-run steps and risks
├── requests approval
├── submits approved calls to authorised services
├── observes results
└── emits structured receipts
```

Forbidden coordinator fields/methods:

```text
root_authority
bypass_policy
force_canon_write
self_approve
automatic_rollback
unlock_operator
ignore_erasure
execute_arbitrary_command
```

## 6. Recovery objects

### 6.1 Failure observation

```text
FailureObservation
├── observation_id
├── source/component
├── failure_class
├── detected_at
├── evidence_refs[]
├── affected scopes
├── current policy snapshot
├── confidence / uncertainty
└── authority = observation_only
```

A model inference alone cannot declare system corruption.

### 6.2 Recovery source descriptor

```text
RecoverySource
├── source_id
├── kind = event_log | backup | checkpoint | projection
├── created_at
├── schema/version identities
├── content/manifest digest
├── signer/verifier information
├── tenant/subject scopes
├── included retention horizon
├── known omissions
└── current admissibility result
```

Signature validity is one input, not a safety verdict.

### 6.3 Recovery plan

```text
RecoveryPlan
├── plan_id                 # content-addressed
├── failure_observation_refs[]
├── selected source refs[]
├── current policy snapshot
├── compatibility profile
├── ordered dry-run steps[]
├── irreversible actions[]
├── required approvals[]
├── expected postconditions[]
├── rollback/abort conditions[]
├── external compensation tasks[]
├── expiry
└── authority = proposal_only
```

### 6.4 Approval receipt

Approval is separate and binds to exact plan digest, policy snapshot, expiry and operator/quorum identity.

### 6.5 Recovery execution receipt

```text
RecoveryReceipt
├── receipt_id
├── plan_digest
├── approval refs[]
├── executor/service identity
├── before-state identities
├── actions attempted[]
├── actions completed[]
├── external compensation state
├── after-state identities
├── invariant results
├── erasure/restriction proof
├── result = SUCCESS | PARTIAL | FAILED | ABORTED
└── failure details
```

A partial or failed recovery receipt is never rewritten into success.

## 7. Checkpoint/backup verification

Verification includes:

- manifest completeness;
- cryptographic digest;
- signature/key status and rotation history;
- schema and application compatibility;
- event/audit continuity;
- tenant and subject scope;
- current erasure/restriction overlay;
- malware/secret/config review where relevant;
- dependency and migration requirements;
- available disk/resource bounds;
- projection rebuild plan;
- external side-effect reconciliation.

A checkpoint is rejected when its provenance, compatibility or current admissibility cannot be proven.

## 8. Erasure and restriction preservation

Irreversible tombstones/restrictions must be maintained outside the rollback domain they constrain, or otherwise be reconstructed from a separately verified current source.

Before activation:

1. load the candidate source in isolation;
2. apply current erasure/restriction state;
3. prove prohibited records and derived references are absent;
4. rebuild projections from allowed events/state;
5. run cross-store and cache checks;
6. record proof in the recovery receipt.

No plan may restore a historical value merely because the backup predates its erasure.

## 9. Schema and migration recovery

Recovery must distinguish:

- restoring data into the current schema;
- forward-migrating an old backup;
- rolling back application code while keeping a newer schema;
- restoring a projection only;
- rebuilding from events.

Blind activation of an older schema is forbidden.

Required evidence:

- supported source/target schema pair;
- deterministic migration plan;
- migration tests on representative fixtures;
- failure/rollback strategy for the migration operation;
- no-loss and erasure-preservation checks;
- current application compatibility.

## 10. External effects

Recovery tracks external effects separately:

```text
ExternalEffectRecord
├── effect_id
├── system/capability
├── idempotency key
├── attempted/completed/unknown
├── compensation action?
├── reconciliation evidence
└── operator decision
```

Examples:

- notifications already sent;
- repository commits/merges;
- remote API mutations;
- deployments;
- financial or billing actions;
- issued credentials.

Unknown execution state remains explicit and blocks repeated non-idempotent actions.

## 11. Operator safety

A future implementation defines:

- approval roles and quorum;
- break-glass procedure;
- approval expiry;
- plan cancellation;
- key rotation/revocation;
- separation of duties;
- recovery rehearsal environment;
- operator lockout prevention;
- audit export independent of the recovering store;
- emergency read-only mode.

No model, LLM or autonomous agent may be the sole approver.

## 12. Signer and receipt compromise

Threats include:

- compromised signing key;
- malicious but correctly signed checkpoint;
- forged same-domain receipts;
- rollback of key-revocation metadata;
- compromised recovery coordinator;
- collusion between planner and executor.

Mitigations may include:

- independent key/status verification;
- key rotation and revocation history;
- multi-party approval;
- write-once/offline audit export;
- deterministic postcondition verification by a separate component;
- content and policy checks beyond signatures.

No signature alone grants activation.

## 13. Recovery modes

Possible future modes:

| Mode | Meaning | Authority |
|---|---|---|
| `OBSERVE_ONLY` | collect failure evidence | no mutation |
| `DRY_RUN` | build and validate a plan in isolation | no mutation |
| `PREPARE` | stage approved artifacts without activation | bounded authorised writes |
| `ACTIVATE` | switch through an authorised service | explicit approval required |
| `VALIDATE` | verify postconditions | no implicit success |
| `ABORT` | stop before irreversible step | explicit receipt |
| `COMPENSATE` | reconcile external effects | separately authorised |

There is no generic `ROLLBACK_EVERYTHING` mode.

## 14. Failure classes

Minimum classes:

- event-log corruption;
- projection corruption;
- schema/migration failure;
- policy dependency unavailable;
- partial write/transaction uncertainty;
- credential/key compromise;
- disk full or resource exhaustion;
- audit discontinuity;
- backup incompatibility;
- external side-effect divergence;
- erasure/restriction mismatch;
- operator/configuration error.

Each class has its own evidence and recovery profile. No universal snapshot restore is assumed.

## 15. Testing before any implementation

Required isolated tests:

- corrupt manifest/digest/signature rejection;
- revoked signer rejection;
- current erasure preserved against old backup;
- current restriction/policy dominates historical state;
- schema forward-migration success and failure;
- crash at every recovery step;
- audit history remains append-only;
- coordinator cannot self-approve;
- approval plan-digest mismatch rejection;
- expired/cancelled approval rejection;
- compromised/stale policy snapshot rejection;
- partial external side effect remains `UNKNOWN`/`PARTIAL`;
- duplicate action blocked through idempotency key;
- disk/resource bound failure remains safe;
- failed recovery preserves prior active state when possible;
- postcondition failure cannot emit success;
- receipt tampering detected;
- projection rebuild deterministic;
- operator lockout and break-glass rehearsal.

Tests run against isolated fixtures, never production data.

## 16. Implementation sequence

### Stage A — placement decision

- merge this docs-only decision;
- close PR #17 as archived/not planned implementation;
- preserve historical research link;
- synchronize GitHub and Notion.

### Stage B — neutral contracts

Only if a concrete recovery need is approved:

- typed observation/source/plan/receipt schemas;
- content-addressed IDs;
- no execution;
- replay and tamper tests;
- explicit Native Kernel/Titan ownership split.

### Stage C — dry-run coordinator

- isolated source inspection;
- compatibility and erasure overlay checks;
- plan generation only;
- operator review interface;
- no activation.

### Stage D — authorised service adapters

Separate PRs for each narrow storage/version capability. No arbitrary shell or universal restore interface.

### Stage E — bounded activation

Requires:

- production threat model;
- independent audit evidence;
- tested backups and runbooks;
- policy owner;
- operator/quorum model;
- monitoring and alerting;
- rollback/abort/compensation proof;
- explicit activation ADR and Operator GO.

## 17. Stop conditions

Stop and keep Draft if any change introduces:

- Titan-specific new root of trust;
- autonomous rollback;
- old-policy override of current policy;
- erased/restricted data restoration;
- audit-history truncation;
- self-approval;
- arbitrary command execution;
- generic database replacement without schema/erasure proof;
- hardware-isolation claims without real hardware/admin separation;
- same-domain receipt treated as independent proof;
- runtime implementation mixed with placement decision.

## 18. Progress by state

```text
Architecture placement:       1/1 = 100%
Neutral contracts:            0/5 =   0%
Dry-run coordinator:          0/5 =   0%
Fault-injection corpus:       0/8 =   0%
Runtime wiring:               0/1 =   0%
Runtime readiness:            0/1 =   0%
```

## 19. Final disposition

```text
PR #17 = ARCHIVE_AS_RESEARCH_SOURCE
Titan Ring Zero root = REJECTED
Future recovery = neutral integrity + current policy gates + operator-approved coordinator
```

The historical branch must not be merged directly.