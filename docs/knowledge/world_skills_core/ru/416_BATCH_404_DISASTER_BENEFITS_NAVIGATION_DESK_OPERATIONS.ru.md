# BATCH 404: Disaster Benefits Navigation Desk Operations

**KnowledgeUnits:** 44  
**Namespace:** `benefitsdeskops.*`  
**Scope:** screening, program matching, document lists, referrals, appointments, appeals and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| benefitsdeskops.intake.request_source | request source | RECORD | Source records survivor center, hotline, shelter, outreach, partner or walk-in desk. | Shows entry path. |
| benefitsdeskops.intake.household_profile | household profile | RECORD | Profile captures household size, location, displacement, income change and urgent needs. | Supports screening. |
| benefitsdeskops.intake.preferred_contact | preferred contact | RECORD | Contact records phone, email, address, language, safe contact and backup person. | Enables follow-up. |
| benefitsdeskops.intake.consent | consent record | RECORD | Consent documents permission to discuss benefits with agencies or caseworkers. | Enables coordination. |
| benefitsdeskops.screening.need_screen | need screen | MODEL | Screen identifies food, cash, housing, unemployment, health, childcare, repair or legal needs. | Finds programs. |
| benefitsdeskops.screening.eligibility_hint | eligibility hint | MODEL | Hint uses disaster impact, income, citizenship rules, residence and household factors. | Guides next step. |
| benefitsdeskops.screening.urgent_benefit | urgent benefit flag | MODEL | Urgency weighs eviction, food shortage, medical need, childcare, income loss and deadline. | Prioritizes help. |
| benefitsdeskops.screening.duplicate_case | duplicate case check | QUALITY_CHECK | Duplicate check links repeated visits and existing applications. | Prevents confusion. |
| benefitsdeskops.program.program_match | program match | METHOD | Matching maps needs to public, nonprofit, insurance, employment and recovery programs. | Builds options. |
| benefitsdeskops.program.program_limits | program limits | CONSTRAINT | Limits explain eligibility boundaries, deadlines, benefit caps and documentation requirements. | Sets expectations. |
| benefitsdeskops.program.sequence | program sequence | METHOD | Sequence orders applications to avoid conflicts and meet deadlines. | Improves outcomes. |
| benefitsdeskops.program.no_wrong_door | no wrong door | METHOD | Staff redirect residents to correct program without closing support. | Keeps access open. |
| benefitsdeskops.documents.document_list | document list | RECORD | List shows required identity, address, income, loss, household and disaster proof. | Organizes preparation. |
| benefitsdeskops.documents.missing_docs | missing documents | RECORD | Missing document list records gaps and replacement pathway. | Targets support. |
| benefitsdeskops.documents.upload_support | upload support | METHOD | Staff help scan or upload documents using secure handling rules. | Completes application. |
| benefitsdeskops.documents.redaction | redaction rule | SAFETY_RULE | Copies redact unnecessary numbers or sensitive details when allowed. | Protects identity. |
| benefitsdeskops.application.form_support | form support | METHOD | Staff explain forms and help with navigation while resident confirms answers. | Reduces errors. |
| benefitsdeskops.application.submission_proof | submission proof | RECORD | Proof includes confirmation number, receipt, mailed tracking or agency note. | Verifies filing. |
| benefitsdeskops.application.status_check | status check | METHOD | Status check uses agency portal, phone line, caseworker or automated notice. | Tracks progress. |
| benefitsdeskops.application.correction | correction request | RECORD | Correction records agency request, missing item, deadline and responsible person. | Keeps case moving. |
| benefitsdeskops.referral.warm_referral | warm referral | METHOD | Warm referral confirms receiving agency, contact, eligibility clue and appointment need. | Reduces drop-off. |
| benefitsdeskops.referral.legal_aid | legal aid referral | METHOD | Legal aid handles denials, appeals, identity issues, landlord conflict or benefit termination. | Adds expertise. |
| benefitsdeskops.referral.case_management | case management referral | METHOD | Case management handles complex multi-need households and long-term recovery. | Provides continuity. |
| benefitsdeskops.referral.language_access | language referral | METHOD | Language support connects interpreter, translated forms or bilingual agency contact. | Improves access. |
| benefitsdeskops.appointment.slot_booking | slot booking | RECORD | Booking records agency, date, mode, confirmation, documents and access needs. | Secures next step. |
| benefitsdeskops.appointment.reminder | reminder process | METHOD | Reminder uses preferred contact, language and backup channel. | Reduces missed appointments. |
| benefitsdeskops.appointment.transport | transport need | RECORD | Transport need records trip purpose, time, accessibility and referral status. | Supports attendance. |
| benefitsdeskops.appointment.no_show | no-show handling | METHOD | No-show reason is recorded and reschedule or alternate pathway is offered. | Preserves case. |
| benefitsdeskops.appeal.denial_intake | denial intake | RECORD | Intake captures notice, deadline, reason, program, evidence and resident goal. | Starts appeal review. |
| benefitsdeskops.appeal.deadline_alert | deadline alert | SAFETY_RULE | Appeal deadlines are flagged with escalation and reminder. | Prevents lost rights. |
| benefitsdeskops.appeal.evidence_plan | evidence plan | METHOD | Plan identifies documents, statements, photos, receipts or agency records needed. | Builds appeal. |
| benefitsdeskops.appeal.referral_status | appeal referral status | RECORD | Status tracks legal aid, advocate, agency contact or self-filed appeal. | Shows owner. |
| benefitsdeskops.followup.followup_queue | follow-up queue | RECORD | Queue tracks open cases by status, deadline, owner and next contact date. | Maintains continuity. |
| benefitsdeskops.followup.outcome_record | outcome record | RECORD | Outcome records approved, denied, pending, referred, withdrawn or unreachable. | Closes loop. |
| benefitsdeskops.followup.unreachable | unreachable process | METHOD | Process documents attempts, backup contact and final closure rule. | Keeps audit fair. |
| benefitsdeskops.followup.reopen | reopen rule | METHOD | Case can reopen for denial, new need, missed deadline or new documents. | Handles change. |
| benefitsdeskops.privacy.minimum_data | minimum data | SAFETY_RULE | Desk stores only needed benefit, identity and contact data. | Reduces exposure. |
| benefitsdeskops.privacy.safe_contact | safe contact | SAFETY_RULE | Safe-contact rule avoids unsafe messages for domestic violence or unstable housing cases. | Protects residents. |
| benefitsdeskops.privacy.role_access | role access | SAFETY_RULE | Access differs for navigators, supervisors, legal partners and volunteers. | Controls records. |
| benefitsdeskops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports visits, programs screened, applications supported, referrals and barriers. | Informs command. |
| benefitsdeskops.metrics.application_count | application count | MEASUREMENT | Count tracks applications by program, status and site. | Shows workload. |
| benefitsdeskops.metrics.approval_rate | approval rate | MEASUREMENT | Approval rate measures known approvals among completed applications by program. | Shows effectiveness. |
| benefitsdeskops.metrics.barrier_count | barrier count | MEASUREMENT | Barriers count missing documents, language, internet, transport, deadline and eligibility issues. | Guides fixes. |
| benefitsdeskops.review.after_action | after-action review | METHOD | Review captures program confusion, document barriers, referral quality, appeals and privacy lessons. | Improves future desks. |
