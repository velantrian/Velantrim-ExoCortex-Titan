# BATCH 412: Emergency School Enrollment Assistance Operations

**KnowledgeUnits:** 44  
**Namespace:** `schoolenrollops.*`  
**Scope:** intake, residency flexibility, documents, transportation, special services and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| schoolenrollops.intake.request_source | request source | RECORD | Source records shelter, family, school district, caseworker, hotline or outreach desk. | Shows entry path. |
| schoolenrollops.intake.student_profile | student profile | RECORD | Profile captures student name, age, grade, prior school, caregiver and language. | Defines enrollment. |
| schoolenrollops.intake.displacement | displacement status | RECORD | Status records temporary address, shelter, doubled-up housing, hotel or no fixed address. | Supports flexibility. |
| schoolenrollops.intake.urgency | urgency model | MODEL | Urgency weighs days out of school, exams, special services, safety and caregiver availability. | Prioritizes help. |
| schoolenrollops.residency.flex_rule | residency flexibility | CONSTRAINT | Disaster displacement may allow enrollment without usual proof under applicable policy. | Keeps access open. |
| schoolenrollops.residency.school_origin | school of origin | METHOD | Family may need support comparing origin school versus local enrollment. | Preserves continuity. |
| schoolenrollops.residency.address_affidavit | address affidavit | RECORD | Affidavit documents temporary living arrangement when standard proof is missing. | Supports enrollment. |
| schoolenrollops.residency.boundary_check | boundary check | QUALITY_CHECK | Check identifies correct district, school, transfer option or liaison. | Avoids routing error. |
| schoolenrollops.documents.document_list | document list | RECORD | List includes ID, birth date, prior records, immunization, guardianship and address alternatives. | Organizes packet. |
| schoolenrollops.documents.missing_records | missing records | RECORD | Missing record list records source, request date, substitute and follow-up owner. | Keeps file moving. |
| schoolenrollops.documents.record_request | record request | METHOD | Prior school records are requested through district, family or emergency liaison. | Restores history. |
| schoolenrollops.documents.secure_handling | secure handling | SAFETY_RULE | Student records are handled with education privacy controls. | Protects children. |
| schoolenrollops.guardian.guardian_check | guardian check | QUALITY_CHECK | Check confirms enrolling adult authority, caregiver role or emergency contact limits. | Prevents improper release. |
| schoolenrollops.guardian.temporary_caregiver | temporary caregiver | RECORD | Record captures disaster caregiver, relationship, permissions and expiration if applicable. | Supports continuity. |
| schoolenrollops.guardian.custody_flag | custody flag | SAFETY_RULE | Custody or safety concerns route to school official or legal pathway. | Protects student. |
| schoolenrollops.guardian.contact_update | contact update | METHOD | Contact list includes safe phone, email, pickup adults and emergency contacts. | Enables communication. |
| schoolenrollops.transport.transport_need | transport need | RECORD | Need records origin school, temporary address, disability access and schedule. | Starts routing. |
| schoolenrollops.transport.route_request | route request | METHOD | Request goes to district transport, liaison, transit partner or voucher path. | Gets student to school. |
| schoolenrollops.transport.accessible_bus | accessible bus | RECORD | Accessible transport records wheelchair, aide, medical equipment or curb needs. | Supports inclusion. |
| schoolenrollops.transport.transport_delay | transport delay | RECORD | Delay records reason, interim plan, caregiver notice and escalation. | Prevents missed school. |
| schoolenrollops.services.special_ed | special education record | RECORD | Record captures IEP/504 status, services, evaluations and prior provider contacts. | Maintains support. |
| schoolenrollops.services.health_plan | health plan | RECORD | Health plan notes allergies, medication boundary, nurse needs and emergency care plan. | Protects student. |
| schoolenrollops.services.language | language services | METHOD | Language support identifies interpreter, bilingual staff and translated forms. | Improves access. |
| schoolenrollops.services.counseling | counseling referral | METHOD | Counseling referral supports trauma, grief, displacement stress or attendance concerns. | Helps adjustment. |
| schoolenrollops.enrollment.application | enrollment application | RECORD | Application records school, date, student, caregiver, documents and missing items. | Starts process. |
| schoolenrollops.enrollment.immediate_entry | immediate entry | METHOD | Immediate entry supports attendance while records are pending where policy allows. | Reduces learning loss. |
| schoolenrollops.enrollment.denial | denial record | RECORD | Denial records reason, policy cited, appeal path and alternate contact. | Enables correction. |
| schoolenrollops.enrollment.transfer | transfer record | RECORD | Transfer records origin, destination, grade placement, credits and services. | Maintains continuity. |
| schoolenrollops.communication.family_script | family script | METHOD | Script explains rights, needed documents, timelines, transport and next steps. | Sets expectations. |
| schoolenrollops.communication.school_contact | school contact | RECORD | Contact records registrar, liaison, counselor, nurse and transport staff. | Coordinates work. |
| schoolenrollops.communication.partner_update | partner update | METHOD | Partners receive aggregate barriers, transport issues and document gaps. | Aligns support. |
| schoolenrollops.communication.reminder | reminder process | METHOD | Reminders cover appointments, first day, transport, missing documents and meetings. | Reduces drop-off. |
| schoolenrollops.followup.first_day | first-day check | METHOD | Check confirms student attended, transport worked and caregiver received schedule. | Closes access loop. |
| schoolenrollops.followup.service_check | service check | QUALITY_CHECK | Follow-up confirms special services, language support and health plans started. | Prevents service gaps. |
| schoolenrollops.followup.attendance | attendance watch | MEASUREMENT | Attendance watch flags repeated absence after enrollment. | Finds barriers. |
| schoolenrollops.followup.case_close | case close | RECORD | Closure records enrolled, transferred, referred, denied, moved or unreachable. | Ends support. |
| schoolenrollops.privacy.student_privacy | student privacy | SAFETY_RULE | Student data is shared only with authorized school and support roles. | Protects records. |
| schoolenrollops.privacy.safe_contact | safe contact | SAFETY_RULE | Safe contact avoids exposing location or caregiver details where risk exists. | Protects family. |
| schoolenrollops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports students assisted, enrolled, pending, transport needs and barriers. | Informs response. |
| schoolenrollops.metrics.time_to_enroll | time to enroll | MEASUREMENT | Metric measures intake to confirmed enrollment or denial. | Shows delay. |
| schoolenrollops.metrics.transport_gap | transport gap | MEASUREMENT | Gap count tracks students waiting for transport by reason. | Guides resources. |
| schoolenrollops.metrics.document_gap | document gap | MEASUREMENT | Gap count tracks missing records, guardianship, immunization or residency proof. | Targets help. |
| schoolenrollops.qa.case_review | case review | QUALITY_CHECK | Review checks application, documents, transport, services and follow-up completeness. | Improves reliability. |
| schoolenrollops.review.after_action | after-action review | METHOD | Review captures enrollment flexibility, transport, records, special services and privacy lessons. | Improves future support. |
