# F2 task-conditioned representation sufficiency contract

Status: BOUNDED RESEARCH CONTRACT NOTE

Authority: NONE

Runtime authorization: NONE

Architecture adoption: NONE

New module: NONE

## Purpose

Record the smallest owner-local contract question exposed by the merged F2 Hidden Exception fixture without turning that fixture into a new runtime subsystem.

The merged F2 evidence establishes that a representation valid for task T1 can omit source material that becomes material for a later task T2.

It does not establish an end-to-end later-task reopen policy.

## Existing Titan coverage

Titan already preserves several important pieces of the boundary:

- bounded digest provenance is fail-closed;
- source claims not represented by synthesis are preserved as `unsupported_source_claim_ids`;
- synthesis can preserve unresolved questions;
- incomplete same-run reading can return `remaining_reread_work_requires_explicit_new_run`;
- source-linked Reader artifacts preserve document/source revision and source spans within the current product result;
- F2 demonstrates `T1 SUFFICIENT != T2 SUFFICIENT` and `NOT REPRESENTED != ABSENT`.

These mechanisms prove that Titan can represent omission and incomplete work without silently upgrading either into truth.

They do NOT prove that Titan can determine whether a particular later task T2 is sufficiently supported by an old compact representation.

## Residual contract gap

The residual is task-conditioned, not global:

`REPRESENTATION HAS UNREPRESENTED SOURCE CLAIMS`

is weaker than:

`THIS REPRESENTATION IS INSUFFICIENT FOR THIS TASK`.

A compact representation may omit source material that is irrelevant to T2, or it may omit exactly the material required by T2. The existence of `unsupported_source_claim_ids` alone cannot decide between those cases.

Therefore:

`UNSUPPORTED SOURCE CLAIM EXISTS != T2 INSUFFICIENT`

and:

`NO T2 SUPPORT FOUND IN COMPACT VIEW != SOURCE FACT ABSENT`.

## Minimum safe contract

For a later task T2, an owner-local evaluator may only claim representation sufficiency when there is positive bounded evidence that the retained representation supports the material requirement of T2.

If that evidence is not established, the safe disposition is one of:

- `REPRESENTATION_INSUFFICIENT`, when bounded evidence establishes that material support required by T2 is absent from the retained representation while source-linked material or an authorized reopen target may contain it;
- `UNKNOWN`, when the evaluator cannot establish either sufficiency or insufficiency without further source access.

These names are research-level contract labels in this note. They are NOT authorized runtime enums, API fields, persistence schema, or cross-project vocabulary.

## Bounded reopen relation

A task-conditioned insufficiency result may justify proposing a bounded source reopen only if an existing authorized owner-local path can recover the relevant source/version/span.

It does not grant permission to:

- create a persistent Reader session store;
- create a universal Reopen Module;
- add a new memory organ;
- move source-body persistence into Crystal;
- treat provenance as permission;
- treat addressability as durable availability;
- convert a test fixture into production authority.

Thus:

`REOPEN CAPABILITY != REOPEN POLICY`

`ADDRESSABILITY != DURABLE RESUME STATE`

`REPRESENTATION INSUFFICIENCY != AUTOMATIC REOPEN AUTHORIZATION`.

## Discriminating PASS / FAIL conditions

### PASS

Given T1 output and a genuinely later T2:

1. the evaluator does not infer source absence from omission in the compact representation;
2. if the compact representation positively supports T2, it may report bounded sufficiency;
3. if material T2 support is known to be omitted from the compact representation, it reports representation insufficiency rather than answering from the incomplete view;
4. if sufficiency cannot be established and source recovery is not available or authorized, it returns UNKNOWN / equivalent fail-safe disposition;
5. any reopen proposal remains bounded by source identity, source revision, span/provenance, and owner authority.

### FAIL

Any of the following is a failure of the contract:

- omitted-from-representation is treated as absent-from-source;
- the old compact T1 view becomes a hidden ceiling for T2;
- unsupported source claims are automatically treated as relevant to every T2;
- a confidence score substitutes for evidence of T2 support;
- source provenance is treated as permission to reopen;
- the contract silently creates durable persistence, memory admission, Canon authority, or a new architecture owner.

## Evidence status

ESTABLISHED:

- F2 phenomenon exists in Titan test evidence;
- compact representation can omit later-material source evidence;
- omission is distinguishable from source absence;
- current Reader product result is not durable resume state;
- Titan already preserves fail-closed provenance and unsupported source claims.

NOT ESTABLISHED:

- generic task-conditioned sufficiency evaluator;
- later-task source-reopen policy;
- durable cross-session Reader resume;
- automatic T2 relevance classification of unsupported claims;
- need for a new subsystem.

## Next gate

The next justified step is a bounded executable contract fixture, not an implementation expansion.

That fixture should discriminate three cases using existing artifacts where possible:

1. T2 positively supported by compact representation -> SUFFICIENT;
2. T2 depends on evidence known to be omitted from compact representation -> REPRESENTATION_INSUFFICIENT;
3. support cannot be established either way without further source access -> UNKNOWN.

If existing Titan mechanisms can express all three without runtime changes, document evidence and STOP.

If they cannot, classify the exact missing surface first as TEST GAP or CONTRACT GAP. Only after a failing discriminating fixture should a minimal implementation refinement be considered.
