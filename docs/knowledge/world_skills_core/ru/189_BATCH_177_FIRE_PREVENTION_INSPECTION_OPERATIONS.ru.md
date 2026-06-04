# BATCH_177 — Fire Prevention Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_177:fire_prevention_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| fireprev.records.occupancy_record | Fire occupancy record | invariant | Occupancy record links building, use, owner, hazards, systems, contacts and inspection history. | know the inspected place |
| fireprev.records.hazard_class | Hazard classification | invariant | Classification groups occupancy by fire load, use, storage, process and life-safety risk. | prioritize inspections |
| fireprev.records.contact_update | Emergency contact update | invariant | Contact update verifies responsible people, after-hours phone and access arrangements. | reach someone in incident |
| fireprev.records.preplan_link | Fire preplan link | variant | Preplan link connects inspection data with operational response information for crews. | prevention helps response |
| fireprev.records.system_inventory | Fire protection system inventory | invariant | Inventory records alarms, sprinklers, standpipes, extinguishers, suppression and smoke control systems. | know protection layers |
| fireprev.records.inspection_history | Fire inspection history | invariant | History shows prior violations, corrections, permits, complaints and enforcement actions. | repeat risk visibility |
| fireprev.routing.inspection_route | Inspection route | invariant | Route organizes inspections by geography, risk, due date, access and inspector workload. | efficient field day |
| fireprev.routing.priority_inspection | Priority inspection | variant | Priority is based on complaints, high hazard, public assembly, overdue status or incident history. | inspect highest risk first |
| fireprev.routing.reinspection_due | Reinspection due date | invariant | Due date sets deadline to verify correction after violation notice. | close loop |
| fireprev.routing.seasonal_focus | Seasonal fire prevention focus | variant | Seasonal focus targets fireworks, heating, holiday displays, wildland interface or assembly events. | timing changes risk |
| fireprev.routing.access_constraint | Inspection access constraint | invariant | Constraint records locked areas, tenant absence, security rules or special entry needs. | plan access |
| fireprev.routing.field_note | Fire inspector field note | invariant | Field note captures observations, photos, measurements and conversations supporting findings. | evidence at site |
| fireprev.inspect.egress_path | Means of egress path | invariant | Egress path must remain visible, unlocked where required, unobstructed and sized for occupants. | escape route |
| fireprev.inspect.exit_sign | Exit sign check | invariant | Exit sign check verifies visibility, illumination, direction and function. | wayfinding in smoke |
| fireprev.inspect.fire_door | Fire door inspection | invariant | Fire door check looks at closure, latching, gaps, labels, damage and propping. | compartment protection |
| fireprev.inspect.extinguisher | Fire extinguisher check | invariant | Check verifies location, type, inspection tag, access, pressure and condition. | first response tool |
| fireprev.inspect.sprinkler_clearance | Sprinkler clearance | invariant | Clearance prevents storage from blocking sprinkler discharge pattern. | water needs space |
| fireprev.inspect.electrical_panel_clearance | Electrical panel clearance | invariant | Panel clearance provides safe access and reduces fire or shock hazard around equipment. | no storage in front |
| fireprev.inspect.storage_height | Storage height limit | invariant | Height limit controls fuel load, sprinkler effectiveness and aisle access. | warehouse fire risk |
| fireprev.inspect.housekeeping | Fire housekeeping | invariant | Housekeeping reduces combustible clutter, blocked exits, waste buildup and ignition sources. | ordinary clutter burns |
| fireprev.systems.alarm_panel_status | Fire alarm panel status | invariant | Panel status shows normal, trouble, supervisory or alarm conditions needing follow-up. | system health |
| fireprev.systems.sprinkler_valve | Sprinkler control valve | invariant | Valve must be open, supervised and accessible to preserve sprinkler protection. | closed valve defeats system |
| fireprev.systems.standpipe_access | Standpipe access | invariant | Standpipe connections need visibility, clearance, caps and usable condition. | firefighter water access |
| fireprev.systems.hood_suppression | Kitchen hood suppression | variant | Hood suppression inspection checks service tags, nozzles, links, fuel shutoff and grease cleaning. | kitchen fire control |
| fireprev.systems.fire_pump_test | Fire pump test record | variant | Pump record documents periodic test, pressures, flow, alarms and deficiencies. | water supply confidence |
| fireprev.systems.impaired_system | Fire system impairment | invariant | Impairment record identifies disabled protection, duration, mitigation, notification and restoration. | risk while offline |
| fireprev.permits.hot_work_permit | Fire prevention hot work permit | invariant | Permit controls welding, cutting or spark work through area prep, watch and post-work checks. | ignition control |
| fireprev.permits.assembly_permit | Public assembly permit | variant | Permit checks occupant load, layout, exits, flame effects, decorations and crowd controls. | event life safety |
| fireprev.permits.tent_permit | Tent permit | variant | Tent permit verifies location, anchoring, flame resistance, exits, spacing and utilities. | temporary structure risk |
| fireprev.permits.hazardous_material_permit | Hazardous material permit | invariant | Permit records quantities, storage, separation, signage, emergency plan and limits. | dangerous inventory |
| fireprev.permits.fire_watch | Fire watch requirement | variant | Fire watch assigns trained observation when protection system is impaired or high-risk condition exists. | temporary human layer |
| fireprev.permits.open_flame | Open flame permit | variant | Permit controls candles, torches, pyrotechnics or flame effects by location and safeguards. | visible ignition |
| fireprev.violations.violation_notice | Fire violation notice | invariant | Notice states finding, code basis, location, correction, deadline and appeal or contact path. | formal correction demand |
| fireprev.violations.severity_level | Violation severity level | invariant | Severity reflects life-safety risk, immediacy, occupancy and history. | prioritize enforcement |
| fireprev.violations.corrective_photo | Corrective photo evidence | variant | Photo evidence can document correction, but may require field verification for critical items. | remote closure support |
| fireprev.violations.extension_request | Correction extension request | variant | Extension evaluates reason, risk, progress and interim measures before deadline change. | flexibility with safety |
| fireprev.violations.escalation | Fire code enforcement escalation | invariant | Escalation moves from notice to citation, order, closure or legal process when risk persists. | consequences |
| fireprev.violations.compliance_closeout | Violation closeout | invariant | Closeout records correction verified, date, inspector and remaining notes. | finish inspection loop |
| fireprev.community.public_education | Fire public education | variant | Education teaches occupants, businesses or communities about prevention, alarms, exits and seasonal risks. | prevention by behavior |
| fireprev.community.drill_observation | Fire drill observation | variant | Observation reviews alarm response, evacuation time, route use, accountability and issues. | practice reveals gaps |
| fireprev.community.complaint_intake | Fire safety complaint intake | invariant | Intake records complainant, location, hazard, urgency and follow-up path. | public risk signal |
| fireprev.community.hydrant_obstruction | Hydrant obstruction note | invariant | Note records blocked, hidden, damaged or inaccessible hydrant for correction. | water access outside |
| fireprev.reporting.inspection_report | Fire inspection report | invariant | Report summarizes scope, observations, violations, photos, contacts and next actions. | official record |
| fireprev.reporting.program_metric | Fire prevention program metric | variant | Metrics track inspections completed, violations, reinspections, closures, complaints and high-risk occupancy coverage. | manage prevention workload |
