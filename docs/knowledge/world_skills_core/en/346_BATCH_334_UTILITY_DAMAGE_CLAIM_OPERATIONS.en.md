# BATCH 334: Utility Damage Claim Operations

**KnowledgeUnits:** 44  
**Namespace:** `damageclaimops.*`  
**Scope:** intake, field evidence, liability review, estimates, approvals, denials, settlements and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| damageclaimops.intake.claim_id | claim ID | RECORD | Claim ID links claimant, incident, location, date, damages and staff owner. | Creates controlled record for possible liability. |
| damageclaimops.intake.timeliness | timeliness screen | CONSTRAINT | Claims are checked against notice deadlines and limitation rules. | Late claims may follow different handling. |
| damageclaimops.intake.damage_type | damage type | RECORD | Damage is classified as property, vehicle, landscaping, plumbing, business loss or injury. | Determines investigation and insurance path. |
| damageclaimops.intake.initial_docs | initial documents | RECORD | Intake requests photos, receipts, estimates, invoices, police report or witness info. | Evidence quality shapes review. |
| damageclaimops.field.site_visit | site visit | METHOD | Field visit documents location, asset condition, work zone, weather and visible damage. | Captures facts before repairs erase evidence. |
| damageclaimops.field.photo_log | photo log | RECORD | Photos include overview, close-up, asset, damage, measurements and direction. | Makes later review possible. |
| damageclaimops.field.asset_history | asset history | RECORD | Work orders, breaks, complaints and maintenance near incident are pulled. | Shows whether utility action or failure was involved. |
| damageclaimops.field.crew_statement | crew statement | RECORD | Crew statements record work performed, timing, observations and unusual conditions. | Adds operational perspective. |
| damageclaimops.evidence.timeline | timeline | METHOD | Timeline aligns customer report, utility work, weather, alarms and field response. | Clarifies causation. |
| damageclaimops.evidence.map_overlay | map overlay | METHOD | Claim location is compared with assets, easements, service lines and work limits. | Prevents reviewing wrong asset. |
| damageclaimops.evidence.third_party | third-party involvement | RECORD | Contractors, other utilities or private plumbers are identified. | Liability may not rest with the utility. |
| damageclaimops.evidence.preexisting | preexisting condition | QUALITY_CHECK | Prior cracks, tree roots, old plumbing or grading are considered. | Avoids paying unrelated damage. |
| damageclaimops.liability.duty | duty analysis | MODEL | Review considers duty, breach, causation and documented damage. | Organizes fair liability decision. |
| damageclaimops.liability.negligence | negligence review | DECISION_RULE | Utility pays only when policy/legal review supports responsibility. | Protects public funds. |
| damageclaimops.liability.no_fault | no-fault event | MODEL | Main breaks or storms may cause damage without utility negligence. | Explains why harm and liability differ. |
| damageclaimops.liability.contractor | contractor liability | METHOD | Contractor-caused damage may be referred to contract insurance or indemnity. | Routes claim to responsible party. |
| damageclaimops.estimates.repair_estimate | repair estimate | RECORD | Claimant estimates are reviewed for scope, reasonableness and relation to incident. | Prevents inflated or unrelated costs. |
| damageclaimops.estimates.depreciation | depreciation | MODEL | Older property may be valued with depreciation or actual cash value by policy. | Settlement reflects value, not automatic new replacement. |
| damageclaimops.estimates.mitigation | mitigation costs | RECORD | Reasonable emergency mitigation may be reimbursable when tied to incident. | Encourages limiting further damage. |
| damageclaimops.estimates.business_loss | business loss review | QUALITY_CHECK | Business loss requires strong documentation of revenue, closure and causation. | Higher-risk claim category needs scrutiny. |
| damageclaimops.approval.threshold | approval threshold | CONSTRAINT | Settlement amount determines supervisor, legal, risk or board approval. | Maintains financial control. |
| damageclaimops.approval.legal_review | legal review | METHOD | Complex, injury or high-value claims go to legal/risk management. | Reduces unmanaged liability. |
| damageclaimops.approval.insurance_notice | insurance notice | METHOD | Insurer or risk pool is notified according to policy and threshold. | Preserves coverage. |
| damageclaimops.decision.approve | approval letter | RECORD | Approval states covered items, amount, release requirements and payment process. | Makes settlement terms clear. |
| damageclaimops.decision.partial | partial approval | RECORD | Partial decision explains accepted and denied components separately. | Reduces confusion and disputes. |
| damageclaimops.decision.denial | denial letter | RECORD | Denial explains evidence, policy basis and appeal or reconsideration option. | Documents fair decision. |
| damageclaimops.settlement.release | release form | CONSTRAINT | Payment may require signed release of claims. | Prevents duplicate recovery. |
| damageclaimops.settlement.payment | payment request | METHOD | Approved payment goes to finance with claim ID, payee, amount and documentation. | Controls disbursement. |
| damageclaimops.settlement.subrogation | subrogation | METHOD | If insurer pays claimant, utility may coordinate subrogation review. | Avoids paying same loss twice. |
| damageclaimops.communication.acknowledge | acknowledgment | METHOD | Claimant receives confirmation, process outline and expected review time. | Sets expectations. |
| damageclaimops.communication.status | status update | METHOD | Staff provide updates when investigation, legal review or insurer review is pending. | Reduces repeat contacts. |
| damageclaimops.communication.boundaries | communication boundaries | SAFETY_RULE | Staff avoid admitting liability before review is complete. | Protects legal position while remaining helpful. |
| damageclaimops.records.claim_file | claim file | RECORD | File stores intake, evidence, decisions, approvals, letters and payments. | Single source for audit and litigation. |
| damageclaimops.records.privilege | privileged material | CONSTRAINT | Legal advice and privileged documents are stored with access controls. | Protects sensitive review. |
| damageclaimops.records.retention | retention | CONSTRAINT | Claim records are retained per legal and insurance requirements. | Supports future disputes. |
| damageclaimops.qa.consistency | consistency check | QUALITY_CHECK | Similar claims are compared for consistent decisions. | Reduces unfair outcomes. |
| damageclaimops.qa.missing_evidence | missing evidence check | QUALITY_CHECK | Reviewer confirms core evidence before final decision. | Prevents weak denials or weak approvals. |
| damageclaimops.qa.fraud_flags | fraud flags | QUALITY_CHECK | Altered invoices, staged photos or inconsistent timeline are flagged. | Protects funds. |
| damageclaimops.reporting.claim_volume | claim volume | MEASUREMENT | Claims are tracked by type, cause, location, amount and outcome. | Shows risk patterns. |
| damageclaimops.reporting.loss_trend | loss trend | MODEL | Repeated claims near asset type or crew activity suggest operational issue. | Turns claims into prevention data. |
| damageclaimops.reporting.recovery | recovery tracking | RECORD | Recoveries from contractors, insurers or third parties are tracked. | Improves financial accuracy. |
| damageclaimops.review.after_action | after-action review | METHOD | Significant claims trigger review of field practices, communication and asset condition. | Prevents repeat damage. |
| damageclaimops.review.policy_update | policy update | METHOD | Claim trends may update forms, thresholds, contractor controls or customer guidance. | Keeps claim process aligned with risk. |
| damageclaimops.safety.injury_claim | injury claim escalation | SAFETY_RULE | Injury claims receive immediate risk/legal review and preservation of evidence. | Higher stakes require controlled handling. |
