# 🏛️ CANON: Truth Engine + Ring Zero — the unified etalon of Velantrim

> **Status:** etalon specification (v1.0, draft-for-implementation) · **Date:** 2026-05-31
> **Purpose:** the single source of truth from which the **full-fledged code** of Velantrim's
> dual-core architecture is written. It unifies two studied etalons into a single canon.
>
> **Source etalons:**
> - 🛡️ **Small Core / Ring Zero** — `Small Core Complex/small_core/` (+ `manifest/`, `OVERVIEW.md`)
> - 🔬 **Truth Engine** — `velantrim_core-3/velantrim_core/velantrim/core/` (P0-1…P0-5, Patch 5, 6.1–6.3)
> - 🔀 **Bridge** — `VELANTRIM_Dual_Core_Router/README.ru.md`
> - 🧠 **Big Core** — `VELANTRIM_ExoCortex_V8.6/` (this repository)
>
> ⚠️ **Historical boundary:** this document is a normative etalon drafted on
> 2026-05-31 from V8.6-era source snapshots. Parenthetical `V8.6:` annotations in
> Part V are immutable **historical audit evidence**, not current Titan 9.0
> implementation status. For current implementation truth, re-read live `main`, tests
> and CI, `docs/ai/CURRENT_STATE.md`, and the relevant current ownership/inventory
> documents. Do not turn an old ❌/⚠️ marker into a current backlog claim without
> revalidation at the exact SHA under review.

---

## 0. TL;DR — one formula

```text
Ring Zero      = conscience + BIOS + immunity (can the ACTION be trusted?)
Truth Engine   = epistemics (can the ANSWER be trusted? is there evidence?)
Big Core       = memory + growth + language + interfaces (variants)
Dual Core Router = the choice of when a strict pass through the small cores is needed
Practical knowledge = the data layer under Big Core, passing through the same gates
```

Both small cores serve a single meta-principle: **honest intelligence** — the system does not confuse
*knowledge, hypothesis, desire, and falsehood* and does not pass off the unknown as known.

---

## 1. Meta-principle and philosophical pillars

### 1.1 Meta-principle
> The strength of the small core lies not in the amount of knowledge, but in the fact that it **protects the conditions of honest knowledge**.
> The small core is not obligated to know everything. It is obligated not to let the smartest layer lose its honesty.

### 1.2 Three pillars (confirmed in Core-3 code)
1. **Graph = Truth** — truth is held by the verified graph + policy, not the LLM's text.
2. **LLM = Language** — the LLM only *extracts structure* and *formulates*, with mandatory evidence; it is not a source of truth.
3. **Evidence before Answer** — no structural proof ⇒ `gap_notice` ("honest I don't know"), not an answer. Trace-only: every answer is explainable.

### 1.3 Five immutable principles (Ring Zero manifest)
| id | Principle | Meaning |
|----|---------|-------|
| `graph_truth` | Graph = Truth | Validated knowledge lives in the verified graph, not only in generated speech |
| `never_lie` | Never lie to the user | No evidence — the system says "I don't know" |
| `hypothesis_not_fact` | Hypothesis is not fact | A hypothesis must not be presented as validated knowledge |
| `life_priority` | Life is priority | Human safety and dignity outrank optimization |
| `small_core_immutable` | Big Core cannot modify Small Core | The working system may *request* a decision, but not rewrite the protected core |

`can_be_modified_by_big_core: false` — this is a manifest invariant, not a wish.

---

## 2. System map

```text
            ┌─────────────────────────────────────────────┐
            │            🛡️ RING ZERO (small core)         │  ← boundaries (invariants)
            │  manifest · invariants I0–I8 · PolicyEngine  │
            │  boot · checkpoint/rollback · quarantine     │
            └───────────────┬─────────────────────────────┘
                            │ ActionContract → PolicyDecision
                            ▼
            ┌─────────────────────────────────────────────┐
            │           🧠 BIG CORE (ExoCortex)            │  ← variants (growth)
            │  memory · profiles · LLM · interfaces · layers│
            └───────────────┬─────────────────────────────┘
                            │ query + facts + relations
                            ▼  (via 🔀 Dual Core Router, for strict queries)
            ┌─────────────────────────────────────────────┐
            │        🔬 TRUTH ENGINE (Core-3)              │  ← the strict organ of truth
            │  truth_policy · EvidenceRef · TruthGate      │
            │  causal_graph · TraceRecord(verdict)         │
            └─────────────────────────────────────────────┘

      📚 Practical knowledge (world_skills_core) — data under Big Core, verified by the same gates.
```

