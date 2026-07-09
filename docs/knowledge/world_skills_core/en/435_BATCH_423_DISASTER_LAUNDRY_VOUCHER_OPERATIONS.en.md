# BATCH 423: Disaster Laundry Voucher Operations

**KnowledgeUnits:** 44  
**Namespace:** `laundryvoucherops.*`  
**Scope:** intake, eligibility, voucher issue, vendor coordination, pickup, reconciliation and fraud controls.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| laundryvoucherops.intake.request_source | request source | RECORD | Source records shelter, hotline, caseworker, outreach, clinic or walk-in request. | Shows entry path. |
| laundryvoucherops.intake.household | household profile | RECORD | Profile captures household size, location, contact, language and laundry barrier. | Sizes support. |
| laundryvoucherops.intake.need_reason | need reason | RECORD | Reason records displacement, flood contamination, utility loss, shelter stay or income shock. | Explains need. |
| laundryvoucherops.intake.urgency | urgency model | MODEL | Urgency weighs hygiene risk, infants, medical needs, work/school clothing and weather. | Prioritizes cases. |
| laundryvoucherops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, service area, household need and frequency limits. | Preserves fairness. |
| laundryvoucherops.eligibility.verification | verification method | METHOD | Verification may use self-attestation, shelter roster, caseworker referral or address impact. | Keeps access workable. |
| laundryvoucherops.eligibility.frequency | frequency limit | CONSTRAINT | Limit defines vouchers per household per period or by load count. | Extends funds. |
| laundryvoucherops.eligibility.exception | exception record | RECORD | Exception records medical, infant, contamination or large household need and approval. | Allows flexibility. |
| laundryvoucherops.voucher.voucher_type | voucher type | RECORD | Type distinguishes laundromat credit, wash/dry card, pickup service or mobile laundry slot. | Defines service. |
| laundryvoucherops.voucher.value | voucher value | MEASUREMENT | Value records amount, loads, expiration and eligible services. | Controls cost. |
| laundryvoucherops.voucher.issue_record | issue record | RECORD | Issue record captures recipient, voucher ID, value, date, staff and restrictions. | Creates audit trail. |
| laundryvoucherops.voucher.expiration | expiration rule | CONSTRAINT | Expiration controls unused voucher liability and reissue timing. | Manages funds. |
| laundryvoucherops.vendor.vendor_roster | vendor roster | RECORD | Roster lists laundromats, mobile laundry, pickup providers, hours and capacity. | Coordinates vendors. |
| laundryvoucherops.vendor.agreement | vendor agreement | RECORD | Agreement defines eligible services, rates, billing, fraud controls and reporting. | Sets terms. |
| laundryvoucherops.vendor.capacity | vendor capacity | MEASUREMENT | Capacity tracks machines, pickup slots, staff, water and power availability. | Avoids overload. |
| laundryvoucherops.vendor.status_update | vendor status update | METHOD | Vendors report closures, queue length, equipment failure and supply shortages. | Keeps referrals current. |
| laundryvoucherops.pickup.pickup_request | pickup request | RECORD | Request records laundry quantity, address, contact, bag count and access constraints. | Starts pickup. |
| laundryvoucherops.pickup.bag_label | bag label | METHOD | Bags are labeled with code, household, count and privacy-safe identifier. | Prevents mixups. |
| laundryvoucherops.pickup.route_plan | route plan | METHOD | Route groups pickups by geography, urgency, bag volume and provider capacity. | Saves time. |
| laundryvoucherops.pickup.no_contact | no-contact handling | METHOD | No-contact rules define retry, hold, cancel or safe pickup alternative. | Controls loss. |
| laundryvoucherops.hygiene.contamination | contamination rule | SAFETY_RULE | Floodwater, mold, chemicals or pest-contaminated items may require special handling or rejection. | Protects workers. |
| laundryvoucherops.hygiene.bagging | bagging guidance | METHOD | Residents receive instructions for bagging, separating and labeling laundry. | Improves processing. |
| laundryvoucherops.hygiene.detergent | detergent need | RECORD | Detergent, hypoallergenic, bleach or sanitizer needs are recorded where service supports them. | Improves fit. |
| laundryvoucherops.hygiene.clean_return | clean return | QUALITY_CHECK | Clean return checks bag count, dryness, obvious mixups and delivery condition. | Protects dignity. |
| laundryvoucherops.fraud.unique_id | unique voucher ID | SAFETY_RULE | Each voucher has non-reusable ID, issue log and redemption record. | Reduces misuse. |
| laundryvoucherops.fraud.duplicate_check | duplicate check | QUALITY_CHECK | Staff compare household, voucher ID, redemption and frequency before new issue. | Prevents double use. |
| laundryvoucherops.fraud.vendor_anomaly | vendor anomaly | QUALITY_CHECK | Anomaly check flags unusual redemptions, repeated voids or inflated load counts. | Detects fraud. |
| laundryvoucherops.fraud.lost_voucher | lost voucher process | METHOD | Lost voucher process voids old ID before reissue where possible. | Controls leakage. |
| laundryvoucherops.reconcile.redemption | redemption record | RECORD | Redemption records voucher ID, vendor, date, amount, service and receipt. | Supports payment. |
| laundryvoucherops.reconcile.invoice | invoice reconciliation | QUALITY_CHECK | Invoice matches vouchers, rates, receipts, voids and approved services. | Prevents overpayment. |
| laundryvoucherops.reconcile.fund_balance | fund balance | MEASUREMENT | Balance tracks issued, redeemed, expired, voided and remaining funds. | Controls budget. |
| laundryvoucherops.reconcile.dispute | dispute record | RECORD | Dispute records rejected charge, duplicate, missing receipt or customer complaint. | Resolves billing. |
| laundryvoucherops.communication.public_notice | public notice | METHOD | Notice states eligibility, locations, voucher limits, pickup option and hygiene rules. | Guides residents. |
| laundryvoucherops.communication.resident_update | resident update | METHOD | Update explains voucher status, pickup time, vendor change or missing laundry issue. | Reduces uncertainty. |
| laundryvoucherops.communication.partner_update | partner update | METHOD | Partners receive capacity, shortages, demand and voucher rules. | Aligns referrals. |
| laundryvoucherops.privacy.minimum_data | minimum data | SAFETY_RULE | Laundry program stores only data needed for voucher and follow-up. | Reduces exposure. |
| laundryvoucherops.records.case_log | case log | RECORD | Log stores intake, eligibility, voucher, pickup, redemption and closeout. | Creates continuity. |
| laundryvoucherops.records.retention | retention rule | CONSTRAINT | Voucher, pickup, redemption and vendor records follow finance and privacy retention schedules. | Preserves audit. |
| laundryvoucherops.metrics.households_served | households served | MEASUREMENT | Count tracks households and people served by area and vendor. | Shows reach. |
| laundryvoucherops.metrics.voucher_use | voucher use rate | MEASUREMENT | Use rate compares issued and redeemed vouchers. | Shows uptake. |
| laundryvoucherops.metrics.cost_per_household | cost per household | MEASUREMENT | Cost metric divides redeemed value by households served. | Supports budgeting. |
| laundryvoucherops.qa.sample_review | sample review | QUALITY_CHECK | Review checks eligibility, issue logs, vendor receipts and fraud controls. | Improves reliability. |
| laundryvoucherops.demob.closeout | closeout | METHOD | Closeout voids unused vouchers, reconciles vendors, archives logs and transfers cases. | Ends operation. |
| laundryvoucherops.review.after_action | after-action review | METHOD | Review captures vendor capacity, fraud controls, pickup issues, dignity and billing lessons. | Improves future laundry support. |
