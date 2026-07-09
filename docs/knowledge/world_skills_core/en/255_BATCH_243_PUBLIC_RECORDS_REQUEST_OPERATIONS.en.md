# BATCH_243 — Public Records Request Operations Detail
# world_skills_core · source: world_skills_core:batch_243:public_records_request_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| recordsreq.intake.request_channel | Public records request channel | invariant | Channel captures web, email, mail, walk-in, phone or portal submission. | receive request |
| recordsreq.intake.requester_profile | Public records requester profile | variant | Profile records requester contact, organization, communication preference and fee status. | route communications |
| recordsreq.intake.scope_statement | Records request scope statement | invariant | Statement defines requested records, date range, departments, keywords and format. | clarify search |
| recordsreq.intake.date_received | Records request date received | invariant | Date starts statutory response clock, acknowledgement and tracking timeline. | deadline control |
| recordsreq.intake.clarification_needed | Records request clarification | invariant | Clarification asks requester to narrow ambiguous, broad or unclear terms. | searchable scope |
| recordsreq.tracking.case_number | Public records case number | invariant | Number links request, correspondence, search tasks, fees, releases and appeals. | case control |
| recordsreq.tracking.deadline_clock | Public records deadline clock | invariant | Clock tracks acknowledgement, estimate, production, extension and appeal deadlines. | compliance |
| recordsreq.tracking.extension_notice | Records request extension notice | variant | Notice explains lawful reason, new date, scope and contact path. | manage time |
| recordsreq.tracking.status_update | Records request status update | invariant | Update records received, searching, reviewing, fee pending, produced, denied or closed. | transparency |
| recordsreq.search.custodian_assignment | Records custodian assignment | invariant | Assignment routes search to department, official, system owner or archive. | find records |
| recordsreq.search.search_instruction | Records search instruction | invariant | Instruction gives scope, keywords, systems, date ranges and preservation expectations. | consistent search |
| recordsreq.search.email_search | Public records email search | variant | Search queries mailbox, archive, subject, sender, recipient, date and attachments. | retrieve email |
| recordsreq.search.casefile_search | Public records casefile search | variant | Search examines permits, complaints, contracts, agendas, logs or case management systems. | retrieve files |
| recordsreq.search.no_record_cert | No-record certification | invariant | Certification documents searched locations, custodians, terms and no responsive records. | support closure |
| recordsreq.search.search_log | Public records search log | invariant | Log records who searched, where, when, terms used and result count. | audit trail |
| recordsreq.exemption.exemption_review | Public records exemption review | invariant | Review identifies legal exemptions, privacy limits, privilege and required withholding basis. | lawful release |
| recordsreq.exemption.privacy_screen | Records privacy screen | invariant | Screen flags personal identifiers, health, juvenile, security or protected contact information. | protect privacy |
| recordsreq.exemption.privilege_claim | Records privilege claim | variant | Claim records attorney-client, deliberative, investigation or other privileged material basis. | controlled withholding |
| recordsreq.exemption.security_risk | Records security risk review | variant | Review checks facility maps, credentials, vulnerabilities, emergency plans or protected infrastructure details. | avoid exposure |
| recordsreq.exemption.segmentation | Records segmentation | invariant | Segmentation separates releasable from exempt portions before denial or redaction. | maximize release |
| recordsreq.redaction.redaction_queue | Public records redaction queue | invariant | Queue organizes responsive records by review priority, volume, format and deadline. | manage workload |
| recordsreq.redaction.redaction_mark | Redaction mark | invariant | Mark blocks exempt text, image, audio or metadata while preserving context. | protect content |
| recordsreq.redaction.redaction_reason | Redaction reason code | invariant | Code links each withheld portion to exemption, reviewer and explanation. | defensible redaction |
| recordsreq.redaction.quality_check | Records redaction quality check | invariant | Check confirms no hidden text, metadata, layers or missed protected details remain. | prevent leakage |
| recordsreq.redaction.version_control | Records redaction version control | variant | Control preserves original, review copy, redacted copy and released copy separately. | evidence control |
| recordsreq.fees.fee_estimate | Public records fee estimate | variant | Estimate calculates search, review, copies, media, postage or special service charges. | inform requester |
| recordsreq.fees.deposit_request | Public records deposit request | variant | Request asks for allowed prepayment before large search, copy or production work. | recover costs |
| recordsreq.fees.fee_waiver | Public records fee waiver | variant | Waiver records public-interest, hardship, media, agency or discretionary fee decision. | fair access |
| recordsreq.fees.payment_record | Public records payment record | invariant | Record links invoice, payment, refund, receipt and release timing. | financial trail |
| recordsreq.production.production_format | Records production format | invariant | Format defines PDF, native file, spreadsheet, paper, audio, video or inspection access. | deliver usable records |
| recordsreq.production.delivery_package | Public records delivery package | invariant | Package includes records, redaction log, cover letter, fee receipt and instructions. | complete response |
| recordsreq.production.portal_release | Records portal release | variant | Release uploads files, access link, expiry, download confirmation and privacy notices. | digital delivery |
| recordsreq.production.partial_release | Public records partial release | variant | Release provides available records while review continues on remaining records. | reduce delay |
| recordsreq.production.inspection_session | Records inspection session | variant | Session schedules on-site review, supervision, copying rules and materials control. | controlled access |
| recordsreq.denial.denial_letter | Public records denial letter | invariant | Letter states denied records, exemption basis, appeal rights and contact. | explain refusal |
| recordsreq.denial.no_responsive_records | No responsive records response | invariant | Response explains search completed and no matching records were located. | close request |
| recordsreq.denial.withdrawn_request | Withdrawn records request | variant | Closure records requester withdrawal, nonpayment, no clarification or abandoned request. | clean queue |
| recordsreq.appeal.appeal_intake | Public records appeal intake | invariant | Intake records appeal basis, request case, date, appellant and required reviewer. | review dispute |
| recordsreq.appeal.appeal_record | Public records appeal record | invariant | Record tracks review, decision, revised release, denial upheld or litigation referral. | appeal trail |
| recordsreq.governance.retention_hold | Records request retention hold | invariant | Hold preserves request file, search logs, originals, redactions and correspondence. | defend process |
| recordsreq.governance.metrics_report | Public records metrics report | variant | Report tracks volume, age, closures, fees, exemptions, appeals and overdue cases. | manage office |
| recordsreq.governance.template_library | Public records template library | variant | Library stores approved acknowledgement, clarification, extension, fee, release and denial templates. | consistent language |
| recordsreq.metrics.records_request_kpi | Public records request KPI | variant | KPI tracks response time, backlog, pages released, appeals, fees and requester satisfaction. | improve service |
| recordsreq.continuity.bulk_request | Public records bulk request response | variant | Response plans staffing, batching, estimates, partial releases and leadership updates. | handle surge |