**Invariants** — that which is frozen (Ring Zero, manifest, contracts).
**Variants** — that which grows (memory, profiles, layers, Big Core knowledge).
The small core sets the boundaries **within** which the big core can grow safely.

---

# 🛡️ PART I — Ring Zero (small core): constitution and immunity

Ring Zero answers not the question "what to think?", but the question "**can this action be trusted?**".

## 3.1 ActionContract — the request format from Big Core to Ring Zero

Big Core does **not** ask in a string "may I add_fact?". It sends a structural contract.

| Field | Type | Req. | Purpose |
|------|-----|:----:|------------|
| `actor` | str | ✅ | who initiates (`big_core`, `llm`, `agent`, `user`, …) |
| `action` | str | ✅ | `add_fact` / `write_memory` / `promote_fact` / `transition_state` / `delete_fact` / `modify_policy` / `rewrite_core` / … |
| `target` | str | ✅ | object of the action (`memory`, `small_core`, `ring_zero`, `values_core`, `immutable_core`, …) |
| `claim` | str? | — | the assertion, if any |
| `from_state` | str? | — | source epistemic state |
| `to_state` | str? | — | target state |
| `confidence` | float? | — | ∈ [0.0, 1.0] |
| `evidence_refs` | tuple[str] | — | references to evidence (see §4.2 — must be structural) |
| `risk` | str | — | `low` \| `medium` \| `high` \| `critical` (default `low`) |
| `reason` | str? | — | human-readable justification |
| `metadata` | dict | — | arbitrary |
| `created_at` | str (UTC ISO) | — | timestamp (timezone-aware) |

**`structural_errors()`** (form validation, → invariant I0): requires non-empty `actor/action/target`,
`risk ∈ ALLOWED_RISKS`, `confidence` numeric and ∈ [0,1].

## 3.2 Invariants I0–I8 (formal rules, may not be violated)

`check_invariants(contract) -> list[InvariantFinding{code, severity, message}]`.
Severity ∈ {`block`, `caution`, `quarantine`}.

| Code | Condition | Severity | Meaning |
|-----|---------|:--------:|-------|
| **I0** | `structural_errors()` non-empty | `block` | contract is broken by form |
| **I1** | `actor ∈ {big_core, llm, agent}` AND `target ∈ PROTECTED_TARGETS` | `block` | Big Core cannot target Small Core / Ring Zero |
| **I2** | `action ∈ MUTATION_ACTIONS` AND `target ∈ PROTECTED_TARGETS` | `block` | protected targets are immutable via ordinary contracts |
| **I3** | `to_state ∈ VALIDATED_STATES` AND no `evidence_refs` | `block` | Validated/ImmutableCore requires evidence |
| **I4** | `to_state ∈ VALIDATED_STATES` AND `confidence < 0.85` | `block` | Validated/ImmutableCore requires confidence ≥ 0.85 |
| **I5** | `action ∈ WRITE_ACTIONS` AND `confidence < 0.5` | `caution` | downgrade a low-confidence write to Observed/Hypothesis |
| **I6** | text contains `DANGEROUS_WORDS` (lie/deceive/fake/harm/kill/break_truth) | `quarantine` | protective danger marker |
| **I7** | `risk == "critical"` | `quarantine` | critical risk → quarantine + manual review |
| **I8** | `risk == "high"` | `caution` | high risk → cautious mode |

Sets (canonical):
```text
PROTECTED_TARGETS = {small_core, ring_zero, values_core, immutable_core}
WRITE_ACTIONS     = {add_fact, write_memory, promote_fact, transition_state}
MUTATION_ACTIONS  = WRITE_ACTIONS ∪ {delete_fact, modify_policy, rewrite_core}
VALIDATED_STATES  = {validated, immutablecore, immutable_core}
DANGEROUS_WORDS   = {lie, deceive, fake, harm, kill, break_truth}
```

