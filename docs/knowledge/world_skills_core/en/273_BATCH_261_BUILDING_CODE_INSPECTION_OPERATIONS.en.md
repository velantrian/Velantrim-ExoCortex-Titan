# BATCH_261 — Building Code Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_261:building_code_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| buildinsp.permit.permit_link | Building inspection permit link | invariant | Link connects inspection request to permit, address, scope, plans and contractor. | inspect right work |
| buildinsp.permit.approved_plan | Approved plan reference | invariant | Reference identifies drawing set, revisions, deferred submittals and special conditions. | compare field work |
| buildinsp.permit.inspection_type | Building inspection type | invariant | Type defines footing, framing, electrical, plumbing, mechanical, fire, final or special inspection. | route inspector |
| buildinsp.schedule.request_intake | Building inspection request intake | invariant | Intake records permit, requested type, date, contact, access and readiness statement. | schedule visit |
| buildinsp.schedule.route_planning | Building inspector route planning | variant | Planning groups inspections by geography, type, duration, priority and travel time. | use day well |
| buildinsp.schedule.cancel_reschedule | Building inspection cancel or reschedule | variant | Change records reason, requester, new time, failed readiness and notice. | calendar control |
| buildinsp.field.site_arrival | Building inspection site arrival | invariant | Arrival records address, time, contact, permit card, access and safety condition. | start field check |
| buildinsp.field.scope_boundary | Building inspection scope boundary | invariant | Boundary keeps inspection limited to permitted work, code phase and visible conditions. | avoid overreach |
| buildinsp.field.photo_record | Building inspection photo record | variant | Photo documents concealed work, correction, hazard, site condition or approval basis. | evidence |
| buildinsp.field.site_safety | Building inspector site safety | invariant | Safety checks fall hazards, excavation, traffic, power, dogs, confined spaces and PPE. | protect inspector |
| buildinsp.structural.footing_check | Building footing inspection | invariant | Check reviews forms, depth, reinforcement, soil, setbacks, drainage and approved plans. | foundation control |
| buildinsp.structural.framing_check | Building framing inspection | invariant | Check reviews members, connections, openings, bracing, fire blocking and plan alignment. | structural quality |
| buildinsp.structural.shear_wall | Shear wall inspection | variant | Inspection checks nailing, hold-downs, panels, anchors, straps and special details. | lateral resistance |
| buildinsp.structural.roof_truss | Roof truss inspection | variant | Inspection checks layout, bracing, hangers, damage, field cuts and engineering documents. | roof safety |
| buildinsp.systems.electrical_rough | Electrical rough inspection | invariant | Check reviews boxes, wiring, grounding, protection, clearances and panel preparation. | safe wiring |
| buildinsp.systems.plumbing_rough | Plumbing rough inspection | invariant | Check reviews piping, slope, supports, vents, tests, cleanouts and protection. | reliable plumbing |
| buildinsp.systems.mechanical_rough | Mechanical rough inspection | invariant | Check reviews ducts, equipment, combustion air, venting, clearances and condensate. | safe systems |
| buildinsp.systems.energy_check | Energy code inspection | variant | Check reviews insulation, air sealing, windows, ducts, lighting or envelope details. | energy compliance |
| buildinsp.systems.elevator_coordination | Elevator inspection coordination | variant | Coordination links elevator permit, third-party inspection, safety devices, access and final approval. | vertical transport |
| buildinsp.fire.firestopping | Firestopping inspection | invariant | Check reviews penetrations, rated assemblies, listed systems and installation quality. | maintain fire rating |
| buildinsp.fire.egress_check | Means of egress check | invariant | Check verifies exits, stairs, doors, lighting, signs, path width and obstructions. | life safety |
| buildinsp.access.accessibility_check | Building accessibility inspection | invariant | Check reviews routes, ramps, doors, restrooms, parking, controls and signage. | inclusive access |
| buildinsp.corrections.correction_notice | Building correction notice | invariant | Notice lists code issue, location, required correction, reference and reinspection need. | guide fix |
| buildinsp.corrections.stop_work | Building stop-work order | variant | Order halts unsafe, unpermitted or noncompliant work and states release criteria. | control risk |
| buildinsp.corrections.deviation_record | Building field deviation record | invariant | Record captures work differing from approved plans and routes revision or correction. | maintain design intent |
| buildinsp.corrections.reinspection | Building reinspection | invariant | Reinspection verifies corrections, prior notice items, access and new related issues. | close issues |
| buildinsp.special.special_inspection | Building special inspection record | variant | Record tracks third-party inspector, tests, reports, deviations and engineer review. | verify critical work |
| buildinsp.special.material_test | Building material test report | variant | Report includes concrete, steel, weld, soil, masonry or fireproofing test results. | evidence quality |
| buildinsp.final.final_inspection | Building final inspection | invariant | Inspection verifies completed work, life safety, systems, accessibility, documents and open items. | permit closeout |
| buildinsp.final.certificate_ready | Certificate readiness review | invariant | Review checks approvals, fees, plans, special reports, addressing and final conditions. | issue certificate |
| buildinsp.final.temporary_certificate | Temporary certificate review | variant | Review permits limited occupancy with remaining safe conditions, deadlines and bonds. | phased opening |
| buildinsp.records.inspection_result | Building inspection result | invariant | Result records approved, partial, failed, cancelled, no access or not ready status. | official outcome |
| buildinsp.records.inspector_note | Building inspector note | invariant | Note documents observations, references, conversations, photos and correction rationale. | case memory |
| buildinsp.records.code_reference | Building code reference | invariant | Reference links finding to adopted code section, standard, plan note or condition. | defensible decision |
| buildinsp.records.data_correction | Building inspection data correction | variant | Correction fixes permit, address, result, date or inspector error with audit note. | accurate record |
| buildinsp.communication.contractor_notice | Building contractor notice | invariant | Notice communicates result, corrections, reinspection steps, fees and contact path. | clear communication |
| buildinsp.communication.owner_question | Building owner question response | variant | Response explains process, status, correction path and limits of inspector advice. | service |
| buildinsp.quality.peer_review | Building inspection peer review | variant | Review checks complex decisions, code interpretation, photographs and consistency. | quality |
| buildinsp.quality.calibration_meeting | Building inspection calibration meeting | variant | Meeting aligns inspectors on code updates, common defects and interpretation. | consistent enforcement |
| buildinsp.reporting.inspection_backlog | Building inspection backlog report | invariant | Report tracks requested, completed, overdue, failed, reinspection and final inspections. | manage workload |
| buildinsp.reporting.permit_closeout | Building permit closeout report | invariant | Report identifies permits ready, stalled, expired, missing inspections or certificate issues. | clean records |
| buildinsp.metrics.buildinsp_kpi | Building inspection KPI | variant | KPI tracks timeliness, pass rate, repeat corrections, stops, certificates and backlog. | manage program |
| buildinsp.continuity.system_outage | Building inspection system outage | invariant | Outage uses paper route, offline notes, photos, phone dispatch and later entry. | keep inspections moving |
| buildinsp.continuity.disaster_damage | Building disaster damage inspection | variant | Inspection triages unsafe structures, placards, utilities, occupancy and follow-up. | post-disaster safety |
