# BATCH 415: Farm Disaster Assistance Intake Operations

**KnowledgeUnits:** 44  
**Namespace:** `farmassistops.*`  
**Scope:** crop/livestock damage, acreage, insurance, agency referrals, documents and status tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| farmassistops.intake.request_source | request source | RECORD | Source records farmer, extension office, hotline, agency, cooperative or lender referral. | Shows entry path. |
| farmassistops.intake.producer_profile | producer profile | RECORD | Profile captures operator, farm location, contacts, entity type and language. | Defines applicant. |
| farmassistops.intake.operation_type | operation type | RECORD | Type distinguishes crop, livestock, dairy, orchard, nursery, aquaculture or mixed operation. | Routes expertise. |
| farmassistops.intake.urgency | urgency model | MODEL | Urgency weighs animal welfare, planting window, cashflow, perishability and safety risk. | Prioritizes cases. |
| farmassistops.crop.damage_type | crop damage type | RECORD | Type records flood, drought, hail, freeze, wind, smoke, pest or disease impact. | Describes loss. |
| farmassistops.crop.acreage | acreage record | MEASUREMENT | Acreage captures affected acres, planted acres, harvested acres and location. | Quantifies impact. |
| farmassistops.crop.growth_stage | growth stage | RECORD | Stage records planting, emergence, flowering, harvest or storage phase. | Supports loss context. |
| farmassistops.crop.yield_estimate | yield estimate | MEASUREMENT | Estimate compares expected, actual and damaged yield where available. | Supports assistance. |
| farmassistops.livestock.herd_count | herd count | MEASUREMENT | Count records species, class, headcount, losses and at-risk animals. | Quantifies need. |
| farmassistops.livestock.mortality | mortality record | RECORD | Mortality records species, count, cause, date, disposal and evidence. | Supports claims. |
| farmassistops.livestock.welfare | welfare need | SAFETY_RULE | Welfare flags feed, water, shelter, veterinary, transport or carcass disposal need. | Protects animals. |
| farmassistops.livestock.facility_damage | facility damage | RECORD | Damage records barns, fencing, pens, wells, pumps, milking or handling equipment. | Defines repairs. |
| farmassistops.insurance.policy | insurance policy | RECORD | Policy captures carrier, crop/livestock coverage, agent, claim number and deductible. | Coordinates claim. |
| farmassistops.insurance.claim_status | claim status | RECORD | Status records not filed, filed, adjuster visit, paid, denied or appealed. | Tracks path. |
| farmassistops.insurance.agent_contact | agent contact | METHOD | Staff help producer contact agent and gather claim requirements. | Moves claim forward. |
| farmassistops.insurance.duplication | duplication check | QUALITY_CHECK | Check compares insurance, grants, loans, indemnity and donations. | Prevents overlap. |
| farmassistops.documents.farm_id | farm ID | RECORD | Farm, tract, parcel or producer numbers are captured where relevant. | Supports agency lookup. |
| farmassistops.documents.photo_evidence | photo evidence | RECORD | Photos document fields, livestock, facilities, equipment and timestamp context. | Supports proof. |
| farmassistops.documents.production_records | production records | RECORD | Records include planting, sales, milk, herd, feed, tax or inventory documents. | Proves operation. |
| farmassistops.documents.missing_doc | missing document | RECORD | Missing document tracks source, owner, deadline and workaround. | Drives completion. |
| farmassistops.agency.extension_referral | extension referral | METHOD | Extension referral supports assessment, technical advice and program navigation. | Adds expertise. |
| farmassistops.agency.fsa_referral | farm agency referral | METHOD | Farm service referral covers loss notice, program eligibility and appointment needs. | Connects aid. |
| farmassistops.agency.conservation_referral | conservation referral | METHOD | Conservation referral handles erosion, debris, fencing, waterway and soil concerns. | Supports recovery. |
| farmassistops.agency.veterinary_referral | veterinary referral | METHOD | Veterinary referral addresses animal health, mortality, movement or quarantine concerns. | Protects herds. |
| farmassistops.appointment.booking | appointment booking | RECORD | Booking records agency, date, location, documents, language and transport needs. | Secures next step. |
| farmassistops.appointment.reminder | reminder process | METHOD | Reminder includes deadline, documents, location and contact details. | Reduces no-shows. |
| farmassistops.appointment.no_show | no-show handling | METHOD | No-show records reason, reschedule path and deadline risk. | Keeps case active. |
| farmassistops.appointment.deadline | deadline alert | SAFETY_RULE | Program notice and application deadlines are flagged for escalation. | Prevents missed aid. |
| farmassistops.status.case_status | case status | RECORD | Status distinguishes intake, documents, referred, appointment, submitted, approved, denied or closed. | Shows progress. |
| farmassistops.status.followup_queue | follow-up queue | RECORD | Queue tracks open tasks, owner, due date and next contact. | Maintains continuity. |
| farmassistops.status.outcome | outcome record | RECORD | Outcome captures funded, insured, referred, denied, withdrawn, unreachable or unresolved. | Closes loop. |
| farmassistops.status.reopen | reopen rule | METHOD | Case reopens for new loss, denial, missing payment or new program. | Handles change. |
| farmassistops.communication.producer_update | producer update | METHOD | Update explains documents, referrals, deadlines, claim status and next steps. | Reduces uncertainty. |
| farmassistops.communication.partner_update | partner update | METHOD | Partners receive aggregate crop, livestock, document and program barriers. | Coordinates response. |
| farmassistops.communication.language | language support | METHOD | Interpreters or translated agricultural forms support intake and appointments. | Improves access. |
| farmassistops.communication.public_notice | public notice | METHOD | Notice explains intake channels, documents, deadlines and eligible loss categories. | Guides producers. |
| farmassistops.privacy.minimum_data | minimum data | SAFETY_RULE | Intake stores only data needed for farm assistance and referrals. | Reduces exposure. |
| farmassistops.privacy.financial_data | financial data control | SAFETY_RULE | Tax, sales and insurance documents use restricted access and secure storage. | Protects producers. |
| farmassistops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports farms assisted, acres affected, animals affected, referrals and barriers. | Informs recovery. |
| farmassistops.metrics.acres_reported | acres reported | MEASUREMENT | Metric totals damaged acreage by crop, geography and disaster type. | Shows scale. |
| farmassistops.metrics.livestock_reported | livestock reported | MEASUREMENT | Metric totals affected livestock by species and need category. | Guides resources. |
| farmassistops.metrics.time_to_referral | time to referral | MEASUREMENT | Time measures intake to agency referral or appointment. | Reveals delay. |
| farmassistops.qa.case_review | case review | QUALITY_CHECK | Review checks loss records, documents, referrals, deadlines and status notes. | Improves reliability. |
| farmassistops.review.after_action | after-action review | METHOD | Review captures program routing, document gaps, insurance coordination and producer feedback. | Improves future intake. |
