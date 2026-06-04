# BATCH 403: Emergency Prescription Refill Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `rxrefillops.*`  
**Scope:** intake, pharmacy contact, proof, emergency supply rules, delivery, privacy and tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| rxrefillops.intake.request_source | request source | RECORD | Source records shelter, hotline, clinic, pharmacy, caseworker or outreach desk. | Shows entry path. |
| rxrefillops.intake.patient_identity | patient identity | RECORD | Identity captures name, date of birth, contact, location and preferred language. | Enables matching. |
| rxrefillops.intake.medication_list | medication list | RECORD | List captures medication names, strength as reported, schedule as reported and prescribing provider. | Defines need. |
| rxrefillops.intake.urgent_flag | urgent flag | MODEL | Urgency weighs running out, chronic condition, controlled status, displacement and access barriers. | Prioritizes help. |
| rxrefillops.proof.prescription_proof | prescription proof | RECORD | Proof may include bottle, pharmacy profile, prescriber note, patient portal or prior claim. | Supports refill. |
| rxrefillops.proof.no_bottle | no-bottle pathway | METHOD | No-bottle pathway uses pharmacy lookup, prescriber contact or health record verification. | Helps displaced patients. |
| rxrefillops.proof.identity_gap | identity gap | CONSTRAINT | Missing ID is documented and routed through pharmacy or emergency policy alternatives. | Avoids automatic denial. |
| rxrefillops.proof.disaster_status | disaster status proof | RECORD | Disaster status records evacuation, sheltering, damage address or declared emergency basis. | Supports exceptions. |
| rxrefillops.pharmacy.preferred_pharmacy | preferred pharmacy | RECORD | Preferred pharmacy records name, phone, chain, store number and operating status. | Starts contact. |
| rxrefillops.pharmacy.open_status | pharmacy status | QUALITY_CHECK | Status checks hours, power, inventory, delivery ability and transfer capacity. | Finds workable outlet. |
| rxrefillops.pharmacy.profile_transfer | profile transfer | METHOD | Transfer coordinates refill history or prescription movement between pharmacies. | Restores access. |
| rxrefillops.pharmacy.callback_log | callback log | RECORD | Callback records staff contacted, time, message, decision and next action. | Maintains trail. |
| rxrefillops.rules.emergency_supply | emergency supply rule | CONSTRAINT | Rule records legal or policy basis for limited emergency supply. | Keeps support compliant. |
| rxrefillops.rules.controlled_med | controlled medication flag | SAFETY_RULE | Controlled or high-risk medicines require stricter verification and lawful pathway. | Prevents unsafe handling. |
| rxrefillops.rules.insurance_override | insurance override | METHOD | Override support helps pharmacy or plan apply disaster refill exception where available. | Reduces payment barrier. |
| rxrefillops.rules.prescriber_required | prescriber required | CONSTRAINT | Some requests must return to prescriber, clinic, pharmacist or emergency medical pathway. | Sets boundary. |
| rxrefillops.delivery.pickup_plan | pickup plan | METHOD | Pickup plan records who can collect, location, ID need, hours and transport barrier. | Gets medicine to patient. |
| rxrefillops.delivery.authorized_pickup | authorized pickup | RECORD | Authorization records caregiver, family member or courier permission and limits. | Protects privacy. |
| rxrefillops.delivery.courier_request | courier request | RECORD | Courier request captures address, pharmacy, package constraints and handoff confirmation. | Enables delivery. |
| rxrefillops.delivery.failed_handoff | failed handoff | RECORD | Failed handoff records no-contact, closed pharmacy, unpaid cost or access problem. | Triggers follow-up. |
| rxrefillops.privacy.minimum_data | minimum data | SAFETY_RULE | Staff avoid storing unnecessary diagnosis, full medication detail or identifiers. | Reduces privacy risk. |
| rxrefillops.privacy.private_space | private discussion | METHOD | Medication conversations occur away from public lines or shelter dorms. | Preserves dignity. |
| rxrefillops.privacy.release_form | release form | RECORD | Release documents permission to speak with pharmacy, prescriber, plan or caregiver. | Enables coordination. |
| rxrefillops.privacy.secure_notes | secure notes | SAFETY_RULE | Case notes are stored in restricted system or sealed paper workflow. | Protects health data. |
| rxrefillops.referral.clinic_referral | clinic referral | METHOD | Clinic referral handles expired prescriptions, new symptoms or medical reassessment needs. | Avoids unsafe refill. |
| rxrefillops.referral.prescriber_contact | prescriber contact | METHOD | Staff help contact prescriber office or on-call coverage for authorization. | Restores continuity. |
| rxrefillops.referral.assistance_program | assistance program | METHOD | Cost barriers route to manufacturer, nonprofit, public benefit or emergency fund support. | Helps affordability. |
| rxrefillops.referral.transport_referral | transport referral | METHOD | Pickup barriers route to crisis transport, delivery partner or mobile pharmacy. | Solves access. |
| rxrefillops.records.case_log | case log | RECORD | Log stores intake, proof, contacts, decision, delivery, cost barrier and closure. | Creates continuity. |
| rxrefillops.records.medication_redaction | medication redaction | SAFETY_RULE | Reports aggregate medication support without exposing individual drug details. | Protects patients. |
| rxrefillops.records.status | request status | RECORD | Status distinguishes intake, verification, pharmacy contacted, ready, delivered, denied or referred. | Shows progress. |
| rxrefillops.records.retention | retention rule | CONSTRAINT | Records follow health privacy, emergency, grant and agency schedules. | Controls lifecycle. |
| rxrefillops.communication.patient_update | patient update | METHOD | Patient update explains status, pickup plan, cost issue, delay or referral. | Reduces uncertainty. |
| rxrefillops.communication.pharmacy_script | pharmacy script | METHOD | Script standardizes disaster context, proof, release and request details. | Improves calls. |
| rxrefillops.communication.partner_update | partner update | METHOD | Partners receive aggregate barriers, pharmacy closures, transport needs and urgent gaps. | Coordinates response. |
| rxrefillops.communication.language | language support | METHOD | Interpreters or translated medication-access scripts support consent and instructions. | Improves access. |
| rxrefillops.qa.supervisor_review | supervisor review | QUALITY_CHECK | Supervisor reviews controlled flags, denials, privacy incidents and aging urgent cases. | Adds control. |
| rxrefillops.qa.case_reconciliation | case reconciliation | QUALITY_CHECK | Reconciliation checks open cases against pharmacy callbacks and delivery logs. | Prevents lost requests. |
| rxrefillops.qa.exception_audit | exception audit | QUALITY_CHECK | Audit checks emergency supply exceptions against policy and documentation. | Maintains compliance. |
| rxrefillops.qa.denial_review | denial review | METHOD | Denials are reviewed for alternate pharmacy, clinic, assistance or appeal path. | Reduces dead ends. |
| rxrefillops.metrics.requests_completed | requests completed | MEASUREMENT | Metric tracks refill support requests completed by pathway and site. | Shows output. |
| rxrefillops.metrics.time_to_ready | time to ready | MEASUREMENT | Time measures intake to pharmacy-ready or referral decision. | Reveals delay. |
| rxrefillops.metrics.barrier_count | barrier count | MEASUREMENT | Barriers count proof, cost, pharmacy closure, controlled status and transport issues. | Guides fixes. |
| rxrefillops.review.after_action | after-action review | METHOD | Review captures verification, privacy, pharmacy access, delivery and cost lessons. | Improves future support. |
