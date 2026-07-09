# BATCH 398: Post-Disaster Mold Remediation Referral Operations

**KnowledgeUnits:** 44  
**Namespace:** `moldreferralops.*`  
**Scope:** intake, safety screening, contractor referral, supplies, education and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| moldreferralops.intake.request_source | request source | RECORD | Source records resident, hotline, caseworker, inspector, health provider or community group. | Shows entry path. |
| moldreferralops.intake.property_info | property information | RECORD | Property record captures address, occupancy, ownership, flood depth, materials and access. | Defines work context. |
| moldreferralops.intake.household_risk | household risk | RECORD | Risk notes asthma, immune concerns, age, disability and displacement status. | Prioritizes support. |
| moldreferralops.intake.consent | consent record | RECORD | Consent documents permission to share property details with referral partners. | Enables referral. |
| moldreferralops.screening.visible_mold | visible mold screen | QUALITY_CHECK | Screen records visible growth, odor, moisture, affected rooms and photos if allowed. | Estimates severity. |
| moldreferralops.screening.moisture_source | moisture source | MODEL | Source distinguishes floodwater, roof leak, plumbing leak, humidity or HVAC problem. | Guides remediation. |
| moldreferralops.screening.structural_risk | structural risk | SAFETY_RULE | Structural damage or unsafe utilities route to building safety before cleanup. | Prevents injury. |
| moldreferralops.screening.medical_risk | medical risk | SAFETY_RULE | Health symptoms or high-risk occupants are referred to medical/public health guidance. | Protects residents. |
| moldreferralops.priority.priority_score | priority score | MODEL | Score weighs occupancy, vulnerable residents, severity, recurrence and lack of resources. | Orders referrals. |
| moldreferralops.priority.habitability | habitability flag | CONSTRAINT | Habitability flag identifies homes unsuitable for occupancy pending repair or inspection. | Supports sheltering decisions. |
| moldreferralops.priority.self_help_fit | self-help suitability | MODEL | Suitability considers area size, materials, PPE access, resident capacity and hazards. | Selects pathway. |
| moldreferralops.priority.urgent_escalation | urgent escalation | METHOD | Urgent cases route to housing, health, code enforcement or emergency repair pathways. | Speeds critical help. |
| moldreferralops.referral.contractor_roster | contractor roster | RECORD | Roster lists vetted contractors, nonprofits, capabilities, insurance, licenses and service area. | Matches providers. |
| moldreferralops.referral.matching_rule | matching rule | METHOD | Matching considers severity, funding, language, availability, accessibility and conflict checks. | Improves fit. |
| moldreferralops.referral.warm_handoff | warm handoff | METHOD | Warm handoff confirms resident contact, scope summary and next appointment. | Reduces drop-off. |
| moldreferralops.referral.decline_reason | decline reason | RECORD | Declines record capacity, eligibility, unsafe site, cost or resident refusal. | Shows barriers. |
| moldreferralops.supplies.ppe_kit | PPE kit | SAFETY_RULE | PPE kit may include gloves, eye protection, respirator guidance and disposable coveralls. | Reduces exposure. |
| moldreferralops.supplies.cleaning_kit | cleaning kit | RECORD | Cleaning kit lists bags, detergent, brushes, disinfectant, towels and instructions. | Supports self-help. |
| moldreferralops.supplies.dehumidifier | drying equipment | RECORD | Drying equipment records dehumidifier, fan, moisture meter or rental referral. | Helps moisture control. |
| moldreferralops.supplies.issue_log | supply issue log | RECORD | Issue log stores household, kit contents, date, staff and safety instruction confirmation. | Tracks distribution. |
| moldreferralops.education.safe_work | safe work education | METHOD | Education covers ventilation, PPE, containment, wet material removal and stop-work triggers. | Prevents risky cleanup. |
| moldreferralops.education.disposal | disposal guidance | METHOD | Guidance explains bagging, debris pickup rules, contaminated materials and local disposal options. | Keeps cleanup compliant. |
| moldreferralops.education.moisture_control | moisture control | METHOD | Education stresses drying, fixing leaks and monitoring humidity after cleanup. | Prevents recurrence. |
| moldreferralops.education.scam_warning | scam warning | METHOD | Warning explains red flags for predatory contractors and payment pressure. | Protects residents. |
| moldreferralops.finance.assistance_check | assistance check | METHOD | Check links household to grants, insurance, nonprofit repair funds or case management. | Finds payment path. |
| moldreferralops.finance.estimate_record | estimate record | RECORD | Estimate records scope, price, assumptions, exclusions and funding status. | Supports decisions. |
| moldreferralops.finance.insurance_note | insurance note | RECORD | Insurance note tracks claim status, adjuster contact and documentation needs. | Coordinates funding. |
| moldreferralops.finance.no_cost_path | no-cost path | CONSTRAINT | No-cost pathway uses volunteer, nonprofit or public assistance resources where eligible. | Helps low-resource homes. |
| moldreferralops.records.case_log | case log | RECORD | Case log stores intake, screening, referrals, supplies, education and closeout. | Creates continuity. |
| moldreferralops.records.photo_control | photo control | SAFETY_RULE | Photos follow consent, privacy, metadata and storage rules. | Protects households. |
| moldreferralops.records.document_packet | document packet | RECORD | Packet includes instructions, referrals, estimates, receipts and follow-up notes. | Organizes case. |
| moldreferralops.records.retention | retention rule | CONSTRAINT | Records follow housing, health, grant, privacy and public records requirements. | Preserves audit. |
| moldreferralops.followup.appointment_check | appointment check | METHOD | Follow-up confirms contractor contact, scheduled visit, no-show or resident cancellation. | Keeps referral alive. |
| moldreferralops.followup.work_started | work started | RECORD | Work-start record captures provider, date, scope and resident concerns. | Tracks progress. |
| moldreferralops.followup.work_complete | work complete | QUALITY_CHECK | Completion verifies cleanup done, moisture source addressed or next repair step identified. | Supports closeout. |
| moldreferralops.followup.recurrence | recurrence report | RECORD | Recurrence report captures new growth, moisture return or failed repair. | Reopens support. |
| moldreferralops.communication.public_info | public information | METHOD | Public messaging explains mold risks, referral channels, eligibility and documentation. | Guides community. |
| moldreferralops.communication.language | language access | METHOD | Materials and calls use common languages and plain housing terms. | Improves access. |
| moldreferralops.communication.partner_update | partner update | METHOD | Partners receive demand, backlog, supply needs, contractor capacity and barriers. | Coordinates response. |
| moldreferralops.communication.caseworker_note | caseworker note | RECORD | Caseworker note summarizes status and next step for recovery coordination. | Aligns support. |
| moldreferralops.metrics.referral_completion | referral completion | MEASUREMENT | Metric tracks referred, contacted, accepted, completed and unresolved cases. | Measures throughput. |
| moldreferralops.metrics.supply_usage | supply usage | MEASUREMENT | Supply usage counts PPE, cleaning kits and drying equipment issued. | Guides restock. |
| moldreferralops.metrics.backlog_age | backlog age | MEASUREMENT | Backlog age measures open cases by priority and days waiting. | Reveals bottlenecks. |
| moldreferralops.review.after_action | after-action review | METHOD | Review captures screening, safety, contractor capacity, education and funding lessons. | Improves future referrals. |
