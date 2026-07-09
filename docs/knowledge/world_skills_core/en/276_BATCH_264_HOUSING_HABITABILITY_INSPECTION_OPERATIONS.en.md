# BATCH_264 — Housing Habitability Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_264:housing_habitability_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| habitinsp.complaint.intake | Housing habitability complaint intake | invariant | Intake records unit, tenant, owner, issue, dates, photos and safe contact. | start case |
| habitinsp.complaint.urgent_flag | Habitability urgent flag | invariant | Flag marks no heat, no water, sewage, fire damage, collapse, lockout or severe hazard. | triage risk |
| habitinsp.complaint.retaliation_note | Housing retaliation note | variant | Note records alleged retaliation, eviction threat, utility shutoff or harassment. | protect tenant |
| habitinsp.complaint.jurisdiction_check | Housing habitability jurisdiction check | invariant | Check confirms unit type, location, authority, exemptions and referral needs. | route case |
| habitinsp.schedule.inspection_notice | Housing inspection notice | invariant | Notice states date, time window, purpose, access rights and contact. | lawful entry |
| habitinsp.schedule.entry_plan | Housing inspection entry plan | variant | Plan coordinates tenant, owner, interpreter, safety, pets, keys and access limits. | field readiness |
| habitinsp.field.entry_record | Housing inspection entry record | invariant | Record captures arrival, persons present, consent, authority and areas inspected. | evidence |
| habitinsp.field.photo_record | Habitability photo record | invariant | Photo links condition, room, violation, date and inspector notes. | document condition |
| habitinsp.field.tenant_statement | Tenant statement | variant | Statement captures reported timeline, effects, repair requests and owner response. | context |
| habitinsp.field.owner_statement | Owner statement | variant | Statement captures repair history, access attempts, contractors and disputed facts. | balanced record |
| habitinsp.check.heat_check | Housing heat check | invariant | Check records heating system, indoor temperature, season rule and utility status. | habitability |
| habitinsp.check.hot_water_check | Housing hot water check | invariant | Check verifies hot water availability, temperature, fixtures and equipment condition. | basic service |
| habitinsp.check.plumbing_check | Housing plumbing check | invariant | Check reviews leaks, drainage, sewage, toilets, sinks, tubs and water pressure. | sanitation |
| habitinsp.check.electrical_check | Housing electrical check | invariant | Check reviews outlets, exposed wiring, panels, lighting, overloads and unsafe conditions. | fire safety |
| habitinsp.check.structural_check | Housing structural check | invariant | Check observes walls, ceilings, floors, stairs, railings, windows and doors. | physical safety |
| habitinsp.check.moisture_mold | Housing moisture and mold check | invariant | Check records visible mold, moisture source, ventilation, leaks and affected materials. | health concern |
| habitinsp.check.pest_condition | Housing pest condition | invariant | Check records rodents, insects, droppings, entry points, sanitation and treatment evidence. | pest control |
| habitinsp.check.smoke_co | Smoke and CO alarm check | invariant | Check verifies presence, placement, power, test status and missing devices. | life safety |
| habitinsp.check.egress_check | Housing egress check | invariant | Check confirms exits, windows, locks, stairs and obstructions allow safe escape. | emergency exit |
| habitinsp.check.sanitation | Housing sanitation check | variant | Check reviews trash, debris, hoarding concern, waste, odors and shared-area condition. | healthy unit |
| habitinsp.violation.code_violation | Housing code violation | invariant | Violation links condition to code, room, severity, evidence and correction. | enforce rule |
| habitinsp.violation.imminent_hazard | Housing imminent hazard | invariant | Hazard requires urgent repair, vacate, utility action or emergency referral. | prevent harm |
| habitinsp.violation.repeat_violation | Housing repeat violation | variant | Violation repeats prior issue, missed repair or recurring condition. | escalate |
| habitinsp.notice.notice_of_violation | Housing notice of violation | invariant | Notice lists violations, corrections, deadlines, parties, appeal and reinspection. | formal order |
| habitinsp.notice.repair_deadline | Housing repair deadline | invariant | Deadline sets correction date by severity, rule and practical urgency. | manage compliance |
| habitinsp.notice.service_proof | Housing notice service proof | invariant | Proof records mail, posting, hand delivery, email if allowed and date. | due process |
| habitinsp.reinspect.reinspection_schedule | Housing reinspection schedule | invariant | Schedule checks claimed or required corrections after deadline or extension. | verify repair |
| habitinsp.reinspect.correction_verified | Housing correction verified | invariant | Verification records repaired, partially repaired, inaccessible or not corrected status. | close item |
| habitinsp.reinspect.no_access | Housing reinspection no-access | variant | Record captures missed access, attempted contact, notice and next step. | preserve process |
| habitinsp.enforcement.citation | Housing habitability citation | variant | Citation records failure to correct, penalty, hearing route and evidence. | enforce compliance |
| habitinsp.enforcement.vacate_order | Housing vacate order | variant | Order removes occupancy due to unsafe, unfit or emergency condition. | protect occupants |
| habitinsp.enforcement.repair_escrow_referral | Repair escrow referral | variant | Referral routes unresolved habitability case to court, escrow or tenant remedy process. | support remedy |
| habitinsp.communication.tenant_update | Housing tenant update | invariant | Update explains inspection result, notices, deadlines, resources and next steps. | keep informed |
| habitinsp.communication.owner_update | Housing owner update | invariant | Update explains violations, evidence, deadlines, appeal and reinspection process. | support compliance |
| habitinsp.communication.language_access | Housing inspection language access | variant | Access provides interpreter, translated notices, plain-language explanation and safe contact. | fair service |
| habitinsp.records.case_file | Housing inspection case file | invariant | File stores complaint, notices, photos, reports, statements, reinspections and closure. | case memory |
| habitinsp.records.inspection_report | Housing habitability report | invariant | Report summarizes unit, findings, violations, photos, orders, deadlines and follow-up. | official record |
| habitinsp.records.audit_trail | Housing inspection audit trail | invariant | Trail records edits, notices, status changes, evidence and closure actions. | accountability |
| habitinsp.quality.supervisor_review | Housing inspection supervisor review | invariant | Review checks authority, evidence, violation coding, deadlines, orders and closure. | consistency |
| habitinsp.safety.inspector_safety | Housing inspector safety | invariant | Safety covers animals, hostility, structural hazards, biohazards, traffic and buddy need. | protect staff |
| habitinsp.reporting.program_report | Housing habitability program report | variant | Report summarizes complaints, inspections, violations, orders, citations and closures. | oversight |
| habitinsp.metrics.habitability_kpi | Housing habitability KPI | variant | KPI tracks response time, urgent cases, correction rate, repeat violations and no-access. | manage program |
| habitinsp.close.case_closure | Housing habitability case closure | invariant | Closure records corrected, unfounded, referred, vacated, legal action or withdrawn. | end case |
| habitinsp.continuity.disaster_housing | Disaster housing habitability inspection | variant | Inspection triages units after fire, flood, storm, freeze or utility outage. | rapid safety |
