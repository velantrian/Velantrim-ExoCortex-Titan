# BATCH_157 — Construction Site Logistics & Safety Detail
# world_skills_core · source: world_skills_core:batch_157:construction_site_logistics_safety
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| sitelog.plan.site_logistics_plan | Site logistics plan | invariant | Site logistics plan maps access, storage, cranes, hoists, pedestrian routes, deliveries, waste and emergency paths. | стройка как поток |
| sitelog.plan.site_access_control | Site access control | invariant | Access control confirms induction, credentials, PPE, visitor status and authorized work zones. | кто может войти |
| sitelog.plan.hoarding_boundary | Hoarding and boundary | invariant | Hoarding separates public from worksite hazards while controlling visibility, security and access. | граница стройки |
| sitelog.plan.welfare_facilities | Welfare facilities | invariant | Welfare facilities provide toilets, washing, drinking water, rest areas and changing space for workers. | базовая worker dignity |
| sitelog.plan.emergency_route | Site emergency route | invariant | Emergency routes must remain clear for evacuation, fire response, ambulance access and rescue equipment. | путь нельзя занять материалами |
| sitelog.plan.neighbor_interface | Neighbor interface | variant | Neighbor interface manages noise, dust, vibration, traffic, complaints and communication around the site. | стройка рядом с людьми |
| sitelog.delivery.delivery_booking | Delivery booking | invariant | Delivery booking schedules trucks by time, gate, unloading method, material type and site readiness. | избежать затора у ворот |
| sitelog.delivery.laydown_area | Laydown area | invariant | Laydown area stores materials safely by weight, weather protection, access, sequencing and theft risk. | где лежит материал |
| sitelog.delivery.just_in_time | Just-in-time delivery | variant | JIT delivery reduces storage needs but increases schedule risk if transport or readiness slips. | меньше склада, больше coordination |
| sitelog.delivery.material_inspection | Material receipt inspection | invariant | Receipt inspection checks quantity, damage, certificates, dimensions, batch numbers and conformance before acceptance. | не принять плохой материал |
| sitelog.delivery.offload_plan | Offload plan | invariant | Offload plan defines lifting points, equipment, exclusion zone, ground capacity and responsible signalers. | unloading is a lift |
| sitelog.delivery.material_traceability | Construction material traceability | invariant | Traceability links installed materials to supplier, batch, certificates, location and inspection records. | доказать что встроено |
| sitelog.lifting.lift_plan | Lift plan | invariant | Lift plan defines load, radius, crane capacity, rigging, ground conditions, exclusion zones and communication. | lift before crane moves |
| sitelog.lifting.crane_coordination | Crane coordination | invariant | Crane coordination prevents conflicts between cranes, loads, structures, power lines, public areas and other trades. | sky traffic control |
| sitelog.lifting.rigging_inspection | Rigging inspection | invariant | Rigging inspection checks slings, shackles, hooks, tags, damage and correct configuration before use. | small gear holds big load |
| sitelog.lifting.exclusion_zone | Lifting exclusion zone | invariant | Exclusion zone keeps people away from suspended loads and potential drop zones. | no one under load |
| sitelog.lifting.banksman_signal | Banksman signal | invariant | Banksman signal provides controlled communication between operator and crew during lifting or vehicle movement. | one clear signal |
| sitelog.lifting.temporary_works_interface | Temporary works interface | variant | Lifts near formwork, scaffolds or shoring require checking temporary works capacity and stability. | temporary is structural |
| sitelog.permit.permit_to_work | Permit to work | invariant | Permit to work authorizes hazardous tasks with scope, controls, time, people, isolation and signoff. | разрешение на риск |
| sitelog.permit.hot_work_permit | Hot work permit | invariant | Hot work permit controls fire risk through isolation, fire watch, extinguishers, atmosphere and post-work checks. | sparks need control |
| sitelog.permit.confined_space_permit | Confined space permit | invariant | Confined space permit requires atmosphere testing, entry control, rescue plan, attendants and communication. | invisible hazards |
| sitelog.permit.excavation_permit | Excavation permit | invariant | Excavation permit checks utilities, shoring, access, spoil placement, water and inspection before digging. | ground can kill |
| sitelog.permit.energization_permit | Energization permit | variant | Energization permit controls introduction of live power, testing boundaries, signage and authorized persons. | system changes state |
| sitelog.permit.permit_closeout | Permit closeout | invariant | Closeout confirms work ended, area safe, isolations removed correctly and records completed. | permit lifecycle |
| sitelog.safety.toolbox_talk | Toolbox talk | invariant | Toolbox talk briefs workers on task hazards, controls, changes, lessons and questions before work. | daily alignment |
| sitelog.safety.method_statement | Method statement | invariant | Method statement describes how work will be done safely, with sequence, equipment, roles and controls. | method before task |
| sitelog.safety.risk_assessment | Construction risk assessment | invariant | Risk assessment identifies hazards, likelihood, severity and control measures for construction activity. | risk made visible |
| sitelog.safety.near_miss_report | Near miss report | invariant | Near miss report captures events that could have caused harm and feeds corrective action. | learn before injury |
| sitelog.safety.ppe_compliance | PPE compliance | invariant | PPE compliance verifies task-specific protection, condition, fit and actual use on site. | hard hats are not enough |
| sitelog.safety.housekeeping | Site housekeeping | invariant | Housekeeping controls trip hazards, waste, access routes, nails, dust and material clutter. | clean site is safer |
| sitelog.temporary.scaffold_handover | Scaffold handover | invariant | Scaffold handover confirms inspected, tagged and authorized structure before use. | do not climb assumptions |
| sitelog.temporary.shoring_inspection | Shoring inspection | invariant | Shoring inspection verifies support condition, movement, load, water and excavation changes. | ground support is active |
| sitelog.temporary.formwork_strike | Formwork strike approval | variant | Strike approval confirms concrete strength, sequence, temporary support and engineer requirements before removal. | removing support is risk |
| sitelog.temporary.temporary_power | Temporary power control | invariant | Temporary power requires protected distribution, inspection, routing, weather resistance and access control. | electricity moves with site |
| sitelog.temporary.edge_protection | Edge protection | invariant | Edge protection prevents falls from slabs, roofs, openings, stairs and excavations. | gravity is constant |
| sitelog.coord.daily_coordination | Daily coordination meeting | invariant | Daily coordination aligns trades, deliveries, permits, constraints, safety risks and schedule priorities. | avoid trade clashes |
| sitelog.coord.lookahead_plan | Lookahead plan | invariant | Lookahead plan reviews upcoming work, constraints, materials, inspections and labor before schedule dates arrive. | future problems today |
| sitelog.coord.trade_interface | Trade interface | variant | Trade interface manages dependencies between subcontractors sharing space, systems, sequence or access. | one trade affects another |
| sitelog.coord.rfi_tracking | Site RFI tracking | invariant | RFI tracking records technical questions, responsible designer, response date and impact on work. | unanswered question delays site |
| sitelog.coord.inspection_request | Inspection request | invariant | Inspection request notifies required party when work is ready for hold point or quality check. | do not cover unchecked work |
| sitelog.coord.daily_report | Construction daily report | invariant | Daily report records labor, weather, work areas, deliveries, delays, incidents and photos. | project memory |
| sitelog.environment.dust_suppression | Dust suppression | invariant | Dust suppression uses water, covers, extraction, housekeeping or sequencing to reduce airborne particles. | protect workers and neighbors |
| sitelog.environment.waste_skip_control | Waste skip control | invariant | Skip control separates waste streams, prevents overflow, tracks haulage and avoids contamination. | waste as site flow |
| sitelog.environment.washout_area | Concrete washout area | invariant | Washout area contains alkaline concrete waste away from drains, soil and watercourses. | small pit prevents pollution |
