# BATCH_253 — Legal Aid Clinic Operations Detail
# world_skills_core · source: world_skills_core:batch_253:legal_aid_clinic_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| legalaid.intake.contact_channel | Legal aid contact channel | invariant | Channel records phone, web, walk-in, referral, outreach, mail or court clinic request. | receive client |
| legalaid.intake.client_profile | Legal aid client profile | invariant | Profile captures identity, contact, language, household, safe contact and accessibility needs. | client record |
| legalaid.intake.urgent_issue | Legal aid urgent issue flag | invariant | Flag identifies deadline, eviction, safety, benefits cutoff, court date or limitation risk. | triage quickly |
| legalaid.intake.consent_notice | Legal aid intake consent notice | invariant | Notice explains confidentiality, limits, data use, no guarantee and representation status. | informed intake |
| legalaid.eligibility.income_screen | Legal aid income screen | invariant | Screen records income, household size, benefits, assets and eligibility threshold. | qualify client |
| legalaid.eligibility.asset_screen | Legal aid asset screen | variant | Screen checks savings, property, vehicles or other resources when program rules require. | eligibility |
| legalaid.eligibility.residency_check | Legal aid residency check | variant | Check verifies service area, county, state, immigration-sensitive limits or program geography. | route correctly |
| legalaid.eligibility.conflict_check | Legal aid conflict check | invariant | Check searches opposing parties, prior clients, staff relationships and adverse interests. | protect ethics |
| legalaid.eligibility.denial_notice | Legal aid denial notice | invariant | Notice explains ineligibility, conflict, capacity, scope limit and referral options. | close respectfully |
| legalaid.issue.issue_screen | Legal aid issue screen | invariant | Screen categorizes housing, family, benefits, consumer, immigration, employment or elder issue. | route expertise |
| legalaid.issue.case_priority | Legal aid case priority | variant | Priority considers harm, deadline, vulnerability, merit, resources and strategic impact. | allocate scarce help |
| legalaid.issue.scope_decision | Legal aid scope decision | invariant | Decision defines advice only, brief service, limited representation, full case or referral. | set boundaries |
| legalaid.issue.nonlegal_need | Legal aid nonlegal need | variant | Need records housing, food, safety, healthcare, documents or social service referral. | holistic support |
| legalaid.appointment.appointment_schedule | Legal aid appointment schedule | invariant | Schedule sets attorney, advocate, time, channel, interpreter and document needs. | plan service |
| legalaid.appointment.no_show | Legal aid appointment no-show | invariant | Record tracks missed appointment, outreach attempt, reschedule and closure rule. | manage capacity |
| legalaid.appointment.interpreter_booking | Legal aid interpreter booking | variant | Booking matches language, confidentiality, date, channel and billing if any. | meaningful access |
| legalaid.appointment.remote_consult | Legal aid remote consultation | variant | Consult records identity check, privacy, platform, documents and advice note. | remote service |
| legalaid.documents.document_request | Legal aid document request | invariant | Request lists notices, leases, orders, bills, letters, IDs, evidence and deadlines. | prepare case |
| legalaid.documents.document_review | Legal aid document review | invariant | Review extracts facts, dates, parties, claims, defenses, deadlines and missing items. | understand issue |
| legalaid.documents.scan_index | Legal aid scan and index | invariant | Index stores documents by client, matter, type, date, source and confidentiality. | retrievable file |
| legalaid.documents.client_upload | Legal aid client upload | variant | Upload receives files, checks readability, confirms receipt and routes to matter. | digital intake |
| legalaid.advice.advice_note | Legal aid advice note | invariant | Note records issue, facts, options, warnings, referrals and next steps. | service record |
| legalaid.advice.self_help_packet | Legal aid self-help packet | variant | Packet gives approved forms, instructions, resources, deadlines and limits of help. | empower client |
| legalaid.advice.safety_planning | Legal aid safety planning referral | variant | Referral connects client to safety, shelter, protection order or advocate support. | reduce harm |
| legalaid.representation.retain_decision | Legal aid representation decision | invariant | Decision records acceptance, scope, attorney, conflicts, deadlines and engagement terms. | open case |
| legalaid.representation.engagement_letter | Legal aid engagement letter | invariant | Letter states scope, client duties, communication, termination and confidentiality. | define relationship |
| legalaid.representation.limited_scope | Limited-scope legal aid | variant | Scope limits help to pleading, hearing, negotiation, advice or document review. | clear boundary |
| legalaid.representation.case_assignment | Legal aid case assignment | invariant | Assignment links attorney, paralegal, advocate, supervisor and workload. | staff case |
| legalaid.referral.referral_directory | Legal aid referral directory | invariant | Directory lists agencies, attorneys, clinics, shelters, benefits offices and courts. | route help |
| legalaid.referral.warm_referral | Legal aid warm referral | variant | Referral contacts partner with client consent and essential facts. | reduce drop-off |
| legalaid.referral.pro_bono_referral | Pro bono referral | variant | Referral sends screened matter to volunteer attorney with scope and packet. | extend capacity |
| legalaid.closure.case_closure | Legal aid case closure | invariant | Closure records outcome, work completed, documents returned, referrals and closing letter. | end matter |
| legalaid.closure.withdrawal | Legal aid withdrawal | variant | Withdrawal documents reason, notice, court permission if needed and deadlines. | ethical exit |
| legalaid.closure.outcome_code | Legal aid outcome code | invariant | Code classifies advice, settlement, dismissal, order, benefits restored or referral. | reporting |
| legalaid.quality.supervisory_review | Legal aid supervisory review | invariant | Review checks eligibility, conflicts, advice quality, deadlines, notes and closure. | quality control |
| legalaid.quality.deadline_tickler | Legal aid deadline tickler | invariant | Tickler tracks court dates, filing deadlines, response dates and follow-ups. | prevent harm |
| legalaid.quality.confidentiality_check | Legal aid confidentiality check | invariant | Check protects files, conversations, safe contact details and adverse party access. | client safety |
| legalaid.reporting.grant_report | Legal aid grant report | variant | Report summarizes clients, issues, outcomes, demographics, hours and funding restrictions. | funder accountability |
| legalaid.reporting.service_volume | Legal aid service volume report | invariant | Report tracks intakes, denials, advice, briefs, full cases, closures and backlog. | manage clinic |
| legalaid.metrics.legalaid_kpi | Legal aid clinic KPI | variant | KPI tracks eligibility rate, wait time, urgent cases, outcomes, referrals and capacity. | manage service |
| legalaid.continuity.clinic_surge | Legal aid clinic surge response | variant | Response adds triage, clinics, volunteers, templates and partner referrals for demand spike. | handle volume |
| legalaid.continuity.system_outage | Legal aid system outage | invariant | Outage uses paper intake, conflict fallback, secure storage and later data entry. | continue service |
| legalaid.outreach.clinic_event | Legal aid outreach clinic event | variant | Event coordinates site, topic, staffing, screening, materials, privacy and follow-up. | reach community |
| legalaid.communication.safe_contact | Legal aid safe contact protocol | invariant | Protocol records when, how and whether messages may be left safely. | protect clients |
