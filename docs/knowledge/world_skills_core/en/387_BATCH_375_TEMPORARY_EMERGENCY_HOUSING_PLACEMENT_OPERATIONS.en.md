# BATCH 375: Temporary Emergency Housing Placement Operations

**KnowledgeUnits:** 44  
**Namespace:** `temphousingops.*`  
**Scope:** eligibility, unit matching, inspections, leases, case support, payments and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| temphousingops.intake.placement_id | placement ID | RECORD | Placement ID links household, disaster, referral, unit, dates and status. | Tracks temporary housing lifecycle. |
| temphousingops.intake.household_profile | household profile | RECORD | Profile records members, pets, accessibility, location preference and contact. | Supports unit matching. |
| temphousingops.intake.displacement_reason | displacement reason | RECORD | Reason distinguishes destroyed home, unsafe access, utility outage, evacuation or health order. | Clarifies eligibility. |
| temphousingops.intake.priority | priority level | MODEL | Priority considers homelessness, disability, children, medical need and unsafe shelter stay. | Allocates scarce units. |
| temphousingops.eligibility.disaster_link | disaster link | CONSTRAINT | Household must connect to eligible incident or program rule. | Keeps program in scope. |
| temphousingops.eligibility.identity | identity verification | SAFETY_RULE | Applicant identity and household authority are checked before placement. | Prevents fraud and unsafe release. |
| temphousingops.eligibility.duplication | duplication check | QUALITY_CHECK | Check compares shelter, hotel, rental aid, insurance and other assistance. | Avoids duplicate benefits. |
| temphousingops.eligibility.income_rule | income or need rule | CONSTRAINT | Some programs require income, uninsured loss, or unmet need criteria. | Applies funding rules. |
| temphousingops.unit.inventory | unit inventory | RECORD | Inventory lists hotels, rentals, trailers, dorms or host sites with availability. | Makes options visible. |
| temphousingops.unit.accessibility | accessibility feature | RECORD | Features include ramps, roll-in shower, elevator, power, service animals and proximity. | Matches functional needs. |
| temphousingops.unit.pet_policy | pet policy | CONSTRAINT | Unit pet rules affect placement and animal shelter coordination. | Prevents failed move-ins. |
| temphousingops.unit.suitability | suitability check | QUALITY_CHECK | Unit is checked for safety, utilities, habitability and household fit. | Avoids unsafe placement. |
| temphousingops.matching.match_rule | match rule | METHOD | Matching uses priority, household size, accessibility, pets, school/work and availability. | Places households fairly. |
| temphousingops.matching.waitlist | waitlist | RECORD | Waitlist records priority, eligible date, preferences and contact attempts. | Manages scarcity. |
| temphousingops.matching.offer | placement offer | METHOD | Offer states unit, rules, costs covered, move-in date and response deadline. | Lets household decide. |
| temphousingops.matching.decline | decline record | RECORD | Decline records reason and whether household remains eligible. | Keeps queue accurate. |
| temphousingops.inspection.preoccupancy | pre-occupancy inspection | QUALITY_CHECK | Inspection checks safety, sanitation, utilities, locks and damage. | Protects residents and program. |
| temphousingops.inspection.photo | inspection photos | RECORD | Photos document condition before move-in. | Reduces damage disputes. |
| temphousingops.inspection.defect | defect log | RECORD | Defects are logged, assigned and resolved before or during occupancy. | Maintains habitability. |
| temphousingops.inspection.reinspection | reinspection | METHOD | Reinspection confirms repairs or recurring concerns. | Keeps units safe. |
| temphousingops.agreement.occupancy | occupancy agreement | RECORD | Agreement states dates, rules, covered costs, responsibilities and termination. | Defines placement terms. |
| temphousingops.agreement.lease | lease or contract | RECORD | Lease links owner, agency, unit, rent, deposits and service period. | Controls payments. |
| temphousingops.agreement.rules | resident rules | CONSTRAINT | Rules cover guests, pets, damage, conduct, utilities and reporting changes. | Prevents misunderstandings. |
| temphousingops.agreement.extension | extension process | METHOD | Extension checks continued need, unit availability, funding and compliance. | Manages temporary duration. |
| temphousingops.case.support_plan | support plan | RECORD | Plan lists recovery tasks, documents, benefits, repairs and move-out target. | Moves household toward stability. |
| temphousingops.case.checkin | resident check-in | METHOD | Check-ins monitor safety, needs, complaints, eligibility and next steps. | Prevents abandonment. |
| temphousingops.case.referral | service referral | METHOD | Referrals connect to benefits, legal aid, repairs, health, transport or school support. | Addresses barriers. |
| temphousingops.case.noncompliance | noncompliance response | METHOD | Issues are handled with notice, support, correction and escalation before termination. | Balances rules and recovery. |
| temphousingops.payments.rent | rent payment | RECORD | Rent payment records amount, period, vendor, funding source and approval. | Controls public funds. |
| temphousingops.payments.deposit | deposit handling | CONSTRAINT | Deposits and damages follow contract and funding rules. | Reduces finance disputes. |
| temphousingops.payments.invoice_review | invoice review | QUALITY_CHECK | Invoices are checked against occupancy, rate, dates and contract. | Prevents overpayment. |
| temphousingops.payments.exception | payment exception | RECORD | Exceptions capture late invoice, disputed charge, damage or duplicate claim. | Keeps issues visible. |
| temphousingops.communication.movein | move-in instructions | METHOD | Instructions include address, time, keys, rules, contact and required items. | Supports smooth placement. |
| temphousingops.communication.landlord | landlord communication | METHOD | Landlord receives approved household status, payment path and maintenance contact. | Aligns property owner. |
| temphousingops.communication.language | language support | METHOD | Placement documents and calls use preferred language where possible. | Improves access. |
| temphousingops.communication.notice | notice process | METHOD | Notices cover extension, termination, move-out, rule issues and program changes. | Protects due process. |
| temphousingops.records.case_file | case file | RECORD | File stores eligibility, match, inspection, agreement, payments and communications. | Creates audit trail. |
| temphousingops.records.privacy | privacy rule | SAFETY_RULE | Household location and personal data are protected by role and need. | Protects survivors. |
| temphousingops.records.retention | retention rule | CONSTRAINT | Records follow disaster, housing, finance and privacy schedules. | Supports audits. |
| temphousingops.metrics.occupancy | occupancy metric | MEASUREMENT | Occupancy tracks occupied, vacant, unavailable and ending units. | Shows housing capacity. |
| temphousingops.metrics.length_stay | length of stay | MEASUREMENT | Length of stay measures placement duration by household and program. | Guides recovery planning. |
| temphousingops.qa.case_audit | case audit | QUALITY_CHECK | Audit checks eligibility, inspections, payments, notices and closure. | Improves integrity. |
| temphousingops.closeout.moveout | move-out closeout | METHOD | Move-out confirms destination, keys, condition, final payment and referrals. | Ends placement cleanly. |
| temphousingops.review.lessons | lessons learned | METHOD | Review captures bottlenecks, unit gaps, equity and vendor issues. | Improves future housing response. |