## 3.3 PolicyEngine — the single decision point

`decide(contract) -> PolicyDecision{allowed, mode, reason, findings, required_state}`.
Severity priority (from strict to lenient):

```text
1. quarantine ∈ severities → escalate(QUARANTINE); allowed=False
2. block      ∈ severities → allowed=False ("blocked by Small Core invariant")
3. caution    ∈ severities → escalate(CAUTIOUS); allowed=True, required_state="Observed"
4. else if NOT write_allowed (QUARANTINE/RECOVERY mode) → allowed=False
5. else → allowed=True ("allowed")
```

🔒 Every decision is written to the **AuditLog** (`policy_decision` + contract + decision). The journal is append-only (JSONL).

## 3.4 Safety modes (SystemSafetyState)

| Mode | Order | write_allowed | validated_write | What is allowed |
|-------|:------:|:------------:|:---------------:|-----------|
| `NORMAL` | 0 | ✅ | ✅ | read, write, learn, answer, promote to Validated |
| `CAUTIOUS` | 1 | ✅ | ❌ | read; write **only** Observed/Hypothesis |
| `QUARANTINE` | 2 | ❌ | ❌ | read and diagnostics only |
| `RECOVERY` | 3 | ❌ | ❌ | rollback to checkpoint, recovery |

- `escalate(mode, reason)` — **monotonically upward** (only raises strictness).
- `clear_to_cautious()` / `clear_to_normal()` — lowering is **manual only** (after review).
- `write_allowed = mode ∈ {NORMAL, CAUTIOUS}` · `validated_write_allowed = mode == NORMAL`.

## 3.5 Boot / Checkpoint / Integrity / Audit (mandatory gates)

`required_gates = [boot_check, action_contract, policy_gate, truth_boundary, checkpoint, rollback, quarantine]`.

- **BootProtocol.verify(root, required_paths, expected_hashes)** → `BootReport{allowed, reasons, checked_root}`:
  checks the existence of the Big Core root, the presence of mandatory paths, and the **matching of hashes** (`hash_tree` + `compare_hashes`). Audited.
- **Integrity** — hashes of files/versions of Big Core; desync → reasons in BootReport (startup forbidden).
- **CheckpointStore** — saving/rolling back state (target: persistent on disk; draft — in-memory).
- **Rollback** — find the best safe checkpoint and restore (triggers RECOVERY).

## 3.6 Ring Zero contract (in/out)
```json
// IN  (ActionContract)
{ "actor":"big_core","action":"promote_fact","target":"memory",
  "claim":"DNA stores genetic information","from_state":"Supported",
  "to_state":"Validated","confidence":0.94,
  "evidence_refs":[{"source_id":"bio_textbook_01","quote":"…"}],"risk":"low" }
// OUT (PolicyDecision)
{ "allowed":true,"mode":"normal","reason":"allowed","findings":[],"required_state":null }
```

---

# 🔬 PART II — Truth Engine (Core-3): epistemics

## 4.1 Unified Truth Policy — ONE law (P0-4)

The single law of fact admissibility, on which **BOTH** writing (TruthGate) **AND** reading (TraceRecord) rely:

```text
admissible(fact) ⇔  confidence ≥ conf_threshold
                AND  a valid EvidenceRef (source → source_id)
                AND  not known_false and not contradicted (checked against the graph)
```

`fact_admissible(fact, conf_threshold) -> (ok: bool, reason: str)`, reasons: `low_confidence` | `no_evidence` | `ok`.
🚫 It is **forbidden** to have several diverging policies for writing and reading.

## 4.2 EvidenceRef — the evidence contract

```text
EvidenceRef{ source_id?, chunk_id?, span?:[int,int], quote? }
is_valid() ⇔ source_id is present AND there is at least one locator (chunk_id | span | quote)
```
- Stored in the DB as a JSON string. `from_raw()` accepts dict | JSON string | plain string | None.
- **A plain string is intentionally invalid** (no `source_id`) — the old format does not pass the contract and requires updating.
- `missing_fields()` explains what is missing (for held reasons).

