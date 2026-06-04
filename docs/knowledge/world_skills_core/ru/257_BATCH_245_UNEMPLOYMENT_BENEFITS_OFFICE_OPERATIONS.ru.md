# BATCH_245 — Unemployment Benefits Office Operations Detail
# world_skills_core · source: world_skills_core:batch_245:unemployment_benefits_office_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| unemployops.claim.initial_claim | Unemployment initial claim | invariant | Claim records claimant identity, employment history, separation, wages and contact. | start benefits case |
| unemployops.claim.identity_proof | Unemployment identity proof | invariant | Proof verifies claimant identity through approved documents, systems or checks. | prevent misidentity |
| unemployops.claim.employer_notice | Unemployment employer notice | invariant | Notice asks employer to confirm wages, dates, separation reason and protest. | gather facts |
| unemployops.claim.effective_date | Unemployment claim effective date | invariant | Date anchors benefit year, waiting week, filing period and payment eligibility. | timeline control |
| unemployops.claim.channel_support | Unemployment claim channel support | variant | Support helps claimant file by web, phone, office, language line or assisted service. | access |
| unemployops.eligibility.base_period | Unemployment base period review | invariant | Review checks wages and covered employment in the applicable measurement period. | monetary eligibility |
| unemployops.eligibility.separation_issue | Unemployment separation issue | invariant | Issue records layoff, quit, discharge, labor dispute or other separation facts. | adjudication input |
| unemployops.eligibility.able_available | Able and available review | invariant | Review checks ability to work, availability, restrictions and work search obligations. | ongoing eligibility |
| unemployops.eligibility.work_search | Unemployment work search record | invariant | Record captures contacts, applications, activities, exemptions and audit trail. | verify effort |
| unemployops.eligibility.partial_earnings | Partial earnings report | variant | Report records wages, hours, self-employment or gig income for benefit adjustment. | correct payment |
| unemployops.documents.document_request | Unemployment document request | invariant | Request asks for paystubs, ID, separation notice, medical restriction or work authorization. | complete file |
| unemployops.documents.upload_intake | Unemployment document upload intake | invariant | Intake records file type, claimant, date, case, readability and virus scan status. | manage evidence |
| unemployops.documents.missing_document | Missing unemployment document | invariant | Record tracks missing item, deadline, reminder, consequence and received status. | avoid delay |
| unemployops.documents.translation_need | Unemployment document translation need | variant | Need routes non-English or unclear document to translation or language support. | understand evidence |
| unemployops.adjudication.issue_queue | Unemployment adjudication issue queue | invariant | Queue prioritizes separation, availability, wages, fraud, overpayment or employer protest. | manage workload |
| unemployops.adjudication.fact_finding | Unemployment fact finding | invariant | Fact finding gathers claimant, employer, documents, timelines and contradictions. | decide fairly |
| unemployops.adjudication.determination | Unemployment determination | invariant | Determination states eligible, ineligible, disqualified, pending or adjusted with reason. | official decision |
| unemployops.adjudication.notice_of_decision | Unemployment notice of decision | invariant | Notice communicates facts, law basis, effect, appeal rights and deadlines. | due process |
| unemployops.adjudication.reopen_claim | Reopen unemployment claim | variant | Reopen handles break in filing, return to work, new separation or missed certifications. | restore case |
| unemployops.certification.weekly_cert | Weekly unemployment certification | invariant | Certification records unemployment status, work search, earnings, availability and job refusal. | authorize payment |
| unemployops.certification.late_cert | Late unemployment certification | variant | Certification records reason for late filing and whether week can be accepted. | handle exceptions |
| unemployops.certification.job_refusal | Job refusal issue | invariant | Issue records job offer, suitability, reason refused, employer contact and decision route. | eligibility control |
| unemployops.payments.payment_release | Unemployment payment release | invariant | Release sends approved benefit amount, week, method, deductions and hold status. | pay claimant |
| unemployops.payments.payment_hold | Unemployment payment hold | invariant | Hold stops payment for unresolved issue, identity, earnings, appeal or fraud concern. | prevent improper pay |
| unemployops.payments.direct_deposit | Unemployment direct deposit setup | variant | Setup records bank validation, claimant authorization, changes and failed deposits. | payment channel |
| unemployops.payments.debit_card | Unemployment debit card issuance | variant | Issuance records card order, address, activation issue, replacement and fraud notice. | payment access |
| unemployops.payments.overpayment | Unemployment overpayment record | invariant | Record captures cause, amount, fault status, notices, waiver, repayment and offset. | recover funds |
| unemployops.appeal.appeal_intake | Unemployment appeal intake | invariant | Intake records appellant, decision, date, timeliness, issues and hearing preference. | start review |
| unemployops.appeal.hearing_packet | Unemployment hearing packet | invariant | Packet contains decision, evidence, parties, notices, exhibits and instructions. | prepare hearing |
| unemployops.appeal.hearing_schedule | Unemployment hearing schedule | invariant | Schedule coordinates parties, interpreter, officer, evidence deadline and notice. | due process |
| unemployops.appeal.appeal_decision | Unemployment appeal decision | invariant | Decision affirms, reverses, remands or modifies determination with reasoning. | final action |
| unemployops.fraud.identity_flag | Unemployment identity fraud flag | invariant | Flag captures suspicious identity, duplicate claim, breached credentials or mismatched data. | protect program |
| unemployops.fraud.employer_mismatch | Employer wage mismatch flag | variant | Flag compares reported earnings, employer records, wage files and claimant statements. | find errors |
| unemployops.fraud.crossmatch_hit | Unemployment crossmatch hit | invariant | Hit identifies incarceration, death, new hire, wages, duplicate state or other disqualifying signal. | fraud control |
| unemployops.fraud.investigation_case | Unemployment fraud investigation | variant | Case records evidence, interviews, findings, referral, penalty and recovery action. | resolve fraud |
| unemployops.service.call_center_case | Unemployment call center case | variant | Case records question, authentication, issue type, response, escalation and callback. | claimant service |
| unemployops.service.appointment | Unemployment office appointment | variant | Appointment schedules in-person or virtual help for complex filing or identity issue. | guided service |
| unemployops.service.language_access | Unemployment language access | invariant | Access provides interpreter, translated notice, bilingual staff or alternate format. | fair service |
| unemployops.service.escalation | Unemployment case escalation | invariant | Escalation routes hardship, legislative inquiry, overdue issue or system error to specialist. | unblock case |
| unemployops.reporting.backlog_report | Unemployment backlog report | invariant | Report summarizes pending claims, adjudication age, appeals, calls and payment holds. | manage office |
| unemployops.reporting.timeliness_report | Unemployment timeliness report | invariant | Report tracks first payment, determination, appeal, call and document processing times. | oversight |
| unemployops.quality.case_review | Unemployment case quality review | invariant | Review checks evidence, notices, law application, payments and audit trail. | improve accuracy |
| unemployops.metrics.unemployment_kpi | Unemployment benefits KPI | variant | KPI tracks claims, payment timeliness, adjudication backlog, appeals, fraud hits and satisfaction. | manage benefits |
| unemployops.continuity.claim_surge | Unemployment claim surge response | variant | Response adds staffing, triage, communications, automation and policy guidance for volume spike. | preserve service |
