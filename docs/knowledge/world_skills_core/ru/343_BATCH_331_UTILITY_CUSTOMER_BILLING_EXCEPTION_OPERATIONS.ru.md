# BATCH 331: Utility Customer Billing Exception Operations

**KnowledgeUnits:** 44  
**Namespace:** `billxops.*`  
**Scope:** high bills, leaks, estimates, meter reads, adjustments, disputes, approvals and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| billxops.intake.case_id | billing exception case | RECORD | Case ID links account, bill, customer contact, issue type and dates. | Prevents scattered notes from becoming inconsistent decisions. |
| billxops.intake.issue_type | issue classification | RECORD | Issues are classified as high bill, estimated read, leak, misread, rate error, move-in/out or dispute. | Routes work to the right review path. |
| billxops.intake.customer_statement | customer statement | RECORD | Customer explanation records occupancy, irrigation, leaks, repairs, travel and unusual use. | Gives context before changing bill data. |
| billxops.intake.deadline | dispute deadline | CONSTRAINT | Policies define how long customers have to dispute bills. | Protects fairness and revenue controls. |
| billxops.highbill.usage_compare | usage comparison | METHOD | Current usage is compared with prior periods, weather, household size and meter history. | Separates real use from possible error. |
| billxops.highbill.seasonality | seasonal pattern | MODEL | Irrigation, cooling, guests or business cycles can explain spikes. | Avoids treating every high bill as a leak. |
| billxops.highbill.neighbor_check | neighbor comparison | QUALITY_CHECK | Nearby accounts or district totals may show shared reading or pressure issues. | Detects systemic events. |
| billxops.highbill.threshold | high-bill threshold | DECISION_RULE | Review triggers may use percentage increase, volume, customer class or dollar amount. | Focuses staff effort on meaningful anomalies. |
| billxops.leak.leak_indicator | leak indicator | MEASUREMENT | AMI continuous flow, meter dial movement or usage pattern can indicate leaks. | Supports leak adjustment decisions. |
| billxops.leak.repair_proof | repair proof | RECORD | Repair invoice, plumber note, photo or customer attestation confirms corrective action. | Prevents repeated credits without repair. |
| billxops.leak.adjustment_formula | leak adjustment formula | MODEL | Adjustment may average normal use, split excess, or waive sewer charges by policy. | Makes credits consistent and auditable. |
| billxops.leak.repeat_limit | repeat leak limit | CONSTRAINT | Policy may limit number or frequency of leak adjustments. | Balances customer relief and utility revenue. |
| billxops.estimate.estimated_read | estimated read | RECORD | Estimated bills are flagged with reason, method and later true-up rule. | Customers can understand non-actual reads. |
| billxops.estimate.true_up | true-up calculation | METHOD | Actual read after estimate reconciles under- or over-billing. | Prevents permanent billing distortion. |
| billxops.estimate.no_read_reason | no-read reason | RECORD | No-read causes include access, endpoint failure, dog, weather, vacancy or meter damage. | Drives field correction. |
| billxops.meter.misread_review | misread review | QUALITY_CHECK | Suspected misreads compare photo, route sheet, AMI, register and historical pattern. | Prevents incorrect adjustments. |
| billxops.meter.multiplier | meter multiplier | CONSTRAINT | Large meters may require multiplier or register factor. | Wrong factor can massively distort bills. |
| billxops.meter.changeout_overlap | changeout overlap | FAILURE_MODE | Meter replacement can create duplicate, missing or reversed reads. | Needs reconciliation before billing. |
| billxops.meter.stopped_meter | stopped meter | FAILURE_MODE | Zero or flat use may indicate stopped meter rather than no consumption. | Protects revenue and service records. |
| billxops.rate.rate_code | rate code review | QUALITY_CHECK | Account class, meter size, sewer status and surcharges are checked. | Rate errors look like usage problems to customers. |
| billxops.rate.proration | proration review | METHOD | Move dates, rate changes and service periods are prorated. | Prevents overcharge at account transitions. |
| billxops.rate.tax_fee | tax and fee check | QUALITY_CHECK | Taxes, storm fees, fire fees and franchise charges are verified. | Some disputes are fee configuration issues. |
| billxops.adjustment.approval_level | approval level | CONSTRAINT | Credit thresholds define staff, supervisor or manager approval. | Maintains internal financial control. |
| billxops.adjustment.reason_code | adjustment reason code | RECORD | Each credit or debit uses standardized reason codes. | Enables reporting and audit. |
| billxops.adjustment.support_docs | support documents | RECORD | Adjustment file stores calculations, evidence, approvals and customer notice. | Makes decision defensible later. |
| billxops.adjustment.audit_trail | audit trail | RECORD | System logs who changed what, when and why. | Prevents unauthorized billing changes. |
| billxops.dispute.hold_status | dispute hold | METHOD | Account may be held from collections while review is active. | Avoids shutoff during unresolved dispute. |
| billxops.dispute.escalation | escalation path | METHOD | Complex disputes route to supervisor, field services, meter shop or legal. | Keeps difficult cases moving. |
| billxops.dispute.hearing | hearing record | RECORD | Formal appeals record evidence, decision, date and final amount. | Supports due process. |
| billxops.communication.explanation | customer explanation | METHOD | Staff explain findings, policy, calculation and next steps in plain language. | Reduces repeat contacts. |
| billxops.communication.denial_letter | denial letter | RECORD | Denial states reason, evidence reviewed, policy basis and appeal option. | Makes negative decisions transparent. |
| billxops.communication.credit_notice | credit notice | RECORD | Credit notice shows amount, bill impact and remaining balance. | Prevents confusion after adjustment. |
| billxops.field.field_read | field read order | METHOD | Field crew verifies read, meter condition, leak indicator and access. | Brings physical evidence into billing review. |
| billxops.field.premise_leak | premise leak observation | OBSERVATION | Running toilets, irrigation leaks or service leaks may be noted when visible. | Helps customer resolve high usage. |
| billxops.field.safety_note | field safety note | RECORD | Dogs, locked gates, unsafe pits and hostile contacts are recorded. | Protects crews and future visits. |
| billxops.qa.batch_review | batch review | QUALITY_CHECK | Large adjustment batches are sampled for correct reason, math and approval. | Catches systemic processing errors. |
| billxops.qa.segmentation | customer class segmentation | MODEL | Residential, commercial and irrigation accounts need different review expectations. | Avoids false positives. |
| billxops.qa.duplicate_credit | duplicate credit check | QUALITY_CHECK | System checks whether same event already received credit. | Prevents double relief. |
| billxops.records.retention | record retention | CONSTRAINT | Billing exception records are retained according to finance and public-record rules. | Supports later audits. |
| billxops.records.linked_cases | linked cases | RECORD | Related leak, meter, shutoff or complaint cases are linked. | Shows full customer history. |
| billxops.reporting.exception_volume | exception volume | MEASUREMENT | Reports track case counts by type, amount, age and outcome. | Shows workload and policy impact. |
| billxops.reporting.credit_total | credit total | MEASUREMENT | Credit totals are monitored by period, reason and approver. | Supports financial oversight. |
| billxops.reporting.root_cause | root-cause report | MODEL | Trends identify meter failures, route issues, confusing bills or policy gaps. | Turns exceptions into process improvement. |
| billxops.review.policy_update | policy update review | METHOD | Repeated disputes inform changes to forms, notices, rates or leak policy. | Keeps billing rules practical. |

