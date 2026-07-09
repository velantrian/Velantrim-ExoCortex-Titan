# BATCH_258 — Mediation Center Operations Detail
# world_skills_core · source: world_skills_core:batch_258:mediation_center_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| mediateops.intake.case_intake | Mediation case intake | invariant | Intake records parties, dispute type, referral source, court status and contact. | open mediation case |
| mediateops.intake.referral_source | Mediation referral source | variant | Source identifies court, agency, school, community, employer, attorney or self-referral. | route case |
| mediateops.intake.party_contact | Mediation party contact | invariant | Contact captures safe phone, email, language, representative and communication limits. | reach parties |
| mediateops.intake.consent_notice | Mediation consent notice | invariant | Notice explains voluntary process, confidentiality, neutrality, limits and fees. | informed participation |
| mediateops.intake.urgent_timeline | Mediation urgent timeline flag | variant | Flag marks court deadline, eviction, custody, workplace disruption or community conflict. | schedule priority |
| mediateops.screen.suitability_screen | Mediation suitability screen | invariant | Screen evaluates willingness, power balance, safety, legal constraints and topic fit. | appropriate process |
| mediateops.screen.safety_screen | Mediation safety screen | invariant | Screen checks intimidation, violence, coercion, restraining orders or unsafe contact. | protect parties |
| mediateops.screen.conflict_check | Mediator conflict check | invariant | Check identifies mediator relationships, prior work, interests or bias concerns. | neutrality |
| mediateops.screen.exclusion_reason | Mediation exclusion reason | variant | Reason records unsafe, inappropriate, nonconsensual, legal bar or unavailable party. | explain nonacceptance |
| mediateops.assignment.mediator_roster | Mediation mediator roster | invariant | Roster stores training, specialty, availability, languages, fees and status. | assignment pool |
| mediateops.assignment.mediator_match | Mediator match | invariant | Match chooses mediator by case type, language, location, availability and conflict status. | fit case |
| mediateops.assignment.co_mediation | Co-mediation assignment | variant | Assignment pairs mediators for complex, high-conflict, training or language needs. | support process |
| mediateops.assignment.confirmation | Mediation assignment confirmation | invariant | Confirmation sends mediator, parties, date, format, location and preparation notes. | align participants |
| mediateops.schedule.session_schedule | Mediation session schedule | invariant | Schedule records date, time, duration, room or link, parties and mediator. | set meeting |
| mediateops.schedule.reschedule_request | Mediation reschedule request | variant | Request records party availability, reason, deadline impact and new date. | manage calendar |
| mediateops.schedule.no_show | Mediation no-show record | invariant | Record captures absent party, contact attempt, fee rule, reschedule or closure. | case control |
| mediateops.schedule.remote_session | Remote mediation session | variant | Session plan includes platform, private rooms, tech check, documents and backup phone. | virtual process |
| mediateops.prep.party_orientation | Mediation party orientation | invariant | Orientation explains roles, ground rules, confidentiality, caucus, agreement and exit options. | prepare parties |
| mediateops.prep.document_exchange | Mediation document exchange | variant | Exchange manages statements, exhibits, summaries, confidentiality and deadlines. | shared context |
| mediateops.prep.interpreter_need | Mediation interpreter need | variant | Need records language, interpreter, confidentiality, remote support and scheduling. | meaningful access |
| mediateops.session.opening_statement | Mediation opening statement | invariant | Statement reviews neutrality, process, confidentiality, voluntary participation and ground rules. | frame session |
| mediateops.session.issue_list | Mediation issue list | invariant | List captures topics, interests, priorities and unresolved questions from parties. | structure dialogue |
| mediateops.session.caucus_note | Mediation caucus note | variant | Note records private meeting occurrence, authorized disclosures and process concerns. | manage confidentiality |
| mediateops.session.power_balance | Mediation power balance action | variant | Action adjusts format, breaks, support persons or shuttle process for fairness. | safer dialogue |
| mediateops.session.impasse_record | Mediation impasse record | invariant | Record states unresolved issues, options explored, party decisions and next step. | close attempt |
| mediateops.agreement.draft_agreement | Mediation draft agreement | invariant | Draft records terms, responsibilities, dates, payments, behavior commitments and review needs. | capture deal |
| mediateops.agreement.legal_review_flag | Mediation legal review flag | variant | Flag reminds parties to seek legal review before signing when appropriate. | avoid overreach |
| mediateops.agreement.signature_process | Mediation signature process | invariant | Process records party signatures, date, copies, filing need and distribution. | formalize agreement |
| mediateops.agreement.court_filing | Mediation court filing | variant | Filing sends agreement, status report or nonagreement notice to court as required. | update docket |
| mediateops.close.case_closure | Mediation case closure | invariant | Closure records agreement, partial agreement, impasse, withdrawal, no-show or unsuitable result. | end case |
| mediateops.close.followup_check | Mediation follow-up check | variant | Check asks parties about compliance, satisfaction, further dispute or referral need. | support durability |
| mediateops.close.satisfaction_survey | Mediation satisfaction survey | variant | Survey measures fairness, clarity, safety, mediator skill and outcome satisfaction. | improve service |
| mediateops.records.confidential_file | Mediation confidential file | invariant | File stores intake, notes, agreement, communications and limits disclosure. | protect process |
| mediateops.records.retention_rule | Mediation record retention | invariant | Rule defines retention, destruction, court reporting and confidential notes handling. | compliance |
| mediateops.records.data_correction | Mediation data correction | invariant | Correction fixes party, date, result, mediator or referral error with audit note. | accurate records |
| mediateops.quality.mediator_feedback | Mediator feedback review | invariant | Review assesses neutrality, process control, complaints, timeliness and training needs. | quality control |
| mediateops.quality.complaint_response | Mediation complaint response | invariant | Response records complaint, review, mediator response, outcome and corrective action. | accountability |
| mediateops.quality.training_record | Mediator training record | invariant | Record tracks basic, advanced, ethics, domestic violence, cultural and specialty training. | qualified roster |
| mediateops.reporting.case_volume | Mediation case volume report | invariant | Report summarizes referrals, scheduled, held, agreements, no-shows, closures and backlog. | manage center |
| mediateops.reporting.outcome_report | Mediation outcome report | variant | Report tracks full agreement, partial, impasse, satisfaction, compliance and court impact. | evaluate program |
| mediateops.metrics.mediation_kpi | Mediation center KPI | variant | KPI tracks time to session, agreement rate, no-shows, safety screens, complaints and satisfaction. | manage mediation |
| mediateops.continuity.mediator_no_show | Mediator no-show response | variant | Response contacts backup, informs parties, reschedules, records impact and roster action. | preserve service |
| mediateops.continuity.system_outage | Mediation system outage | invariant | Outage uses paper schedule, secure notes, phone confirmations and later entry. | continue operations |
| mediateops.outreach.community_referral | Mediation community referral outreach | variant | Outreach explains services, eligibility, neutrality, limits and referral process to partners. | build pipeline |
