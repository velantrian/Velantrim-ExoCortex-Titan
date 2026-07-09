# BATCH_256 — Victim Services Office Operations Detail
# world_skills_core · source: world_skills_core:batch_256:victim_services_office_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| victimops.intake.victim_contact | Victim services intake contact | invariant | Contact records person, case, relationship, safe contact, language and immediate concern. | start support |
| victimops.intake.referral_source | Victim services referral source | variant | Source identifies police, prosecutor, court, shelter, hospital, hotline, school or self-referral. | route context |
| victimops.intake.consent_notice | Victim services consent notice | invariant | Notice explains confidentiality, mandatory reporting limits, data use and voluntary participation. | informed support |
| victimops.intake.urgent_safety | Victim urgent safety flag | invariant | Flag marks threat, stalking, retaliation, shelter need, medical need or child safety concern. | triage risk |
| victimops.intake.service_plan | Victim services initial plan | variant | Plan lists safety, court, compensation, counseling, housing, referrals and follow-up. | organize support |
| victimops.safety.safety_plan | Victim safety plan | invariant | Plan covers contacts, safe routes, emergency numbers, documents, shelter and technology safety. | reduce risk |
| victimops.safety.protection_order_referral | Protection order referral | variant | Referral connects victim to court, advocate, forms, eligibility information and safety planning. | support filing |
| victimops.safety.safe_contact_protocol | Victim safe contact protocol | invariant | Protocol defines allowed phone, text, email, mail, voicemail and times. | avoid exposure |
| victimops.safety.threat_update | Victim threat update | invariant | Update records new threat, violation, suspect contact, stalking pattern or escalation. | adjust response |
| victimops.referral.referral_directory | Victim services referral directory | invariant | Directory lists shelter, counseling, legal, medical, financial, immigration and child services. | connect help |
| victimops.referral.warm_referral | Victim services warm referral | variant | Referral contacts partner with consent, essential facts and appointment details. | reduce drop-off |
| victimops.referral.counseling_referral | Victim counseling referral | variant | Referral links trauma counseling, crisis support, group services or specialized therapy. | emotional support |
| victimops.referral.shelter_referral | Victim shelter referral | invariant | Referral checks bed availability, safety, transport, household size and confidentiality. | safe housing |
| victimops.notification.case_status_notice | Victim case status notice | invariant | Notice updates on arrest, charges, hearing, release, plea, sentence or appeal. | victim rights |
| victimops.notification.court_date_notice | Victim court date notice | invariant | Notice sends hearing type, date, location, remote access, rights and support options. | prepare victim |
| victimops.notification.release_notice | Victim release notice | variant | Notice communicates custody release, conditions, timing and safety steps when permitted. | manage risk |
| victimops.notification.preference_record | Victim notification preference | invariant | Record stores desired notices, channels, language, frequency and opt-out choices. | respect control |
| victimops.compensation.comp_application | Victim compensation application | invariant | Application records crime, expenses, eligibility, documents, deadlines and claimant. | financial aid |
| victimops.compensation.expense_document | Victim expense document | invariant | Document captures medical, counseling, funeral, relocation, lost wage or repair expense. | support claim |
| victimops.compensation.claim_status | Victim compensation claim status | invariant | Status tracks submitted, pending, approved, denied, appealed, paid or missing documents. | case visibility |
| victimops.compensation.denial_review | Victim compensation denial review | variant | Review explains reason, appeal route, missing evidence and alternative resources. | fair process |
| victimops.court.court_accompaniment | Victim court accompaniment | variant | Accompaniment schedules advocate, arrival, waiting area, safety, testimony and debrief. | reduce stress |
| victimops.court.waiting_area | Victim waiting area plan | variant | Plan separates victim from defendant, witnesses, media or unsafe contacts. | protect privacy |
| victimops.court.impact_statement | Victim impact statement support | variant | Support explains format, deadlines, submission, safety and emotional considerations. | prepare statement |
| victimops.court.testimony_support | Victim testimony support | invariant | Support coordinates subpoena, logistics, breaks, accessibility, interpreter and safety needs. | court readiness |
| victimops.followup.followup_schedule | Victim services follow-up schedule | invariant | Schedule sets check-ins after intake, hearing, referral, release or safety change. | maintain support |
| victimops.followup.contact_attempt | Victim follow-up contact attempt | invariant | Attempt records date, channel, outcome, safe-message status and next step. | track outreach |
| victimops.followup.unreachable_case | Unreachable victim services case | variant | Case records attempts, safety constraints, referral options and closure rule. | avoid unsafe pursuit |
| victimops.followup.service_update | Victim service update | invariant | Update records referral outcome, needs change, safety issue or resource gap. | adapt support |
| victimops.records.case_note | Victim services case note | invariant | Note captures contact, services, safety, referrals, notices and advocate action. | service record |
| victimops.records.confidential_file | Victim confidential file | invariant | File protects safe contact, address, statements, compensation and service notes. | privacy |
| victimops.records.release_of_information | Victim information release | variant | Release authorizes sharing with partner, attorney, agency or compensation program. | controlled sharing |
| victimops.records.retention_rule | Victim services retention rule | invariant | Rule defines retention and destruction for service, compensation and notification records. | compliance |
| victimops.quality.supervisor_review | Victim services supervisor review | invariant | Review checks safety, documentation, referrals, rights notices, compensation and closure. | quality |
| victimops.quality.secondary_trauma | Advocate secondary trauma support | variant | Support tracks workload, debrief, supervision, rotation and wellness referral. | sustain staff |
| victimops.quality.complaint_response | Victim services complaint response | invariant | Response records complaint, review, correction, explanation and follow-up. | accountability |
| victimops.reporting.service_volume | Victim services volume report | invariant | Report summarizes intakes, referrals, court support, notices, compensation and closures. | manage office |
| victimops.reporting.rights_compliance | Victim rights compliance report | variant | Report tracks required notices, opt-ins, failures, late notices and corrective actions. | oversight |
| victimops.metrics.victim_services_kpi | Victim services KPI | variant | KPI tracks response time, safety plans, referrals completed, notices, compensation and satisfaction. | manage support |
| victimops.close.case_closure | Victim services case closure | invariant | Closure records resolved need, opt-out, unreachable, referral completed or case ended. | close support |
| victimops.continuity.high_profile_case | Victim services high-profile case response | variant | Response plans media concerns, privacy, safety, staffing, court support and leadership updates. | protect victim |
| victimops.continuity.afterhours_call | Victim services after-hours call | variant | Call handles urgent safety, shelter, crisis support, notification and next-day handoff. | continuous support |
| victimops.outreach.rights_material | Victim rights material | invariant | Material explains rights, services, compensation, contacts, privacy and safety resources. | inform community |
| victimops.partners.multidisciplinary_team | Victim services multidisciplinary team | variant | Team coordinates with prosecution, law enforcement, shelters, medical and advocacy partners. | coordinated care |
