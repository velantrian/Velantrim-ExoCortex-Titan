# BATCH 430: Crisis Fuel Voucher Controls Operations

**KnowledgeUnits:** 44  
**Namespace:** `fuelvoucherops.*`  
**Scope:** eligibility, issue limits, vendor validation, redemption, reconciliation, fraud and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| fuelvoucherops.activation.trigger | activation trigger | MODEL | Trigger includes evacuation, job/medical transport, outage, supply disruption or recovery travel. | Starts fuel aid. |
| fuelvoucherops.activation.program_scope | program scope | CONSTRAINT | Scope defines eligible trips, service area, fuel type and excluded uses. | Controls purpose. |
| fuelvoucherops.activation.funding_source | funding source | RECORD | Source records grant, donation, public fund, restrictions and reporting code. | Supports accounting. |
| fuelvoucherops.activation.command_link | command link | RECORD | Program links finance, logistics, casework, transport and fraud review. | Maintains oversight. |
| fuelvoucherops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, need, trip purpose, vehicle access and frequency. | Preserves fairness. |
| fuelvoucherops.eligibility.trip_purpose | trip purpose | RECORD | Purpose records medical, shelter, work, school, supply pickup, evacuation or caregiving trip. | Justifies voucher. |
| fuelvoucherops.eligibility.vehicle_check | vehicle check | QUALITY_CHECK | Check confirms applicant has vehicle access or authorized driver. | Avoids unusable issue. |
| fuelvoucherops.eligibility.exception | exception record | RECORD | Exception records urgent medical, rural access, disability or family reunification need. | Allows flexibility. |
| fuelvoucherops.limits.value_limit | value limit | MEASUREMENT | Limit records amount per voucher, household, week and funding source. | Controls spending. |
| fuelvoucherops.limits.frequency | frequency limit | CONSTRAINT | Frequency limits repeat vouchers by household, case or trip type. | Extends funds. |
| fuelvoucherops.limits.expiration | expiration rule | CONSTRAINT | Expiration defines use-by date and unused fund release. | Reduces open liability. |
| fuelvoucherops.limits.partial_issue | partial issue | METHOD | Partial issue provides smaller amount when need or funds are limited. | Preserves access. |
| fuelvoucherops.vendor.vendor_roster | vendor roster | RECORD | Roster lists approved fuel stations, contacts, locations, hours and payment methods. | Enables redemption. |
| fuelvoucherops.vendor.validation | vendor validation | QUALITY_CHECK | Validation checks station legitimacy, tax/payment details, fuel availability and agreement. | Prevents fraud. |
| fuelvoucherops.vendor.agreement | vendor agreement | RECORD | Agreement defines eligible purchases, voucher handling, receipts, invoicing and disputes. | Sets rules. |
| fuelvoucherops.vendor.status_update | vendor status update | METHOD | Vendors report closures, fuel shortages, price changes and redemption issues. | Keeps referrals current. |
| fuelvoucherops.issue.unique_id | unique voucher ID | SAFETY_RULE | Each voucher has unique ID, value, expiration, recipient and restrictions. | Prevents reuse. |
| fuelvoucherops.issue.issue_record | issue record | RECORD | Issue captures applicant, purpose, value, vendor option, date and staff. | Creates trail. |
| fuelvoucherops.issue.identity_check | identity check | QUALITY_CHECK | Staff verify recipient according to program policy before issue. | Reduces misuse. |
| fuelvoucherops.issue.lost_voucher | lost voucher process | METHOD | Lost voucher is voided, flagged or replaced according to control rules. | Controls leakage. |
| fuelvoucherops.redemption.receipt | redemption receipt | RECORD | Receipt records voucher ID, vendor, date, amount, gallons and eligible items. | Supports reconciliation. |
| fuelvoucherops.redemption.restriction | purchase restriction | CONSTRAINT | Voucher covers approved fuel or transport use, not unrelated store purchases. | Protects funds. |
| fuelvoucherops.redemption.overage | overage rule | METHOD | Overage explains who pays beyond voucher value and how it is recorded. | Avoids disputes. |
| fuelvoucherops.redemption.void | void record | RECORD | Void records expired, canceled, duplicate, damaged or fraud-suspect voucher. | Maintains control. |
| fuelvoucherops.reconcile.invoice | invoice reconciliation | QUALITY_CHECK | Invoice matches voucher IDs, receipts, rates, vendor agreement and payment request. | Prevents overpayment. |
| fuelvoucherops.reconcile.fund_balance | fund balance | MEASUREMENT | Balance tracks issued, redeemed, voided, expired and remaining funds. | Controls budget. |
| fuelvoucherops.reconcile.exception_review | exception review | QUALITY_CHECK | Review checks high-value, repeat, manual or out-of-area redemptions. | Detects misuse. |
| fuelvoucherops.reconcile.dispute | dispute record | RECORD | Dispute captures duplicate redemption, missing receipt, wrong item or vendor error. | Resolves issue. |
| fuelvoucherops.fraud.duplicate_check | duplicate check | QUALITY_CHECK | Check compares applicant, household, vehicle, purpose and recent issues. | Reduces double dipping. |
| fuelvoucherops.fraud.pattern_alert | pattern alert | MODEL | Alert flags unusual redemption patterns by vendor, staff, household or value. | Finds risk. |
| fuelvoucherops.fraud.staff_separation | duty separation | SAFETY_RULE | Approval, issue and reconciliation roles are separated where possible. | Strengthens controls. |
| fuelvoucherops.fraud.escalation | fraud escalation | METHOD | Suspected fraud routes to supervisor, finance or compliance process. | Protects program. |
| fuelvoucherops.communication.recipient_script | recipient script | METHOD | Script explains eligible use, expiration, vendor, receipt and replacement rules. | Reduces confusion. |
| fuelvoucherops.communication.vendor_script | vendor script | METHOD | Script explains how vendor validates, redeems, documents and invoices voucher. | Standardizes redemption. |
| fuelvoucherops.communication.partner_update | partner update | METHOD | Partners receive eligibility, limits, available vendors and funding status. | Aligns referrals. |
| fuelvoucherops.records.case_log | case log | RECORD | Log stores eligibility, issue, redemption, exception, dispute and closeout. | Creates continuity. |
| fuelvoucherops.records.retention | retention rule | CONSTRAINT | Voucher, vendor, finance and fraud records follow retention schedules. | Preserves audit. |
| fuelvoucherops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports vouchers issued, redeemed, voided, funds remaining and exceptions. | Informs managers. |
| fuelvoucherops.metrics.redemption_rate | redemption rate | MEASUREMENT | Rate compares issued and redeemed vouchers by period and vendor. | Shows uptake. |
| fuelvoucherops.metrics.cost_per_trip | cost per trip | MEASUREMENT | Cost metric links redeemed value to supported trip purpose. | Supports budgeting. |
| fuelvoucherops.metrics.fraud_flags | fraud flags | MEASUREMENT | Count tracks suspected fraud or control exceptions by category. | Guides review. |
| fuelvoucherops.qa.sample_audit | sample audit | QUALITY_CHECK | Audit samples eligibility, voucher issue, vendor receipt and reconciliation. | Improves reliability. |
| fuelvoucherops.demob.closeout | closeout | METHOD | Closeout voids unused vouchers, reconciles vendors, archives logs and releases funds. | Ends safely. |
| fuelvoucherops.review.after_action | after-action review | METHOD | Review captures eligibility, vendor controls, fraud patterns, reconciliation and reporting lessons. | Improves future vouchers. |