## 4.3 TruthGate — promotion pending → validated

`TruthGate(store, graph, promote_threshold=0.75)`:
- `submit_inferred(inferred)` — saves the inferred relation as **PENDING**, evidence is serialized.
- `review_pending()` → `{promoted, rejected, held}`. For each pending forward relation:
  1. `is_known_false(frm,to,rtype)` (validated deny edge) → **refuted** (rejected: known_false)
  2. validated/approved `contradicts` affirm edge → **refuted** (rejected: contradicts)
  3. `EvidenceRef.from_raw(...).is_valid()` false → **held** (`no_evidence:<fields>`)
  4. empty `source` → **held** (no_source)
  5. `confidence ≥ promote_threshold` → **validated** (cascade onto the inverse via pair_id) · otherwise **held** (low_confidence)

## 4.4 TraceRecord — the answer verdict (P0-4/P0-5)

`build_facts_pack` admits into the pack **only** facts that passed §4.1 (the rest → `rejected` with a reason, `evidence_ref` is filled in).
`build_trace` issues the verdict:

| Condition | decision | truth_status | Meaning |
|---------|:--------:|:------------:|-------|
| there is a validated `contradicts`/`known_false` between facts of the pack | **`reject`** | contradicted | answer rejected |
| no fact passed policy (incl. high-conf without source) | **`gap_notice`** | insufficient | honest "I don't know" |
| otherwise | **`allow`** | validated | N facts with evidence + a path of K edges |

`TraceRecord{ query, intent, facts_pack_id, evidence_ids, path[PathStep], truth_status, decision, note }`.
`path` is built only over `validated/approved`, non-inverse edges between admitted facts (explainability).

## 4.5 Causal graph — rules

- **Only FORWARD types** are added; the inverse is created automatically. `FORWARD_TYPES = {causes, prevents, requires, enables, implies, contradicts, generalizes, specializes, precedes, follows, composes, analogous_to, becomes}`.
- **Idempotency (P0-3):** a duplicate `(from,to,type,source)` → the **existing** id is returned (no phantoms, no silent OR IGNORE).
- **Atomicity:** forward + inverse are written in **one transaction** with a shared `pair_id`.
- **Status cascade (P0-2):** `set_status(rid)` changes the status of the **entire pair** via `pair_id`.
- **Negative knowledge:** `polarity='deny'` = "A is NOT rtype B". `is_known_false` blocks only by validated/approved deny.
- **Bi-temporal:** `valid_from/valid_to`, `as_of` queries (Pearl L2 do-operator in `propagate_change`).
- DB invariant: `CHECK(from≠to)`, `CHECK(polarity IN ('affirm','deny'))`, `UNIQUE(from,to,type,source)`.

## 4.6 Store — integrity invariants

- **A single source of truth — the DB.** ❌ **No L0 cache** desyncable with L1 ⇒ split-brain is impossible *by construction*.
- **Thread safety:** all DB access goes through the locked API (`query/execute/transaction`) under a **single reentrant `RLock`**. No one outside the store touches `.conn` directly.
- **UPSERT, not `INSERT OR REPLACE`:** REPLACE = DELETE+INSERT → `ON DELETE CASCADE` wipes relations. UPSERT updates the row in place, preserving `fact_id`, relations, and `created_at`.
- `transaction()` — an atomic block: commit all at once or rollback.

## 4.7 Inference discipline → always PENDING

Any auto-inference (affordance→causal, ingest inference) is written as `truth_status='hypothesis'/review_state='pending'`,
the concept is resolved to a `fact_id` (not a bare string), only valid FORWARD types.
🚫 It is **forbidden** to write an inferred relation directly as `approved/validated`.

## 4.8 Retrieval — HybridRetriever
`score = α·lexical + γ·graph_proximity + δ·recency` (normalized [0..1]; defaults α=0.5, γ=0.35, δ=0.15, decay=0.7, depth=3).
The graph **participates in ranking** (recursive CTE, weight spreads over `causes/enables/requires/...`). The honest name is "graph proximity", not "PageRank". Flags `use_graph/use_recency` for ablation in eval.

