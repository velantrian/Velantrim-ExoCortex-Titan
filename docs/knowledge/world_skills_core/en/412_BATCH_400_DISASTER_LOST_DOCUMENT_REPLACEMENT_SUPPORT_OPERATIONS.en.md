# BATCH 400: Disaster Lost Document Replacement Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `lostdocops.*`  
**Scope:** intake, identity proof, agency referrals, fee waivers, appointments and status tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| lostdocops.intake.request_source | request source | RECORD | Source records survivor center, hotline, shelter, caseworker, legal aid or outreach entry. | Shows referral path. |
| lostdocops.intake.document_type | document type | RECORD | Type distinguishes ID, birth record, title, deed, benefits card, immigration document or school record. | Routes request. |
| lostdocops.intake.loss_cause | loss cause | RECORD | Loss cause records fire, flood, evacuation, theft, displacement or inaccessible property. | Supports waiver. |
| lostdocops.intake.urgency | urgency level | MODEL | Urgency weighs shelter access, benefits, employment, travel, medical care and legal deadlines. | Prioritizes help. |
| lostdocops.identity.primary_proof | primary proof | RECORD | Primary proof captures available government ID, passport, license or certified record. | Supports replacement. |
| lostdocops.identity.secondary_proof | secondary proof | RECORD | Secondary proof uses bills, school records, employer letters, medical records or affidavits. | Helps no-ID cases. |
| lostdocops.identity.affidavit | affidavit pathway | METHOD | Affidavit pathway documents witness, notary, relationship and limits. | Handles missing proof. |
| lostdocops.identity.name_variation | name variation | RECORD | Name variation records former names, transliteration, marriage name and spelling differences. | Reduces rejections. |
| lostdocops.agency.directory | agency directory | RECORD | Directory lists issuing agencies, forms, hours, fees, contacts and disaster procedures. | Guides staff. |
| lostdocops.agency.vital_records | vital records referral | METHOD | Vital records path covers birth, death, marriage and divorce record replacement. | Restores core documents. |
| lostdocops.agency.motor_vehicle | motor vehicle referral | METHOD | Motor vehicle path covers license, vehicle title, registration and disability placard. | Restores mobility/legal status. |
| lostdocops.agency.benefits_card | benefits card referral | METHOD | Benefits path covers SNAP, Medicaid, social security, unemployment or local assistance cards. | Restores aid access. |
| lostdocops.forms.form_packet | form packet | RECORD | Packet includes correct forms, instructions, required proof, fees and mailing/upload options. | Reduces errors. |
| lostdocops.forms.prefill | prefill support | METHOD | Staff help prefill non-sensitive fields while resident confirms accuracy. | Speeds applications. |
| lostdocops.forms.translation | translation need | METHOD | Translation support identifies language, interpreter and document translation requirements. | Improves acceptance. |
| lostdocops.forms.signature | signature control | SAFETY_RULE | Applicants sign their own forms unless legal representative authority is documented. | Prevents fraud. |
| lostdocops.fees.waiver_eligibility | fee waiver eligibility | MODEL | Eligibility checks disaster declaration, income, agency policy and document type. | Reduces cost. |
| lostdocops.fees.waiver_form | waiver form | RECORD | Waiver form records basis, supporting proof, agency and submission date. | Documents relief. |
| lostdocops.fees.payment_assist | payment assistance | METHOD | Payment support routes to nonprofit funds, vouchers or case management where allowed. | Helps low-resource residents. |
| lostdocops.fees.receipt | fee receipt | RECORD | Receipt stores amount, payer, document type, agency and reimbursement status. | Supports audit. |
| lostdocops.appointments.slot_search | appointment search | METHOD | Staff search agency slots by location, accessibility, urgency and document requirements. | Gets service time. |
| lostdocops.appointments.booking | booking record | RECORD | Booking records date, agency, confirmation, documents needed and transport needs. | Tracks next step. |
| lostdocops.appointments.reminder | reminder process | METHOD | Reminders use preferred contact, language, time and backup contact. | Reduces no-shows. |
| lostdocops.appointments.no_show | no-show handling | METHOD | No-show handling records reason, reschedule need and barrier. | Keeps case active. |
| lostdocops.status.case_status | case status | RECORD | Status distinguishes intake, proof gathering, submitted, appointment booked, issued, denied or closed. | Shows progress. |
| lostdocops.status.submission_proof | submission proof | RECORD | Proof includes receipt, tracking number, upload confirmation or agency note. | Verifies action. |
| lostdocops.status.denial_reason | denial reason | RECORD | Denial records missing proof, mismatch, fee issue, ineligible document or agency hold. | Guides correction. |
| lostdocops.status.reopen | reopen rule | METHOD | Case reopens when denial, lost mail, new proof or urgent need appears. | Prevents dead ends. |
| lostdocops.privacy.data_minimum | data minimum | SAFETY_RULE | Staff avoid storing full IDs, images or sensitive numbers unless required and protected. | Reduces exposure. |
| lostdocops.privacy.secure_copy | secure copy | SAFETY_RULE | Copies are encrypted, locked, redacted or returned according to policy. | Protects identity. |
| lostdocops.privacy.authorized_release | authorized release | RECORD | Release records permission to speak with agency, legal aid or caseworker. | Enables follow-up. |
| lostdocops.privacy.fraud_flag | fraud flag | RECORD | Fraud concerns are recorded and escalated without blocking legitimate aid unfairly. | Balances safety. |
| lostdocops.communication.script | resident script | METHOD | Script explains steps, proof options, expected time, costs and limits. | Sets expectations. |
| lostdocops.communication.partner_update | partner update | METHOD | Partners receive aggregate demand, barriers, agency delays and fee-waiver needs. | Coordinates support. |
| lostdocops.communication.accessibility | accessibility support | METHOD | Support covers mobility, language, internet access, phone access and cognitive assistance. | Improves equity. |
| lostdocops.communication.deadline_alert | deadline alert | METHOD | Alerts flag court, benefits, school, employment or housing deadlines tied to documents. | Prevents harm. |
| lostdocops.records.case_log | case log | RECORD | Log stores request, proof, forms, appointments, submissions, outcomes and referrals. | Creates continuity. |
| lostdocops.records.document_checklist | document checklist | RECORD | Checklist tracks which proof and forms are ready, missing or not applicable. | Organizes work. |
| lostdocops.records.audit_note | audit note | RECORD | Audit note explains fee support, waiver basis, staff action and resident consent. | Supports review. |
| lostdocops.records.retention | retention rule | CONSTRAINT | Records follow privacy, legal aid, emergency and grant retention schedules. | Controls lifecycle. |
| lostdocops.metrics.completion_rate | completion rate | MEASUREMENT | Completion measures requests ending with replacement issued or verified path completed. | Shows effectiveness. |
| lostdocops.metrics.time_to_submit | time to submit | MEASUREMENT | Time to submit measures intake to agency submission. | Shows bottlenecks. |
| lostdocops.metrics.barrier_count | barrier count | MEASUREMENT | Barriers count missing proof, fees, appointments, language, transport and agency delay. | Guides fixes. |
| lostdocops.review.after_action | after-action review | METHOD | Review captures agency procedures, proof barriers, waiver success, privacy and appointment lessons. | Improves future support. |
