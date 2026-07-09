# BATCH 372: Disaster Shelter Medical Desk Operations

**KnowledgeUnits:** 44  
**Namespace:** `sheltermedops.*`  
**Scope:** intake, triage, medication support, referrals, infection control, privacy and documentation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| sheltermedops.setup.medical_desk | medical desk setup | METHOD | Desk is placed for privacy, access, visibility and emergency exit. | Creates safe care point. |
| sheltermedops.setup.role_roster | role roster | RECORD | Roster lists nurses, EMTs, public health, mental health and support roles. | Clarifies staffing. |
| sheltermedops.setup.scope | scope boundary | CONSTRAINT | Shelter medical desk provides basic assessment, support and referral, not full clinic care. | Prevents false capability. |
| sheltermedops.setup.supplies | medical supplies | RECORD | Supplies include gloves, masks, first aid, forms, sanitizer, BP cuff and thermometer. | Supports basic work. |
| sheltermedops.intake.visit_id | visit ID | RECORD | Visit ID links resident, complaint, time, staff and disposition. | Tracks medical encounters. |
| sheltermedops.intake.identity | resident match | METHOD | Resident is matched to registration or temporary ID. | Connects care to shelter record. |
| sheltermedops.intake.complaint | chief concern | RECORD | Concern is recorded in resident words with onset and severity. | Guides triage. |
| sheltermedops.intake.consent | consent context | METHOD | Staff explain limits, privacy and referral choices. | Builds trust. |
| sheltermedops.triage.acuity | acuity level | MODEL | Acuity ranks emergency, urgent, routine, wellness or information-only. | Prioritizes care. |
| sheltermedops.triage.red_flags | red flags | SAFETY_RULE | Chest pain, stroke signs, severe breathing, trauma or overdose trigger EMS. | Protects life safety. |
| sheltermedops.triage.vulnerable | vulnerable resident | MODEL | Age, pregnancy, disability, oxygen, dialysis or dependence increases priority. | Supports high-risk residents. |
| sheltermedops.triage.repeat_visit | repeat visit | QUALITY_CHECK | Repeat visits for same issue prompt review or referral. | Avoids missed deterioration. |
| sheltermedops.medication.med_list | medication list | RECORD | Medication list records resident-reported meds, storage needs and gaps. | Supports continuity. |
| sheltermedops.medication.no_dosing | no dosing boundary | SAFETY_RULE | Staff do not improvise dosing outside credentialed scope and orders. | Prevents unsafe care. |
| sheltermedops.medication.refrigeration | refrigeration support | METHOD | Refrigerated medications use labeled storage and access log. | Preserves medication. |
| sheltermedops.medication.refill_help | refill help | METHOD | Staff help contact pharmacy, prescriber or assistance program. | Reduces interruption. |
| sheltermedops.referral.ems | EMS referral | SAFETY_RULE | EMS referral is used for emergency symptoms or unsafe transport need. | Escalates appropriately. |
| sheltermedops.referral.clinic | clinic referral | METHOD | Clinic referral gives location, hours, eligibility and transport path. | Connects routine care. |
| sheltermedops.referral.behavioral | behavioral referral | METHOD | Distress, anxiety, grief or crisis routes to mental health support. | Supports shelter wellbeing. |
| sheltermedops.referral.public_health | public health referral | METHOD | Communicable disease, exposure or outbreak concern routes to public health. | Protects shelter population. |
| sheltermedops.infection.symptom_screen | symptom screen | METHOD | Screen checks fever, cough, GI symptoms, rash or exposure as relevant. | Detects infection risk. |
| sheltermedops.infection.isolation | isolation referral | SAFETY_RULE | Symptomatic residents may be moved to isolation area or alternate site. | Reduces spread. |
| sheltermedops.infection.hand_hygiene | hand hygiene | METHOD | Desk promotes hand hygiene, masks and cleaning. | Lowers transmission. |
| sheltermedops.infection.line_list | illness line list | RECORD | Line list tracks symptoms, onset, location and action. | Supports outbreak investigation. |
| sheltermedops.accessibility.functional_needs | functional needs | RECORD | Needs include mobility, oxygen, devices, communication, vision/hearing and caregiver. | Guides shelter support. |
| sheltermedops.accessibility.device_power | device power | METHOD | Power needs for CPAP, oxygen concentrator or wheelchair are logged. | Prevents device failure. |
| sheltermedops.accessibility.diet | medical diet | METHOD | Medical diet requests coordinate with food service when possible. | Supports chronic conditions. |
| sheltermedops.accessibility.transport | medical transport | METHOD | Transport support arranges nonemergency or emergency movement based on acuity. | Reduces access barriers. |
| sheltermedops.privacy.private_space | private space | SAFETY_RULE | Medical conversations avoid public disclosure in shelter areas. | Protects dignity. |
| sheltermedops.privacy.record_access | record access | CONSTRAINT | Only authorized health/shelter staff access medical notes. | Limits sensitive data. |
| sheltermedops.privacy.minimum | minimum necessary | SAFETY_RULE | Shelter operations receive only support needs, not full diagnoses, unless needed. | Balances care and privacy. |
| sheltermedops.documentation.note | encounter note | RECORD | Note records concern, assessment, action, referral and follow-up. | Creates continuity. |
| sheltermedops.documentation.incident | medical incident | RECORD | Incidents capture injury, EMS, medication loss, exposure or adverse event. | Supports review. |
| sheltermedops.documentation.handoff | handoff note | METHOD | Shift handoff lists pending referrals, high-risk residents and infection concerns. | Maintains continuity. |
| sheltermedops.documentation.retention | retention rule | CONSTRAINT | Medical desk records follow health, emergency and privacy retention rules. | Controls lifecycle. |
| sheltermedops.supplies.inventory | supply inventory | MEASUREMENT | Inventory tracks first aid, PPE, forms and special items. | Prevents shortages. |
| sheltermedops.supplies.reorder | reorder trigger | MODEL | Reorder uses burn rate, census, illness activity and delivery time. | Maintains readiness. |
| sheltermedops.supplies.sharps | sharps control | SAFETY_RULE | Sharps containers and needlestick protocol are available where injections/testing occur. | Protects staff/residents. |
| sheltermedops.metrics.visit_volume | visit volume | MEASUREMENT | Visits are counted by issue, acuity, referral and time. | Shows medical demand. |
| sheltermedops.metrics.ems_rate | EMS transfer rate | MEASUREMENT | EMS rate tracks emergency transfers from shelter. | Signals acuity pressure. |
| sheltermedops.qa.chart_review | chart review | QUALITY_CHECK | Sample notes check privacy, triage, referrals and follow-up. | Improves quality. |
| sheltermedops.demob.closeout | desk closeout | METHOD | Closeout secures records, returns supplies and transfers open follow-ups. | Ends desk safely. |
| sheltermedops.demob.resident_handoff | resident handoff | RECORD | High-need residents are handed off to clinic, shelter manager or caseworker before desk closure. | Prevents care gaps. |
| sheltermedops.review.after_action | after-action review | METHOD | Review captures illness trends, supply gaps, privacy issues and staffing needs. | Improves shelter medical support. |
