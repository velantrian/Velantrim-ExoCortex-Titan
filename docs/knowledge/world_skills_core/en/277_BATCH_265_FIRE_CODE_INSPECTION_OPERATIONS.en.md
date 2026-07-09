# BATCH_265 — Fire Code Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_265:fire_code_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| fireinsp.occupancy.occupancy_record | Fire inspection occupancy record | invariant | Record stores business, use group, occupant load, contacts, permits and hazards. | know site |
| fireinsp.occupancy.preplan_link | Fire preplan link | variant | Link connects inspection findings to response plan, hydrants, access and hazards. | response readiness |
| fireinsp.occupancy.risk_class | Fire inspection risk class | invariant | Class ranks occupancy by hazard, size, vulnerability, history and systems. | schedule priority |
| fireinsp.schedule.inspection_cycle | Fire inspection cycle | invariant | Cycle sets routine frequency by occupancy, risk, code and local policy. | plan workload |
| fireinsp.schedule.complaint_assignment | Fire code complaint assignment | invariant | Assignment routes complaint by hazard, occupancy, inspector, urgency and jurisdiction. | investigate |
| fireinsp.entry.entry_conference | Fire inspection entry conference | invariant | Conference identifies responsible person, scope, authority and inspection route. | set expectations |
| fireinsp.entry.access_problem | Fire inspection access problem | variant | Problem records locked doors, no representative, unsafe entry or denied access. | reschedule/escalate |
| fireinsp.hazard.egress_obstruction | Egress obstruction | invariant | Finding records blocked exits, aisles, doors, stairs or discharge paths. | keep escape clear |
| fireinsp.hazard.storage_hazard | Fire storage hazard | invariant | Finding records combustible storage, height, clearance, housekeeping or incompatible materials. | reduce fuel |
| fireinsp.hazard.electrical_hazard | Fire electrical hazard | invariant | Finding records extension cords, overloads, panels, exposed wiring or damaged equipment. | reduce ignition |
| fireinsp.hazard.hot_work | Fire hot work control | variant | Control checks permits, fire watch, shielding, combustibles, extinguishers and duration. | prevent fires |
| fireinsp.hazard.fire_lane_access | Fire lane and hydrant access | invariant | Finding records blocked fire lanes, hydrants, fire department connections or access roads. | support response |
| fireinsp.system.alarm_panel | Fire alarm panel check | invariant | Check reviews status, trouble, monitoring, inspections, documentation and access. | alarm readiness |
| fireinsp.system.sprinkler_system | Fire sprinkler system check | invariant | Check reviews valves, gauges, clearance, tags, impairments and records. | suppression readiness |
| fireinsp.system.extinguisher | Fire extinguisher check | invariant | Check reviews location, type, charge, tag, access and spacing. | first response |
| fireinsp.system.hood_suppression | Kitchen hood suppression check | variant | Check reviews tags, nozzles, fuel shutoff, cleaning and service records. | kitchen safety |
| fireinsp.system.emergency_lighting | Emergency lighting check | invariant | Check verifies exit signs, backup lights, testing records and visibility. | egress safety |
| fireinsp.permit.special_event | Fire special event permit | variant | Permit checks tents, crowds, exits, cooking, generators, pyrotechnics and emergency access. | event safety |
| fireinsp.permit.hazardous_material | Fire hazardous material permit | variant | Permit records quantities, storage, SDS, signage, separation and emergency plan. | manage hazmat |
| fireinsp.permit.occupancy_permit | Fire occupancy permit | invariant | Permit confirms use, capacity, systems, exits, address and inspection approval. | lawful occupancy |
| fireinsp.violation.violation_notice | Fire code violation notice | invariant | Notice lists violation, code basis, correction, deadline, appeal and reinspection. | enforce code |
| fireinsp.violation.immediate_danger | Fire immediate danger | invariant | Danger triggers evacuation, closure, fire watch, system repair or emergency order. | prevent casualties |
| fireinsp.violation.repeat_violation | Fire repeat violation | variant | Violation repeats prior issue and may escalate enforcement or penalties. | address pattern |
| fireinsp.firewatch.fire_watch_order | Fire watch order | variant | Order requires trained watch, patrol frequency, logs, communication and duration. | compensate impairment |
| fireinsp.firewatch.fire_watch_log | Fire watch log | invariant | Log records patrol times, findings, staff, communication device and termination. | verify watch |
| fireinsp.reinspect.reinspection_schedule | Fire reinspection schedule | invariant | Schedule verifies correction by deadline, risk, occupancy and inspector availability. | close violations |
| fireinsp.reinspect.correction_evidence | Fire correction evidence | invariant | Evidence includes photos, service tags, invoices, test reports or field observation. | verify fix |
| fireinsp.enforcement.citation | Fire code citation | variant | Citation records uncorrected violation, penalty, authority, evidence and hearing route. | compel compliance |
| fireinsp.enforcement.closure_order | Fire closure order | variant | Order closes occupancy or area due to unsafe fire condition or system failure. | protect public |
| fireinsp.education.owner_guidance | Fire code owner guidance | variant | Guidance explains corrections, maintenance, permits, records and prevention practices. | help compliance |
| fireinsp.education.public_education | Fire public education contact | variant | Contact records smoke alarms, evacuation, extinguisher, school or business outreach. | prevention |
| fireinsp.records.inspection_report | Fire inspection report | invariant | Report documents occupancy, findings, systems, violations, photos and deadlines. | official record |
| fireinsp.records.system_test_record | Fire system test record | invariant | Record stores alarm, sprinkler, hood, pump, extinguisher or emergency light test. | system history |
| fireinsp.records.photo_log | Fire inspection photo log | invariant | Log links image, location, violation, date and inspector. | evidence |
| fireinsp.records.case_file | Fire inspection case file | invariant | File stores reports, permits, complaints, notices, reinspections and enforcement. | case memory |
| fireinsp.quality.supervisor_review | Fire inspection supervisor review | invariant | Review checks code basis, deadlines, enforcement, closures and documentation. | consistency |
| fireinsp.quality.code_update | Fire code update briefing | variant | Briefing aligns inspectors on adopted code changes, interpretations and policy. | shared practice |
| fireinsp.safety.inspector_safety | Fire inspector safety | invariant | Safety covers hostile sites, traffic, roofs, confined spaces, chemicals and PPE. | protect staff |
| fireinsp.reporting.program_report | Fire inspection program report | invariant | Report summarizes inspections, violations, permits, fire watches, closures and education. | oversight |
| fireinsp.metrics.fireinsp_kpi | Fire inspection KPI | variant | KPI tracks inspection completion, correction rate, repeat violations, closures and system impairments. | manage program |
| fireinsp.continuity.post_fire_inspection | Post-fire inspection | variant | Inspection documents damage, utilities, hazards, occupancy limits and investigation coordination. | recover safely |
| fireinsp.continuity.system_outage | Fire inspection system outage | invariant | Outage uses paper route, offline reports, phone dispatch and later entry. | keep inspections |
| fireinsp.close.case_closure | Fire inspection case closure | invariant | Closure records corrected, referred, cited, closed, withdrawn or education-only outcome. | finish case |
| fireinsp.audit.audit_trail | Fire inspection audit trail | invariant | Trail records user, date, report, notice, edit, result and enforcement actions. | accountability |
