# BATCH 427: Disaster Mobile Shower Voucher Operations

**KnowledgeUnits:** 44  
**Namespace:** `showervoucherops.*`  
**Scope:** intake, eligibility, vendor coordination, scheduling, redemption, accessibility and reconciliation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| showervoucherops.intake.request_source | request source | RECORD | Source records shelter, outreach, hotline, caseworker, clinic or walk-in. | Shows entry path. |
| showervoucherops.intake.household | household profile | RECORD | Profile captures people, location, contact, language and shower barrier. | Defines demand. |
| showervoucherops.intake.need_reason | need reason | RECORD | Reason records displacement, utility outage, flooding, shelter crowding or hygiene risk. | Explains support. |
| showervoucherops.intake.urgency | urgency model | MODEL | Urgency weighs health risk, work/school need, caregiving, heat and days without shower. | Prioritizes slots. |
| showervoucherops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, location, frequency and referral requirements. | Preserves fairness. |
| showervoucherops.eligibility.verification | verification method | METHOD | Verification uses self-attestation, shelter roster, referral or affected-address check. | Keeps access workable. |
| showervoucherops.eligibility.frequency | frequency limit | CONSTRAINT | Frequency limit defines uses per person or household per period. | Extends capacity. |
| showervoucherops.eligibility.exception | exception record | RECORD | Exception records medical, occupational, disability or caregiver need and approval. | Allows flexibility. |
| showervoucherops.vendor.vendor_roster | vendor roster | RECORD | Roster lists mobile shower providers, gyms, pools, hotels and community sites. | Coordinates capacity. |
| showervoucherops.vendor.agreement | vendor agreement | RECORD | Agreement defines eligible service, rate, hours, privacy, cleaning and billing. | Sets terms. |
| showervoucherops.vendor.capacity | capacity status | MEASUREMENT | Capacity tracks stalls, hours, water, wastewater, staff and accessible units. | Avoids overbooking. |
| showervoucherops.vendor.status_update | status update | METHOD | Vendors report closures, queue, water limits, sanitation issues and available slots. | Keeps schedule current. |
| showervoucherops.schedule.slot_request | slot request | RECORD | Request records preferred time, site, household size, accessibility and transport need. | Starts scheduling. |
| showervoucherops.schedule.booking | booking record | RECORD | Booking stores voucher ID, time, site, person count, confirmation and restrictions. | Creates appointment. |
| showervoucherops.schedule.reminder | reminder process | METHOD | Reminder gives time, location, documents, towel/toiletry note and cancellation rule. | Reduces no-shows. |
| showervoucherops.schedule.no_show | no-show handling | METHOD | No-show records reason, rebooking rule and unused slot recovery. | Protects capacity. |
| showervoucherops.voucher.voucher_id | voucher ID | SAFETY_RULE | Unique voucher ID links issue, booking, redemption and billing. | Reduces misuse. |
| showervoucherops.voucher.issue_record | issue record | RECORD | Issue record captures recipient, value, date, site, staff and expiration. | Creates audit trail. |
| showervoucherops.voucher.transfer_rule | transfer rule | CONSTRAINT | Transfer limits define whether another household member may use the voucher. | Controls fairness. |
| showervoucherops.voucher.lost_voucher | lost voucher | METHOD | Lost voucher is voided or flagged before reissue where possible. | Prevents double use. |
| showervoucherops.accessibility.accessible_slot | accessible slot | RECORD | Slot records wheelchair access, caregiver, service animal, privacy or extra time need. | Improves inclusion. |
| showervoucherops.accessibility.transport | transport link | METHOD | Transport referral supports people unable to reach shower site. | Restores access. |
| showervoucherops.accessibility.language | language support | METHOD | Shower-site instructions translate voucher use, privacy rules, time slots and hygiene steps. | Improves comprehension. |
| showervoucherops.accessibility.dignity | dignity practice | SAFETY_RULE | Staff protect privacy around hygiene needs, gender concerns and disability support. | Preserves dignity. |
| showervoucherops.safety.site_sanitation | site sanitation | QUALITY_CHECK | Site checks cleaning, drainage, waste, slip hazards and supplies. | Protects users. |
| showervoucherops.safety.water_temp | water temperature | SAFETY_RULE | Water temperature and anti-scald controls are checked where feasible. | Prevents burns. |
| showervoucherops.safety.security | security rule | SAFETY_RULE | Site uses supervision, lighting, complaint route and separation from unsafe areas. | Protects users. |
| showervoucherops.safety.incident | incident report | RECORD | Incident records injury, harassment, lost item, sanitation failure or conflict. | Supports review. |
| showervoucherops.redemption.redemption_log | redemption log | RECORD | Log captures voucher ID, vendor, date, service count and staff confirmation. | Supports payment. |
| showervoucherops.redemption.void | void record | RECORD | Void records expired, duplicate, lost, unused or canceled voucher. | Controls funds. |
| showervoucherops.redemption.dispute | dispute record | RECORD | Dispute captures rejected charge, user complaint, duplicate redemption or vendor error. | Resolves billing. |
| showervoucherops.reconcile.invoice_packet | invoice packet | RECORD | Packet groups vendor invoice, redemption list, voids, disputes and approval note. | Supports payment. |
| showervoucherops.reconcile.invoice | invoice reconciliation | QUALITY_CHECK | Invoice matches redemption logs, rates, voids and vendor agreement. | Prevents overpayment. |
| showervoucherops.reconcile.fund_balance | fund balance | MEASUREMENT | Balance tracks issued, redeemed, voided, expired and remaining voucher funds. | Controls budget. |
| showervoucherops.communication.public_notice | public notice | METHOD | Notice states eligibility, sites, hours, limits, accessibility and hygiene rules. | Guides residents. |
| showervoucherops.communication.partner_update | partner update | METHOD | Partners receive capacity, schedule, transport gaps and voucher rules. | Aligns referrals. |
| showervoucherops.records.case_log | case log | RECORD | Log stores intake, eligibility, scheduling, voucher, redemption and closeout. | Creates continuity. |
| showervoucherops.records.retention | retention rule | CONSTRAINT | Voucher, vendor, incident and finance records follow retention schedules. | Preserves audit. |
| showervoucherops.metrics.people_served | people served | MEASUREMENT | Count tracks people served by site, day and accessibility need. | Shows reach. |
| showervoucherops.metrics.no_show_rate | no-show rate | MEASUREMENT | Rate tracks no-shows by site, time and reminder method. | Improves scheduling. |
| showervoucherops.metrics.cost_per_use | cost per use | MEASUREMENT | Cost per use compares redeemed value with completed showers. | Supports budgeting. |
| showervoucherops.qa.sample_review | sample review | QUALITY_CHECK | Review checks eligibility, issue, redemption, invoice and complaint records. | Improves reliability. |
| showervoucherops.demob.closeout | closeout | METHOD | Closeout voids unused vouchers, reconciles vendors and transfers unresolved cases. | Ends operation. |
| showervoucherops.review.after_action | after-action review | METHOD | Review captures capacity, accessibility, dignity, sanitation, no-shows and billing lessons. | Improves future showers. |
