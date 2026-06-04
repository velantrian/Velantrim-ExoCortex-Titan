# BATCH_255 — Court Interpreter Scheduling Operations Detail
# world_skills_core · source: world_skills_core:batch_255:court_interpreter_scheduling_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| interpops.request.language_request | Court interpreter language request | invariant | Request records language, dialect, case, party, proceeding, date and urgency. | start assignment |
| interpops.request.source_channel | Interpreter request source channel | variant | Channel identifies judge, clerk, attorney, self-represented party, agency or portal. | route request |
| interpops.request.dialect_detail | Court interpreter dialect detail | variant | Detail captures regional dialect, sign language mode, relay need or special terminology. | match accurately |
| interpops.request.case_context | Interpreter case context | invariant | Context lists case type, proceeding, expected duration, parties and confidentiality level. | prepare interpreter |
| interpops.request.priority_flag | Interpreter scheduling priority flag | invariant | Flag marks custody, protection order, emergency, juvenile, trial or statutory deadline matter. | triage coverage |
| interpops.credentials.certification_check | Court interpreter certification check | invariant | Check verifies credential, language pair, court authorization, expiration and standing. | qualified service |
| interpops.credentials.roster_profile | Court interpreter roster profile | invariant | Profile stores languages, credentials, availability, remote capacity, rates and restrictions. | assignment pool |
| interpops.credentials.conflict_history | Interpreter conflict history | variant | History records prior party contact, case involvement, employment or personal conflict. | avoid bias |
| interpops.credentials.oath_record | Interpreter oath record | invariant | Record confirms oath, confidentiality, accuracy duty and proceeding-specific requirements. | lawful interpretation |
| interpops.calendar.availability_block | Interpreter availability block | invariant | Block records date, time, location, language, remote status and travel constraints. | schedule work |
| interpops.calendar.assignment_hold | Interpreter assignment hold | variant | Hold reserves interpreter while court time, party need or funding approval is confirmed. | avoid double booking |
| interpops.calendar.double_booking_check | Interpreter double-booking check | invariant | Check compares calendar, travel time, remote sessions and backup coverage. | prevent conflict |
| interpops.calendar.continuance_update | Interpreter continuance update | invariant | Update cancels or reschedules interpreter after hearing date changes. | reduce waste |
| interpops.calendar.backup_interpreter | Backup interpreter plan | variant | Plan names alternate interpreter for trial, rare language, custody or long proceeding. | continuity |
| interpops.remote.remote_platform | Remote interpreting platform | variant | Platform record lists video link, phone bridge, security, test status and access details. | connect session |
| interpops.remote.tech_check | Interpreter remote tech check | invariant | Check verifies audio, video, headset, bandwidth, privacy and backup phone. | reliable session |
| interpops.remote.private_channel | Remote interpreting private channel | variant | Channel supports confidential attorney-client or party consultation when allowed. | preserve privacy |
| interpops.remote.failed_connection | Interpreter connection failure | invariant | Failure log records time, cause, participants, workaround and proceeding impact. | troubleshoot |
| interpops.assignment.matching_rule | Court interpreter matching rule | invariant | Rule matches language, credential, conflict status, location, gender if required and availability. | assign correctly |
| interpops.assignment.confirmation_notice | Interpreter confirmation notice | invariant | Notice sends assignment, court, room, time, case, contact and cancellation rule. | clear assignment |
| interpops.assignment.party_notice | Interpreter party notice | variant | Notice informs party or counsel that language access support is arranged. | reduce uncertainty |
| interpops.assignment.last_minute_request | Last-minute interpreter request | variant | Request triggers emergency roster, remote fallback, continuance note and supervisor review. | cover urgent need |
| interpops.conflict.conflict_screen | Court interpreter conflict screen | invariant | Screen checks party, attorney, witness, prior work, employment and personal relationships. | neutrality |
| interpops.conflict.conflict_disclosure | Interpreter conflict disclosure | invariant | Disclosure records issue, reviewer, decision, substitution or waiver if permitted. | transparent process |
| interpops.conflict.recusal_record | Interpreter recusal record | variant | Record captures interpreter withdrawal due to conflict, competence, fatigue or impartiality concern. | ethical action |
| interpops.billing.service_time | Interpreter service time | invariant | Time records arrival, start, end, waiting, travel and remote connection duration. | pay accurately |
| interpops.billing.rate_code | Interpreter rate code | variant | Code applies credential, language, in-person, remote, cancellation or overtime rate. | billing control |
| interpops.billing.invoice_review | Interpreter invoice review | invariant | Review compares assignment, timesheet, rate, cancellation, mileage and approval. | avoid overpayment |
| interpops.billing.grant_tracking | Language access grant tracking | variant | Tracking tags interpreter expense to grant, court program, case type or fund. | reporting |
| interpops.quality.feedback_note | Interpreter quality feedback | invariant | Note records clarity, punctuality, professionalism, complaints, technical issues and reviewer. | improve roster |
| interpops.quality.complaint_process | Interpreter complaint process | invariant | Process receives complaint, gathers facts, notifies reviewer and records outcome. | accountability |
| interpops.quality.competence_issue | Interpreter competence issue | variant | Issue flags terminology difficulty, dialect mismatch, ethical concern or performance problem. | protect record |
| interpops.quality.training_need | Interpreter training need | variant | Need identifies courtroom protocol, ethics, remote tools, trauma-informed or terminology training. | develop roster |
| interpops.records.assignment_log | Interpreter assignment log | invariant | Log records request, match, confirmation, attendance, changes, billing and notes. | audit trail |
| interpops.records.confidentiality_control | Interpreter confidentiality control | invariant | Control restricts access to sealed cases, minors, protected parties and sensitive notes. | protect privacy |
| interpops.records.record_retention | Interpreter scheduling record retention | invariant | Retention defines how long requests, invoices, rosters and complaints are kept. | compliance |
| interpops.operations.daily_docket_review | Interpreter daily docket review | invariant | Review checks next-day cases, languages, rooms, custody, remote links and gaps. | prevent misses |
| interpops.operations.courtroom_change | Interpreter courtroom change | variant | Change updates interpreter, clerk, courtroom, remote link and affected parties. | keep alignment |
| interpops.operations.rare_language_search | Rare language interpreter search | variant | Search contacts regional rosters, remote vendors, agencies and qualified backups. | cover uncommon need |
| interpops.reporting.coverage_report | Interpreter coverage report | invariant | Report summarizes requests, filled, unfilled, continuances, languages and costs. | manage access |
| interpops.reporting.unfilled_request | Unfilled interpreter request report | invariant | Report records reason, impact, alternatives attempted and corrective action. | expose gap |
| interpops.metrics.interpreter_kpi | Court interpreter scheduling KPI | variant | KPI tracks fill rate, late requests, cancellations, costs, complaints and remote failures. | manage program |
| interpops.continuity.interpreter_no_show | Interpreter no-show response | invariant | Response contacts backup, informs court, logs impact and updates roster review. | keep court moving |
| interpops.continuity.system_outage | Interpreter scheduling system outage | invariant | Outage plan uses manual docket, phone confirmations, paper logs and later entry. | maintain coverage |