## 4.9 Living Context — 8 dimensions
`LivingContext`: **WHERE** (locations) · **WHO** (agents) · **HOW** (affordances) · **WHAT** (products) · **FEEL** (qualities) · **ROLE** (systemic_roles) · **TIME** (temporal) · **DEEP** (deep_knowledge).
Affordances are **agent-relative** (Gibson): a tree affords "to nest" for a bird, "to fell" for a human. Lossless `to_dict/from_dict`, provenance on every affordance.

## 4.10 LLM = Language — an extractor with mandatory evidence
The LLM **extracts structure** (relations + 8-dimensional context), the prompt **forces** it to return `evidence_ref{source_id,chunk_id,span,quote}`.
`confidence = the fraction of self-consistency runs that agree on (from,to,type)`; evidence — the first valid one (provenance is not averaged). All extracted relations are born `pending`. No LLM → a deterministic regex fallback.

## 4.11 FSRS — maturation through use
`plasticity_factor ∈ [0.3..1.0]` from `retrieval_count`, **not** from wall-clock. The agent was turned off for 14 days → facts did not "mature". Exception: `INVARIANT/PRINCIPLE` mature slowly over time (rarely queried).

---

# 🔀 PART III — Unification: the single gateway

## 5.1 Unified vocabulary of decisions

The two small cores and the router must speak **one language of verdicts**:

| Ring Zero (PolicyDecision) | Truth Engine (TraceRecord) | Dual Core Router | Unified verdict |
|----------------------------|----------------------------|------------------|----------------|
| `allowed=True, mode=normal` | `decision=allow` | `allow` | **ALLOW** — answer with reliance on facts |
| `caution` / `required_state=Observed` | `decision=gap_notice` | `gap_notice` | **GAP_NOTICE** — "insufficient data" |
| `block` / `quarantine` | `decision=reject` | `reject` | **REJECT** — do not issue the assertion |

> Ring Zero — the **coarse constitutional** gate (is this *action* permissible).
> Truth Engine — the **fine epistemic** gate (is there *evidence* behind the *answer*).
> This is one law on two levels: I3/I4 (evidence+conf for Validated) ≡ truth_policy (evidence+conf for admissible).

## 5.2 Unified vocabulary of epistemic states

The canonical set (superset of ESM V8.6 ∪ Core-3 ∪ Ring Zero):
```text
Observed → Hypothesized/Supported → Validated → ImmutableCore
                     ↘ Contradicted / Collapsed / Deprecated
relations.truth_status: pending → validated | refuted   (+ review_state: pending/approved)
relations.polarity:     affirm | deny (negative knowledge)
```
New facts are **born `Observed`**. Promotion to `Validated` — only through TruthGate (evidence+conf≥0.75) AND when `validated_write_allowed` (NORMAL mode). Up to `ImmutableCore`/constitution — conf ≥ 0.85 (I4).

## 5.3 End-to-end query flow (reference)

```text
boot:    BootProtocol.verify(big_core_root, hashes) → else RECOVERY
write:   Big Core → ActionContract → PolicyEngine.decide
             ├─ REJECT (block/quarantine) → StopRule / Quarantine / Rollback
             ├─ GAP/CAUTION → write only Observed/Hypothesis
             └─ ALLOW → store_fact → (inferred → TruthGate.submit_inferred = pending)
review:  TruthGate.review_pending → promoted/refuted/held
read:    Big Core → (Router: high-risk?) → build_trace(query)
             ├─ reject     → an honest refusal (+ blocked_reason)
             ├─ gap_notice → "insufficient data" (the LLM does not "make things up")
             └─ allow      → the LLM formulates the ANSWER strictly from the FactsPack (+ TraceRecord)
audit:   every Ring Zero decision and every Truth Engine verdict → append-only journal
```

## 5.4 Unified ladder of thresholds (reconcile)

The three thresholds are **not a contradiction, but three rungs** of a single ladder. The implementation must keep them in **one place** as explicit constants:

