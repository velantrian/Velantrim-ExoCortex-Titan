# BATCH 333: Water Conservation Rebate Program Operations

**KnowledgeUnits:** 44  
**Namespace:** `rebateops.*`  
**Scope:** applications, eligibility, inspections, devices, approvals, payments, audits and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| rebateops.program.rebate_catalog | rebate catalog | RECORD | Catalog lists eligible devices, rebate amounts, limits, dates and required proof. | Gives customers and staff one rule source. |
| rebateops.program.budget_cap | budget cap | CONSTRAINT | Program stops, waits or prorates when budget is exhausted. | Prevents overcommitment. |
| rebateops.program.target_savings | target savings | MODEL | Program estimates water savings by device, customer class and adoption rate. | Connects rebates to conservation goals. |
| rebateops.application.case_id | application ID | RECORD | Application ID links customer, device, property, documents and payment status. | Tracks request from intake to closeout. |
| rebateops.application.required_docs | required documents | CONSTRAINT | Receipts, photos, model numbers, install date and account status may be required. | Prevents unsupported payments. |
| rebateops.application.preapproval | preapproval | DECISION_RULE | Some rebates require approval before purchase or installation. | Controls eligibility before customer spends money. |
| rebateops.application.duplicate_check | duplicate check | QUALITY_CHECK | Account, address, serial and receipt are checked for prior rebates. | Prevents double payment. |
| rebateops.eligibility.account_good | account eligibility | QUALITY_CHECK | Account class, service status, arrears and location are checked. | Ensures funds serve program jurisdiction. |
| rebateops.eligibility.device_qualified | device qualification | CONSTRAINT | Device must meet efficiency, label, model or performance criteria. | Rebate buys verified conservation. |
| rebateops.eligibility.old_device | old device replacement | RECORD | Some programs require proof of inefficient fixture removed. | Avoids paying for upgrades that do not save water. |
| rebateops.eligibility.property_limit | property limit | CONSTRAINT | Maximum rebates per property, year or device type are enforced. | Spreads funds fairly. |
| rebateops.devices.toilet | high-efficiency toilet | METHOD | Toilet rebate checks gallons per flush and installation proof. | Reduces indoor baseline demand. |
| rebateops.devices.washer | efficient washer | METHOD | Washer rebate verifies eligible model and residential account. | Saves water and energy in frequent use. |
| rebateops.devices.irrigation_controller | smart irrigation controller | METHOD | Controller rebate verifies weather-based or soil-moisture capability. | Reduces outdoor overwatering. |
| rebateops.devices.turf_removal | turf removal | METHOD | Turf program verifies area removed, replacement landscape and irrigation changes. | Targets high outdoor demand. |
| rebateops.devices.rain_barrel | rain barrel | METHOD | Rain barrel rebate may require capacity, downspout connection and mosquito control. | Supports small nonpotable reuse. |
| rebateops.inspection.pre_inspection | pre-inspection | INSPECTION | Pre-inspection confirms existing condition before customer changes site. | Prevents fraudulent after-the-fact claims. |
| rebateops.inspection.post_inspection | post-inspection | INSPECTION | Post-inspection verifies installed device, landscape and continued service. | Confirms conservation measure exists. |
| rebateops.inspection.photo_review | photo review | QUALITY_CHECK | Submitted photos are checked for date, location, device and completeness. | Reduces field visits while controlling fraud. |
| rebateops.inspection.failed_inspection | failed inspection | RECORD | Failure records missing device, wrong model, incomplete install or unsafe condition. | Gives customer correction path. |
| rebateops.approval.review_queue | review queue | METHOD | Applications are reviewed by received date, completeness, budget and priority. | Keeps workflow fair. |
| rebateops.approval.approval_code | approval code | RECORD | Approval stores eligible amount, reviewer, program year and funding source. | Supports payment and audit. |
| rebateops.approval.denial | denial record | RECORD | Denial states rule, missing proof, ineligible device or deadline miss. | Makes decisions transparent. |
| rebateops.approval.appeal | appeal path | METHOD | Customers can submit missing evidence or request review under policy. | Reduces unfair denials. |
| rebateops.payment.payee | payee verification | QUALITY_CHECK | Payee name, account, address and tax requirements are verified. | Prevents payment errors. |
| rebateops.payment.payment_batch | payment batch | METHOD | Approved rebates are grouped for finance processing with controls. | Efficient payment without losing audit trail. |
| rebateops.payment.status | payment status | RECORD | Status tracks approved, sent to finance, paid, voided or returned. | Customer service can answer payment questions. |
| rebateops.payment.tax_form | tax form trigger | CONSTRAINT | Large incentives may require tax forms or vendor records. | Keeps finance compliant. |
| rebateops.audit.sample_audit | sample audit | QUALITY_CHECK | Random paid rebates are checked for documents, eligibility and inspection evidence. | Detects errors and fraud. |
| rebateops.audit.receipt_fraud | receipt fraud screen | QUALITY_CHECK | Duplicate receipts, altered dates or mismatched models are flagged. | Protects public funds. |
| rebateops.audit.site_recheck | site recheck | INSPECTION | Some sites are rechecked after payment for continued compliance. | Discourages temporary installations. |
| rebateops.outcomes.savings_estimate | savings estimate | MODEL | Savings are estimated from device factors, usage history or measured demand change. | Reports program effectiveness. |
| rebateops.outcomes.baseline | baseline use | MEASUREMENT | Pre-install consumption sets baseline for outcome analysis. | Helps avoid overstated savings. |
| rebateops.outcomes.persistence | persistence | MODEL | Savings may decay if devices fail, landscapes change or behavior reverts. | Long-term value needs monitoring. |
| rebateops.communication.application_help | application help | METHOD | Staff explain eligibility, documents and deadlines before submission. | Improves complete applications. |
| rebateops.communication.status_notice | status notice | METHOD | Notices tell customer received, incomplete, approved, denied or paid status. | Reduces calls and uncertainty. |
| rebateops.communication.water_budget | water budget advice | METHOD | Rebate communication may include efficient-use guidance. | Device incentives pair with behavior change. |
| rebateops.equity.low_income | low-income priority | DECISION_RULE | Program may reserve funds or higher rebates for low-income customers. | Makes conservation accessible. |
| rebateops.equity.multifamily | multifamily handling | METHOD | Multifamily rebates handle owner/tenant roles, unit counts and common areas. | Avoids excluding renters. |
| rebateops.records.document_retention | document retention | RECORD | Applications, receipts, inspections, approvals and payments are retained. | Supports audits and grant reporting. |
| rebateops.records.crm_link | CRM link | RECORD | Rebate case links to account, conservation outreach and complaint records. | Gives full customer context. |
| rebateops.reporting.dashboard | program dashboard | RECORD | Dashboard tracks applications, approvals, payments, budget and estimated savings. | Shows program health. |
| rebateops.reporting.cost_effectiveness | cost effectiveness | MODEL | Cost per saved unit of water compares rebate types. | Guides future funding allocation. |
| rebateops.review.program_tuning | program tuning | METHOD | Review adjusts eligible devices, rebate amounts, outreach and inspection rates. | Keeps conservation spending effective. |

