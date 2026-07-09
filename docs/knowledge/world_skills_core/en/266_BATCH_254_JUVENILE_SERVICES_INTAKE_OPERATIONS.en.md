# BATCH_254 — Juvenile Services Intake Operations Detail
# world_skills_core · source: world_skills_core:batch_254:juvenile_services_intake_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| juvops.referral.referral_intake | Juvenile services referral intake | invariant | Intake records youth, guardian, referral source, allegation, school and contact. | start case |
| juvops.referral.source_type | Juvenile referral source type | invariant | Source identifies law enforcement, school, court, family, agency or self-referral. | route response |
| juvops.referral.deadline_flag | Juvenile intake deadline flag | invariant | Flag tracks detention, hearing, diversion, notice or assessment timelines. | protect deadlines |
| juvops.referral.prior_history | Juvenile prior history review | variant | Review checks prior referrals, services, court orders, safety plans and outcomes. | context |
| juvops.identity.youth_identity | Youth identity verification | invariant | Verification checks name, birthdate, guardian, address, school and identifiers. | correct youth |
| juvops.identity.guardian_record | Juvenile guardian record | invariant | Record captures legal guardian, caregiver, contact, language and notification rules. | involve family |
| juvops.identity.school_link | Juvenile school link | variant | Link records school, grade, attendance contact, IEP signal and release needs. | coordinate support |
| juvops.screen.risk_screen | Juvenile intake risk screen | invariant | Screen evaluates safety, reoffense risk, needs, victim concern and supervision level. | triage case |
| juvops.screen.safety_screen | Juvenile safety screen | invariant | Screen flags self-harm, abuse, exploitation, violence, medical or immediate protection needs. | protect youth |
| juvops.screen.detention_criteria | Juvenile detention criteria review | variant | Review checks legal criteria, alternatives, guardian availability and public safety factors. | custody decision |
| juvops.screen.diversion_fit | Juvenile diversion fit | variant | Fit evaluates offense, history, accountability, victim input, needs and eligibility. | avoid deeper system |
| juvops.screen.service_need | Juvenile service need | invariant | Need identifies mental health, substance, school, family, housing, mentoring or restitution support. | plan help |
| juvops.notification.guardian_contact | Juvenile guardian contact | invariant | Contact records attempted and completed notice, language, method and response. | family notification |
| juvops.notification.victim_notice | Juvenile victim notice | variant | Notice follows rules for victim rights, safety, restitution or diversion input. | include victim |
| juvops.notification.court_notice | Juvenile court notice | invariant | Notice communicates hearing, intake outcome, deadlines and attendance requirements. | due process |
| juvops.diversion.diversion_plan | Juvenile diversion plan | variant | Plan lists requirements, services, restitution, apology, community work and completion date. | accountability |
| juvops.diversion.contract | Juvenile diversion contract | invariant | Contract records youth, guardian, terms, consequences, confidentiality and signatures. | formal agreement |
| juvops.diversion.progress_check | Juvenile diversion progress check | invariant | Check tracks attendance, tasks, service engagement, school update and barriers. | monitor completion |
| juvops.diversion.noncompletion | Juvenile diversion noncompletion | invariant | Record documents missed terms, outreach, barriers, extension or court referral. | resolve failure |
| juvops.assignment.case_assignment | Juvenile case assignment | invariant | Assignment links intake worker, supervisor, probation, diversion or service coordinator. | ownership |
| juvops.assignment.workload_review | Juvenile intake workload review | variant | Review balances cases by urgency, geography, specialization, language and availability. | fair coverage |
| juvops.appointment.intake_meeting | Juvenile intake meeting | invariant | Meeting gathers facts, family context, needs, rights, documents and next steps. | informed decision |
| juvops.appointment.no_show | Juvenile intake no-show | invariant | Record captures missed meeting, guardian contact, reschedule and escalation. | maintain process |
| juvops.appointment.interpreter | Juvenile intake interpreter | variant | Interpreter support covers youth, guardian, documents and confidentiality. | meaningful access |
| juvops.documents.document_packet | Juvenile intake document packet | invariant | Packet includes referral, notices, school records, assessments, releases and court papers. | case file |
| juvops.documents.release_form | Juvenile information release | variant | Release authorizes contact with school, provider, agency or guardian within limits. | coordinate care |
| juvops.documents.record_sealing_flag | Juvenile record sealing flag | invariant | Flag notes confidentiality, sealing, expungement or access restriction requirements. | protect records |
| juvops.services.service_directory | Juvenile services directory | invariant | Directory lists counseling, mentoring, substance, school, family, housing and recreation programs. | referral options |
| juvops.services.warm_referral | Juvenile warm referral | variant | Referral connects family directly to provider with consent and appointment details. | reduce drop-off |
| juvops.services.transport_barrier | Juvenile transport barrier | variant | Barrier note records lack of ride, distance, safety, schedule or cost issue. | plan access |
| juvops.services.family_support | Juvenile family support referral | variant | Referral connects guardian to parenting, benefits, housing, crisis or mediation support. | stabilize home |
| juvops.court.petition_review | Juvenile petition review | invariant | Review prepares referral for formal petition decision with facts and eligibility. | court path |
| juvops.court.hearing_prep | Juvenile hearing preparation | invariant | Preparation gathers notices, reports, parties, recommendations and interpreter needs. | ready court |
| juvops.court.status_update | Juvenile court status update | invariant | Update communicates diversion, detention, services, compliance or risk changes. | inform court |
| juvops.compliance.condition_tracking | Juvenile condition tracking | invariant | Tracking records curfew, school, contact, restitution, service or testing conditions. | monitor case |
| juvops.compliance.violation_note | Juvenile violation note | variant | Note records alleged noncompliance, context, response, guardian contact and next step. | proportional action |
| juvops.quality.supervisor_review | Juvenile intake supervisor review | invariant | Review checks screening, notices, diversion, detention decision, services and documentation. | quality control |
| juvops.quality.confidentiality_check | Juvenile confidentiality check | invariant | Check restricts record access, sharing, public disclosure and safe contact details. | protect youth |
| juvops.reporting.intake_report | Juvenile intake report | invariant | Report summarizes referrals, risk levels, diversion, detention, services and backlog. | manage office |
| juvops.reporting.equity_review | Juvenile services equity review | variant | Review compares outcomes by geography, race, language, gender, disability and referral source. | detect disparity |
| juvops.metrics.juvenile_intake_kpi | Juvenile services intake KPI | variant | KPI tracks time to screen, diversion completion, no-shows, detention rate and service connection. | manage intake |
| juvops.close.case_closure | Juvenile intake case closure | invariant | Closure records completed diversion, court referral, service handoff, withdrawal or duplicate. | close loop |
| juvops.continuity.afterhours_intake | Juvenile after-hours intake response | variant | Response handles urgent referrals, detention decisions, guardian contact and next-day handoff. | maintain coverage |
| juvops.continuity.system_outage | Juvenile intake system outage | invariant | Outage uses paper intake, secure custody of forms, manual logs and later entry. | continue safely |
