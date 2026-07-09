# BATCH 410: Disaster Legal Clinic Appointment Operations

**KnowledgeUnits:** 44  
**Namespace:** `legalclinicops.*`  
**Scope:** intake, issue triage, conflict checks, scheduling, documents, reminders and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| legalclinicops.intake.request_source | request source | RECORD | Source records survivor center, hotline, shelter, caseworker, court, nonprofit or walk-in. | Shows entry path. |
| legalclinicops.intake.client_profile | client profile | RECORD | Profile captures name, contact, location, language, household and safe-contact limits. | Supports appointment. |
| legalclinicops.intake.disaster_link | disaster link | RECORD | Link records how the legal issue relates to disaster damage, displacement or recovery. | Determines relevance. |
| legalclinicops.intake.urgency | urgency model | MODEL | Urgency weighs court date, eviction, benefits deadline, safety risk and document deadline. | Prioritizes scheduling. |
| legalclinicops.triage.issue_type | issue type | RECORD | Type distinguishes housing, benefits, insurance, documents, employment, family, debt or consumer issue. | Routes expertise. |
| legalclinicops.triage.service_level | service level | MODEL | Level distinguishes information, advice, brief service, referral or full representation screen. | Sets expectation. |
| legalclinicops.triage.deadline | deadline capture | SAFETY_RULE | Deadlines are recorded with date, source, consequence and reminder. | Prevents missed rights. |
| legalclinicops.triage.out_of_scope | out-of-scope rule | CONSTRAINT | Criminal, complex litigation, non-disaster or prohibited matters may route elsewhere. | Protects clinic limits. |
| legalclinicops.conflict.identity_check | identity check | RECORD | Conflict check captures opposing parties, landlords, insurers, employers and agencies. | Finds conflicts. |
| legalclinicops.conflict.database_search | database search | QUALITY_CHECK | Staff search prior clients, related parties and adverse parties before advice. | Protects ethics. |
| legalclinicops.conflict.potential_conflict | potential conflict | RECORD | Potential conflict is flagged for attorney review before appointment proceeds. | Avoids improper advice. |
| legalclinicops.conflict.clearance | clearance record | RECORD | Clearance records reviewer, decision, limits and date. | Documents ethics step. |
| legalclinicops.scheduling.slot_match | slot match | METHOD | Slot matches issue, urgency, language, attorney skill, clinic site and access needs. | Books right appointment. |
| legalclinicops.scheduling.appointment_record | appointment record | RECORD | Record stores date, mode, location/link, client, issue, attorney and documents needed. | Creates schedule. |
| legalclinicops.scheduling.waitlist | waitlist | RECORD | Waitlist captures priority, issue, deadline and callback method. | Tracks unmet demand. |
| legalclinicops.scheduling.reschedule | reschedule process | METHOD | Reschedule records reason, new date, deadline impact and notification. | Keeps case active. |
| legalclinicops.documents.document_list | document list | RECORD | List includes notices, leases, policies, IDs, bills, photos, letters and agency decisions. | Prepares review. |
| legalclinicops.documents.upload | upload support | METHOD | Staff help securely scan or upload documents before appointment. | Saves clinic time. |
| legalclinicops.documents.missing | missing document | RECORD | Missing items and alternatives are documented for attorney review. | Keeps issue visible. |
| legalclinicops.documents.privacy | document privacy | SAFETY_RULE | Sensitive records are stored securely and shared only with authorized clinic roles. | Protects client. |
| legalclinicops.reminders.first_notice | first reminder | METHOD | Reminder confirms time, place, documents, phone/link and safe contact. | Reduces no-shows. |
| legalclinicops.reminders.deadline_notice | deadline reminder | SAFETY_RULE | Cases with legal deadlines receive extra reminder and escalation. | Protects rights. |
| legalclinicops.reminders.language | language reminder | METHOD | Reminder uses preferred language and interpreter instructions. | Improves access. |
| legalclinicops.reminders.no_response | no-response handling | METHOD | No-response cases receive attempts, backup contact and waitlist adjustment. | Maintains schedule. |
| legalclinicops.dayof.checkin | check-in | RECORD | Check-in confirms identity, appointment, conflict status, consent and documents. | Starts visit. |
| legalclinicops.dayof.interpreter | interpreter assignment | RECORD | Interpreter assignment records language, mode, confidentiality and availability. | Enables advice. |
| legalclinicops.dayof.private_space | private space | SAFETY_RULE | Legal conversations occur in private area or secure remote channel. | Preserves confidentiality. |
| legalclinicops.dayof.no_show | no-show record | RECORD | No-show records attempts, reason if known, deadline impact and reschedule decision. | Manages capacity. |
| legalclinicops.outcome.advice_given | advice outcome | RECORD | Outcome records advice topic, brief service, documents reviewed and next steps without excess detail. | Closes loop. |
| legalclinicops.outcome.referral | referral outcome | METHOD | Referral connects client to legal aid, bar program, agency, court help or advocate. | Extends help. |
| legalclinicops.outcome.representation_screen | representation screen | RECORD | Screen records eligibility for further legal services and decision status. | Handles complex cases. |
| legalclinicops.outcome.client_copy | client copy | METHOD | Client receives plain next-step summary, deadlines and contact information. | Supports follow-through. |
| legalclinicops.records.case_note | case note | RECORD | Note stores intake, triage, conflicts, appointment, documents, outcome and follow-up. | Creates continuity. |
| legalclinicops.records.confidentiality | confidentiality rule | SAFETY_RULE | Records follow attorney-client, legal aid and privacy requirements. | Protects privilege. |
| legalclinicops.records.retention | retention rule | CONSTRAINT | Records follow legal clinic, funder and professional retention schedules. | Controls lifecycle. |
| legalclinicops.records.supervisor_review | supervisor review | QUALITY_CHECK | Supervisor reviews appointment records for triage, conflict, deadline and outcome completeness. | Improves reliability. |
| legalclinicops.records.data_export | data export | QUALITY_CHECK | Aggregate exports avoid client-identifying facts and legal advice details. | Supports reporting safely. |
| legalclinicops.followup.followup_task | follow-up task | RECORD | Task tracks documents, deadline, referral completion, appeal filing or next appointment. | Keeps momentum. |
| legalclinicops.followup.callback | callback process | METHOD | Callback documents attempt, result, new issue and closure decision. | Maintains continuity. |
| legalclinicops.followup.referral_confirm | referral confirmation | QUALITY_CHECK | Confirmation checks whether referred client reached receiving service. | Closes loop. |
| legalclinicops.metrics.appointments_held | appointments held | MEASUREMENT | Metric tracks scheduled, completed, canceled, no-show and rescheduled appointments. | Shows throughput. |
| legalclinicops.metrics.issue_mix | issue mix | MEASUREMENT | Issue mix counts housing, benefits, insurance, documents and other legal needs. | Plans staffing. |
| legalclinicops.metrics.deadline_cases | deadline cases | MEASUREMENT | Deadline cases track urgent legal deadlines and outcomes. | Shows risk load. |
| legalclinicops.review.after_action | after-action review | METHOD | Review captures triage, conflicts, document readiness, no-shows, referrals and privacy lessons. | Improves future clinics. |
