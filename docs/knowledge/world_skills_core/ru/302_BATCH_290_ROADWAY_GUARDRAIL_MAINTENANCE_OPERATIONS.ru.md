# BATCH_290 — Roadway Guardrail Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_290:roadway_guardrail_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| guardrailops.inventory.guardrail_run | Guardrail run record | invariant | Record stores run ID, route, side, length, system type, terminals and condition. | manage asset |
| guardrailops.inventory.terminal_record | Guardrail terminal record | invariant | Record captures end treatment type, orientation, condition, crash history and installation date. | track terminals |
| guardrailops.inventory.post_spacing | Guardrail post spacing | invariant | Spacing records post intervals and deviations that affect system performance. | inspect geometry |
| guardrailops.inventory.obstacle_shielded | Shielded roadside obstacle | variant | Obstacle may be slope, bridge end, culvert, tree, drop-off, water or fixed object. | know purpose |
| guardrailops.inspection.routine_guardrail_inspection | Routine guardrail inspection | invariant | Inspection checks rail height, alignment, posts, blocks, terminals, bolts, damage and vegetation. | find defects |
| guardrailops.inspection.post_crash_inspection | Post-crash guardrail inspection | invariant | Inspection evaluates impact damage, system function, debris, hazard exposure and repair priority. | restore protection |
| guardrailops.inspection.night_visibility_check | Guardrail night visibility check | variant | Check reviews delineators, reflectors, alignment and driver recognition in low light. | improve guidance |
| guardrailops.condition.rail_damage | Guardrail rail damage | invariant | Damage includes bent, torn, crushed, kinked, detached or corroded rail sections. | repair system |
| guardrailops.condition.post_damage | Guardrail post damage | invariant | Damage includes broken, rotted, bent, missing, loose or improperly embedded posts. | restore support |
| guardrailops.condition.blockout_damage | Guardrail blockout damage | invariant | Damage affects rail offset from post and can impair crash performance. | fix connection |
| guardrailops.condition.terminal_damage | Guardrail terminal damage | invariant | Damage to end treatment can create severe hazard or prevent energy absorption. | urgent repair |
| guardrailops.condition.height_deficiency | Guardrail height deficiency | invariant | Deficiency occurs when rail height is too low or high due to overlay, settlement or installation. | restore geometry |
| guardrailops.condition.flared_terminal_issue | Flared terminal issue | variant | Issue concerns terminal angle, grading, clear area or exposure to traffic path. | assess end |
| guardrailops.condition.corrosion | Guardrail corrosion | variant | Corrosion weakens rail, posts, bolts or connection hardware over time. | plan replacement |
| guardrailops.repairs.rail_section_replacement | Guardrail rail section replacement | invariant | Replacement installs compatible rail, splice bolts, lap direction and alignment. | repair barrier |
| guardrailops.repairs.post_replacement | Guardrail post replacement | invariant | Replacement restores post type, depth, spacing, blockout and soil support. | restore strength |
| guardrailops.repairs.terminal_repair | Guardrail terminal repair | invariant | Repair restores approved end treatment components, nose, cable, posts and alignment. | protect end |
| guardrailops.repairs.hardware_tightening | Guardrail hardware tightening | variant | Tightening corrects loose bolts, washers, splice connections and terminal hardware. | maintain integrity |
| guardrailops.repairs.grading_around_terminal | Terminal grading repair | variant | Repair restores traversable grading around terminal so system can function as intended. | support crashworthiness |
| guardrailops.priority.exposed_hazard_priority | Exposed hazard priority | invariant | Priority increases when damaged guardrail no longer shields steep slope, water, bridge or fixed object. | rank repair |
| guardrailops.priority.traffic_volume_priority | Guardrail traffic volume priority | variant | Priority considers road class, speed, traffic volume, heavy vehicles and crash exposure. | allocate crews |
| guardrailops.priority.temporary_protection | Temporary guardrail protection | variant | Protection uses cones, barrels, signs or temporary barrier until permanent repair. | reduce risk |
| guardrailops.crash.crash_record_link | Guardrail crash record link | invariant | Link connects damage to crash report, police record, claim, location and repair cost. | recover costs |
| guardrailops.crash.hit_and_run_damage | Guardrail hit-and-run damage | variant | Damage lacks responsible party and requires public repair funding or investigation. | document loss |
| guardrailops.crash.debris_cleanup | Guardrail crash debris cleanup | invariant | Cleanup removes rail fragments, vehicle parts, posts, bolts and sharp debris from roadway. | restore safety |
| guardrailops.workorders.guardrail_repair_order | Guardrail repair work order | invariant | Order specifies location, damage, parts, priority, traffic control, crew and closeout evidence. | schedule repair |
| guardrailops.workorders.contractor_repair | Guardrail contractor repair | variant | Contractor handles specialized terminal, long runs, emergency work or capital replacement. | expand capacity |
| guardrailops.workorders.parts_picklist | Guardrail repair parts picklist | variant | Picklist includes rail sections, posts, blockouts, bolts, terminals, reflectors and tools. | prepare crew |
| guardrailops.safety.traffic_control | Guardrail work traffic control | invariant | Control protects crews working at shoulder, median, curve, bridge approach or high-speed road. | worker safety |
| guardrailops.safety.sharp_metal_hazard | Sharp metal guardrail hazard | invariant | Hazard occurs from torn rail, twisted panels, exposed bolts or crash debris. | prevent injury |
| guardrailops.safety.lifting_handling | Guardrail lifting and handling | variant | Handling controls heavy rail sections, posts, awkward shapes, pinch points and equipment use. | protect crew |
| guardrailops.quality.lap_direction_check | Guardrail lap direction check | invariant | Check ensures rail overlaps in correct direction relative to traffic flow. | reduce snagging |
| guardrailops.quality.bolt_pattern_check | Guardrail bolt pattern check | invariant | Check verifies bolts, washers, torque, splice pattern and missing hardware. | quality control |
| guardrailops.quality.terminal_model_check | Guardrail terminal model check | variant | Check confirms installed terminal matches approved model, parts and orientation. | avoid mismatch |
| guardrailops.data.photo_documentation | Guardrail photo documentation | invariant | Photos show damage, measurements, terminal, repair stages, final condition and location. | evidence |
| guardrailops.data.asset_update | Guardrail asset update | invariant | Update records repaired parts, replaced terminal, condition, crash link and inspection date. | current inventory |
| guardrailops.reporting.damage_backlog | Guardrail damage backlog report | invariant | Report summarizes unrepaired damage by severity, route, age, parts and hazard exposure. | manage risk |
| guardrailops.reporting.crash_cost_report | Guardrail crash cost report | variant | Report tracks repair labor, parts, traffic control, contractor cost and recovery billing. | recover funds |
| guardrailops.metrics.repair_response_time | Guardrail repair response time KPI | invariant | KPI measures time from damage discovery to temporary control and permanent repair. | improve safety |
| guardrailops.metrics.terminal_defect_rate | Guardrail terminal defect rate KPI | variant | KPI tracks damaged, obsolete, misaligned or deficient terminals by corridor. | target upgrades |
| guardrailops.coordination.bridge_team_link | Guardrail bridge team coordination | variant | Coordination handles bridge rail transitions, parapets, approach rails and structure-related repairs. | align assets |
| guardrailops.coordination.mowing_visibility_link | Guardrail mowing coordination | variant | Coordination removes vegetation that hides rail, terminals, delineators or damage. | improve inspection |
| guardrailops.continuity.storm_damage_response | Guardrail storm damage response | variant | Response handles debris impact, washout, downed trees, flooding or slope failure damaging barrier. | restore protection |
| guardrailops.close.repair_closeout | Guardrail repair closeout | invariant | Closeout confirms geometry, hardware, terminal, photos, traffic control removal and records update. | finish repair |
