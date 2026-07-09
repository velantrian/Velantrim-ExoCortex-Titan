# BATCH_269 — Bridge Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_269:bridge_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| bridgeinsp.inventory.bridge_record | Bridge inventory record | invariant | Record stores bridge ID, location, owner, route, span, material, age and geometry. | know bridge |
| bridgeinsp.inventory.component_list | Bridge component list | invariant | List identifies deck, superstructure, substructure, bearings, joints, railings and approaches. | inspect system |
| bridgeinsp.inventory.waterway_flag | Bridge waterway flag | variant | Flag records stream, scour risk, flood history, channel condition and access constraints. | hydraulic awareness |
| bridgeinsp.schedule.cycle | Bridge inspection cycle | invariant | Cycle sets routine, fracture-critical, underwater, special or interim inspection frequency. | meet requirements |
| bridgeinsp.schedule.access_plan | Bridge inspection access plan | variant | Plan defines lane closure, snooper truck, boat, rope access, rail coordination or drone. | reach components |
| bridgeinsp.schedule.traffic_control | Bridge inspection traffic control | invariant | Control protects inspectors and road users with signs, cones, closures or flaggers. | safe inspection |
| bridgeinsp.field.arrival_safety | Bridge inspection arrival safety | invariant | Safety reviews traffic, fall hazards, water, weather, utilities, wildlife and PPE. | protect crew |
| bridgeinsp.field.photo_log | Bridge inspection photo log | invariant | Log links photo to component, defect, location, direction and date. | visual evidence |
| bridgeinsp.field.measurement | Bridge defect measurement | invariant | Measurement records length, width, depth, offset, crack size, section loss or movement. | quantify defect |
| bridgeinsp.field.soundings | Bridge deck sounding | variant | Sounding identifies delamination, voids or debonded areas by acoustic response. | find hidden damage |
| bridgeinsp.deck.deck_condition | Bridge deck condition | invariant | Condition rates wearing surface, cracking, spalls, patches, drainage and delamination. | assess deck |
| bridgeinsp.deck.joint_condition | Bridge joint condition | invariant | Condition checks seals, leakage, debris, armoring, movement and damage. | protect structure |
| bridgeinsp.deck.drainage_condition | Bridge deck drainage condition | invariant | Condition reviews scuppers, downspouts, ponding, clogging and erosion. | prevent deterioration |
| bridgeinsp.super.beam_condition | Bridge beam condition | invariant | Condition records corrosion, cracks, section loss, impact damage, distortion and paint. | assess superstructure |
| bridgeinsp.super.girder_fatigue | Bridge girder fatigue detail | variant | Detail checks fatigue-prone welds, connections, cover plates or distortion. | prevent fracture |
| bridgeinsp.super.truss_member | Bridge truss member condition | variant | Condition reviews members, gusset plates, pins, pack rust, cracks and deformation. | truss safety |
| bridgeinsp.sub.pier_condition | Bridge pier condition | invariant | Condition reviews cracking, spalling, scour, settlement, collision damage and reinforcement exposure. | support stability |
| bridgeinsp.sub.abutment_condition | Bridge abutment condition | invariant | Condition checks cracks, rotation, wingwalls, settlement, backwall and drainage. | end support |
| bridgeinsp.sub.bearing_condition | Bridge bearing condition | invariant | Condition records alignment, corrosion, frozen movement, displacement and debris. | load transfer |
| bridgeinsp.scour.scour_observation | Bridge scour observation | variant | Observation records exposed footings, holes, debris, channel migration and erosion. | water risk |
| bridgeinsp.approach.approach_slab | Bridge approach slab condition | variant | Condition records settlement, bumps, cracks, voids, drainage and pavement transition. | ride safety |
| bridgeinsp.approach.guardrail_transition | Bridge guardrail transition | invariant | Check reviews approach rail, end treatments, connections, height and damage. | crash protection |
| bridgeinsp.rating.element_rating | Bridge element rating | invariant | Rating assigns condition state to element using standard definitions and quantities. | compare condition |
| bridgeinsp.rating.general_condition | Bridge general condition rating | invariant | Rating summarizes deck, superstructure, substructure or culvert condition. | program metric |
| bridgeinsp.rating.load_posting | Bridge load posting review | invariant | Review evaluates rating, signs, legal loads, restrictions and posting need. | protect bridge |
| bridgeinsp.defect.critical_finding | Bridge critical finding | invariant | Finding identifies condition needing immediate restriction, closure, repair or engineering review. | prevent failure |
| bridgeinsp.defect.impact_damage | Bridge impact damage | variant | Damage records vehicle, vessel, debris or equipment strike and urgent assessment. | respond quickly |
| bridgeinsp.defect.crack_monitor | Bridge crack monitor | variant | Monitor tracks crack size, location, date, gauge, growth and response threshold. | watch progression |
| bridgeinsp.repair.repair_recommendation | Bridge repair recommendation | invariant | Recommendation states defect, priority, method, quantity, urgency and responsible unit. | plan fix |
| bridgeinsp.repair.maintenance_referral | Bridge maintenance referral | variant | Referral sends debris, joint cleaning, drainage, sign, guardrail or minor repair to crews. | close small issues |
| bridgeinsp.repair.capital_project_flag | Bridge capital project flag | variant | Flag identifies rehab, replacement, widening, scour retrofit or major strengthening need. | long-term plan |
| bridgeinsp.records.inspection_report | Bridge inspection report | invariant | Report documents team, access, ratings, defects, photos, recommendations and restrictions. | official record |
| bridgeinsp.records.plan_review | Bridge plan review reference | variant | Reference uses prior plans, as-builts, load ratings and repair documents. | understand structure |
| bridgeinsp.records.data_update | Bridge inventory data update | invariant | Update corrects geometry, material, ownership, traffic, waterway, ratings or status. | current database |
| bridgeinsp.quality.peer_review | Bridge inspection peer review | invariant | Review checks ratings, critical findings, photos, measurements and recommendations. | consistency |
| bridgeinsp.quality.certification | Bridge inspector certification record | invariant | Record tracks team leader qualifications, training, experience and expiration. | qualified inspection |
| bridgeinsp.reporting.program_report | Bridge inspection program report | variant | Report summarizes inspections due, completed, condition, postings, critical findings and backlog. | oversight |
| bridgeinsp.metrics.bridge_kpi | Bridge inspection KPI | variant | KPI tracks on-time inspections, poor bridges, critical findings, load postings and repair closure. | manage bridges |
| bridgeinsp.communication.owner_notice | Bridge owner notice | invariant | Notice communicates findings, restrictions, repairs, deadlines and responsibilities. | prompt action |
| bridgeinsp.communication.public_restriction | Bridge public restriction notice | variant | Notice explains closure, lane limit, load posting, detour and duration. | public safety |
| bridgeinsp.continuity.emergency_inspection | Bridge emergency inspection | invariant | Inspection responds to flood, earthquake, fire, collision, overload or observed distress. | urgent safety |
| bridgeinsp.close.finding_closure | Bridge finding closure | invariant | Closure records repair, monitoring, restriction, engineering acceptance or capital project handoff. | close loop |
| bridgeinsp.audit.audit_trail | Bridge inspection audit trail | invariant | Trail records inspection, rating changes, reports, restrictions, repairs and approvals. | defensible history |
| bridgeinsp.safety.railroad_coordination | Railroad bridge access coordination | variant | Coordination manages track access, flagging, schedules, safety briefing and permits. | safe rail proximity |