| Rung | conf threshold | Additionally | Source |
|---------|:----------:|---------------|----------|
| **Admission into the answer** (admissible/read) | ≥ **0.5** | + valid evidence | `truth_policy.DEFAULT_CONF_THRESHOLD` |
| **Promotion to Validated** (graph) | ≥ **0.75** | + evidence + no contradiction/known_false | `TruthGate.promote_threshold` |
| **Constitutional Validated/Immutable** | ≥ **0.85** | + evidence_refs (I3) | Ring Zero `I4` |

Invariant: `0.5 ≤ 0.75 ≤ 0.85`. A low-confidence write (<0.5) → `caution`/Observed (I5).

## 5.5 Dual Core Router — the bridge contract
```json
// IN
{ "query":"…", "facts":[{ "fact_id","claim","confidence","source" }],
  "relations":[{ "from_fact_id","to_fact_id","relation_type","confidence","source" }],
  "mode":"strict" }
// OUT
{ "decision":"allow|gap_notice|reject", "truth_status":"validated|insufficient|contradicted",
  "evidence_ids":["…"], "trace_note":"…", "blocked_reason":null }
```
Integration rules (from Dual Core Router): the adapter does **not** drag the small core inside Big Core; the subprocess variant comes first (isolation); the small core does **not** write to Big Core's main SafeDB without separate permission; the router is engaged **not on all** queries, but on strict/high-risk ones (medicine, law, science, grant).

---

# 🧭 PART IV — Invariants vs Variants vs Practical knowledge

| Layer | Nature | Where | Can it be changed? |
|------|---------|-----|:-------------:|
| Manifest + invariants I0–I8 | **invariant** | Ring Zero | ❌ only through an explicit constitutional process, not Big Core |
| Contracts (ActionContract, EvidenceRef, TraceRecord, FORWARD_TYPES) | **invariant** | both small cores | ❌ must not be broken (versioning — yes) |
| Truth Policy, threshold ladder | **quasi-invariant** | Truth Engine | ⚠️ only in concert, in one place |
| Memory, profiles, lenses, layers L0–L6 | **variant** | Big Core | ✅ grows freely within the boundaries |
| Practical knowledge (`world_skills_core`) | **data** | Big Core | ✅ is populated; passes the same gates (evidence/TruthGate) |

Practical knowledge consists of **facts with a source**, not an exception to the rules: every `world_skills_core` batch
upon entering the graph must carry a `source` and pass Truth Policy; unproven ones remain Observed/pending.

---

# ✅ PART V — Normative conformance checklist + historical V8.6 snapshot

> The requirements C1–C12 below are normative. The parenthetical `V8.6:` notes beside
> C1–C9 are **historical findings captured on 2026-05-31**. They do not assert the
> current Titan 9.0 result of those checks. Current conformance must be re-established
> from live code, tests, CI and current inventories at the exact SHA under review.

A full-fledged implementation of the dual-core system **must** satisfy:

- **C1.** A unified `truth_policy`, used by BOTH writing AND reading. *(V8.6: ❌ 4+ diverging gates)*
- **C2.** A structural `EvidenceRef` (source_id + locator) connected to promotion; a plain string is invalid. *(V8.6: ❌ `EvidenceItem` exists, but is not connected; `_count_evidence` returns 1)*
- **C3.** The read path issues `allow|gap_notice|reject`; high-conf without evidence ⇒ `gap_notice`; does not answer at 0 facts. *(V8.6: ❌ answers on bare confidence)*
- **C4.** A contradiction/known_false between answer facts ⇒ `reject` at the answer stage, not only offline. *(V8.6: ❌ only annotates)*
- **C5.** Inference is written `pending`, promotion only through TruthGate. *(V8.6: ⚠️ `causal_bridge` writes inferred as approved)*
- **C6.** A single source of truth (no desync cache) OR a cache under a lock with an L1→L0 write. *(V8.6: ❌ split-brain C1/C2/H3)*
- **C7.** All DB access is thread-safe (RLock/single connection or per-op with a lock). *(V8.6: ❌ unlocked L0, shared graph conn M1)*
- **C8.** Graph: idempotent `add_relation`, atomic forward+inverse with `pair_id`, `set_status` cascade. *(V8.6: ⚠️ inverse metadata bug M2)*
- **C9.** Ring Zero as a real gate before a Big Core write (PolicyEngine.decide), not a disabled `graph_ring_zero`. *(V8.6: ❌ `ENABLE_IMMUTABLE_CORE` off, 0% coverage)*
- **C10.** Boot integrity check of Big Core (hashes) before startup; desync → RECOVERY.
- **C11.** Append-only audit on every Ring Zero decision and every Truth Engine verdict.
- **C12.** The threshold ladder `0.5 ≤ 0.75 ≤ 0.85` in one place as explicit constants.

