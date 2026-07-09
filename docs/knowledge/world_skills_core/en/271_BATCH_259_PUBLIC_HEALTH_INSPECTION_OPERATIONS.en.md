# BATCH_259 — Public Health Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_259:public_health_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| healthinsp.complaint.intake | Public health complaint intake | invariant | Intake records complainant, site, concern, exposure, dates, photos and contact preference. | start investigation |
| healthinsp.complaint.anonymous | Anonymous health complaint | variant | Complaint preserves anonymity while capturing enough location, hazard and timing detail. | enable action |
| healthinsp.complaint.duplicate_link | Health complaint duplicate link | invariant | Link connects repeated complaints about the same site, event, hazard or operator. | avoid fragmentation |
| healthinsp.complaint.jurisdiction_check | Health inspection jurisdiction check | invariant | Check confirms agency authority, facility type, geography and referral path. | route correctly |
| healthinsp.risk.risk_ranking | Public health risk ranking | invariant | Ranking considers severity, population exposed, vulnerable groups, history and immediacy. | prioritize field work |
| healthinsp.risk.hazard_category | Public health hazard category | invariant | Category identifies food, housing, water, vector, sewage, nuisance, school or event risk. | choose protocol |
| healthinsp.risk.response_time | Health inspection response time | invariant | Time standard sets urgent, routine, scheduled or referral response target. | meet obligations |
| healthinsp.schedule.inspection_assignment | Public health inspection assignment | invariant | Assignment links inspector, case, site, priority, protocol, equipment and due date. | organize work |
| healthinsp.schedule.preinspection_review | Public health pre-inspection review | invariant | Review checks permits, history, prior violations, complaints, maps and contacts. | arrive prepared |
| healthinsp.schedule.access_plan | Health inspection access plan | variant | Plan defines entry route, appointment, authority, interpreter, safety and after-hours access. | field readiness |
| healthinsp.field.site_entry | Public health site entry | invariant | Entry records arrival, credentials, responsible person, purpose, scope and consent or authority. | lawful inspection |
| healthinsp.field.observation_log | Public health observation log | invariant | Log records conditions, measurements, photos, statements, documents and locations. | evidence trail |
| healthinsp.field.interview_note | Public health interview note | variant | Note captures operator, resident, worker, witness or complainant statements. | context |
| healthinsp.field.sampling_decision | Public health sampling decision | variant | Decision selects whether to collect food, water, surface, air, vector or other sample. | evidence choice |
| healthinsp.field.immediate_hazard | Immediate health hazard | invariant | Hazard triggers containment, closure, embargo, referral or urgent corrective order. | protect public |
| healthinsp.sampling.sample_chain | Public health sample chain | invariant | Chain records sample ID, location, time, collector, preservation, transport and lab. | defensible sample |
| healthinsp.sampling.field_measurement | Public health field measurement | invariant | Measurement records temperature, sanitizer, pH, chlorine, moisture, CO or other reading. | quantify condition |
| healthinsp.sampling.lab_result | Public health lab result | invariant | Result links sample, method, finding, threshold, interpretation and follow-up action. | guide enforcement |
| healthinsp.violations.violation_code | Public health violation code | invariant | Code maps observed condition to rule, severity, correction deadline and evidence. | consistent citation |
| healthinsp.violations.critical_violation | Critical health violation | invariant | Violation presents immediate risk such as contamination, no water, sewage or dangerous exposure. | urgent correction |
| healthinsp.violations.repeat_violation | Repeat health violation | variant | Violation repeats prior finding and may escalate enforcement or reinspection frequency. | address pattern |
| healthinsp.orders.correction_order | Public health correction order | invariant | Order states violation, required correction, deadline, responsible party and appeal rights. | compel fix |
| healthinsp.orders.closure_order | Public health closure order | variant | Order closes site, activity or area until hazard is corrected and clearance obtained. | stop exposure |
| healthinsp.orders.embargo_hold | Public health embargo hold | variant | Hold prevents use, sale or disposal of suspected unsafe goods pending decision. | preserve control |
| healthinsp.followup.reinspection_schedule | Public health reinspection schedule | invariant | Schedule sets follow-up date by risk, deadline, correction claim and availability. | verify correction |
| healthinsp.followup.correction_proof | Public health correction proof | invariant | Proof includes photo, receipt, lab result, work order, statement or field verification. | close violation |
| healthinsp.followup.noncompliance | Public health noncompliance | invariant | Noncompliance records missed deadline, refusal, continued hazard or inadequate correction. | escalate case |
| healthinsp.enforcement.notice_of_violation | Public health notice of violation | invariant | Notice documents facts, rules, deadlines, penalties, hearing rights and contact. | formal enforcement |
| healthinsp.enforcement.administrative_hearing | Health administrative hearing | variant | Hearing record tracks notice, evidence, parties, decision, penalty and appeal route. | due process |
| healthinsp.enforcement.referral | Public health enforcement referral | variant | Referral sends case to legal, environmental, housing, building, police or state agency. | coordinate authority |
| healthinsp.communication.operator_notice | Health inspection operator notice | invariant | Notice communicates findings, required actions, deadlines, reopening criteria and contacts. | clear expectations |
| healthinsp.communication.public_notice | Public health public notice | variant | Notice informs affected public about closure, exposure, advisory, recall or unsafe condition. | risk communication |
| healthinsp.communication.language_access | Health inspection language access | variant | Access provides interpreter, translated forms, plain-language explanation and follow-up. | fair process |
| healthinsp.records.inspection_report | Public health inspection report | invariant | Report summarizes site, observations, violations, samples, orders, photos and next steps. | official record |
| healthinsp.records.photo_log | Health inspection photo log | invariant | Log links photos to date, location, condition, violation and inspector. | evidence organization |
| healthinsp.records.case_file | Public health inspection case file | invariant | File stores complaint, assignment, notes, samples, reports, orders, correspondence and closure. | case memory |
| healthinsp.quality.supervisor_review | Public health inspection supervisor review | invariant | Review checks jurisdiction, evidence, violations, orders, deadlines and closure quality. | reduce errors |
| healthinsp.quality.calibration_check | Health inspection equipment calibration | invariant | Check tracks thermometer, meter, sampling kit or detector readiness and calibration. | reliable measurements |
| healthinsp.safety.field_safety | Public health inspector field safety | invariant | Safety covers animals, hostility, traffic, confined spaces, chemicals and buddy system. | protect staff |
| healthinsp.reporting.program_report | Public health inspection program report | variant | Report summarizes complaints, inspections, violations, closures, samples and enforcement. | oversight |
| healthinsp.metrics.healthinsp_kpi | Public health inspection KPI | variant | KPI tracks response time, closure rate, repeat violations, reinspections, samples and appeals. | manage program |
| healthinsp.continuity.outbreak_surge | Public health outbreak inspection surge | variant | Surge plan reallocates inspectors, templates, sampling, communication and partner coordination. | handle crisis |
| healthinsp.close.case_closure | Public health inspection case closure | invariant | Closure records corrected, referred, unfounded, unresolved, legal action or advisory issued. | end case |
| healthinsp.audit.audit_trail | Public health inspection audit trail | invariant | Trail records user, date, change, evidence, order and closure actions. | accountability |
