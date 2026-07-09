# BATCH_257 — Civil Process Service Operations Detail
# world_skills_core · source: world_skills_core:batch_257:civil_process_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| civilserv.intake.document_intake | Civil process document intake | invariant | Intake records court, case, parties, document type, deadline, fee and address. | start service |
| civilserv.intake.service_type | Civil process service type | invariant | Type identifies summons, subpoena, eviction, restraining order, writ or notice. | route correctly |
| civilserv.intake.fee_payment | Civil process fee payment | variant | Payment records amount, waiver, agency billing, refund and receipt. | financial trail |
| civilserv.intake.deadline_review | Civil service deadline review | invariant | Review checks return date, hearing date, statutory service window and priority. | avoid late service |
| civilserv.intake.address_quality | Civil service address quality | invariant | Quality check validates address, apartment, workplace, gate code, hazards and alternate leads. | improve attempts |
| civilserv.routing.route_assignment | Civil process route assignment | invariant | Assignment groups papers by geography, priority, officer, safety and deadline. | efficient service |
| civilserv.routing.priority_order | Civil process priority order | variant | Order ranks protection orders, evictions, short deadlines, subpoenas and routine papers. | focus work |
| civilserv.routing.officer_workload | Civil process officer workload | variant | Workload tracks active papers, attempts due, zones, court returns and safety flags. | balance routes |
| civilserv.attempt.service_attempt | Civil process service attempt | invariant | Attempt records date, time, location, person contacted, outcome and notes. | proof trail |
| civilserv.attempt.personal_service | Personal service | invariant | Service records direct delivery to named person with identity indicators. | valid service |
| civilserv.attempt.substitute_service | Substitute service | variant | Service records delivery to allowed substitute person, relationship and follow-up. | lawful alternative |
| civilserv.attempt.posting_service | Posting service | variant | Service records posting location, photo, witness and mailing if required. | eviction or notice path |
| civilserv.attempt.workplace_attempt | Workplace service attempt | variant | Attempt records employer access, privacy, work schedule, security and outcome. | find respondent |
| civilserv.attempt.failed_attempt | Failed service attempt | invariant | Attempt records no answer, bad address, moved, refused, unsafe or unable to locate. | explain failure |
| civilserv.affidavit.affidavit_create | Affidavit of service | invariant | Affidavit states who, what, when, where, how and under what authority served. | court proof |
| civilserv.affidavit.notarization | Civil service notarization | variant | Notarization verifies officer signature, date, identity and affidavit completeness. | formal filing |
| civilserv.affidavit.return_packet | Civil process return packet | invariant | Packet includes affidavit, unserved return, fees, notes and court filing route. | close paper |
| civilserv.affidavit.error_correction | Service affidavit correction | invariant | Correction fixes clerical error with supervisor review and audit trail. | reliable proof |
| civilserv.unserved.unserved_return | Civil process unserved return | invariant | Return states attempts, reasons, dates, locations, leads and next available action. | court update |
| civilserv.unserved.bad_address | Bad address finding | invariant | Finding records invalid, vacant, demolished, no such number or inaccessible address. | stop futile attempts |
| civilserv.unserved.evasion_note | Service evasion note | variant | Note records behavior suggesting evasion, facts observed and lawful next steps. | guide strategy |
| civilserv.unserved.forwarding_lead | Forwarding address lead | variant | Lead records new address, source, confidence, restrictions and requester notice. | improve service |
| civilserv.safety.hazard_flag | Civil process safety hazard flag | invariant | Flag records weapons, animals, threats, mental health crisis, terrain or prior violence. | protect officer |
| civilserv.safety.two_officer_service | Two-officer service plan | variant | Plan assigns backup for high-risk service, time, staging and communication. | safer attempt |
| civilserv.safety.law_enforcement_backup | Civil service law enforcement backup | variant | Backup coordinates agency support for writ, eviction, threat or court order. | reduce risk |
| civilserv.safety.incident_report | Civil process incident report | invariant | Report records threat, assault, chase, dog bite, crash, property issue or injury. | incident trail |
| civilserv.records.case_tracking | Civil process case tracking | invariant | Tracking links documents, attempts, fees, affidavits, returns and court status. | process visibility |
| civilserv.records.body_camera_note | Civil process body camera note | variant | Note records recording use, retention, incident link and disclosure restrictions. | evidence control |
| civilserv.records.confidential_address | Confidential address handling | invariant | Handling protects protected party, shelter, juvenile or sealed address information. | privacy |
| civilserv.records.document_custody | Civil process document custody | invariant | Custody tracks original papers, copies, officer possession, filing and disposal. | avoid loss |
| civilserv.court.return_filing | Civil process court return filing | invariant | Filing submits affidavit or unserved return to court by deadline and method. | complete court cycle |
| civilserv.court.court_rejection | Court return rejection | variant | Rejection records defect, correction, refiling, deadline risk and requester notice. | fix filing |
| civilserv.court.hearing_notice | Hearing notice service | variant | Service prioritizes hearing notice based on date, party type and required method. | preserve hearing |
| civilserv.finance.mileage_fee | Civil process mileage fee | variant | Fee records distance, zone, attempt count, billing rule and waiver. | charge properly |
| civilserv.finance.refund_request | Civil process refund request | variant | Request handles overpayment, cancellation, duplicate filing or unattempted service. | close finance |
| civilserv.quality.supervisor_review | Civil service supervisor review | invariant | Review checks attempts, affidavit wording, deadlines, safety and rejected returns. | quality control |
| civilserv.quality.attempt_pattern | Civil service attempt pattern | variant | Pattern reviews time-of-day spread, weekdays, weekends and alternate locations. | improve success |
| civilserv.reporting.daily_attempts | Civil process daily attempts report | invariant | Report summarizes served, unserved, attempts, hazards, deadlines and officer routes. | manage unit |
| civilserv.reporting.service_rate | Civil process service rate report | variant | Report compares served rate by document type, route, officer and address quality. | improve operations |
| civilserv.metrics.civil_service_kpi | Civil process service KPI | variant | KPI tracks timely service, attempts per paper, unserved rate, hazards, rejections and backlog. | manage service |
| civilserv.continuity.system_outage | Civil process system outage | invariant | Outage plan uses paper logs, manual assignment, secure custody and later entry. | continue service |
| civilserv.continuity.surge_workload | Civil process surge workload | variant | Surge plan reallocates routes, overtime, contractors, priority and court notices. | handle backlog |
| civilserv.communication.requester_update | Civil process requester update | invariant | Update informs requester of served, attempted, unserved, fee, defect or deadline status. | transparency |
| civilserv.communication.language_access | Civil process language access | variant | Access supports non-English parties for notices, questions and safe communication limits. | fair service |
