# BATCH_262 — Occupational Safety Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_262:occupational_safety_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| oshinsp.complaint.complaint_intake | Occupational safety complaint intake | invariant | Intake records workplace, hazard, workers exposed, timing, complainant status and contact. | start case |
| oshinsp.complaint.whistleblower_privacy | Safety complainant privacy | invariant | Privacy protects complainant identity and communication limits under applicable rules. | reduce retaliation risk |
| oshinsp.complaint.imminent_danger | Imminent danger flag | invariant | Flag identifies conditions that may cause death or serious harm before normal processing. | urgent response |
| oshinsp.complaint.jurisdiction | Safety inspection jurisdiction check | invariant | Check confirms employer, worksite, industry, agency authority and referral needs. | route correctly |
| oshinsp.plan.inspection_plan | Occupational safety inspection plan | invariant | Plan defines scope, standards, hazards, records, sampling, PPE and team. | prepare inspection |
| oshinsp.plan.site_entry_strategy | Worksite entry strategy | variant | Strategy covers arrival, credentials, employer representative, union or worker representative. | lawful entry |
| oshinsp.plan.history_review | Workplace safety history review | invariant | Review checks prior citations, injuries, complaints, programs and abatement. | target risks |
| oshinsp.entry.opening_conference | Safety inspection opening conference | invariant | Conference explains authority, scope, rights, process, records requested and walkaround. | align parties |
| oshinsp.entry.representative_selection | Worker representative selection | variant | Selection identifies authorized employee representative or alternate walkaround participant. | worker participation |
| oshinsp.entry.refusal_entry | Safety inspection entry refusal | invariant | Refusal record captures employer response, reason, legal step and preservation needs. | enforce authority |
| oshinsp.field.walkaround | Safety inspection walkaround | invariant | Walkaround observes operations, hazards, controls, worker exposure and employer practices. | gather evidence |
| oshinsp.field.hazard_photo | Occupational hazard photo | invariant | Photo links hazard, location, worker exposure, equipment, controls and timestamp. | evidence |
| oshinsp.field.worker_interview | Safety worker interview | invariant | Interview gathers task, exposure, training, incidents, controls and retaliation concern. | worker evidence |
| oshinsp.field.employer_interview | Safety employer interview | variant | Interview captures policies, supervision, controls, training, maintenance and explanations. | management evidence |
| oshinsp.field.document_request | Safety inspection document request | invariant | Request asks for logs, training, programs, monitoring, maintenance and injury records. | support findings |
| oshinsp.hazard.machine_guarding | Machine guarding hazard assessment | variant | Assessment reviews pinch points, guards, interlocks, lockout and exposure. | prevent injury |
| oshinsp.hazard.fall_protection | Fall protection hazard assessment | variant | Assessment checks heights, guardrails, harnesses, anchors, ladders and openings. | prevent falls |
| oshinsp.hazard.chemical_exposure | Chemical exposure assessment | variant | Assessment reviews labels, SDS, ventilation, PPE, storage, monitoring and symptoms. | reduce exposure |
| oshinsp.hazard.ergonomic_risk | Ergonomic risk assessment | variant | Assessment reviews force, repetition, posture, lifting, tools and work pace. | reduce strain |
| oshinsp.hazard.heat_stress | Heat stress hazard assessment | variant | Assessment checks temperature, workload, acclimatization, water, rest, shade and symptoms. | prevent illness |
| oshinsp.sampling.exposure_sampling | Occupational exposure sampling | invariant | Sampling records contaminant, method, worker, duration, equipment, calibration and chain. | quantify risk |
| oshinsp.sampling.noise_monitoring | Occupational noise monitoring | variant | Monitoring records dosimeter, area readings, task, duration, protection and results. | hearing risk |
| oshinsp.sampling.calibration_record | Safety sampling calibration record | invariant | Record documents pre, post, device, standard, time and acceptable range. | defensible data |
| oshinsp.citation.violation_analysis | Occupational safety violation analysis | invariant | Analysis links hazard, standard, exposure, employer knowledge and severity. | citation basis |
| oshinsp.citation.serious_classification | Serious violation classification | invariant | Classification records likelihood and severity of death or serious physical harm. | enforcement level |
| oshinsp.citation.repeat_classification | Repeat violation classification | variant | Classification compares prior final orders, similarity, employer and timeframe. | pattern enforcement |
| oshinsp.citation.willful_review | Willful violation review | variant | Review assesses intentional disregard, plain indifference, knowledge and evidence. | severe enforcement |
| oshinsp.abatement.abatement_requirement | Safety abatement requirement | invariant | Requirement states correction, date, proof, interim protection and certification. | remove hazard |
| oshinsp.abatement.interim_control | Safety interim control | variant | Control reduces exposure before permanent fix through guarding, isolation, PPE or procedure. | temporary protection |
| oshinsp.abatement.followup_inspection | Safety follow-up inspection | invariant | Inspection verifies abatement, documentation, worker protection and continuing compliance. | close citation |
| oshinsp.closing.closing_conference | Safety inspection closing conference | invariant | Conference explains findings, rights, abatement, contest process and next steps. | procedural closure |
| oshinsp.records.case_file | Occupational safety inspection case file | invariant | File stores complaint, notes, interviews, photos, samples, citations and correspondence. | evidence record |
| oshinsp.records.evidence_index | Safety inspection evidence index | invariant | Index maps evidence items to hazards, standards, dates, locations and witnesses. | organize case |
| oshinsp.records.confidential_note | Safety inspection confidential note | invariant | Note protects worker identity, whistleblower details or sensitive business information. | privacy |
| oshinsp.appeal.contest_record | Safety citation contest record | variant | Record tracks employer contest, conference, settlement, hearing, decision and abatement impact. | due process |
| oshinsp.appeal.informal_conference | Safety informal conference | variant | Conference reviews citation, penalty, abatement, evidence and settlement options. | resolve dispute |
| oshinsp.communication.worker_notice | Safety inspection worker notice | invariant | Notice communicates complaint outcome, citation, abatement or rights as allowed. | inform workers |
| oshinsp.communication.employer_notice | Safety inspection employer notice | invariant | Notice communicates findings, citations, penalties, abatement and contest rights. | formal action |
| oshinsp.quality.supervisor_review | Safety inspection supervisor review | invariant | Review checks jurisdiction, evidence, citation elements, sampling, penalty and closure. | quality control |
| oshinsp.reporting.program_report | Occupational safety inspection report | variant | Report summarizes complaints, inspections, hazards, citations, abatement and appeals. | oversight |
| oshinsp.metrics.osha_kpi | Occupational safety inspection KPI | variant | KPI tracks response time, serious hazards, abatement, contested cases and injury trends. | manage program |
| oshinsp.continuity.fatality_response | Occupational fatality response | invariant | Response secures scene, coordinates agencies, interviews, evidence, family sensitivity and deadlines. | critical investigation |
| oshinsp.continuity.multiemployer_site | Multi-employer worksite coordination | variant | Coordination identifies controlling, exposing, creating and correcting employers. | assign responsibility |
| oshinsp.close.case_closure | Occupational safety inspection closure | invariant | Closure records citations, no citation, referral, settlement, abatement or appeal status. | end case |
