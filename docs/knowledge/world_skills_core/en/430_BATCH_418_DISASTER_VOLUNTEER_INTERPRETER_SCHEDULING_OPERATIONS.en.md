# BATCH 418: Disaster Volunteer Interpreter Scheduling Operations

**KnowledgeUnits:** 44  
**Namespace:** `interpvolops.*`  
**Scope:** language requests, credentials, assignments, confidentiality, no-shows and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| interpvolops.intake.request_source | request source | RECORD | Source records shelter, clinic, benefits desk, hotline, legal clinic or field team. | Shows demand origin. |
| interpvolops.intake.language | language request | RECORD | Request captures language, dialect, modality, urgency, topic and preferred channel. | Defines need. |
| interpvolops.intake.service_context | service context | RECORD | Context distinguishes registration, medical, legal, benefits, reunification, outreach or briefing. | Routes skill. |
| interpvolops.intake.urgency | urgency model | MODEL | Urgency weighs life safety, legal deadline, medical need, appointment time and wait duration. | Prioritizes assignment. |
| interpvolops.volunteer.profile | volunteer profile | RECORD | Profile captures name, contact, languages, availability, location and remote capacity. | Builds roster. |
| interpvolops.volunteer.language_level | language level | QUALITY_CHECK | Language level records self-report, test, credential, reference or prior performance. | Matches complexity. |
| interpvolops.volunteer.specialty | specialty tag | RECORD | Specialty tags legal, medical, mental health, benefits, child services or general support. | Improves fit. |
| interpvolops.volunteer.availability | availability record | RECORD | Availability lists shifts, time zone, travel limits and blackout periods. | Supports scheduling. |
| interpvolops.credentials.credential_check | credential check | QUALITY_CHECK | Credential check verifies certification, training, background or agency approval if required. | Controls quality. |
| interpvolops.credentials.scope_limit | scope limit | CONSTRAINT | Scope limit prevents unqualified volunteers handling specialized or high-risk topics. | Reduces harm. |
| interpvolops.credentials.conflict | conflict check | QUALITY_CHECK | Conflict check screens family ties, adverse parties or confidentiality concerns. | Protects neutrality. |
| interpvolops.credentials.badge | badge record | RECORD | Badge or access record controls site entry and role identification. | Enables deployment. |
| interpvolops.assignment.matching | assignment matching | METHOD | Matching considers language, specialty, urgency, availability, location and modality. | Fills request. |
| interpvolops.assignment.assignment_record | assignment record | RECORD | Record stores request, volunteer, site, time, contact, topic and supervisor. | Creates schedule. |
| interpvolops.assignment.remote_link | remote link | RECORD | Remote link captures phone/video details, backup number and privacy setup. | Enables remote support. |
| interpvolops.assignment.standby | standby pool | METHOD | Standby pool covers high-demand languages and urgent no-show replacement. | Adds resilience. |
| interpvolops.confidentiality.brief | confidentiality brief | SAFETY_RULE | Volunteers receive confidentiality, impartiality and role-boundary briefing. | Protects clients. |
| interpvolops.confidentiality.acknowledgement | acknowledgement | RECORD | Acknowledgement records volunteer agreement to confidentiality and conduct rules. | Creates proof. |
| interpvolops.confidentiality.private_space | private space | METHOD | Sessions use private area or secure remote setup where needed. | Preserves dignity. |
| interpvolops.confidentiality.data_minimum | data minimum | SAFETY_RULE | Schedule stores only necessary client, topic and contact details. | Reduces exposure. |
| interpvolops.shift.checkin | volunteer check-in | RECORD | Check-in confirms arrival, assignment, badge, briefing and contact method. | Starts shift. |
| interpvolops.shift.handoff | shift handoff | METHOD | Handoff lists pending requests, urgent languages, no-shows and sensitive limits. | Maintains continuity. |
| interpvolops.shift.breaks | break planning | METHOD | Breaks prevent fatigue during long or emotionally intense interpreting. | Maintains quality. |
| interpvolops.shift.checkout | volunteer checkout | RECORD | Checkout records completed assignments, issues, hours and next availability. | Closes shift. |
| interpvolops.noshow.volunteer_noshow | volunteer no-show | RECORD | No-show records missed assignment, contact attempts, replacement and reason. | Improves reliability. |
| interpvolops.noshow.client_noshow | client no-show | RECORD | Client no-show records wait time, contact attempts and reschedule need. | Keeps queue accurate. |
| interpvolops.noshow.replacement | replacement process | METHOD | Replacement searches standby, remote option or partner provider. | Preserves service. |
| interpvolops.noshow.pattern_review | pattern review | QUALITY_CHECK | Repeated no-shows are reviewed for roster status or scheduling changes. | Improves roster. |
| interpvolops.outcome.completed | completed session | RECORD | Completion records time served, topic category, modality and next step. | Tracks output. |
| interpvolops.outcome.referred | referred request | METHOD | Requests beyond scope route to certified interpreter, agency or specialist. | Maintains quality. |
| interpvolops.outcome.unfilled | unfilled request | RECORD | Unfilled records language, urgency, reason, wait time and escalation. | Shows gaps. |
| interpvolops.outcome.feedback | feedback record | RECORD | Feedback captures staff/client concerns about clarity, neutrality or access. | Improves service. |
| interpvolops.communication.requester_update | requester update | METHOD | Requester receives assignment, delay, replacement or unfilled status. | Reduces uncertainty. |
| interpvolops.communication.volunteer_notice | volunteer notice | METHOD | Volunteer receives location, time, topic, role limits, parking and contact. | Prepares shift. |
| interpvolops.communication.language_gap | language gap alert | METHOD | Gap alert asks partners for rare language support or remote provider. | Expands capacity. |
| interpvolops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports requests, filled, unfilled, languages, hours and no-shows. | Informs command. |
| interpvolops.metrics.fill_rate | fill rate | MEASUREMENT | Fill rate tracks completed assignments versus requests by language. | Shows coverage. |
| interpvolops.metrics.response_time | response time | MEASUREMENT | Response time measures request to assignment or unfilled decision. | Reveals delay. |
| interpvolops.metrics.no_show_rate | no-show rate | MEASUREMENT | No-show rate tracks volunteer and client no-shows by context. | Improves scheduling. |
| interpvolops.qa.session_review | session review | QUALITY_CHECK | Review samples assignments for credential fit, confidentiality and outcome completeness. | Improves reliability. |
| interpvolops.qa.roster_audit | roster audit | QUALITY_CHECK | Audit checks active volunteers, credentials, availability and conduct issues. | Keeps roster current. |
| interpvolops.records.case_log | case log | RECORD | Log stores request, assignment, credential fit, attendance, outcome and follow-up notes. | Preserves continuity. |
| interpvolops.records.retention | retention rule | CONSTRAINT | Records follow privacy, volunteer, legal and emergency retention schedules. | Controls lifecycle. |
| interpvolops.review.after_action | after-action review | METHOD | Review captures language gaps, credential limits, no-shows, remote support and confidentiality lessons. | Improves future scheduling. |
