# Canonical initial raw provenance creation

Issue #290 closes the create-time residual left after #289.

- `raw_*` in `facts.derived_from` denotes L0 raw provenance and must resolve to `l0_raw_memory`.
- New fact + `l0_fact_provenance` + FACT_CREATED AuditChain evidence commit in the same parent transaction.
- A brand-new fact has no VersionStore pre-image by definition.
- Existing facts cannot be rebound by `store_fact()` or `store_facts_batch()`; their durable pointer wins.
- Post-create binding remains owned by `SQLiteGraphStore.link_raw_to_fact()` with its #289 CAS/version/provenance/audit contract.
- Non-`raw_` `derived_from` remains fact-lineage data such as GIST → VERBATIM and does not manufacture L0 provenance.
- `supersede_fact_cas()` follows the same parent-create rule for a newly inserted replacement fact.

No runtime or production authority follows from this convergence.