> Historical gap analysis: see the deep audit 2026-05-31 (findings C1/C2/H1–H3,
> M1–M2, security) and `docs/AUDIT_V8_6.ru.md`. Each `V8.6:` ❌/⚠️ above records that
> historical snapshot only; it must not be cited as a current Titan 9.0 failure or
> current backlog item without revalidation.

---

## Appendix A — Canonical constants
```text
# Ring Zero
PROTECTED_TARGETS = {small_core, ring_zero, values_core, immutable_core}
VALIDATED_STATES  = {validated, immutablecore, immutable_core}
ALLOWED_RISKS     = {low, medium, high, critical}
I4_VALIDATED_MIN_CONF = 0.85 ; I5_WRITE_CAUTION_BELOW = 0.5
MODE_ORDER: NORMAL<CAUTIOUS<QUARANTINE<RECOVERY ; write_allowed = {NORMAL,CAUTIOUS}

# Truth Engine
DEFAULT_CONF_THRESHOLD = 0.5     # admissible / read
PROMOTE_THRESHOLD      = 0.75    # pending → validated
FORWARD_TYPES (13) ; PROX_TYPES = {causes,enables,requires,prevents,composes,becomes}
retrieval: alpha=0.5 gamma=0.35 delta=0.15 decay=0.7 max_depth=3
FSRS: plasticity ∈ [0.3..1.0] ; PRIMING_WINDOW_DAYS=14
```

## Appendix B — Glossary
- **Ring Zero / Small Core** — the protected immutable core (constitution + BIOS + immunity).
- **Truth Engine / Core-3** — the strict organ of truth (evidence + graph + verdict).
- **Big Core / ExoCortex** — the working system (memory, language, interfaces).
- **ActionContract** — a structural request from Big Core → Ring Zero.
- **EvidenceRef** — a structural evidence object (source_id + locator).
- **TraceRecord** — an explainable answer verdict (allow/gap_notice/reject + path).
- **gap_notice** — an honest "I don't know" in the absence of evidence.
- **known_false** — a validated deny edge (negative knowledge).
- **split-brain** — desync of the L0 cache and the L1 store (forbidden by the canon, C6).

## Appendix C — Etalon files (where the canon was taken from)
```text
Small Core Complex/manifest/small_core_manifest.draft.json   # manifest (5 principles)
Small Core Complex/small_core/invariants.py                  # I0–I8
Small Core Complex/small_core/action_contract.py             # ActionContract
Small Core Complex/small_core/policy_engine.py               # PolicyEngine.decide
Small Core Complex/small_core/quarantine.py                  # SafetyMode / SystemSafetyState
Small Core Complex/small_core/boot_protocol.py               # BootProtocol.verify
velantrim_core-3/.../core/truth_policy.py                    # the unified law
velantrim_core-3/.../core/truth_gate.py                      # promotion
velantrim_core-3/.../core/evidence.py                        # EvidenceRef
velantrim_core-3/.../core/trace.py                           # TraceRecord / verdict
velantrim_core-3/.../core/causal_graph.py                    # the truth graph
velantrim_core-3/.../core/store.py                           # integrity invariants
VELANTRIM_Dual_Core_Router/README.ru.md                      # the adapter contract
```

---

*Canon v1.0 — the unified etalon. Changes — only through coordinated versioning; violating the invariants of §1.3 and the contracts of §3–§4 is forbidden. This document is what the code is written from.*