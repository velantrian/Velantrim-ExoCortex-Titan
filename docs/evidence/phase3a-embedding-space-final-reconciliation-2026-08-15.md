# Phase 3A — Embedding Space Identity & Projection Contract Convergence

## Final reconciliation evidence — 2026-08-15

Parent architecture issue: #53  
Bounded child issue: #327  
Implementation PR: #328  
Documentation scope: `GITHUB_AND_NOTION`

## Accepted implementation

```text
final accepted PR head:           96f4aad2ae4a65203cc133dbe2af40ed869c99e8
protected squash merge/main:      4932727c348ec967564d8babf80e25ca82bce8be
parent:                            86ed963d2d31b9da174c88f0cf05cc27faced2b9
signature:                         VERIFIED / valid
```

## Exact-head acceptance evidence

```text
Full CI:                           #1210 · 31882948349 · SUCCESS
Docker:                            #799  · 31882948356 · SUCCESS
CodeQL:                            #48   · 31882948357 · SUCCESS
READY aggregate:                   #1315 · 31883253917 · SUCCESS
submitted reviews:                 0
review threads:                    0
PR comments:                       0
Notion candidate sync/read-back:   SYNCED
```

## Exact implementation post-merge evidence

```text
Full CI:                           #1211 · 31883324866 · SUCCESS
Docker:                            #800  · 31883324890 · SUCCESS
CodeQL:                            #49   · 31883324957 · SUCCESS
aggregate merge evidence:          #1316 · 31883324900 · SUCCESS
```

Full CI #1211 passed the blocking mypy gate, full pytest, core coverage ratchet ≥74%,
dependency vulnerability audit, reproducible wheel, deterministic SBOM and the repository
architecture/project-state/portable-KB guards.

No local CLI execution result and no Codex approval are claimed.

## Requirement closure

| Requirement | Final state |
|---|---|
| deterministic complete embedding-space identity | CLOSED |
| provider identity axis | CLOSED |
| model identity axis | CLOSED |
| model revision axis | CLOSED |
| dimension axis | CLOSED |
| normalization axis | CLOSED |
| pooling axis | CLOSED |
| distance metric axis | CLOSED |
| chunker version axis | CLOSED |
| preprocessing version axis | CLOSED |
| same-dimension incompatible spaces | FAIL CLOSED |
| legacy row auto-compatibility | FORBIDDEN / FAIL CLOSED |
| persistent storage owner | EXISTING OWNER REUSED |
| project schema migration | NOT REQUIRED · v7 PRESERVED |
| lexical fallback | PRESERVED |
| automatic rebuild on mismatch | NOT ADDED |
| erasure semantics | PRESERVED |
| dimension mismatch before scoring | FAIL CLOSED |
| PolicyKernel permission ownership | PRESERVED |
| CapabilityRegistry permission authority | NOT GRANTED |
| pipeline default-route change | NONE |
| persistent projection live wiring | NOT ADMITTED |
| provider/network execution | NOT ADMITTED |
| Canon/ESM mutation | NONE |

## Frozen authority state

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

## Implemented / tested / wired / enabled

```text
Implemented:            yes — bounded identity + dimension-safety contract
Tested:                 yes — focused tests + exact-head/post-merge repository gates
Wired:                  no — persistent projection remains outside live retrieval
Enabled:                no
Observed:               contract and fail-closed behavior in tests/CI only; no live semantic execution claim
Runtime authority:      false
Production authority:   false
```

## Closure boundary

This reconciliation closes only Phase 3A. Parent #53 remains a separate architecture line.
No Phase 3B admission follows automatically.

A future local embedding execution / persistent projection runtime-integration phase would
require a new live owner audit, explicit bounded admission, Titan-specific benchmark plan,
exact-head tests/CI, protected merge and synchronized GitHub/Notion evidence.

When this file is read from `main`, the repository-side Phase 3A final reconciliation is
merged. Resolve the exact documentation-closure merge SHA and current issue lifecycle from
live GitHub rather than hard-coding a self-referential future SHA into this pre-merge file.
