# BATCH_284 — Public Playground Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_284:public_playground_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| playgroundops.inventory.playground_record | Public playground record | invariant | Record stores site, equipment, age range, surfacing, owner, installation date and inspection history. | manage asset |
| playgroundops.inventory.equipment_inventory | Playground equipment inventory | invariant | Inventory lists swings, slides, climbers, spinners, seesaws, panels, shade and site furniture. | know equipment |
| playgroundops.inventory.age_group_zone | Playground age-group zone | invariant | Zone separates equipment intended for toddlers, preschool children or school-age children. | match users |
| playgroundops.inventory.fall_zone | Playground fall zone | invariant | Fall zone defines required protective surface area around equipment. | assess safety |
| playgroundops.inspection.routine_visual_inspection | Routine playground visual inspection | invariant | Inspection checks obvious hazards, surfacing, litter, broken parts, vandalism and closures. | daily safety |
| playgroundops.inspection.operational_inspection | Playground operational inspection | invariant | Inspection checks wear, movement, fasteners, chains, bearings, surfacing depth and function. | maintain equipment |
| playgroundops.inspection.annual_audit | Playground annual audit | invariant | Audit reviews equipment against current standards, records, hazards, surfacing and accessibility. | program assurance |
| playgroundops.inspection.post_incident_inspection | Post-incident playground inspection | variant | Inspection follows injury, complaint, vandalism, storm damage or equipment failure. | document response |
| playgroundops.surfacing.loose_fill_depth | Loose-fill surfacing depth | invariant | Depth measures engineered wood fiber, rubber mulch, sand or pea gravel under fall zones. | absorb impact |
| playgroundops.surfacing.unitary_surface_condition | Unitary playground surface condition | invariant | Condition checks poured rubber, tiles or turf for cracks, holes, seams, hardness and trip edges. | protect falls |
| playgroundops.surfacing.displacement | Playground surfacing displacement | variant | Displacement occurs under swings, slide exits or high-use paths and reduces protection. | refill surface |
| playgroundops.surfacing.contamination | Playground surfacing contamination | variant | Contamination includes glass, needles, feces, oil, pests, trash or hazardous objects. | clean urgently |
| playgroundops.hazards.entrapment_hazard | Playground entrapment hazard | invariant | Hazard exists when openings can trap head, neck, body, fingers or clothing. | prevent injury |
| playgroundops.hazards.protrusion_hazard | Playground protrusion hazard | invariant | Hazard includes bolts, hooks, hardware or broken pieces that can puncture or snag. | remove danger |
| playgroundops.hazards.sharp_edge | Playground sharp edge | invariant | Edge arises from broken metal, cracked plastic, splintered wood or damaged hardware. | make safe |
| playgroundops.hazards.crush_shear_point | Playground crush or shear point | invariant | Point occurs where moving parts can pinch, crush or cut body parts. | inspect movement |
| playgroundops.hazards.trip_hazard | Playground trip hazard | variant | Hazard includes exposed footings, edging, roots, mats, holes or uneven access paths. | reduce falls |
| playgroundops.equipment.swing_chain_wear | Swing chain wear | invariant | Wear includes thinning links, corrosion, twisting, broken connectors or unsafe seats. | replace parts |
| playgroundops.equipment.slide_condition | Playground slide condition | invariant | Condition checks bedway, sidewalls, exit zone, heat, cracks, fasteners and alignment. | safe sliding |
| playgroundops.equipment.climber_integrity | Playground climber integrity | invariant | Integrity checks rungs, nets, ropes, welds, anchors, grips and fall exposure. | prevent failure |
| playgroundops.equipment.rotating_equipment | Rotating playground equipment check | variant | Check reviews bearings, speed, clearances, surfacing and pinch or ejection hazards. | control motion |
| playgroundops.access.accessible_route | Playground accessible route | invariant | Route connects parking, sidewalk, entrance, equipment and surfacing without barriers. | inclusive access |
| playgroundops.access.transfer_platform | Playground transfer platform | variant | Platform enables transfer from mobility device to elevated play structure. | access equipment |
| playgroundops.access.ground_level_component | Accessible ground-level component | variant | Component provides play value reachable without climbing or elevated transfer. | inclusive play |
| playgroundops.repairs.make_safe_action | Playground make-safe action | invariant | Action removes, barricades, locks out or temporarily repairs unsafe component. | immediate control |
| playgroundops.repairs.part_replacement_order | Playground part replacement order | invariant | Order specifies part, model, fasteners, warranty, supplier, installation and verification. | restore equipment |
| playgroundops.repairs.surfacing_replenishment | Playground surfacing replenishment | invariant | Replenishment restores loose-fill depth, levels displacement and documents material quantity. | restore protection |
| playgroundops.repairs.contractor_repair | Playground contractor repair | variant | Repair uses certified vendor for specialized equipment, surfacing, welding or warranty work. | ensure quality |
| playgroundops.closure.partial_closure | Playground partial closure | invariant | Closure isolates unsafe equipment while keeping safe areas open with clear barriers and signs. | limit disruption |
| playgroundops.closure.full_closure | Playground full closure | invariant | Closure shuts entire play area for severe hazard, construction, contamination or unsafe surfacing. | protect users |
| playgroundops.closure.reopening_check | Playground reopening check | invariant | Check confirms hazards corrected, surfacing restored, barriers removed and inspection documented. | reopen safely |
| playgroundops.records.inspection_form | Playground inspection form | invariant | Form records date, inspector, site, findings, actions, photos, priority and signature. | trace inspection |
| playgroundops.records.photo_evidence | Playground photo evidence | invariant | Photos document hazards, repairs, surfacing depth, closures and final condition. | support records |
| playgroundops.records.standard_reference | Playground standard reference | variant | Reference links finding to applicable playground safety standard, local rule or manufacturer guidance. | justify action |
| playgroundops.safety.inspector_safety | Playground inspector safety | invariant | Safety covers sharps, unstable equipment, weather, hostile animals, traffic and lone work. | protect staff |
| playgroundops.safety.heat_surface_risk | Playground hot surface risk | variant | Risk occurs when metal, rubber or synthetic surfaces become hot enough to burn skin. | prevent burns |
| playgroundops.safety.sanitation_hazard | Playground sanitation hazard | variant | Hazard includes feces, vomit, needles, pests, bodily fluids or contaminated surfacing. | clean safely |
| playgroundops.reporting.hazard_backlog | Playground hazard backlog report | invariant | Report summarizes open hazards by severity, site, equipment, age and repair status. | manage risk |
| playgroundops.reporting.inspection_compliance | Playground inspection compliance report | variant | Report tracks completed inspections against required frequency and missed sites. | program control |
| playgroundops.metrics.repair_cycle_time | Playground repair cycle time KPI | invariant | KPI measures time from hazard finding to make-safe and permanent repair. | improve response |
| playgroundops.metrics.closure_days | Playground closure days KPI | variant | KPI tracks days equipment or sites remain closed by cause and repair dependency. | reduce downtime |
| playgroundops.coordination.risk_management_notice | Playground risk management notice | variant | Notice alerts legal or insurance staff for serious injury, repeated hazard or claim. | manage liability |
| playgroundops.coordination.capital_replacement_link | Playground capital replacement link | variant | Link escalates obsolete or high-cost equipment from maintenance to replacement planning. | renew asset |
| playgroundops.close.inspection_closeout | Playground inspection closeout | invariant | Closeout confirms hazards assigned, urgent actions done, records filed and next inspection scheduled. | finish inspection |
