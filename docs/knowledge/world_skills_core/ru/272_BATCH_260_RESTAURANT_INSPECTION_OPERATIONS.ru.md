# BATCH_260 — Restaurant Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_260:restaurant_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| restinsp.schedule.routine_cycle | Restaurant routine inspection cycle | invariant | Cycle schedules facility by risk class, history, permit type and due date. | plan inspections |
| restinsp.schedule.complaint_assignment | Restaurant complaint inspection assignment | invariant | Assignment links complaint, facility, priority, inspector, protocol and response target. | investigate promptly |
| restinsp.schedule.followup_due | Restaurant follow-up due date | invariant | Due date tracks correction deadline, reinspection need and enforcement status. | verify fixes |
| restinsp.prep.facility_history | Restaurant inspection history review | invariant | Review checks prior violations, closures, ownership, menu, equipment and complaints. | inspect intelligently |
| restinsp.entry.entry_conference | Restaurant inspection entry conference | invariant | Conference identifies person in charge, purpose, scope, authority and inspection flow. | set expectations |
| restinsp.entry.person_in_charge | Restaurant person-in-charge check | invariant | Check verifies knowledgeable responsible person is present and accountable. | management control |
| restinsp.food.temperature_check | Restaurant food temperature check | invariant | Check records hot, cold, cooling, reheating and holding temperatures. | control pathogen risk |
| restinsp.food.cooling_process | Restaurant cooling process review | invariant | Review checks time, temperature, containers, depth, labels and logs. | prevent growth |
| restinsp.food.cook_reheat | Restaurant cook and reheat check | invariant | Check verifies required cooking or reheating control points and documentation. | safe preparation |
| restinsp.food.cross_contamination | Restaurant cross-contamination check | invariant | Check reviews raw and ready-to-eat separation, utensils, storage and workflow. | prevent contamination |
| restinsp.food.date_marking | Restaurant date marking check | invariant | Check reviews prepared food labels, discard dates, opening dates and rotation. | control shelf life |
| restinsp.hygiene.handwashing | Restaurant handwashing check | invariant | Check verifies sinks, soap, towels, access, employee practice and timing. | reduce illness |
| restinsp.hygiene.employee_health | Restaurant employee health policy check | invariant | Check reviews illness reporting, exclusions, restrictions and manager knowledge. | prevent outbreaks |
| restinsp.hygiene.bare_hand_contact | Bare-hand contact check | variant | Check reviews ready-to-eat handling, gloves, utensils and approved alternatives. | food protection |
| restinsp.sanitation.dishwasher_check | Restaurant dish machine check | invariant | Check records sanitizer, temperature, pressure, test strips and ware condition. | clean utensils |
| restinsp.sanitation.surface_sanitizer | Food-contact surface sanitizer check | invariant | Check verifies concentration, contact time, cloth storage and solution age. | sanitize surfaces |
| restinsp.sanitation.cleaning_schedule | Restaurant cleaning schedule review | variant | Review checks frequency, responsible staff, hard-to-clean areas and verification. | maintain hygiene |
| restinsp.facility.equipment_condition | Restaurant equipment condition check | invariant | Check reviews refrigeration, hot holding, prep tables, thermometers and maintenance. | reliable controls |
| restinsp.facility.plumbing_check | Restaurant plumbing check | invariant | Check verifies hot water, backflow prevention, sewage, leaks and mop sink. | facility safety |
| restinsp.facility.pest_activity | Restaurant pest activity check | invariant | Check records droppings, insects, doors, traps, contractor logs and harborage. | pest control |
| restinsp.storage.food_source | Restaurant approved source review | invariant | Review checks invoices, suppliers, shellstock tags, labels and traceability. | safe sourcing |
| restinsp.storage.chemical_storage | Restaurant chemical storage check | invariant | Check verifies labeling, separation, sanitizer, toxic materials and employee access. | prevent poisoning |
| restinsp.storage.allergen_control | Restaurant allergen control review | variant | Review checks menu communication, ingredient knowledge, cross-contact and staff training. | protect diners |
| restinsp.violation.priority_violation | Restaurant priority violation | invariant | Violation directly relates to foodborne illness risk and needs rapid correction. | urgent fix |
| restinsp.violation.core_violation | Restaurant core violation | variant | Violation concerns sanitation, facility, maintenance or management support systems. | improve baseline |
| restinsp.violation.repeat_violation | Restaurant repeat violation | invariant | Violation repeats previous issue and may affect scoring or enforcement. | address pattern |
| restinsp.scoring.inspection_score | Restaurant inspection score | variant | Score aggregates violation severity, points, grade, risk or compliance status. | public rating |
| restinsp.scoring.grade_posting | Restaurant grade posting | variant | Posting displays required grade, placard, permit status or inspection result. | public information |
| restinsp.corrective.onsite_correction | Restaurant onsite correction | invariant | Correction fixes violation during inspection with inspector verification and notation. | immediate improvement |
| restinsp.corrective.corrective_plan | Restaurant corrective action plan | invariant | Plan states root cause, action, staff training, deadline and proof needed. | durable fix |
| restinsp.corrective.reinspection | Restaurant reinspection | invariant | Reinspection verifies prior violations, new hazards, documentation and compliance status. | close follow-up |
| restinsp.closure.imminent_hazard | Restaurant imminent health hazard | invariant | Hazard includes sewage, no water, fire, pest infestation, illness outbreak or unsafe food. | closure trigger |
| restinsp.closure.closure_order | Restaurant closure order | invariant | Order stops operation, lists hazards, reopening criteria and appeal rights. | protect public |
| restinsp.closure.reopening_check | Restaurant reopening check | invariant | Check verifies hazard removal, cleaning, food disposition, equipment and manager readiness. | resume safely |
| restinsp.outbreak.illness_complaint | Restaurant illness complaint | invariant | Complaint records symptoms, meal, timing, party, foods, contact and sample possibility. | outbreak signal |
| restinsp.outbreak.food_history | Restaurant food history investigation | variant | Investigation links menu items, ingredients, staff, preparation logs and exposed guests. | trace source |
| restinsp.outbreak.exclusion_notice | Restaurant employee exclusion notice | invariant | Notice restricts ill employee according to approved public health criteria. | reduce spread |
| restinsp.records.inspection_report | Restaurant inspection report | invariant | Report documents observations, violations, corrections, score, photos and signatures. | official record |
| restinsp.records.operator_signature | Restaurant operator signature | invariant | Signature acknowledges receipt, not agreement, and records person-in-charge. | service proof |
| restinsp.records.photo_evidence | Restaurant inspection photo evidence | variant | Evidence links photo to violation, location, time, inspector and report. | support finding |
| restinsp.quality.supervisor_review | Restaurant inspection supervisor review | invariant | Review checks violation coding, scoring, enforcement, closure and report clarity. | consistency |
| restinsp.reporting.public_portal | Restaurant inspection public portal update | variant | Update publishes grade, inspection date, violations and closure status as allowed. | transparency |
| restinsp.metrics.restaurant_kpi | Restaurant inspection KPI | variant | KPI tracks inspection timeliness, critical violations, closures, repeat findings and complaints. | manage program |
| restinsp.continuity.mass_event_food | Mass event food inspection surge | variant | Surge coordinates temporary food booths, staffing, sampling, complaints and closures. | protect event diners |
